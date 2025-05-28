# src/dev_platform/infrastructure/database/repositories.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from application.user.ports import UserRepository
from domain.user.entities import User
from infrastructure.database.models import UserModel

class SQLUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, user: User) -> User:
        try:
            db_user = UserModel(name=user.name, email=user.email)
            self._session.add(db_user)
            await self._session.flush()
            
            # Retorna o user com o ID atualizado
            return User(id=db_user.id, name=user.name, email=user.email)
        except Exception as e:
            await self._session.rollback()
            raise RuntimeError(f"Error saving user: {e}")
    
    async def find_by_email(self, email: str) -> Optional[User]:
        try:
            result = await self._session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            db_user = result.scalars().first()
            
            if db_user:
                return User(id=db_user.id, name=db_user.name, email=db_user.email)
            return None
        except Exception as e:
            raise RuntimeError(f"Error finding user by email: {e}")
    
    async def find_all(self) -> List[User]:
        try:
            result = await self._session.execute(select(UserModel))
            db_users = result.scalars().all()
            return [User(id=u.id, name=u.name, email=u.email) for u in db_users]
        except Exception as e:
            raise RuntimeError(f"Error finding all users: {e}")
    
    async def find_by_id(self, user_id: int) -> Optional[User]:
        try:
            result = await self._session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            db_user = result.scalars().first()
            if db_user:
                return User(id=db_user.id, name=db_user.name, email=db_user.email)
            return None
        except Exception as e:
            raise RuntimeError(f"Error finding user by id: {e}")