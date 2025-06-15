import asyncio
import click
import sys
from typing import Optional, List
from dev_platform.application.user.dtos import UserCreateDTO, UserUpdateDTO, UserDTO
from dev_platform.infrastructure.composition_root import CompositionRoot
from dev_platform.infrastructure.config import CONFIG
from dev_platform.infrastructure.database.unit_of_work import SQLUnitOfWork
from dev_platform.application.ports.logger import ILogger
from dev_platform.infrastructure.logging.structured_logger import StructuredLogger
from dev_platform.domain.user.exceptions import ConfigurationException


# Logger global para uso em run_async
_LOGGER: ILogger = StructuredLogger(CONFIG__=CONFIG)

def run_async(coro):
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
            f"Runtime error occurred: {re}",
            exception=str(re)
        )
        # Para ambientes onde não há loop
        sys.exit(1)  # Encerra o CLI com erro
    

class UserCommands:
    def __init__(self, logger: ILogger = StructuredLogger()):
        self._logger: ILogger = logger or StructuredLogger()
        try:
            self._composition_root = CompositionRoot()
        except ConfigurationException as ce:
            self._logger.critical(
                f"Configuration error during initialization: {ce}",
                exception=str(ce)
            )
            raise
        except Exception as e:
            self._logger.critical(
                f"Unexpected error during initialization: {e}",
                exception=str(e)
            )
            raise ConfigurationException(
                config_key="COMPOSITION_ROOT",
                reason=f"Unexpected error: {e}"
            )

    async def create_user_async(self, name: str, email: str) -> str:
        try:
            async with SQLUnitOfWork() as uow:
                repo = uow.user_repository
                use_case = self._composition_root.create_user_use_case(uow, repo)
                dto: UserCreateDTO = UserCreateDTO(name=name, email=email)
                user: UserDTO = await use_case.execute(dto)
                name = getattr(user.name, "value", user.name)
                email = getattr(user.email, "value", user.email)
                return f"User created successfully: ID {user.id}, Name: {name}, Email: {email}"
        except ValueError as e:
            self._logger.warning(f"Validation error: {e}")
            return f"Validation Error: {e}"
        except ConfigurationException as ce:
            self._logger.error(f"Configuration error: {ce}", exception=str(ce))
            return f"Configuration Error: {ce}"
        except Exception as e:
            self._logger.error(f"Error creating user: {e}", exception=str(e))
            return f"Error creating user: {e}"

    async def list_users_async(self) -> List[str]:
        try:
            async with SQLUnitOfWork() as uow:
                use_case = self._composition_root.list_users_use_case(uow)
                users: List[UserDTO] = await use_case.execute()
                if not users:
                    return ["No users found"]

                result: List[str] = []
                for user in users:
                    name = getattr(user.name, "value", user.name)
                    email = getattr(user.email, "value", user.email)
                    result.append(
                        f"ID: {user.id}, Name: {name}, Email: {email}"
                    )
                return result
        except ConfigurationException as ce:
            self._logger.error(f"Configuration error: {ce}", exception=str(ce))
            return [f"Configuration Error: {ce}"]
        except Exception as e:
            self._logger.error(f"Error listing users: {e}", exception=str(e))
            return [f"Error: {e}"]

    async def update_user_async(
        self, user_id: int, name: Optional[str] = None, email: Optional[str] = None
    ) -> str:
        try:
            async with SQLUnitOfWork() as uow:
                repo = uow.user_repository
                get_use_case = self._composition_root.get_user_use_case(uow, repo)
                existing_user: UserDTO = await get_use_case.execute(user_id=user_id)
                update_name = name if name is not None else existing_user.name.value
                update_email = email if email is not None else existing_user.email.value
                user_update_dto = UserUpdateDTO(name=update_name, email=update_email)
                update_use_case = self._composition_root.update_user_use_case(uow, repo)
                updated_user_entity = await update_use_case.execute(user_id=user_id, dto=user_update_dto)
                name = getattr(updated_user_entity.name, "value", updated_user_entity.name)
                email = getattr(updated_user_entity.email, "value", updated_user_entity.email)
                return f"User {user_id} updated successfully: ID {updated_user_entity.id}, Name: {name}, Email: {email}"
        except ConfigurationException as ce:
            self._logger.error(f"Configuration error: {ce}", exception=str(ce))
            return f"Configuration Error: {ce}"
        except Exception as e:
            self._logger.error(f"Error updating user: {e}", exception=str(e))
            return f"Error updating user: {e}"

    async def get_user_async(self, user_id: int) -> str:
        try:
            async with SQLUnitOfWork() as uow:
                repo = uow.user_repository
                use_case = self._composition_root.get_user_use_case(uow, repo)
                user_entity = await use_case.execute(user_id=user_id)
                if not user_entity:
                    return f"User with ID {user_id} not found."
                name = getattr(user_entity.name, "value", user_entity.name)
                email = getattr(user_entity.email, "value", user_entity.email)
                return f"User found: ID {user_entity.id}, Name: {name}, Email: {email}"
        except ConfigurationException as ce:
            self._logger.error(f"Configuration error: {ce}", exception=str(ce))
            return f"Configuration Error: {ce}"
        except Exception as e:
            self._logger.error(f"Error getting user: {e}", exception=str(e))
            return f"Error getting user: {e}"

    async def delete_user_async(self, user_id: int) -> str:
        try:
            async with SQLUnitOfWork() as uow:
                repo = uow.user_repository
                use_case = self._composition_root.delete_user_use_case(uow, repo)
                success: bool = await use_case.execute(user_id=user_id)
                if success:
                    return f"User {user_id} deleted successfully."
                else:
                    return f"User {user_id} could not be deleted (not found or other issue)."
        except ConfigurationException as ce:
            self._logger.error(f"Configuration error: {ce}", exception=str(ce))
            return f"Configuration Error: {ce}"
        except Exception as e:
            self._logger.error(f"Error deleting user: {e}", exception=str(e))
            return f"Error deleting user: {e}"

