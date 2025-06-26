# ./src/dev_platform/application/user/mappers.py
# -*- coding: utf-8 -*-
"""
Este módulo define os mapeadores para converter entre entidades User e seus Data Transfer Objects (DTOs),
permitindo a transferência de dados entre camadas da aplicação.
"""

from dev_platform.domain.user.entities import User
from dev_platform.application.user.dtos import UserDTO
from typing import List


class UserMapper:
    """Componente responsável por mapear entre Entidades User e DTOs."""

    def to_dto(self, user: User) -> UserDTO:
        """Converte uma entidade User para UserDTO."""
        return UserDTO(id=str(user.id), name=user.name.value, email=user.email.value)

    def to_dtos(self, users: List[User]) -> List[UserDTO]:
        """Converte uma lista de entidades User para uma lista de UserDTOs."""
        return [self.to_dto(user) for user in users]

    def to_user(dto: UserDTO) -> User:
        return User.create(name=dto.name, email=dto.email)


    # Para get, basta usar user_to_dto
    # Para delete, normalmente só o id é necessário, não precisa de conversão extra