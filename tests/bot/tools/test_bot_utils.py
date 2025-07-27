"""Comprehensive tests for bot utilities module."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import discord
import pytest
from src.bot.tools import bot_utils


class TestColorsEnum:
    """Test Colors enum functionality."""

    def test_colors_enum_values(self):
        """Test that Colors enum has expected Discord color values."""
        colors = bot_utils.Colors

        # Test a few key colors
        assert colors.black.value == discord.Color.default()
        assert colors.red.value == discord.Color.red()
        assert colors.green.value == discord.Color.green()
        assert colors.blue.value == discord.Color.blue()
        assert colors.blurple.value == discord.Color.blurple()

    def test_colors_enum_completeness(self):
        """Test that all expected colors are defined."""
        colors = bot_utils.Colors
        expected_colors = [
            'black',
            'teal',
            'dark_teal',
            'green',
            'dark_green',
            'blue',
            'dark_blue',
            'purple',
            'dark_purple',
            'magenta',
            'dark_magenta',
            'gold',
            'dark_gold',
            'orange',
            'dark_orange',
            'red',
            'dark_red',
            'lighter_grey',
            'dark_grey',
            'light_grey',
            'darker_grey',
            'blurple',
            'greyple',
        ]

        for color_name in expected_colors:
            assert hasattr(colors, color_name)
            assert isinstance(getattr(colors, color_name).value, discord.Color)


class TestServerUtilities:
    """Test server-related utility functions."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot instance."""
        bot = AsyncMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def mock_server(self):
        """Create a mock Discord server/guild."""
        guild = MagicMock()
        guild.id = 12345
        guild.name = "Test Server"
        return guild

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.ServersDal')
    @patch('src.gw2.tools.gw2_utils.insert_gw2_server_configs')
    async def test_insert_server_success(self, mock_gw2_insert, mock_servers_dal, mock_bot, mock_server):
        """Test successful server insertion."""
        mock_dal = AsyncMock()
        mock_servers_dal.return_value = mock_dal
        mock_gw2_insert.return_value = None

        await bot_utils.insert_server(mock_bot, mock_server)

        # Verify DAL was created with correct parameters
        mock_servers_dal.assert_called_once_with(mock_bot.db_session, mock_bot.log)

        # Verify server insertion was called
        mock_dal.insert_server.assert_called_once_with(12345, "Test Server")

        # Verify GW2 configs were inserted
        mock_gw2_insert.assert_called_once_with(mock_bot, mock_server)

    @patch('src.bot.tools.bot_utils.BackgroundTasks')
    def test_init_background_tasks_enabled(self, mock_bg_tasks_class, mock_bot):
        """Test background task initialization when enabled."""
        mock_bot.settings = {"bot": {"BGActivityTimer": 30}}
        mock_bot.loop = MagicMock()
        mock_bg_tasks = MagicMock()
        mock_bg_tasks_class.return_value = mock_bg_tasks

        bot_utils.init_background_tasks(mock_bot)

        # Verify BackgroundTasks was created
        mock_bg_tasks_class.assert_called_once_with(mock_bot)

        # Verify task was created
        mock_bot.loop.create_task.assert_called_once()

    def test_init_background_tasks_disabled(self, mock_bot):
        """Test background task initialization when disabled."""
        test_cases = [
            {"bot": {"BGActivityTimer": 0}},
            {"bot": {"BGActivityTimer": None}},
            {"bot": {"BGActivityTimer": -1}},
        ]

        for settings in test_cases:
            mock_bot.reset_mock()
            mock_bot.settings = settings
            mock_bot.loop = MagicMock()

            bot_utils.init_background_tasks(mock_bot)

            # Verify no task was created
            mock_bot.loop.create_task.assert_not_called()


