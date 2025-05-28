# src/dev_platform/infrastructure/database/session.py
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from infrastructure.config import CONFIG


# Configurações do pool de conexões
pool_size = CONFIG.get("database.pool_size", 5)
max_overflow = CONFIG.get("database.max_overflow", 10)

# Engine síncrono
database_url = CONFIG.get_database_url()
Engine = create_engine(
    database_url,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_pre_ping=True  # Verifica se a conexão está ativa antes de usar
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# Engine assíncrono
# A URL já deve vir formatada para o driver assíncrono (e.g., mysql+aiomysql://)
# ou mysql+asyncpg para postgres
if database_url.startswith(('mysql+aiomysql://', 'postgresql+asyncpg://', 'sqlite+aiosqlite://')): # Adicione outros drivers assíncronos aqui se necessário
    # Usamos a própria database_url, pois ela já está formatada para o async driver
    AsyncEngine = create_async_engine(
        database_url, # Usamos a URL diretamente, pois esperamos que ela já contenha o driver assíncrono
        pool_size=pool_size,
        max_overflow=max_overflow
    )
    AsyncSessionLocal = sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=AsyncEngine)


# @contextmanager
# def db_session():
#     """Context manager para sessões síncronas de banco de dados."""
#     session = SessionLocal()
#     try:
#         yield session
#         session.commit()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()

@asynccontextmanager
async def get_async_session():
    """Context manager para sessões assíncronas de banco de dados."""
    if not 'AsyncSessionLocal' in globals():
        raise RuntimeError("Async database session not supported with current database URL")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# # Abordagem mais sofisticada com Provider
# class AsyncSessionProvider:
#     def __init__(self):
#         self._session: Optional[AsyncSession] = None
    
#     async def get_session(self) -> AsyncSession:
#         if self._session is None:
#             self._session = AsyncSessionLocal()
#         return self._session
    
#     async def close(self):
#         if self._session:
#             await self._session.close()
#             self._session = None


# class AsyncCreateUserUseCase:
#     def __init__(self, session_provider: AsyncSessionProvider):
#         self.session_provider = session_provider
    
#     async def execute(self, user_create_dto: UserCreateDTO) -> User:
#         session = await self.session_provider.get_session()
#         user_repository = AsyncSQLUserRepository(session)
        
#         # Lógica do use case...
#         user = User(id=None, name=user_create_dto.name, email=user_create_dto.email)
#         user.validate()
#         return await user_repository.save(user) 