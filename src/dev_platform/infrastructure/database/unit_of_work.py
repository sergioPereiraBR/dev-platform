# ./src/dev_platform/infrastructure/database/unit_of_work.py
# -*- coding: utf-8 -*-
"""
Este módulo implementa o padrão Unit of Work para gerenciar transações de banco de dados
e repositórios de usuários usando SQLAlchemy.
"""

from typing import Optional
from contextlib import AbstractAsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession

from dev_platform.infrastructure.config import ConfigurationFacade
from dev_platform.application.user.ports import UnitOfWork
from dev_platform.application.ports.logger import ILogger
from dev_platform.infrastructure.logging.structured_logger import StructuredLogger
from dev_platform.domain.user.interfaces import IUserRepository
from dev_platform.infrastructure.database.session import db_manager
from dev_platform.infrastructure.database.repositories import SQLUserRepository


class SQLUnitOfWork(UnitOfWork):
    def __init__(self, logger: Optional[ILogger] = StructuredLogger(CONFIG__=ConfigurationFacade())):
        self._session_context: Optional[AbstractAsyncContextManager[AsyncSession]] = None # Gerenciador de contexto para a sessão assíncrona
        self._logger: ILogger = logger or StructuredLogger(CONFIG__=ConfigurationFacade()) 
        self._user_repository: Optional[IUserRepository] = None
        self._session: Optional[AsyncSession] = None

    @property
    def user_repository(self) -> Optional[IUserRepository]:
        return self._user_repository

    async def __aenter__(self):
        # Usar o gerenciador de sessões
        self._session_context = db_manager.get_async_session()
        self._session = await self._session_context.__aenter__()
        self._user_repository = SQLUserRepository(self._session, logger=self._logger)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Delega TODA a lógica de saída para o gerenciador de sessão.
        # O gerenciador já cuida do commit, rollback e fechamento.
        if self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        # Limpa as referências
        self._session = None
        self._user_repository = None
        self._session_context = None

    async def commit(self):
        if self._session:
            await self._session.commit()

    async def rollback(self):
        if self._session:
            await self._session.rollback()
