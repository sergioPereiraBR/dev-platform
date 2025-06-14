# ./src/dev_platform/interface/cli/user_commands.py
import asyncio
import click
from typing import List, Optional
from dev_platform.application.user.dtos import UserCreateDTO, UserUpdateDTO, UserDTO
from dev_platform.infrastructure.composition_root import CompositionRoot


class UserCommands:
    def __init__(self):
        self._composition_root = CompositionRoot()

    async def create_user_async(self, name: str, email: str) -> str:
        try:
            use_case = self._composition_root.create_user_use_case
            dto = UserCreateDTO(name=name, email=email)
            user = await use_case.execute(dto)
            return f"User created successfully: ID {user.id}, Name: {user.name}, Email: {user.email}"
        except ValueError as e:
            return f"Validation Error: {e}"
        except Exception as e:
            return f"Error creating user: {e}"

    async def list_users_async(self) -> list:
        try:
            use_case = self._composition_root.list_users_use_case
            users = await use_case.execute()
            if not users:
                return ["No users found"]

            result = []
            for user in users:
                # CORRIGIDO: Acessar .value dos value objects
                result.append(
                    f"ID: {user.id}, Name: {user.name}, Email: {user.email}"
                )
            return result
        except Exception as e:
            return [f"Error: {e}"]

    # Adicione os métodos para Update, Get, Delete se necessário, seguindo o padrão
    # Se você tiver implementado os outros comandos (update, get, delete)
    # Lembre-se de chamar .execute() neles também.
    async def update_user_async(
        self, user_id: int, name: Optional[str] = None, email: Optional[str] = None
    ) -> str:
        try:
            use_case = self._composition_root.update_user_use_case
            # Recuperar o usuário existente para preencher DTO com dados atuais se não forem fornecidos
            existing_user = await self._composition_root.get_user_use_case.execute(user_id)
            # Criar DTO de atualização com dados existentes ou novos
            update_name = name if name is not None else existing_user.name.value
            update_email = email if email is not None else existing_user.email.value
            user_dto = UserUpdateDTO(name=update_name, email=update_email) # Use UserUpdateDTO
            updated_user_entity = await use_case.execute(user_id=user_id, dto=user_dto) # Passar DTO
            return f"User {user_id} updated successfully: ID {updated_user_entity.id}, Name: {updated_user_entity.name.value}, Email: {updated_user_entity.email.value}"
        except Exception as e:
            return f"Error updating user: {e}"

    async def get_user_async(self, user_id: int) -> str:
        try:
            use_case = self._composition_root.get_user_use_case
            user_entity = await use_case.execute(user_id=user_id)
            if not user_entity:
                return f"User with ID {user_id} not found."
            return f"User found: ID {user_entity.id}, Name: {user_entity.name.value}, Email: {user_entity.email.value}"
        except Exception as e:
            return f"Error getting user: {e}"

    async def delete_user_async(self, user_id: int) -> str:
        try:
            use_case = self._composition_root.delete_user_use_case
            success = await use_case.execute(user_id=user_id)
            if success:
                return f"User {user_id} deleted successfully."
            else:
                return f"User {user_id} could not be deleted (not found or other issue)."
        except Exception as e:
            return f"Error deleting user: {e}"

# Obtém ou cria um loop de eventos global
loop = asyncio.get_event_loop()

@click.group()
def cli():
    pass
    # try:
    #     pass
    # finally:
    # Fecha o loop de eventos ao final da execução
    # if not loop.is_closed():
    #     loop.close()

# COMANDOS CLICK - CADA UM AGORA GERENCIA SEU PRÓPRIO asyncio.run() E LIMPEZA
@cli.command()
@click.option("--name", prompt="User name")
@click.option("--email", prompt="User email")
def create_user(name: str, email: str):
    """Create a new user."""
    commands = UserCommands()

    async def _run_create():
        result = await commands.create_user_async(name, email)
        click.echo(result)

    # Executa a corrotina no loop de eventos existente
    return loop.run_until_complete(_run_create())

@cli.command()
def list_users():
    """List all users."""
    commands = UserCommands()

    async def _run_list():
        results = await commands.list_users_async()
        for line in results:
            click.echo(line)

    return loop.run_until_complete(_run_list())

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
    commands = UserCommands()

    async def _run_update():
        result = await commands.update_user_async(
            user_id, name if name else None, email if email else None
        )
        click.echo(result)

    return loop.run_until_complete(_run_update())

@cli.command()
@click.option("--user-id", type=int, prompt="User ID to retrieve")
def get_user(user_id: int):
    """Get a user by ID."""
    commands = UserCommands()

    async def _run_get():
        result = await commands.get_user_async(user_id)
        click.echo(result)

    return loop.run_until_complete(_run_get())

@cli.command()
@click.option("--user-id", type=int, prompt="User ID to delete")
def delete_user(user_id: int):
    """Delete a user by ID."""
    commands = UserCommands()

    async def _run_delete():
        result = await commands.delete_user_async(user_id)
        click.echo(result)

    return loop.run_until_complete(_run_delete())
