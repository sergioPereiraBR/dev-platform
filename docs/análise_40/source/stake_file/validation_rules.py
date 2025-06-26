# ./src/dev_platform/domain/validation_rules.py
# -*- coding: utf-8 -*-
"""
Este módulo contém regras de validação para diversas operações no domínio de usuários.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Set
import re
from datetime import datetime
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


class EmailFormatAdvancedValidationRule(ValidationRule):
    """Advanced email format validation beyond basic regex."""

    def __init__(self):
        self.pattern = re.compile(
            r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$"
        )

    async def validate(self, user: User) -> Optional[str]:
        email = user.email.value

        if not self.pattern.match(email):
            return "Email format is invalid"

        if ".." in email:
            return "Email cannot contain consecutive dots"

        if len(email) > 254:
            return "Email is too long (max 254 characters)"

        local_part, domain_part = email.split("@")

        if len(local_part) > 64:
            return "Email local part is too long (max 64 characters)"

        if len(domain_part) > 253:
            return "Email domain part is too long (max 253 characters)"

        return None

    @property
    def rule_name(self) -> str:
        return "email_format_advanced_validation"


class NameContentValidationRule(ValidationRule):
    """Validates name content and format."""

    def __init__(self, allowed_chars: Optional[Set[str]] = None):
        if allowed_chars is None:
            allowed_chars = set(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ -'àáâãèéêìíîòóôõùúûçÀÁÂÃÈÉÊÌÍÎÒÓÔÕÙÚÛÇ"
            )
        self.allowed_chars = allowed_chars

    async def validate(self, user: User) -> Optional[str]:
        name = user.name.value

        if name.strip() != name:
            return "Name cannot start or end with whitespace"

        if "  " in name:
            return "Name cannot contain consecutive spaces"

        if any(char.isdigit() for char in name):
            return "Name cannot contain numbers"

        if not all(char in self.allowed_chars for char in name):
            invalid_chars = [char for char in name if char not in self.allowed_chars]
            return f"Name contains invalid characters: {', '.join(set(invalid_chars))}"

        words = name.split()
        if len(words) < 2:
            return "Name must contain at least first and last name"

        for word in words:
            if len(word) < 2:
                return "Each name part must be at least 2 characters long"

        return None

    @property
    def rule_name(self) -> str:
        return "name_content_validation"


class EmailDomainValidationRule(ValidationRule):
    """Validates that email domain is in allowed list."""

    def __init__(self, allowed_domains: List[str]):
        self.allowed_domains = set(domain.lower() for domain in allowed_domains)

    async def validate(self, user: User) -> Optional[str]:
        email_domain = user.email.value.split("@")[1].lower()
        if email_domain not in self.allowed_domains:
            return f"Email domain '{email_domain}' is not allowed. Allowed domains: {', '.join(self.allowed_domains)}"
        return None

    @property
    def rule_name(self) -> str:
        return "email_domain_validation"


class ForbiddenWordsValidationRule(ValidationRule):
    """
    Valida se o nome do usuário contém palavras específicas proibidas.
    """

    def __init__(self, forbidden_words: List[str]):
        self.forbidden_words = [word.lower() for word in forbidden_words]

    async def validate(self, user: User) -> Optional[str]:
        for word in self.forbidden_words:
            if word in user.name.value.lower():
                return f"Name contains forbidden word: {word}"
        return None

    @property
    def rule_name(self) -> str:
        return "forbidden_words_validation"


class NameProfanityValidationRule(ValidationRule):
    """
    Valida se o nome do usuário contém palavrões ou termos ofensivos.
    """

    def __init__(self, forbidden_words: List[str]):
        self.forbidden_words = [word.lower() for word in forbidden_words]

    async def validate(self, user: User) -> Optional[str]:
        name_lower = user.name.value.lower()
        for word in self.forbidden_words:
            if word in name_lower:
                return f"Name contains forbidden word: {word}"
        return None

    @property
    def rule_name(self) -> str:
        return "name_profanity_validation"


class IDateTimeProvider(ABC):
    @abstractmethod
    def now(self) -> datetime:
        pass

class SystemDateTimeProvider(IDateTimeProvider):
    def now(self) -> datetime:
        return datetime.now()

class BusinessHoursValidationRule(ValidationRule):
    """
    Regra de validação para verificar se uma operação está dentro do horário comercial permitido.

    Verifica o dia da semana (apenas dias úteis) e as horas (9 AM - 5 PM).

    Exemplo de uso:
        rule = BusinessHoursValidationRule(business_hours_only=True) # Usa o provedor padrão
        rule_test = BusinessHoursValidationRule(business_hours_only=True, datetime_provider=MockDateTimeProvider(specific_time))
    """
    def __init__(self, business_hours_only: bool = False, datetime_provider: IDateTimeProvider = None):
        """
        Inicializa a regra de validação de horário comercial.

        Args:
            business_hours_only (bool): Se True, a validação de horário comercial será aplicada.
                                        Caso contrário, a regra será ignorada.
            datetime_provider (IDateTimeProvider, optional): Provedor de data/hora para testabilidade.
                                                             Usa SystemDateTimeProvider por padrão.
        """
        self.business_hours_only = business_hours_only
        self.datetime_provider = datetime_provider if datetime_provider is not None else SystemDateTimeProvider()

    async def validate(self, user: User) -> Optional[str]:
        """
        Valida se o registro do usuário está dentro do horário comercial permitido.

        Args:
            user (User): O objeto do usuário a ser validado.

        Returns:
            Optional[str]: Uma mensagem de erro se a validação falhar, None caso contrário.
        """
        if not self.business_hours_only:
            return None
        now = self.datetime_provider.now() # Alteração: usando o provedor injetado
        if now.weekday() >= 5:
            return "User registration only allowed during business days"
        if now.hour < 9 or now.hour >= 17:
            return "User registration only allowed during business hours (9 AM - 5 PM)"
        return None
    
    @property
    def rule_name(self) -> str:
        return "business_hours_validation"
