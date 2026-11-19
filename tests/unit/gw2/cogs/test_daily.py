"""Tests for the GW2 Wizard's Vault daily cog."""

import pytest
from discord.ext import commands
from src.gw2.cogs.daily import GW2Daily, daily
from src.gw2.constants import gw2_messages, gw2_variables
from unittest.mock import AsyncMock, MagicMock, patch
lazy from src.gw2.cogs.gw2 import GuildWars2

DAILY_RESPONSE = {
    "meta_progress_current": 2,
    "meta_progress_complete": 4,
    "meta_reward_item_id": 99961,
    "meta_reward_astral": 20,
    "meta_reward_claimed": False,
    "objectives": [
        {
            "id": 1,
            "title": "Complete 3 Events",
            "track": "PvE",
            "acclaim": 10,
            "progress_current": 3,
            "progress_complete": 3,
            "claimed": True,
        },
        {
            "id": 2,
            "title": "Compete in 1 Player vs. Player Team Battle",
            "track": "PvP",
            "acclaim": 10,
            "progress_current": 0,
            "progress_complete": 1,
            "claimed": False,
        },
    ],
}


@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ctx.bot.db_session = MagicMock()
    ctx.bot.log = MagicMock()
    ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
    ctx.message.author.id = 12345
    ctx.message.author.display_name = "TestUser"
    ctx.message.author.display_avatar.url = "https://example.com/avatar.png"
    ctx.prefix = "!"
    return ctx


async def _run(ctx, *args, api_response=None, api_side_effect=None, key_rows=None):
    """Run the daily command with the key DAL, GW2 client and send helpers patched."""
    key_rows = [{"key": "test-api-key"}] if key_rows is None else key_rows
    with (
        patch("src.gw2.cogs.daily.Gw2KeyDal") as mock_dal,
        patch("src.gw2.cogs.daily.Gw2Client") as mock_client,
        patch("src.gw2.cogs.daily.gw2_utils.send_progress_embed", new_callable=AsyncMock),
        patch("src.gw2.cogs.daily.bot_utils.send_paginated_embed", new_callable=AsyncMock) as mock_paginated,
        patch("src.gw2.cogs.daily.bot_utils.send_warning_msg", new_callable=AsyncMock) as mock_warning,
        patch("src.gw2.cogs.daily.bot_utils.send_error_msg", new_callable=AsyncMock) as mock_error,
    ):
        mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=key_rows)
        mock_client.return_value.call_api = AsyncMock(return_value=api_response, side_effect=api_side_effect)
        await daily(ctx, *args)
        return {
            "call_api": mock_client.return_value.call_api,
            "paginated": mock_paginated,
            "warning": mock_warning,
            "error": mock_error,
        }


def test_cog_inherits_guild_wars2():

    assert isinstance(GW2Daily(MagicMock()), GuildWars2)


@pytest.mark.asyncio
async def test_daily_calls_wizardsvault_daily_endpoint(mock_ctx):
    mocks = await _run(mock_ctx, api_response=DAILY_RESPONSE)
    mocks["call_api"].assert_awaited_once_with(f"{gw2_variables.API_ACCOUNT_WIZARDSVAULT}/daily", "test-api-key")


@pytest.mark.asyncio
@pytest.mark.parametrize("period", ["weekly", "special", "WEEKLY"])
async def test_daily_other_periods(mock_ctx, period):
    mocks = await _run(mock_ctx, period, api_response=DAILY_RESPONSE)
    expected = f"{gw2_variables.API_ACCOUNT_WIZARDSVAULT}/{period.lower()}"
    mocks["call_api"].assert_awaited_once_with(expected, "test-api-key")


@pytest.mark.asyncio
async def test_daily_invalid_period_raises_bad_argument(mock_ctx):
    with pytest.raises(commands.BadArgument):
        await daily(mock_ctx, "monthly")


@pytest.mark.asyncio
async def test_daily_embed_content(mock_ctx):
    mocks = await _run(mock_ctx, api_response=DAILY_RESPONSE)
    embed = mocks["paginated"].call_args[0][1]
    assert embed.title == gw2_messages.Daily.title("daily")
    assert "`2/4`" in embed.description
    assert "20 Astral Acclaim" in embed.description
    assert gw2_messages.Daily.CLAIMED not in embed.description
    assert [f.name for f in embed.fields] == ["Complete 3 Events", "Compete in 1 Player vs. Player Team Battle"]
    assert embed.fields[0].value.startswith("✅ ")
    assert "`PvP`" in embed.fields[1].value
    assert "`0/1`" in embed.fields[1].value
    assert not embed.fields[1].value.startswith("✅")


@pytest.mark.asyncio
async def test_daily_meta_reward_claimed(mock_ctx):
    response = {**DAILY_RESPONSE, "meta_reward_claimed": True}
    mocks = await _run(mock_ctx, api_response=response)
    embed = mocks["paginated"].call_args[0][1]
    assert f"({gw2_messages.Daily.CLAIMED})" in embed.description


@pytest.mark.asyncio
async def test_special_objectives_have_no_meta_line(mock_ctx):
    mocks = await _run(mock_ctx, "special", api_response={"objectives": DAILY_RESPONSE["objectives"]})
    embed = mocks["paginated"].call_args[0][1]
    assert embed.description is None
    assert len(embed.fields) == 2


@pytest.mark.asyncio
async def test_daily_no_api_key(mock_ctx):
    mocks = await _run(mock_ctx, key_rows=[])
    mocks["error"].assert_awaited_once()
    assert gw2_messages.Key.NO_API_KEY in mocks["error"].call_args[0][1]
    mocks["call_api"].assert_not_awaited()


@pytest.mark.asyncio
async def test_daily_no_objectives(mock_ctx):
    mocks = await _run(mock_ctx, api_response={"objectives": []})
    mocks["warning"].assert_awaited_once_with(mock_ctx, gw2_messages.Daily.NO_OBJECTIVES)
    mocks["paginated"].assert_not_awaited()


@pytest.mark.asyncio
async def test_daily_api_error(mock_ctx):
    err = RuntimeError("boom")
    mocks = await _run(mock_ctx, api_side_effect=err)
    mocks["error"].assert_awaited_once_with(mock_ctx, err)
    mocks["paginated"].assert_not_awaited()
