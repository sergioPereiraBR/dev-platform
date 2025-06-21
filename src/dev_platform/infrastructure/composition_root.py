# ./src/dev_platform/infrastructure/composition_root.py
# -*- coding: utf-8 -*-
"""
Este módulo define a raiz de composição para injeção de dependências,
centralizando a criação e configuração de todas as dependências da aplicação.
Agora utiliza um ValidationRuleProvider para desacoplar a lógica de regras de validação,
respeitando OCP e separando logging de infraestrutura.
"""

from typing import Any, Dict, List, Optional
from dev_platform.infrastructure.config import ConfigurationFacade
from dev_platform.application.user.use_cases import (
    CreateUserUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
    GetUserUseCase,
    DeleteUserUseCase,
)
from dev_platform.domain.user.interfaces import IUserRepository
from dev_platform.infrastructure.database.unit_of_work import SQLUnitOfWork
from dev_platform.infrastructure.logging.structured_logger import StructuredLogger
from dev_platform.domain.user.services import (
    UserDomainService,
    UserAnalyticsService,
)
from dev_platform.domain.validation_rules import (
    EmailFormatAdvancedValidationRule,
    NameContentValidationRule,
    EmailDomainValidationRule,
    BusinessHoursValidationRule,
    NameProfanityValidationRule,
    ForbiddenWordsValidationRule
)
from dev_platform.application.ports.logger import ILogger
from dev_platform.domain.validation_rules import ValidationRule


class ValidationRuleProvider:
    """Provider para regras de validação, desacoplado da infraestrutura."""
    def __init__(
        self,
        default_allowed_domains: List[str],
        default_forbidden_words: List[str],
        enterprise_allowed_domains: List[str],
        enterprise_forbidden_words: List[str],
        enable_profanity_filter: bool,
        logger: ILogger
    ):
        self._default_allowed_domains = default_allowed_domains
        self._default_forbidden_words = default_forbidden_words
        self._enterprise_allowed_domains = enterprise_allowed_domains
        self._enterprise_forbidden_words = enterprise_forbidden_words
        self._enable_profanity_filter = enable_profanity_filter
        self._logger = logger

    def _default_rules(self) -> List[ValidationRule]:
        if self._enable_profanity_filter and not self._default_forbidden_words:
            self._logger.warning("Profanity filter enabled, but forbidden words list is empty.")
        return [
            EmailFormatAdvancedValidationRule(),
            NameContentValidationRule(),
            EmailDomainValidationRule(self._default_allowed_domains),
            NameProfanityValidationRule(forbidden_words=self._default_forbidden_words)
        ]

    def _enterprise_rules(self) -> List[ValidationRule]:
        """
        Regras de validação específicas para usuários enterprise.
        Permite maior controle e customização para clientes corporativos.
        """
        if self._enable_profanity_filter and not self._enterprise_forbidden_words:
            self._logger.warning("Profanity filter enabled for enterprise, but forbidden words list is empty.")

        rules: List[ValidationRule] = [
            EmailFormatAdvancedValidationRule(),
            NameContentValidationRule(),
            EmailDomainValidationRule(self._enterprise_allowed_domains),
            NameProfanityValidationRule(forbidden_words=self._enterprise_forbidden_words),
            # Regras extras para enterprise:
            ForbiddenWordsValidationRule(forbidden_words=self._enterprise_forbidden_words),
            BusinessHoursValidationRule(True),  # Exemplo: só permitir operações em horário comercial
        ]
        return rules

    def _parse_csv(self, key: str) -> List[str]:
        value = self._config.get(key)
        if not value:
            return []
        return [w.strip() for w in value.split(",") if w.strip()]


class CompositionRoot:
    """
    Composition root for dependency injection.
    Centraliza a criação e configuração de todas as dependências da aplicação.
    Utiliza ValidationRuleProvider para regras de validação (OCP).
    """

    def __init__(
        self,
        config: ConfigurationFacade,
        logger: Optional[ILogger] = None,
        validation_rule_provider: Optional[ValidationRuleProvider] = None
    ):
        self._config = config
        self._logger = logger or StructuredLogger()

        # A CompositionRoot lê da infraestrutura...
        def _parse_csv(key: str) -> List[str]:
            value = self._config.get(key, "")
            return [w.strip() for w in value.split(",") if w.strip()]

        # ...e passa dados primitivos para o provider.
        self._validation_rule_provider = ValidationRuleProvider(
            default_allowed_domains=_parse_csv("allowed_domains"),
            default_forbidden_words=_parse_csv("validation_forbidden_words"),
            enterprise_allowed_domains=_parse_csv("enterprise_allowed_domains"),
            enterprise_forbidden_words=_parse_csv("enterprise_forbidden_words"),
            enable_profanity_filter=self._config.get_typed("validation_enable_profanity_filter", False, bool),
            logger=self._logger
        )

    def create_user_use_case(self, uow: SQLUnitOfWork, user_repository: IUserRepository) -> CreateUserUseCase:
        return CreateUserUseCase(
            uow=uow,
            domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
        )

    def list_users_use_case(self, uow: SQLUnitOfWork) -> ListUsersUseCase:
        return ListUsersUseCase(uow=uow, logger=self._logger)

    def update_user_use_case(self, uow: SQLUnitOfWork, user_repository: IUserRepository) -> UpdateUserUseCase:
        return UpdateUserUseCase(
            uow=uow,
            domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
        )

    def get_user_use_case(self, uow: SQLUnitOfWork, user_repository: IUserRepository) -> GetUserUseCase:
        return GetUserUseCase(
            uow=uow,
            domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
        )

    def delete_user_use_case(self, uow: SQLUnitOfWork, user_repository: IUserRepository) -> DeleteUserUseCase:
        return DeleteUserUseCase(
            uow=uow,
            domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
        )

    def user_domain_service(self, user_repository: IUserRepository, user_type: str = "default") -> UserDomainService:
        """
        Cria UserDomainService com regras de validação baseadas em configuração e tipo de usuário.
        """
        rules = self._validation_rule_provider.get_rules(user_type)
        return UserDomainService(user_repository, rules)

    def user_analytics_service(self, user_repository: IUserRepository) -> UserAnalyticsService:
        """
        Cria o serviço de analytics de usuários.
        """
        return UserAnalyticsService(user_repository)

    def create_enterprise_user_domain_service(
        self, user_repository: IUserRepository
    ) -> UserDomainService:
        return self.user_domain_service(user_repository, user_type="enterprise")
