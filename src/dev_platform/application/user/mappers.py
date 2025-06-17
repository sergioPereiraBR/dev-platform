# ./src/dev_platform/application/user/mappers.py
from dev_platform.domain.user.entities import User
from dev_platform.application.user.dtos import UserDTO, UserCreateDTO, UserUpdateDTO
from typing import List

def user_to_dto(user: User) -> UserDTO:
    return UserDTO(id=str(user.id), name=user.name.value, email=user.email.value)

def dto_to_user(dto: UserDTO) -> User:
    return User.create(name=dto.name, email=dto.email)

def create_dto_to_user(dto: UserCreateDTO) -> User:
    return User.create(name=dto.name, email=dto.email)

def update_dto_to_user(user_id: str, dto: UserUpdateDTO) -> User:
    # Supondo que User.create aceita id como argumento opcional
    return User.create(id=user_id, name=dto.name, email=dto.email)

def users_to_dtos(users: List[User]) -> List[UserDTO]:
    return [user_to_dto(user) for user in users]

# Para get, basta usar user_to_dto
# Para delete, normalmente só o id é necessário, não precisa de conversão extra