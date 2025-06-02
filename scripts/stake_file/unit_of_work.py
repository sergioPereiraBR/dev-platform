# src/dev_platform/infrastructure/database/unit_of_work.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from application.user.ports import UnitOfWork as AbstractUnitOfWork
from infrastructure.database.session import db_manager
from infrastructure.database.repositories import SQLUserRepository


class SQLUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self.users: Optional[SQLUserRepository] = None

    async def __aenter__(self):
        # Usar o gerenciador de sessões
        self._session_context = db_manager.get_async_session()
        self._session = await self._session_context.__aenter__()
        self.users = SQLUserRepository(self._session)
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
                await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
                self._session = None
                self.users = None
            except Exception as e:
                self._logger.error(f"Error closing session: {e}")

    async def commit(self):
        if self._session:
            await self._session.commit()

    async def rollback(self):
        if self._session:
            await self._session.rollback()