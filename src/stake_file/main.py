# ./src/dev_platform/main.py
# -*- coding: utf-8 -*-
"""
Este módulo define a interface de linha de comando (CLI) para o DEV Platform,
permitindo a interação com os comandos relacionados a usuários.
"""

import click
# Importe user_cli do user_commands (renomeado para evitar conflito)
from dev_platform.interface.cli.user_commands import cli


# Cria um grupo Click principal
@click.group()
def main_cli():
    """CLI para o DEV Platform."""
    pass

# Adiciona os comandos de usuário como um subgrupo 'user'
main_cli.add_command(cli, name="user")

if __name__ == "__main__":
    main_cli()
