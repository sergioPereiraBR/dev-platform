# ./src/dev_platform/infrastructure/config.py
# -*- coding: utf-8 -*-
"""
Este módulo define a infraestrutura de configuração do DEV Platform,
responsável por carregar e acessar as configurações do sistema.
"""

import os
import json
from typing import List, Dict, Any, Optional, Callable, Type
from dotenv import load_dotenv
from dev_platform.domain.exceptions import ConfigurationException
from dev_platform.application.ports.logger import ILogger
from dev_platform.infrastructure.logging.structured_logger import StructuredLogger

class EnvLoader:
    """
    Responsável por carregar variáveis de ambiente de arquivos .env.
    """
    def __init__(self, environment: str, logger: ILogger):
        self.environment = environment
        self.logger = logger

    def load(self) -> None:
        """
        Carrega variáveis de ambiente do arquivo .env.<environment>.
        """
        dotenv_path = f".env.{self.environment}"
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        full_dotenv_path = os.path.join(base_dir, dotenv_path)
        if os.path.exists(full_dotenv_path):
            load_dotenv(dotenv_path=full_dotenv_path, override=True)
        else:
            if self.environment == "production":
                self.logger.info(
                    f"Arquivo .env.{self.environment} não encontrado em {full_dotenv_path}. Assumindo que as variáveis de ambiente são configuradas externamente."
                )
            else:
                self.logger.info(
                    f"AVISO: Arquivo .env.{self.environment} não encontrado em {full_dotenv_path}. Algumas variáveis de ambiente podem não estar definidas."
                )

class JsonConfigLoader:
    """
    Responsável por carregar configurações de arquivos JSON.
    """
    def __init__(self, environment: str, logger: ILogger):
        self.environment = environment
        self.logger = logger

    def load(self) -> Dict[str, Any]:
        """
        Carrega configurações do arquivo config.<environment>.json.
        """
        config_file_path = f"config.{self.environment}.json"
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        full_config_file_path = os.path.join(base_dir, config_file_path)
        config: Dict[str, Any] = {}
        if os.path.exists(full_config_file_path):
            try:
                with open(full_config_file_path, "r") as f:
                    config = json.load(f)
            except Exception as e:
                self.logger.error(
                    "Erro ao carregar o arquivo de configuração.",
                    config_key="CONFIG_FILE_LOAD_ERROR"
                )
                raise ConfigurationException(
                    config_key="CONFIG_FILE_LOAD_ERROR",
                    reason=f"Erro ao carregar o arquivo de configuração {full_config_file_path}: {e}"
                )
        else:
            self.logger.info(
                f"Arquivo de {full_config_file_path} não encontrado. Usando apenas variáveis de ambiente e padrões.",
                config_key="CONFIG_FILE_NOT_FOUND"
            )
        return config

class ConfigValidator:
    """
    Responsável por validar configurações críticas.
    """
    def __init__(self, environment: str, logger: ILogger):
        self.environment = environment
        self.logger = logger

    def validate(self) -> None:
        """
        Valida se as configurações críticas estão presentes (ex: DATABASE_URL em produção).
        """
        if self.environment == "production":
            if not os.getenv("DATABASE_URL"):
                self.logger.error(
                    "DATABASE_URL não configurada para produção.",
                    config_key="DATABASE_URL"
                )
                raise ConfigurationException(
                    config_key="DATABASE_URL",
                    reason="DATABASE_URL must be set in production environment."
                )

class DatabaseDriverChecker:
    """
    Responsável por garantir o uso de drivers assíncronos na URL do banco de dados.
    """
    @staticmethod
    def ensure_async_driver(url: str) -> str:
        """
        Ajusta a URL do banco para usar driver assíncrono, se necessário.
        """
        if url.startswith("mysql://"):
            return url.replace("mysql://", "mysql+aiomysql://")
        elif url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        elif url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///")
        return url

