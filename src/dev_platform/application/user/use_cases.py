# ./src/dev_platform/application/user/use_cases.py
from typing import List

from dev_platform.application.user.dtos import UserCreateDTO, UserUpdateDTO, UserDTO
from dev_platform.domain.user.entities import User
from dev_platform.application.ports.logger import ILogger
from dev_platform.application.user.ports import UnitOfWork
from dev_platform.domain.user.services import DomainServiceFactory
from dev_platform.domain.user.exceptions import (
    UserValidationException,
    UserAlreadyExistsException,
    UserNotFoundException,
    DomainException,
)


class BaseUseCase:
    """Base class for all use cases, providing access to Unit of Work and logger."""
    def __init__(self, uow: UnitOfWork, logger: ILogger):
        """Base class for all use cases, providing access to Unit of Work and logger."""
        self._uow = uow
        self._logger = logger

    # Helper method to get the value from a value object or return the object itself.
    def get_value(self, obj):
        return obj.value if hasattr(obj, "value") else obj

    # Helper method to convert a user entity to a UserDTO
    def fet_dto(self, user):
        """Converts a user entity to a UserDTO."""
        return UserDTO(
            id=str(user.id),
            name=self.get_value(user.name),
            email=self.get_value(user.email)
        )   


class CreateUserUseCase(BaseUseCase):
    """Use case for creating a new user."""
    def __init__(
        self,
        uow: UnitOfWork,
        logger: ILogger,
        domain_service_factory: DomainServiceFactory,
    ):
        super().__init__(uow, logger)
        self._domain_service_factory = domain_service_factory

    async def execute(self, dto: UserCreateDTO) -> UserDTO:
        """Executes the use case to create a new user."""
        async with self._uow:
            # Gerar ID de correlação para esta operação
            self._logger.set_correlation_id()

            self._logger.info("Starting user creation", name=dto.name, email=dto.email)

            try:
                # Create user entity from DTO
                user = User.create(name=dto.name, email=dto.email)

                # Create domain service with repository access
                domain_service = (
                    self._domain_service_factory.create_user_domain_service(
                        self._uow.users
                    )
                )

                # CORRIGIDO: Método correto é validate_business_rules
                await domain_service.validate_business_rules(user)

                self._logger.info("User validation passed", email=dto.email)

                # Save user
                saved_user = await self._uow.users.save(user)
                await self._uow.commit()

                self._logger.info(
                    "User created successfully",
                    user_id=saved_user.id,
                    name=self.get_value(saved_user.name),
                    email=self.get_value(saved_user.email),
                )

                return UserDTO(
                    id=str(saved_user.id),  # se id for int, converta para string
                    name=self.get_value(saved_user.name),  # value object -> string
                    email=self.get_value(saved_user.email)  # value object -> string
                )

            except UserValidationException as e:
                self._logger.error(
                    "User validation failed",
                    email=dto.email,
                    validation_errors=e.validation_errors,
                )
                raise

            except UserAlreadyExistsException as e:
                self._logger.warning(
                    "Attempted to create duplicate user", email=dto.email
                )
                raise

            except DomainException as e:
                self._logger.error(
                    "Domain error during user creation",
                    error_code=e.error_code,
                    message=e.message,
                    details=e.details,
                )
                raise


class ListUsersUseCase(BaseUseCase): 
    """Use case for listing all users."""  
    async def execute(self) -> List[UserDTO]:
        """Executes the use case to list all users."""
        async with self._uow:
            try:
                self._logger.info("Starting user listing")
                users = await self._uow.users.find_all()
                
                self._logger.info("Users retrieved successfully", count=len(users))
                users_dto = [self.fet_dto(user) for user in users]  
                return users_dto
            
            except UserNotFoundException:
                self._logger.error("User not found")
                raise


