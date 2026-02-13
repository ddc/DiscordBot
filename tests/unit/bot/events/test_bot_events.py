"""Comprehensive tests for bot event cogs: OnCommand, OnDisconnect,
OnGuildChannelCreate, OnGuildChannelDelete, OnGuildChannelUpdate,
OnGuildRemove, and OnPresenceUpdate."""

# Mock problematic imports before importing the modules
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.events.on_command import CommandLogger, OnCommand
from src.bot.cogs.events.on_disconnect import OnDisconnect
from src.bot.cogs.events.on_guild_channel_create import OnGuildChannelCreate
from src.bot.cogs.events.on_guild_channel_delete import OnGuildChannelDelete
from src.bot.cogs.events.on_guild_channel_update import OnGuildChannelUpdate
from src.bot.cogs.events.on_guild_remove import GuildCleanupHandler, OnGuildRemove
from src.bot.cogs.events.on_presence_update import OnPresenceUpdate
from src.bot.constants import messages


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.log = MagicMock()
    bot.log.error = MagicMock()
    bot.log.info = MagicMock()
    bot.log.warning = MagicMock()
    bot.db_session = MagicMock()
    bot.user = MagicMock()
    bot.user.name = "TestBot"
    bot.user.__str__ = MagicMock(return_value="TestBot#1234")
    bot.add_cog = AsyncMock(return_value=None)
    return bot


@pytest.fixture
def mock_ctx():
    """Create a mock command context."""
    ctx = MagicMock()
    ctx.command = MagicMock()
    ctx.command.name = "testcmd"
    ctx.invoked_subcommand = None
    ctx.prefix = "!"
    ctx.message = MagicMock()
    ctx.message.content = "!testcmd arg1 arg2"
    ctx.guild = MagicMock()
    ctx.guild.name = "Test Server"
    ctx.channel = MagicMock()
    ctx.channel.name = "general"
    ctx.author = MagicMock()
    ctx.author.__str__ = MagicMock(return_value="TestUser#5678")
    return ctx


@pytest.fixture
def mock_guild():
    """Create a mock guild instance."""
    guild = MagicMock()
    guild.id = 12345
    guild.name = "Test Server"
    return guild


# =============================================================================
# Tests for on_command.py - CommandLogger
# =============================================================================


