import pytest
import pytest_asyncio
from src.database.dal.bot.custom_commands_dal import CustomCommandsDal
from src.database.dal.bot.servers_dal import ServersDal

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

SERVER_ID = 222222222222222222
USER_ID = 100


@pytest_asyncio.fixture
async def server(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, "Cmd Test Server")


async def test_insert_and_get_command(db_session, log, server):
    dal = CustomCommandsDal(db_session, log)
    await dal.insert_command(SERVER_ID, USER_ID, "ping", "responds with pong")
    result = await dal.get_command(SERVER_ID, "ping")
    assert result is not None
    assert result["name"] == "ping"
    assert result["description"] == "responds with pong"
    assert result["created_by"] == USER_ID


async def test_get_command_returns_none_for_missing(db_session, log, server):
    dal = CustomCommandsDal(db_session, log)
    result = await dal.get_command(SERVER_ID, "nonexistent")
    assert result is None


async def test_update_command_description(db_session, log, server):
    dal = CustomCommandsDal(db_session, log)
    await dal.insert_command(SERVER_ID, USER_ID, "greet", "old desc")
    await dal.update_command_description(SERVER_ID, USER_ID + 1, "greet", "new desc")
    result = await dal.get_command(SERVER_ID, "greet")
    assert result["description"] == "new desc"
    assert result["updated_by"] == USER_ID + 1


async def test_delete_server_command(db_session, log, server):
    dal = CustomCommandsDal(db_session, log)
    await dal.insert_command(SERVER_ID, USER_ID, "bye", "says bye")
    await dal.delete_server_command(SERVER_ID, "bye")
    result = await dal.get_command(SERVER_ID, "bye")
    assert result is None


async def test_delete_all_commands(db_session, log, server):
    dal = CustomCommandsDal(db_session, log)
    await dal.insert_command(SERVER_ID, USER_ID, "cmd1", "d1")
    await dal.insert_command(SERVER_ID, USER_ID, "cmd2", "d2")
    await dal.delete_all_commands(SERVER_ID)
    results = await dal.get_all_server_commands(SERVER_ID)
    assert len(results) == 0


async def test_get_all_server_commands_sorted(db_session, log, server):
    dal = CustomCommandsDal(db_session, log)
    await dal.insert_command(SERVER_ID, USER_ID, "zebra", "z")
    await dal.insert_command(SERVER_ID, USER_ID, "alpha", "a")
    await dal.insert_command(SERVER_ID, USER_ID, "mid", "m")
    results = await dal.get_all_server_commands(SERVER_ID)
    assert len(results) == 3
    assert results[0]["name"] == "alpha"
    assert results[1]["name"] == "mid"
    assert results[2]["name"] == "zebra"


async def test_commands_scoped_to_server(db_session, log):
    server_dal = ServersDal(db_session, log)
    cmd_dal = CustomCommandsDal(db_session, log)
    other_server = SERVER_ID + 1
    await server_dal.insert_server(SERVER_ID, "Server A")
    await server_dal.insert_server(other_server, "Server B")
    await cmd_dal.insert_command(SERVER_ID, USER_ID, "shared_name", "on A")
    await cmd_dal.insert_command(other_server, USER_ID, "shared_name", "on B")
    result_a = await cmd_dal.get_command(SERVER_ID, "shared_name")
    result_b = await cmd_dal.get_command(other_server, "shared_name")
    assert result_a["description"] == "on A"
    assert result_b["description"] == "on B"
