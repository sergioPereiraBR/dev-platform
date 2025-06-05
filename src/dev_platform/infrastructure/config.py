# src/dev_platform/infrastructure/config.py
from dotenv import load_dotenv
import os
import json
from typing import Dict, Any, Optional
import warnings
from domain.user.exceptions import ConfigurationException


# Definição de exceções para configuração
class ConfigurationException(Exception):
    pass

class Configuration:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # A flag para garantir que a inicialização ocorra apenas uma vez por instância singleton
        if not hasattr(self, '_initialized') or not self._initialized:
            self._initialized = False # Garante que a flag seja redefinida se a instância já existia, mas não inicializada
            self._environment = os.getenv("ENVIRONMENT", "production") # Garante que ENVIRONMENT seja lido primeiro
            self._config = {}
            self._load_environment_variables()
            self._load_config_file()
            self._validate_production_config()
            self._initialized = True # Marca como inicializado

    def _load_environment_variables(self):
        """
        Carrega variáveis de ambiente de um arquivo .env específico do ambiente.
        Por exemplo, se ENVIRONMENT=development, ele tentará carregar .env.development.
        """
        dotenv_path = f".env.{self._environment}"
        
        # O base_dir é importante se o script não for executado da raiz do projeto.
        # Assumindo que os arquivos .env estão na raiz do projeto.
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        full_dotenv_path = os.path.join(base_dir, dotenv_path)

        if os.path.exists(full_dotenv_path):
            load_dotenv(dotenv_path=full_dotenv_path, override=True)
            # print(f"INFO: Carregado .env de {full_dotenv_path}")
        else:
            # Para produção, pode ser normal que as variáveis de ambiente venham do deploy.
            # Para outros ambientes, avise se o arquivo não for encontrado.
            if self._environment == "production":
                print(f"AVISO: Arquivo .env.{self._environment} não encontrado em {full_dotenv_path}. Assumindo que as variáveis de ambiente são configuradas externamente para produção.")
            else:
                warnings.warn(f"AVISO: Arquivo .env.{self._environment} não encontrado em {full_dotenv_path}. Algumas variáveis de ambiente podem não estar definidas.")

    def _load_config_file(self):
        """
        Carrega e mescla configurações de arquivos JSON específicos do ambiente.
        Ex: config.development.json, config.test.json.
        """
        config_file_path = f"config.{self._environment}.json"
        
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        full_config_file_path = os.path.join(base_dir, config_file_path)

        if os.path.exists(full_config_file_path):
            try:
                with open(full_config_file_path, 'r') as f:
                    print(f"INFO: Abrindo arquivo de configuração {full_config_file_path}")
                    environment_config = json.load(f)
                    self._config.update(environment_config)
                    print(f"INFO: Carregado arquivo de configuração {full_config_file_path}")
            except Exception as e:
                warnings.warn(f"Erro ao carregar o arquivo de configuração {full_config_file_path}: {e}")
        else:
            print(f"INFO: Arquivo de configuração {full_config_file_path} não encontrado. Usando apenas variáveis de ambiente e padrões.")

    def _validate_production_config(self):
        """Valida que a DATABASE_URL esteja presente em ambiente de produção."""
        if self._environment == "production":
            # Agora verifica diretamente de os.getenv, que já foi populado pelo load_dotenv
            if not os.getenv("DATABASE_URL"):
                raise ConfigurationException("DATABASE_URL must be set in production environment.")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém um valor de configuração, preferindo variáveis de ambiente.
        Converte a chave de ponto (ex: 'logging.level') para underscore maiúsculo (ex: 'LOGGING_LEVEL').
        """
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key) 
        if env_value is not None:
            return env_value
        # Se não estiver nas variáveis de ambiente, tenta pegar do arquivo JSON (se carregado)
        return self._config.get(key, default)

    def get_all_config(self) -> Dict[str, Any]:
        """Retorna todas as configurações carregadas (mescladas de arquivos e ambiente)."""
        # Itera sobre os atributos que se parecem com chaves de configuração e os combina com _config
        # ou, mais simples, crie um dicionário combinando as variáveis de ambiente com as configs de arquivo
        all_configs = self._config.copy()
        # Adiciona variáveis de ambiente que podem não estar no _config
        for env_key, env_value in os.environ.items():
            # Pode-se adicionar uma lógica para filtrar apenas variáveis relevantes se necessário
            all_configs[env_key.lower().replace('_', '.')] = env_value
        return all_configs

    def _ensure_async_driver(self, url: str) -> str:
        """Garante que a URL do banco de dados use um driver assíncrono."""
        if url.startswith("mysql://"):
            return url.replace("mysql://", "mysql+aiomysql://")
        elif url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        elif url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///")
        return url

    @property
    def database_url(self) -> str:
        """Retorna a URL do banco de dados com driver assíncrono garantido."""
        url = self.get("DATABASE_URL")
        if not url:
            raise ConfigurationException("DATABASE_URL is not configured for the current environment.")
        return self._ensure_async_driver(url)
    
    @property
    def sync_database_url(self) -> str:
        """Retorna a URL do banco de dados sem garantir driver assíncrono (para ferramentas síncronas)."""
        url = self.get("DATABASE_URL")
        if not url:
            raise ConfigurationException("DATABASE_URL is not configured for the current environment.")
        return url

# Instância singleton da configuração
CONFIG = Configuration()
