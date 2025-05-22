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

        print(f"DEBUG: DATABASE_URL lida do .env: {self.config['database']['url']}")
        
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
                return "mysql+aiomysql://root:Malato#01@127.0.0.1:3306/user_management" # "sqlite:///./dev.db"
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
