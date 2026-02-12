import pytest
from src.database.dal.bot.servers_dal import ServersDal

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

SERVER_ID = 111111111111111111
SERVER_NAME = "Test Server"


async def test_insert_server(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    result = await dal.get_server(server_id=SERVER_ID)
    assert result is not None
    assert result["id"] == SERVER_ID
    assert result["name"] == SERVER_NAME


async def test_insert_server_upsert_updates_name(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    await dal.insert_server(SERVER_ID, "Updated Name")
    result = await dal.get_server(server_id=SERVER_ID)
    assert result["name"] == "Updated Name"


async def test_delete_server(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    await dal.delete_server(SERVER_ID)
    result = await dal.get_server(server_id=SERVER_ID)
    assert result is None


async def test_get_server_returns_none_for_missing(db_session, log):
    dal = ServersDal(db_session, log)
    result = await dal.get_server(server_id=999999999999999999)
    assert result is None


async def test_get_all_servers(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, "Alpha Server")
    await dal.insert_server(SERVER_ID + 1, "Beta Server")
    results = await dal.get_server()
    assert len(results) == 2
    assert results[0]["name"] == "Alpha Server"
    assert results[1]["name"] == "Beta Server"


async def test_default_boolean_flags(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    result = await dal.get_server(server_id=SERVER_ID)
    assert result["msg_on_join"] is True
    assert result["msg_on_leave"] is True
    assert result["msg_on_server_update"] is True
    assert result["msg_on_member_update"] is True
    assert result["block_invis_members"] is False
    assert result["bot_word_reactions"] is True


async def test_update_msg_on_join(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    await dal.update_msg_on_join(SERVER_ID, False, 123)
    result = await dal.get_server(server_id=SERVER_ID)
    assert result["msg_on_join"] is False
    assert result["updated_by"] == 123


async def test_update_msg_on_leave(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    await dal.update_msg_on_leave(SERVER_ID, False, 456)
    result = await dal.get_server(server_id=SERVER_ID)
    assert result["msg_on_leave"] is False


async def test_update_msg_on_server_update(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    await dal.update_msg_on_server_update(SERVER_ID, False, 789)
    result = await dal.get_server(server_id=SERVER_ID)
    assert result["msg_on_server_update"] is False


async def test_update_msg_on_member_update(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    await dal.update_msg_on_member_update(SERVER_ID, False, 111)
    result = await dal.get_server(server_id=SERVER_ID)
    assert result["msg_on_member_update"] is False


async def test_update_block_invis_members(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    await dal.update_block_invis_members(SERVER_ID, True, 222)
    result = await dal.get_server(server_id=SERVER_ID)
    assert result["block_invis_members"] is True


async def test_update_bot_word_reactions(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    await dal.update_bot_word_reactions(SERVER_ID, False, 333)
    result = await dal.get_server(server_id=SERVER_ID)
    assert result["bot_word_reactions"] is False


async def test_get_server_with_profanity_join_no_filter(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, SERVER_NAME)
    result = await dal.get_server(server_id=SERVER_ID, channel_id=999)
    assert result is not None
    assert result["profanity_filter"] is None


async def test_delete_server_cascades_children(db_session, log):
    from src.database.dal.bot.custom_commands_dal import CustomCommandsDal

    server_dal = ServersDal(db_session, log)
    cmd_dal = CustomCommandsDal(db_session, log)
    await server_dal.insert_server(SERVER_ID, SERVER_NAME)
    await cmd_dal.insert_command(SERVER_ID, 1, "hello", "says hello")
    await server_dal.delete_server(SERVER_ID)
    cmds = await cmd_dal.get_all_server_commands(SERVER_ID)
    assert len(cmds) == 0
