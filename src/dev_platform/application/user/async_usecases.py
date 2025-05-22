# src/dev_platform/application/user/async_usecases.py
from typing import List
from domain.user.entities import User
from domain.user.interfaces import AsyncUserRepository
from application.user.dtos import UserCreateDTO
from shared.exceptions import DomainException
from shared.logging import logger


class AsyncCreateUserUseCase:
    def __init__(self, user_repository: AsyncUserRepository):
        self.user_repository = user_repository

    async def execute(self, user_create_dto: UserCreateDTO) -> User:
        try:
            logger.info("Creating user", name=user_create_dto.name, email=user_create_dto.email)
            user = User(id=None, name=user_create_dto.name, email=user_create_dto.email)
            user.validate()
            saved_user = await self.user_repository.save(user)  # ✅ AWAIT adicionado
            logger.info("User created successfully", user_id=saved_user.id)
            return saved_user
        except ValueError as e:
            logger.error("Domain validation error", error=str(e))
            raise DomainException(str(e))


class AsyncListUsersUseCase:
    def __init__(self, user_repository: AsyncUserRepository):
        self.user_repository = user_repository

    async def execute(self) -> List[User]:
        logger.info("List user all")
        return await self.user_repository.find_all()  # ✅ AWAIT adicionado