# src/dev_platform/application/user/use_cases.py
from typing import List
from application.user.ports import Logger, UnitOfWork
from application.user.dtos import UserCreateDTO
from domain.user.entities import User
from domain.user.services import UserDomainService
from domain.user.exceptions import (
    UserValidationException,
    UserAlreadyExistsException,
    DomainException
)


class CreateUserUseCase:
    def __init__(self, uow: UnitOfWork, logger: Logger):
        self._uow = uow
        self._logger = logger
    
    async def execute(self, dto: UserCreateDTO) -> User:
        async with self._uow:
            self._logger.info("Starting user creation", name=dto.name, email=dto.email)
            
            try:
                # Create user entity from DTO
                user = User.create(name=dto.name, email=dto.email)
                
                # Initialize domain service with repository access
                domain_service = UserDomainService(self._uow.users)
                
                # Validate all business rules using domain service
                await domain_service.validate_business_rules(user)
                
                self._logger.info("User validation passed", email=dto.email)
                
                # Save user
                saved_user = await self._uow.users.save(user)
                await self._uow.commit()
                
                self._logger.info("User created successfully", 
                                user_id=saved_user.id, 
                                name=saved_user.name.value, 
                                email=saved_user.email.value)
                
                return saved_user
                
            except UserValidationException as e:
                self._logger.error("User validation failed", 
                                 email=dto.email, 
                                 validation_errors=e.validation_errors)
                raise
            
            except UserAlreadyExistsException as e:
                self._logger.warning("Attempted to create duplicate user", email=dto.email)
                raise
            
            except DomainException as e:
                self._logger.error("Domain error during user creation", 
                                 error_code=e.error_code, 
                                 message=e.message,
                                 details=e.details)
                raise
            
            except Exception as e:
                self._logger.error("Unexpected error during user creation", 
                                 email=dto.email, 
                                 error=str(e))
                raise RuntimeError(f"Failed to create user: {str(e)}")


class ListUsersUseCase:
    def __init__(self, uow: UnitOfWork, logger: Logger):
        self._uow = uow
        self._logger = logger
    
    async def execute(self) -> List[User]:
        async with self._uow:
            try:
                self._logger.info("Starting user listing")
                users = await self._uow.users.find_all()
                self._logger.info("Users retrieved successfully", count=len(users))
                return users
            
            except Exception as e:
                self._logger.error("Error listing users", error=str(e))
                raise RuntimeError(f"Failed to list users: {str(e)}")


class UpdateUserUseCase:
    def __init__(self, uow: UnitOfWork, logger: Logger):
        self._uow = uow
        self._logger = logger
    
    async def execute(self, user_id: int, dto: UserCreateDTO) -> User:
        async with self._uow:
            self._logger.info("Starting user update", user_id=user_id, name=dto.name, email=dto.email)
            
            try:
                # Check if user exists
                existing_user = await self._uow.users.find_by_id(user_id)
                if not existing_user:
                    from domain.user.exceptions import UserNotFoundException
                    raise UserNotFoundException(str(user_id))
                
                # Create updated user entity
                updated_user = User.create(name=dto.name, email=dto.email)
                updated_user.id = user_id  # Preserve the ID
                
                # Initialize domain service
                domain_service = UserDomainService(self._uow.users)
                
                # Validate update using domain service
                await domain_service.validate_user_update(user_id, updated_user)
                
                self._logger.info("User update validation passed", user_id=user_id)
                
                # Save updated user
                saved_user = await self._uow.users.save(updated_user)
                await self._uow.commit()
                
                self._logger.info("User updated successfully", 
                                user_id=saved_user.id,
                                name=saved_user.name.value,
                                email=saved_user.email.value)
                
                return saved_user
                
            except UserValidationException as e:
                self._logger.error("User update validation failed", 
                                 user_id=user_id,
                                 validation_errors=e.validation_errors)
                raise
            
            except DomainException as e:
                self._logger.error("Domain error during user update", 
                                 user_id=user_id,
                                 error_code=e.error_code, 
                                 message=e.message,
                                 details=e.details)
                raise
            
            except Exception as e:
                self._logger.error("Unexpected error during user update", 
                                 user_id=user_id, 
                                 error=str(e))
                raise RuntimeError(f"Failed to update user: {str(e)}")


class GetUserUseCase:
    def __init__(self, uow: UnitOfWork, logger: Logger):
        self._uow = uow
        self._logger = logger
    
    async def execute(self, user_id: int) -> User:
        async with self._uow:
            try:
                self._logger.info("Getting user", user_id=user_id)
                user = await self._uow.users.find_by_id(user_id)
                
                if not user:
                    from domain.user.exceptions import UserNotFoundException
                    raise UserNotFoundException(str(user_id))
                
                self._logger.info("User retrieved successfully", user_id=user_id)
                return user
            
            except DomainException:
                raise
            
            except Exception as e:
                self._logger.error("Error getting user", user_id=user_id, error=str(e))
                raise RuntimeError(f"Failed to get user: {str(e)}")


class DeleteUserUseCase:
    def __init__(self, uow: UnitOfWork, logger: Logger):
        self._uow = uow
        self._logger = logger
    
    async def execute(self, user_id: int) -> bool:
        async with self._uow:
            try:
                self._logger.info("Starting user deletion", user_id=user_id)
                
                # Check if user exists
                existing_user = await self._uow.users.find_by_id(user_id)
                if not existing_user:
                    from domain.user.exceptions import UserNotFoundException
                    raise UserNotFoundException(str(user_id))
                
                # Perform deletion (you'll need to implement this in repository)
                success = await self._uow.users.delete(user_id)
                
                if success:
                    await self._uow.commit()
                    self._logger.info("User deleted successfully", user_id=user_id)
                else:
                    self._logger.warning("User deletion failed", user_id=user_id)
                
                return success
                
            except DomainException:
                raise
            
            except Exception as e:
                self._logger.error("Error deleting user", user_id=user_id, error=str(e))
                raise RuntimeError(f"Failed to delete user: {str(e)}")
