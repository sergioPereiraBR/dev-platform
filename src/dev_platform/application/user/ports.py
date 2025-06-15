# ./src/dev_platform/application/user/ports.py
from abc import ABC, abstractmethod

from dev_platform.domain.user.interfaces import IUserRepository


class UnitOfWork(ABC):
    """
    Interface for the Unit of Work pattern.
    """
    users: IUserRepository

    @abstractmethod
    async def __aenter__(self):
        """Enter the context of the unit of work."""
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context of the unit of work."""
        raise NotImplementedError

    @abstractmethod
    async def commit(self):
        """Commit the changes made during the unit of work."""
        raise NotImplementedError
