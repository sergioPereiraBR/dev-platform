# src/dev_platform/interface/cli/user_cli.py
import asyncio
import click
from application.user.usecases import CreateUserUseCase, ListUsersUseCase
from application.user.dtos import UserCreateDTO
from infrastructure.database.async_repositories import AsyncSQLUserRepository
from infrastructure.database.session import AsyncSessionLocal
from shared.exceptions import DomainException, DatabaseException


@click.group()
def cli():
    pass


async def async_create_user(name: str, email: str):
    async with AsyncSessionLocal() as session:
        try:
            repository = AsyncSQLUserRepository(session)
            use_case = CreateUserUseCase(repository)
            user_create_dto = UserCreateDTO(name=name, email=email)
            
            user = await use_case.execute(user_create_dto)
            return f"User created: {user.name} ({user.email})"
        except DomainException as e:
            return f"Domain Error: {e}"
        except DatabaseException as e:
            return f"Database Error: {e}"
        except Exception as e:
            return f"Unexpected Error: {e}"


@cli.command()
@click.option('--name', prompt='User name', help='Name of the user')
@click.option('--email', prompt='User email', help='Email of the user')
def create_user(name: str, email: str):
    """Create a new user."""
    result = asyncio.run(async_create_user(name, email))
    click.echo(result)


async def async_list_users():
    async with AsyncSessionLocal() as session:
        try:
            repository = AsyncSQLUserRepository(session)
            use_case = ListUsersUseCase(repository)
            
            users = await use_case.execute()
            result = []
            for user in users:
                result.append(f"ID: {user.id}, Name: {user.name}, Email: {user.email}")
            return result
        except DatabaseException as e:
            return [f"Database Error: {e}"]
        except Exception as e:
            return [f"Unexpected Error: {e}"]


@cli.command()
def list_users():
    """List all users."""
    results = asyncio.run(async_list_users())
    for line in results:
        click.echo(line)
