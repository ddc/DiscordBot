"""Tests for the on_resumed event cog."""

import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, Mock

sys.modules["ddcDatabases"] = Mock()

from src.bot.cogs.events.on_resumed import OnResumed, setup
from src.bot.constants import messages


@pytest.fixture
def bot():
    bot = MagicMock()
    bot.user = "TestBot#0001"
    bot.add_cog = AsyncMock()
    return bot


def test_init_stores_bot(bot):
    assert OnResumed(bot).bot is bot


@pytest.mark.asyncio
async def test_logs_resumed_message(bot):
    await OnResumed(bot).on_resumed()
    bot.log.info.assert_called_once_with(messages.Bot.resumed(bot.user))


@pytest.mark.asyncio
async def test_logging_failure_falls_back_to_print(bot, capsys):
    bot.log.info.side_effect = RuntimeError("log closed")
    await OnResumed(bot).on_resumed()
    assert "Bot resumed - logging failed: log closed" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_setup_adds_cog(bot):
    await setup(bot)
    cog = bot.add_cog.call_args[0][0]
    assert isinstance(cog, OnResumed)
