"""Comprehensive tests for the OnGuildJoin event cog."""

# Mock problematic imports before importing the module
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import discord
import pytest


sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.events.on_guild_join import OnGuildJoin, WelcomeMessageBuilder
from src.bot.constants import messages, variables


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.log = MagicMock()
    # Ensure log methods are not coroutines
    bot.log.error = MagicMock()
    bot.user = MagicMock()
    bot.user.name = "TestBot"
    bot.user.avatar = MagicMock()
    bot.user.avatar.url = "https://example.com/bot_avatar.png"
    bot.command_prefix = "!"
    bot.owner_id = 123456789
    bot.get_user = MagicMock()
    # Ensure add_cog doesn't return a coroutine
    bot.add_cog = AsyncMock(return_value=None)
    # Mock the event decorator to prevent coroutine issues
    bot.event = MagicMock(side_effect=lambda func: func)
    return bot


@pytest.fixture
def on_guild_join_cog(mock_bot):
    """Create an OnGuildJoin cog instance."""
    return OnGuildJoin(mock_bot)


@pytest.fixture
def welcome_message_builder():
    """Create a WelcomeMessageBuilder instance."""
    return WelcomeMessageBuilder()


@pytest.fixture
def mock_guild():
    """Create a mock guild instance."""
    guild = MagicMock()
    guild.id = 12345
    guild.name = "Test Server"
    guild.system_channel = MagicMock()
    return guild


@pytest.fixture
def mock_owner():
    """Create a mock bot owner."""
    owner = MagicMock()
    owner.avatar = MagicMock()
    owner.avatar.url = "https://example.com/owner_avatar.png"
    owner.__str__ = MagicMock(return_value="BotOwner#1234")
    return owner


class TestWelcomeMessageBuilder:
    """Test cases for WelcomeMessageBuilder class."""

    def test_build_welcome_message(self, welcome_message_builder):
        """Test building welcome message text."""
        bot_name = "TestBot"
        prefix = "!"
        games_included = "GW2, WoW"

        result = welcome_message_builder.build_welcome_message(bot_name, prefix, games_included)

        # Should use the message template with proper formatting
        expected = messages.GUILD_JOIN_BOT_MESSAGE.format(bot_name, prefix, games_included, prefix, prefix)
        assert result == expected

    def test_build_welcome_embed_with_avatar(self, welcome_message_builder, mock_bot):
        """Test building welcome embed with bot avatar."""
        test_message = "Welcome to the server!"

        result = welcome_message_builder.build_welcome_embed(mock_bot, test_message)

        # Verify embed properties
        assert isinstance(result, discord.Embed)
        assert result.color == discord.Color.green()
        assert result.description == test_message

        # Verify author was set
        assert result.author.name == f"TestBot v{variables.VERSION}"
        assert result.author.icon_url == mock_bot.user.avatar.url
        assert result.author.url == variables.BOT_WEBPAGE_URL

        # Verify thumbnail was set
        assert result.thumbnail.url == mock_bot.user.avatar.url

    def test_build_welcome_embed_without_avatar(self, welcome_message_builder, mock_bot):
        """Test building welcome embed without bot avatar."""
        mock_bot.user.avatar = None
        test_message = "Welcome to the server!"

        result = welcome_message_builder.build_welcome_embed(mock_bot, test_message)

        # Verify author was set without icon
        assert result.author.name == f"TestBot v{variables.VERSION}"
        assert result.author.icon_url is None
        assert result.author.url == variables.BOT_WEBPAGE_URL

        # Verify no thumbnail was set
        assert result.thumbnail.url is None

    def test_set_footer_with_owner_and_avatar(self, welcome_message_builder, mock_bot, mock_owner):
        """Test setting footer with owner information and avatar."""
        mock_bot.get_user.return_value = mock_owner
        embed = discord.Embed()

        welcome_message_builder._set_footer(embed, mock_bot)

        # Verify footer was set with owner info
        python_version = "Python {}.{}.{}".format(*sys.version_info[:3])
        expected_text = f"Developed by BotOwner#1234 | {python_version}"

        assert embed.footer.text == expected_text
        assert embed.footer.icon_url == mock_owner.avatar.url

    def test_set_footer_with_owner_no_avatar(self, welcome_message_builder, mock_bot, mock_owner):
        """Test setting footer with owner but no avatar."""
        mock_owner.avatar = None
        mock_bot.get_user.return_value = mock_owner
        embed = discord.Embed()

        welcome_message_builder._set_footer(embed, mock_bot)

        # Verify footer was set with fallback
        python_version = "Python {}.{}.{}".format(*sys.version_info[:3])
        expected_text = f"Developed by Bot Owner | {python_version}"

        assert embed.footer.text == expected_text

    def test_set_footer_no_owner(self, welcome_message_builder, mock_bot):
        """Test setting footer when owner is not found."""
        mock_bot.get_user.return_value = None
        embed = discord.Embed()

        welcome_message_builder._set_footer(embed, mock_bot)

        # Verify footer was set with fallback
        python_version = "Python {}.{}.{}".format(*sys.version_info[:3])
        expected_text = f"Developed by Bot Owner | {python_version}"

        assert embed.footer.text == expected_text

    def test_set_footer_exception(self, welcome_message_builder, mock_bot):
        """Test setting footer when exception occurs."""
        mock_bot.get_user.side_effect = Exception("User fetch error")
        embed = discord.Embed()

        welcome_message_builder._set_footer(embed, mock_bot)

        # Verify footer was set with exception fallback
        python_version = "Python {}.{}.{}".format(*sys.version_info[:3])
        expected_text = f"Discord Bot | {python_version}"

        assert embed.footer.text == expected_text


