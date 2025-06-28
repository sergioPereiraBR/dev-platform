# ./src/dev_platform/client/cli/user_commands.py
# -*- coding: utf-8 -*-
"""
CLI para gerenciamento de usuários no DEV Platform.
Este módulo define comandos CLI para criar, listar, atualizar, obter e excluir usuários.
"""

import asyncio
import click
import sys, os
from typing import Callable, Awaitable, Any, Dict, List, Optional

from dev_platform.application.user.dtos import UserCreateDTO, UserUpdateDTO, UserDTO
from dev_platform.infrastructure.composition_root import CompositionRoot
from dev_platform.application.ports.logger import ILogger
from dev_platform.domain.exceptions import ConfigurationException
from dev_platform.domain.user.user_exceptions import (
    UserAlreadyExistsException,
    UserValidationException,
    UserNotFoundException,
)

EXCEPTION_MAPPINGS = {
    UserAlreadyExistsException: {"log_level": "warning", "user_message": "Erro: Usuário já existe: {e}"},
    UserValidationException: {"log_level": "warning", "user_message": "Erro: Validação: {e}"},
    UserNotFoundException: {"log_level": "warning", "user_message": "Erro: Usuário não encontrado: {e}"},
    ConfigurationException: {"log_level": "error", "user_message": "Erro: Configuração: {e}"},
}


