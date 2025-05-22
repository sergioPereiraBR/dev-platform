# src/dev_platform/infrastructure/database/session.py
from contextlib import contextmanager
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

# Engine assíncrono - se a URL for compatível
if database_url.startswith(('mysql://', 'mysql+pymysql://')):
    async_database_url = database_url.replace('mysql://', 'mysql+pymysql://')
    AsyncEngine = create_async_engine(
        async_database_url,
        pool_size=pool_size,
        max_overflow=max_overflow
    )
    AsyncSessionLocal = sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=AsyncEngine)

@contextmanager
def db_session():
    """Context manager para sessões síncronas de banco de dados."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

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


# from contextlib import contextmanager
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from infrastructure.config import DATABASE_URL

# Engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# @contextmanager
# def db_session():
#     """Context manager para sessões de banco de dados."""
#     session = SessionLocal()
#     try:
#         yield session
#         session.commit()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()

# # Exemplo para session.py assíncrono
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker

# async_engine = create_async_engine(DATABASE_URL)
# AsyncSessionLocal = sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=async_engine)

# async def get_async_session():
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#             await session.commit()
#         except Exception:
#             await session.rollback()
#             raise
