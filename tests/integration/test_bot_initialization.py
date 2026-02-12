import discord
import pytest
from aiohttp import ClientSession
from src.bot.constants import variables
from src.bot.discord_bot import Bot
from src.database.dal.bot.bot_configs_dal import BotConfigsDal

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_get_command_prefix_from_db(db_session, log):
    from src.__main__ import _get_command_prefix

    prefix = await _get_command_prefix(db_session, log)
    assert prefix == variables.PREFIX


async def test_get_command_prefix_after_update(db_session, log):
    from src.__main__ import _get_command_prefix

    dal = BotConfigsDal(db_session, log)
    await dal.update_bot_prefix("?")
    prefix = await _get_command_prefix(db_session, log)
    assert prefix == "?"


async def test_bot_init_with_real_session(db_session, log):
    async with ClientSession() as aiosession:
        bot = Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            aiosession=aiosession,
            db_session=db_session,
            log=log,
        )
        assert bot.db_session is db_session
        assert bot.command_prefix == "!"
        assert isinstance(bot.settings, dict)
        assert "bot" in bot.settings
        assert "gw2" in bot.settings
        await bot.close()


async def test_bot_settings_loaded(db_session, log):
    async with ClientSession() as aiosession:
        bot = Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            aiosession=aiosession,
            db_session=db_session,
            log=log,
        )
        assert "BGActivityTimer" in bot.settings["bot"]
        assert "AllowedDMCommands" in bot.settings["bot"]
        assert "EmbedColor" in bot.settings["bot"]
        assert "EmbedColor" in bot.settings["gw2"]
        await bot.close()
