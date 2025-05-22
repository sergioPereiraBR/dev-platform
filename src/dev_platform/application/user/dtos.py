#   src/dev_platform/application/user/dtos.py
from dataclasses import dataclass


@dataclass
class UserCreateDTO:
    name: str
    email: str
