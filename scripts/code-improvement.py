# 1. Corrigindo o problema de importação em main.py

# src/dev_platform/main.py
from dev_platform.interface.cli.user_cli import cli  # Importação absoluta corrigida

if __name__ == "__main__":
    cli()


# 2. Implementando um arquivo de configuração melhorado

# src/dev_platform/infrastructure/config.py
from dotenv import load_dotenv
import os
import json
from typing import Dict, Any, Optional
from shared.exceptions import ConfigurationException

class Configuration:
    """Classe avançada para gerenciar configurações da aplicação."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        load_dotenv()
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.config = {}
        self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """Carrega configurações baseadas no ambiente."""
        # Configurações base aplicáveis a todos os ambientes
        self.config = {
            "database": {
                "url": os.getenv("DATABASE_URL"),
                "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10"))
            },
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "format": os.getenv("LOG_FORMAT", "json")
            },
            "app": {
                "debug": os.getenv("DEBUG", "False").lower() == "true"
            }
        }
        
        # Carrega configurações específicas do ambiente, se existirem
        config_file = f"config/{self.environment}.json"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                env_config = json.load(f)
                # Mescla com as configurações existentes
                self._merge_configs(self.config, env_config)
    
    def _merge_configs(self, base_config: Dict, new_config: Dict) -> None:
        """Mescla configurações recursivamente."""
        for key, value in new_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_configs(base_config[key], value)
            else:
                base_config[key] = value
    
    def get_database_url(self) -> str:
        """Obtém a URL do banco de dados ou lança uma exceção."""
        url = self.config.get("database", {}).get("url")
        if not url:
            if self.environment == "development":
                return "sqlite:///./dev.db"
            raise ConfigurationException("DATABASE_URL environment variable is not set")
        return url
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna todas as configurações como um dicionário."""
        return self.config
    
    def get(self, path: str, default: Any = None) -> Any:
        """Obtém um valor de configuração por caminho pontilhado, ex: 'database.url'"""
        keys = path.split(".")
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value

# Instância Singleton para uso fácil em outros módulos
CONFIG = Configuration()
DATABASE_URL = CONFIG.get_database_url()


# 3. Melhorando o gerenciamento de sessões de banco de dados (assíncrono e síncrono)

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
if database_url.startswith(('postgresql://', 'postgresql+asyncpg://')):
    async_database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
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


# 4. Implementando um serviço de cache

# src/dev_platform/infrastructure/cache/cache_service.py
import time
from typing import Any, Dict, Optional, Callable, TypeVar, Generic

T = TypeVar('T')

class CacheService(Generic[T]):
    """Serviço de cache genérico com suporte para TTL."""
    
    def __init__(self, ttl: int = 300):
        """
        Inicializa o serviço de cache.
        
        Args:
            ttl: Tempo de vida das entradas em segundos (default 300s = 5min)
        """
        self.cache: Dict[str, T] = {}
        self.ttl = ttl
        self.timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[T]:
        """
        Retorna um valor do cache ou None se não existir ou estiver expirado.
        
        Args:
            key: Chave do item no cache
            
        Returns:
            O valor armazenado ou None
        """
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                self.invalidate(key)
        return None
    
    def set(self, key: str, value: T) -> None:
        """
        Armazena um valor no cache.
        
        Args:
            key: Chave para o item
            value: Valor a ser armazenado
        """
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        """
        Retorna um valor do cache ou executa a factory para criá-lo se não existir.
        
        Args:
            key: Chave do item no cache
            factory: Função que cria o valor se não existir no cache
            
        Returns:
            O valor do cache ou criado pela factory
        """
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value)
        return value
    
    def invalidate(self, key: str) -> None:
        """
        Remove um item do cache.
        
        Args:
            key: Chave do item a ser removido
        """
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        self.cache.clear()
        self.timestamps.clear()


# 5. Implementando um repositório assíncrono

# src/dev_platform/infrastructure/database/async_repositories.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.user.entities import User
from domain.user.interfaces import AsyncUserRepository  # Precisamos criar esta interface
from infrastructure.database.models import UserModel
from shared.exceptions import DatabaseException

class AsyncSQLUserRepository(AsyncUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, user: User) -> User:
        try:
            db_user = UserModel(name=user.name, email=user.email)
            self.session.add(db_user)
            await self.session.flush()
            user.id = db_user.id
            return user
        except Exception as e:
            await self.session.rollback()
            raise DatabaseException(f"Error saving user: {e}")
    
    async def find_all(self) -> List[User]:
        try:
            result = await self.session.execute(select(UserModel))
            db_users = result.scalars().all()
            return [User(id=u.id, name=u.name, email=u.email) for u in db_users]
        except Exception as e:
            raise DatabaseException(f"Error finding all users: {e}")
    
    async def find_by_id(self, user_id: int) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            db_user = result.scalars().first()
            if db_user:
                return User(id=db_user.id, name=db_user.name, email=db_user.email)
            return None
        except Exception as e:
            raise DatabaseException(f"Error finding user by id: {e}")
    
    async def find_by_email(self, email: str) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            db_user = result.scalars().first()
            if db_user:
                return User(id=db_user.id, name=db_user.name, email=db_user.email)
            return None
        except Exception as e:
            raise DatabaseException(f"Error finding user by email: {e}")


# 6. Interface para repositório assíncrono

# src/dev_platform/domain/user/interfaces.py (adicionar à versão existente)
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.user.entities import User

class AsyncUserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def find_all(self) -> List[User]:
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass


# 7. API REST usando FastAPI

# src/dev_platform/interface/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from domain.user.entities import User
from application.user.dtos import UserCreateDTO
from infrastructure.database.async_repositories import AsyncSQLUserRepository
from infrastructure.database.session import get_async_session
from shared.exceptions import DomainException, DatabaseException

app = FastAPI(title="Dev Platform API")

# CORS configuração
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, defina origens específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas Pydantic para API
class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    
    class Config:
        orm_mode = True

# Rotas da API
@app.post("/users/", response_model=UserResponse)
async def create_user(user_data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    repository = AsyncSQLUserRepository(session)
    
    try:
        # Simular o caso de uso assíncrono
        user = User(id=None, name=user_data.name, email=user_data.email)
        user.validate()
        saved_user = await repository.save(user)
        return UserResponse(id=saved_user.id, name=saved_user.name, email=saved_user.email)
    
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/", response_model=list[UserResponse])
async def list_users(session: AsyncSession = Depends(get_async_session)):
    repository = AsyncSQLUserRepository(session)
    
    try:
        users = await repository.find_all()
        return [UserResponse(id=u.id, name=u.name, email=u.email) for u in users]
    
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: AsyncSession = Depends(get_async_session)):
    repository = AsyncSQLUserRepository(session)
    
    try:
        user = await repository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(id=user.id, name=user.name, email=user.email)
    
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