class TestOnGuildJoin:
    """Test cases for OnGuildJoin cog."""

    def test_init(self, mock_bot):
        """Test OnGuildJoin cog initialization."""
        cog = OnGuildJoin(mock_bot)
        assert cog.bot == mock_bot
        assert isinstance(cog.message_builder, WelcomeMessageBuilder)

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_guild_join import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnGuildJoin)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.insert_server')
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.send_msg_to_system_channel')
    @patch('src.bot.cogs.events.on_guild_join.variables.GAMES_INCLUDED', ['GW2', 'WoW'])
    async def test_on_guild_join_success(self, mock_send_msg, mock_insert_server, mock_bot, mock_guild):
        """Test successful guild join handling."""
        OnGuildJoin(mock_bot)

        # Access the event handler directly
        on_guild_join_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_join_event(mock_guild)

        # Verify server was inserted
        mock_insert_server.assert_called_once_with(mock_bot, mock_guild)

        # Verify welcome message was sent
        mock_send_msg.assert_called_once()
        call_args = mock_send_msg.call_args[0]

        # Check arguments passed to send_msg_to_system_channel
        assert call_args[0] == mock_bot.log  # logger
        assert call_args[1] == mock_guild  # guild
        assert isinstance(call_args[2], discord.Embed)  # embed
        assert isinstance(call_args[3], str)  # message text

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.insert_server')
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.send_msg_to_system_channel')
    @patch('src.bot.cogs.events.on_guild_join.variables.GAMES_INCLUDED', ['GW2'])
    async def test_on_guild_join_with_games(self, mock_send_msg, mock_insert_server, mock_bot, mock_guild):
        """Test guild join with specific games included."""
        OnGuildJoin(mock_bot)

        # Access the event handler directly
        on_guild_join_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_join_event(mock_guild)

        # Verify the welcome message includes games
        call_args = mock_send_msg.call_args[0]
        welcome_text = call_args[3]

        # Should contain the games included
        assert "GW2" in welcome_text

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.insert_server')
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.send_msg_to_system_channel')
    async def test_on_guild_join_insert_server_error(self, mock_send_msg, mock_insert_server, mock_bot, mock_guild):
        """Test guild join when server insertion fails."""
        mock_insert_server.side_effect = Exception("Database error")
        OnGuildJoin(mock_bot)

        # Access the event handler directly
        on_guild_join_event = mock_bot.event.call_args_list[0][0][0]

        # Should raise exception since we're not handling it
        with pytest.raises(Exception, match="Database error"):
            await on_guild_join_event(mock_guild)

        # Insert should still have been attempted
        mock_insert_server.assert_called_once_with(mock_bot, mock_guild)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.insert_server')
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.send_msg_to_system_channel')
    async def test_on_guild_join_send_message_error(self, mock_send_msg, mock_insert_server, mock_bot, mock_guild):
        """Test guild join when sending message fails."""
        mock_send_msg.side_effect = Exception("Send error")
        OnGuildJoin(mock_bot)

        # Access the event handler directly
        on_guild_join_event = mock_bot.event.call_args_list[0][0][0]

        # Should raise exception since we're not handling it
        with pytest.raises(Exception, match="Send error"):
            await on_guild_join_event(mock_guild)

        # Both operations should have been attempted
        mock_insert_server.assert_called_once_with(mock_bot, mock_guild)
        mock_send_msg.assert_called_once()

    def test_on_guild_join_cog_inheritance(self, on_guild_join_cog):
        """Test that OnGuildJoin cog properly inherits from commands.Cog."""
        from discord.ext import commands

        assert isinstance(on_guild_join_cog, commands.Cog)
        assert hasattr(on_guild_join_cog, 'bot')

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.insert_server')
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.send_msg_to_system_channel')
    async def test_on_guild_join_embed_properties(self, mock_send_msg, mock_insert_server, mock_bot, mock_guild):
        """Test that the welcome embed has the correct properties."""
        OnGuildJoin(mock_bot)

        # Access the event handler directly
        on_guild_join_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_join_event(mock_guild)

        # Get the embed that was sent
        call_args = mock_send_msg.call_args[0]
        embed = call_args[2]

        # Verify embed properties
        assert isinstance(embed, discord.Embed)
        assert embed.color == discord.Color.green()
        assert embed.author.name == f"TestBot v{variables.VERSION}"
        assert embed.author.url == variables.BOT_WEBPAGE_URL

    def test_welcome_message_builder_static_methods(self):
        """Test that WelcomeMessageBuilder methods are static."""
        import inspect
        assert inspect.isfunction(WelcomeMessageBuilder.build_welcome_message)
        assert inspect.isfunction(WelcomeMessageBuilder.build_welcome_embed)
        assert inspect.isfunction(WelcomeMessageBuilder._set_footer)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.insert_server')
    @patch('src.bot.cogs.events.on_guild_join.bot_utils.send_msg_to_system_channel')
    @patch('src.bot.cogs.events.on_guild_join.variables.GAMES_INCLUDED', [])
    async def test_on_guild_join_no_games(self, mock_send_msg, mock_insert_server, mock_bot, mock_guild):
        """Test guild join with no games included."""
        OnGuildJoin(mock_bot)

        # Access the event handler directly
        on_guild_join_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_join_event(mock_guild)

        # Should still work with empty games list
        mock_insert_server.assert_called_once_with(mock_bot, mock_guild)
        mock_send_msg.assert_called_once()

    def test_build_welcome_message_formatting(self, welcome_message_builder):
        """Test welcome message formatting with various inputs."""
        # Test with special characters
        bot_name = "Test Bot #1"
        prefix = "$"
        games_included = "Game1, Game2"

        result = welcome_message_builder.build_welcome_message(bot_name, prefix, games_included)

        # Should handle special characters properly
        assert bot_name in result
        assert prefix in result
        assert games_included in result

    def test_build_welcome_embed_integration(self, welcome_message_builder, mock_bot, mock_owner):
        """Test complete integration of welcome embed building."""
        mock_bot.get_user.return_value = mock_owner
        test_message = "Complete integration test message"

        result = welcome_message_builder.build_welcome_embed(mock_bot, test_message)

        # Verify all components are present
        assert result.description == test_message
        assert result.author.name == f"TestBot v{variables.VERSION}"
        assert result.thumbnail.url == mock_bot.user.avatar.url
        assert "BotOwner#1234" in result.footer.text
        assert result.footer.icon_url == mock_owner.avatar.url
