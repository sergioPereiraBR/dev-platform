# src/dev_platform/infrastructure/composition_root.py
from typing import List, Optional
from application.user.use_cases import (
    CreateUserUseCase, 
    ListUsersUseCase, 
    UpdateUserUseCase,
    GetUserUseCase,
    DeleteUserUseCase
)
from infrastructure.database.unit_of_work import SQLUnitOfWork
from infrastructure.logging.structured_logger import StructuredLogger
from domain.user.services import (
    UserDomainService, 
    UserAnalyticsService,
    DomainServiceFactory
)


class CompositionRoot:
    """
    Composition root for dependency injection.
    Centralizes the creation and configuration of all application dependencies.
    """
    
    def __init__(self, config: dict = None):
        self._config = config or {}
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
        return self._domain_service_factory
    
    # Use Cases - CORRIGIDO: Adicionando domain_service_factory onde necessário
    def create_user_use_case(self) -> CreateUserUseCase:
        return CreateUserUseCase(
            uow=self.uow,
            logger=self._logger,
            domain_service_factory=self.domain_service_factory  # ADICIONADO
        )
    
    def list_users_use_case(self) -> ListUsersUseCase:
        return ListUsersUseCase(
            uow=self.uow,
            logger=self._logger
        )
    
    def update_user_use_case(self) -> UpdateUserUseCase:
        return UpdateUserUseCase(
            uow=self.uow,
            logger=self._logger,
            domain_service_factory=self.domain_service_factory  # ADICIONADO
        )
    
    def get_user_use_case(self) -> GetUserUseCase:
        return GetUserUseCase(
            uow=self.uow,
            logger=self._logger
        )
    
    def delete_user_use_case(self) -> DeleteUserUseCase:
        return DeleteUserUseCase(
            uow=self.uow,
            logger=self._logger
        )
    
    # Domain Services
    def user_domain_service(self, user_repository) -> UserDomainService:
        """
        Create UserDomainService with configuration-based rules.
        """
        # Get configuration for validation rules
        validation_config = self._config.get('validation', {})
        
        return self.domain_service_factory.create_user_domain_service(
            user_repository=user_repository,
            enable_profanity_filter=validation_config.get('enable_profanity_filter', False),
            allowed_domains=validation_config.get('allowed_domains'),
            business_hours_only=validation_config.get('business_hours_only', False)
        )
    
    def user_analytics_service(self, user_repository) -> UserAnalyticsService:
        """Create UserAnalyticsService."""
        return self.domain_service_factory.create_analytics_service(user_repository)
    
    # Utility methods for specific configurations
    def create_enterprise_user_domain_service(self, user_repository) -> UserDomainService:
        """
        Create UserDomainService with enterprise-level validation rules.
        """
        return self.domain_service_factory.create_user_domain_service(
            user_repository=user_repository,
            enable_profanity_filter=True,
            allowed_domains=['empresa.com', 'company.com'],
            business_hours_only=True
        )
