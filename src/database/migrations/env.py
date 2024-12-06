# -*- coding: utf-8 -*-
from logging.config import fileConfig
from urllib.parse import quote_plus
from alembic import context
from alembic.script import ScriptDirectory
from ddcDatabases.settings import PostgreSQLSettings
from sqlalchemy import engine_from_config, pool
from src.database.models.bot_models import BotBase
from src.database.models.gw2_models import Gw2Base


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = [
    BotBase.metadata,
    Gw2Base.metadata,
]


_settings = PostgreSQLSettings()
_password = quote_plus(_settings.password).replace("%", "%%")
_conn_url = (f"{_settings.sync_driver}://"
             f"{_settings.username}:"
             f"{_password}@"
             f"{_settings.host}:"
             f"{_settings.port}/"
             f"{_settings.database}")
config.set_main_option("sqlalchemy.url", _conn_url)


def _process_revision_directives(ctx, revision, directives):
    migration_script = directives[0]
    head_revision = ScriptDirectory.from_config(ctx.config).get_current_head()
    if head_revision is None:
        new_rev_id = 1
    else:
        last_rev_id = int(head_revision.lstrip('0'))
        new_rev_id = last_rev_id + 1
    migration_script.rev_id = '{0:04}'.format(new_rev_id)


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
        process_revision_directives=_process_revision_directives,
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
            target_metadata=target_metadata,
            process_revision_directives=_process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