class ConfigAccessor:
    """
    Responsável por acessar valores de configuração.
    """
    def __init__(self, config: Dict[str, Any], logger: ILogger):
        self._config = config
        self._logger = logger

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém um valor de configuração, preferindo variáveis de ambiente.
        """
        env_key = key.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        value = self._config.get(key, default)
        if value is None:
            self._logger.error(
                f"Configuração obrigatória '{key}' não encontrada.",
                config_key=key
            )
            raise ConfigurationException(
                config_key=key,
                reason=f"Required configuration '{key}' is missing."
            )
        return value

    def get_typed(self, key: str, default: Any = None, cast_type: Type = str) -> Any:
        """
        Obtém um valor de configuração e converte para o tipo desejado.
        """
        value = self.get(key, default)
        if value is None:
            return default
        try:
            if cast_type is bool:
                return str(value).strip().lower() in ("1", "true", "yes", "on")
            return cast_type(value)
        except Exception:
            return default
        
    def get_list(self, key: str, default: Optional[List[str]] = None) -> List[str]:
        """Obtém um valor de configuração como uma lista de strings a partir de um valor separado por vírgulas."""
        value = self.get(key, None)  # Usando get() para pegar o valor bruto
        
        if value is None:
            return default if default is not None else []
        if isinstance(value, list):
            return value
        if not isinstance(value, str) or not value.strip():
            return []

        return [item.strip() for item in value.split(',') if item.strip()]


    def get_all_config(self) -> Dict[str, Any]:
        """
        Retorna todas as configurações efetivas, mesclando arquivo JSON e variáveis de ambiente.
        """
        all_configs = self._config.copy()
        for env_key, env_value in os.environ.items():
            all_configs[env_key.lower().replace(".", "_")] = env_value
        return all_configs

class ConfigurationFacade:
    """
    Fachada para acesso às configurações do sistema, permitindo injeção de dependências.

    Parâmetros de __init__:
        logger: ILogger customizado (opcional)
        env_loader_factory: Callable para criar um EnvLoader customizado (opcional)
        json_loader_factory: Callable para criar um JsonConfigLoader customizado (opcional)
        validator_factory: Callable para criar um ConfigValidator customizado (opcional)
        accessor_factory: Callable para criar um ConfigAccessor customizado (opcional)
    """

    def __init__(
        self,
        logger: Optional[ILogger] = None,
        env_loader_factory: Optional[Callable[[str, ILogger], EnvLoader]] = None,
        json_loader_factory: Optional[Callable[[str, ILogger], JsonConfigLoader]] = None,
        validator_factory: Optional[Callable[[str, ILogger], ConfigValidator]] = None,
        accessor_factory: Optional[Callable[[Dict[str, Any], ILogger], ConfigAccessor]] = None,
        environment: Optional[str] = None,
    ) -> None:
        """
        Inicializa a fachada de configuração, permitindo injeção de dependências para testes ou customização.
        """
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._logger: ILogger = logger or StructuredLogger()
        self._environment: str = environment or os.getenv("ENVIRONMENT", "production")

        # Permite injeção de dependências para facilitar testes/mocks
        env_loader: EnvLoader = (env_loader_factory or EnvLoader)(self._environment, self._logger)
        env_loader.load()
        json_loader: JsonConfigLoader = (json_loader_factory or JsonConfigLoader)(self._environment, self._logger)
        config_dict: Dict[str, Any] = json_loader.load()
        validator: ConfigValidator = (validator_factory or ConfigValidator)(self._environment, self._logger)
        validator.validate()
        self._accessor: ConfigAccessor = (accessor_factory or ConfigAccessor)(config_dict, self._logger)
        self._initialized: bool = True

    @classmethod
    def _reset_singleton(cls) -> None:
        """
        Reseta a instância singleton (apenas para uso em testes).
        """
        cls._instance = None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém um valor de configuração, preferindo variáveis de ambiente.
        """
        return self._accessor.get(key, default)

    def get_typed(self, key: str, default: Any = None, cast_type: Type = str) -> Any:
        """
        Obtém um valor de configuração e converte para o tipo desejado.
        """
        return self._accessor.get_typed(key, default, cast_type)
    
    def get_list(self, key: str, default: Optional[List[str]] = None) -> List[str]:
        """Obtém um valor de configuração como uma lista de strings a partir de um valor separado por vírgulas."""
        value = self.get(key, None)
        if value is None:
            return default if default is not None else []
        if isinstance(value, list):
            return value
        if not isinstance(value, str) or not value.strip():
            return []
        return [item.strip() for item in value.split(',') if item.strip()]
        # return self._accessor.get_list(key, default)


    def get_all_config(self) -> Dict[str, Any]:
        """
        Retorna todas as configurações efetivas, mesclando arquivo JSON e variáveis de ambiente.
        """
        return self._accessor.get_all_config()

    @property
    def database_url(self) -> str:
        """
        Retorna a URL do banco de dados com driver assíncrono garantido.
        """
        url = self.get("DATABASE_URL")
        if not url:
            raise ConfigurationException(
                config_key="DATABASE_URL",
                reason="DATABASE_URL is not configured for the current environment."
            )
        return DatabaseDriverChecker.ensure_async_driver(url)

    @property
    def sync_database_url(self) -> str:
        """
        Retorna a URL do banco de dados sem garantir driver assíncrono.
        """
        url = self.get("DATABASE_URL")
        if not url:
            raise ConfigurationException(
                config_key="DATABASE_URL",
                reason="DATABASE_URL is not configured for the current environment."
            )
        return url