class TestCommandLogger:
    """Test cases for CommandLogger class."""

    def test_init(self, mock_bot):
        """Test CommandLogger initialization."""
        logger = CommandLogger(mock_bot)
        assert logger.bot == mock_bot

    def test_log_command_execution_guild_with_prefix(self, mock_bot, mock_ctx):
        """Test logging command execution in a guild context with prefix."""
        logger = CommandLogger(mock_bot)

        logger.log_command_execution(mock_ctx)

        mock_bot.log.info.assert_called_once_with(
            "Command executed in 'Test Server#general' by TestUser#5678: testcmd arg1 arg2"
        )

    def test_log_command_execution_guild_with_subcommand(self, mock_bot, mock_ctx):
        """Test logging command execution in a guild context with subcommand."""
        logger = CommandLogger(mock_bot)
        mock_ctx.invoked_subcommand = MagicMock()
        mock_ctx.invoked_subcommand.name = "sub"
        mock_ctx.message.content = "!testcmd sub arg1"

        logger.log_command_execution(mock_ctx)

        mock_bot.log.info.assert_called_once_with(
            "Command executed in 'Test Server#general' by TestUser#5678: testcmd sub arg1"
        )

    def test_log_command_execution_guild_without_prefix(self, mock_bot, mock_ctx):
        """Test logging command execution when message does not start with prefix."""
        logger = CommandLogger(mock_bot)
        mock_ctx.prefix = None
        mock_ctx.message.content = "testcmd arg1 arg2"

        logger.log_command_execution(mock_ctx)

        # When prefix is None, the else branch uses command_parts
        mock_bot.log.info.assert_called_once_with("Command executed in 'Test Server#general' by TestUser#5678: testcmd")

    def test_log_command_execution_dm_context(self, mock_bot, mock_ctx):
        """Test logging command execution in DM context (no guild)."""
        logger = CommandLogger(mock_bot)
        mock_ctx.guild = None

        logger.log_command_execution(mock_ctx)

        mock_bot.log.info.assert_called_once_with("DM Command executed by TestUser#5678: testcmd arg1 arg2")

    def test_log_command_execution_dm_context_no_prefix(self, mock_bot, mock_ctx):
        """Test logging command execution in DM context without prefix."""
        logger = CommandLogger(mock_bot)
        mock_ctx.guild = None
        mock_ctx.prefix = None

        logger.log_command_execution(mock_ctx)

        mock_bot.log.info.assert_called_once_with("DM Command executed by TestUser#5678: testcmd")

    def test_log_command_execution_exception(self, mock_bot, mock_ctx):
        """Test logging command execution when an exception occurs."""
        logger = CommandLogger(mock_bot)
        # Make ctx.command raise an exception when accessed
        mock_ctx.command = MagicMock()
        type(mock_ctx.command).name = property(lambda self: (_ for _ in ()).throw(RuntimeError("attr error")))

        logger.log_command_execution(mock_ctx)

        mock_bot.log.error.assert_called_once()
        error_call = mock_bot.log.error.call_args[0][0]
        assert "Failed to log command execution" in error_call

    def test_log_command_execution_with_subcommand_no_prefix(self, mock_bot, mock_ctx):
        """Test logging with subcommand when prefix does not match message start."""
        logger = CommandLogger(mock_bot)
        mock_ctx.prefix = "/"
        mock_ctx.message.content = "!testcmd sub arg1"
        mock_ctx.invoked_subcommand = MagicMock()
        mock_ctx.invoked_subcommand.name = "sub"

        logger.log_command_execution(mock_ctx)

        # prefix is "/" but message starts with "!", so else branch is taken
        mock_bot.log.info.assert_called_once_with(
            "Command executed in 'Test Server#general' by TestUser#5678: testcmd sub"
        )


# =============================================================================
# Tests for on_command.py - OnCommand cog
# =============================================================================


class TestOnCommand:
    """Test cases for OnCommand cog."""

    def test_init(self, mock_bot):
        """Test OnCommand cog initialization."""
        cog = OnCommand(mock_bot)
        assert cog.bot == mock_bot
        assert isinstance(cog.command_logger, CommandLogger)
        assert cog.command_logger.bot == mock_bot

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_command import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnCommand)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_on_command_event_calls_logger(self, mock_bot, mock_ctx):
        """Test on_command event handler calls the command logger."""
        cog = OnCommand(mock_bot)

        # Call the listener method directly
        await cog.on_command(mock_ctx)

        # Verify the log was called (command_logger.log_command_execution was invoked)
        mock_bot.log.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_command_event_exception(self, mock_bot, mock_ctx):
        """Test on_command event handler when exception occurs."""
        cog = OnCommand(mock_bot)

        # Patch command_logger to raise an exception
        cog.command_logger.log_command_execution = MagicMock(side_effect=RuntimeError("Logger error"))

        # Call the listener method directly
        await cog.on_command(mock_ctx)

        mock_bot.log.error.assert_called_once()
        error_call = mock_bot.log.error.call_args[0][0]
        assert "Error in on_command event" in error_call

    def test_on_command_cog_inheritance(self, mock_bot):
        """Test that OnCommand cog properly inherits from commands.Cog."""
        from discord.ext import commands

        cog = OnCommand(mock_bot)
        assert isinstance(cog, commands.Cog)
        assert hasattr(cog, 'bot')


# =============================================================================
# Tests for on_disconnect.py - OnDisconnect cog
# =============================================================================


