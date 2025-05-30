# src/dev_platform/infrastructure/database/repositories.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from application.user.ports import UserRepository
from domain.user.entities import User
from domain.user.value_objects import UserName, Email
from infrastructure.database.models import UserModel


class SQLUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, user: User) -> User:
        try:
            if user.id is None:
                # Create new user
                db_user = UserModel(
                    name=user.name.value,
                    email=user.email.value
                )
                self._session.add(db_user)
                await self._session.flush()
                
                # Return user with the ID
                return User(
                    id=db_user.id,
                    name=user.name,
                    email=user.email
                )
            else:
                # Update existing user
                result = await self._session.execute(
                    select(UserModel).where(UserModel.id == user.id)
                )
                db_user = result.scalars().first()
                
                if not db_user:
                    raise ValueError(f"User with ID {user.id} not found")
                
                db_user.name = user.name.value
                db_user.email = user.email.value
                await self._session.flush()
                
                return User(
                    id=db_user.id,
                    name=user.name,
                    email=user.email
                )
                
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
                return User(
                    id=db_user.id,
                    name=UserName(db_user.name),
                    email=Email(db_user.email)
                )
            return None
        except Exception as e:
            raise RuntimeError(f"Error finding user by email: {e}")
    
    async def find_all(self) -> List[User]:
        try:
            result = await self._session.execute(select(UserModel))
            db_users = result.scalars().all()
            return [
                User(
                    id=u.id,
                    name=UserName(u.name),
                    email=Email(u.email)
                )
                for u in db_users
            ]
        except Exception as e:
            raise RuntimeError(f"Error finding all users: {e}")
    
    async def find_by_id(self, user_id: int) -> Optional[User]:
        try:
            result = await self._session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            db_user = result.scalars().first()
            
            if db_user:
                return User(
                    id=db_user.id,
                    name=UserName(db_user.name),
                    email=Email(db_user.email)
                )
            return None
        except Exception as e:
            raise RuntimeError(f"Error finding user by id: {e}")
    
    async def delete(self, user_id: int) -> bool:
        try:
            result = await self._session.execute(
                delete(UserModel).where(UserModel.id == user_id)
            )
            return result.rowcount > 0
        except Exception as e:
            await self._session.rollback()
            raise RuntimeError(f"Error deleting user: {e}")
    
    async def find_by_name_contains(self, name_part: str) -> List[User]:
        """Find users whose name contains the given string."""
        try:
            result = await self._session.execute(
                select(UserModel).where(UserModel.name.contains(name_part))
            )
            db_users = result.scalars().all()
            return [
                User(
                    id=u.id,
                    name=UserName(u.name),
                    email=Email(u.email)
                )
                for u in db_users
            ]
        except Exception as e:
            raise RuntimeError(f"Error searching users by name: {e}")
    
    async def count(self) -> int:
        """Count total number of users."""
        try:
            from sqlalchemy import func
            result = await self._session.execute(
                select(func.count(UserModel.id))
            )
            return result.scalar()
        except Exception as e:
            raise RuntimeError(f"Error counting users: {e}")
