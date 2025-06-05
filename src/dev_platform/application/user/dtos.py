# src/dev_platform/application/user/dtos.py
from pydantic import BaseModel, validator, validate_arguments, StrictStr


class UserDTO(BaseModel):
    id: str
    name: StrictStr
    email: StrictStr

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=str(entity.id),
            name=entity.name.value,
            email=entity.email.value
        )
    
    def to_entity(self):
        from domain.user.entities import User  # Importar aqui para evitar dependência circular
        return User.create(name=self.name, email=self.email)

class UserCreateDTO(BaseModel):
    name: StrictStr
    email: StrictStr

    def validate_name(cls, v):
        return v.strip()
    
    def validate_email(cls, v):
        # Validação básica antes de criar Value Object
        return v.lower().strip()
    
class UserUpdateDTO(BaseModel):
    name: StrictStr
    email: StrictStr

    def validate_name(cls, v):
        return v.strip()

    def validate_email(cls, v):
        # Validação básica antes de criar Value Object
        return v.lower().strip()
