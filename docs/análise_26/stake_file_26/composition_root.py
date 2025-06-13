# ./src/dev_platform/infrastructure/composition_root.py
from typing import List, Optional
from dev_platform.application.user.use_cases import (
    CreateUserUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
    GetUserUseCase,
    DeleteUserUseCase,
)
from dev_platform.infrastructure.database.unit_of_work import SQLUnitOfWork
from dev_platform.infrastructure.logging.structured_logger import StructuredLogger
from dev_platform.domain.user.services import (
    UserDomainService,
    UserAnalyticsService,
    DomainServiceFactory,
    # Importar as regras de validação padrão
    EmailFormatAdvancedValidationRule,
    NameContentValidationRule,
    EmailDomainValidationRule,  # Para exemplo enterprise
    BusinessHoursValidationRule,  # Para exemplo enterprise
    NameProfanityValidationRule  # Para exemplo enterprise
)
from dev_platform.infrastructure.config import CONFIG


class CompositionRoot:
    """
    Composition root for dependency injection.
    Centralizes the creation and configuration of all application dependencies.
    """

    def __init__(self):
        # self._config = config or {}
        self._logger = StructuredLogger()
        self._uow = None
        self._domain_service_factory = DomainServiceFactory()

    @property
    def uow(self) -> SQLUnitOfWork:
        if self._uow is None:
            self._uow = SQLUnitOfWork()
        return self._uow

    @property
    def domain_service_factory(self) -> DomainServiceFactory:
        if self._domain_service_factory is None:
            self._domain_service_factory = DomainServiceFactory()
        return self._domain_service_factory

    @property
    def create_user_use_case(self) -> CreateUserUseCase:
        return CreateUserUseCase(
            uow=self.uow,
            user_domain_service=self.domain_service_factory.user_domain_service,
            logger=self._logger,
            domain_service_factory=self.domain_service_factory, # Passa a factory para o use case
        )

    @property
    def list_users_use_case(self) -> ListUsersUseCase:
        return ListUsersUseCase(uow=self.uow, logger=self._logger)

    @property
    def update_user_use_case(self) -> UpdateUserUseCase:
        return UpdateUserUseCase(
            uow=self.uow,
            user_domain_service=self.domain_service_factory.user_domain_service,
            logger=self._logger,
        )

    @property
    def get_user_use_case(self) -> GetUserUseCase:
        return GetUserUseCase(uow=self.uow, logger=self._logger)

    @property
    def delete_user_use_case(self) -> DeleteUserUseCase:
        return DeleteUserUseCase(uow=self.uow, logger=self._logger)

    # Domain Services
    def user_domain_service(self, user_repository) -> UserDomainService:
        """
        Create UserDomainService with configuration-based rules.
        """
        # Get configuration for validation rules
        validation_config = CONFIG.get("validation", {})

        # Definir as regras padrão aqui, ou carregar de outra parte da CONFIG
        # Estas são as regras que SEMPRE devem ser aplicadas por padrão
        default_rules_for_factory = [
            EmailFormatAdvancedValidationRule(),
            NameContentValidationRule(),
            EmailDomainValidationRule(),
            BusinessHoursValidationRule(),
            NameProfanityValidationRule()
        ]


        return self.domain_service_factory.create_user_domain_service(
            user_repository=user_repository,
            enable_profanity_filter=validation_config.get(
                "enable_profanity_filter", False
            ),
            allowed_domains=validation_config.get("allowed_domains"),
            business_hours_only=validation_config.get("business_hours_only", False),
            default_validation_rules=default_rules_for_factory,  # Injetar regras padrão
        )

    def user_analytics_service(self, user_repository) -> UserAnalyticsService:
        """Create UserAnalyticsService."""
        return self.domain_service_factory.create_analytics_service(user_repository)

    # Utility methods for specific configurations
    def create_enterprise_user_domain_service(
        self, user_repository
    ) -> UserDomainService:
        """
        Create UserDomainService with enterprise-level validation rules.
        """
        forbidden_words = CONFIG.get("validation.forbidden_words", "").split(",")
        enterprise_forbidden_words = CONFIG.get("enterprise.forbidden_words", "").split(",")
        enterprise_allowed_domains = CONFIG.get("enterprise.allowed_domains", "").split(",")

        # Regras específicas para o caso Enterprise
        enterprise_rules = [
            NameProfanityValidationRule(enterprise_forbidden_words),  # Exemplo de palavra proibida específica
            EmailDomainValidationRule(enterprise_allowed_domains),
            BusinessHoursValidationRule(True),
        ]

        return self.domain_service_factory.create_user_domain_service(
            user_repository=user_repository,
            # Passar as regras diretamente, ou usar os flags e deixar a fábrica montá-las
            # Para maior clareza, pode-se passar os flags aqui se a fábrica já tiver a lógica de montagem
            enable_profanity_filter=True, # A fábrica usará a CONFIG ou a lista injetada
            allowed_domains=enterprise_allowed_domains,
            business_hours_only=True,
            default_validation_rules=enterprise_rules # Injetar regras específicas
        )
