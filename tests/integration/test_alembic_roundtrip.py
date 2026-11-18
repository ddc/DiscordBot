"""Round-trip every Alembic migration (upgrade -> downgrade -> upgrade) in a scratch database."""

import os
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from ddcdatabases import clear_postgresql_settings_cache
from src.bot.constants import variables

pytestmark = pytest.mark.integration

SCRATCH_DB = "alembic_roundtrip"


def _sync_url(database: str) -> str:
    return (
        f"postgresql+psycopg://{os.environ['POSTGRESQL_USER']}:{os.environ['POSTGRESQL_PASSWORD']}@"
        f"{os.environ['POSTGRESQL_HOST']}:{os.environ['POSTGRESQL_PORT']}/{database}"
    )


def _scalar(database: str, sql: str):
    engine = sa.create_engine(_sync_url(database))
    try:
        with engine.connect() as conn:
            return conn.execute(sa.text(sql)).scalar()
    finally:
        engine.dispose()


@pytest.fixture
def alembic_cfg():
    return Config(str(variables.BASE_DIR / "alembic.ini"))


@pytest.fixture
def scratch_database(monkeypatch):
    """Point Alembic at a separate database so the shared test database is never downgraded."""
    monkeypatch.setenv("POSTGRESQL_DATABASE", SCRATCH_DB)
    clear_postgresql_settings_cache()
    yield SCRATCH_DB
    monkeypatch.undo()
    clear_postgresql_settings_cache()
    engine = sa.create_engine(_sync_url("postgres"), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{SCRATCH_DB}" WITH (FORCE)'))
    engine.dispose()


def test_upgrade_downgrade_upgrade_roundtrip(alembic_cfg, scratch_database):
    command.upgrade(alembic_cfg, "head")
    assert _scalar(scratch_database, "SELECT version_num FROM alembic_version") == "0011"

    command.downgrade(alembic_cfg, "base")
    user_tables = _scalar(
        scratch_database,
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema IN ('public', 'gw2') AND table_name <> 'alembic_version'",
    )
    assert user_tables == 0
    assert _scalar(scratch_database, "SELECT count(*) FROM alembic_version") == 0
    assert (
        _scalar(
            scratch_database,
            "SELECT count(*) FROM information_schema.routines WHERE routine_name = 'updated_at_column_func'",
        )
        == 0
    )

    command.upgrade(alembic_cfg, "head")
    assert _scalar(scratch_database, "SELECT version_num FROM alembic_version") == "0011"
    assert _scalar(scratch_database, "SELECT count(*) FROM bot_configs") == 1


def test_offline_sql_generation(alembic_cfg, scratch_database, capsys):
    command.upgrade(alembic_cfg, "head", sql=True)
    sql = capsys.readouterr().out
    assert "CREATE SCHEMA IF NOT EXISTS gw2" in sql
    assert "servers (" in sql
    assert "gw2.gw2_sessions (" in sql
    assert "SET version_num='0011'" in sql


@pytest.fixture
def revision_dir(tmp_path, alembic_cfg):
    """Extra version location so a generated revision is written to tmp, never into the repo."""
    versions = variables.BASE_DIR / "src" / "database" / "migrations" / "versions"
    alembic_cfg.set_main_option("version_locations", f"{versions}{os.pathsep}{tmp_path}")
    return tmp_path


def test_models_match_migrations(alembic_cfg, scratch_database):
    command.upgrade(alembic_cfg, "head")
    command.check(alembic_cfg)


def test_new_revision_gets_next_sequential_id(alembic_cfg, scratch_database, revision_dir):
    command.upgrade(alembic_cfg, "head")
    script = command.revision(alembic_cfg, message="probe", autogenerate=True, version_path=str(revision_dir))
    assert script.revision == "0012"
    assert script.down_revision == "0011"
    generated = next(revision_dir.glob("0012_*probe*.py")).read_text()
    assert "alembic_version" not in generated
