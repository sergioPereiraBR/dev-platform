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
    """Serviço focado em validação de regras de negócio para User."""
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

class UserDomainService:
    """
    Serviço de domínio para validações complexas de domínio de usuário e regras de negócio.
    Recebe explicitamente as regras de validação a serem aplicadas.
    """

    def __init__(self, validation_rules: List[ValidationRule], user_repository: IUserRepository):
        self._validation_rules: List[ValidationRule] = validation_rules
        self._repository = user_repository

    def add_validation_rule(self, rule: ValidationRule):
        """Add a custom validation rule."""
        self._validation_rules.append(rule)

    def remove_validation_rule(self, rule_name: str):
        """Remove a validation rule by name."""
        self._validation_rules = [
            rule for rule in self._validation_rules if rule.rule_name != rule_name
        ]

    async def validate_business_rules(self, user: User) -> None:
        """
        Valida todas as regras de negócio para um usuário.
        Levanta UserValidationException se alguma regra falhar.
        """
        validation_errors = {}
        for rule in self._validation_rules:
            error_message = await rule.validate(user)
            if error_message:
                validation_errors[rule.rule_name] = error_message
        if validation_errors:
            raise UserValidationException(validation_errors)

    async def validate_user_update(self, user_id: int, updated_user: User) -> None:
        """
        Validate user update, checking uniqueness only if email changed.
        """
        validation_errors = {}
        for rule in self._validation_rules:
            try:
                error_message = await rule.validate(updated_user)
                if error_message:
                    validation_errors[rule.rule_name] = error_message
            except Exception as e:
                validation_errors[rule.rule_name] = f"Validation rule failed: {str(e)}"
        if validation_errors:
            raise UserValidationException(validation_errors)

    def get_validation_summary(self) -> Dict[str, str]:
        """Get summary of all active validation rules."""
        return {
            rule.rule_name: rule.__class__.__doc__ or "No description available"
            for rule in self._validation_rules
        }

    async def validate_user_creation_constraints(self, user: User) -> None:
        """
        Validate constraints specific to user creation.
        (Exemplo: limite de usuários, regras de negócio específicas)
        """
        validation_errors = {}
        try:
            current_count = await self._repository.count()
            if current_count >= 10000:  # Exemplo de limite
                validation_errors["system_limit"] = "Maximum number of users reached"
        except Exception as e:
            validation_errors["system_check"] = f"Unable to verify system constraints: {str(e)}"
        if validation_errors:
            raise UserValidationException(validation_errors)

    async def validate_business_domain_rules(
        self, user: User, domain_whitelist: Optional[List[str]] = None
    ) -> None:
        """
        Validate business-specific domain rules.
        """
        if domain_whitelist:
            email_domain = user.email.value.split("@")[1].lower()
            if email_domain not in [d.lower() for d in domain_whitelist]:
                raise EmailDomainNotAllowedException(
                    user.email.value, email_domain, domain_whitelist
                )

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
