# src/dev_platform/infrastructure/database/session.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from infrastructure.config import CONFIG

class DatabaseSessionManager:
    """Gerenciador centralizado de sessões de banco de dados."""
    
    def __init__(self):
        self._async_engine = None
        self._sync_engine = None
        self._async_session_factory = None
        self._sync_session_factory = None
        self._initialize_engines()

    def _initialize_engines(self):
        """Inicializa os engines síncronos e assíncronos."""
        # Configurações do pool
        pool_config = {
            "pool_size": CONFIG.get("database.pool_size", 5),
            "max_overflow": CONFIG.get("database.max_overflow", 10),
            "pool_pre_ping": CONFIG.get("database.pool_pre_ping", True)
        }
        
        # Engine assíncrono
        async_url = CONFIG.get("DATABASE_URL")
        print(async_url)
        self._async_engine = create_async_engine(
            async_url,
            echo=CONFIG.get("database.echo", False),
            **pool_config
        )
        
        # Session factory assíncrona
        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Engine síncrono (se necessário para migrações ou outras operações)
        if not async_url.startswith("sqlite+aiosqlite"):  # SQLite não precisa de engine síncrono separado
            sync_url = CONFIG.get("DATABASE_URL")
            self._sync_engine = create_engine(
                sync_url,
                echo=CONFIG.get("database.echo", False),
                **pool_config
            )
            
            self._sync_session_factory = sessionmaker(
                bind=self._sync_engine,
                autocommit=False,
                autoflush=False
            )

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager para sessões assíncronas de banco de dados."""
        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def get_sync_session(self):
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
    def async_engine(self):
        """Propriedade para acessar o engine assíncrono."""
        return self._async_engine

    @property
    def sync_engine(self):
        """Propriedade para acessar o engine síncrono."""
        return self._sync_engine


# Instância global do gerenciador de sessões
db_manager = DatabaseSessionManager()

# Funções de conveniência para compatibilidade
async def get_async_session():
    """Função de conveniência para obter sessão assíncrona."""
    async with db_manager.get_async_session() as session:
        yield session

def get_sync_session():
    """Função de conveniência para obter sessão síncrona."""
    return db_manager.get_sync_session()

# Aliases para compatibilidade com código existente
AsyncSessionLocal = db_manager._async_session_factory
if db_manager._sync_session_factory:
    SessionLocal = db_manager._sync_session_factory

