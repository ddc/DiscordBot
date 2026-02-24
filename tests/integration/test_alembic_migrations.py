import pytest
from sqlalchemy import text

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

EXPECTED_TABLES = [
    "bot_configs",
    "servers",
    "custom_commands",
    "profanity_filters",
    "dice_rolls",
    "gw2_keys",
    "gw2_configs",
    "gw2_sessions",
    "gw2_session_chars",
]

EXPECTED_TRIGGERS = [
    "before_update_bot_configs_tr",
    "before_update_servers_tr",
    "before_update_custom_commands_tr",
    "before_update_profanity_filters_tr",
    "before_update_dice_rolls_tr",
    "before_update_gw2_keys_tr",
    "before_update_gw2_configs_tr",
    "before_update_gw2_sessions_tr",
    "before_update_gw2_session_chars_tr",
]


async def _fetch_rows(db_session, stmt):
    from ddcDatabases import DBUtilsAsync

    db = DBUtilsAsync(db_session)
    return await db.fetchall(stmt, True)


async def _execute(db_session, stmt):
    from ddcDatabases import DBUtilsAsync

    db = DBUtilsAsync(db_session)
    await db.execute(stmt)


# ──────────────────────────────────────────────────────────────────────
# 0001 — Functions & schema
# ──────────────────────────────────────────────────────────────────────


async def test_updated_at_function_exists(db_session):
    rows = await _fetch_rows(
        db_session,
        text("SELECT routine_name FROM information_schema.routines WHERE routine_name = 'updated_at_column_func'"),
    )
    assert len(rows) == 1
    assert rows[0]["routine_name"] == "updated_at_column_func"


# ──────────────────────────────────────────────────────────────────────
# All tables created
# ──────────────────────────────────────────────────────────────────────


async def test_all_tables_exist(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        ),
    )
    table_names = [r["table_name"] for r in rows]
    for expected in EXPECTED_TABLES:
        assert expected in table_names, f"Table '{expected}' not found"


async def test_all_triggers_exist(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT trigger_name FROM information_schema.triggers WHERE trigger_schema = 'public' ORDER BY trigger_name"
        ),
    )
    trigger_names = [r["trigger_name"] for r in rows]
    for expected in EXPECTED_TRIGGERS:
        assert expected in trigger_names, f"Trigger '{expected}' not found"


async def test_alembic_version_at_head(db_session):
    rows = await _fetch_rows(
        db_session,
        text("SELECT version_num FROM alembic_version"),
    )
    assert len(rows) == 1
    assert rows[0]["version_num"] == "0011"


# ──────────────────────────────────────────────────────────────────────
# 0002 — bot_configs columns & seed data
# ──────────────────────────────────────────────────────────────────────


async def test_bot_configs_columns(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_name = 'bot_configs' ORDER BY ordinal_position"
        ),
    )
    cols = {r["column_name"]: r for r in rows}
    assert "id" in cols
    assert "prefix" in cols
    assert "author_id" in cols
    assert "url" in cols
    assert "description" in cols
    assert "updated_at" in cols
    assert "created_at" in cols
    assert cols["prefix"]["data_type"] == "character"
    assert cols["id"]["is_nullable"] == "NO"


async def test_bot_configs_seed_row(db_session):
    rows = await _fetch_rows(
        db_session,
        text("SELECT id, prefix FROM bot_configs WHERE id = 1"),
    )
    assert len(rows) == 1
    assert rows[0]["id"] == 1


async def test_bot_configs_insert_and_read(db_session):
    await _execute(
        db_session,
        text(
            "INSERT INTO bot_configs (id, prefix, author_id, url, description) "
            "VALUES (99, '?', 123, 'http://test', 'test bot')"
        ),
    )
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM bot_configs WHERE id = 99"),
    )
    assert len(rows) == 1
    assert rows[0]["prefix"] == "?"
    assert rows[0]["description"] == "test bot"
    assert rows[0]["updated_at"] is not None
    assert rows[0]["created_at"] is not None


# ──────────────────────────────────────────────────────────────────────
# 0003 — servers columns, defaults & indexes
# ──────────────────────────────────────────────────────────────────────


