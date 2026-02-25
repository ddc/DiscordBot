from alembic import context
from alembic.script import ScriptDirectory
from ddcDatabases import get_postgresql_settings
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.schema import SchemaItem
from src.bot.constants.settings import get_bot_settings
from src.database.models import BotBase
from typing import Any, Literal
from urllib.parse import quote_plus

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = [BotBase.metadata]

_project_settings = get_bot_settings()
_postgres_settings = get_postgresql_settings()
_password = quote_plus(_postgres_settings.password).replace("%", "%%")
_conn_url = (
    f"{_postgres_settings.sync_driver}://"
    f"{_postgres_settings.user}:"
    f"{_password}@"
    f"{_postgres_settings.host}:"
    f"{_postgres_settings.port}/"
    f"{_postgres_settings.database}"
    f"?sslmode={_postgres_settings.ssl_mode}"
)
config.set_main_option("sqlalchemy.url", _conn_url)

_schemas = {s.strip() for s in (_postgres_settings.schema or "public").split(",")}


def _include_object(
    obj: SchemaItem,
    _name: str | None,
    type_: Literal["schema", "table", "column", "index", "unique_constraint", "foreign_key_constraint"],
    _reflected: bool,
    _compare_to: SchemaItem | None,
) -> bool | None:
    """
    Filter to only include objects from our target schemas.
    This prevents Alembic from trying to manage tables in other schemas.
    """
    if type_ == "table" and hasattr(obj, "schema"):
        obj_schema = obj.schema  # type: ignore[attr-defined]
        if obj_schema is None or obj_schema in _schemas:
            return True
        return False
    return True


def _process_revision_directives(ctx: Any, revision: Any, directives: Any) -> None:
    migration_script = directives[0]
    head_revision = ScriptDirectory.from_config(ctx.config).get_current_head()
    if head_revision is None:
        new_rev_id = 1
    else:
        last_rev_id = int(head_revision.lstrip("0"))
        new_rev_id = last_rev_id + 1
    migration_script.rev_id = f"{new_rev_id:04}"


_version_table_schema = "public" if len(_schemas) > 1 else next(iter(_schemas))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.
    By skipping the Engine creation,
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
        version_table_schema=_version_table_schema,
        version_table=_project_settings.alembic_version_table_name,
        include_schemas=True,
        include_object=_include_object,
    )

    with context.begin_transaction():
        for s in _schemas:
            if s != "public":
                context.execute(f"CREATE SCHEMA IF NOT EXISTS {s}")
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario, we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        for s in _schemas:
            if s != "public":
                connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {s}"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=_process_revision_directives,
            version_table_schema=_version_table_schema,
            version_table=_project_settings.alembic_version_table_name,
            include_schemas=True,
            include_object=_include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
