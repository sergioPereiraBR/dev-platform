# src/dev_platform/application/user/use_cases.py
from typing import List
from application.user.ports import Logger, UnitOfWork
from application.user.dtos import UserCreateDTO
from domain.user.entities import User
from domain.user.services import DomainServiceFactory
from domain.user.exceptions import (
    UserValidationException,
    UserAlreadyExistsException,
    UserNotFoundException,
    DomainException
)


class BaseUseCase:
    """Base class for all use cases with common functionality."""
    
    def __init__(self, uow: UnitOfWork, logger: Logger):
        self._uow = uow
        self._logger = logger
    
    def _log_error(self, message: str, **kwargs):
        """Centralized error logging."""
        self._logger.error(message, **kwargs)
    
    def _log_info(self, message: str, **kwargs):
        """Centralized info logging.""" 
        self._logger.info(message, **kwargs)


class CreateUserUseCase(BaseUseCase):
    def __init__(self, uow: UnitOfWork, logger: Logger):
        super().__init__(uow, logger)
    # def __init__(self, uow: UnitOfWork, logger: Logger, domain_service_factory: DomainServiceFactory):
    #     super().__init__(uow, logger)
    #     self._domain_service_factory = domain_service_factory
    
    async def execute(self, dto: UserCreateDTO) -> User:
        async with self._uow:
            self._log_info("Starting user creation", name=dto.name, email=dto.email)
            
            try:
                # Create user entity from DTO
                user = User.create(name=dto.name, email=dto.email)
                
                # Create domain service with repository access
                domain_service = self._domain_service_factory.create_user_domain_service(
                    self._uow.users
                )
                
                # Validate all business rules
                await domain_service.validate_new_user(user)
                
                self._log_info("User validation passed", email=dto.email)
                
                # Save user
                saved_user = await self._uow.users.save(user)
                await self._uow.commit()
                
                self._log_info("User created successfully", 
                             user_id=saved_user.id, 
                             name=saved_user.name.value, 
                             email=saved_user.email.value)
                
                return saved_user
                
            except UserValidationException as e:
                self._log_error("User validation failed", 
                              email=dto.email, 
                              validation_errors=e.validation_errors)
                raise
            
            except UserAlreadyExistsException as e:
                self._logger.warning("Attempted to create duplicate user", email=dto.email)
                raise
            
            except DomainException as e:
                self._log_error("Domain error during user creation", 
                              error_code=e.error_code, 
                              message=e.message,
                              details=e.details)
                raise
            
            except Exception as e:
                self._log_error("Unexpected error during user creation", 
                              email=dto.email, 
                              error=str(e))
                raise RuntimeError(f"Failed to create user: {str(e)}")


class ListUsersUseCase(BaseUseCase):
    async def execute(self) -> List[User]:
        async with self._uow:
            try:
                self._log_info("Starting user listing")
                users = await self._uow.users.find_all()
                self._log_info("Users retrieved successfully", count=len(users))
                return users
            
            except Exception as e:
                self._log_error("Error listing users", error=str(e))
                raise RuntimeError(f"Failed to list users: {str(e)}")


class UpdateUserUseCase(BaseUseCase):
    def __init__(self, uow: UnitOfWork, logger: Logger, domain_service_factory: DomainServiceFactory):
        super().__init__(uow, logger)
        self._domain_service_factory = domain_service_factory
    
    async def execute(self, user_id: int, dto: UserCreateDTO) -> User:
        async with self._uow:
            self._log_info("Starting user update", user_id=user_id, name=dto.name, email=dto.email)
            
            try:
                # Check if user exists
                existing_user = await self._uow.users.find_by_id(user_id)
                if not existing_user:
                    raise UserNotFoundException(str(user_id))
                
                # Create updated user entity
                updated_user = User.create(name=dto.name, email=dto.email)
                updated_user.id = user_id  # Preserve the ID
                
                # Create domain service
                domain_service = self._domain_service_factory.create_user_domain_service(
                    self._uow.users
                )
                
                # Validate update
                await domain_service.validate_user_update(user_id, updated_user)
                
                self._log_info("User update validation passed", user_id=user_id)
                
                # Save updated user
                saved_user = await self._uow.users.save(updated_user)
                await self._uow.commit()
                
                self._log_info("User updated successfully", 
                             user_id=saved_user.id,
                             name=saved_user.name.value,
                             email=saved_user.email.value)
                
                return saved_user
                
            except (UserValidationException, UserNotFoundException) as e:
                if isinstance(e, UserValidationException):
                    self._log_error("User update validation failed", 
                                  user_id=user_id,
                                  validation_errors=e.validation_errors)
                else:
                    self._log_error("User not found for update", user_id=user_id)
                raise
            
            except DomainException as e:
                self._log_error("Domain error during user update", 
                              user_id=user_id,
                              error_code=e.error_code, 
                              message=e.message,
                              details=e.details)
                raise
            
            except Exception as e:
                self._log_error("Unexpected error during user update", 
                              user_id=user_id, 
                              error=str(e))
                raise RuntimeError(f"Failed to update user: {str(e)}")


class GetUserUseCase(BaseUseCase):    
    async def execute(self, user_id: int) -> User:
        async with self._uow:
            try:
                self._log_info("Getting user", user_id=user_id)
                user = await self._uow.users.find_by_id(user_id)
                
                if not user:
                    raise UserNotFoundException(str(user_id))
                
                self._log_info("User retrieved successfully", user_id=user_id)
                return user
            
            except UserNotFoundException:
                self._log_error("User not found", user_id=user_id)
                raise
            
            except Exception as e:
                self._log_error("Error getting user", user_id=user_id, error=str(e))
                raise RuntimeError(f"Failed to get user: {str(e)}")


class DeleteUserUseCase(BaseUseCase):
    async def execute(self, user_id: int) -> bool:
        async with self._uow:
            try:
                self._log_info("Starting user deletion", user_id=user_id)
                
                # Check if user exists
                existing_user = await self._uow.users.find_by_id(user_id)
                if not existing_user:
                    raise UserNotFoundException(str(user_id))
                
                # Perform deletion
                success = await self._uow.users.delete(user_id)
                
                if success:
                    await self._uow.commit()
                    self._log_info("User deleted successfully", user_id=user_id)
                else:
                    self._logger.warning("User deletion failed", user_id=user_id)
                
                return success
                
            except UserNotFoundException:
                self._log_error("User not found for deletion", user_id=user_id)
                raise
            
            except Exception as e:
                self._log_error("Error deleting user", user_id=user_id, error=str(e))
                raise RuntimeError(f"Failed to delete user: {str(e)}")


# Factory para criar use cases com dependências configuradas
class UseCaseFactory:
    def __init__(self, composition_root):
        self._composition_root = composition_root
    
    def create_user_use_case(self) -> CreateUserUseCase:
        return self._composition_root.create_user_use_case()
    
    def list_users_use_case(self) -> ListUsersUseCase:
        return self._composition_root.list_users_use_case()
    
    def update_user_use_case(self) -> UpdateUserUseCase:
        return self._composition_root.update_user_use_case()
    
    def get_user_use_case(self) -> GetUserUseCase:
        return self._composition_root.get_user_use_case()
    
    def delete_user_use_case(self) -> DeleteUserUseCase:
        return self._composition_root.delete_user_use_case()
