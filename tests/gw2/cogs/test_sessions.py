"""Comprehensive tests for GW2 Sessions cog."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
import discord
from discord.ext import commands

from src.gw2.cogs.sessions import GW2Session, session, setup


class TestGW2Session:
    """Test cases for the GW2Session cog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {
            "gw2": {
                "EmbedColor": 0x00ff00
            }
        }
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


class TestSessionCommand:
    """Test cases for the session command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {
            "gw2": {
                "EmbedColor": 0x00ff00
            }
        }
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.author.mention = "<@12345>"
        ctx.message.author.activity = None
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def sample_api_key_data(self):
        """Create sample API key data with all permissions."""
        return [{
            "key": "test-api-key-12345",
            "server": "Anvil Rock",
            "permissions": "account,characters,progression,wallet",
        }]

    @pytest.fixture
    def sample_session_data(self):
        """Create sample session data."""
        return [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
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
            },
            "end": {
                "date": "2024-01-15 12:30:00",
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
            },
        }]

    @pytest.fixture
    def sample_time_passed(self):
        """Create a sample TimeObject."""
        from src.gw2.tools.gw2_utils import TimeObject
        time_obj = TimeObject()
        time_obj.hours = 2
        time_obj.minutes = 30
        time_obj.seconds = 0
        time_obj.days = 0
        time_obj.timedelta = "2:30:00"
        return time_obj

    @pytest.mark.asyncio
    async def test_session_no_api_key(self, mock_ctx):
        """Test session command when user has no API key."""
        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=None)

            with patch('src.gw2.cogs.sessions.bot_utils.send_error_msg') as mock_error:
                await session(mock_ctx)

                mock_error.assert_called_once()
                error_msg = mock_error.call_args[0][1]
                assert "You dont have an API key registered" in error_msg

    @pytest.mark.asyncio
    async def test_session_not_active_in_config(self, mock_ctx, sample_api_key_data):
        """Test session command when session is not active in server config."""
        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": False}]
                )

                with patch('src.gw2.cogs.sessions.bot_utils.send_warning_msg') as mock_warning:
                    await session(mock_ctx)

                    mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_not_active_empty_config(self, mock_ctx, sample_api_key_data):
        """Test session command when server config is empty."""
        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(return_value=[])

                with patch('src.gw2.cogs.sessions.bot_utils.send_warning_msg') as mock_warning:
                    await session(mock_ctx)

                    mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_missing_all_permissions(self, mock_ctx):
        """Test session command when all required permissions are missing."""
        api_key_no_perms = [{
            "key": "test-api-key-12345",
            "server": "Anvil Rock",
            "permissions": "guilds,pvp",
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_no_perms)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.bot_utils.send_error_msg') as mock_error:
                    await session(mock_ctx)

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "permissions" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_session_has_some_permissions_not_all_missing(self, mock_ctx):
        """Test session command when some but not all permissions are present (should pass)."""
        api_key_some_perms = [{
            "key": "test-api-key-12345",
            "server": "Anvil Rock",
            "permissions": "account,guilds",  # Only account present, missing wallet/progression/characters
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_some_perms)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=None)

                    with patch('src.gw2.cogs.sessions.bot_utils.send_error_msg') as mock_error:
                        await session(mock_ctx)

                        # Should not error on permissions since at least one is present
                        # Should error on no session found instead
                        mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_no_session_found(self, mock_ctx, sample_api_key_data):
        """Test session command when no session records are found."""
        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=None)

                    with patch('src.gw2.cogs.sessions.bot_utils.send_error_msg') as mock_error:
                        await session(mock_ctx)

                        mock_error.assert_called_once()
                        # Second arg is the message, third is True for dm
                        assert mock_error.call_args[0][2] is True

    @pytest.mark.asyncio
    async def test_session_end_date_is_none(self, mock_ctx, sample_api_key_data):
        """Test session command when session end date is None."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {"date": "2024-01-15 10:00:00"},
            "end": {"date": None},
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.send_error_msg') as mock_error:
                        await session(mock_ctx)

                        mock_error.assert_called_once()
                        assert mock_error.call_args[0][2] is True

    @pytest.mark.asyncio
    async def test_session_time_passed_less_than_one_minute(self, mock_ctx, sample_api_key_data):
        """Test session command when time passed is less than 1 minute."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {"date": "2024-01-15 10:00:00"},
            "end": {"date": "2024-01-15 10:00:30"},
        }]

        from src.gw2.tools.gw2_utils import TimeObject
        time_obj = TimeObject()
        time_obj.hours = 0
        time_obj.minutes = 0
        time_obj.seconds = 30

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = time_obj

                            with patch('src.gw2.cogs.sessions.gw2_utils.send_msg') as mock_send_msg:
                                await session(mock_ctx)

                                mock_send_msg.assert_called_once()
                                msg = mock_send_msg.call_args[0][1]
                                assert "still updating" in msg.lower() or "Bot still updating" in msg

    @pytest.mark.asyncio
    async def test_session_gold_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when gold is gained (positive)."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000,
                "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 150000,  # Gained 50000
                "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.gw2_utils.format_gold') as mock_format:
                                mock_format.return_value = "5g 00s 00c"

                                with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                    mock_chars_instance = mock_chars_dal.return_value
                                    mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                    with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                        with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                            await session(mock_ctx)

                                            mock_send.assert_called_once()
                                            embed = mock_send.call_args[0][1]
                                            gold_field = next(
                                                (f for f in embed.fields if f.name == "Gained gold"), None
                                            )
                                            assert gold_field is not None
                                            assert "+" in gold_field.value

    @pytest.mark.asyncio
    async def test_session_gold_lost(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when gold is lost (negative)."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 150000,
                "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000,  # Lost 50000
                "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.gw2_utils.format_gold') as mock_format:
                                mock_format.return_value = "5g 00s 00c"

                                with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                    mock_chars_instance = mock_chars_dal.return_value
                                    mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                    with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                        with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                            await session(mock_ctx)

                                            mock_send.assert_called_once()
                                            embed = mock_send.call_args[0][1]
                                            gold_field = next(
                                                (f for f in embed.fields if f.name == "Lost gold"), None
                                            )
                                            assert gold_field is not None

    @pytest.mark.asyncio
    async def test_session_gold_lost_with_leading_dash(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when gold is lost and formatted gold starts with dash."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 150000,
                "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000,
                "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.gw2_utils.format_gold') as mock_format:
                                # Formatted gold already starts with dash
                                mock_format.return_value = "-5g 00s 00c"

                                with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                    mock_chars_instance = mock_chars_dal.return_value
                                    mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                    with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                        with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                            await session(mock_ctx)

                                            mock_send.assert_called_once()
                                            embed = mock_send.call_args[0][1]
                                            gold_field = next(
                                                (f for f in embed.fields if f.name == "Lost gold"), None
                                            )
                                            assert gold_field is not None
                                            # Should not have double dash
                                            assert "--" not in gold_field.value

    @pytest.mark.asyncio
    async def test_session_characters_with_deaths(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command with character deaths."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000,
                "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000,
                "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        chars_start = {
            "char1": {"name": "TestChar", "profession": "Warrior", "deaths": 10},
            "char2": {"name": "TestChar2", "profession": "Ranger", "deaths": 5},
        }
        chars_end = {
            "char1": {"name": "TestChar", "profession": "Warrior", "deaths": 15},
            "char2": {"name": "TestChar2", "profession": "Ranger", "deaths": 5},  # No change
        }

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=chars_start)
                                mock_chars_instance.get_all_end_characters = AsyncMock(return_value=chars_end)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        mock_send.assert_called_once()
                                        embed = mock_send.call_args[0][1]
                                        deaths_field = next(
                                            (f for f in embed.fields if f.name == "Times you died"), None
                                        )
                                        assert deaths_field is not None
                                        assert "Warrior" in deaths_field.value
                                        assert "TestChar" in deaths_field.value
                                        assert "Total:5" in deaths_field.value

    @pytest.mark.asyncio
    async def test_session_karma_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when karma is gained."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 55000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        embed = mock_send.call_args[0][1]
                                        karma_field = next(
                                            (f for f in embed.fields if f.name == "Gained karma"), None
                                        )
                                        assert karma_field is not None

    @pytest.mark.asyncio
    async def test_session_karma_lost(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when karma is lost."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 55000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        embed = mock_send.call_args[0][1]
                                        karma_field = next(
                                            (f for f in embed.fields if f.name == "Lost karma"), None
                                        )
                                        assert karma_field is not None

    @pytest.mark.asyncio
    async def test_session_laurels_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when laurels are gained."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 105, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        embed = mock_send.call_args[0][1]
                                        laurels_field = next(
                                            (f for f in embed.fields if f.name == "Gained laurels"), None
                                        )
                                        assert laurels_field is not None

    @pytest.mark.asyncio
    async def test_session_wvw_rank_change(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when WvW rank changes."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 502,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        embed = mock_send.call_args[0][1]
                                        wvw_rank_field = next(
                                            (f for f in embed.fields if f.name == "Gained wvw ranks"), None
                                        )
                                        assert wvw_rank_field is not None
                                        assert "2" in wvw_rank_field.value

    @pytest.mark.asyncio
    async def test_session_all_wvw_stats(self, mock_ctx, sample_api_key_data, sample_session_data, sample_time_passed):
        """Test session command with all WvW stats changed (yaks, players, keeps, towers, camps, castles)."""
        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=sample_session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.gw2_utils.format_gold') as mock_format:
                                mock_format.return_value = "5g 00s 00c"

                                with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                    mock_chars_instance = mock_chars_dal.return_value
                                    mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                    with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                        with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                            await session(mock_ctx)

                                            embed = mock_send.call_args[0][1]
                                            field_names = [f.name for f in embed.fields]
                                            assert "Yaks killed" in field_names
                                            assert "Yaks scorted" in field_names
                                            assert "Players killed" in field_names
                                            assert "Keeps captured" in field_names
                                            assert "Towers captured" in field_names
                                            assert "Camps captured" in field_names
                                            assert "SMC captured" in field_names

    @pytest.mark.asyncio
    async def test_session_wvw_tickets_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when WvW tickets are gained."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 120, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        embed = mock_send.call_args[0][1]
                                        tickets_field = next(
                                            (f for f in embed.fields if f.name == "Gained wvw tickets"), None
                                        )
                                        assert tickets_field is not None

    @pytest.mark.asyncio
    async def test_session_wvw_tickets_lost(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when WvW tickets are lost."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 120, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        embed = mock_send.call_args[0][1]
                                        tickets_field = next(
                                            (f for f in embed.fields if f.name == "Lost wvw tickets"), None
                                        )
                                        assert tickets_field is not None

    @pytest.mark.asyncio
    async def test_session_proof_heroics_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when proof of heroics are gained."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 60,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        embed = mock_send.call_args[0][1]
                                        heroics_field = next(
                                            (f for f in embed.fields if f.name == "Gained proof heroics"), None
                                        )
                                        assert heroics_field is not None

    @pytest.mark.asyncio
    async def test_session_badges_honor_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when badges of honor are gained."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 230, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        embed = mock_send.call_args[0][1]
                                        badges_field = next(
                                            (f for f in embed.fields if f.name == "Gained badges of honor"), None
                                        )
                                        assert badges_field is not None

    @pytest.mark.asyncio
    async def test_session_guild_commendations_gained(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when guild commendations are gained."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 35,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        embed = mock_send.call_args[0][1]
                                        commendations_field = next(
                                            (f for f in embed.fields if f.name == "Gained guild commendations"), None
                                        )
                                        assert commendations_field is not None

    @pytest.mark.asyncio
    async def test_session_still_playing_gw2(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when user is still playing GW2."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        # Set up activity
        mock_ctx.message.author.activity = MagicMock()
        mock_ctx.message.author.activity.name = "Guild Wars 2"
        mock_ctx.channel = MagicMock(spec=discord.TextChannel)  # Not a DMChannel

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.gw2_utils.end_session', new_callable=AsyncMock) as mock_end_session:
                                    with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                        with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                            await session(mock_ctx)

                                            mock_end_session.assert_called_once()
                                            mock_ctx.send.assert_called_once()
                                            still_playing_msg = mock_ctx.send.call_args[0][0]
                                            assert "playing Guild Wars 2" in still_playing_msg

    @pytest.mark.asyncio
    async def test_session_not_playing_gw2_no_activity(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when user has no activity (not playing)."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        mock_ctx.message.author.activity = None

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.gw2_utils.end_session', new_callable=AsyncMock) as mock_end_session:
                                    with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                        with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                            await session(mock_ctx)

                                            # end_session should NOT be called
                                            mock_end_session.assert_not_called()
                                            mock_ctx.send.assert_not_called()
                                            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_dm_channel_no_still_playing(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command in DM channel does not trigger still playing message."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        # Set channel to DMChannel
        mock_ctx.channel = MagicMock(spec=discord.DMChannel)
        mock_ctx.message.author.activity = MagicMock()
        mock_ctx.message.author.activity.name = "Guild Wars 2"

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.gw2_utils.end_session', new_callable=AsyncMock) as mock_end_session:
                                    with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                        with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                            await session(mock_ctx)

                                            # In DM channel, end_session should NOT be called
                                            mock_end_session.assert_not_called()
                                            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_successful_embed_basic_fields(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command sends embed with basic fields."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        mock_send.assert_called_once()
                                        embed = mock_send.call_args[0][1]
                                        field_names = [f.name for f in embed.fields]
                                        assert "Account Name" in field_names
                                        assert "Server" in field_names
                                        assert "Total played time" in field_names

    @pytest.mark.asyncio
    async def test_session_time_passed_exactly_one_minute(self, mock_ctx, sample_api_key_data):
        """Test session command when time passed is exactly 1 minute (should proceed)."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 10:01:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        from src.gw2.tools.gw2_utils import TimeObject
        time_obj = TimeObject()
        time_obj.hours = 0
        time_obj.minutes = 1
        time_obj.seconds = 0
        time_obj.timedelta = "0:01:00"

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = time_obj

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        # Should proceed normally since minutes >= 1
                                        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_laurels_lost(self, mock_ctx, sample_api_key_data, sample_time_passed):
        """Test session command when laurels are lost."""
        session_data = [{
            "acc_name": "TestUser.1234",
            "start": {
                "date": "2024-01-15 10:00:00",
                "gold": 100000, "karma": 50000, "laurels": 105, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
            "end": {
                "date": "2024-01-15 12:30:00",
                "gold": 100000, "karma": 50000, "laurels": 100, "wvw_rank": 500,
                "yaks": 10, "yaks_scorted": 5, "players": 20,
                "keeps": 2, "towers": 5, "camps": 10, "castles": 1,
                "wvw_tickets": 100, "proof_heroics": 50,
                "badges_honor": 200, "guild_commendations": 30,
            },
        }]

        with patch('src.gw2.cogs.sessions.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch('src.gw2.cogs.sessions.Gw2ConfigsDal') as mock_configs:
                mock_configs_instance = mock_configs.return_value
                mock_configs_instance.get_gw2_server_configs = AsyncMock(
                    return_value=[{"session": True}]
                )

                with patch('src.gw2.cogs.sessions.Gw2SessionsDal') as mock_sessions_dal:
                    mock_sessions_instance = mock_sessions_dal.return_value
                    mock_sessions_instance.get_user_last_session = AsyncMock(return_value=session_data)

                    with patch('src.gw2.cogs.sessions.bot_utils.convert_str_to_datetime_short') as mock_convert:
                        mock_convert.side_effect = lambda x: x

                        with patch('src.gw2.cogs.sessions.gw2_utils.get_time_passed') as mock_time:
                            mock_time.return_value = sample_time_passed

                            with patch('src.gw2.cogs.sessions.Gw2SessionCharsDal') as mock_chars_dal:
                                mock_chars_instance = mock_chars_dal.return_value
                                mock_chars_instance.get_all_start_characters = AsyncMock(return_value=None)

                                with patch('src.gw2.cogs.sessions.bot_utils.send_embed') as mock_send:
                                    with patch('src.gw2.cogs.sessions.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                                        await session(mock_ctx)

                                        embed = mock_send.call_args[0][1]
                                        laurels_field = next(
                                            (f for f in embed.fields if f.name == "Lost laurels"), None
                                        )
                                        assert laurels_field is not None


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
