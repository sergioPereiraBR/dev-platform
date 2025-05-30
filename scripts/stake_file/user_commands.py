# src/dev_platform/interface/cli/user_commands.py
import asyncio
import click
from application.user.dtos import UserCreateDTO
from infrastructure.composition_root import CompositionRoot

class UserCommands:
    def __init__(self):
        self._composition_root = CompositionRoot()
    
    async def create_user(self, name: str, email: str) -> str:
        try:
            use_case = self._composition_root.create_user_use_case()
            dto = UserCreateDTO(name=name, email=email)
            user = await use_case.execute(dto)
            return f"User created: {user.name} ({user.email}) with ID: {user.id}"
        except ValueError as e:
            return f"Validation Error: {e}"
        except Exception as e:
            return f"Error: {e}"
    
    async def list_users(self) -> list:
        try:
            use_case = self._composition_root.list_users_use_case()
            users = await use_case.execute()
            if not users:
                return ["No users found"]
            
            result = []
            for user in users:
                result.append(f"ID: {user.id}, Name: {user.name}, Email: {user.email}")
            return result
        except Exception as e:
            return [f"Error: {e}"]

@click.group()
def cli():
    pass

@cli.command()
@click.option('--name', prompt='User name')
@click.option('--email', prompt='User email')
def create_user(name: str, email: str):
    """Create a new user."""
    commands = UserCommands()
    result = asyncio.run(commands.create_user(name, email))
    click.echo(result)

@cli.command()
def list_users():
    """List all users."""
    commands = UserCommands()
    results = asyncio.run(commands.list_users())
    for line in results:
        click.echo(line)