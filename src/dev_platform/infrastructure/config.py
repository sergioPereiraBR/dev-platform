# src/dev_platform/infrastructure/config.py
from dotenv import load_dotenv
import os
import json
from typing import Dict, Any, Optional
import warnings
from domain.user.exceptions import ConfigurationException

    
class Configuration():
    """Classe avançada para gerenciar configurações da aplicação."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # A flag para garantir que a inicialização ocorra apenas uma vez por instância singleton
        if not hasattr(self, '_initialized'):
            self._initialized = False
        
        if not self._initialized:
            self._environment = os.getenv("ENVIRONMENT", "production") # Garante que ENVIRONMENT seja lido primeiro
            self._config = {}
            self._load_environment_variables()
            self._load_config_file()
            self._validate_production_config()
            self._initialized = True # Marca como inicializado

    def _load_environment_variables(self):
        """Carrega variáveis de ambiente de um arquivo .env específico do ambiente."""
        # Determina o nome do arquivo .env com base no ambiente
        dotenv_path = f".env.{self._environment}"
        
        # Carrega as variáveis do arquivo .env específico do ambiente
        # override=True garante que variáveis do .env sobrescrevam variáveis de ambiente existentes
        load_dotenv(dotenv_path=dotenv_path, override=True)
        
        # Se for produção e o arquivo .env.production não for usado,
        # ou se variáveis de ambiente já são definidas externamente,
        # load_dotenv() sem path carrega do .env padrão se existir, ou do ambiente
        # Isso é mais uma garantia, mas o principal é o dotenv_path
        if self._environment == "production" and not os.path.exists(dotenv_path):
             print(f"Aviso: .env.{self._environment} não encontrado. Assumindo variáveis de ambiente serão configuradas externamente para produção.")


    def _load_config_file(self):
        """Carrega e mescla configurações de arquivos JSON específicos do ambiente."""
        config_file_path = f"config.{self._environment}.json"
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r') as f:
                    environment_config = json.load(f)
                    self._config.update(environment_config)
            except Exception as e:
                warnings.warn(f"Erro ao carregar o arquivo de configuração {config_file_path}: {e}")
        
        # Carrega configs padrão se não houver configs específicas do ambiente já carregadas
        # ou se você tiver um arquivo de config padrão.
        # Por simplicidade, assumimos que as configurações são principalmente via .env agora.
        # Se você tiver um config.json padrão, você carregaria ele primeiro e depois faria o update com o específico.

    def _validate_production_config(self):
        """Valida que a DATABASE_URL esteja presente em ambiente de produção."""
        if self._environment == "production":
            if not os.getenv("DATABASE_URL"): # Agora verifica diretamente de os.getenv
                raise ConfigurationException("DATABASE_URL must be set in production environment.")

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém um valor de configuração, preferindo variáveis de ambiente."""
        env_value = os.getenv(key.upper().replace('.', '_')) # Converte key para formato de var de ambiente (ex: logging.level -> LOGGING_LEVEL)
        if env_value is not None:
            return env_value
        return self._config.get(key, default)

    # Remova os métodos get_database_url, get_sync_database_url e get_async_database_url
    # e acesse DATABASE_URL diretamente via get() ou os.getenv()
    # Exemplo: CONFIG.get("DATABASE_URL") ou os.getenv("DATABASE_URL")

    # Mantenha _ensure_async_driver se ainda precisar dele para transformar URLs
    def _ensure_async_driver(self, url: str) -> str:
        # Sua implementação existente de _ensure_async_driver
        if url.startswith("mysql://"):
            return url.replace("mysql://", "mysql+aiomysql://")
        elif url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        elif url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///")
        return url

    @property
    def database_url(self) -> str:
        """Retorna a URL do banco de dados, garantindo driver assíncrono."""
        url = self.get("DATABASE_URL") # Obtém do .env ou ambiente
        if not url:
            raise ConfigurationException("DATABASE_URL is not configured.")
        return self._ensure_async_driver(url)
    
    @property
    def sync_database_url(self) -> str:
        """Retorna a URL do banco de dados, sem garantir driver assíncrono."""
        url = self.get("DATABASE_URL") # Obtém do .env ou ambiente
        if not url:
            raise ConfigurationException("DATABASE_URL is not configured.")
        return url

    def get_config(self) -> Dict[str, Any]:
        """Retorna todas as configurações como um dicionário."""
        return self.config

    # def get(self, path: str, default: Any = None) -> Any:
    #     """Obtém um valor de configuração por caminho pontilhado, ex: 'database.url'"""
    #     keys = path.split(".")
    #     value = self.config
        
    #     for key in keys:
    #         if isinstance(value, dict) and key in value:
    #             value = value[key]
    #         else:
    #             return default
        
    #     return value

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
DATABASE_URL = CONFIG.get("DATABASE_URL") # CONFIG.database_url()
