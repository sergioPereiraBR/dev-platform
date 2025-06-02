# src/dev_platform/infrastructure/config.py
from dotenv import load_dotenv
import os
import json
from typing import Dict, Any, Optional
from domain.user.exceptions import ConfigurationException

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
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.config = {}
        self._load_config()
        self._initialized = True

    def _load_config(self):
        """Carrega configurações baseadas no ambiente."""
        # Configurações base aplicáveis a todos os ambientes
        self.config = {
            "database": {
                "url": self._get_database_url_by_environment(),
                "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
                "echo": os.getenv("DB_ECHO", "False").lower() == "true",
                "pool_pre_ping": True
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

    def _get_database_url_by_environment(self) -> str:
        """Obtém a URL do banco baseada no ambiente."""
        # Primeiro tenta pegar do ambiente
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return self._ensure_async_driver(db_url)
        
        # URLs padrão por ambiente
        default_urls = {
            "development": "mysql+aiomysql://root:Malato#01@127.0.0.1:3306/user_management", # "sqlite+aiosqlite:///./dev.db",
            "test": "sqlite+aiosqlite:///./test.db",
            "production": "mysql+aiomysql://root:Malato#01@127.0.0.1:3306/user_management", # None  # Deve ser definida via variável de ambiente
        }
        
        url = default_urls.get(self.environment)
        if not url and self.environment == "production":
            raise ConfigurationException(
                "DATABASE_URL", 
                "DATABASE_URL environment variable is required for production"
            )
        
        return url or default_urls["development"]

    def _ensure_async_driver(self, url: str) -> str:
        """Garante que a URL use driver assíncrono."""
        # Mapeamento de drivers síncronos para assíncronos
        driver_mapping = {
            "mysql://": "mysql+aiomysql://",
            "mysql+pymysql://": "mysql+aiomysql://",
            "postgresql://": "postgresql+asyncpg://",
            "postgres://": "postgresql+asyncpg://",
            "sqlite://": "sqlite+aiosqlite://",
        }
        
        for sync_driver, async_driver in driver_mapping.items():
            if url.startswith(sync_driver):
                return url.replace(sync_driver, async_driver, 1)
        
        # Se já for assíncrono ou não reconhecido, retorna como está
        return url

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
            raise ConfigurationException("DATABASE_URL", "Database URL is not configured")
        return url

    def get_sync_database_url(self) -> str:
        """Obtém a URL síncrona do banco de dados."""
        async_url = self.get_database_url()
        
        # Mapeamento de drivers assíncronos para síncronos
        driver_mapping = {
            "mysql+aiomysql://": "mysql+pymysql://",
            "postgresql+asyncpg://": "postgresql://",
            "sqlite+aiosqlite://": "sqlite://",
        }
        
        for async_driver, sync_driver in driver_mapping.items():
            if async_url.startswith(async_driver):
                return async_url.replace(async_driver, sync_driver, 1)
        
        return async_url

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

    def is_development(self) -> bool:
        """Verifica se está em ambiente de desenvolvimento."""
        return self.environment == "development"

    def is_production(self) -> bool:
        """Verifica se está em ambiente de produção."""
        return self.environment == "production"

    def is_test(self) -> bool:
        """Verifica se está em ambiente de teste."""
        return self.environment == "test"


# Instância Singleton para uso fácil em outros módulos
CONFIG = Configuration()
DATABASE_URL = CONFIG.get_database_url()