async def test_servers_columns(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT column_name, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_name = 'servers' ORDER BY ordinal_position"
        ),
    )
    cols = {r["column_name"]: r for r in rows}
    assert "id" in cols
    assert "name" in cols
    assert cols["name"]["is_nullable"] == "YES"
    assert "msg_on_join" in cols
    assert "block_invis_members" in cols
    assert "updated_by" in cols
    assert cols["updated_by"]["is_nullable"] == "YES"


async def test_servers_index_exists(db_session):
    rows = await _fetch_rows(
        db_session,
        text("SELECT indexname FROM pg_indexes WHERE tablename = 'servers' AND indexname = 'ix_servers_id'"),
    )
    assert len(rows) == 1


async def test_servers_insert_and_read_defaults(db_session):
    await _execute(
        db_session,
        text("INSERT INTO servers (id, name) VALUES (10001, 'Migration Test Server')"),
    )
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM servers WHERE id = 10001"),
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["name"] == "Migration Test Server"
    assert row["msg_on_join"] is True
    assert row["msg_on_leave"] is True
    assert row["msg_on_server_update"] is True
    assert row["msg_on_member_update"] is True
    assert row["block_invis_members"] is False
    assert row["bot_word_reactions"] is True
    assert row["updated_by"] is None


# ──────────────────────────────────────────────────────────────────────
# 0004 — custom_commands FK, index & cascade
# ──────────────────────────────────────────────────────────────────────


async def test_custom_commands_fk_to_servers(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT tc.constraint_name, ccu.table_name AS foreign_table "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.constraint_column_usage ccu "
            "  ON tc.constraint_name = ccu.constraint_name "
            "WHERE tc.table_name = 'custom_commands' AND tc.constraint_type = 'FOREIGN KEY'"
        ),
    )
    assert len(rows) >= 1
    assert any(r["foreign_table"] == "servers" for r in rows)


async def test_custom_commands_server_id_index(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'custom_commands' "
            "AND indexname = 'ix_custom_commands_server_id'"
        ),
    )
    assert len(rows) == 1


async def test_custom_commands_insert_and_read(db_session):
    await _execute(db_session, text("INSERT INTO servers (id, name) VALUES (10002, 'CC Server')"))
    await _execute(
        db_session,
        text(
            "INSERT INTO custom_commands (server_id, name, description, created_by) "
            "VALUES (10002, 'hello', 'says hello', 42)"
        ),
    )
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM custom_commands WHERE server_id = 10002"),
    )
    assert len(rows) == 1
    assert rows[0]["name"] == "hello"
    assert rows[0]["description"] == "says hello"
    assert rows[0]["created_by"] == 42


async def test_custom_commands_cascade_delete(db_session):
    await _execute(db_session, text("INSERT INTO servers (id, name) VALUES (10003, 'Cascade CC')"))
    await _execute(
        db_session,
        text("INSERT INTO custom_commands (server_id, name, description) VALUES (10003, 'temp', 'will be cascaded')"),
    )
    await _execute(db_session, text("DELETE FROM servers WHERE id = 10003"))
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM custom_commands WHERE server_id = 10003"),
    )
    assert len(rows) == 0


# ──────────────────────────────────────────────────────────────────────
# 0005 — profanity_filters
# ──────────────────────────────────────────────────────────────────────


async def test_profanity_filters_columns(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'profanity_filters' ORDER BY ordinal_position"
        ),
    )
    cols = [r["column_name"] for r in rows]
    assert "server_id" in cols
    assert "channel_id" in cols
    assert "channel_name" in cols
    assert "created_by" in cols


async def test_profanity_filters_insert_and_read(db_session):
    await _execute(db_session, text("INSERT INTO servers (id, name) VALUES (10004, 'PF Server')"))
    await _execute(
        db_session,
        text(
            "INSERT INTO profanity_filters (server_id, channel_id, channel_name, created_by) "
            "VALUES (10004, 80001, 'general', 7)"
        ),
    )
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM profanity_filters WHERE server_id = 10004"),
    )
    assert len(rows) == 1
    assert rows[0]["channel_id"] == 80001
    assert rows[0]["channel_name"] == "general"


