"""Tests for the base gw2 command group and cog setup functions."""

import pytest
from src.gw2.cogs import daily, gw2
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_gw2_group_invokes_subcommand():
    ctx = MagicMock()
    with patch("src.gw2.cogs.gw2.bot_utils.invoke_subcommand", new_callable=AsyncMock) as mock_invoke:
        await gw2.GuildWars2.gw2.callback(gw2.GuildWars2(MagicMock()), ctx)
    mock_invoke.assert_awaited_once_with(ctx, "gw2")


@pytest.mark.asyncio
async def test_gw2_setup_adds_cog():
    bot = MagicMock()
    bot.add_cog = AsyncMock()
    await gw2.setup(bot)
    assert isinstance(bot.add_cog.call_args[0][0], gw2.GuildWars2)


@pytest.mark.asyncio
async def test_daily_setup_replaces_gw2_command():
    bot = MagicMock()
    bot.add_cog = AsyncMock()
    await daily.setup(bot)
    bot.remove_command.assert_called_once_with("gw2")
    assert isinstance(bot.add_cog.call_args[0][0], daily.GW2Daily)
