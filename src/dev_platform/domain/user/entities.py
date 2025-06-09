# ./src/dev_platform/domain/user/entities.py
from dataclasses import dataclass
from typing import Optional
from dev_platform.domain.user.value_objects import Email, UserName


@dataclass(frozen=True)
class User:
    id: Optional[int]
    name: UserName
    email: Email

    @classmethod
    def create(cls, name: str, email: str) -> "User":
        return cls(id=None, name=UserName(name), email=Email(email))

    def with_id(self, new_id: int) -> "User":
        return User(new_id, self.name, self.email)
