# ./src/dev_platform/infrastructure/database/repositories.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dev_platform.domain.user.interfaces import IUserRepository
from dev_platform.domain.user.entities import User
from dev_platform.domain.user.value_objects import UserName, Email
from dev_platform.domain.user.exceptions import (
    DatabaseException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from dev_platform.infrastructure.database.models import UserModel


class SQLUserRepository(IUserRepository):
    """SQLAlchemy implementation of the IUserRepository interface."""
    def __init__(self, session: AsyncSession):
        self._session = session

    def _convert_to_domain_user(self, db_user: UserModel) -> User:
        """Convert database model to domain entity."""
        try:
            return User(
                id=db_user.id, name=UserName(db_user.name), email=Email(db_user.email)
            )
        except ValueError as e:
            # This should not happen if database constraints are properly set
            raise DatabaseException(
                operation="data_conversion",
                reason=f"Invalid data in database: {str(e)}",
                original_exception=e,
            )

    async def save(self, user: User) -> User:
        """Save a user to the database."""
        try:
            if user.id is None:
                # Create new user
                db_user = UserModel(name=user.name.value, email=user.email.value)
                self._session.add(db_user)
                await self._session.flush()

                # Return user with the generated ID
                return User(id=db_user.id, name=user.name, email=user.email)
            else:
                # Update existing user
                result = await self._session.execute(
                    select(UserModel).where(UserModel.id == user.id)
                )
                db_user = result.scalars().first()

                if not db_user:
                    raise UserNotFoundException(str(user.id))

                db_user.name = user.name.value
                db_user.email = user.email.value
                await self._session.flush()

                return User(id=db_user.id, name=user.name, email=user.email)

        except UserNotFoundException:
            # Re-raise domain exceptions as-is
            raise
        except UserAlreadyExistsException:
            # Re-raise domain exceptions as-is
            raise
        except SQLAlchemyError as e:
            RepositoryExceptionHandler.handle_sqlalchemy_error(
                operation="save_user", 
                error=e, 
                user_id=user.id, 
                name=user.name.value, 
                email=user.email.value
            )
        except Exception as e:
            RepositoryExceptionHandler.handle_generic_error(
                operation="save_user", 
                error=e, 
                user_id=user.id, 
                email=user.email.value
            )

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address."""
        try:
            result = await self._session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            db_user = result.scalars().first()

            if db_user:
                return self._convert_to_domain_user(db_user)
            return None

        except SQLAlchemyError as e:
            RepositoryExceptionHandler.handle_sqlalchemy_error(operation="find_by_email", error=e, email=email)
        except Exception as e:
            RepositoryExceptionHandler.handle_generic_error(operation="find_by_email", error=e, email=email)
        return None

    async def find_all(self) -> List[User]:
        """Find all users in the database."""
        try:
            result = await self._session.execute(select(UserModel))
            db_users = result.scalars().all()

            return [self._convert_to_domain_user(db_user) for db_user in db_users]

        except SQLAlchemyError as e:
            RepositoryExceptionHandler.handle_sqlalchemy_error(operation="find_all_users", error=e)
        except Exception as e:
            RepositoryExceptionHandler.handle_generic_error(operation="find_all_users", error=e)

        return (
            []
        )  # Nota de teste: Retornar None aqui pode ser problemático, pois o método deve retornar uma lista vazia se não houver usuários. Considere retornar uma lista vazia em vez de None.

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """Find a user by ID."""
        try:
            result = await self._session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            db_user = result.scalars().first()

            if db_user:
                return self._convert_to_domain_user(db_user)
            return None

        except SQLAlchemyError as e:
            RepositoryExceptionHandler.handle_sqlalchemy_error(
                operation="find_by_id", error=e, user_id=user_id
            )
        except Exception as e:
            RepositoryExceptionHandler.handle_generic_error(
                operation="find_by_id", error=e, user_id=user_id
            )

        return None

    async def find_by_ids(self, user_ids: List[int]) -> List[User]:
        """Find users by a list of IDs."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id.in_(user_ids))
        )

        return [self._convert_to_domain_user(u) for u in result.scalars().all()]

    async def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        try:
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

        except UserNotFoundException:
            # Re-raise domain exceptions as-is
            raise
        except SQLAlchemyError as e:
            RepositoryExceptionHandler.handle_sqlalchemy_error(
                operation="delete_user", error=e, user_id=user_id
            )
        except Exception as e:
            RepositoryExceptionHandler.handle_generic_error(
                operation="delete_user", error=e, user_id=user_id
            )  # Nota de teste: Retornar False se a exclusão falhar, o que é mais intuitivo do que retornar None.
        return False

    async def find_by_name_contains(self, name_part: str) -> List[User]:
        """Find users whose name contains the given string."""
        try:
            result = await self._session.execute(
                select(UserModel).where(UserModel.name.contains(name_part))
            )
            db_users = result.scalars().all()

            return [self._convert_to_domain_user(db_user) for db_user in db_users]

        except SQLAlchemyError as e:
            RepositoryExceptionHandler.handle_sqlalchemy_error(
                operation="find_by_name_contains", error=e, name_part=name_part
            )
        except Exception as e:
            RepositoryExceptionHandler.handle_generic_error(
                operation="find_by_name_contains", error=e, name_part=name_part
            )

        return []

    async def count(self) -> int:  # Nota
        """Count total number of users."""
        try:
            result = await self._session.execute(select(func.count(UserModel.id)))
            count = result.scalar()
            return count if count is not None else 0

        except SQLAlchemyError as e:
            RepositoryExceptionHandler.handle_sqlalchemy_error(operation="count_users", error=e)
        except Exception as e:
            RepositoryExceptionHandler.handle_generic_error(operation="count_users", error=e)

        return 0  # Nota de teste: Retornar 0 se a contagem falhar, o que é mais intuitivo do que retornar None.


class RepositoryExceptionHandler:
    """Utility class for handling repository exceptions consistently."""

    @staticmethod
    def handle_sqlalchemy_error(operation: str, error: SQLAlchemyError, **context):
        """Handle SQLAlchemy specific errors."""
        if isinstance(error, IntegrityError):
            if (
                "email" in str(error.orig).lower()
                and "unique" in str(error.orig).lower()
            ):
                email = context.get("email", "unknown")
                raise UserAlreadyExistsException(email)

        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        error_msg = f"{operation} failed"
        if context_str:
            error_msg += f" ({context_str})"

        raise DatabaseException(
            operation=operation, reason=str(error), original_exception=error
        )

    @staticmethod
    def handle_generic_error(operation: str, error: Exception, **context):
        """Handle generic errors."""
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        error_msg = f"{operation} failed"
        if context_str:
            error_msg += f" ({context_str})"

        raise DatabaseException(
            operation=operation, reason=str(error), original_exception=error
        )
