from logging.config import fileConfig
from alembic import context
from ddcDatabases.settings import PostgreSQLSettings
from sqlalchemy import engine_from_config, pool
from src.database.models.bot_models import BotBase
from src.database.models.gw2_models import Gw2Base


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = [
    BotBase.metadata,
    Gw2Base.metadata,
]

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
env_configs = PostgreSQLSettings()
db_configs = {
    "database": env_configs.database,
    "username": env_configs.username,
    "password": env_configs.password,
    "host": env_configs.host,
    "port": env_configs.port,
}
config.set_main_option(
    "sqlalchemy.url",
    f"postgresql://{db_configs['username']}:{db_configs['password']}@{db_configs['host']}:{db_configs['port']}/{db_configs['database']}"
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
