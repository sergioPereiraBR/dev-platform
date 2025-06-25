# ./src/dev_platform/client/cli/user_commands.py
# -*- coding: utf-8 -*-
"""
CLI para gerenciamento de usuários no DEV Platform.
Este módulo define comandos CLI para criar, listar, atualizar, obter e excluir usuários.
"""

import asyncio
import click
import sys, os
from typing import Optional, List
from dev_platform.infrastructure.config import ConfigurationFacade
from dev_platform.application.user.dtos import UserCreateDTO, UserUpdateDTO, UserDTO
from dev_platform.infrastructure.composition_root import CompositionRoot
from dev_platform.infrastructure.database.unit_of_work import SQLUnitOfWork
from dev_platform.application.ports.logger import ILogger
from dev_platform.infrastructure.logging.structured_logger import StructuredLogger
from dev_platform.domain.exceptions import ConfigurationException
from dev_platform.domain.user.user_exceptions import (
    UserAlreadyExistsException,
    UserValidationException,
    UserNotFoundException,
)

_LOGGER: ILogger = StructuredLogger()

def run_async(coro) -> None:
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
        _LOGGER.critical(
            f"Ocorreu erro em tempo de execução: {re}",
            exception=str(re)
        )
        sys.exit(1)
    except Exception as e:
        _LOGGER.error(f"Erro: {e}", exception=str(e))
        sys.exit(1)

