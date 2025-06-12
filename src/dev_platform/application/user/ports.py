# ./src/dev_platform/application/user/ports.py
from abc import ABC, abstractmethod
from typing import List, Optional
from dev_platform.domain.user.entities import User
from dev_platform.domain.user.interfaces import UserRepository


class UnitOfWork(ABC):
    users: UserRepository

    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def commit(self):
        pass

class Logger(ABC):
    @abstractmethod
    def info(self, message: str, **kwargs):
        pass

    @abstractmethod
    def error(self, message: str, **kwargs):
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs):
        pass
