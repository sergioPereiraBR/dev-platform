# src/dev_platform/application/user/use_cases.py#
from typing import List
from application.user.ports import Logger, UnitOfWork
from application.user.dtos import UserCreateDTO
from domain.user.entities import User

class CreateUserUseCase:
    def __init__(self, uow: UnitOfWork, logger: Logger):
        self._uow = uow
        self._logger = logger
    
    async def execute(self, dto: UserCreateDTO) -> User:
        async with self._uow:
            self._logger.info("Creating user", name=dto.name, email=dto.email)
            
            # Verifica se já existe
            existing = await self._uow.users.find_by_email(dto.email)
            if existing:
                raise ValueError("User with this email already exists")
            
            # Cria e valida
            user = User(id=None, name=dto.name, email=dto.email)
            user.validate()
            
            # Salva
            saved_user = await self._uow.users.save(user)
            await self._uow.commit()
            
            self._logger.info("User created", user_id=saved_user.id)
            return saved_user

class ListUsersUseCase:
    def __init__(self, uow: UnitOfWork, logger: Logger):
        self._uow = uow
        self._logger = logger
    
    async def execute(self) -> List[User]:
        async with self._uow:
            self._logger.info("Listing all users")
            users = await self._uow.users.find_all()
            self._logger.info("Found users", count=len(users))
            return users
