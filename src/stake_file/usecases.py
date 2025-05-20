#   src/dev_platform/application/user/usecases.py
from typing import List
from domain.user.entities import User
from domain.user.interfaces import UserRepository
from application.user.dtos import UserCreateDTO  #   New DTO
from shared.exceptions import DomainException

class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, user_create_dto: UserCreateDTO) -> User:  #   Using DTO
        try:
            user = User(id=None, name=user_create_dto.name, email=user_create_dto.email)
            user.validate()
            return self.user_repository.save(user)
        except ValueError as e:
            raise DomainException(str(e))

class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self) -> List[User]:
        return self.user_repository.find_all()
    