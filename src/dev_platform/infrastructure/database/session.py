# ./src/dev_platform/infrastructure/database/session.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from dev_platform.infrastructure.config import CONFIG


class DatabaseSessionManager:
    """ 
    Gerenciador centralizado de sessões de banco de dados.

    ⚠️ Commit automático no context manager
    O método get_async_session realiza automaticamente um await session.commit() ao sair do bloco async with.
    
    Se ocorrer uma exceção dentro do bloco, será feito await session.rollback() antes de propagar o erro.

    Atenção:
    Esse comportamento pode surpreender desenvolvedores que esperam controlar o commit manualmente.
    Se você precisa de controle total sobre commit/rollback, utilize a factory de sessão diretamente.

    Exemplo de uso:
    async with db_manager.get_async_session() as session:
        # Todas as operações dentro deste bloco serão automaticamente commitadas ao final,
        # ou rollback em caso de exceção.
        ...
    
    Resumo:
    O commit é automático ao sair do bloco.
    O rollback é automático em caso de exceção.
    Para controle manual, crie a sessão diretamente via factory."""

    def __init__(self):
        self._async_engine: Optional[AsyncEngine] = None
        self._sync_engine: Optional[Engine] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        self._sync_session_factory: Optional[sessionmaker] = None
        self._initialize_engines()

    def _initialize_engines(self):
        """Inicializa os engines síncronos e assíncronos."""
        # Configurações do pool
        pool_config = {
            "pool_size": int(CONFIG.get("database_pool_size", 5)),
            "max_overflow": int(CONFIG.get("database_max_overflow", 10)),
            "pool_pre_ping": CONFIG.get("database_pool_pre_ping", True),
        }

        # Engine assíncrono
        async_url = CONFIG.get("database_url")
        self._async_engine = create_async_engine(
            async_url, echo=CONFIG.get("database_echo", False), **pool_config
        )

        # Session factory assíncrona
        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Engine síncrono (se necessário para migrações ou outras operações)
        if not async_url.startswith(
            "sqlite+aiosqlite"
        ):  # SQLite não precisa de engine síncrono separado
            sync_url = CONFIG.get("database_url")
            self._sync_engine = create_engine(
                sync_url, echo=CONFIG.get("database_echo", False), **pool_config
            )

            self._sync_session_factory = sessionmaker(
                bind=self._sync_engine, autocommit=False, autoflush=False
            )

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager para sessões assíncronas de banco de dados.

        ⚠️ Commit automático: Ao sair do bloco async with, será feito await session.commit().
        Em caso de exceção, será feito await session.rollback() automaticamente.

        Se precisar de controle manual sobre commit/rollback, utilize a factory de sessão diretamente.

        Exemplo:
            async with db_manager.get_async_session() as session:
                # Operações...
        """
        if self._async_session_factory is None:
            raise RuntimeError("Async session factory is not initialized")
        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def get_sync_session(self) -> Session:
        """Obtém uma sessão síncrona (para migrações, etc.)."""
        if not self._sync_session_factory:
            raise RuntimeError("Sync session not available for this database type")
        return self._sync_session_factory()

    async def close_async_engine(self):
        """Fecha o engine assíncrono."""
        if self._async_engine:
            await self._async_engine.dispose()

    def close_sync_engine(self):
        """Fecha o engine síncrono."""
        if self._sync_engine:
            self._sync_engine.dispose()

    @property
    def async_engine(self) -> AsyncEngine:
        """Propriedade para acessar o engine assíncrono."""
        return self._async_engine

    @property
    def sync_engine(self) -> Engine:
        """Propriedade para acessar o engine síncrono."""
        return self._sync_engine


# Instância global do gerenciador de sessões
db_manager = DatabaseSessionManager()

# Funções de conveniência para compatibilidade
async def get_async_session():
    """Função de conveniência para obter sessão assíncrona.
    Garante que o gerenciador de sessões assíncronas esteja inicializado
    e faz await session.commit() automaticamente ao sair do bloco."""
    if db_manager._async_session_factory is None:
        raise RuntimeError("Async session factory is not initialized")
    async with db_manager.get_async_session() as session:
        yield session

def get_sync_session():
    """Função de conveniência para obter sessão síncrona."""
    return db_manager.get_sync_session()

# Aliases para compatibilidade com código existente
if db_manager._async_session_factory:
    AsyncSessionLocal = db_manager._async_session_factory

if db_manager._sync_session_factory:
    SessionLocal = db_manager._sync_session_factory