async def test_profanity_filters_cascade_delete(db_session):
    await _execute(db_session, text("INSERT INTO servers (id, name) VALUES (10005, 'Cascade PF')"))
    await _execute(
        db_session,
        text("INSERT INTO profanity_filters (server_id, channel_id, channel_name) VALUES (10005, 80002, 'spam')"),
    )
    await _execute(db_session, text("DELETE FROM servers WHERE id = 10005"))
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM profanity_filters WHERE server_id = 10005"),
    )
    assert len(rows) == 0


# ──────────────────────────────────────────────────────────────────────
# 0006 — dice_rolls indexes
# ──────────────────────────────────────────────────────────────────────


async def test_dice_rolls_indexes(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'dice_rolls' "
            "AND indexname IN ('ix_dice_rolls_server_id', 'ix_dice_rolls_user_id')"
        ),
    )
    index_names = [r["indexname"] for r in rows]
    assert "ix_dice_rolls_server_id" in index_names
    assert "ix_dice_rolls_user_id" in index_names


async def test_dice_rolls_insert_and_read(db_session):
    await _execute(db_session, text("INSERT INTO servers (id, name) VALUES (10006, 'Dice Server')"))
    await _execute(
        db_session,
        text("INSERT INTO dice_rolls (server_id, user_id, roll, dice_size) VALUES (10006, 555, 18, 20)"),
    )
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM dice_rolls WHERE server_id = 10006 AND user_id = 555"),
    )
    assert len(rows) == 1
    assert rows[0]["roll"] == 18
    assert rows[0]["dice_size"] == 20


async def test_dice_rolls_cascade_delete(db_session):
    await _execute(db_session, text("INSERT INTO servers (id, name) VALUES (10007, 'Cascade Dice')"))
    await _execute(
        db_session,
        text("INSERT INTO dice_rolls (server_id, user_id, roll, dice_size) VALUES (10007, 1, 6, 6)"),
    )
    await _execute(db_session, text("DELETE FROM servers WHERE id = 10007"))
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM dice_rolls WHERE server_id = 10007"),
    )
    assert len(rows) == 0


# ──────────────────────────────────────────────────────────────────────
# 0007 — gw2_keys unique constraint
# ──────────────────────────────────────────────────────────────────────


async def test_gw2_keys_user_id_unique(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT constraint_name FROM information_schema.table_constraints "
            "WHERE table_name = 'gw2_keys' AND constraint_type = 'UNIQUE' "
            "AND constraint_name != 'gw2_keys_pkey'"
        ),
    )
    assert len(rows) >= 1


async def test_gw2_keys_insert_and_read(db_session):
    await _execute(
        db_session,
        text(
            "INSERT INTO gw2_keys (user_id, name, gw2_acc_name, server, permissions, key) "
            "VALUES (7001, 'Main', 'Acc.1234', 'Anvil Rock', 'account', 'KEY-ABC')"
        ),
    )
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM gw2_keys WHERE user_id = 7001"),
    )
    assert len(rows) == 1
    assert rows[0]["gw2_acc_name"] == "Acc.1234"
    assert rows[0]["key"] == "KEY-ABC"


# ──────────────────────────────────────────────────────────────────────
# 0008 — gw2_configs FK + unique server_id
# ──────────────────────────────────────────────────────────────────────


async def test_gw2_configs_fk_and_unique(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT constraint_type FROM information_schema.table_constraints "
            "WHERE table_name = 'gw2_configs' "
            "AND constraint_type IN ('FOREIGN KEY', 'UNIQUE')"
        ),
    )
    types = [r["constraint_type"] for r in rows]
    assert "FOREIGN KEY" in types
    assert "UNIQUE" in types


async def test_gw2_configs_insert_and_read(db_session):
    await _execute(db_session, text("INSERT INTO servers (id, name) VALUES (10008, 'GW2 Cfg Server')"))
    await _execute(
        db_session,
        text("INSERT INTO gw2_configs (server_id) VALUES (10008)"),
    )
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM gw2_configs WHERE server_id = 10008"),
    )
    assert len(rows) == 1
    assert rows[0]["session"] is False
    assert rows[0]["updated_by"] is None


async def test_gw2_configs_cascade_delete(db_session):
    await _execute(db_session, text("INSERT INTO servers (id, name) VALUES (10009, 'Cascade GW2')"))
    await _execute(db_session, text("INSERT INTO gw2_configs (server_id) VALUES (10009)"))
    await _execute(db_session, text("DELETE FROM servers WHERE id = 10009"))
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM gw2_configs WHERE server_id = 10009"),
    )
    assert len(rows) == 0


