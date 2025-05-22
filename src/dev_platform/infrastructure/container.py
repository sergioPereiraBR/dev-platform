# src/dev_platform/infrastructure/container.py
# src/dev_platform/infrastructure/container.py
from typing import Dict, Any, Callable, Type, TypeVar
from infrastructure.database.session import get_async_session
from infrastructure.database.async_repositories import AsyncSQLUserRepository
from dev_platform.scripts.usecases import CreateUserUseCase, ListUsersUseCase
from application.user.async_usecases import AsyncCreateUserUseCase, AsyncListUsersUseCase  # ✅ NOVO IMPORT
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


# ✅ CORREÇÃO: Funções para criar dependências assíncronas
async def create_async_user_repository():
    """Factory para criar repositório assíncrono."""
    async with get_async_session() as session:
        return AsyncSQLUserRepository(session)

async def create_async_create_user_usecase():
    """Factory para criar use case assíncrono."""
    repo = await create_async_user_repository()
    return AsyncCreateUserUseCase(repo)

async def create_async_list_users_usecase():
    """Factory para criar use case assíncrono."""
    repo = await create_async_user_repository()
    return AsyncListUsersUseCase(repo)

