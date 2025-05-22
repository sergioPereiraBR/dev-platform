#   src/dev_platform/main.py
from interface.cli.user_cli import cli

if __name__ == "__main__":
    cli()

"""
NOTE:
PS D:\02_trabalho\03_estudos_profissionais\computação\learning\Gemini\developer_platform\dev_platform> poetry run python .\src\dev_platform\main.py list_users
Traceback (most recent call last):
  File "D:\02_trabalho\03_estudos_profissionais\computação\learning\Gemini\developer_platform\dev_platform\src\dev_platform\main.py", line 2, in <module>
    from src.dev_platform.interface.cli.user_cli import cli
ModuleNotFoundError: No module named 'src'
"""
