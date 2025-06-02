#   src/dev_platform/application/user/dtos.py
from pydantic import BaseModel, validator


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
