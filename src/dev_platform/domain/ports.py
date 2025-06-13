# ./src/dev_platform/domain/ports.py
from abc import ABC, abstractmethod
from typing import Optional, List
from dev_platform.domain.user.entities import User
from dev_platform.domain.user.value_objects import Email

class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_email(self, email: Email) -> Optional[User]:
        pass

    @abstractmethod
    def add(self, user: User) -> None:
        pass

    @abstractmethod
    def update(self, user: User) -> None:
        pass

    @abstractmethod
    def delete(self, user: User) -> None:
        pass

class EmailService(ABC):
    @abstractmethod
    def send_email(self, recipient: Email, subject: str, body: str) -> bool:
        pass