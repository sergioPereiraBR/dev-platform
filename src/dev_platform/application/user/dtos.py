#   src/dev_platform/application/user/dtos.py
from pydantic import BaseModel, validator


class UserDTO(BaseModel):
    id: str
    name: str
    email: str

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
    name: str
    email: str

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Name must be at least 3 characters')
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        # Validação básica antes de criar Value Object
        return v.lower().strip()
    
class UserUpdateDTO(BaseModel):
    name: str
    email: str

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Name must be at least 3 characters')
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        # Validação básica antes de criar Value Object
        return v.lower().strip()
