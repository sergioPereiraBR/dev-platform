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
from dev_platform.domain.user.user_exceptions import (
    UserValidationException,
    UserAlreadyExistsException,
    UserNotFoundException
)
from dev_platform.domain.user.services import UserUniquenessService, UserValidatorService
from dev_platform.application.user.mappers import UserMapper


class BaseUseCase:
    """Base class for all use cases, providing access to Unit of Work and logger."""
    def __init__(self, uow: UnitOfWork, logger: ILogger, mapper: UserMapper):
        self._uow = uow
        self._logger = logger
        self._mapper = mapper

class CreateUserUseCase(BaseUseCase):
    """Caso de uso para criar um novo usuário."""
    def __init__(
        self,
        uow: UnitOfWork, 
        logger: ILogger,
        mapper: UserMapper,
        user_validator: UserValidatorService,
        user_uniqueness_service: UserUniquenessService,
    ):
        super().__init__(uow, logger, mapper)
        self._user_validator = user_validator
        self._user_uniqueness_service = user_uniqueness_service

    async def execute(self, dto: UserCreateDTO) -> UserDTO:
        # O 'async with' gerencia a transação automaticamente.
        # O rollback é implícito em caso de exceção, e o commit é implícito em caso de sucesso.
        async with self._uow:
            try:  
                self._logger.info("Iniciando criação de usuário (UC).", name=dto.name, email=dto.email)             
                await self._user_uniqueness_service.ensure_email_is_unique(dto.email)
                user_to_create = User.create(name=dto.name, email=dto.email)
                await self._user_validator.validate(user_to_create)
                saved_user = await self._uow.user_repository.add(user_to_create)
                self._logger.info(
                    "Usuário criado com sucesso (UC).",
                    user_id=saved_user.id,
                )
                return self._mapper.to_dto(saved_user)
            except (UserAlreadyExistsException, UserValidationException) as e:
                self._logger.warning(
                    "Falha ao validar as regras de negócio na criação do usuário. A transação será revertida (UC).",
                    error=str(e)
                )
                raise # A UoW cuidará do rollback ao capturar a exceção.
            except Exception as e:
                self._logger.error(
                    "Erro inesperado durante a criação do usuário. A transação será revertida (UC).",
                    error=str(e),
                )
                raise

class ListUsersUseCase(BaseUseCase): 
    """Use case for listing all users."""  
    async def execute(self) -> List[UserDTO]:
        async with self._uow:
            try:
                self._logger.info("Starting user listing (UCL).")
                users = await self._uow.user_repository.find_all()
                self._logger.info("Users retrieved successfully (UCL).", count=len(users))
                return [self._mapper.to_dto(user) for user in users]
            except UserNotFoundException:
                self._logger.error("User not found (UCL).")
                raise
            except Exception as e:
                self._logger.error("Erro inesperado durante a listagem de usuário (UCL).", error=str(e))
                raise

class UpdateUserUseCase(BaseUseCase):
    """Use case for updating an existing user."""
    def __init__(
        self,
        uow: UnitOfWork,
        logger: ILogger,
        mapper: UserMapper,
        user_validator: UserValidatorService,
        user_uniqueness_service: UserUniquenessService,
    ):
        super().__init__(uow, logger, mapper)
        self._user_validator = user_validator
        self._user_uniqueness_service = user_uniqueness_service

    async def execute(self, user_id: int, dto: UserUpdateDTO) -> UserDTO:
        async with self._uow:
            self._logger.set_correlation_id()
            self._logger.info(
                "Starting user update (UC).", user_id=user_id, update_data=dto.model_dump()
            )
            try:
                existing_user = await self._uow.user_repository.find_by_id(user_id)
                if not existing_user:
                    self._logger.error("User not found for update (UC).", user_id=user_id)
                    raise UserNotFoundException(str(user_id))
                
                new_name = dto.name if dto.name is not None else existing_user.name.value
                new_email = dto.email if dto.email is not None else existing_user.email.value

                # Verifica se o e-mail foi alterado para acionar a validação de unicidade
                if new_email.lower() != existing_user.email.value.lower():
                    await self._user_uniqueness_service.ensure_email_is_unique(
                        new_email, exclude_user_id=existing_user.id
                    )

                updated_user = existing_user.update_details(new_name, new_email)

                # Valida a entidade atualizada com as regras de negócio
                await self._user_validator.validate(updated_user)

                saved_user = await self._uow.user_repository.update(updated_user)
                saved_user_dto = self._mapper.to_dto(saved_user)
                self._logger.info(
                    "User updated successfully (UC).",
                    user_id=saved_user_dto.id,
                    name=saved_user_dto.name,
                    email=saved_user_dto.email,
                )
                return saved_user_dto
            except (UserValidationException, UserNotFoundException) as e:
                if isinstance(e, UserValidationException):
                    self._logger.error(
                        "User update validation failed (UC).",
                        user_id=user_id,
                        validation_errors=e.validation_errors,
                    )
                else:
                    self._logger.error("User not found for update (UC).", user_id=user_id)
                raise
            except Exception as e:
                self._logger.error(
                    "Domain error during user update (UC).",
                    user_id=user_id,
                    error=str(e),
                )
                raise

class GetUserUseCase(BaseUseCase):
    """Use case for retrieving a user by ID."""
    async def execute(self, user_id: int) -> UserDTO:
        async with self._uow:
            try:
                self._logger.info("Getting user (UC).", user_id=user_id)
                user = await self._uow.user_repository.find_by_id(user_id)
                if not user:
                    self._logger.error("User not found (UC).", user_id=user_id)
                    raise UserNotFoundException(str(user_id))
                self._logger.info("User retrieved successfully (UC).", user_id=user_id)
                return self._mapper.to_dto(user)
            except UserNotFoundException:
                self._logger.error("User not found (UC).", user_id=user_id)
                raise

class DeleteUserUseCase(BaseUseCase):
    """Use case for deleting a user by ID."""
    async def execute(self, user_id: int) -> bool:
        async with self._uow:
            try:
                self._logger.info("Starting user deletion (UC).", user_id=user_id)
                existing_user = await self._uow.user_repository.find_by_id(user_id)
                if not existing_user:
                    self._logger.error("User not found for deletion (UC).", user_id=user_id)
                    raise UserNotFoundException(str(user_id))
                success = await self._uow.user_repository.delete(user_id)
                if success:
                    self._logger.info("User deleted successfully (UC).", user_id=user_id)
                else:
                    self._logger.warning("User deletion failed (UC).", user_id=user_id)
                return success
            except UserNotFoundException:
                self._logger.error("User not found for deletion (UC).", user_id=user_id)
                raise
            except Exception as e:
                self._logger.error(
                    "Domain error during user deletion (UC).",
                    user_id=user_id,
                    error=str(e),
                )
                raise
