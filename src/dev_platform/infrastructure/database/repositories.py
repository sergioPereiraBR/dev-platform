# src/dev_platform/infrastructure/database/repositories.py
from typing import List
from sqlalchemy.orm import Session
from domain.user.entities import User
from domain.user.interfaces import UserRepository
from infrastructure.database.models import UserModel
from shared.exceptions import DatabaseException  #   New DatabaseException

class SQLUserRepository(UserRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> User:
        try:
            db_user = UserModel(name=user.name, email=user.email)
            self.session.add(db_user)
            self.session.commit()
            self.session.refresh(db_user)
            user.id = db_user.id
            return user
        except Exception as e:
            self.session.rollback()  #   Important: Rollback on error
            raise DatabaseException(f"Error saving user: {e}")

    def find_all(self) -> List[User]:
        try:
            db_users = self.session.query(UserModel).all()
            return [User(id=u.id, name=u.name, email=u.email) for u in db_users]
        except Exception as e:
            raise DatabaseException(f"Error finding all users: {e}")