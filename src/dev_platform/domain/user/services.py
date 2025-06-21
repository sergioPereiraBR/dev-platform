# ./src/dev_platform/domain/user/services.py
# -*- coding: utf-8 -*-
"""
Este módulo define os serviços de domínio relacionados à entidade User.
Os serviços são responsáveis por validações complexas, regras de negócio e operações
com usuários.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
import re
from datetime import datetime
from dev_platform.domain.user.interfaces import IUserRepository 
from dev_platform.domain.user.entities import User
from dev_platform.domain.exceptions import DatabaseException
from dev_platform.domain.user.user_exceptions import (
    UserValidationException,
    UserAlreadyExistsException,
    UserNotFoundException,
    EmailDomainNotAllowedException,
)

# --- Regras de validação devem ser extraídas para um módulo próprio (ex: validation_rules.py) ---
# Aqui mantemos apenas a interface base para uso no domínio.

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

# --- Serviço de domínio focado apenas na lógica de negócio ---

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
    Service for complex user domain validations and business rules.
    Recebe explicitamente as regras de validação a serem aplicadas.
    """

    def __init__(self, validation_rules: List[ValidationRule]): 
        self._validation_rules = validation_rules 
    
    def __init__(self, user_repository: IUserRepository, validation_rules: List[ValidationRule]):
        self._repository = user_repository
        self._validation_rules = validation_rules

    async def create_user(self, user: User) -> User:
        """
        Creates a new user, ensuring all domain rules, including
        uniqueness, are met.
        """
        # 1. Verifica unicidade como parte da operação de criação
        existing = await self._repository.find_by_email(user.email.value)
        if existing:
            raise UserAlreadyExistsException(user.email.value)
        # 2. Valida outras regras de negócio
        await self.validate_business_rules(user)
        # 3. Persiste o usuário
        saved_user = await self._repository.add(user)
        return saved_user

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
        Validate all business rules for a user.
        Raises UserValidationException if any rule fails.
        """
        validation_errors = {}

        # Run all validation rules
        for rule in self._validation_rules:
            try:
                error_message = await rule.validate(user)
                if error_message:
                    validation_errors[rule.rule_name] = error_message
            except Exception as e:
                validation_errors[rule.rule_name] = f"Validation rule failed: {str(e)}"

        # If there are validation errors, raise exception
        if validation_errors:
            raise UserValidationException(validation_errors)

    async def validate_user_update(self, user_id: int, updated_user: User) -> None:
        """
        Validate user update, checking uniqueness only if email changed.
        """
        validation_errors = {}

        # Get current user
        # current_user = await self._repository.find_by_id(user_id)
        # if not current_user:
        #     raise UserNotFoundException(str(user_id))

        # Check email uniqueness only if email changed
        # if current_user.email.value != updated_user.email.value:
        #     try:
        #         await self._uniqueness_service.ensure_email_is_unique(updated_user.email.value)
        #     except UserAlreadyExistsException as e:
        #         validation_errors["email"] = e.message

        # Run validation rules
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
