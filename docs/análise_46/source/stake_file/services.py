# ./src/dev_platform/domain/user/services.py
# -*- coding: utf-8 -*-
"""
Este módulo define os serviços de domínio relacionados à entidade User.
Os serviços são responsáveis por validações complexas, regras de negócio e operações
com usuários.
"""

from typing import List, Dict, Optional
from dev_platform.domain.user.interfaces import IUserRepository 
from dev_platform.domain.user.entities import User
from dev_platform.domain.exceptions import DatabaseException
from dev_platform.domain.user.user_exceptions import (
    UserValidationException,
    UserAlreadyExistsException,
    EmailDomainNotAllowedException,
)
from dev_platform.domain.user.validation_rules import ValidationRule


class UserValidatorService:
    """
    Serviço focado em validação de regras de negócio para User.
    Para utilizar pode ser necessário importar UserType
    """
    def __init__(self, validation_rules: List[ValidationRule]):
        self._validation_rules: List[ValidationRule] = validation_rules

    async def validate(self, user: User) -> None:
        validation_errors: dict = {}
        for rule in self._validation_rules:
            error_message = await rule.validate(user)
            if error_message:
                validation_errors[rule.rule_name] = error_message
        if validation_errors:
            raise UserValidationException(validation_errors)


class UserUniquenessService:
    """Service focused on uniqueness validation."""

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository

    async def ensure_email_is_unique(
        self, email: str, exclude_user_id: Optional[int] = None
    ) -> None:
        existing_user = await self._repository.find_by_email(email)
        if existing_user and (
            exclude_user_id is None or existing_user.id != exclude_user_id
        ):
            raise UserAlreadyExistsException(email)


class UserAnalyticsService:
    """Service for user analytics and reporting."""

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository

    async def get_user_statistics(self) -> Dict[str, int]:
        """Get basic user statistics."""
        try:
            total_users = await self._repository.count()
            return {
                "total_users": total_users,
            }
        except Exception as e:
            raise DatabaseException("count", str(e), e)

    async def find_users_by_domain(self, domain: str) -> List[User]:
        """Find all users with emails from a specific domain."""
        try:
            all_users = await self._repository.find_all()
            return [
                user
                for user in all_users
                if user.email.value.split("@")[1].lower() == domain.lower()
            ]
        except Exception as e:
            raise DatabaseException("find_all", str(e), e)
