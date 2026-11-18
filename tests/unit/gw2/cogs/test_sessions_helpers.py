"""Direct tests for the helper functions behind the GW2 session command."""

import discord
import pytest
from src.gw2.cogs import sessions
from src.gw2.constants import gw2_messages
from unittest.mock import AsyncMock, MagicMock, patch

MODULE = "src.gw2.cogs.sessions"


@pytest.fixture
def ctx():
    ctx = MagicMock()
    ctx.prefix = "!"
    ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
    ctx.channel = MagicMock(spec=discord.TextChannel)
    ctx.message.author.id = 12345
    ctx.message.author.display_name = "TestUser"
    ctx.message.author.mention = "<@12345>"
    ctx.message.author.activities = ()
    return ctx


def _activity(name, activity_type=discord.ActivityType.playing):
    activity = MagicMock()
    activity.name = name
    activity.type = activity_type
    return activity


class TestMissingPermissionsMsg:
    def test_returns_none_when_any_permission_present(self, ctx):
        assert sessions._missing_permissions_msg(ctx, "wallet") is None

    def test_lists_every_permission_as_missing(self, ctx):
        msg = sessions._missing_permissions_msg(ctx, "guilds,pvp")
        assert msg.startswith(gw2_messages.Session.MISSING_PERMISSIONS_TITLE)
        for name in ("account", "characters", "progression", "wallet"):
            assert f"- {name} is MISSING" in msg
        assert gw2_messages.Key.add_info_help("!") in msg


class TestSessionEndingMsg:
    @pytest.mark.parametrize("remaining", [None, 0, -5])
    def test_no_waiting_time_without_positive_remaining(self, remaining):
        with patch(f"{MODULE}.gw2_utils.get_session_end_remaining_seconds", return_value=remaining):
            assert sessions._session_ending_msg(1) == gw2_messages.Session.END_PROCESSING

    @pytest.mark.parametrize(("remaining", "expected"), [(45, "`45s`"), (125, "`2m 5s`"), (60, "`1m 0s`")])
    def test_formats_waiting_time(self, remaining, expected):
        with patch(f"{MODULE}.gw2_utils.get_session_end_remaining_seconds", return_value=remaining):
            msg = sessions._session_ending_msg(1)
        assert msg.startswith(gw2_messages.Session.END_PROCESSING)
        assert f"{gw2_messages.Session.WAITING_TIME}: {expected}" in msg


class TestResolveOpenSession:
    @pytest.mark.asyncio
    async def test_session_still_ending_sends_warning(self, ctx):
        dal = MagicMock()
        dal.get_user_last_session = AsyncMock()
        with (
            patch(f"{MODULE}.gw2_utils.is_session_ending", return_value=True),
            patch(f"{MODULE}.gw2_utils.get_session_end_remaining_seconds", return_value=30),
            patch(f"{MODULE}.bot_utils.send_warning_msg", new_callable=AsyncMock) as mock_warning,
        ):
            result = await sessions._resolve_open_session(ctx, dal, [{}], "key", 1, is_playing=False)

        assert result is None
        mock_warning.assert_awaited_once()
        assert "`30s`" in mock_warning.call_args[0][1]
        dal.get_user_last_session.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_finalizes_session_when_not_playing(self, ctx):
        finalized = [{"start": {"date": "a"}, "end": {"date": "b"}}]
        dal = MagicMock()
        dal.get_user_last_session = AsyncMock(return_value=finalized)
        progress = AsyncMock()
        with (
            patch(f"{MODULE}.gw2_utils.is_session_ending", return_value=False),
            patch(f"{MODULE}.gw2_utils.send_progress_embed", new_callable=AsyncMock, return_value=progress),
            patch(f"{MODULE}.gw2_utils.end_session", new_callable=AsyncMock) as mock_end,
        ):
            result = await sessions._resolve_open_session(ctx, dal, [{}], "key", 1, is_playing=False)

        assert result == (finalized, {"date": "b"}, False, progress)
        mock_end.assert_awaited_once_with(ctx.bot, ctx.message.author, "key", skip_delay=True)

    @pytest.mark.asyncio
    async def test_live_snapshot_reuses_given_session_rows(self, ctx):
        rs_session = [{"start": {"date": "a"}, "end": None}]
        dal = MagicMock()
        dal.get_user_last_session = AsyncMock()
        progress = AsyncMock()
        with (
            patch(f"{MODULE}.gw2_utils.send_progress_embed", new_callable=AsyncMock, return_value=progress),
            patch(f"{MODULE}.gw2_utils.get_user_stats", new_callable=AsyncMock, return_value={"gold": 1}),
            patch(f"{MODULE}.bot_utils.convert_datetime_to_str_short", return_value="2024-01-15 12:00:00"),
        ):
            result = await sessions._resolve_open_session(ctx, dal, rs_session, "key", 1, is_playing=True)

        assert result == (rs_session, {"gold": 1, "date": "2024-01-15 12:00:00"}, True, progress)
        dal.get_user_last_session.assert_not_awaited()


