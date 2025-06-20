# ./src/dev_platform/application/user/dtos.py
# -*- coding: utf-8 -*-
"""
Este módulo define os Data Transfer Objects (DTOs) para a entidade User,
permitindo a transferência de dados entre camadas da aplicação.
"""

from typing import Optional
from pydantic import BaseModel, StrictStr, EmailStr, field_validator

class UserDTO(BaseModel):
    """
    Data Transfer Object for User entity.
    """
    id: StrictStr
    name: StrictStr
    email: StrictStr

    class Config:
        """
        Configurações do Pydantic para o DTO.
        """
        from_attributes = True

class UserCreateDTO(BaseModel):
    """
    Data Transfer Object for creating a new User.
    """
    name: Optional[StrictStr] = None
    email: Optional[EmailStr] = None


    @field_validator("name", mode="before")
    def validate_name(cls, v):
        """
        Valida o nome do usuário.
        """
        if not v or len(v) == 0:
            raise ValueError("Precisa ser um nome, o campo não pode ficar vazio")
        return v.strip()

    @field_validator("email", mode="before")
    def validate_email(cls, v):
        """
        Valida o e-mail do usuário.
        """
        if not v or len(v) == 0:
            raise ValueError("Precisa ser um e-mail")
        return v.lower().strip()

    class Config:
        """
        Configurações do Pydantic para o DTO de criação.
        """
        from_attributes = True

class UserUpdateDTO(BaseModel):
    """
    Data Transfer Object for updating an existing User.
    """
    name: StrictStr
    email: EmailStr

    @field_validator("name", mode="before")
    def validate_name(cls, v):
        """
        Valida o nome do usuário para atualização.
        """
        return v.strip()

    @field_validator("email", mode="before")
    def validate_email(cls, v):
        """
        Valida o e-mail do usuário para atualização.
        """
        return v.lower().strip()

    class Config:
        """
        Configurações do Pydantic para o DTO de atualização.
        """
        from_attributes = True
