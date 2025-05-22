# src/dev_platform/infrastructure/database/async_repositories.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.user.entities import User
from domain.user.interfaces import AsyncUserRepository  # Precisamos criar esta interface
from infrastructure.database.models import UserModel
from shared.exceptions import DatabaseException

class AsyncSQLUserRepository(AsyncUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, user: User) -> User:
        try:
            db_user = UserModel(name=user.name, email=user.email)
            self.session.add(db_user)
            await self.session.flush()
            user.id = db_user.id
            return user
        except Exception as e:
            await self.session.rollback()
            raise DatabaseException(f"Error saving user: {e}")
    
    async def find_all(self) -> List[User]:
        try:
            result = await self.session.execute(select(UserModel))
            db_users = result.scalars().all()
            return [User(id=u.id, name=u.name, email=u.email) for u in db_users]
        except Exception as e:
            raise DatabaseException(f"Error finding all users: {e}")
    
    async def find_by_id(self, user_id: int) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            db_user = result.scalars().first()
            if db_user:
                return User(id=db_user.id, name=db_user.name, email=db_user.email)
            return None
        except Exception as e:
            raise DatabaseException(f"Error finding user by id: {e}")
    
    async def find_by_email(self, email: str) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            db_user = result.scalars().first()
            if db_user:
                return User(id=db_user.id, name=db_user.name, email=db_user.email)
            return None
        except Exception as e:
            raise DatabaseException(f"Error finding user by email: {e}")
