# src/dev_platform/interface/cli/user_cli.py
import click
from application.user.usecases import CreateUserUseCase, ListUsersUseCase
from application.user.dtos import UserCreateDTO
from infrastructure.database.async_repositories import AsyncSQLUserRepository
from infrastructure.database.session import db_session
from shared.exceptions import DomainException, DatabaseException


@click.group()
def cli():
    pass

@cli.command()
@click.option('--name', prompt='User name', help='Name of the user')
@click.option('--email', prompt='User email', help='Email of the user')
def create_user(name: str, email: str):
    with db_session() as session:
        repository = AsyncSQLUserRepository(session)
        use_case = CreateUserUseCase(repository)
        user_create_dto = UserCreateDTO(name=name, email=email)
        try:
            user = use_case.execute(user_create_dto)
            click.echo(f"User created: {user.name} ({user.email})")
        except DomainException as e:
            click.echo(f"Domain Error: {e}")
        except DatabaseException as e:
            click.echo(f"Database Error: {e}")

@cli.command()
async  def list_users():
    with db_session() as session:
        repository = AsyncSQLUserRepository(session)
        use_case = await ListUsersUseCase(repository)
        try:
            users = use_case.execute()
            for user in users:
                click.echo(f"ID: {user.id}, Name: {user.name}, Email: {user.email}")
        except DatabaseException as e:
            click.echo(f"Database Error: {e}")