class TestOnDisconnect:
    """Test cases for OnDisconnect cog."""

    def test_init(self, mock_bot):
        """Test OnDisconnect cog initialization."""
        cog = OnDisconnect(mock_bot)
        assert cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_disconnect import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnDisconnect)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_on_disconnect_event_logs_warning(self, mock_bot):
        """Test on_disconnect event logs a warning message."""
        cog = OnDisconnect(mock_bot)

        # Call the listener method directly
        await cog.on_disconnect()

        mock_bot.log.warning.assert_called_once_with(messages.bot_disconnected(mock_bot.user))

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_disconnect.messages')
    async def test_on_disconnect_event_with_bot_disconnected_message(self, mock_messages, mock_bot):
        """Test on_disconnect event calls bot_disconnected function."""
        mock_messages.bot_disconnected.return_value = f"Bot {mock_bot.user} has disconnected!"

        cog = OnDisconnect(mock_bot)

        await cog.on_disconnect()

        mock_messages.bot_disconnected.assert_called_once_with(mock_bot.user)
        mock_bot.log.warning.assert_called_once_with(f"Bot {mock_bot.user} has disconnected!")

    @pytest.mark.asyncio
    async def test_on_disconnect_event_exception(self, mock_bot):
        """Test on_disconnect event when exception occurs during logging."""
        mock_bot.log.warning.side_effect = RuntimeError("Logging failure")

        cog = OnDisconnect(mock_bot)

        # Should not raise; falls through to print fallback
        with patch('builtins.print') as mock_print:
            await cog.on_disconnect()
            mock_print.assert_called_once()
            print_call = mock_print.call_args[0][0]
            assert "Bot disconnected - logging failed" in print_call

    def test_on_disconnect_cog_inheritance(self, mock_bot):
        """Test that OnDisconnect cog properly inherits from commands.Cog."""
        from discord.ext import commands

        cog = OnDisconnect(mock_bot)
        assert isinstance(cog, commands.Cog)
        assert hasattr(cog, 'bot')


# =============================================================================
# Tests for on_guild_channel_create.py - OnGuildChannelCreate cog
# =============================================================================


class TestOnGuildChannelCreate:
    """Test cases for OnGuildChannelCreate cog."""

    def test_init(self, mock_bot):
        """Test OnGuildChannelCreate cog initialization."""
        cog = OnGuildChannelCreate(mock_bot)
        assert cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_guild_channel_create import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnGuildChannelCreate)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_on_guild_channel_create_event(self, mock_bot):
        """Test on_guild_channel_create event handler (currently a no-op)."""
        cog = OnGuildChannelCreate(mock_bot)

        mock_channel = MagicMock()
        mock_channel.name = "new-channel"

        # Should not raise any exception
        await cog.on_guild_channel_create(mock_channel)

    def test_on_guild_channel_create_cog_inheritance(self, mock_bot):
        """Test that OnGuildChannelCreate cog properly inherits from commands.Cog."""
        from discord.ext import commands

        cog = OnGuildChannelCreate(mock_bot)
        assert isinstance(cog, commands.Cog)
        assert hasattr(cog, 'bot')


# =============================================================================
# Tests for on_guild_channel_delete.py - OnGuildChannelDelete cog
# =============================================================================


class TestOnGuildChannelDelete:
    """Test cases for OnGuildChannelDelete cog."""

    def test_init(self, mock_bot):
        """Test OnGuildChannelDelete cog initialization."""
        cog = OnGuildChannelDelete(mock_bot)
        assert cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_guild_channel_delete import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnGuildChannelDelete)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_on_guild_channel_delete_event(self, mock_bot):
        """Test on_guild_channel_delete event handler (currently a no-op)."""
        cog = OnGuildChannelDelete(mock_bot)

        mock_channel = MagicMock()
        mock_channel.name = "deleted-channel"

        # Should not raise any exception
        await cog.on_guild_channel_delete(mock_channel)

    def test_on_guild_channel_delete_cog_inheritance(self, mock_bot):
        """Test that OnGuildChannelDelete cog properly inherits from commands.Cog."""
        from discord.ext import commands

        cog = OnGuildChannelDelete(mock_bot)
        assert isinstance(cog, commands.Cog)
        assert hasattr(cog, 'bot')


