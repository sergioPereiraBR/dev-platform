# src/dev_platform/infrastructure/config.py
from dotenv import load_dotenv
import os
from typing import Dict, Any
from shared.exceptions import ConfigurationException

load_dotenv()

class Configuration:
    """Classe para gerenciar configurações da aplicação."""
    
    @staticmethod
    def get_database_url() -> str:
        """Obtém a URL do banco de dados ou lança uma exceção."""
        url = os.getenv("DATABASE_URL")
        if not url:
            # Opção 1: Lançar exceção
            raise ConfigurationException("DATABASE_URL environment variable is not set")
            # Opção 2: Usar valor padrão SQLite para desenvolvimento
            # return "sqlite:///./dev.db"
        return url
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Retorna todas as configurações como um dicionário."""
        return {
            "database_url": Configuration.get_database_url(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "False").lower() == "true"
        }

# Para uso fácil em outros módulos
CONFIG = Configuration.get_config()
DATABASE_URL = CONFIG["database_url"]


# #   src/dev_platform/infrastructure/config.py (similar to your config.py, but in the Infrastructure layer)
# from dotenv import load_dotenv
# import os

# load_dotenv()
# DATABASE_URL = os.getenv("DATABASE_URL")
# #   You might want to handle the case where DATABASE_URL is not set