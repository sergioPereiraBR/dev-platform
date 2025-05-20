#   src/dev_platform/domain/user/entities.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: Optional[int]
    name: str
    email: str

    def validate(self):
        if not self.name or len(self.name) < 3:
            raise ValueError("Name must be at least 3 characters long")
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email format")