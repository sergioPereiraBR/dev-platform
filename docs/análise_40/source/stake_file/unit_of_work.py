# ./src/dev_platform/infrastructure/database/unit_of_work.py
# -*- coding: utf-8 -*-
"""
Este módulo implementa o padrão Unit of Work para gerenciar transações de banco de dados
e repositórios de usuários usando SQLAlchemy.
"""

from typing import Optional
from contextlib import AbstractAsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession

from dev_platform.application.ports.logger import ILogger
from dev_platform.infrastructure.database.session import db_manager
from dev_platform.application.user.ports import UnitOfWork
from dev_platform.domain.user.interfaces import IUserRepository 


class SQLUnitOfWork(UnitOfWork):
    def __init__(self, logger: ILogger, user_repository: IUserRepository):
        self._session_context: Optional[AbstractAsyncContextManager[AsyncSession]]=None # Gerenciador de contexto para a sessão assíncrona
        self._logger: ILogger = logger
        self._user_repository: IUserRepository = user_repository # Atribui o repositório injetado
        self._session: Optional[AsyncSession] = None

    @property
    def user_repository(self) -> IUserRepository:
        return self._user_repository

    async def __aenter__(self):
        # Usar o gerenciador de sessões
        self._session_context = db_manager.get_async_session()
        self._session = await self._session_context.__aenter__()
        if hasattr(self._user_repository, '_session'):
            self._user_repository.set_session(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Delega TODA a lógica de saída para o gerenciador de sessão.
        # O gerenciador já cuida do commit, rollback e fechamento.
        if self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        # Limpa as referências
        self._session = None
        self._session_context = None

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
