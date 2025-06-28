# ./src/dev_platform/infrastructure/database/repositories.py
# -*- coding: utf-8 -*-
"""
This module implements the SQLAlchemy repository for the User entity,
providing methods for CRUD operations and queries.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dev_platform.domain.user.interfaces import IUserRepository
from dev_platform.domain.user.entities import User
from dev_platform.domain.user.value_objects import UserName, Email
from dev_platform.domain.exceptions import (
    DataIntegrityException,
    DatabaseException, 
)
from dev_platform.domain.user.user_exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException
)
from dev_platform.infrastructure.database.models import UserModel
from dev_platform.application.ports.logger import ILogger
from .exception_handler import handle_repository_errors, IExceptionMapper


class SQLUserRepository(IUserRepository):
    """SQLAlchemy implementation of the IUserRepository interface."""
    def __init__(self, session: AsyncSession, logger: ILogger, exception_mapper: IExceptionMapper):
        self._session: AsyncSession = session
        self._logger: ILogger = logger
        self._exception_mapper: IExceptionMapper = exception_mapper # Apenas armazena o mapper

    def set_session(self, session: AsyncSession):
        self._session = session

    def _convert_to_domain_user(self, db_user: UserModel) -> User:
        """Convert database model to domain entity."""
        try:
            return User(
                id=db_user.id, name=UserName(db_user.name), email=Email(db_user.email)
            )
        except ValueError as e:
            self._logger.error(
                f"Data conversion error for user {db_user.id}: {str(e)}"
            )
            # This should not happen if database constraints are properly set
            raise DatabaseException(
                operation="data_conversion",
                reason=f"Invalid data in database: {str(e)}",
                original_exception=e,
            )

    @handle_repository_errors    
    async def add(self, user: User) -> User:
        """Adds a new user to the database."""
        if user.id is not None:
            raise DatabaseException(operation="add", reason="Cannot add a user that already has an ID.")
        db_user = UserModel(name=user.name.value, email=user.email.value)
        self._session.add(db_user)
        await self._session.flush()
        return user.with_id(db_user.id)  # Retorna nova instância com ID

    @handle_repository_errors    
    async def update(self, user: User) -> User:
        """Updates an existing user in the database."""
        if user.id is None:
            raise UserNotFoundException("None")
        # O find_by_id já foi feito no caso de uso, podemos ir direto para o merge ou update.
        # A forma mais segura é buscar e atualizar para garantir que o registro existe.
        db_user = await self._session.get(UserModel, user.id)
        if not db_user:
            raise UserNotFoundException(str(user.id))
        await self._session.merge(
            UserModel(id=user.id, name=user.name.value, email=user.email.value)
        )
        await self._session.flush()
        return user

    @handle_repository_errors
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        db_user = result.scalars().first()
        if db_user:
            return self._convert_to_domain_user(db_user)
        return None

    @handle_repository_errors
    async def find_all(self) -> List[User]:
        """Find all users in the database."""
        result = await self._session.execute(select(UserModel))
        db_users = result.scalars().all()
        return [self._convert_to_domain_user(db_user) for db_user in db_users]

    @handle_repository_errors
    async def find_by_id(self, user_id: int) -> Optional[User]:
        """Find a user by ID."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        db_user = result.scalars().first()
        if db_user:
            return self._convert_to_domain_user(db_user)
        return None

    @handle_repository_errors
    async def find_by_ids(self, user_ids: List[int]) -> List[User]:
        """Find users by a list of IDs."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id.in_(user_ids))
        )
        return [self._convert_to_domain_user(u) for u in result.scalars().all()]

    @handle_repository_errors
    async def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        # First check if user exists
        existing_user = await self.find_by_id(user_id)
        if not existing_user:
            raise UserNotFoundException(str(user_id))
        # Perform deletion
        result = await self._session.execute(
            delete(UserModel).where(UserModel.id == user_id)
        )
        success = result.rowcount > 0
        if success:
            await self._session.flush()
        return success

    @handle_repository_errors
    async def find_by_name_contains(self, name_part: str) -> List[User]:
        """Find users whose name contains the given string."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.name.contains(name_part))
        )
        db_users = result.scalars().all()

        return [self._convert_to_domain_user(db_user) for db_user in db_users]

    @handle_repository_errors
    async def count(self) -> int:  # Nota
        """Count total number of users."""
        result = await self._session.execute(select(func.count(UserModel.id)))
        count = result.scalar()
        return count if count is not None else 0