class TestCogLoading:
    """Test cog loading functionality."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot for cog loading."""
        bot = AsyncMock()
        bot.log = MagicMock()
        bot.load_extension = AsyncMock()
        return bot

    @pytest.mark.asyncio
    async def test_load_cogs_success(self, mock_bot):
        """Test successful cog loading."""
        with patch(
            'src.bot.tools.bot_utils.variables.ALL_COGS', ['src/bot/cogs/test_cog.py', 'src/bot/events/test_event.py']
        ):
            await bot_utils.load_cogs(mock_bot)

            # Verify extensions were loaded
            expected_extensions = ['src.bot.cogs.test_cog', 'src.bot.events.test_event']

            assert mock_bot.load_extension.call_count == 2
            actual_calls = [call[0][0] for call in mock_bot.load_extension.call_args_list]
            assert actual_calls == expected_extensions

            # Verify debug logging
            assert mock_bot.log.debug.call_count >= 2

    @pytest.mark.asyncio
    async def test_load_cogs_with_failure(self, mock_bot):
        """Test cog loading with some failures."""
        with patch(
            'src.bot.tools.bot_utils.variables.ALL_COGS',
            ['src/bot/cogs/working_cog.py', 'src/bot/cogs/broken_cog.py'],
        ):
            # Make second cog fail to load
            mock_bot.load_extension.side_effect = [None, Exception("Failed to load")]

            await bot_utils.load_cogs(mock_bot)

            # Verify both extensions were attempted
            assert mock_bot.load_extension.call_count == 2

            # Verify error was logged
            mock_bot.log.error.assert_called()
            error_calls = [call[0][0] for call in mock_bot.log.error.call_args_list]
            assert any("src.bot.cogs.broken_cog" in call for call in error_calls)


class TestCommandUtilities:
    """Test command-related utility functions."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.message = MagicMock()
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.invoked_subcommand = None
        ctx.command = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.get_command = MagicMock()
        return ctx

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.send_help_msg')
    async def test_invoke_subcommand_with_subcommand(self, mock_send_help, mock_ctx):
        """Test invoke_subcommand when subcommand exists."""
        mock_subcommand = MagicMock()
        mock_ctx.invoked_subcommand = mock_subcommand

        result = await bot_utils.invoke_subcommand(mock_ctx, "test")

        # Should return the subcommand and not send help
        assert result == mock_subcommand
        mock_send_help.assert_not_called()
        mock_ctx.message.channel.typing.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.send_help_msg')
    async def test_invoke_subcommand_without_subcommand(self, mock_send_help, mock_ctx):
        """Test invoke_subcommand when no subcommand exists."""
        mock_ctx.invoked_subcommand = None
        mock_ctx.command = MagicMock()

        result = await bot_utils.invoke_subcommand(mock_ctx, "test")

        # Should send help for the command
        assert result is None
        mock_send_help.assert_called_once_with(mock_ctx, mock_ctx.command)

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.send_help_msg')
    async def test_invoke_subcommand_no_command(self, mock_send_help, mock_ctx):
        """Test invoke_subcommand when no command exists."""
        mock_ctx.invoked_subcommand = None
        mock_ctx.command = None
        mock_bot_command = MagicMock()
        mock_ctx.bot.get_command.return_value = mock_bot_command

        result = await bot_utils.invoke_subcommand(mock_ctx, "testcommand")

        # Should get command from bot and send help
        assert result is None
        mock_ctx.bot.get_command.assert_called_once_with("testcommand")
        mock_send_help.assert_called_once_with(mock_ctx, mock_bot_command)


class TestEmbedUtilities:
    """Test embed-related utility functions."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context for embed functions."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.settings = {"bot": {"EmbedColor": discord.Color.blue()}}
        return ctx

    def test_get_embed_default(self, mock_ctx):
        """Test get_embed with default parameters."""
        embed = bot_utils.get_embed(mock_ctx)

        assert isinstance(embed, discord.Embed)
        assert embed.color == discord.Color.blue()
        assert embed.description is None

    def test_get_embed_with_description(self, mock_ctx):
        """Test get_embed with description."""
        embed = bot_utils.get_embed(mock_ctx, description="Test description")

        assert embed.description == "Test description"
        assert embed.color == discord.Color.blue()

    def test_get_embed_with_custom_color(self, mock_ctx):
        """Test get_embed with custom color."""
        custom_color = discord.Color.red()
        embed = bot_utils.get_embed(mock_ctx, color=custom_color)

        assert embed.color == custom_color
        assert embed.description is None

    def test_get_embed_with_all_parameters(self, mock_ctx):
        """Test get_embed with all parameters."""
        custom_color = discord.Color.green()
        embed = bot_utils.get_embed(mock_ctx, description="Test", color=custom_color)

        assert embed.description == "Test"
        assert embed.color == custom_color