class TestBuildLiveCharDeaths:
    @pytest.mark.asyncio
    async def test_returns_none_without_db_rows(self, ctx):
        with patch(f"{MODULE}.Gw2SessionCharDeathsDal") as mock_dal:
            mock_dal.return_value.get_char_deaths = AsyncMock(return_value=[])
            assert await sessions._build_live_char_deaths(ctx, "key", 1) is None

    @pytest.mark.asyncio
    async def test_returns_none_when_api_fails(self, ctx):
        with (
            patch(f"{MODULE}.Gw2SessionCharDeathsDal") as mock_dal,
            patch(f"{MODULE}.Gw2Client") as mock_client,
        ):
            mock_dal.return_value.get_char_deaths = AsyncMock(return_value=[{"name": "A", "start": 1, "end": None}])
            mock_client.return_value.call_api = AsyncMock(side_effect=RuntimeError("down"))
            assert await sessions._build_live_char_deaths(ctx, "key", 1) is None

    @pytest.mark.asyncio
    async def test_merges_current_deaths_into_db_rows(self, ctx):
        rows = [{"name": "A", "start": 1, "end": None}, {"name": "Deleted", "start": 4, "end": None}]
        with (
            patch(f"{MODULE}.Gw2SessionCharDeathsDal") as mock_dal,
            patch(f"{MODULE}.Gw2Client") as mock_client,
        ):
            mock_dal.return_value.get_char_deaths = AsyncMock(return_value=rows)
            mock_client.return_value.call_api = AsyncMock(return_value=[{"name": "A", "deaths": 7}])
            result = await sessions._build_live_char_deaths(ctx, "key", 1)

        assert result[0]["end"] == 7
        assert result[1]["end"] is None


class TestIsUserPlayingGw2:
    def test_false_in_dm_channel(self, ctx):
        ctx.channel = MagicMock(spec=discord.DMChannel)
        ctx.message.author.activities = (_activity(gw2_messages.Gw2.FULL_NAME),)
        assert sessions._is_user_playing_gw2(ctx) is False

    def test_false_when_author_has_no_activities(self, ctx):
        ctx.message.author = object()
        assert sessions._is_user_playing_gw2(ctx) is False

    def test_custom_status_mentioning_gw2_does_not_count(self, ctx):
        ctx.message.author.activities = (_activity("Guild Wars 2 later", discord.ActivityType.custom),)
        assert sessions._is_user_playing_gw2(ctx) is False

    def test_true_when_playing_gw2(self, ctx):
        ctx.message.author.activities = (_activity("Spotify"), _activity("guild wars 2"))
        assert sessions._is_user_playing_gw2(ctx) is True


class TestAddDeathsFieldTruncation:
    def test_truncates_to_discord_field_limit(self):
        char_deaths = [
            {"name": f"Character Number {i:03d}", "profession": "Necromancer", "start": 0, "end": 5} for i in range(60)
        ]
        embed = discord.Embed()
        sessions._add_deaths_field(embed, char_deaths)

        value = embed.fields[0].value
        assert len(value) <= 1024
        assert value.rstrip("`").endswith("...")


class TestSessionCommandErrorPath:
    @pytest.mark.asyncio
    async def test_unexpected_error_deletes_progress_and_reports(self, ctx):
        rs_session = [{"acc_name": "A.1234", "start": {"date": "bad"}, "end": {"date": "bad"}}]
        progress = AsyncMock()
        err = ValueError("bad date")
        with (
            patch(f"{MODULE}.Gw2KeyDal") as mock_key_dal,
            patch(f"{MODULE}.Gw2ConfigsDal") as mock_configs,
            patch(f"{MODULE}.Gw2SessionsDal") as mock_sessions_dal,
            patch(f"{MODULE}.gw2_utils.send_progress_embed", new_callable=AsyncMock, return_value=progress),
            patch(f"{MODULE}.bot_utils.convert_str_to_datetime_short", side_effect=err),
            patch(f"{MODULE}.bot_utils.send_error_msg", new_callable=AsyncMock) as mock_error,
        ):
            mock_key_dal.return_value.get_api_key_by_user = AsyncMock(
                return_value=[{"key": "k", "server": "Anvil Rock", "permissions": "account"}]
            )
            mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])
            mock_sessions_dal.return_value.get_user_last_session = AsyncMock(return_value=rs_session)
            await sessions.session(ctx)

        progress.delete.assert_awaited_once()
        mock_error.assert_awaited_once_with(ctx, err)
        ctx.bot.log.error.assert_called_once()
