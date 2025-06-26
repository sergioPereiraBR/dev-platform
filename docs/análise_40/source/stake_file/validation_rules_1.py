from abc import ABC, abstractmethod
from typing import Optional
from dev_platform.domain.user.entities import User

class ValidationRule(ABC):
    """Base class for validation rules."""

    @abstractmethod
    async def validate(self, user: User) -> Optional[str]:
        """
        Validate user according to this rule.
        Returns None if valid, error message if invalid.
        """
        pass

    @property
    @abstractmethod
    def rule_name(self) -> str:
        pass