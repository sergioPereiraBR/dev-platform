# ./src/dev_platform/infrastructure/database/unit_of_work.py
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Importe a CONFIG global
from dev_platform.infrastructure.config import CONFIG
from dev_platform.application.user.ports import UnitOfWork
from dev_platform.domain.user.interfaces import UserRepository # noqa: F401
from dev_platform.infrastructure.database.session import db_manager
from dev_platform.infrastructure.database.repositories import SQLUserRepository


# Estas variáveis devem ser criadas uma única vez na aplicação.
# Poderiam estar em um módulo 'session.py' separado ou aqui,
# mas fora da classe para garantir que não sejam recriadas.
_async_engine = None
_async_session_factory = None


async def get_async_engine():
    """Cria e retorna o engine assíncrono, garantindo que seja um singleton."""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            CONFIG.database_url,
            echo=CONFIG.get("DB_ECHO", "False").lower() == "true",
            pool_size=int(CONFIG.get("DB_POOL_SIZE", 10)),
            max_overflow=int(CONFIG.get("DB_MAX_OVERFLOW", 20)),
        )
    return _async_engine


async def get_async_session_factory():
    """Cria e retorna a factory de sessão assíncrona, garantindo que seja um singleton."""
    global _async_session_factory
    if _async_session_factory is None:
        engine = await get_async_engine()  # Garante que o engine está criado
        _async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_factory


class SQLUnitOfWork(UnitOfWork):
    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self.users: Optional[UserRepository] = None # Usar a interface do domínio
        #self.users: Optional[SQLUserRepository] = None
        self.users = SQLUserRepository(self._session) # Inicializa como None

    async def __aenter__(self):
        # Usar o gerenciador de sessões
        self._session_context = db_manager.get_async_session()
        self._session = await self._session_context.__aenter__()
        self.users = SQLUserRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self._session:
            return

        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        except Exception as e:
            self._logger.error(f"Error in transaction cleanup: {e}")
            try:
                await self._session.rollback()
            except:
                pass
        finally:
            try:
                await self._session.close()
                await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
                self._session = None
                self.users = None
            except Exception as e:
                self._logger.error(f"Error closing session: {e}")

    async def commit(self):
        if self._session:
            await self._session.commit()

    async def rollback(self):
        if self._session:
            await self._session.rollback()
