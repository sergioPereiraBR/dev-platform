# src/dev_platform/infrastructure/logging/structured_logger.py

from typing import Dict, Any, Optional
import os
from uuid import uuid4
from loguru import logger
from infrastructure.config import CONFIG
from application.user.ports import Logger as LoggerPort


class StructuredLogger(LoggerPort):
    """Logger estruturado usando Loguru com suporte a níveis dinâmicos e correlação de logs."""
    
    def __init__(self, name: str = "DEV Platform"):
        self._name = name
        self._configure_logger()

    def _configure_logger(self):
        """Configura o logger com base no ambiente e adiciona handlers."""
        # Remover handlers padrão do Loguru
        logger.remove()

        # Obter nível de log com base no ambiente
        environment = CONFIG.get("environment", "production")
        log_level = CONFIG.get("logging.level", "INFO").upper()
        log_levels = {
            "development": "DEBUG",
            "test": "DEBUG",
            "production": "INFO"
        }
        default_level = log_levels.get(environment, "INFO")
        final_level = log_level if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] else default_level

        # Configurar handler para console (JSON, todos os níveis)
        logger.add(
            sink="sys.stdout",
            level=final_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message} | {extra}",
            serialize=True  # Formato JSON
        )

        # Configurar handler para arquivo (apenas ERROR, com rotação)
        if not os.path.exists("logs"):
            os.makedirs("logs")
        logger.add(
            sink=f"logs/{self._name}_{{time:YYYY-MM-DD}}.log",
            level="ERROR",
            rotation="10 MB",
            retention="5 days",
            compression="zip",
            enqueue=True  # Assíncrono
        )

    def set_correlation_id(self, correlation_id: Optional[str] = None):
        """Define um ID de correlação para rastreamento."""
        logger.contextualize(correlation_id=correlation_id or str(uuid4()))

    def info(self, message: str, **kwargs):
        """Registra uma mensagem de nível INFO."""
        logger.bind(**kwargs).info(message)

    def error(self, message: str, **kwargs):
        """Registra uma mensagem de nível ERROR."""
        logger.bind(**kwargs).error(message)

    def warning(self, message: str, **kwargs):
        """Registra uma mensagem de nível WARNING."""
        logger.bind(**kwargs).warning(message)

    def debug(self, message: str, **kwargs):
        """Registra uma mensagem de nível DEBUG."""
        logger.bind(**kwargs).debug(message)
    
    def critical(self, message: str, **kwargs):
        """Registra uma mensagem de nível CRITICAL."""
        logger.bind(**kwargs).critical(message)

    # NOVO MÉTODO PARA SHUTDOWN GRACIOSO DO LOGGER
    @staticmethod
    def shutdown():
        """
        Garante que todas as mensagens enfileiradas pelo Loguru sejam processadas
        e que os handlers sejam removidos. Isso é crucial para limpar recursos
        assíncronos do logger antes que o loop de eventos feche.
        """
        logger.complete() # Processa todas as mensagens enfileiradas
        logger.remove()  # Remove todos os handlers para evitar vazamentos de recursos
