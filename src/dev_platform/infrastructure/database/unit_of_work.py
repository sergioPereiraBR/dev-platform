# src/dev_platform/infrastructure/database/unit_of_work.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from application.user.ports import UnitOfWork as AbstractUnitOfWork
from infrastructure.database.session import AsyncSessionLocal
from infrastructure.database.repositories import SQLUserRepository

class SQLUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self._session: Optional[AsyncSession] = None
    
    async def __aenter__(self):
        self._session = AsyncSessionLocal()
        self.users = SQLUserRepository(self._session)
        return self
    
    # async def __aexit__(self, exc_type, exc_val, exc_tb):
    #     if self._session:
    #         if exc_type is not None:
    #             await self._session.rollback()
    #         await self._session.close()

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
            except Exception as e:
                self._logger.error(f"Error closing session: {e}")
    
    async def commit(self):
        if self._session:
            await self._session.commit()
