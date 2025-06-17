# ./src/dev_platform/infrastructure/composition_root.py
# -*- coding: utf-8 -*-
"""
Este módulo define a raiz de composição para injeção de dependências,
centralizando a criação e configuração de todas as dependências da aplicação.
"""

from typing import Any, Dict, List, Optional
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
    DomainServiceFactory,
    EmailFormatAdvancedValidationRule,
    NameContentValidationRule,
    EmailDomainValidationRule,
    BusinessHoursValidationRule,
    NameProfanityValidationRule,
    ForbiddenWordsValidationRule
)
from dev_platform.infrastructure.config import CONFIG


class CompositionRoot:
    """
    Composition root for dependency injection.
    Centralizes the creation and configuration of all application dependencies.
    Now receives environment and configuration as dependencies (SRP/DIP).
    """

    def __init__(
        self,
        environment: str,
        config: Dict[str, Any] = CONFIG,
        logger: Optional[Any] = None,
        domain_service_factory: Optional[DomainServiceFactory] = None
    ):
        """
        :param environment: The current environment (e.g., 'production', 'development').
        :param config: Configuration provider (default: CONFIG singleton).
        :param logger: Logger instance (default: StructuredLogger).
        :param domain_service_factory: Factory for domain services (default: DomainServiceFactory).
        """
        self._environment = environment
        self._config = config
        self._logger = logger or StructuredLogger()
        self._domain_service_factory = domain_service_factory or DomainServiceFactory()

    @property
    def domain_service_factory(self) -> DomainServiceFactory:
        return self._domain_service_factory

    def create_user_use_case(self, uow: SQLUnitOfWork, user_repository: IUserRepository) -> CreateUserUseCase:
        """
        Cria o caso de uso para criação de usuário.
        """
        return CreateUserUseCase(
            uow=uow,
            user_domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
            domain_service_factory=self.domain_service_factory,
        )

    def list_users_use_case(self, uow: SQLUnitOfWork) -> ListUsersUseCase:
        """
        Cria o caso de uso para listagem de usuários.
        """
        return ListUsersUseCase(uow=uow, logger=self._logger)

    def update_user_use_case(self, uow: SQLUnitOfWork, user_repository: IUserRepository) -> UpdateUserUseCase:
        """
        Cria o caso de uso para atualização de usuário.
        """
        return UpdateUserUseCase(
            uow=uow,
            user_domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
            domain_service_factory=self.domain_service_factory,
        )

    def get_user_use_case(self, uow: SQLUnitOfWork, user_repository: IUserRepository) -> GetUserUseCase:
        """
        Cria o caso de uso para obtenção de usuário.
        """
        return GetUserUseCase(
            uow=uow,
            user_domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
            domain_service_factory=self.domain_service_factory,
        )

    def delete_user_use_case(self, uow: SQLUnitOfWork, user_repository: IUserRepository) -> DeleteUserUseCase:
        """
        Cria o caso de uso para exclusão de usuário.
        """
        return DeleteUserUseCase(
            uow=uow,
            user_domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
            domain_service_factory=self.domain_service_factory,
        )

    def parse_csv_config(self, key: str) -> List[str]:
        """
        Parse a CSV configuration value from the config provider.
        """
        return [w.strip() for w in self._config.get(key, "").split(",") if w.strip()]

    def default_rules_for_factory(self) -> List[Any]:
        """
        Default validation rules for the domain service factory.
        """
        _allowed_domains = self.parse_csv_config("allowed_domains")
        _forbidden_words = self.parse_csv_config("validation_forbidden_words")
        return [
            EmailFormatAdvancedValidationRule(),
            NameContentValidationRule(),
            EmailDomainValidationRule(_allowed_domains),
            BusinessHoursValidationRule(False),
            NameProfanityValidationRule(forbidden_words=_forbidden_words),
            ForbiddenWordsValidationRule(forbidden_words=_forbidden_words)
        ]

    def user_domain_service(self, user_repository: IUserRepository) -> UserDomainService:
        """
        Create UserDomainService with configuration-based rules.
        """
        validation_config = self._config.get("validation", {})
        allowed_domains = self.parse_csv_config("allowed_domains")
        forbidden_words = self.parse_csv_config("validation_forbidden_words")

        if validation_config.get("enable_profanity_filter", False) and not forbidden_words:
            self._logger.warning("Profanity filter enabled, but forbidden words list is empty in configuration.")

        return self.domain_service_factory.create_user_domain_service(
            user_repository=user_repository,
            enable_profanity_filter=validation_config.get("enable_profanity_filter", False),
            allowed_domains=allowed_domains,
            business_hours_only=validation_config.get("business_hours_only", False),
        )

    def user_analytics_service(self, user_repository:IUserRepository) -> UserAnalyticsService:
        """
        Cria o serviço de analytics de usuários.
        """
        return self.domain_service_factory.create_analytics_service(user_repository)

    def create_enterprise_user_domain_service(
        self, user_repository:IUserRepository
    ) -> UserDomainService:
        """
        Create UserDomainService with enterprise-level validation rules.
        """
        validation_forbidden_words = self.parse_csv_config("validation_forbidden_words")
        enterprise_forbidden_words = self.parse_csv_config("enterprise_forbidden_words")
        enterprise_allowed_domains = self.parse_csv_config("enterprise_allowed_domains")

        if not enterprise_forbidden_words:
            self._logger.warning("Enterprise forbidden words list is empty in configuration.")

        enterprise_rules = [
            ForbiddenWordsValidationRule(validation_forbidden_words),
            NameProfanityValidationRule(enterprise_forbidden_words),
            EmailDomainValidationRule(enterprise_allowed_domains),
            BusinessHoursValidationRule(True),
        ]

        return self.domain_service_factory.create_user_domain_service(
            user_repository=user_repository,
            enable_profanity_filter=True,
            allowed_domains=enterprise_allowed_domains,
            business_hours_only=True,
            default_validation_rules=enterprise_rules
        )
    