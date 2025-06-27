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
from dev_platform.application.user.ports import UnitOfWork
from dev_platform.infrastructure.database.unit_of_work import SQLUnitOfWork

from dev_platform.domain.user.interfaces import IUserRepository
from dev_platform.infrastructure.database.repositories import SQLUserRepository
from dev_platform.domain.validation_rules import UserCountLimitValidationRule
from dev_platform.domain.user.services import UserValidatorService
from dev_platform.application.user.mappers import UserMapper


class ValidationRuleProvider:
    """Provider para regras de validação, desacoplado da infraestrutura."""
    def __init__(
        self,
        default_allowed_domains: List[str],
        default_forbidden_words: List[str],
        enterprise_allowed_domains: List[str],
        enterprise_forbidden_words: List[str],
        enable_profanity_filter: bool,
        repository: IUserRepository,
        logger: ILogger
    ):
        self._default_allowed_domains = default_allowed_domains
        self._default_forbidden_words = default_forbidden_words
        self._enterprise_allowed_domains = enterprise_allowed_domains
        self._enterprise_forbidden_words = enterprise_forbidden_words
        self._enable_profanity_filter = enable_profanity_filter
        self._repository = repository
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
            NameProfanityValidationRule(forbidden_words=self._default_forbidden_words),
            UserCountLimitValidationRule(repository=self._repository)
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
            BusinessHoursValidationRule(True),  # True: só permitir operações em horário comercial
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
        # config: ConfigurationFacade, # Configuração injetada
		logger: ILogger, # Logger injetado
    ):
        # self._config = config
        self._logger = logger
        self._user_mapper = UserMapper()
        # Inicializa a ConfigurationFacade UMA VEZ aqui
        self._config_facade = ConfigurationFacade(logger=self._logger) # Passa o logger existente

    def get_configuration_facade(self) -> ConfigurationFacade:
        """Retorna a instância da fachada de configuração."""
        return self._config_facade

    def _create_validation_provider(self, repository: IUserRepository) -> ValidationRuleProvider:
        return ValidationRuleProvider(
            default_allowed_domains=self._config_facade.get_list("allowed_domains"),
            default_forbidden_words=self._config_facade.get_list("validation_forbidden_words"),
            enterprise_allowed_domains=self._config_facade.get_list("enterprise_allowed_domains"),
            enterprise_forbidden_words=self._config_facade.get_list("enterprise_forbidden_words"),
            enable_profanity_filter=self._config_facade.get_typed("validation_enable_profanity_filter", False, bool),
            repository=repository,  # Injeta o repositório recebido como argumento
            logger=self._logger
        )
    
    def _create_user_repository(self) -> IUserRepository:
        """
		Método privado para criar e configurar o repositório de usuários.
		Centraliza a lógica de inicialização do repositório.
		"""
		# A sessão é injetada pelo UoW posteriormente
        return SQLUserRepository(session=None, logger=self._logger)

    def create_unit_of_work(self) -> UnitOfWork:
        # Agora, create_unit_of_work utiliza o método privado para criar o repositório
        user_repo: SQLUserRepository = self._create_user_repository()
        return SQLUnitOfWork(logger=self._logger, user_repository=user_repo)
    
    def create_user_use_case(self) -> CreateUserUseCase:
        uow: SQLUnitOfWork = self.create_unit_of_work()
		# Acesso ao user_repository através da UoW, evitando duplicação na criação do repositório
        user_repository: IUserRepository = uow.user_repository # Este acesso é necessário para os serviços dependentes do repositório
        rule_provider = self._create_validation_provider(user_repository)
        validator_service = UserValidatorService(rule_provider.get_rules("default"))
        return CreateUserUseCase(
            uow=uow,
            user_validator=validator_service, # Serviço limpo injetado
            user_uniqueness_service=self.user_uniqueness_service(user_repository),
            logger=self._logger,
            mapper=self._user_mapper
        )

    def list_users_use_case(self) -> ListUsersUseCase:
        uow: SQLUnitOfWork = self.create_unit_of_work()
        return ListUsersUseCase(
            uow=uow,
            logger=self._logger,
            mapper=self._user_mapper
        )

    def update_user_use_case(self) -> UpdateUserUseCase:
        uow: SQLUnitOfWork = self.create_unit_of_work()
        user_repository: IUserRepository = uow.user_repository # Necessário para os serviços de domínio
        rule_provider = self._create_validation_provider(user_repository)
        validator_service = UserValidatorService(rule_provider.get_rules("default"))
        uniqueness_service = UserUniquenessService(user_repository)
        return UpdateUserUseCase(
            uow=uow,
            logger=self._logger,
            mapper=self._user_mapper,
            user_validator=validator_service,
            user_uniqueness_service=uniqueness_service,
        )

    def get_user_use_case(self) -> GetUserUseCase:
        uow: SQLUnitOfWork = self.create_unit_of_work()
        user_repository: IUserRepository = uow.user_repository
        rule_provider = self._create_validation_provider(user_repository)
        # O provider é criado aqui, com o repositório do UoW
        validator_service = UserValidatorService(rule_provider.get_rules("default"))
        uniqueness_service = UserUniquenessService(user_repository)
        return GetUserUseCase(
            uow=uow,
            user_validator=validator_service,
            domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
            mapper=self._user_mapper,
            user_uniqueness_service=uniqueness_service
        )

    def delete_user_use_case(self) -> DeleteUserUseCase:
        uow: SQLUnitOfWork = self.create_unit_of_work()
        user_repository: IUserRepository = uow.user_repository
        rule_provider = self._create_validation_provider(user_repository)
        # O provider é criado aqui, com o repositório do UoW
        rule_provider = self._create_validation_provider(user_repository)
        validator_service = UserValidatorService(rule_provider.get_rules("default"))
        uniqueness_service = UserUniquenessService(user_repository)
        return DeleteUserUseCase(
            uow=uow,
            user_validator=validator_service,
            domain_service=self.user_domain_service(user_repository),
            logger=self._logger,
            mapper=self._user_mapper,
            user_uniqueness_service=uniqueness_service
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

    # def create_enterprise_user_domain_service(self) -> UserDomainService:
    #     """
    #     Cria o serviço de domínio do usuário corporativo.
    #     """
    #     return self.user_domain_service(user_type="enterprise")