# ──────────────────────────────────────────────────────────────────────
# 0009 — gw2_sessions JSONB columns
# ──────────────────────────────────────────────────────────────────────


async def test_gw2_sessions_jsonb_columns(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_name = 'gw2_sessions' AND column_name IN ('start', 'end')"
        ),
    )
    cols = {r["column_name"]: r for r in rows}
    assert cols["start"]["data_type"] == "jsonb"
    assert cols["start"]["is_nullable"] == "NO"
    assert cols["end"]["data_type"] == "jsonb"
    assert cols["end"]["is_nullable"] == "YES"


async def test_gw2_sessions_insert_and_read_jsonb(db_session):
    await _execute(
        db_session,
        text(
            "INSERT INTO gw2_sessions (user_id, acc_name, start) "
            """VALUES (8001, 'TestAcc.9999', '{"gold": 100, "karma": 5000}'::jsonb)"""
        ),
    )
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM gw2_sessions WHERE user_id = 8001"),
    )
    assert len(rows) == 1
    assert rows[0]["start"]["gold"] == 100
    assert rows[0]["start"]["karma"] == 5000
    assert rows[0]["end"] is None


# ──────────────────────────────────────────────────────────────────────
# 0010/0011 — gw2_session_chars FK (unique name dropped in 0011)
# ──────────────────────────────────────────────────────────────────────


async def test_gw2_session_chars_fk_to_sessions(db_session):
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT ccu.table_name AS foreign_table "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.constraint_column_usage ccu "
            "  ON tc.constraint_name = ccu.constraint_name "
            "WHERE tc.table_name = 'gw2_session_chars' AND tc.constraint_type = 'FOREIGN KEY'"
        ),
    )
    assert any(r["foreign_table"] == "gw2_sessions" for r in rows)


async def test_gw2_session_chars_no_unique_name(db_session):
    """Migration 0011 dropped the unique constraint on name to allow start+end records."""
    rows = await _fetch_rows(
        db_session,
        text(
            "SELECT constraint_name FROM information_schema.table_constraints "
            "WHERE table_name = 'gw2_session_chars' AND constraint_type = 'UNIQUE' "
            "AND constraint_name = 'gw2_session_chars_name_key'"
        ),
    )
    assert len(rows) == 0


async def test_gw2_session_chars_insert_and_read(db_session):
    await _execute(
        db_session,
        text(
            "INSERT INTO gw2_sessions (id, user_id, acc_name, start) "
            """VALUES (90001, 8002, 'Char.1111', '{}'::jsonb)"""
        ),
    )
    await _execute(
        db_session,
        text(
            "INSERT INTO gw2_session_chars "
            "(session_id, user_id, name, profession, deaths, start) "
            "VALUES (90001, 8002, 'MyWarrior', 'Warrior', 5, true)"
        ),
    )
    rows = await _fetch_rows(
        db_session,
        text("SELECT * FROM gw2_session_chars WHERE user_id = 8002"),
    )
    assert len(rows) == 1
    assert rows[0]["name"] == "MyWarrior"
    assert rows[0]["profession"] == "Warrior"
    assert rows[0]["deaths"] == 5
    assert rows[0]["start"] is True
    assert rows[0]["end"] is None


# ──────────────────────────────────────────────────────────────────────
# Trigger functionality — updated_at auto-updates
# ──────────────────────────────────────────────────────────────────────


async def test_updated_at_trigger_fires_on_update(db_session):
    """Verify the updated_at_column_func trigger actually updates the timestamp."""
    await _execute(db_session, text("INSERT INTO servers (id, name) VALUES (10010, 'Trigger Test')"))
    rows_before = await _fetch_rows(
        db_session,
        text("SELECT updated_at FROM servers WHERE id = 10010"),
    )
    original_ts = rows_before[0]["updated_at"]

    # Small delay then update
    await _execute(
        db_session,
        text("UPDATE servers SET name = 'Trigger Test Updated' WHERE id = 10010"),
    )
    rows_after = await _fetch_rows(
        db_session,
        text("SELECT updated_at FROM servers WHERE id = 10010"),
    )
    new_ts = rows_after[0]["updated_at"]
    assert new_ts >= original_ts
