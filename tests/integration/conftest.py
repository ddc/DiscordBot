import logging
import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `from src...` imports work
# regardless of whether pytest was invoked via `python -m pytest` or `pytest`
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Prevent tests/docker/ from shadowing the real `docker` package
# pytest adds tests/ to sys.path, causing tests/docker/__init__.py to shadow docker from PyPI
_tests_dir = os.path.dirname(os.path.dirname(__file__))
if _tests_dir in sys.path:
    sys.path.remove(_tests_dir)
    import docker  # noqa: F401 - ensure real docker is loaded

    sys.path.insert(0, _tests_dir)
else:
    import docker  # noqa: F401

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from src.bot.constants import variables


@pytest.fixture(scope="session")
def postgres_container():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:latest", driver=None) as pg:
        yield pg


@pytest.fixture(scope="session", autouse=True)
def setup_env_and_run_migrations(postgres_container):
    host = postgres_container.get_container_host_ip()
    port = str(postgres_container.get_exposed_port(5432))
    user = postgres_container.username
    password = postgres_container.password
    database = postgres_container.dbname

    os.environ["POSTGRESQL_HOST"] = host
    os.environ["POSTGRESQL_PORT"] = port
    os.environ["POSTGRESQL_USER"] = user
    os.environ["POSTGRESQL_PASSWORD"] = password
    os.environ["POSTGRESQL_DATABASE"] = database
    os.environ["POSTGRESQL_SCHEMA"] = "public"
    os.environ["POSTGRESQL_SSL_MODE"] = "disable"

    from ddcDatabases import clear_postgresql_settings_cache

    clear_postgresql_settings_cache()

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(str(variables.BASE_DIR / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
def db_url():
    return (
        f"postgresql+asyncpg://"
        f"{os.environ['POSTGRESQL_USER']}:{os.environ['POSTGRESQL_PASSWORD']}@"
        f"{os.environ['POSTGRESQL_HOST']}:{os.environ['POSTGRESQL_PORT']}/"
        f"{os.environ['POSTGRESQL_DATABASE']}"
    )


_SEED_BOT_CONFIGS = sa.text(
    "INSERT INTO bot_configs (id, prefix, author_id, url, description) "
    "VALUES (1, :prefix, :author_id, :url, :description)"
)

_SEED_PARAMS = {
    "prefix": variables.PREFIX,
    "author_id": int(variables.AUTHOR_ID),
    "url": variables.BOT_WEBPAGE_URL,
    "description": variables.DESCRIPTION,
}

_TRUNCATE_ALL = sa.text(
    "TRUNCATE gw2_session_chars, gw2_sessions, gw2_keys, gw2_configs, "
    "dice_rolls, profanity_filters, custom_commands, servers, bot_configs "
    "RESTART IDENTITY CASCADE"
)


@pytest_asyncio.fixture
async def db_session(db_url):
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.execute(_TRUNCATE_ALL)
        await conn.execute(_SEED_BOT_CONFIGS, _SEED_PARAMS)
    await engine.dispose()


@pytest.fixture(scope="session")
def log():
    return logging.getLogger("integration-tests")