@click.group()
def cli():
    pass

@cli.command()
@click.option("--name", prompt="User name")
@click.option("--email", prompt="User email")
def create_user(name: str, email: str):
    """Create a new user."""
    commands: UserCommands = UserCommands()

    async def _run_create():
        result: str = await commands.create_user_async(name, email)
        click.echo(result)

    return run_async(_run_create())

@cli.command()
def list_users():
    """List all users."""
    commands: UserCommands = UserCommands()

    async def _run_list():
        results: List[str] = await commands.list_users_async()
        for line in results:
            click.echo(line)

    return run_async(_run_list())

@cli.command()
@click.option("--user-id", type=int, prompt="User ID to update")
@click.option(
    "--name",
    prompt="New user name (leave empty to keep current)",
    default="",
    show_default=False,
)
@click.option(
    "--email",
    prompt="New user email (leave empty to keep current)",
    default="",
    show_default=False,
)
def update_user(user_id: int, name: str, email: str):
    """Update an existing user."""
    commands: UserCommands = UserCommands()

    async def _run_update():
        result: str = await commands.update_user_async(
            user_id, name if name else None, email if email else None
        )
        click.echo(result)

    return run_async(_run_update())

@cli.command()
@click.option("--user-id", type=int, prompt="User ID to retrieve")
def get_user(user_id: int):
    """Get a user by ID."""
    commands: UserCommands = UserCommands()

    async def _run_get():
        result: str = await commands.get_user_async(user_id)
        click.echo(result)

    return run_async(_run_get())

@cli.command()
@click.option("--user-id", type=int, prompt="User ID to delete")
def delete_user(user_id: int):
    """Delete a user by ID."""
    commands: UserCommands = UserCommands()

    async def _run_delete():
        result: str = await commands.delete_user_async(user_id)
        click.echo(result)

    return run_async(_run_delete())
