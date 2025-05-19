#   src/domain/user/interfaces.py
from abc import ABC, abstractmethod
from typing import List
from domain.user.entities import User

class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def find_all(self) -> List[User]:
        pass