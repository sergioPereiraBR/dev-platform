#   src/interface/cli/user_cli.py  (formerly user_cli.py, renamed for clarity)
import click
from src.application.user.usecases import CreateUserUseCase, ListUsersUseCase
from src.application.user.dtos import UserCreateDTO
from src.infrastructure.database.repositories import SQLUserRepository
from src.infrastructure.database.session import get_db_session
from src.shared.exceptions import DomainException, DatabaseException

@click.group()
def cli():
    pass

@cli.command()
@click.option('--name', prompt='User name', help='Name of the user')
@click.option('--email', prompt='User email', help='Email of the user')
def create_user(name: str, email: str):
    db_session = next(get_db_session())  #   Get the session
    repository = SQLUserRepository(db_session)
    use_case = CreateUserUseCase(repository)
    user_create_dto = UserCreateDTO(name=name, email=email)  #   Create DTO
    try:
        user = use_case.execute(user_create_dto)
        click.echo(f"User created: {user.name} ({user.email})")
    except DomainException as e:
        click.echo(f"Domain Error: {e}")
    except DatabaseException as e:
        click.echo(f"Database Error: {e}")
    finally:
        db_session.close()

@cli.command()
def list_users():
    db_session = next(get_db_session())
    repository = SQLUserRepository(db_session)
    use_case = ListUsersUseCase(repository)
    try:
        users = use_case.execute()
        for user in users:
            click.echo(f"ID: {user.id}, Name: {user.name}, Email: {user.email}")
    except DatabaseException as e:
        click.echo(f"Database Error: {e}")
    finally:
        db_session.close()