# ./src/dev_platform/application/user/dtos.py
from pydantic import BaseModel, StrictStr, field_validator

class UserDTO(BaseModel):
    """
    Data Transfer Object for User entity.
    """
    id: StrictStr
    name: StrictStr
    email: StrictStr

    @classmethod
    def from_entity(cls, entity):
        """
        Cria um UserDTO a partir de uma entidade User.
        """
        return cls(id=str(entity.id), name=entity.name.value, email=entity.email.value)

    def to_entity(self):
        """
        Converte o UserDTO de volta para uma entidade User.
        """
        from dev_platform.domain.user.entities import User  # Importar aqui para evitar dependência circular
        return User.create(name=self.name, email=self.email)

    class Config:
        """
        Configurações do Pydantic para o DTO.
        """
        from_attributes = True

class UserCreateDTO(BaseModel):
    """
    Data Transfer Object for creating a new User.
    """
    name: StrictStr
    email: StrictStr

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
    email: StrictStr

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
