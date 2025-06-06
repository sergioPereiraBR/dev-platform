# migrations/env.py
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Isso importa a instância singleton da sua configuração
# Assumindo que o caminho é src.dev_platform.infrastructure.config
# Ajuste o import path conforme a estrutura real do seu projeto.
import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos funcionarem
# Se alembic.ini e .env estiverem na raiz do projeto, e src/dev_platform for o módulo,
# precisamos garantir que o sys.path inclua o diretório que contém 'src'.
# O Alembic geralmente é executado da raiz do projeto, então isso é crucial.
# Descobre o caminho do alembic.ini e navega para a raiz do projeto.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..')) # Ajuste conforme a profundidade de 'migrations'
sys.path.insert(0, project_root)

# Agora podemos importar a configuração do seu projeto
# Ajuste o caminho se a sua `config.py` não estiver diretamente em infrastructure
from src.dev_platform.infrastructure.config import CONFIG, ConfigurationException

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import Base
# target_metadata = Base.metadata
# Exemplo: Se você tem um models.py na camada de infraestrutura
from src.dev_platform.infrastructure.database.models import Base # Ajuste este import para seu modelo base
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# --- Começo da Modificação para usar sua CONFIG ---
def get_database_url_from_project_config():
    try:
        # Acesse a URL do banco de dados diretamente da sua instância CONFIG
        # Isso garante que a URL seja carregada dos arquivos .env corretamente.
        return CONFIG.sync_database_url # Use sync_database_url para Alembic, pois ele é síncrono.
    except ConfigurationException as e:
        print(f"ERRO: Não foi possível obter DATABASE_URL da configuração do projeto: {e}")
        # Isso é um erro fatal para o Alembic, então re-lançar ou sair.
        sys.exit(1)

# Pega a URL do banco de dados da sua configuração customizada
database_url = get_database_url_from_project_config()

# Define a URL do banco de dados para o contexto do Alembic
config.set_main_option("sqlalchemy.url", database_url)

# --- Fim da Modificação ---

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is additionally
    permissible.  By not creating an Engine, we don't even
    need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # config.url já está definido pelo get_database_url_from_project_config() acima
    connectable = engine_from_config(
        CONFIG.get_section_arg(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
