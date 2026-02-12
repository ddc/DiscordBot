"""Comprehensive tests for the Admin cog."""

# Mock problematic imports before importing the module
import discord
import pytest
import sys
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.admin.admin import Admin
from src.bot.constants import messages


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.db_session = MagicMock()
    bot.log = MagicMock()
    bot.user = MagicMock()
    bot.user.display_name = "TestBot"
    bot.user.avatar = MagicMock()
    bot.user.avatar.url = "https://example.com/bot_avatar.png"
    bot.command_prefix = ("!",)
    bot.settings = {"bot": {"BGActivityTimer": 0}}
    return bot


@pytest.fixture
def admin_cog(mock_bot):
    """Create an Admin cog instance."""
    return Admin(mock_bot)


@pytest.fixture
def mock_ctx():
    """Create a mock context."""
    ctx = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    ctx.guild.name = "Test Server"
    ctx.guild.icon = MagicMock()
    ctx.guild.icon.url = "https://example.com/icon.png"

    author = MagicMock()
    author.id = 67890
    author.display_name = "TestUser"
    author.avatar = MagicMock()
    author.avatar.url = "https://example.com/avatar.png"

    ctx.author = author
    ctx.message = MagicMock()
    ctx.message.author = author
    ctx.message.channel = AsyncMock()
    ctx.invoked_subcommand = None
    ctx.prefix = "!"

    return ctx


