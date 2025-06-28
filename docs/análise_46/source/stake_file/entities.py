# ./src/dev_platform/domain/user/entities.py
# -*- coding: utf-8 -*-
"""
Este módulo define a entidade User, representando um usuário do sistema.
A entidade é imutável e utiliza Value Objects para validação de nome e e-mail.
"""

from dataclasses import dataclass, field, replace
from uuid import UUID
from dev_platform.domain.user.value_objects import Email, UserName, Address

@dataclass(frozen=True)
class User:
    """Entidade de domínio representando um usuário (imutável)."""
    # id: Optional[int]
    id: UUID
    name: UserName
    email: Email
    address: Address = field(default_factory=lambda: Address("", "")) # Address é parte do agregado User
    _is_active: bool = True

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
    
    # Método para alterar o endereço, respeitando a imutabilidade.
    def update_address(self, new_street: str, new_city: str) -> "User":
        """Retorna uma nova instância do usuário com o endereço atualizado."""
        if not new_street or not new_city:
            raise ValueError("Street and city cannot be empty.")
        
        # Cria um novo Address
        new_address = Address(street=new_street, city=new_city)
        
        # Usa 'replace' para criar e retornar uma nova instância de User
        return replace(self, address=new_address)
