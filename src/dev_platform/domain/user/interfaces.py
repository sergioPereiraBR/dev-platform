#./src/dev_platform/domain/user/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional
from dev_platform.domain.user.entities import User
from dev_platform.domain.user.value_objects import Email


class IUserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[User]:
        pass
    
    @abstractmethod
    async def find_all(self) -> List[User]:
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        pass
    
    @abstractmethod
    async def find_by_name_contains(self, name_part: str) -> List[User]:
        pass
    
    @abstractmethod
    async def count(self) -> int:
        pass
