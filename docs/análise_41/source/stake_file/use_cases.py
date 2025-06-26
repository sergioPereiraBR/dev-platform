# ./src/dev_platform/application/user/use_cases.py
# -*- coding: utf-8 -*-
"""
Este módulo define os casos de uso para a entidade User,
encapsulando a lógica de negócios e as interações com os repositórios.
"""

from typing import List

from dev_platform.application.user.dtos import UserCreateDTO, UserUpdateDTO, UserDTO
from dev_platform.domain.user.entities import User
from dev_platform.application.ports.logger import ILogger
from dev_platform.application.user.ports import UnitOfWork
from dev_platform.domain.exceptions import DatabaseException
from dev_platform.domain.user.user_exceptions import (
    UserValidationException,
    UserAlreadyExistsException,
    UserNotFoundException
)
from dev_platform.domain.user.services import UserDomainService, UserUniquenessService, UserValidatorService

# Função Helper para vonversão do entity para DTO
def user_to_dto(user: User) -> UserDTO:
    return UserDTO(
        id=str(user.id),
        name=user.name.value if hasattr(user.name, "value") else user.name,
        email=user.email.value if hasattr(user.email, "value") else user.email,
    )

class BaseUseCase:
    """Base class for all use cases, providing access to Unit of Work and logger."""
    def __init__(self, uow: UnitOfWork, logger: ILogger):
        self._uow = uow
        self._logger = logger

class CreateUserUseCase(BaseUseCase):
    """Caso de uso para criar um novo usuário."""
    def __init__(
        self,
        uow: UnitOfWork, 
        logger: ILogger,
        user_validator: UserValidatorService,
        user_uniqueness_service: UserUniquenessService,
    ):
        super().__init__(uow, logger)
        self._user_validator = user_validator
        self._user_uniqueness_service = user_uniqueness_service

    async def execute(self, dto: UserCreateDTO) -> UserDTO:
        # Solução: O 'async with' é movido para cá, encapsulando a transação.
        async with self._uow:
            self._logger.info("Iniciando criação de usuário", name=dto.name, email=dto.email)
            # O bloco try/except original agora fica dentro do 'async with'.
            # O rollback é tratado automaticamente pelo __aexit__ da UoW em caso de exceção.
            try:               
                await self._user_uniqueness_service.ensure_email_is_unique(dto.email)
                user_to_create = User.create(name=dto.name, email=dto.email)
                await self._user_validator.validate(user_to_create)

                saved_user = await self._uow.user_repository.add(user_to_create)
                # O commit agora é explícito dentro do bloco de sucesso.
                await self._uow.commit()
                self._logger.info(
                    "Usuário criado com sucesso",
                    user_id=saved_user.id,
                    name=saved_user.name.value if hasattr(saved_user.name, "value") else saved_user.name,
                    email=saved_user.email.value if hasattr(saved_user.email, "value") else saved_user.email,
                )
                return user_to_dto(saved_user)
            except UserAlreadyExistsException as e:
                await self._uow.rollback()
                self._logger.warning(
                    "Validação de domínio tentou criar usuário duplicado", email=dto.email
                )
                raise
            except UserValidationException as e:
                await self._uow.rollback()
                self._logger.warning(
					"Validação de regras de negócio falhou", validation_errors=e.validation_errors
				)
                raise
            except Exception as e:
                await self._uow.rollback()
                self._logger.error(
                    "Erro inesperado durante a criação do usuário",
                    error=str(e),
                )
                raise

class ListUsersUseCase(BaseUseCase): 
    """Use case for listing all users."""  
    async def execute(self) -> List[UserDTO]:
        async with self._uow:
            try:
                self._logger.info("Starting user listing")
                users = await self._uow.user_repository.find_all()
                self._logger.info("Users retrieved successfully", count=len(users))
                return [user_to_dto(user) for user in users]
            except UserNotFoundException:
                self._logger.error("User not found")
                raise
            except Exception as e:
                self._logger.error("Erro inesperado durante a listagem de usuário", error=str(e))
                raise

class UpdateUserUseCase(BaseUseCase):
    """Use case for updating an existing user."""
    def __init__(
        self,
        uow: UnitOfWork,
        logger: ILogger,
        domain_service: UserDomainService,
    ):
        super().__init__(uow, logger)
        self._domain_service = domain_service

    async def execute(self, user_id: int, dto: UserUpdateDTO) -> UserDTO:
        async with self._uow:
            self._logger.set_correlation_id()
            self._logger.info(
                "Starting user update", user_id=user_id, update_data=dto.model_dump()
            )
            try:
                existing_user = await self._uow.user_repository.find_by_id(user_id)
                if not existing_user:
                    self._logger.error("User not found for update", user_id=user_id)
                    raise UserNotFoundException(str(user_id))
                
                new_name = dto.name if dto.name is not None else existing_user.name.value
                new_email = dto.email if dto.email is not None else existing_user.email.value
                updated_user = existing_user.update_details(new_name, new_email)

                saved_user = await self._uow.user_repository.update(updated_user)
                await self._uow.commit()
                saved_user_dto = user_to_dto(saved_user)
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
            except Exception as e:
                self._logger.error(
                    "Domain error during user update",
                    user_id=user_id,
                    error=str(e),
                )
                raise

class GetUserUseCase(BaseUseCase):
    """Use case for retrieving a user by ID."""
    async def execute(self, user_id: int) -> UserDTO:
        async with self._uow:
            try:
                self._logger.info("Getting user", user_id=user_id)
                user = await self._uow.user_repository.find_by_id(user_id)
                if not user:
                    self._logger.error("User not found", user_id=user_id)
                    raise UserNotFoundException(str(user_id))
                self._logger.info("User retrieved successfully", user_id=user_id)
                return user_to_dto(user)
            except UserNotFoundException:
                self._logger.error("User not found", user_id=user_id)
                raise

class DeleteUserUseCase(BaseUseCase):
    """Use case for deleting a user by ID."""
    async def execute(self, user_id: int) -> bool:
        async with self._uow:
            try:
                self._logger.info("Starting user deletion", user_id=user_id)
                existing_user = await self._uow.user_repository.find_by_id(user_id)
                if not existing_user:
                    self._logger.error("User not found for deletion", user_id=user_id)
                    raise UserNotFoundException(str(user_id))
                success = await self._uow.user_repository.delete(user_id)
                if success:
                    await self._uow.commit()
                    self._logger.info("User deleted successfully", user_id=user_id)
                else:
                    self._logger.warning("User deletion failed", user_id=user_id)
                return success
            except UserNotFoundException:
                self._logger.error("User not found for deletion", user_id=user_id)
                raise
            except Exception as e:
                self._logger.error(
                    "Domain error during user deletion",
                    user_id=user_id,
                    error=str(e),
                )
                raise