class UserCommands:
    def __init__(self, composition_root: CompositionRoot, logger: ILogger):
        self._composition_root: CompositionRoot = composition_root
        self._logger: ILogger = logger

    async def create_user_async(self, name: str, email: str) -> str:
        """
        Cria um novo usuário.
        """
        try:
            async with SQLUnitOfWork(self._logger) as uow:
                repo = uow.user_repository
                use_case = self._composition_root.create_user_use_case(uow, repo)
                dto: UserCreateDTO = UserCreateDTO(name=name, email=email)
                user: UserDTO = await use_case.execute(dto)
                return f"Usuário criado com sucesso: ID {user.id}, Nome: {user.name}, E-mail: {user.email}"
        except UserAlreadyExistsException as e:
            self._logger.warning(f"Usuário já existe: {e}")
            return f"Erro: Usuário já existe: {e}"
        except UserValidationException as e:
            self._logger.warning(f"Erro de validação: {e}")
            return f"Erro: Validação: {e}"
        except ConfigurationException as ce:
            self._logger.error(f"Erro de configuração: {ce}", exception=str(ce))
            return f"Erro: Configuração: {ce}"
        except Exception as e:
            self._logger.error(f"Erro inesperado ao criar usuário: {e}", exception=str(e))
            return f"Erro: Erro inesperado ao criar usuário: {e}"

    async def list_users_async(self) -> List[str]:
        """
        Lista todos os usuários.
        """
        try:
            async with SQLUnitOfWork(self._logger) as uow:
                repo = uow.user_repository
                use_case = self._composition_root.list_users_use_case(uow, repo)
                users: List[UserDTO] = await use_case.execute()
                if not users:
                    return ["Nenhum usuário encontrado"]
                result: List[str] = []
                for user in users:
                    result.append(
                        f"ID: {user.id}, Nome: {user.name}, E-mail: {user.email}"
                    )
                return result
        except UserNotFoundException as e:
            self._logger.warning(f"Usuário não encontrado: {e}")
            return [f"Erro: Usuário não encontrado: {e}"]
        except UserValidationException as e:
            self._logger.warning(f"Erro de validação: {e}")
            return [f"Erro: Validação: {e}"]
        except ConfigurationException as ce:
            self._logger.error(f"Erro de configuração: {ce}", exception=str(ce))
            return [f"Erro: Configuração: {ce}"]
        except Exception as e:
            self._logger.error(f"Erro inesperado ao listar usuários: {e}", exception=str(e))
            return [f"Erro: Erro inesperado ao listar usuários: {e}"]

    async def update_user_async(
        self, user_id: int, name: Optional[str] = None, email: Optional[str] = None
    ) -> str:
        """
        Atualiza um usuário existente.
        """
        try:
            async with SQLUnitOfWork(self._logger) as uow:
                repo = uow.user_repository
                update_dto = UserUpdateDTO(name=name, email=email)
                update_use_case = self._composition_root.update_user_use_case(uow, repo)
                updated_user = await update_use_case.execute(user_id=user_id, dto=update_dto)
            return f"Usuário {user_id} atualizado com sucesso: Nome: {updated_user.name}, E-mail: {updated_user.email}"
        except UserNotFoundException as e:
            self._logger.warning(f"Usuário não encontrado: {e}")
            return f"Erro: Usuário não encontrado: {e}"
        except UserAlreadyExistsException as e:
            self._logger.warning(f"Usuário já existe: {e}")
            return f"Erro: Usuário já existe: {e}"
        except UserValidationException as e:
            self._logger.warning(f"Erro de validação: {e}")
            return f"Erro: Validação: {e}"
        except ConfigurationException as ce:
            self._logger.error(f"Erro de configuração: {ce}", exception=str(ce))
            return f"Erro: Configuração: {ce}"
        except Exception as e:
            self._logger.error(f"Erro inesperado ao atualizar usuário: {e}", exception=str(e))
            return f"Erro: Erro inesperado ao atualizar usuário: {e}"

    async def get_user_async(self, user_id: int) -> str:
        """
        Obtém um usuário pelo ID.
        """
        try:
            async with SQLUnitOfWork(self._logger) as uow:
                repo = uow.user_repository
                use_case = self._composition_root.get_user_use_case(uow, repo)
                user_entity = await use_case.execute(user_id=user_id)
                if not user_entity:
                    return f"Usuário com ID {user_id} não encontrado."
                return f"Usuário encontrado: ID {user_entity.id}, Nome: {user_entity.name}, E-mail: {user_entity.email}"
        except UserNotFoundException as e:
            self._logger.warning(f"Usuário não encontrado: {e}")
            return f"Erro: Usuário não encontrado: {e}"
        except UserValidationException as e:
            self._logger.warning(f"Erro de validação: {e}")
            return f"Erro: Validação: {e}"
        except ConfigurationException as ce:
            self._logger.error(f"Erro de configuração: {ce}", exception=str(ce))
            return f"Erro: Configuração: {ce}"
        except Exception as e:
            self._logger.error(f"Erro inesperado ao obter usuário: {e}", exception=str(e))
            return f"Erro: Erro inesperado ao obter usuário: {e}"

    async def delete_user_async(self, user_id: int) -> str:
        """
        Exclui um usuário pelo ID.
        """
        try:
            async with SQLUnitOfWork(self._logger) as uow:
                repo = uow.user_repository
                use_case = self._composition_root.delete_user_use_case(uow, repo)
                success: bool = await use_case.execute(user_id=user_id)
                if success:
                    return f"Usuário {user_id} excluído com sucesso."
                else:
                    return f"Usuário {user_id} não pôde ser excluído (não encontrado ou outro problema)."
        except UserNotFoundException as e:
            self._logger.warning(f"Usuário não encontrado: {e}")
            return f"Erro: Usuário não encontrado: {e}"
        except UserValidationException as e:
            self._logger.warning(f"Erro de validação: {e}")
            return f"Erro: Validação: {e}"
        except ConfigurationException as ce:
            self._logger.error(f"Erro de configuração: {ce}", exception=str(ce))
            return f"Erro: Configuração: {ce}"
        except Exception as e:
            self._logger.error(f"Erro inesperado ao excluir usuário: {e}", exception=str(e))
            return f"Erro: Erro inesperado ao excluir usuário: {e}"


# Ponto de entrada cria as dependências de infraestrutura
def get_commands() -> UserCommands:
    config = ConfigurationFacade(environment=os.getenv("ENVIRONMENT",
    "production"), logger=_LOGGER)
    composition_root = CompositionRoot(config=config, logger=_LOGGER)
    return UserCommands(composition_root, _LOGGER)

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
    return run_async(_run_create())

@user_commands.command()
def list_users():
    """Lista todos os usuários."""
    async def _run_list():
        results: List[str] = await get_commands().list_users_async()
        for line in results:
            click.echo(line)
    return run_async(_run_list())

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

    return run_async(_run_update())

@user_commands.command()
@click.option("--user-id", type=int, prompt="ID do usuário para consultar")
def get_user(user_id: int):
    """Obtém um usuário pelo ID."""
    async def _run_get():
        result: str = await get_commands().get_user_async(user_id)
        click.echo(result)

    return run_async(_run_get())

@user_commands.command()
@click.option("--user-id", type=int, prompt="ID do usuário para excluir")
def delete_user(user_id: int):
    """Exclui um usuário pelo ID."""
    async def _run_delete():
        result: str = await get_commands().delete_user_async(user_id)
        click.echo(result)

    return run_async(_run_delete())
