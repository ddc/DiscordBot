"""Additional tests for bot_utils module to cover uncovered lines."""

import discord
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules["ddcDatabases"] = Mock()

from src.bot.tools import bot_utils


class TestSendHelpMsg:
    """Test send_help_msg function (lines 112-116)."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context for send_help_msg."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.help_command = MagicMock()
        ctx.author = MagicMock()
        ctx.author.send = AsyncMock()
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def mock_cmd(self):
        """Create a mock command with help text."""
        cmd = MagicMock()
        cmd.help = "This is the help text for the command."
        return cmd

    @pytest.mark.asyncio
    async def test_send_help_msg_dm_help_true(self, mock_ctx, mock_cmd):
        """Test send_help_msg sends to author DM when dm_help is True."""
        mock_ctx.bot.help_command.dm_help = True

        await bot_utils.send_help_msg(mock_ctx, mock_cmd)

        mock_ctx.author.send.assert_called_once_with("```This is the help text for the command.```")
        mock_ctx.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_help_msg_dm_help_false(self, mock_ctx, mock_cmd):
        """Test send_help_msg sends to channel when dm_help is False."""
        mock_ctx.bot.help_command.dm_help = False

        await bot_utils.send_help_msg(mock_ctx, mock_cmd)

        mock_ctx.send.assert_called_once_with("```This is the help text for the command.```")
        mock_ctx.author.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_help_msg_formats_with_box(self, mock_ctx, mock_cmd):
        """Test that send_help_msg wraps help text in code block formatting."""
        mock_ctx.bot.help_command.dm_help = False
        mock_cmd.help = "usage: !command <arg>"

        await bot_utils.send_help_msg(mock_ctx, mock_cmd)

        mock_ctx.send.assert_called_once_with("```usage: !command <arg>```")


class TestSendEmbed:
    """Test send_embed function (lines 119-144)."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context for send_embed."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.settings = {"bot": {"EmbedColor": discord.Color.blue()}}
        ctx.bot.logger = MagicMock()
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.author.display_avatar = MagicMock()
        ctx.message.author.display_avatar.url = "https://example.com/avatar.png"
        ctx.author = MagicMock()
        ctx.author.send = AsyncMock()
        ctx.author.display_name = "TestUser"
        ctx.author.avatar = MagicMock()
        ctx.author.avatar.url = "https://example.com/avatar.png"
        ctx.author.default_avatar = MagicMock()
        ctx.author.default_avatar.url = "https://example.com/default.png"
        ctx.send = AsyncMock()
        ctx.channel = MagicMock()  # Not a DMChannel by default
        return ctx

    @pytest.mark.asyncio
    async def test_send_embed_no_color_sets_from_settings(self, mock_ctx):
        """Test that embed with no color gets color from bot settings."""
        embed = discord.Embed(description="Test")
        # Embed starts with no color (None)
        assert embed.color is None

        await bot_utils.send_embed(mock_ctx, embed)

        assert embed.color == discord.Color.blue()

    @pytest.mark.asyncio
    async def test_send_embed_with_color_keeps_color(self, mock_ctx):
        """Test that embed with existing color keeps its color."""
        embed = discord.Embed(description="Test", color=discord.Color.red())

        await bot_utils.send_embed(mock_ctx, embed)

        assert embed.color == discord.Color.red()

    @pytest.mark.asyncio
    async def test_send_embed_no_author_sets_from_ctx(self, mock_ctx):
        """Test that embed with no author gets author from context."""
        embed = discord.Embed(description="Test", color=discord.Color.green())

        await bot_utils.send_embed(mock_ctx, embed)

        assert embed.author.name == "TestUser"
        assert embed.author.icon_url == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_send_embed_with_author_keeps_author(self, mock_ctx):
        """Test that embed with existing author keeps its author."""
        embed = discord.Embed(description="Test", color=discord.Color.green())
        embed.set_author(name="ExistingAuthor", icon_url="https://other.com/pic.png")

        await bot_utils.send_embed(mock_ctx, embed)

        # The author should not be overwritten since embed.author is truthy
        assert embed.author.name == "ExistingAuthor"

    @pytest.mark.asyncio
    async def test_send_embed_private_message(self, mock_ctx):
        """Test send_embed when in a private/DM channel."""
        mock_ctx.channel = MagicMock(spec=discord.DMChannel)
        embed = discord.Embed(description="DM content", color=discord.Color.green())

        await bot_utils.send_embed(mock_ctx, embed)

        mock_ctx.author.send.assert_called_once_with(embed=embed)
        mock_ctx.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_embed_dm_true(self, mock_ctx):
        """Test send_embed with dm=True sends to DM and notification to channel."""
        embed = discord.Embed(description="DM content", color=discord.Color.green())

        await bot_utils.send_embed(mock_ctx, embed, dm=True)

        # Should send embed to author DM
        mock_ctx.author.send.assert_called_once_with(embed=embed)

        # Should send notification embed to channel
        mock_ctx.send.assert_called_once()
        notification_call = mock_ctx.send.call_args
        notification_embed = notification_call[1]["embed"]
        assert isinstance(notification_embed, discord.Embed)
        assert notification_embed.color == discord.Color.green()
        assert "Response sent to your DM" in notification_embed.description

    @pytest.mark.asyncio
    async def test_send_embed_dm_true_notification_author_with_avatar(self, mock_ctx):
        """Test DM notification embed uses author avatar."""
        embed = discord.Embed(description="Test", color=discord.Color.green())

        await bot_utils.send_embed(mock_ctx, embed, dm=True)

        notification_call = mock_ctx.send.call_args
        notification_embed = notification_call[1]["embed"]
        assert notification_embed.author.name == "TestUser"
        assert notification_embed.author.icon_url == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_send_embed_dm_true_notification_author_no_avatar(self, mock_ctx):
        """Test DM notification embed uses default avatar when no avatar set."""
        mock_ctx.author.avatar = None
        embed = discord.Embed(description="Test", color=discord.Color.green())

        await bot_utils.send_embed(mock_ctx, embed, dm=True)

        notification_call = mock_ctx.send.call_args
        notification_embed = notification_call[1]["embed"]
        assert notification_embed.author.icon_url == "https://example.com/default.png"

    @pytest.mark.asyncio
    async def test_send_embed_normal_channel_send(self, mock_ctx):
        """Test send_embed sends to channel when not DM and dm=False."""
        embed = discord.Embed(description="Channel content", color=discord.Color.green())

        await bot_utils.send_embed(mock_ctx, embed, dm=False)

        mock_ctx.send.assert_called_once_with(embed=embed)
        mock_ctx.author.send.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.bot.tools.bot_utils.send_error_msg")
    async def test_send_embed_discord_forbidden_exception(self, mock_send_error, mock_ctx):
        """Test send_embed handles discord.Forbidden exception."""
        embed = discord.Embed(description="Test", color=discord.Color.green())
        mock_ctx.channel = MagicMock(spec=discord.DMChannel)
        mock_ctx.author.send.side_effect = discord.Forbidden(MagicMock(), "Cannot send messages")

        await bot_utils.send_embed(mock_ctx, embed)

        mock_send_error.assert_called_once()
        call_args = mock_send_error.call_args[0]
        assert call_args[0] == mock_ctx

    @pytest.mark.asyncio
    @patch("src.bot.tools.bot_utils.send_error_msg")
    async def test_send_embed_discord_http_exception(self, mock_send_error, mock_ctx):
        """Test send_embed handles discord.HTTPException."""
        embed = discord.Embed(description="Test", color=discord.Color.green())
        mock_ctx.send.side_effect = discord.HTTPException(MagicMock(), "HTTP error")

        await bot_utils.send_embed(mock_ctx, embed, dm=False)

        mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_embed_generic_exception(self, mock_ctx):
        """Test send_embed handles generic Exception."""
        embed = discord.Embed(description="Test", color=discord.Color.green())
        mock_ctx.send.side_effect = ValueError("Some unexpected error")

        await bot_utils.send_embed(mock_ctx, embed, dm=False)

        mock_ctx.bot.log.error.assert_called_once()
        error_arg = mock_ctx.bot.log.error.call_args[0][0]
        assert isinstance(error_arg, ValueError)
        assert str(error_arg) == "Some unexpected error"


