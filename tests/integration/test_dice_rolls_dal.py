import pytest
import pytest_asyncio
from src.database.dal.bot.dice_rolls_dal import DiceRollsDal
from src.database.dal.bot.servers_dal import ServersDal

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

SERVER_ID = 333333333333333333
USER_ID = 200


@pytest_asyncio.fixture
async def server(db_session, log):
    dal = ServersDal(db_session, log)
    await dal.insert_server(SERVER_ID, "Dice Test Server")


async def test_insert_and_get_roll(db_session, log, server):
    dal = DiceRollsDal(db_session, log)
    await dal.insert_user_roll(SERVER_ID, USER_ID, 20, 18)
    results = await dal.get_user_roll_by_dice_size(SERVER_ID, USER_ID, 20)
    assert len(results) == 1
    assert results[0]["roll"] == 18
    assert results[0]["dice_size"] == 20


async def test_update_user_roll(db_session, log, server):
    dal = DiceRollsDal(db_session, log)
    await dal.insert_user_roll(SERVER_ID, USER_ID, 20, 10)
    await dal.update_user_roll(SERVER_ID, USER_ID, 20, 20)
    results = await dal.get_user_roll_by_dice_size(SERVER_ID, USER_ID, 20)
    assert results[0]["roll"] == 20


async def test_get_user_rolls_all_dice_sizes(db_session, log, server):
    dal = DiceRollsDal(db_session, log)
    await dal.insert_user_roll(SERVER_ID, USER_ID, 100, 99)
    await dal.insert_user_roll(SERVER_ID, USER_ID, 20, 15)
    await dal.insert_user_roll(SERVER_ID, USER_ID, 6, 5)
    results = await dal.get_user_rolls_all_dice_sizes(SERVER_ID, USER_ID)
    assert len(results) == 3
    assert results[0]["dice_size"] == 6
    assert results[1]["dice_size"] == 20
    assert results[2]["dice_size"] == 100


async def test_get_all_server_rolls_ordered_desc(db_session, log, server):
    dal = DiceRollsDal(db_session, log)
    await dal.insert_user_roll(SERVER_ID, USER_ID, 20, 5)
    await dal.insert_user_roll(SERVER_ID, USER_ID + 1, 20, 19)
    await dal.insert_user_roll(SERVER_ID, USER_ID + 2, 20, 12)
    results = await dal.get_all_server_rolls(SERVER_ID, 20)
    assert len(results) == 3
    assert results[0]["roll"] == 19
    assert results[1]["roll"] == 12
    assert results[2]["roll"] == 5


async def test_get_server_max_roll(db_session, log, server):
    dal = DiceRollsDal(db_session, log)
    await dal.insert_user_roll(SERVER_ID, USER_ID, 20, 5)
    await dal.insert_user_roll(SERVER_ID, USER_ID + 1, 20, 20)
    results = await dal.get_server_max_roll(SERVER_ID, 20)
    assert len(results) == 1
    assert results[0]["max_roll"] == 20
    assert results[0]["user_id"] == USER_ID + 1


async def test_delete_all_server_rolls(db_session, log, server):
    dal = DiceRollsDal(db_session, log)
    await dal.insert_user_roll(SERVER_ID, USER_ID, 20, 10)
    await dal.insert_user_roll(SERVER_ID, USER_ID, 6, 3)
    await dal.delete_all_server_rolls(SERVER_ID)
    results = await dal.get_user_rolls_all_dice_sizes(SERVER_ID, USER_ID)
    assert len(results) == 0


async def test_rolls_scoped_to_server(db_session, log):
    server_dal = ServersDal(db_session, log)
    dice_dal = DiceRollsDal(db_session, log)
    other_server = SERVER_ID + 1
    await server_dal.insert_server(SERVER_ID, "Server A")
    await server_dal.insert_server(other_server, "Server B")
    await dice_dal.insert_user_roll(SERVER_ID, USER_ID, 20, 15)
    await dice_dal.insert_user_roll(other_server, USER_ID, 20, 10)
    results_a = await dice_dal.get_user_roll_by_dice_size(SERVER_ID, USER_ID, 20)
    results_b = await dice_dal.get_user_roll_by_dice_size(other_server, USER_ID, 20)
    assert results_a[0]["roll"] == 15
    assert results_b[0]["roll"] == 10
