#   src/dev_platform/domain/user/entities.py
from dataclasses import dataclass
from typing import Optional
from domain.user.value_objects import Email, UserName

@dataclass
class User:
    id: Optional[int]
    name: UserName
    email: Email
    
    @classmethod
    def create(cls, name: str, email: str) -> 'User':
        return cls(
            id=None,
            name=UserName(name),
            email=Email(email)
        )
