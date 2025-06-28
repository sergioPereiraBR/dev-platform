# src/dev_platform/infrastructure/logging/structured_logger.py
# -*- coding: utf-8 -*-
"""
Este módulo implementa um logger estruturado usando Loguru,
com suporte a níveis dinâmicos e correlação de logs.
Ele permite a configuração de handlers para diferentes níveis de log
e formatos, incluindo JSON para fácil integração com sistemas de monitoramento.
"""

from typing import Optional, Any, Dict
import os
from uuid import uuid4
from loguru import logger
from dev_platform.infrastructure.config import ConfigurationFacade
from dev_platform.application.ports.logger import ILogger


class StructuredLogger(ILogger):
    """Logger estruturado usando Loguru com suporte a níveis dinâmicos e correlação de logs."""

    def __init__(self, name: str = "DEV Platform", config: ConfigurationFacade = None):
        if config is None:
            raise ValueError("ConfigurationFacade must be provided to StructuredLogger.")

        self._name = name
        self._config = config
        self._configure_logger()

    def _configure_logger(self):
        """Configura o logger com base no ambiente e adiciona handlers."""
        # Remover handlers padrão do Loguru
        logger.remove()

        # Obter nível de log com base no ambiente
        # Usa a configuração injetada
        environment = self._config.get("environment", "production")
        log_level = self._config.get("logging_level", "INFO").upper()
        log_levels = {
            "development": "DEBUG", 
            "test": "DEBUG", 
            "production": "INFO", 
            "DEBUG": "DEBUG", 
            "INFO": "INFO", 
            "WARNING": "WARNING", 
            "ERROR": "ERROR", 
            "CRITICAL": "CRITICAL"
        }
        default_level = log_levels.get(environment, "INFO")
        # effective_log_level = log_levels.get(log_level, "INFO")
        final_level = (
            log_level
            if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            else default_level
        )

        # Configurar handler para console (JSON, todos os níveis)
        logger.add(
            sink="sys.stdout",
            level=final_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message} | {extra}",
            serialize=True,  # Formato JSON
        )

        # logger.add(
        #     sys.stderr,
        #     level=effective_log_level,
        #     format="{time} {level} {message}",
        #     colorize=True,
        #     backtrace=True,
        #     diagnose=True,
        # )


        # Configurar handler para arquivo (apenas ERROR, com rotação)
        if not os.path.exists("logs"):
            os.makedirs("logs")
        logger.add(
            sink=f"logs/{self._name}_{{time:YYYY-MM-DD}}.log",
            level="ERROR",
            rotation="10 MB",
            retention="5 days",
            compression="zip",
            enqueue=True,  # Assíncrono
            serialize=True,  # <-- Adicione esta linha para JSON
        )

        # if environment == "production":
        #     logger.add(
        #         "logs/file.log",
        #         rotation="10 MB",
        #         retention="1 week",
        #         compression="zip",
        #         level=effective_log_level,
        #         format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {process.name: <10} | {thread.name: <10} | {file.name}:{line} {function} - {message}",
        #         serialize=True,
        #         enqueue=True,
        #     )


    def set_correlation_id(self, correlation_id: Optional[str] = None):
        """Define um ID de correlação para rastreamento."""
        self._logger = logger.bind(correlation_id=correlation_id or str(uuid4()))

    def debug(self, message: str, **kwargs: Any) -> None:
        """Registra uma mensagem de nível DEBUG."""
        (self._logger if hasattr(self, "_logger") else logger).bind(**kwargs).debug(message)

    def info(self, message: str, **kwargs: Any) -> None:
        """Registra uma mensagem de nível INFO."""
        (self._logger if hasattr(self, "_logger") else logger).bind(**kwargs).info(message)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Registra uma mensagem de nível WARNING."""
        (self._logger if hasattr(self, "_logger") else logger).bind(**kwargs).warning(message)

    def error(self, message: str, **kwargs: Any) -> None:
        """Registra uma mensagem de nível ERROR."""
        (self._logger if hasattr(self, "_logger") else logger).bind(**kwargs).error(message)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Registra uma mensagem de nível CRITICAL."""
        (self._logger if hasattr(self, "_logger") else logger).bind(**kwargs).critical(message)

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        logger.log(level.upper(), message, **kwargs)


    # NOVO MÉTODO PARA SHUTDOWN GRACIOSO DO LOGGER
    @staticmethod
    def shutdown():
        """
        Garante que todas as mensagens enfileiradas pelo Loguru sejam processadas
        e que os handlers sejam removidos. Isso é crucial para limpar recursos
        assíncronos do logger antes que o loop de eventos feche.
        """
        logger.shutdown()  # Processa todas as mensagens enfileiradas
        logger.remove()  # Remove todos os handlers para evitar vazamentos de recursos
