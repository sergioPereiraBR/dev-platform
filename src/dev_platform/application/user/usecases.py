#   src/dev_platform/application/user/usecases.py
from typing import List
from domain.user.entities import User
from domain.user.interfaces import UserRepository
from application.user.dtos import UserCreateDTO  #   New DTO
from shared.exceptions import DomainException
from shared.logging import logger

class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, user_create_dto: UserCreateDTO) -> User:  #   Using DTO
        try:
            logger.info("Creating user", name=user_create_dto.name, email=user_create_dto.email)
            user = User(id=None, name=user_create_dto.name, email=user_create_dto.email)
            user.validate()
            saved_user = self.user_repository.save(user)
            logger.info("User created successfully", user_id=saved_user.id)
            return saved_user
        except ValueError as e:
            logger.error("Domain validation error", error=str(e))
            raise DomainException(str(e))

class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self) -> List[User]:
        logger.info("List user all")
        return self.user_repository.find_all()
    