# =============================================================================
# Tests for on_guild_channel_update.py - OnGuildChannelUpdate cog
# =============================================================================


class TestOnGuildChannelUpdate:
    """Test cases for OnGuildChannelUpdate cog."""

    def test_init(self, mock_bot):
        """Test OnGuildChannelUpdate cog initialization."""
        cog = OnGuildChannelUpdate(mock_bot)
        assert cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_guild_channel_update import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnGuildChannelUpdate)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_on_guild_channel_update_event(self, mock_bot):
        """Test on_guild_channel_update event handler (currently a no-op)."""
        cog = OnGuildChannelUpdate(mock_bot)

        mock_before = MagicMock()
        mock_before.name = "old-channel"
        mock_after = MagicMock()
        mock_after.name = "new-channel"

        # Should not raise any exception
        await cog.on_guild_channel_update(mock_before, mock_after)

    def test_on_guild_channel_update_cog_inheritance(self, mock_bot):
        """Test that OnGuildChannelUpdate cog properly inherits from commands.Cog."""
        from discord.ext import commands

        cog = OnGuildChannelUpdate(mock_bot)
        assert isinstance(cog, commands.Cog)
        assert hasattr(cog, 'bot')


# =============================================================================
# Tests for on_guild_remove.py - GuildCleanupHandler
# =============================================================================


class TestGuildCleanupHandler:
    """Test cases for GuildCleanupHandler class."""

    def test_init(self, mock_bot):
        """Test GuildCleanupHandler initialization."""
        handler = GuildCleanupHandler(mock_bot)
        assert handler.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_remove.ServersDal')
    async def test_cleanup_server_data_success(self, mock_dal_class, mock_bot, mock_guild):
        """Test successful cleanup of server data."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        handler = GuildCleanupHandler(mock_bot)

        result = await handler.cleanup_server_data(mock_guild)

        assert result is True
        mock_dal_class.assert_called_once_with(mock_bot.db_session, mock_bot.log)
        mock_dal.delete_server.assert_called_once_with(mock_guild.id)
        mock_bot.log.info.assert_called_once_with(
            f"Successfully cleaned up data for guild: {mock_guild.name} (ID: {mock_guild.id})"
        )

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_remove.ServersDal')
    async def test_cleanup_server_data_failure(self, mock_dal_class, mock_bot, mock_guild):
        """Test cleanup of server data when exception occurs."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.delete_server.side_effect = RuntimeError("Database deletion error")

        handler = GuildCleanupHandler(mock_bot)

        result = await handler.cleanup_server_data(mock_guild)

        assert result is False
        mock_bot.log.error.assert_called_once()
        error_call = mock_bot.log.error.call_args[0][0]
        assert "Failed to cleanup data for guild" in error_call
        assert mock_guild.name in error_call
        assert str(mock_guild.id) in error_call

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_remove.ServersDal')
    async def test_cleanup_server_data_dal_init_failure(self, mock_dal_class, mock_bot, mock_guild):
        """Test cleanup of server data when DAL initialization fails."""
        mock_dal_class.side_effect = RuntimeError("DAL init error")

        handler = GuildCleanupHandler(mock_bot)

        result = await handler.cleanup_server_data(mock_guild)

        assert result is False
        mock_bot.log.error.assert_called_once()


# =============================================================================
# Tests for on_guild_remove.py - OnGuildRemove cog
# =============================================================================


