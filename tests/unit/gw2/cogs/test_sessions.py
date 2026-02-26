"""Comprehensive tests for GW2 Sessions cog."""

import discord
import pytest
from datetime import datetime, timedelta
from src.gw2.cogs.sessions import (
    GW2Session,
    _add_deaths_field,
    _add_gold_field,
    _add_wallet_currency_fields,
    _add_wvw_stats,
    session,
    setup,
)
from src.gw2.constants import gw2_messages
from src.gw2.constants.gw2_currencies import WALLET_DISPLAY_NAMES
from src.gw2.constants.gw2_messages import GW2_FULL_NAME
from unittest.mock import AsyncMock, MagicMock, patch


class TestGW2Session:
    """Test cases for the GW2Session cog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def gw2_session_cog(self, mock_bot):
        """Create a GW2Session cog instance."""
        return GW2Session(mock_bot)

    def test_gw2_session_initialization(self, mock_bot):
        """Test GW2Session cog initialization."""
        cog = GW2Session(mock_bot)
        assert cog.bot == mock_bot

    def test_gw2_session_inheritance(self, gw2_session_cog):
        """Test that GW2Session inherits from GuildWars2 properly."""
        from src.gw2.cogs.gw2 import GuildWars2

        assert isinstance(gw2_session_cog, GuildWars2)


def _make_session_data(start_overrides=None, end_overrides=None):
    """Helper to create session data with defaults."""
    base_stats = {
        "date": "2024-01-15 10:00:00",
        "age": 5000000,
        "gold": 100000,
        "karma": 50000,
        "laurels": 100,
        "wvw_rank": 500,
        "yaks": 10,
        "yaks_scorted": 5,
        "players": 20,
        "keeps": 2,
        "towers": 5,
        "camps": 10,
        "castles": 1,
        "wvw_tickets": 100,
        "proof_heroics": 50,
        "badges_honor": 200,
        "guild_commendations": 30,
        "spirit_shards": 100,
        "transmutation_charges": 50,
        "volatile_magic": 1000,
        "unbound_magic": 500,
        "gems": 0,
    }
    end_stats = {
        "date": "2024-01-15 12:30:00",
        "age": 5009000,
        **{k: v for k, v in base_stats.items() if k not in ("date", "age")},
    }
    if start_overrides:
        base_stats.update(start_overrides)
    if end_overrides:
        end_stats.update(end_overrides)
    return [
        {
            "acc_name": "TestUser.1234",
            "start": base_stats,
            "end": end_stats,
            "created_at": datetime(2024, 1, 15, 10, 0, 0),
            "updated_at": datetime(2024, 1, 15, 12, 30, 0),
        }
    ]


class TestSessionCommand:
    """Test cases for the session command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.author.mention = "<@12345>"
        ctx.message.author.activities = ()
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = MagicMock()
        ctx.message.channel.typing.return_value.__aenter__ = AsyncMock(return_value=None)
        ctx.message.channel.typing.return_value.__aexit__ = AsyncMock(return_value=False)
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def sample_api_key_data(self):
        """Create sample API key data with all permissions."""
        return [
            {
                "key": "test-api-key-12345",
                "server": "Anvil Rock",
                "permissions": "account,characters,progression,wallet",
            }
        ]

    @pytest.fixture
    def sample_session_data(self):
        """Create sample session data with all stats changed."""
        return _make_session_data(
            end_overrides={
                "gold": 150000,
                "karma": 55000,
                "laurels": 105,
                "wvw_rank": 502,
                "yaks": 15,
                "yaks_scorted": 8,
                "players": 35,
                "keeps": 4,
                "towers": 8,
                "camps": 15,
                "castles": 2,
                "wvw_tickets": 120,
                "proof_heroics": 60,
                "badges_honor": 230,
                "guild_commendations": 35,
                "spirit_shards": 110,
                "volatile_magic": 1200,
            },
        )

    @pytest.fixture
    def sample_time_passed(self):
        """Create a sample TimeObject."""
        from src.gw2.tools.gw2_utils import TimeObject

        time_obj = TimeObject()
        time_obj.hours = 2
        time_obj.minutes = 30
        time_obj.seconds = 0
        time_obj.days = 0
        time_obj.timedelta = timedelta(hours=2, minutes=30)
        return time_obj

    def _run_session(self, mock_ctx, sample_api_key_data, session_data, sample_time_passed, extra_patches=None):
        """Helper that sets up all patches for a successful session command call.
        Returns a context manager dict with mock references."""
        import contextlib

        class SessionRunner:
            def __init__(self):
                self.mock_send = None
                self.mock_chars_dal = None
                self.mock_end_session = None

            @contextlib.asynccontextmanager
            async def run(self_runner):
                with (
                    patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal,
                    patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs,
                    patch("src.gw2.cogs.sessions.Gw2SessionsDal") as mock_sessions_dal,
                    patch("src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short", side_effect=lambda x: x),
                    patch("src.gw2.cogs.sessions.gw2_utils.get_time_passed", return_value=sample_time_passed),
                    patch("src.gw2.cogs.sessions.Gw2SessionCharDeathsDal") as mock_chars_dal_class,
                    patch("src.gw2.cogs.sessions.bot_utils.send_paginated_embed") as mock_send,
                    patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"),
                    patch(
                        "src.gw2.cogs.sessions.gw2_utils.send_progress_embed",
                        new_callable=AsyncMock,
                        return_value=AsyncMock(),
                    ),
                ):
                    mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
                    mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])
                    mock_sessions_dal.return_value.get_user_last_session = AsyncMock(return_value=session_data)
                    mock_chars_dal_class.return_value.get_char_deaths = AsyncMock(return_value=None)

                    self_runner.mock_send = mock_send
                    self_runner.mock_chars_dal = mock_chars_dal_class.return_value

                    yield self_runner

        return SessionRunner()

    # === Error path tests ===

    @pytest.mark.asyncio
    async def test_session_no_api_key(self, mock_ctx):
        """Test session command when user has no API key."""
        with patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal:
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=None)
            with patch("src.gw2.cogs.sessions.bot_utils.send_error_msg") as mock_error:
                await session(mock_ctx)
                mock_error.assert_called_once()
                assert gw2_messages.NO_API_KEY in mock_error.call_args[0][1]

    @pytest.mark.asyncio
    async def test_session_not_active_in_config(self, mock_ctx, sample_api_key_data):
        """Test session command when session is not active in server config."""
        with patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal:
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs:
                mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": False}])
                with patch("src.gw2.cogs.sessions.bot_utils.send_warning_msg") as mock_warning:
                    await session(mock_ctx)
                    mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_not_active_empty_config(self, mock_ctx, sample_api_key_data):
        """Test session command when server config is empty."""
        with patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal:
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs:
                mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[])
                with patch("src.gw2.cogs.sessions.bot_utils.send_warning_msg") as mock_warning:
                    await session(mock_ctx)
                    mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_missing_all_permissions(self, mock_ctx):
        """Test session command when all required permissions are missing."""
        api_key_no_perms = [{"key": "test-api-key", "server": "Anvil Rock", "permissions": "guilds,pvp"}]
        with patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal:
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_no_perms)
            with patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs:
                mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])
                with patch("src.gw2.cogs.sessions.bot_utils.send_error_msg") as mock_error:
                    await session(mock_ctx)
                    mock_error.assert_called_once()
                    assert "permissions" in mock_error.call_args[0][1].lower()

    @pytest.mark.asyncio
    async def test_session_has_some_permissions_not_all_missing(self, mock_ctx):
        """Test session command when some but not all permissions are present (should pass)."""
        api_key_some_perms = [{"key": "test-api-key", "server": "Anvil Rock", "permissions": "account,guilds"}]
        with patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal:
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_some_perms)
            with patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs:
                mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])
                with patch("src.gw2.cogs.sessions.Gw2SessionsDal") as mock_sessions_dal:
                    mock_sessions_dal.return_value.get_user_last_session = AsyncMock(return_value=None)
                    with patch("src.gw2.cogs.sessions.bot_utils.send_error_msg") as mock_error:
                        await session(mock_ctx)
                        mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_no_session_found(self, mock_ctx, sample_api_key_data):
        """Test session command when no session records are found."""
        with patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal:
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs:
                mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])
                with patch("src.gw2.cogs.sessions.Gw2SessionsDal") as mock_sessions_dal:
                    mock_sessions_dal.return_value.get_user_last_session = AsyncMock(return_value=None)
                    with patch("src.gw2.cogs.sessions.bot_utils.send_error_msg") as mock_error:
                        await session(mock_ctx)
                        mock_error.assert_called_once()
                        # Error sent to channel (not via DM)
                        assert len(mock_error.call_args[0]) == 2

    @pytest.mark.asyncio
    async def test_session_end_date_is_none_api_fails(self, mock_ctx, sample_api_key_data):
        """Test session command when session end is None, user not playing, and API fails to finalize."""
        session_data = [{"acc_name": "TestUser.1234", "start": {}, "end": None}]
        with patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal:
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs:
                mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])
                with patch("src.gw2.cogs.sessions.Gw2SessionsDal") as mock_sessions_dal:
                    # end_session is called but fails, so re-fetch still returns None end
                    mock_sessions_dal.return_value.get_user_last_session = AsyncMock(return_value=session_data)
                    with patch("src.gw2.cogs.sessions.gw2_utils.end_session", new_callable=AsyncMock):
                        with patch(
                            "src.gw2.cogs.sessions.gw2_utils.send_progress_embed",
                            new_callable=AsyncMock,
                            return_value=AsyncMock(),
                        ):
                            with patch("src.gw2.cogs.sessions.bot_utils.send_error_msg") as mock_error:
                                await session(mock_ctx)
                                mock_error.assert_called_once()
                                assert gw2_messages.SESSION_BOT_STILL_UPDATING in str(mock_error.call_args[0][1])

    @pytest.mark.asyncio
    async def test_session_end_date_is_none_auto_completes(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command auto-completes when end is None and user stopped playing."""
        start_data = {"date": "2024-01-15 10:00:00", "gold": 100000, "wvw_rank": 100}
        end_data = {"date": "2024-01-15 12:30:00", "gold": 120000, "wvw_rank": 101}
        session_no_end = [{"acc_name": "TestUser.1234", "start": start_data, "end": None}]
        session_with_end = [{"acc_name": "TestUser.1234", "start": start_data, "end": end_data}]

        with (
            patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs,
            patch("src.gw2.cogs.sessions.Gw2SessionsDal") as mock_sessions_dal,
            patch("src.gw2.cogs.sessions.gw2_utils.end_session", new_callable=AsyncMock) as mock_end,
            patch(
                "src.gw2.cogs.sessions.gw2_utils.send_progress_embed",
                new_callable=AsyncMock,
                return_value=AsyncMock(),
            ),
            patch("src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short", side_effect=lambda x: x),
            patch("src.gw2.cogs.sessions.gw2_utils.get_time_passed", return_value=sample_time_passed),
            patch("src.gw2.cogs.sessions.Gw2SessionCharDeathsDal") as mock_chars_dal,
            patch("src.gw2.cogs.sessions.bot_utils.send_paginated_embed") as mock_send,
            patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"),
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])
            # First call returns no end, second call (after end_session) returns with end
            mock_sessions_dal.return_value.get_user_last_session = AsyncMock(
                side_effect=[session_no_end, session_with_end]
            )
            mock_chars_dal.return_value.get_char_deaths = AsyncMock(return_value=None)

            await session(mock_ctx)

            mock_end.assert_called_once()
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_end_date_is_none_while_playing_api_fails(self, mock_ctx, sample_api_key_data):
        """Test session command when end is None, playing, but API fails - shows SESSION_IN_PROGRESS."""
        session_data = [{"acc_name": "TestUser.1234", "start": {}, "end": None}]
        gw2_activity = MagicMock()
        gw2_activity.type = discord.ActivityType.playing
        gw2_activity.name = GW2_FULL_NAME
        mock_ctx.message.author.activities = (gw2_activity,)
        with patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal:
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs:
                mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])
                with patch("src.gw2.cogs.sessions.Gw2SessionsDal") as mock_sessions_dal:
                    mock_sessions_dal.return_value.get_user_last_session = AsyncMock(return_value=session_data)
                    with patch(
                        "src.gw2.cogs.sessions.gw2_utils.get_user_stats", new_callable=AsyncMock, return_value=None
                    ):
                        with patch(
                            "src.gw2.cogs.sessions.gw2_utils.send_progress_embed",
                            new_callable=AsyncMock,
                            return_value=AsyncMock(),
                        ):
                            with patch("src.gw2.cogs.sessions.gw2_utils.send_msg") as mock_send:
                                await session(mock_ctx)
                                mock_send.assert_called_once()
                                assert gw2_messages.SESSION_IN_PROGRESS in mock_send.call_args[0][1]

    @pytest.mark.asyncio
    async def test_session_live_snapshot_while_playing(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command shows live snapshot when user is playing and end is None."""
        start_data = {"date": "2024-01-15 10:00:00", "gold": 100000, "wvw_rank": 100}
        session_data = [{"acc_name": "TestUser.1234", "start": start_data, "end": None}]
        live_stats = {"acc_name": "TestUser.1234", "gold": 120000, "wvw_rank": 101}

        gw2_activity = MagicMock()
        gw2_activity.type = discord.ActivityType.playing
        gw2_activity.name = GW2_FULL_NAME
        mock_ctx.message.author.activities = (gw2_activity,)

        with (
            patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs,
            patch("src.gw2.cogs.sessions.Gw2SessionsDal") as mock_sessions_dal,
            patch("src.gw2.cogs.sessions.gw2_utils.get_user_stats", new_callable=AsyncMock, return_value=live_stats),
            patch("src.gw2.cogs.sessions.bot_utils.convert_datetime_to_str_short", return_value="2024-01-15 12:30:00"),
            patch("src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short", side_effect=lambda x: x),
            patch("src.gw2.cogs.sessions.gw2_utils.get_time_passed", return_value=sample_time_passed),
            patch("src.gw2.cogs.sessions.Gw2SessionCharDeathsDal"),
            patch("src.gw2.cogs.sessions._build_live_char_deaths", new_callable=AsyncMock, return_value=None),
            patch("src.gw2.cogs.sessions.bot_utils.send_paginated_embed") as mock_send,
            patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"),
            patch(
                "src.gw2.cogs.sessions.gw2_utils.send_progress_embed",
                new_callable=AsyncMock,
                return_value=AsyncMock(),
            ),
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])
            mock_sessions_dal.return_value.get_user_last_session = AsyncMock(return_value=session_data)

            await session(mock_ctx)

            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            assert "(Live)" in embed.author.name
            assert gw2_messages.SESSION_USER_STILL_PLAYING in embed.footer.text

    @pytest.mark.asyncio
    async def test_session_time_passed_less_than_one_minute(self, mock_ctx, sample_api_key_data):
        """Test session command when time passed is less than 1 minute."""
        session_data = _make_session_data()
        from src.gw2.tools.gw2_utils import TimeObject

        time_obj = TimeObject()
        time_obj.hours = 0
        time_obj.minutes = 0
        time_obj.seconds = 30

        with patch("src.gw2.cogs.sessions.Gw2KeyDal") as mock_dal:
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch("src.gw2.cogs.sessions.Gw2ConfigsDal") as mock_configs:
                mock_configs.return_value.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])
                with patch("src.gw2.cogs.sessions.Gw2SessionsDal") as mock_sessions_dal:
                    mock_sessions_dal.return_value.get_user_last_session = AsyncMock(return_value=session_data)
                    with patch(
                        "src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short", side_effect=lambda x: x
                    ):
                        with patch("src.gw2.cogs.sessions.gw2_utils.get_time_passed", return_value=time_obj):
                            with patch("src.gw2.cogs.sessions.gw2_utils.send_msg") as mock_send_msg:
                                await session(mock_ctx)
                                mock_send_msg.assert_called_once()
                                msg = mock_send_msg.call_args[0][1]
                                assert "still updating" in msg.lower() or "Bot still updating" in msg

    # === Playtime tests ===

    @pytest.mark.asyncio
    async def test_session_play_time_from_jsonb_dates(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test that play time uses JSONB date fields for session duration."""
        session_data = _make_session_data()
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            play_time_field = next((f for f in embed.fields if f.name == gw2_messages.PLAY_TIME), None)
            assert play_time_field is not None
            assert "2h 30m" in play_time_field.value

    # === Gold tests ===

    @pytest.mark.asyncio
    async def test_session_gold_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when gold is gained (positive)."""
        session_data = _make_session_data(end_overrides={"gold": 150000})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            with patch("src.gw2.cogs.sessions.gw2_utils.format_gold", return_value="5 Gold 00 Silver 00 Copper"):
                await session(mock_ctx)
                embed = r.mock_send.call_args[0][1]
                gold_field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["gold"]), None)
                assert gold_field is not None
                assert "+" in gold_field.value

    @pytest.mark.asyncio
    async def test_session_gold_lost(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when gold is lost (negative)."""
        session_data = _make_session_data(start_overrides={"gold": 150000}, end_overrides={"gold": 100000})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            with patch("src.gw2.cogs.sessions.gw2_utils.format_gold", return_value="5 Gold 00 Silver 00 Copper"):
                await session(mock_ctx)
                embed = r.mock_send.call_args[0][1]
                gold_field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["gold"]), None)
                assert gold_field is not None

    @pytest.mark.asyncio
    async def test_session_gold_lost_with_leading_dash(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when gold is lost and formatted gold starts with dash."""
        session_data = _make_session_data(start_overrides={"gold": 150000}, end_overrides={"gold": 100000})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            with patch("src.gw2.cogs.sessions.gw2_utils.format_gold", return_value="-5 Gold 00 Silver 00 Copper"):
                await session(mock_ctx)
                embed = r.mock_send.call_args[0][1]
                gold_field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["gold"]), None)
                assert gold_field is not None
                assert "--" not in gold_field.value

    # === Deaths tests ===

    @pytest.mark.asyncio
    async def test_session_characters_with_deaths(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command with character deaths."""
        session_data = _make_session_data()
        char_deaths = [
            {"name": "TestChar", "profession": "Warrior", "start": 10, "end": 15},
            {"name": "TestChar2", "profession": "Ranger", "start": 5, "end": 5},
        ]
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            r.mock_chars_dal.get_char_deaths = AsyncMock(return_value=char_deaths)
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            deaths_field = next((f for f in embed.fields if f.name == gw2_messages.TIMES_YOU_DIED), None)
            assert deaths_field is not None
            assert "Warrior" in deaths_field.value
            assert "TestChar" in deaths_field.value
            assert "Total: 5" in deaths_field.value

    @pytest.mark.asyncio
    async def test_session_no_deaths_when_unchanged(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command shows no deaths field when deaths unchanged."""
        session_data = _make_session_data()
        char_deaths = [{"name": "TestChar", "profession": "Warrior", "start": 10, "end": 10}]
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            r.mock_chars_dal.get_char_deaths = AsyncMock(return_value=char_deaths)
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            deaths_field = next((f for f in embed.fields if f.name == gw2_messages.TIMES_YOU_DIED), None)
            assert deaths_field is None

    @pytest.mark.asyncio
    async def test_session_multiple_character_deaths(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command with multiple characters dying."""
        session_data = _make_session_data()
        char_deaths = [
            {"name": "Char1", "profession": "Warrior", "start": 10, "end": 13},
            {"name": "Char2", "profession": "Mesmer", "start": 5, "end": 8},
        ]
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            r.mock_chars_dal.get_char_deaths = AsyncMock(return_value=char_deaths)
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            deaths_field = next((f for f in embed.fields if f.name == gw2_messages.TIMES_YOU_DIED), None)
            assert deaths_field is not None
            assert "Total: 6" in deaths_field.value
            assert "Warrior" in deaths_field.value
            assert "Mesmer" in deaths_field.value

    # === WvW stats tests ===

    @pytest.mark.asyncio
    async def test_session_wvw_rank_change(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when WvW rank changes."""
        session_data = _make_session_data(end_overrides={"wvw_rank": 502})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            wvw_field = next((f for f in embed.fields if f.name == gw2_messages.WVW_RANKS), None)
            assert wvw_field is not None
            assert "2" in wvw_field.value

    @pytest.mark.asyncio
    async def test_session_all_wvw_stats(self, mock_ctx, sample_api_key_data, sample_session_data, sample_time_passed):
        """Test session command with all WvW stats changed."""
        runner = self._run_session(mock_ctx, sample_api_key_data, sample_session_data, sample_time_passed)
        async with runner.run() as r:
            with patch("src.gw2.cogs.sessions.gw2_utils.format_gold", return_value="5 Gold"):
                await session(mock_ctx)
                embed = r.mock_send.call_args[0][1]
                field_names = [f.name for f in embed.fields]
                assert gw2_messages.YAKS_KILLED in field_names
                assert gw2_messages.YAKS_SCORTED in field_names
                assert gw2_messages.PLAYERS_KILLED in field_names
                assert gw2_messages.KEEPS_CAPTURED in field_names
                assert gw2_messages.TOWERS_CAPTURED in field_names
                assert gw2_messages.CAMPS_CAPTURED in field_names
                assert gw2_messages.SMC_CAPTURED in field_names

    # === Wallet currency tests ===

    @pytest.mark.asyncio
    async def test_session_karma_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when karma is gained."""
        session_data = _make_session_data(end_overrides={"karma": 55000})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["karma"]), None)
            assert field is not None
            assert "+5000" in field.value

    @pytest.mark.asyncio
    async def test_session_karma_lost(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when karma is lost."""
        session_data = _make_session_data(start_overrides={"karma": 55000}, end_overrides={"karma": 50000})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["karma"]), None)
            assert field is not None
            assert "-5000" in field.value

    @pytest.mark.asyncio
    async def test_session_laurels_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when laurels are gained."""
        session_data = _make_session_data(end_overrides={"laurels": 105})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["laurels"]), None)
            assert field is not None
            assert "+5" in field.value

    @pytest.mark.asyncio
    async def test_session_laurels_lost(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when laurels are lost."""
        session_data = _make_session_data(start_overrides={"laurels": 105}, end_overrides={"laurels": 100})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["laurels"]), None)
            assert field is not None
            assert "-5" in field.value

    @pytest.mark.asyncio
    async def test_session_wvw_tickets_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when WvW tickets are gained."""
        session_data = _make_session_data(end_overrides={"wvw_tickets": 120})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["wvw_tickets"]), None)
            assert field is not None
            assert "+20" in field.value

    @pytest.mark.asyncio
    async def test_session_wvw_tickets_lost(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when WvW tickets are lost."""
        session_data = _make_session_data(start_overrides={"wvw_tickets": 120}, end_overrides={"wvw_tickets": 100})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["wvw_tickets"]), None)
            assert field is not None
            assert "-20" in field.value

    @pytest.mark.asyncio
    async def test_session_proof_heroics_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when proof of heroics are gained."""
        session_data = _make_session_data(end_overrides={"proof_heroics": 60})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["proof_heroics"]), None)
            assert field is not None
            assert "+10" in field.value

    @pytest.mark.asyncio
    async def test_session_badges_honor_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when badges of honor are gained."""
        session_data = _make_session_data(end_overrides={"badges_honor": 230})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["badges_honor"]), None)
            assert field is not None
            assert "+30" in field.value

    @pytest.mark.asyncio
    async def test_session_guild_commendations_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when guild commendations are gained."""
        session_data = _make_session_data(end_overrides={"guild_commendations": 35})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["guild_commendations"]), None)
            assert field is not None
            assert "+5" in field.value

    # === New currency tests ===

    @pytest.mark.asyncio
    async def test_session_spirit_shards_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when spirit shards are gained."""
        session_data = _make_session_data(end_overrides={"spirit_shards": 110})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["spirit_shards"]), None)
            assert field is not None
            assert "+10" in field.value

    @pytest.mark.asyncio
    async def test_session_volatile_magic_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when volatile magic is gained."""
        session_data = _make_session_data(end_overrides={"volatile_magic": 1200})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["volatile_magic"]), None)
            assert field is not None
            assert "+200" in field.value

    @pytest.mark.asyncio
    async def test_session_unbound_magic_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when unbound magic is gained."""
        session_data = _make_session_data(end_overrides={"unbound_magic": 700})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["unbound_magic"]), None)
            assert field is not None
            assert "+200" in field.value

    @pytest.mark.asyncio
    async def test_session_transmutation_charges_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when transmutation charges are gained."""
        session_data = _make_session_data(end_overrides={"transmutation_charges": 55})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["transmutation_charges"]), None)
            assert field is not None
            assert "+5" in field.value

    @pytest.mark.asyncio
    async def test_session_currency_lost(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when a currency is lost (negative diff)."""
        session_data = _make_session_data(start_overrides={"spirit_shards": 110}, end_overrides={"spirit_shards": 100})
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["spirit_shards"]), None)
            assert field is not None
            assert "-10" in field.value

    @pytest.mark.asyncio
    async def test_session_no_currency_field_when_unchanged(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test that no currency field is added when values are unchanged."""
        session_data = _make_session_data()  # All values same between start/end
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            field_names = [f.name for f in embed.fields]
            # Only basic fields should be present
            assert gw2_messages.ACCOUNT_NAME in field_names
            assert gw2_messages.SERVER in field_names
            assert gw2_messages.PLAY_TIME in field_names
            # Only the 3 basic fields should be present (no currency/gold fields)
            assert len(field_names) == 3

    # === Stale data tests (missing keys) ===

    @pytest.mark.asyncio
    async def test_session_gold_not_shown_when_missing_from_start(
        self, mock_ctx, sample_api_key_data, sample_time_passed
    ):
        """Test that gold is not shown when the key is missing from start data."""
        session_data = _make_session_data(end_overrides={"gold": 150000})
        del session_data[0]["start"]["gold"]
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            gold_fields = [f for f in embed.fields if WALLET_DISPLAY_NAMES["gold"] in f.name]
            assert len(gold_fields) == 0

    @pytest.mark.asyncio
    async def test_session_currency_not_shown_when_missing_from_start(
        self, mock_ctx, sample_api_key_data, sample_time_passed
    ):
        """Test that a currency is skipped when the key is missing from start data."""
        session_data = _make_session_data(end_overrides={"karma": 55000})
        del session_data[0]["start"]["karma"]
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            karma_fields = [f for f in embed.fields if WALLET_DISPLAY_NAMES["karma"] in f.name]
            assert len(karma_fields) == 0

    @pytest.mark.asyncio
    async def test_session_wvw_stat_not_shown_when_missing_from_start(
        self, mock_ctx, sample_api_key_data, sample_time_passed
    ):
        """Test that WvW stats are skipped when the key is missing from start data."""
        session_data = _make_session_data(end_overrides={"yaks": 15})
        del session_data[0]["start"]["yaks"]
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            embed = r.mock_send.call_args[0][1]
            yaks_fields = [f for f in embed.fields if gw2_messages.YAKS_KILLED in f.name]
            assert len(yaks_fields) == 0

    # === Still playing / DM tests ===

    @pytest.mark.asyncio
    async def test_session_still_playing_gw2(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when user is still playing GW2 (completed session exists)."""
        session_data = _make_session_data()
        gw2_activity = MagicMock()
        gw2_activity.type = discord.ActivityType.playing
        gw2_activity.name = GW2_FULL_NAME
        mock_ctx.message.author.activities = (gw2_activity,)
        mock_ctx.channel = MagicMock(spec=discord.TextChannel)

        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            with patch("src.gw2.cogs.sessions.gw2_utils.end_session", new_callable=AsyncMock) as mock_end_session:
                await session(mock_ctx)
                mock_end_session.assert_called_once()
                mock_ctx.send.assert_called_once()
                assert "playing Guild Wars 2" in mock_ctx.send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_session_not_playing_gw2_no_activity(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when user has no activity (not playing)."""
        session_data = _make_session_data()
        mock_ctx.message.author.activities = ()

        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            with patch("src.gw2.cogs.sessions.gw2_utils.end_session", new_callable=AsyncMock) as mock_end_session:
                await session(mock_ctx)
                mock_end_session.assert_not_called()
                mock_ctx.send.assert_not_called()
                r.mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_dm_channel_no_still_playing(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command in DM channel does not trigger still playing message."""
        session_data = _make_session_data()
        mock_ctx.channel = MagicMock(spec=discord.DMChannel)
        gw2_activity = MagicMock()
        gw2_activity.type = discord.ActivityType.playing
        gw2_activity.name = GW2_FULL_NAME
        mock_ctx.message.author.activities = (gw2_activity,)

        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            with patch("src.gw2.cogs.sessions.gw2_utils.end_session", new_callable=AsyncMock) as mock_end_session:
                await session(mock_ctx)
                mock_end_session.assert_not_called()
                r.mock_send.assert_called_once()

    # === Basic embed tests ===

    @pytest.mark.asyncio
    async def test_session_successful_embed_basic_fields(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command sends embed with basic fields."""
        session_data = _make_session_data()
        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, sample_time_passed)
        async with runner.run() as r:
            await session(mock_ctx)
            r.mock_send.assert_called_once()
            embed = r.mock_send.call_args[0][1]
            field_names = [f.name for f in embed.fields]
            assert gw2_messages.ACCOUNT_NAME in field_names
            assert gw2_messages.SERVER in field_names
            assert gw2_messages.PLAY_TIME in field_names

    @pytest.mark.asyncio
    async def test_session_time_passed_exactly_one_minute(self, mock_ctx, sample_api_key_data):
        """Test session command when time passed is exactly 1 minute (should proceed)."""
        session_data = _make_session_data()
        from src.gw2.tools.gw2_utils import TimeObject

        time_obj = TimeObject()
        time_obj.hours = 0
        time_obj.minutes = 1
        time_obj.seconds = 0
        time_obj.timedelta = timedelta(minutes=1)

        runner = self._run_session(mock_ctx, sample_api_key_data, session_data, time_obj)
        async with runner.run() as r:
            await session(mock_ctx)
            r.mock_send.assert_called_once()


class TestAddGoldField:
    """Test the _add_gold_field helper function."""

    def test_gold_gained(self):
        embed = discord.Embed()
        with patch("src.gw2.cogs.sessions.gw2_utils.format_gold", return_value="5 Gold"):
            with patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"):
                _add_gold_field(embed, {"gold": 100}, {"gold": 200})
                assert len(embed.fields) == 1
                assert embed.fields[0].name == WALLET_DISPLAY_NAMES["gold"]

    def test_gold_lost(self):
        embed = discord.Embed()
        with patch("src.gw2.cogs.sessions.gw2_utils.format_gold", return_value="5 Gold"):
            with patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"):
                _add_gold_field(embed, {"gold": 200}, {"gold": 100})
                assert len(embed.fields) == 1
                assert embed.fields[0].name == WALLET_DISPLAY_NAMES["gold"]

    def test_gold_unchanged(self):
        embed = discord.Embed()
        _add_gold_field(embed, {"gold": 100}, {"gold": 100})
        assert len(embed.fields) == 0

    def test_gold_missing_from_start(self):
        """Gold key missing from start — should not add any field."""
        embed = discord.Embed()
        _add_gold_field(embed, {}, {"gold": 200})
        assert len(embed.fields) == 0

    def test_gold_missing_from_end(self):
        """Gold key missing from end — should not add any field."""
        embed = discord.Embed()
        _add_gold_field(embed, {"gold": 100}, {})
        assert len(embed.fields) == 0

    def test_gold_missing_from_both(self):
        embed = discord.Embed()
        _add_gold_field(embed, {}, {})
        assert len(embed.fields) == 0


class TestAddDeathsField:
    """Test the _add_deaths_field helper function."""

    def test_deaths_changed(self):
        embed = discord.Embed()
        char_deaths = [{"name": "Char1", "profession": "Warrior", "start": 10, "end": 15}]
        with patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"):
            _add_deaths_field(embed, char_deaths)
            assert len(embed.fields) == 1
            assert embed.fields[0].name == gw2_messages.TIMES_YOU_DIED
            assert "Char1 (Warrior): 5" in embed.fields[0].value
            assert "Total: 5" in embed.fields[0].value

    def test_no_deaths(self):
        embed = discord.Embed()
        char_deaths = [{"name": "Char1", "profession": "Warrior", "start": 10, "end": 10}]
        _add_deaths_field(embed, char_deaths)
        assert len(embed.fields) == 0

    def test_end_deaths_none_skipped(self):
        embed = discord.Embed()
        char_deaths = [{"name": "Char1", "profession": "Warrior", "start": 10, "end": None}]
        _add_deaths_field(embed, char_deaths)
        assert len(embed.fields) == 0

    def test_multiple_characters_per_line_format(self):
        """Test that each character appears on its own line."""
        embed = discord.Embed()
        char_deaths = [
            {"name": "I Hadesz I", "profession": "Necromancer", "start": 10, "end": 11},
            {"name": "Hàdész", "profession": "Mesmer", "start": 5, "end": 7},
        ]
        with patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"):
            _add_deaths_field(embed, char_deaths)
            assert len(embed.fields) == 1
            assert embed.fields[0].name == gw2_messages.TIMES_YOU_DIED
            assert "I Hadesz I (Necromancer): 1" in embed.fields[0].value
            assert "Hàdész (Mesmer): 2" in embed.fields[0].value
            assert "Total: 3" in embed.fields[0].value


class TestAddWvwStats:
    """Test the _add_wvw_stats helper function."""

    def test_all_stats_changed(self):
        embed = discord.Embed()
        start = {
            "wvw_rank": 10,
            "yaks": 5,
            "yaks_scorted": 3,
            "players": 10,
            "keeps": 1,
            "towers": 2,
            "camps": 3,
            "castles": 0,
        }
        end = {
            "wvw_rank": 12,
            "yaks": 8,
            "yaks_scorted": 5,
            "players": 15,
            "keeps": 3,
            "towers": 4,
            "camps": 6,
            "castles": 1,
        }
        with patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"):
            _add_wvw_stats(embed, start, end)
            assert len(embed.fields) == 8
            # WvW stats should not have + sign (they can only increase)
            rank_field = next(f for f in embed.fields if f.name == gw2_messages.WVW_RANKS)
            assert rank_field.value == "`2`"
            yaks_field = next(f for f in embed.fields if f.name == gw2_messages.YAKS_KILLED)
            assert yaks_field.value == "`3`"

    def test_no_stats_changed(self):
        embed = discord.Embed()
        stats = {
            "wvw_rank": 10,
            "yaks": 5,
            "yaks_scorted": 3,
            "players": 10,
            "keeps": 1,
            "towers": 2,
            "camps": 3,
            "castles": 0,
        }
        _add_wvw_stats(embed, stats, stats)
        assert len(embed.fields) == 0

    def test_missing_keys_skipped(self):
        """Keys missing from start or end are skipped entirely."""
        embed = discord.Embed()
        _add_wvw_stats(embed, {}, {})
        assert len(embed.fields) == 0

    def test_key_missing_from_one_side(self):
        """A stat present only in end is skipped."""
        embed = discord.Embed()
        _add_wvw_stats(embed, {}, {"yaks": 5})
        assert len(embed.fields) == 0


class TestAddWalletCurrencyFields:
    """Test the _add_wallet_currency_fields helper function."""

    def test_currency_gained(self):
        embed = discord.Embed()
        start = {"karma": 100, "laurels": 10}
        end = {"karma": 200, "laurels": 15}
        with patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"):
            _add_wallet_currency_fields(embed, start, end)
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["karma"]), None)
            assert field is not None
            assert "+100" in field.value
            field2 = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["laurels"]), None)
            assert field2 is not None
            assert "+5" in field2.value

    def test_currency_lost(self):
        embed = discord.Embed()
        start = {"karma": 200}
        end = {"karma": 100}
        with patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"):
            _add_wallet_currency_fields(embed, start, end)
            field = next((f for f in embed.fields if f.name == WALLET_DISPLAY_NAMES["karma"]), None)
            assert field is not None
            assert "-100" in field.value

    def test_gold_is_skipped(self):
        embed = discord.Embed()
        start = {"gold": 100}
        end = {"gold": 200}
        _add_wallet_currency_fields(embed, start, end)
        assert len(embed.fields) == 0

    def test_no_change(self):
        embed = discord.Embed()
        start = {"karma": 100}
        end = {"karma": 100}
        _add_wallet_currency_fields(embed, start, end)
        assert len(embed.fields) == 0

    def test_gained_and_lost_separate_fields(self):
        embed = discord.Embed()
        start = {"karma": 100, "laurels": 50}
        end = {"karma": 200, "laurels": 30}
        with patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"):
            _add_wallet_currency_fields(embed, start, end)
            field_names = [f.name for f in embed.fields]
            assert WALLET_DISPLAY_NAMES["karma"] in field_names
            assert WALLET_DISPLAY_NAMES["laurels"] in field_names

    def test_currency_missing_from_start_skipped(self):
        """Currency key missing from start data — should not add any field."""
        embed = discord.Embed()
        _add_wallet_currency_fields(embed, {}, {"karma": 200})
        assert len(embed.fields) == 0

    def test_inline_fields(self):
        """Currency fields should be inline for compact display."""
        embed = discord.Embed()
        start = {"karma": 100}
        end = {"karma": 200}
        with patch("src.gw2.cogs.sessions.chat_formatting.inline", side_effect=lambda x: f"`{x}`"):
            _add_wallet_currency_fields(embed, start, end)
            assert embed.fields[0].inline is True


class TestSessionSetup:
    """Test cases for session cog setup."""

    @pytest.mark.asyncio
    async def test_setup_function_exists(self):
        """Test that setup function exists and is callable."""
        assert callable(setup)

    @pytest.mark.asyncio
    async def test_setup_removes_gw2_command(self):
        """Test that setup removes existing gw2 command."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()
        await setup(mock_bot)
        mock_bot.remove_command.assert_called_once_with("gw2")

    @pytest.mark.asyncio
    async def test_setup_adds_cog(self):
        """Test that setup adds the GW2Session cog."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()
        await setup(mock_bot)
        mock_bot.add_cog.assert_called_once()
        cog_instance = mock_bot.add_cog.call_args[0][0]
        assert isinstance(cog_instance, GW2Session)
