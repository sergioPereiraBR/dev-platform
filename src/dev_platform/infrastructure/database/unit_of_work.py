# ./src/dev_platform/infrastructure/database/unit_of_work.py
from typing import Optional
from contextlib import AbstractAsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession

from dev_platform.application.user.ports import UnitOfWork
from dev_platform.application.ports.logger import ILogger
from dev_platform.infrastructure.config import CONFIG
from dev_platform.infrastructure.logging.structured_logger import StructuredLogger
from dev_platform.domain.user.interfaces import IUserRepository
from dev_platform.infrastructure.database.session import db_manager
from dev_platform.infrastructure.database.repositories import SQLUserRepository


class SQLUnitOfWork(UnitOfWork):
    def __init__(self, logger: Optional[ILogger] = StructuredLogger(CONFIG__=CONFIG)):
        self._session_context: Optional[AbstractAsyncContextManager[AsyncSession]] = None # Gerenciador de contexto para a sessão assíncrona
        self._logger: ILogger = logger or StructuredLogger(CONFIG__=CONFIG) 
        self._user_repository: Optional[IUserRepository] = None
        self._session: Optional[AsyncSession] = None

    @property
    def user_repository(self) -> Optional[IUserRepository]:
        return self._user_repository

    async def __aenter__(self):
        # Usar o gerenciador de sessões
        self._session_context = db_manager.get_async_session()
        self._session = await self._session_context.__aenter__()
        self._user_repository = SQLUserRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self._session:
            return 
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        except Exception as e:
            self._logger.error(f"Error in transaction cleanup: {e}")
            try:
                await self._session.rollback()
            except:
                pass
        finally:
            try:
                await self._session.close()
                await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
                self._session = None
                self._user_repository = None
            except Exception as e:
                self._logger.error(f"Error closing session: {e}")

    async def commit(self):
        if self._session:
            await self._session.commit()

    async def rollback(self):
        if self._session:
            await self._session.rollback()