def run_async(coro, logger: ILogger) -> None:
    """
    Executa uma corrotina de forma segura em qualquer ambiente.
    Usa run_until_complete em CLI puro e asyncio.run se possível.
    Lança erro amigável se já houver um loop rodando (ex: Jupyter).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            raise RuntimeError(
                "Já existe um loop de eventos rodando. "
                "Execute este comando em um terminal/CLI puro."
            )
        return loop.run_until_complete(coro)
    except RuntimeError as re:
        logger.critical(
            f"Ocorreu erro em tempo de execução: {re}",
            exception=str(re)
        )
        print(f"Erro crítico: {re}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro: {e}", exception=str(e))
        print(f"Erro: {e}")
        sys.exit(1)

class UserCommands:
    """
    Sempre crie o UoW via create_unit_of_work() e o passe para os métodos de casos de uso.
    """
    def __init__(self, composition_root: CompositionRoot):
        self._composition_root: CompositionRoot = composition_root
        self._logger: ILogger = composition_root.get_logger()

    async def _handle_cli_errors(self, func: Callable[..., Awaitable[Any]], default_error_message: str, **kwargs) -> Any:
        try:
            return await func(**kwargs)
        except Exception as e:
            handler = EXCEPTION_MAPPINGS.get(type(e))
            if handler:
                log_level = handler["log_level"]
                user_message = handler["user_message"].format(e=e)
                if log_level == "warning":
                    self._logger.warning(user_message, exception=str(e))
                elif log_level == "error":
                    self._logger.error(user_message, exception=str(e))
                return user_message
            else:
                self._logger.error(f"{default_error_message}: {e}", exception=str(e))
                return f"{default_error_message}: {e}"

    async def create_user_async(self, name: str, email: str) -> str:
        """
        Cria um novo usuário.
        """
        async def _create_user_logic() -> str:
            use_case = self._composition_root.create_user_use_case()
            dto: UserCreateDTO = UserCreateDTO(name=name, email=email)
            user: UserDTO = await use_case.execute(dto)
            return f"Usuário criado com sucesso: ID {user.id}, Nome: {user.name}, E-mail: {user.email}"
        
        return await self._handle_cli_errors(
            _create_user_logic,
            default_error_message="Erro inesperado ao criar usuário"
        )

    async def list_users_async(self) -> List[str]:
        """
        Lista todos os usuários.
        """
        async def _list_users_logic() -> List[str]:
            use_case = self._composition_root.list_users_use_case()
            users: List[UserDTO] = await use_case.execute()
            if not users:
                return ["Nenhum usuário encontrado"]
            result: List[str] = []
            for user in users:
                result.append(f"ID: {user.id}, Nome: {user.name}, E-mail: {user.email}")
            return result
        
        return await self._handle_cli_errors(
            _list_users_logic,
            default_error_message="Erro inesperado ao listar usuários"
        )

    async def update_user_async(
        self, user_id: int, name: Optional[str] = None, email: Optional[str] = None
    ) -> str:
        """
        Atualiza um usuário existente.
        """
        async def _update_user_logic() -> str:
            update_use_case = self._composition_root.update_user_use_case()
            update_dto = UserUpdateDTO(name=name, email=email)
            updated_user = await update_use_case.execute(user_id=user_id, dto=update_dto)
            return f"Usuário {user_id} atualizado com sucesso: Nome: {updated_user.name}, E-mail: {updated_user.email}"

        return await self._handle_cli_errors(
            _update_user_logic,
            default_error_message="Erro inesperado ao atualizar usuário"
        )


    async def get_user_async(self, user_id: int) -> str:
        """
        Obtém um usuário pelo ID.
        """
        async def _get_user_logic() -> str:
            get_use_case = self._composition_root.get_user_use_case()
            user = await get_use_case.execute(user_id)
            return f"ID: {user.id}, Nome: {user.name}, E-mail: {user.email}"

        return await self._handle_cli_errors(
            _get_user_logic,
            default_error_message="Erro inesperado ao obter usuário",
            user_id=user_id # Passa user_id para o contexto de log, se necessário
        )


    async def delete_user_async(self, user_id: int) -> str:
        """
        Exclui um usuário pelo ID.
        """
        async def _delete_user_logic() -> str:
            delete_use_case = self._composition_root.delete_user_use_case()
            success = await delete_use_case.execute(user_id)
            if success:
                return f"Usuário {user_id} excluído com sucesso."
            else:
                return f"Falha ao excluir usuário {user_id}."
        
        return await self._handle_cli_errors(
            _delete_user_logic,
            default_error_message="Erro inesperado ao excluir usuário",
            user_id=user_id
        )


# Ponto de entrada cria as dependências de infraestrutura

_composition_root = CompositionRoot()
_LOGGER: ILogger = _composition_root.get_logger()

def get_commands() -> UserCommands:
    return UserCommands(_composition_root)

@click.group()
def user_commands():
    pass

@user_commands.command()
@click.option("--name", prompt="Nome do usuário")
@click.option("--email", prompt="E-mail do usuário")
def create_user(name: str, email: str):
    """Cria um novo usuário."""
    async def _run_create():
        result: str = await get_commands().create_user_async(name, email)
        click.echo(result)
    return run_async(_run_create(), _LOGGER)

@user_commands.command()
def list_users():
    """Lista todos os usuários."""
    async def _run_list():
        results: List[str] = await get_commands().list_users_async()
        for line in results:
            click.echo(line)
    return run_async(_run_list(), _LOGGER)

@user_commands.command()
@click.option("--user-id", type=int, prompt="ID do usuário para atualizar")
@click.option(
    "--name",
    prompt="Novo nome do usuário (deixe em branco para manter o atual)",
    default="",
    show_default=False,
    help="Novo nome do usuário. Deixe em branco para manter o atual."
)
@click.option(
    "--email",
    prompt="Novo e-mail do usuário (deixe em branco para manter o atual)",
    default="",
    show_default=False,
    help="Novo e-mail do usuário. Deixe em branco para manter o atual."
)
def update_user(user_id: int, name: str, email: str):
    """Atualiza um usuário existente."""
    async def _run_update():
        result: str = await get_commands().update_user_async(
            user_id, name if name else None, email if email else None
        )
        click.echo(result)

    return run_async(_run_update(), _LOGGER)

@user_commands.command()
@click.option("--user-id", type=int, prompt="ID do usuário para consultar")
def get_user(user_id: int):
    """Obtém um usuário pelo ID."""
    async def _run_get():
        result: str = await get_commands().get_user_async(user_id)
        click.echo(result)

    return run_async(_run_get(), _LOGGER)

@user_commands.command()
@click.option("--user-id", type=int, prompt="ID do usuário para excluir")
def delete_user(user_id: int):
    """Exclui um usuário pelo ID."""
    async def _run_delete():
        result: str = await get_commands().delete_user_async(user_id)
        click.echo(result)

    return run_async(_run_delete(), _LOGGER)
