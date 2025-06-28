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
from dev_platform.application.user.ports import UnitOfWork
from dev_platform.domain.user.interfaces import IUserRepository 
from dev_platform.infrastructure.database.session import DatabaseSessionManager # Importa



class SQLUnitOfWork(UnitOfWork):
    def __init__(self, logger: ILogger, user_repository: IUserRepository, db_session_manager: DatabaseSessionManager):
        self._logger: ILogger = logger
        self._user_repository: IUserRepository = user_repository # Atribui o repositório injetado
        self._db_session_manager: DatabaseSessionManager = db_session_manager
        self._session_context: Optional[AbstractAsyncContextManager[AsyncSession]]=None # Gerenciador de contexto para a sessão assíncrona
        self._session: Optional[AsyncSession] = None

    @property
    def user_repository(self) -> IUserRepository:
        return self._user_repository

    async def __aenter__(self):
        self._session_context = self._db_session_manager.get_async_session()
        self._session = await self._session_context.__aenter__()
        if hasattr(self._user_repository, '_session'):
            self._user_repository.set_session(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                # Se uma exceção ocorreu, faz o rollback
                self._logger.warning("Ocorreu uma exceção, revertendo a transação", exc_info=(exc_type, exc_val, exc_tb))
                await self._session.rollback()
            else:
                # Se não houve exceção, faz o commit
                await self._session.commit()
        finally:
            # Garante que a sessão seja fechada
            await self._session.close()
            self._session = None

    async def _commit(self):
        await self._session.commit()

    async def _rollback(self):
        await self._session.rollback()