class TestAdmin:
    """Test cases for Admin cog."""

    def test_init(self, mock_bot):
        """Test Admin cog initialization."""
        cog = Admin(mock_bot)
        assert cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.admin.bot_utils.invoke_subcommand')
    async def test_admin_group_command(self, mock_invoke, admin_cog, mock_ctx):
        """Test admin group command."""
        mock_invoke.return_value = "mock_command"

        result = await admin_cog.admin.callback(admin_cog, mock_ctx)

        mock_invoke.assert_called_once_with(mock_ctx, "admin")
        assert result == "mock_command"

    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.admin.bot_utils.send_embed')
    async def test_botgame_command_success(self, mock_send_embed, admin_cog, mock_ctx):
        """Test successful botgame command execution."""
        game = "Minecraft"

        await admin_cog.botgame.callback(admin_cog, mock_ctx, game=game)

        # Verify typing indicator
        mock_ctx.message.channel.typing.assert_called_once()

        # Verify bot presence change
        admin_cog.bot.change_presence.assert_called_once()
        activity_call = admin_cog.bot.change_presence.call_args[1]['activity']
        assert isinstance(activity_call, discord.Game)
        assert activity_call.name == f"{game} | !help"

        # Verify embed was sent
        assert mock_send_embed.call_count == 1  # No warning embed since BGActivityTimer is 0

        embed_call = mock_send_embed.call_args_list[0]
        embed = embed_call[0][1]
        assert messages.BOT_ANNOUNCE_PLAYING.format(game) in embed.description
        assert embed.author.name == "TestBot"
        assert embed.author.icon_url == "https://example.com/bot_avatar.png"

    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.admin.bot_utils.send_embed')
    async def test_botgame_command_with_bg_timer_warning(self, mock_send_embed, admin_cog, mock_ctx):
        """Test botgame command with background activity timer warning."""
        game = "Reading documentation"
        admin_cog.bot.settings["bot"]["BGActivityTimer"] = 300  # 5 minutes

        await admin_cog.botgame.callback(admin_cog, mock_ctx, game=game)

        # Verify both embeds were sent (success + warning)
        assert mock_send_embed.call_count == 2

        # Check success embed
        success_embed = mock_send_embed.call_args_list[0][0][1]
        assert messages.BOT_ANNOUNCE_PLAYING.format(game) in success_embed.description

        # Check warning embed
        warning_embed = mock_send_embed.call_args_list[1][0][1]
        assert messages.BG_TASK_WARNING.format(300) in warning_embed.description

        # Verify warning embed was sent with dm=False
        warning_call = mock_send_embed.call_args_list[1]
        assert len(warning_call[0]) == 3  # ctx, embed, dm
        assert warning_call[0][2] is False

    @pytest.mark.asyncio
    async def test_warn_about_bg_activity_timer_enabled(self, admin_cog, mock_ctx):
        """Test _warn_about_bg_activity_timer when timer is enabled."""
        admin_cog.bot.settings["bot"]["BGActivityTimer"] = 600

        with patch('src.bot.cogs.admin.admin.bot_utils.send_embed') as mock_send_embed:
            await admin_cog._warn_about_bg_activity_timer(mock_ctx)

            mock_send_embed.assert_called_once()
            embed = mock_send_embed.call_args[0][1]
            assert messages.BG_TASK_WARNING.format(600) in embed.description
            # Verify dm=False parameter
            assert mock_send_embed.call_args[0][2] is False

    @pytest.mark.asyncio
    async def test_warn_about_bg_activity_timer_disabled(self, admin_cog, mock_ctx):
        """Test _warn_about_bg_activity_timer when timer is disabled."""
        admin_cog.bot.settings["bot"]["BGActivityTimer"] = 0

        with patch('src.bot.cogs.admin.admin.bot_utils.send_embed') as mock_send_embed:
            await admin_cog._warn_about_bg_activity_timer(mock_ctx)

            mock_send_embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_warn_about_bg_activity_timer_none(self, admin_cog, mock_ctx):
        """Test _warn_about_bg_activity_timer when timer is None."""
        admin_cog.bot.settings["bot"]["BGActivityTimer"] = None

        with patch('src.bot.cogs.admin.admin.bot_utils.send_embed') as mock_send_embed:
            await admin_cog._warn_about_bg_activity_timer(mock_ctx)

            mock_send_embed.assert_not_called()

    def test_create_admin_embed(self, admin_cog):
        """Test _create_admin_embed static method."""
        description = "Test description"
        embed = admin_cog._create_admin_embed(description)

        assert isinstance(embed, discord.Embed)
        assert embed.description == description

    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.admin.bot_utils.send_embed')
    async def test_botgame_with_special_characters(self, mock_send_embed, admin_cog, mock_ctx):
        """Test botgame command with special characters in game name."""
        game = "Game with émojis 🎮 and spéciál chars!"

        await admin_cog.botgame.callback(admin_cog, mock_ctx, game=game)

        # Verify the game name is properly handled
        activity_call = admin_cog.bot.change_presence.call_args[1]['activity']
        expected_name = f"{game} | !help"
        assert activity_call.name == expected_name

        # Verify embed contains the game name
        embed = mock_send_embed.call_args[0][1]
        assert game in embed.description

    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.admin.bot_utils.send_embed')
    async def test_botgame_with_empty_game_name(self, mock_send_embed, admin_cog, mock_ctx):
        """Test botgame command with empty game name."""
        game = ""

        await admin_cog.botgame.callback(admin_cog, mock_ctx, game=game)

        # Even empty game name should work
        activity_call = admin_cog.bot.change_presence.call_args[1]['activity']
        assert activity_call.name == " | !help"

    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.admin.bot_utils.send_embed')
    async def test_botgame_with_no_bot_avatar(self, mock_send_embed, admin_cog, mock_ctx):
        """Test botgame command when bot has no avatar."""
        admin_cog.bot.user.avatar = None
        game = "Test Game"

        await admin_cog.botgame.callback(admin_cog, mock_ctx, game=game)

        embed = mock_send_embed.call_args[0][1]
        assert embed.author.icon_url is None
        assert embed.author.name == "TestBot"

    @pytest.mark.asyncio
    async def test_botgame_different_prefix(self, admin_cog, mock_ctx):
        """Test botgame command with different command prefix."""
        admin_cog.bot.command_prefix = ("$",)
        game = "Test Game"

        with patch('src.bot.cogs.admin.admin.bot_utils.send_embed'):
            await admin_cog.botgame.callback(admin_cog, mock_ctx, game=game)

            activity_call = admin_cog.bot.change_presence.call_args[1]['activity']
            assert activity_call.name == f"{game} | $help"

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.admin.admin import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, Admin)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.admin.bot_utils.send_embed')
    async def test_botgame_preserve_embed_formatting(self, mock_send_embed, admin_cog, mock_ctx):
        """Test that botgame preserves proper embed formatting."""
        game = "Markdown **test** `code`"

        await admin_cog.botgame.callback(admin_cog, mock_ctx, game=game)

        embed = mock_send_embed.call_args[0][1]
        # Should be wrapped in code block
        assert "```" in embed.description
        assert messages.BOT_ANNOUNCE_PLAYING.format(game) in embed.description

    def test_admin_cog_inheritance(self, admin_cog):
        """Test that Admin cog properly inherits from commands.Cog."""
        assert isinstance(admin_cog, commands.Cog)
        assert hasattr(admin_cog, 'bot')

    @pytest.mark.asyncio
    async def test_botgame_activity_type(self, admin_cog, mock_ctx):
        """Test that botgame creates the correct activity type."""
        game = "Test Activity"

        with patch('src.bot.cogs.admin.admin.bot_utils.send_embed'):
            await admin_cog.botgame.callback(admin_cog, mock_ctx, game=game)

            activity_call = admin_cog.bot.change_presence.call_args[1]['activity']
            assert isinstance(activity_call, discord.Game)
            assert activity_call.type == discord.ActivityType.playing
