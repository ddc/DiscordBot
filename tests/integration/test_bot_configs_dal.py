import pytest
from src.bot.constants import variables
from src.database.dal.bot.bot_configs_dal import BotConfigsDal
from uuid import UUID

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_get_bot_configs_returns_seeded_row(db_session, log):
    dal = BotConfigsDal(db_session, log)
    results = await dal.get_bot_configs()
    assert len(results) == 1
    row = results[0]
    assert isinstance(row["id"], UUID)
    assert row["prefix"] == variables.PREFIX
    assert row["author_id"] == int(variables.AUTHOR_ID)
    assert row["url"] == variables.BOT_WEBPAGE_URL
    assert row["description"] == variables.DESCRIPTION


async def test_get_bot_prefix_returns_seeded_value(db_session, log):
    dal = BotConfigsDal(db_session, log)
    prefix = await dal.get_bot_prefix()
    assert prefix == variables.PREFIX


async def test_update_bot_prefix(db_session, log):
    dal = BotConfigsDal(db_session, log)
    await dal.update_bot_prefix("?")
    prefix = await dal.get_bot_prefix()
    assert prefix == "?"


async def test_update_bot_description(db_session, log):
    dal = BotConfigsDal(db_session, log)
    new_desc = "Updated description"
    await dal.update_bot_description(new_desc)
    results = await dal.get_bot_configs()
    assert results[0]["description"] == new_desc


async def test_update_prefix_does_not_affect_other_fields(db_session, log):
    dal = BotConfigsDal(db_session, log)
    await dal.update_bot_prefix("$")
    results = await dal.get_bot_configs()
    row = results[0]
    assert row["prefix"] == "$"
    assert row["author_id"] == int(variables.AUTHOR_ID)
    assert row["url"] == variables.BOT_WEBPAGE_URL
