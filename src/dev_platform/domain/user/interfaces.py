#./src/dev_platform/domain/user/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional
from dev_platform.domain.user.entities import User
from dev_platform.domain.user.value_objects import Email


class IUserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        """Salva um usuário no repositório."""
        pass

    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[User]:
        """Busca um usuário pelo e-mail. Retorna o usuário ou None se não encontrado."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[User]:
        """Busca todos os usuários."""
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        """Busca um usuário pelo ID. Retorna o usuário ou None se não encontrado."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Deleta um usuário pelo ID."""
        pass
    
    @abstractmethod
    async def find_by_name_contains(self, name_part: str) -> List[User]:
        """Busca usuários por uma parte do nome."""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Conta o número total de usuários."""
        pass
