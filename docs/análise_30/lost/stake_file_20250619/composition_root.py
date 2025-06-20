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
    """
    Provider para regras de validação de usuários.
    Permite extensão sem modificar a CompositionRoot (OCP).
    Responsável por logging de configuração relacionado às regras.
    """
    def __init__(self, config: Dict[str, Any], logger: ILogger):
        self._config = ConfigurationFacade()
        self._logger = logger

    def get_rules(self, user_type: str = "default") -> List[ValidationRule]:
        """
        Retorna a lista de regras de validação conforme o tipo de usuário.
        """
        if user_type == "enterprise":
            return self._enterprise_rules()
        return self._default_rules()

    def _default_rules(self) -> List[ValidationRule]:
        allowed_domains = self._parse_csv("allowed_domains")
        forbidden_words = self._parse_csv("validation_forbidden_words")
        validation_config = self._config.get("validation", {})

        if validation_config.get("enable_profanity_filter", False) and not forbidden_words:
            self._logger.warning("Profanity filter enabled, but forbidden words list is empty in configuration.")

        return [
            EmailFormatAdvancedValidationRule(),
            NameContentValidationRule(),
            EmailDomainValidationRule(allowed_domains),
            BusinessHoursValidationRule(validation_config.get("business_hours_only", False)),
            NameProfanityValidationRule(forbidden_words=forbidden_words),
            ForbiddenWordsValidationRule(forbidden_words=forbidden_words)
        ]

    def _enterprise_rules(self) -> List[ValidationRule]:
        validation_forbidden_words = self._parse_csv("validation_forbidden_words")
        enterprise_forbidden_words = self._parse_csv("enterprise_forbidden_words")
        enterprise_allowed_domains = self._parse_csv("enterprise_allowed_domains")

        if not enterprise_forbidden_words:
            self._logger.warning("Enterprise forbidden words list is empty in configuration.")

        return [
            ForbiddenWordsValidationRule(validation_forbidden_words),
            NameProfanityValidationRule(enterprise_forbidden_words),
            EmailDomainValidationRule(enterprise_allowed_domains),
            BusinessHoursValidationRule(True),
        ]

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
        environment: str,
        logger: Optional[ILogger] = None,
        validation_rule_provider: Optional[ValidationRuleProvider] = None
    ):
        self._environment = environment
        self._config = ConfigurationFacade()
        self._logger = logger or StructuredLogger()
        self._validation_rule_provider = validation_rule_provider or ValidationRuleProvider(self._config, self._logger)

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