class TestDeleteMessage:
    """Test delete_message function - specifically the warning=True path (lines 159-160)."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context for delete_message."""
        ctx = MagicMock()
        ctx.message = MagicMock()
        ctx.message.delete = AsyncMock()
        ctx.channel = MagicMock()  # Not a DMChannel
        ctx.bot = MagicMock()
        ctx.bot.settings = {"bot": {"EmbedColor": discord.Color.blue()}}
        ctx.bot.log = MagicMock()
        ctx.send = AsyncMock()
        ctx.message.author = MagicMock()
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        return ctx

    @pytest.mark.asyncio
    @patch("src.bot.tools.bot_utils.send_msg")
    async def test_delete_message_warning_true_success(self, mock_send_msg, mock_ctx):
        """Test delete_message with warning=True sends privacy message after successful delete."""
        await bot_utils.delete_message(mock_ctx, warning=True)

        mock_ctx.message.delete.assert_called_once()
        mock_send_msg.assert_called_once()
        call_args = mock_send_msg.call_args[0]
        assert call_args[0] == mock_ctx
        # msg should be MESSAGE_REMOVED_FOR_PRIVACY
        from src.bot.constants import messages

        assert call_args[1] == messages.MESSAGE_REMOVED_FOR_PRIVACY
        assert call_args[2] is False  # dm=False
        assert call_args[3] is None  # color=None (no error)

    @pytest.mark.asyncio
    @patch("src.bot.tools.bot_utils.send_msg")
    async def test_delete_message_warning_true_delete_fails(self, mock_send_msg, mock_ctx):
        """Test delete_message with warning=True sends error message when delete fails."""
        mock_ctx.message.delete.side_effect = discord.Forbidden(MagicMock(), "No permission")

        await bot_utils.delete_message(mock_ctx, warning=True)

        mock_send_msg.assert_called_once()
        call_args = mock_send_msg.call_args[0]
        assert call_args[0] == mock_ctx
        from src.bot.constants import messages

        assert call_args[1] == messages.DELETE_MESSAGE_NO_PERMISSION
        assert call_args[2] is False  # dm=False
        assert call_args[3] == discord.Color.red()  # color=red for error

    @pytest.mark.asyncio
    @patch("src.bot.tools.bot_utils.send_msg")
    async def test_delete_message_warning_false_success(self, mock_send_msg, mock_ctx):
        """Test delete_message with warning=False does not send message after successful delete."""
        await bot_utils.delete_message(mock_ctx, warning=False)

        mock_ctx.message.delete.assert_called_once()
        mock_send_msg.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.bot.tools.bot_utils.send_msg")
    async def test_delete_message_warning_false_delete_fails(self, mock_send_msg, mock_ctx):
        """Test delete_message with warning=False does not send message even when delete fails."""
        mock_ctx.message.delete.side_effect = Exception("Delete failed")

        await bot_utils.delete_message(mock_ctx, warning=False)

        mock_send_msg.assert_not_called()
        mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.tools.bot_utils.send_msg")
    async def test_delete_message_private_message_no_action(self, mock_send_msg):
        """Test delete_message does nothing for private messages."""
        ctx = MagicMock()
        ctx.channel = MagicMock(spec=discord.DMChannel)
        ctx.message = MagicMock()
        ctx.message.delete = AsyncMock()

        await bot_utils.delete_message(ctx, warning=True)

        ctx.message.delete.assert_not_called()
        mock_send_msg.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.bot.tools.bot_utils.send_msg")
    async def test_delete_message_warning_true_logs_error_on_failure(self, mock_send_msg, mock_ctx):
        """Test delete_message logs error when delete fails."""
        mock_ctx.message.delete.side_effect = Exception("Permission denied")

        await bot_utils.delete_message(mock_ctx, warning=True)

        mock_ctx.bot.log.error.assert_called_once()
        error_msg = mock_ctx.bot.log.error.call_args[0][0]
        assert "Permission denied" in error_msg