class TestMessageUtilities:
    """Test message-related utility functions."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context for message functions."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.settings = {"bot": {"EmbedColor": discord.Color.blue()}}
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.send = AsyncMock()
        ctx.author = MagicMock()
        ctx.author.send = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.send_embed')
    async def test_send_msg_basic(self, mock_send_embed, mock_ctx):
        """Test basic send_msg functionality."""
        await bot_utils.send_msg(mock_ctx, "Test message")

        mock_send_embed.assert_called_once()
        call_args = mock_send_embed.call_args
        ctx_arg, embed_arg, dm_arg = call_args[0]

        assert ctx_arg == mock_ctx
        assert isinstance(embed_arg, discord.Embed)
        assert embed_arg.description == "Test message"
        assert dm_arg is False

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.send_embed')
    async def test_send_msg_dm(self, mock_send_embed, mock_ctx):
        """Test send_msg with DM enabled."""
        await bot_utils.send_msg(mock_ctx, "DM message", dm=True)

        call_args = mock_send_embed.call_args
        dm_arg = call_args[0][2]
        assert dm_arg is True

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.send_embed')
    async def test_send_warning_msg(self, mock_send_embed, mock_ctx):
        """Test send_warning_msg functionality."""
        await bot_utils.send_warning_msg(mock_ctx, "Warning message")

        call_args = mock_send_embed.call_args
        embed_arg = call_args[0][1]
        assert embed_arg.color == discord.Color.orange()

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.send_embed')
    async def test_send_info_msg(self, mock_send_embed, mock_ctx):
        """Test send_info_msg functionality."""
        await bot_utils.send_info_msg(mock_ctx, "Info message")

        call_args = mock_send_embed.call_args
        embed_arg = call_args[0][1]
        assert embed_arg.color == discord.Color.blue()

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.send_embed')
    async def test_send_error_msg(self, mock_send_embed, mock_ctx):
        """Test send_error_msg functionality."""
        await bot_utils.send_error_msg(mock_ctx, "Error message")

        call_args = mock_send_embed.call_args
        embed_arg = call_args[0][1]
        assert embed_arg.color == discord.Color.red()


class TestPermissionChecks:
    """Test permission checking functions."""

    def test_is_member_admin_true(self):
        """Test is_member_admin with admin member."""
        member = MagicMock()
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = True

        result = bot_utils.is_member_admin(member)
        assert result is True

    def test_is_member_admin_false(self):
        """Test is_member_admin with non-admin member."""
        member = MagicMock()
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = False

        result = bot_utils.is_member_admin(member)
        assert result is False

    def test_is_member_admin_none(self):
        """Test is_member_admin with None member."""
        result = bot_utils.is_member_admin(None)
        assert result is False

    def test_is_member_admin_no_permissions(self):
        """Test is_member_admin with member without guild_permissions."""
        member = MagicMock()
        del member.guild_permissions  # Remove the attribute

        result = bot_utils.is_member_admin(member)
        assert result is False

    def test_is_bot_owner_true(self):
        """Test is_bot_owner with bot owner."""
        ctx = MagicMock()
        ctx.bot.owner_id = 12345
        member = MagicMock()
        member.id = 12345

        result = bot_utils.is_bot_owner(ctx, member)
        assert result is True

    def test_is_bot_owner_false(self):
        """Test is_bot_owner with non-owner."""
        ctx = MagicMock()
        ctx.bot.owner_id = 12345
        member = MagicMock()
        member.id = 67890

        result = bot_utils.is_bot_owner(ctx, member)
        assert result is False

    def test_is_server_owner_true(self):
        """Test is_server_owner with server owner."""
        ctx = MagicMock()
        ctx.guild.owner_id = 12345
        member = MagicMock()
        member.id = 12345

        result = bot_utils.is_server_owner(ctx, member)
        assert result is True

    def test_is_server_owner_false(self):
        """Test is_server_owner with non-owner."""
        ctx = MagicMock()
        ctx.guild.owner_id = 12345
        member = MagicMock()
        member.id = 67890

        result = bot_utils.is_server_owner(ctx, member)
        assert result is False


class TestChannelUtilities:
    """Test channel-related utility functions."""

    def test_is_private_message_dm(self):
        """Test is_private_message with DM channel."""
        ctx = MagicMock()
        ctx.channel = MagicMock(spec=discord.DMChannel)

        result = bot_utils.is_private_message(ctx)
        assert result is True

    def test_is_private_message_guild(self):
        """Test is_private_message with guild channel."""
        ctx = MagicMock()
        ctx.channel = MagicMock()  # Not a DMChannel

        result = bot_utils.is_private_message(ctx)
        assert result is False


class TestDateTimeUtilities:
    """Test date and time utility functions."""

    @patch('src.bot.tools.bot_utils.datetime')
    def test_get_current_date_time(self, mock_datetime):
        """Test get_current_date_time function."""
        mock_now = MagicMock()
        mock_datetime.now.return_value = mock_now

        result = bot_utils.get_current_date_time()

        mock_datetime.now.assert_called_once_with(timezone.utc)
        assert result == mock_now

    @patch('src.bot.tools.bot_utils.get_current_date_time')
    @patch('src.bot.tools.bot_utils.convert_datetime_to_str_long')
    def test_get_current_date_time_str_long(self, mock_convert, mock_get_current):
        """Test get_current_date_time_str_long function."""
        mock_datetime = MagicMock()
        mock_get_current.return_value = mock_datetime
        mock_convert.return_value = "formatted_date"

        result = bot_utils.get_current_date_time_str_long()

        mock_get_current.assert_called_once()
        mock_convert.assert_called_once_with(mock_datetime)
        assert result == "formatted_date"

    @patch('src.bot.tools.bot_utils.variables.DATE_TIME_FORMATTER_STR', '%Y-%m-%d %H:%M:%S')
    def test_convert_datetime_to_str_long(self):
        """Test convert_datetime_to_str_long function."""
        test_date = datetime(2023, 1, 1, 12, 30, 45, tzinfo=timezone.utc)

        result = bot_utils.convert_datetime_to_str_long(test_date)

        assert result == "2023-01-01 12:30:45"

    @patch('src.bot.tools.bot_utils.variables.DATE_FORMATTER', '%Y-%m-%d')
    @patch('src.bot.tools.bot_utils.variables.TIME_FORMATTER', '%H:%M:%S')
    def test_convert_datetime_to_str_short(self):
        """Test convert_datetime_to_str_short function."""
        test_date = datetime(2023, 1, 1, 12, 30, 45, tzinfo=timezone.utc)

        result = bot_utils.convert_datetime_to_str_short(test_date)

        assert result == "2023-01-01 12:30:45"

    @patch('src.bot.tools.bot_utils.variables.DATE_FORMATTER', '%Y-%m-%d')
    @patch('src.bot.tools.bot_utils.variables.TIME_FORMATTER', '%H:%M:%S')
    def test_convert_str_to_datetime_short(self):
        """Test convert_str_to_datetime_short function."""
        date_string = "2023-01-01 12:30:45"

        result = bot_utils.convert_str_to_datetime_short(date_string)

        expected = datetime(2023, 1, 1, 12, 30, 45)
        assert result == expected


class TestMemberUtilities:
    """Test member lookup and utility functions."""

    def test_get_object_member_by_str_private_message(self):
        """Test get_object_member_by_str with private message."""
        ctx = MagicMock()
        ctx.channel = MagicMock(spec=discord.DMChannel)

        result = bot_utils.get_object_member_by_str(ctx, "TestUser")
        assert result is None

    def test_get_object_member_by_str_found_by_name(self):
        """Test get_object_member_by_str finding member by name."""
        ctx = MagicMock()
        ctx.channel = MagicMock()  # Not a DMChannel

        member1 = MagicMock()
        member1.name = "TestUser"
        member1.display_name = "Display"
        member1.nick = None

        member2 = MagicMock()
        member2.name = "OtherUser"
        member2.display_name = "Other"
        member2.nick = None

        ctx.guild.members = [member1, member2]

        result = bot_utils.get_object_member_by_str(ctx, "TestUser")
        assert result == member1

    def test_get_object_member_by_str_found_by_display_name(self):
        """Test get_object_member_by_str finding member by display name."""
        ctx = MagicMock()
        ctx.channel = MagicMock()

        member = MagicMock()
        member.name = "user123"
        member.display_name = "TestDisplay"
        member.nick = None

        ctx.guild.members = [member]

        result = bot_utils.get_object_member_by_str(ctx, "TestDisplay")
        assert result == member

    def test_get_object_member_by_str_found_by_nick(self):
        """Test get_object_member_by_str finding member by nickname."""
        ctx = MagicMock()
        ctx.channel = MagicMock()

        member = MagicMock()
        member.name = "user123"
        member.display_name = "Display"
        member.nick = "TestNick"

        ctx.guild.members = [member]

        result = bot_utils.get_object_member_by_str(ctx, "testnick")  # Case-insensitive
        assert result == member

    def test_get_object_member_by_str_not_found(self):
        """Test get_object_member_by_str when member not found."""
        ctx = MagicMock()
        ctx.channel = MagicMock()

        member = MagicMock()
        member.name = "DifferentUser"
        member.display_name = "Different"
        member.nick = None

        ctx.guild.members = [member]

        result = bot_utils.get_object_member_by_str(ctx, "NotFound")
        assert result is None

    def test_get_user_by_id(self):
        """Test get_user_by_id function."""
        bot = MagicMock()
        mock_user = MagicMock()
        bot.get_user.return_value = mock_user

        result = bot_utils.get_user_by_id(bot, 12345)

        bot.get_user.assert_called_once_with(12345)
        assert result == mock_user

    def test_get_member_by_id(self):
        """Test get_member_by_id function."""
        guild = MagicMock()
        mock_member = MagicMock()
        guild.get_member.return_value = mock_member

        result = bot_utils.get_member_by_id(guild, 67890)

        guild.get_member.assert_called_once_with(67890)
        assert result == mock_member


class TestSystemChannelUtilities:
    """Test system channel related utilities."""

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.get_server_system_channel')
    async def test_send_msg_to_system_channel_success(self, mock_get_channel):
        """Test send_msg_to_system_channel with successful send."""
        mock_log = MagicMock()
        mock_server = MagicMock()
        mock_embed = MagicMock()
        mock_channel = AsyncMock()
        mock_get_channel.return_value = mock_channel

        await bot_utils.send_msg_to_system_channel(mock_log, mock_server, mock_embed)

        mock_get_channel.assert_called_once_with(mock_server)
        mock_channel.send.assert_called_once_with(embed=mock_embed)
        mock_log.error.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.get_server_system_channel')
    async def test_send_msg_to_system_channel_no_channel(self, mock_get_channel):
        """Test send_msg_to_system_channel when no channel found."""
        mock_log = MagicMock()
        mock_server = MagicMock()
        mock_embed = MagicMock()
        mock_get_channel.return_value = None

        await bot_utils.send_msg_to_system_channel(mock_log, mock_server, mock_embed)

        mock_get_channel.assert_called_once_with(mock_server)
        mock_log.error.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.tools.bot_utils.get_server_system_channel')
    async def test_send_msg_to_system_channel_with_fallback(self, mock_get_channel):
        """Test send_msg_to_system_channel with fallback to plain message."""
        mock_log = MagicMock()
        mock_server = MagicMock()
        mock_embed = MagicMock()
        mock_channel = AsyncMock()
        mock_channel.send.side_effect = [discord.HTTPException(MagicMock(), "Embed failed"), None]
        mock_get_channel.return_value = mock_channel

        await bot_utils.send_msg_to_system_channel(mock_log, mock_server, mock_embed, "Plain message")

        assert mock_channel.send.call_count == 2
        # First call with embed, second with plain message
        mock_channel.send.assert_any_call(embed=mock_embed)
        mock_channel.send.assert_any_call("Plain message")
        mock_log.error.assert_called_once()


class TestColorSettings:
    """Test color settings functionality."""

    def test_get_color_settings_random(self):
        """Test get_color_settings with 'random'."""
        result = bot_utils.get_color_settings("random")

        assert isinstance(result, discord.Color)
        # Should be a valid color (value between 0 and 16777215)
        assert 0 <= result.value <= 16777215

    def test_get_color_settings_named_color(self):
        """Test get_color_settings with named color."""
        result = bot_utils.get_color_settings("red")

        assert result == discord.Color.red()

    def test_get_color_settings_case_insensitive(self):
        """Test get_color_settings is case-insensitive."""
        result1 = bot_utils.get_color_settings("RED")
        result2 = bot_utils.get_color_settings("red")
        result3 = bot_utils.get_color_settings("Red")

        assert result1 == result2 == result3 == discord.Color.red()

    def test_get_color_settings_invalid_color(self):
        """Test get_color_settings with invalid color."""
        result = bot_utils.get_color_settings("nonexistent")

        assert result is None

    @patch('random.SystemRandom')
    def test_get_color_settings_random_consistency(self, mock_system_random):
        """Test that random color generation is consistent."""
        mock_random = MagicMock()
        mock_random.choice.side_effect = ['A', 'B', 'C', 'D', 'E', 'F']
        mock_system_random.return_value = mock_random

        result = bot_utils.get_color_settings("random")

        # Should create a valid color
        assert isinstance(result, discord.Color)
        assert result.value == int("ABCDEF", 16)


class TestBotStats:
    """Test bot statistics functionality."""

    def test_get_bot_stats_basic(self):
        """Test get_bot_stats with basic bot setup."""
        bot = MagicMock()

        # Setup users
        user1 = MagicMock()
        user1.bot = False
        user2 = MagicMock()
        user2.bot = True
        user3 = MagicMock()
        user3.bot = False
        bot.users = [user1, user2, user3]

        # Setup guilds with channels
        guild = MagicMock()
        text_channel = MagicMock(spec=discord.TextChannel)
        voice_channel = MagicMock(spec=discord.VoiceChannel)
        guild.channels = [text_channel, voice_channel]
        bot.guilds = [guild]

        # Mock start_time
        mock_start_time = MagicMock()
        bot.start_time = mock_start_time

        result = bot_utils.get_bot_stats(bot)

        expected = {
            "servers": "1 servers",
            "users": "(2 users)(1 bots)[3 total]",
            "channels": "(1 text)(1 voice)[2 total]",
            "start_time": mock_start_time,
        }

        assert result == expected

    def test_get_bot_stats_no_start_time(self):
        """Test get_bot_stats when bot has no start_time."""
        bot = MagicMock()
        bot.users = []
        bot.guilds = []
        bot.start_time = None

        with patch('src.bot.tools.bot_utils.get_current_date_time') as mock_get_time:
            mock_current_time = MagicMock()
            mock_get_time.return_value = mock_current_time

            result = bot_utils.get_bot_stats(bot)

            assert result["start_time"] == mock_current_time

    def test_get_bot_stats_multiple_guilds(self):
        """Test get_bot_stats with multiple guilds."""
        bot = MagicMock()
        bot.users = []
        bot.start_time = MagicMock()

        # Guild 1: 2 text, 1 voice
        guild1 = MagicMock()
        guild1.channels = [
            MagicMock(spec=discord.TextChannel),
            MagicMock(spec=discord.TextChannel),
            MagicMock(spec=discord.VoiceChannel),
        ]

        # Guild 2: 1 text, 2 voice
        guild2 = MagicMock()
        guild2.channels = [
            MagicMock(spec=discord.TextChannel),
            MagicMock(spec=discord.VoiceChannel),
            MagicMock(spec=discord.VoiceChannel),
        ]

        bot.guilds = [guild1, guild2]

        result = bot_utils.get_bot_stats(bot)

        assert result["servers"] == "2 servers"
        assert result["channels"] == "(3 text)(3 voice)[6 total]"
