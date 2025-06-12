# ./src/dev_platform/main.py
import click
# Importe user_cli do user_commands (renomeado para evitar conflito)
from dev_platform.interface.cli.user_commands import cli as user_cli


# Cria um grupo Click principal
@click.group()
def main_cli():
    """CLI para o DEV Platform."""
    pass

# Adiciona os comandos de usuário como um subgrupo 'user'
main_cli.add_command(user_cli, name="user")

if __name__ == "__main__":
    main_cli()
