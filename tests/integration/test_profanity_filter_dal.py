import pytest
import pytest_asyncio
from src.database.dal.bot.profanity_filters_dal import ProfanityFilterDal
from src.database.dal.bot.servers_dal import ServersDal

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

SERVER_ID = 444444444444444444
CHANNEL_ID = 900000000000000001
USER_ID = 300


@pytest_asyncio.fixture
async def server(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, "Profanity Test Server")


async def test_insert_and_get_channel(db_session, log, server):
    dal = ProfanityFilterDal(db_session, log)
    await dal.insert_profanity_filter_channel(SERVER_ID, CHANNEL_ID, "general", USER_ID)
    results = await dal.get_profanity_filter_channel(CHANNEL_ID)
    assert len(results) == 1
    assert results[0]["channel_id"] == CHANNEL_ID
    assert results[0]["channel_name"] == "general"
    assert results[0]["created_by"] == USER_ID


async def test_delete_profanity_filter_channel(db_session, log, server):
    dal = ProfanityFilterDal(db_session, log)
    await dal.insert_profanity_filter_channel(SERVER_ID, CHANNEL_ID, "general", USER_ID)
    await dal.delete_profanity_filter_channel(CHANNEL_ID)
    results = await dal.get_profanity_filter_channel(CHANNEL_ID)
    assert len(results) == 0


async def test_get_all_server_profanity_filter_channels_sorted(db_session, log, server):
    dal = ProfanityFilterDal(db_session, log)
    await dal.insert_profanity_filter_channel(SERVER_ID, CHANNEL_ID, "zoo", USER_ID)
    await dal.insert_profanity_filter_channel(SERVER_ID, CHANNEL_ID + 1, "alpha", USER_ID)
    await dal.insert_profanity_filter_channel(SERVER_ID, CHANNEL_ID + 2, "middle", USER_ID)
    results = await dal.get_all_server_profanity_filter_channels(SERVER_ID)
    assert len(results) == 3
    assert results[0]["channel_name"] == "alpha"
    assert results[1]["channel_name"] == "middle"
    assert results[2]["channel_name"] == "zoo"


async def test_channels_scoped_to_server(db_session, log):
    server_dal = ServersDal(db_session, log)
    pf_dal = ProfanityFilterDal(db_session, log)
    other_server = SERVER_ID + 1
    await server_dal.insert_server(SERVER_ID, "Server A")
    await server_dal.insert_server(other_server, "Server B")
    await pf_dal.insert_profanity_filter_channel(SERVER_ID, CHANNEL_ID, "chan-a", USER_ID)
    await pf_dal.insert_profanity_filter_channel(other_server, CHANNEL_ID + 1, "chan-b", USER_ID)
    results_a = await pf_dal.get_all_server_profanity_filter_channels(SERVER_ID)
    results_b = await pf_dal.get_all_server_profanity_filter_channels(other_server)
    assert len(results_a) == 1
    assert len(results_b) == 1
    assert results_a[0]["channel_name"] == "chan-a"
    assert results_b[0]["channel_name"] == "chan-b"


async def test_get_server_with_profanity_join(db_session, log, server):
    pf_dal = ProfanityFilterDal(db_session, log)
    server_dal = ServersDal(db_session, log)
    await pf_dal.insert_profanity_filter_channel(SERVER_ID, CHANNEL_ID, "filtered", USER_ID)
    result = await server_dal.get_server(server_id=SERVER_ID, channel_id=CHANNEL_ID)
    assert result is not None
    assert result["profanity_filter"] is not None
