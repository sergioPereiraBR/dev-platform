#   src/dev_platform/domain/user/entities.py
from dataclasses import dataclass
from typing import Optional

from domain.user.validators import UserValidationService


@dataclass
class User:
    id: Optional[int]
    name: str
    email: str

    def validate(self):
        UserValidationService.validate_user(self.name, self.email)
