# src/dev_platform/infrastructure/container.py
from typing import Dict, Any, Callable, Type, TypeVar
from infrastructure.database.session import SessionLocal, get_async_session
from infrastructure.database.async_repositories import AsyncSQLUserRepository
from application.user.usecases import CreateUserUseCase, ListUsersUseCase
from domain.user.interfaces import AsyncUserRepository

T = TypeVar('T')


class Container:
    """Container avançado de injeção de dependências."""
    
    _instances: Dict[str, Any] = {}
    _factories: Dict[str, Callable[[], Any]] = {}
    
    @classmethod
    def register(cls, key: str, factory: Callable[[], Any]) -> None:
        """Registra uma factory para um tipo específico."""
        cls._factories[key] = factory
    
    @classmethod
    def get(cls, key: str) -> Any:
        """Obtém ou cria uma instância para o key especificado."""
        if key not in cls._instances:
            if key not in cls._factories:
                raise KeyError(f"No factory registered for key: {key}")
            cls._instances[key] = cls._factories[key]()
        return cls._instances[key]
    
    @classmethod
    def get_scoped(cls, key: str) -> Any:
        """Cria sempre uma nova instância para o key especificado."""
        if key not in cls._factories:
            raise KeyError(f"No factory registered for key: {key}")
        return cls._factories[key]()
    
    @classmethod
    def clear(cls) -> None:
        """Limpa todas as instâncias armazenadas."""
        cls._instances.clear()


# Configuração do container
async def setup_container():
    """Configura o container com todas as dependências."""
    # Repositórios
    Container.register("async_session", get_async_session)
    Container.register("user_repository", lambda: AsyncSQLUserRepository(Container.get("async_session")))
    
    # Use cases
    Container.register("create_user_usecase", lambda: CreateUserUseCase(Container.get("user_repository")))
    Container.register("list_users_usecase", lambda: ListUsersUseCase(Container.get("user_repository")))

# Funções utilitárias para obter dependências específicas
async def get_user_repository() -> AsyncUserRepository:
    return Container.get("user_repository")

async def get_create_user_usecase() -> CreateUserUseCase:
    return Container.get("create_user_usecase")

async def get_list_users_usecase() -> ListUsersUseCase:
    return Container.get("list_users_usecase")
