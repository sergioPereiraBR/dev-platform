# ./src/dev_platform/domain/user/entities.py
from dataclasses import dataclass, replace
from typing import Optional
from dev_platform.domain.user.value_objects import Email, UserName


@dataclass # Removed frozen=True
class User:
    """Entidade de domínio representando um usuário."""
    # O id é opcional, pois pode ser None quando o usuário é criado
    id: Optional[int]
    name: UserName
    email: Email

    @classmethod
    def create(cls, name: str, email: str) -> "User":
        """Cria um novo usuário, validando nome e e-mail via Value Objects."""
        return cls(id=None, name=UserName(name), email=Email(email))
    
    def with_id(self, new_id: int) -> "User":
        """Atualiza o id, sendo único campo que pode ser "mutado"
        via nova instância"""
        return replace(self, id=new_id) # Usar replace se o ID é o
        # único campo que pode ser "mutado" via nova instância

    def update_details(self, new_name: str, new_email: str) -> None:
        """Atualiza o nome e o e-mail do usuário, re-validando via
        Value Objects."""
        self.name = UserName(new_name) # Re-instancia o Value Object
        # para garantir validação
        self.email = Email(new_email) # Re-instancia o Value Object
        # para garantir validação
