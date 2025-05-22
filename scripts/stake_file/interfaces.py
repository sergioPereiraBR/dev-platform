#   src/dev_platform/domain/user/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.user.entities import User

class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def find_all(self) -> List[User]:
        pass

class AsyncUserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def find_all(self) -> List[User]:
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass
