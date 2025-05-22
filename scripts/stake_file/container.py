# src/dev_platform/infrastructure/container.py
from infrastructure.database.session import SessionLocal
from infrastructure.database.async_repositories import AsyncSQLUserRepository
from application.user.usecases import CreateUserUseCase, ListUsersUseCase

class Container:
    """Contêiner simples de injeção de dependências."""
    
    @staticmethod
    def get_user_repository():
        session = get_async_session()
        return AsyncSQLUserRepository(session)
    
    @staticmethod
    def get_create_user_usecase():
        return CreateUserUseCase(Container.get_user_repository())
    
    @staticmethod
    def get_list_users_usecase():
        return ListUsersUseCase(Container.get_user_repository())
