# ./src/dev_platform/infrastructure/composition_root.py
# -*- coding: utf-8 -*-
"""
Este módulo define a raiz de composição para injeção de dependências,
centralizando a criação e configuração de todas as dependências da aplicação.
Agora utiliza um ValidationRuleProvider para desacoplar a lógica de regras de validação,
respeitando OCP e separando logging de infraestrutura.
"""

from typing import List
from dev_platform.application.user.use_cases import (
    CreateUserUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
    GetUserUseCase,
    DeleteUserUseCase,
)
from dev_platform.domain.user.services import (
    UserDomainService,
    UserAnalyticsService,
    UserUniquenessService,
    UserValidatorService
)
from dev_platform.domain.validation_rules import (
    EmailFormatAdvancedValidationRule,
    NameContentValidationRule,
    EmailDomainValidationRule,
    BusinessHoursValidationRule,
    NameProfanityValidationRule,
    ForbiddenWordsValidationRule
)

from dev_platform.infrastructure.config import ConfigurationFacade
from dev_platform.application.ports.logger import ILogger
from dev_platform.domain.validation_rules import ValidationRule

from dev_platform.application.user.ports import UnitOfWork # Importa a interface
from dev_platform.domain.user.interfaces import IUserRepository # Importa a interface
from dev_platform.infrastructure.database.unit_of_work import SQLUnitOfWork # Ainda precisa da implementação concreta para instanciar
from dev_platform.infrastructure.database.repositories import SQLUserRepository # Ainda precisa da implementação concreta para instanciar


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
        """
        Regras de validação padrão para usuários comuns.
        Essas regras são aplicadas a todos os usuários, exceto os enterprise.
        """
        return [
            EmailFormatAdvancedValidationRule(),
            NameContentValidationRule(),
            EmailDomainValidationRule(self._default_allowed_domains),
            NameProfanityValidationRule(forbidden_words=self._default_forbidden_words)
        ]
    
    def get_rules(self, user_type: str = "default") -> List[ValidationRule]:
        """
        Retorna a lista de regras de validação conforme o tipo de usuário.
        """
        if user_type == "enterprise":
            return self._enterprise_rules()
        return self._default_rules()

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


class CompositionRoot:
    """
    Composition root for dependency injection.
    Centraliza a criação e configuração de todas as dependências da aplicação.
    Utiliza ValidationRuleProvider para regras de validação (OCP).
    """

    def __init__(
        self,
        config: ConfigurationFacade, # Configuração injetada
		logger: ILogger, # Logger injetado
    ):
        self._config = config
        self._logger = logger
        # A CompositionRoot solicita os dados já formatados para a facade de configuração.
        self._validation_rule_provider = ValidationRuleProvider(
            default_allowed_domains=self._config.get_list("allowed_domains"),
            default_forbidden_words=self._config.get_list("validation_forbidden_words"),
            enterprise_allowed_domains=self._config.get_list("enterprise_allowed_domains"),
            enterprise_forbidden_words=self._config.get_list("enterprise_forbidden_words"),
            enable_profanity_filter=self._config.get_typed("validation_enable_profanity_filter", False, bool),
            logger=self._logger
        )
   
    def create_unit_of_work(self) -> UnitOfWork:
        # O SQLUnitOfWork recebe o repositório via injeção ou uma factory
        user_repo = SQLUserRepository(session=None, logger=self._logger) # A sessão será injetada pelo UoW
        # O repositório concreto é injetado na UoW.
        return SQLUnitOfWork(logger=self._logger, user_repository=user_repo) # Passa o repositório concreto
    
    def create_user_use_case(self, uow: SQLUnitOfWork) -> CreateUserUseCase:
        # Acessa o repositório através da propriedade da UoW após a sua criação.
        user_repository = uow.user_repository 
        # O domain_service deve receber apenas o que ele precisa para as regras de domínio.
        return CreateUserUseCase(
            uow=uow,
            user_validator=self.user_domain_service(),
            user_uniqueness_service=self.user_uniqueness_service(user_repository),
            logger=self._logger,
        )

    def list_users_use_case(self, uow: SQLUnitOfWork) -> ListUsersUseCase:
        return ListUsersUseCase(
            uow=uow,
            logger=self._logger
        )

    def update_user_use_case(self, uow: SQLUnitOfWork) -> UpdateUserUseCase:
        user_repository = uow.user_repository
        return UpdateUserUseCase(
            uow=uow,
            domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
        )

    def get_user_use_case(self, uow: SQLUnitOfWork) -> GetUserUseCase:
        user_repository = uow.user_repository
        return GetUserUseCase(
            uow=uow,
            domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
        )

    def delete_user_use_case(self, uow: SQLUnitOfWork) -> DeleteUserUseCase:
        user_repository = uow.user_repository
        return DeleteUserUseCase(
            uow=uow,
            domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
        )

    def user_domain_service(self, user_type: str = "default") -> UserValidatorService:
        """
        Cria UserValidatorService com regras de validação baseadas em configuração e tipo de usuário.
        """
        rules = self._validation_rule_provider.get_rules(user_type)
        return UserValidatorService(validation_rules=rules)
    
    def user_uniqueness_service(self, user_repository: IUserRepository) -> UserUniquenessService:
        """
		Cria UserUniquenessService, que depende do repositório.
		"""
        return UserUniquenessService(user_repository)

    def user_analytics_service(self, user_repository: IUserRepository) -> UserAnalyticsService:
        """
        Cria o serviço de analytics de usuários.
        """
        return UserAnalyticsService(user_repository)

    def create_enterprise_user_domain_service(self) -> UserDomainService:
        """
        Cria o serviço de domínio do usuário corporativo.
        """
        return self.user_domain_service(user_type="enterprise")
