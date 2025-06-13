# ./src/dev_platform/application/user/dtos.py
from pydantic import BaseModel, StrictStr, field_validator


class UserDTO(BaseModel):
    id: StrictStr
    name: StrictStr
    email: StrictStr

    @classmethod
    def from_entity(cls, entity):
        return cls(id=str(entity.id), name=entity.name.value, email=entity.email.value)

    def to_entity(self):
        from dev_platform.domain.user.entities import (
            User,
        )  # Importar aqui para evitar dependência circular

        return User.create(name=self.name, email=self.email)


class UserCreateDTO(BaseModel):
    name: StrictStr
    email: StrictStr

    @field_validator("name")
    def validate_name(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Precisar ser um nome, o campo não pode ficar vazio")
        return v.strip()

    @field_validator("email")
    def validate_email(cls, v):
        # Validação básica antes de criar Value Object
        if not v or len(v) == 0:
            raise ValueError("Precisar ser um e-mail")
        return v.lower().strip()


class UserUpdateDTO(BaseModel):
    name: StrictStr
    email: StrictStr

    @field_validator("name")
    def validate_name(cls, v):
        return v.strip()

    @field_validator("email")
    def validate_email(cls, v):
        return v.lower().strip()
