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

    @property
    def uow(self) -> SQLUnitOfWork:
        if self._uow is None:
            self._uow = SQLUnitOfWork()
        return self._uow
    
    # Use Cases
    def create_user_use_case(self) -> CreateUserUseCase:
        return CreateUserUseCase(
            uow=SQLUnitOfWork(),
            logger=self._logger
        )
    
    def list_users_use_case(self) -> ListUsersUseCase:
        return ListUsersUseCase(
            uow=SQLUnitOfWork(),
            logger=self._logger
        )
    
    def update_user_use_case(self) -> UpdateUserUseCase:
        return UpdateUserUseCase(
            uow=SQLUnitOfWork(),
            logger=self._logger
        )
    
    def get_user_use_case(self) -> GetUserUseCase:
        return GetUserUseCase(
            uow=SQLUnitOfWork(),
            logger=self._logger
        )
    
    def delete_user_use_case(self) -> DeleteUserUseCase:
        return DeleteUserUseCase(
            uow=SQLUnitOfWork(),
            logger=self._logger
        )
    
    # Domain Services
    def user_domain_service(self, user_repository) -> UserDomainService:
        """
        Create UserDomainService with configuration-based rules.
        """
        # Get configuration for validation rules
        validation_config = self._config.get('validation', {})
        
        return DomainServiceFactory.create_user_domain_service(
            user_repository=user_repository,
            enable_profanity_filter=validation_config.get('enable_profanity_filter', False),
            allowed_domains=validation_config.get('allowed_domains'),
            business_hours_only=validation_config.get('business_hours_only', False)
        )
    
    def user_analytics_service(self, user_repository) -> UserAnalyticsService:
        """Create UserAnalyticsService."""
        return DomainServiceFactory.create_analytics_service(user_repository)
    
    # Utility methods for specific configurations
    def create_enterprise_user_domain_service(self, user_repository) -> UserDomainService:
        """
        Create UserDomainService with enterprise-level validation rules.
        """
        ...