# ./src/dev_platform/infrastructure/database/models.py
# -*- coding: utf-8 -*-
"""
Este módulo define os modelos de banco de dados usando SQLAlchemy,
permitindo a persistência de entidades do domínio em um banco de dados relacional.
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint('email', name='uq_users_email'),)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<UserModel(id={self.id}, name='{self.name}', email='{self.email}')>"