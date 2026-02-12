import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from src.database.dal.bot.servers_dal import ServersDal
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

SERVER_ID = 555555555555555555


@pytest_asyncio.fixture
async def server(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, "GW2 Config Server")


async def test_insert_and_get_configs(db_session, log, server):
    dal = Gw2ConfigsDal(db_session, log)
    await dal.insert_gw2_server_configs(SERVER_ID)
    results = await dal.get_gw2_server_configs(SERVER_ID)
    assert len(results) == 1
    assert results[0]["server_id"] == SERVER_ID
    assert results[0]["session"] is False


async def test_update_session_flag(db_session, log, server):
    dal = Gw2ConfigsDal(db_session, log)
    await dal.insert_gw2_server_configs(SERVER_ID)
    await dal.update_gw2_session_config(SERVER_ID, True, 42)
    results = await dal.get_gw2_server_configs(SERVER_ID)
    assert results[0]["session"] is True
    assert results[0]["updated_by"] == 42


async def test_get_configs_returns_empty_for_missing_server(db_session, log, server):
    dal = Gw2ConfigsDal(db_session, log)
    results = await dal.get_gw2_server_configs(999999999999999999)
    assert len(results) == 0


async def test_unique_server_id_constraint(db_session, log, server):
    dal = Gw2ConfigsDal(db_session, log)
    await dal.insert_gw2_server_configs(SERVER_ID)
    with pytest.raises(IntegrityError):
        await dal.insert_gw2_server_configs(SERVER_ID)
