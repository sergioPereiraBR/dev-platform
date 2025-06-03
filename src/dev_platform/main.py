# src/dev_platform/main.py
import click
import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importe user_cli do user_commands (renomeado para evitar conflito)
from src.dev_platform.interface.cli.user_commands import cli as user_cli


# Cria um grupo Click principal
@click.group()
def main_cli():
    """CLI para o DEV Platform."""
    pass

# Adiciona os comandos de usuário como um subgrupo 'user'
main_cli.add_command(user_cli, name="user")


if __name__ == '__main__':
    # Simplesmente executa a CLI principal.
    # A gestão do ciclo de vida do asyncio e a limpeza do DB
    # agora são feitas individualmente por cada comando de usuário.
    main_cli()