class TestOnGuildRemove:
    """Test cases for OnGuildRemove cog."""

    def test_init(self, mock_bot):
        """Test OnGuildRemove cog initialization."""
        cog = OnGuildRemove(mock_bot)
        assert cog.bot == mock_bot
        assert isinstance(cog.cleanup_handler, GuildCleanupHandler)
        assert cog.cleanup_handler.bot == mock_bot

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_guild_remove import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnGuildRemove)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_remove.ServersDal')
    async def test_on_guild_remove_event_success(self, mock_dal_class, mock_bot, mock_guild):
        """Test on_guild_remove event handler with successful cleanup."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        cog = OnGuildRemove(mock_bot)

        # Call the listener method directly
        await cog.on_guild_remove(mock_guild)

        # Verify info log about removal
        mock_bot.log.info.assert_any_call(f"Bot removed from guild: {mock_guild.name} (ID: {mock_guild.id})")
        # Verify cleanup was attempted
        mock_dal.delete_server.assert_called_once_with(mock_guild.id)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_remove.ServersDal')
    async def test_on_guild_remove_event_cleanup_failure(self, mock_dal_class, mock_bot, mock_guild):
        """Test on_guild_remove event handler when cleanup fails."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.delete_server.side_effect = RuntimeError("DB error")

        cog = OnGuildRemove(mock_bot)

        # Call the listener method directly
        await cog.on_guild_remove(mock_guild)

        # Verify warning about incomplete cleanup
        mock_bot.log.warning.assert_called_once_with(f"Database cleanup may be incomplete for guild: {mock_guild.name}")

    @pytest.mark.asyncio
    async def test_on_guild_remove_event_general_exception(self, mock_bot, mock_guild):
        """Test on_guild_remove event handler with general exception."""
        cog = OnGuildRemove(mock_bot)

        # Make the info log raise to trigger the outer exception handler
        mock_bot.log.info.side_effect = RuntimeError("Unexpected error")

        # Call the listener method directly
        await cog.on_guild_remove(mock_guild)

        mock_bot.log.error.assert_called_once()
        error_call = mock_bot.log.error.call_args[0][0]
        assert "Error handling guild removal" in error_call

    def test_on_guild_remove_cog_inheritance(self, mock_bot):
        """Test that OnGuildRemove cog properly inherits from commands.Cog."""
        from discord.ext import commands

        cog = OnGuildRemove(mock_bot)
        assert isinstance(cog, commands.Cog)
        assert hasattr(cog, 'bot')


# =============================================================================
# Tests for on_presence_update.py - OnPresenceUpdate cog
# =============================================================================


class TestOnPresenceUpdate:
    """Test cases for OnPresenceUpdate cog."""

    def test_init(self, mock_bot):
        """Test OnPresenceUpdate cog initialization."""
        cog = OnPresenceUpdate(mock_bot)
        assert cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_presence_update import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnPresenceUpdate)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_presence_update.gw2_utils.check_gw2_game_activity')
    async def test_on_presence_update_non_bot_user(self, mock_check_gw2, mock_bot):
        """Test on_presence_update event for a non-bot user."""
        cog = OnPresenceUpdate(mock_bot)

        mock_before = MagicMock()
        mock_after = MagicMock()
        mock_after.bot = False

        # Call the listener method directly
        await cog.on_presence_update(mock_before, mock_after)

        mock_check_gw2.assert_called_once_with(mock_bot, mock_before, mock_after)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_presence_update.gw2_utils.check_gw2_game_activity')
    async def test_on_presence_update_bot_user(self, mock_check_gw2, mock_bot):
        """Test on_presence_update event for a bot user (should be ignored)."""
        cog = OnPresenceUpdate(mock_bot)

        mock_before = MagicMock()
        mock_after = MagicMock()
        mock_after.bot = True

        # Call the listener method directly
        await cog.on_presence_update(mock_before, mock_after)

        mock_check_gw2.assert_not_called()

    def test_on_presence_update_cog_inheritance(self, mock_bot):
        """Test that OnPresenceUpdate cog properly inherits from commands.Cog."""
        from discord.ext import commands

        cog = OnPresenceUpdate(mock_bot)
        assert isinstance(cog, commands.Cog)
        assert hasattr(cog, 'bot')