class TestGetServerSystemChannel:
    """Test get_server_system_channel function (lines 241-255)."""

    def test_returns_system_channel_if_exists(self):
        """Test that system_channel is returned when set."""
        server = MagicMock()
        system_channel = MagicMock(spec=discord.TextChannel)
        server.system_channel = system_channel

        result = bot_utils.get_server_system_channel(server)

        assert result is system_channel

    def test_no_system_channel_finds_readable_channel(self):
        """Test that first readable text channel is returned when no system_channel."""
        server = MagicMock()
        server.system_channel = None

        # Create channels with overwrites
        channel1 = MagicMock()
        channel1.position = 0

        everyone_role = MagicMock()
        everyone_role.name = "@everyone"

        permissions = MagicMock()
        permissions.read_messages = True

        channel1.overwrites = {everyone_role: permissions}

        server.text_channels = [channel1]

        result = bot_utils.get_server_system_channel(server)

        assert result is channel1

    def test_no_system_channel_permissions_none_is_readable(self):
        """Test that read_messages=None is treated as readable."""
        server = MagicMock()
        server.system_channel = None

        channel = MagicMock()
        channel.position = 0

        everyone_role = MagicMock()
        everyone_role.name = "@everyone"

        permissions = MagicMock()
        permissions.read_messages = None  # None means not explicitly denied

        channel.overwrites = {everyone_role: permissions}

        server.text_channels = [channel]

        result = bot_utils.get_server_system_channel(server)

        assert result is channel

    def test_no_system_channel_read_messages_false_not_returned(self):
        """Test that channel with read_messages=False is not returned."""
        server = MagicMock()
        server.system_channel = None

        channel = MagicMock()
        channel.position = 0

        everyone_role = MagicMock()
        everyone_role.name = "@everyone"

        permissions = MagicMock()
        permissions.read_messages = False

        channel.overwrites = {everyone_role: permissions}

        server.text_channels = [channel]

        result = bot_utils.get_server_system_channel(server)

        assert result is None

    def test_no_system_channel_no_overwrites_attribute(self):
        """Test that channels without overwrites attribute are skipped."""
        server = MagicMock()
        server.system_channel = None

        channel = MagicMock()
        channel.position = 0
        del channel.overwrites  # Remove overwrites attribute

        server.text_channels = [channel]

        result = bot_utils.get_server_system_channel(server)

        assert result is None

    def test_no_system_channel_returns_first_by_position(self):
        """Test that channels are sorted by position and first readable is returned."""
        server = MagicMock()
        server.system_channel = None

        everyone_role = MagicMock()
        everyone_role.name = "@everyone"

        # Channel at position 2 (should be second)
        channel_high = MagicMock()
        channel_high.position = 2
        permissions_high = MagicMock()
        permissions_high.read_messages = True
        channel_high.overwrites = {everyone_role: permissions_high}

        # Channel at position 0 (should be first)
        channel_low = MagicMock()
        channel_low.position = 0
        permissions_low = MagicMock()
        permissions_low.read_messages = True
        channel_low.overwrites = {everyone_role: permissions_low}

        # Put them in reverse order to test sorting
        server.text_channels = [channel_high, channel_low]

        result = bot_utils.get_server_system_channel(server)

        assert result is channel_low

    def test_no_system_channel_no_text_channels(self):
        """Test returns None when no text channels exist."""
        server = MagicMock()
        server.system_channel = None
        server.text_channels = []

        result = bot_utils.get_server_system_channel(server)

        assert result is None

    def test_no_system_channel_target_without_name_attribute(self):
        """Test that overwrites targets without name attribute are skipped."""
        server = MagicMock()
        server.system_channel = None

        channel = MagicMock()
        channel.position = 0

        # Target without name attribute (e.g., a Member without name)
        target_no_name = MagicMock()
        del target_no_name.name

        permissions = MagicMock()
        permissions.read_messages = True

        channel.overwrites = {target_no_name: permissions}

        server.text_channels = [channel]

        result = bot_utils.get_server_system_channel(server)

        assert result is None

    def test_no_system_channel_target_name_not_everyone(self):
        """Test that targets with name other than @everyone are skipped."""
        server = MagicMock()
        server.system_channel = None

        channel = MagicMock()
        channel.position = 0

        admin_role = MagicMock()
        admin_role.name = "Admin"

        permissions = MagicMock()
        permissions.read_messages = True

        channel.overwrites = {admin_role: permissions}

        server.text_channels = [channel]

        result = bot_utils.get_server_system_channel(server)

        assert result is None

    def test_no_system_channel_multiple_overwrites_with_everyone(self):
        """Test channel with multiple overwrites including @everyone."""
        server = MagicMock()
        server.system_channel = None

        channel = MagicMock()
        channel.position = 0

        admin_role = MagicMock()
        admin_role.name = "Admin"
        admin_permissions = MagicMock()
        admin_permissions.read_messages = True

        everyone_role = MagicMock()
        everyone_role.name = "@everyone"
        everyone_permissions = MagicMock()
        everyone_permissions.read_messages = True

        channel.overwrites = {admin_role: admin_permissions, everyone_role: everyone_permissions}

        server.text_channels = [channel]

        result = bot_utils.get_server_system_channel(server)

        assert result is channel

    def test_no_system_channel_skips_unreadable_finds_readable(self):
        """Test skips channel with denied read and finds readable one."""
        server = MagicMock()
        server.system_channel = None

        everyone_role = MagicMock()
        everyone_role.name = "@everyone"

        # Channel 1: read_messages=False (not readable)
        channel1 = MagicMock()
        channel1.position = 0
        perms1 = MagicMock()
        perms1.read_messages = False
        channel1.overwrites = {everyone_role: perms1}

        # Channel 2: read_messages=True (readable)
        channel2 = MagicMock()
        channel2.position = 1
        perms2 = MagicMock()
        perms2.read_messages = True
        channel2.overwrites = {everyone_role: perms2}

        server.text_channels = [channel1, channel2]

        result = bot_utils.get_server_system_channel(server)

        assert result is channel2
