# ./src/dev_platform/domain/user/value_objects.py
# -*- coding: utf-8 -*-
"""
Este módulo define os Value Objects para o domínio de usuários, incluindo Email e UserName.
"""
from dataclasses import dataclass, field
import re
from abc import ABC, abstractmethod
from typing import Any


# Definição da interface de especificação
class ISpecification(ABC):
    """Interface genérica para especificações de domínio."""
    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        """
        Verifica se o candidato satisfaz a especificação.

        Args:
            candidate (Any): O objeto a ser verificado.

        Returns:
            bool: True se o candidato satisfaz a especificação, False caso contrário.
        """
        pass


# Implementação da especificação de formato de email
class EmailFormatSpecification(ISpecification):
    """Especificação para validar o formato de um endereço de email."""
    EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    def is_satisfied_by(self, email_value: str) -> bool:
        """
        Verifica se a string de email fornecida tem um formato válido.

        Args:
            email_value (str): O endereço de email a ser validado.

        Returns:
            bool: True se o formato do email for válido, False caso contrário.
        """
        return re.match(self.EMAIL_REGEX, email_value) is not None


@dataclass(frozen=True)
class Email:
    """
    Representa um Value Object para endereço de email.

    Garante que o endereço de email seja válido no momento da criação.

    Exemplo de uso:
        email = Email("test@example.com")
        email_invalid = Email("invalid-email")
    """
    value: str
    # Injetando a especificação como uma dependência, com valor padrão para conveniência
    _email_format_spec: ISpecification = field(default_factory=EmailFormatSpecification, init=False, repr=False, compare=False)

    def __post_init__(self):
        """
        Método chamado após a inicialização para validar o formato do email.

        Raises:
            ValueError: Se o formato do email for inválido.
        """
        if not self._email_format_spec.is_satisfied_by(self.value): # Alteração: Usando a especificação
            raise ValueError(f"Invalid email format: {self.value}")


# Implementação da especificação de validação de nome de usuário
class UserNameSpecification(ISpecification):
    """Especificação para validar o nome de usuário."""
    MIN_LENGTH = 3
    MAX_LENGTH = 100

    def is_satisfied_by(self, name_value: str) -> bool:
        trimmed = name_value.strip()
        return (
            bool(trimmed)
            and self.MIN_LENGTH <= len(trimmed) <= self.MAX_LENGTH
        )

@dataclass(frozen=True)
class UserName:
    value: str
    _name_spec: ISpecification = field(default_factory=UserNameSpecification, init=False, repr=False, compare=False)

    def __post_init__(self):
        trimmed = self.value.strip()
        if not self._name_spec.is_satisfied_by(trimmed):
            raise ValueError(
                f"Name must be between {self._name_spec.MIN_LENGTH} and {self._name_spec.MAX_LENGTH} characters long"
            )
        object.__setattr__(self, "value", trimmed)
