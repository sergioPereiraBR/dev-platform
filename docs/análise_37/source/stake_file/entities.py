# ./src/dev_platform/domain/user/entities.py
# -*- coding: utf-8 -*-
"""
Este módulo define a entidade User, representando um usuário do sistema.
A entidade é imutável e utiliza Value Objects para validação de nome e e-mail.
"""

from dataclasses import dataclass, replace
from typing import Optional
from dev_platform.domain.user.value_objects import Email, UserName

@dataclass(frozen=True)
class User:
    """Entidade de domínio representando um usuário (imutável)."""
    id: Optional[int]
    name: UserName
    email: Email

    @classmethod
    def create(cls, name: str, email: str) -> "User":
        """Cria um novo usuário, validando nome e e-mail via Value Objects."""
        return cls(id=None, name=UserName(name), email=Email(email))
    
    def with_id(self, new_id: int) -> "User":
        """Retorna uma nova instância do usuário com o id atualizado."""
        return replace(self, id=new_id)

    def update_details(self, new_name: str, new_email: str) -> "User":
        """Retorna uma nova instância do usuário com nome e e-mail atualizados."""
        return replace(self, name=UserName(new_name), email=Email(new_email))