class UpdateUserUseCase(BaseUseCase):
    """Use case for updating an existing user."""
    def __init__(
        self,
        uow: UnitOfWork,
        logger: ILogger,
        domain_service_factory: DomainServiceFactory,
    ):
        super().__init__(uow, logger)
        self._domain_service_factory = domain_service_factory  

    async def execute(self, user_id: int, dto: UserUpdateDTO) -> UserDTO:
        """Executes the use case to update an existing user."""
        async with self._uow:
            # Gerar ID de correlação para esta operação
            self._logger.set_correlation_id()
            self._logger.info(
                "Starting user update", user_id=user_id, name=dto.name, email=dto.email
            )

            try:
                # Check if user exists
                existing_user = await self._uow.users.find_by_id(user_id)
                if not existing_user:
                    self._logger.error("User not found for update", user_id=user_id)
                    raise UserNotFoundException(str(user_id))

                # Atualizar a entidade existente diretamente com os novos dados do DTO
                existing_user.update_details(dto.name, dto.email)
                domain_service = self._domain_service_factory.create_user_domain_service(self._uow.users)

                # Validar a entidade atualizada, incluindo a verificação de unicidade de e-mail se ele mudou
                await domain_service.validate_user_update(user_id, existing_user)
                # Salvar a entidade atualizada
                saved_user = await self._uow.users.save(existing_user)
                await self._uow.commit()

                saved_user_dto = UserDTO(
                    id=str(saved_user.id),  # se id for int, converta para string
                    name=self.get_value(saved_user.name),
                    email=self.get_value(saved_user.email),  # value object -> string
                )

                self._logger.info(
                    "User updated successfully",
                    user_id=saved_user_dto.id,
                    name=saved_user_dto.name,
                    email=saved_user_dto.email,
                )

                return saved_user_dto

            
            except (UserValidationException, UserNotFoundException) as e:
                if isinstance(e, UserValidationException):
                    self._logger.error(
                        "User update validation failed",
                        user_id=user_id,
                        validation_errors=e.validation_errors,
                    )
                else:
                    self._logger.error("User not found for update", user_id=user_id)
                raise

            except DomainException as e:
                self._logger.error(
                    "Domain error during user update",
                    user_id=user_id,
                    error_code=e.error_code,
                    message=e.message,
                    details=e.details,
                )
                raise


class GetUserUseCase(BaseUseCase):
    """Use case for retrieving a user by ID."""
    
    async def execute(self, user_id: int) -> UserDTO:
        """Executes the use case to retrieve a user by ID."""
        async with self._uow:
            try:
                self._logger.info("Getting user", user_id=user_id)
                user = await self._uow.users.find_by_id(user_id)

                if not user:
                    self._logger.error("User not found", user_id=user_id)
                    raise UserNotFoundException(str(user_id))

                self._logger.info("User retrieved successfully", user_id=user_id)
                return UserDTO(
                    id=str(user.id),
                    name=self.get_value(user.name),
                    email=self.get_value(user.email),
                )

            except UserNotFoundException:
                self._logger.error("User not found", user_id=user_id)
                raise


class DeleteUserUseCase(BaseUseCase):
    """Use case for deleting a user by ID."""
    async def execute(self, user_id: int) -> bool:
        """Executes the use case to delete a user by ID."""
        async with self._uow:
            try:
                self._logger.info("Starting user deletion", user_id=user_id)

                # Check if user exists
                existing_user = await self._uow.users.find_by_id(user_id)
                if not existing_user:
                    self._logger.error("User not found for deletion", user_id=user_id)
                    raise UserNotFoundException(str(user_id))

                # Perform deletion
                success = await self._uow.users.delete(user_id)

                if success:
                    await self._uow.commit()
                    self._logger.info("User deleted successfully", user_id=user_id)
                else:
                    self._logger.warning("User deletion failed", user_id=user_id)

                return success

            except UserNotFoundException:
                self._logger.error("User not found for deletion", user_id=user_id)
                raise


# Factory para criar use cases com dependências configuradas
class UseCaseFactory:
    def __init__(self, composition_root: BaseUseCase):
        """Initializes the UseCaseFactory with a composition root."""
        self._composition_root: BaseUseCase = composition_root

    def create_user_use_case(self) -> CreateUserUseCase:
        """Creates an instance of CreateUserUseCase."""
        return self._composition_root.create_user_use_case()

    def list_users_use_case(self) -> ListUsersUseCase:
        """Creates an instance of ListUsersUseCase."""
        return self._composition_root.list_users_use_case()

    def update_user_use_case(self) -> UpdateUserUseCase:
        """Creates an instance of UpdateUserUseCase."""
        return self._composition_root.update_user_use_case()

    def get_user_use_case(self) -> GetUserUseCase:
        """Creates an instance of GetUserUseCase."""
        return self._composition_root.get_user_use_case()

    def delete_user_use_case(self) -> DeleteUserUseCase:
        """Creates an instance of DeleteUserUseCase."""
        return self._composition_root.delete_user_use_case()    
