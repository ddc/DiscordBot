"""Comprehensive tests for the Errors event cog."""

# Mock problematic imports before importing the module
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest
from discord.ext import commands


sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.events.on_command_error import Errors, ErrorContext, ErrorMessageBuilder
from src.bot.constants import messages, variables


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.log = MagicMock()
    # Ensure log methods are not coroutines
    bot.log.error = MagicMock()
    # Ensure add_cog doesn't return a coroutine
    bot.add_cog = AsyncMock(return_value=None)
    # Mock the event decorator to prevent coroutine issues
    bot.event = MagicMock(side_effect=lambda func: func)
    return bot


@pytest.fixture
def errors_cog(mock_bot):
    """Create an Errors cog instance."""
    return Errors(mock_bot)


@pytest.fixture
def mock_ctx():
    """Create a mock context."""
    ctx = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    ctx.guild.name = "Test Server"

    ctx.command = MagicMock()
    ctx.command.__str__ = MagicMock(return_value="testcommand")
    ctx.prefix = "!"
    ctx.subcommand_passed = None

    ctx.message = MagicMock()
    ctx.message.content = "!testcommand arg1 arg2"
    ctx.message.clean_content = "!testcommand arg1 arg2"
    ctx.message.author = MagicMock()
    ctx.message.author.id = 67890
    ctx.message.channel = MagicMock()
    ctx.message.channel.id = 98765

    # Setup ctx.bot with proper mock configuration
    ctx.bot = AsyncMock()
    ctx.bot.log = MagicMock()
    ctx.bot.log.error = MagicMock()

    return ctx


@pytest.fixture
def mock_error():
    """Create a mock error."""
    error = Exception("Test error message")
    return error


class TestErrorContext:
    """Test cases for ErrorContext class."""

    def test_init(self, mock_ctx, mock_error):
        """Test ErrorContext initialization."""
        context = ErrorContext(mock_ctx, mock_error)

        assert context.ctx == mock_ctx
        assert context.error == mock_error
        assert context.command == "!testcommand"
        assert context.error_msg == ""
        assert context.bad_argument is None

    def test_build_command_string_no_subcommand(self, mock_ctx, mock_error):
        """Test command string building without subcommand."""
        context = ErrorContext(mock_ctx, mock_error)
        assert context.command == "!testcommand"

    def test_build_command_string_with_subcommand(self, mock_ctx, mock_error):
        """Test command string building with subcommand."""
        mock_ctx.subcommand_passed = "subcmd"
        context = ErrorContext(mock_ctx, mock_error)
        assert context.command == "!testcommand subcmd"

    def test_help_command_property(self, mock_ctx, mock_error):
        """Test help command property."""
        context = ErrorContext(mock_ctx, mock_error)
        assert context.help_command == "!help testcommand"


class TestErrorMessageBuilder:
    """Test cases for ErrorMessageBuilder class."""

    def test_get_error_message_with_args(self):
        """Test error message extraction with args."""
        error = Exception("Test error")
        result = ErrorMessageBuilder.get_error_message(error)
        assert result == "Test error"

    def test_get_error_message_with_command_raised_exception(self):
        """Test error message extraction with command raised exception."""
        error = Exception(f"{messages.COMMAND_RAISED_EXCEPTION}:Actual error")
        result = ErrorMessageBuilder.get_error_message(error)
        assert result == "Actual error"

    def test_get_error_message_with_original(self):
        """Test error message extraction with original attribute."""
        error = MagicMock()
        error.args = []
        error.original = MagicMock()
        error.original.args = ["Original error"]

        result = ErrorMessageBuilder.get_error_message(error)
        assert result == "Original error"

    def test_build_command_not_found(self, mock_ctx, mock_error):
        """Test command not found message building."""
        context = ErrorContext(mock_ctx, mock_error)
        result = ErrorMessageBuilder.build_command_not_found(context)
        expected = f"{messages.COMMAND_NOT_FOUND}:\n`!testcommand`"
        assert result == expected

    def test_build_missing_argument(self, mock_ctx, mock_error):
        """Test missing argument message building."""
        context = ErrorContext(mock_ctx, mock_error)
        result = ErrorMessageBuilder.build_missing_argument(context)
        expected = f"{messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE}: `!help testcommand`"
        assert result == expected

    def test_build_check_failure_not_admin(self, mock_ctx, mock_error):
        """Test check failure message for not admin."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "user not admin"
        result = ErrorMessageBuilder.build_check_failure(context)
        expected = f"{messages.NOT_ADMIN_USE_COMMAND}: `!testcommand`"
        assert result == expected

    def test_build_check_failure_not_owner(self, mock_ctx, mock_error):
        """Test check failure message for not owner."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "user not owner"
        result = ErrorMessageBuilder.build_check_failure(context)
        expected = f"{messages.BOT_OWNERS_ONLY_COMMAND}: `!testcommand`"
        assert result == expected

    def test_build_check_failure_other(self, mock_ctx, mock_error):
        """Test check failure message for other errors."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "some other error"
        result = ErrorMessageBuilder.build_check_failure(context)
        assert result == "some other error"

    def test_build_bad_argument_bot_prefix(self, mock_ctx, mock_error):
        """Test bad argument message for bot prefix."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "invalid bot_prefix"
        context.bad_argument = "#"
        result = ErrorMessageBuilder.build_bad_argument(context)

        expected_prefixes = " ".join(variables.ALLOWED_PREFIXES)
        assert f"{messages.PREFIXES_CHOICE}: {expected_prefixes}" in result
        assert f"{messages.HELP_COMMAND_MORE_INFO}: `!help testcommand`" in result

    def test_build_command_invoke_error_dm_disabled(self, mock_ctx, mock_error):
        """Test command invoke error for DM disabled."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "Cannot send messages to this user"
        result = ErrorMessageBuilder.build_command_invoke_error(context)

        assert messages.DIRECT_MESSAGES_DISABLED in result
        assert f"{messages.HELP_COMMAND_MORE_INFO}: `!help testcommand`" in result

    def test_build_forbidden_error_dm_channel(self, mock_ctx, mock_error):
        """Test forbidden error for DM channel."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "Cannot execute action on a DM channel"
        result = ErrorMessageBuilder.build_forbidden_error(context)
        assert result == messages.DM_CANNOT_EXECUTE_COMMAND

    def test_build_forbidden_error_other(self, mock_ctx, mock_error):
        """Test forbidden error for other cases."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "Some other forbidden error"
        result = ErrorMessageBuilder.build_forbidden_error(context)
        assert result == messages.PRIVILEGE_LOW


class TestErrors:
    """Test cases for Errors cog."""

    def test_init(self, mock_bot):
        """Test Errors cog initialization."""
        cog = Errors(mock_bot)
        assert cog.bot == mock_bot
        assert hasattr(cog, 'message_builder')

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_command_error.bot_utils.send_error_msg')
    async def test_send_error_message_no_log(self, mock_send_error, mock_ctx):
        """Test sending error message without logging."""
        await Errors._send_error_message(mock_ctx, "Test error", False)

        mock_send_error.assert_called_once_with(mock_ctx, "Test error")
        mock_ctx.bot.log.error.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_command_error.bot_utils.send_error_msg')
    async def test_send_error_message_with_log(self, mock_send_error, mock_ctx):
        """Test sending error message with logging."""
        await Errors._send_error_message(mock_ctx, "Test error", True)

        mock_send_error.assert_called_once_with(mock_ctx, "Test error")
        mock_ctx.bot.log.error.assert_called_once()

        log_call = mock_ctx.bot.log.error.call_args[0][0]
        assert "Test error" in log_call
        assert str(mock_ctx.message.author) in log_call
        assert "Test Server" in log_call

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_command_error.Errors._send_error_message')
    async def test_handle_no_private_message(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling NoPrivateMessage error."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "Test error"

        await errors_cog._handle_no_private_message(context, True)
        mock_send_error.assert_called_once_with(mock_ctx, "Test error", True)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_command_error.Errors._send_error_message')
    async def test_handle_command_not_found(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling CommandNotFound error."""
        context = ErrorContext(mock_ctx, Exception())

        await errors_cog._handle_command_not_found(context, False)

        expected_msg = f"{messages.COMMAND_NOT_FOUND}:\n`!testcommand`"
        mock_send_error.assert_called_once_with(mock_ctx, expected_msg, False)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_command_error.Errors._send_error_message')
    async def test_handle_bad_argument_gw2_config_status(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling BadArgument error for GW2 config status."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "BadArgument_Gw2ConfigStatus"
        mock_ctx.message.clean_content = "!gw2 config status invalid"

        await errors_cog._handle_bad_argument(context, False)

        assert context.bad_argument == "invalid"
        mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_command_error.Errors._send_error_message')
    @patch('src.bot.cogs.events.on_command_error.bot_utils.delete_message')
    async def test_handle_command_on_cooldown_sensitive_command(
        self, mock_delete, mock_send_error, errors_cog, mock_ctx
    ):
        """Test handling CommandOnCooldown for sensitive commands."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "Command is on cooldown"
        mock_ctx.message.content = "!gw2 key add mykey"

        await errors_cog._handle_command_on_cooldown(context, False)

        mock_delete.assert_called_once_with(mock_ctx)
        mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_command_error.Errors._send_error_message')
    @patch('src.bot.cogs.events.on_command_error.bot_utils.delete_message')
    async def test_handle_command_on_cooldown_normal_command(self, mock_delete, mock_send_error, errors_cog, mock_ctx):
        """Test handling CommandOnCooldown for normal commands."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "Command is on cooldown"
        mock_ctx.message.content = "!ping"

        await errors_cog._handle_command_on_cooldown(context, False)

        mock_delete.assert_not_called()
        mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_command_error.Errors._send_error_message')
    async def test_handle_too_many_arguments(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling TooManyArguments error."""
        context = ErrorContext(mock_ctx, Exception())

        await errors_cog._handle_too_many_arguments(context, False)

        expected_msg = f"{messages.COMMAND_ERROR}!\n {messages.HELP_COMMAND_MORE_INFO}: `!help testcommand`"
        mock_send_error.assert_called_once_with(mock_ctx, expected_msg, False)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_command_error.Errors._send_error_message')
    async def test_handle_unknown_error(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling unknown error types."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "Unknown error"

        await errors_cog._handle_unknown_error(context, True)

        mock_send_error.assert_called_once_with(mock_ctx, "Unknown error", True)

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_command_error import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, Errors)
        assert added_cog.bot == mock_bot

    def test_errors_cog_inheritance(self, errors_cog):
        """Test that Errors cog properly inherits from commands.Cog."""
        assert isinstance(errors_cog, commands.Cog)
        assert hasattr(errors_cog, 'bot')

    def test_error_context_with_complex_command(self, mock_ctx, mock_error):
        """Test ErrorContext with complex command structure."""
        mock_ctx.command.__str__ = MagicMock(return_value="admin config")
        mock_ctx.subcommand_passed = "profanity on"

        context = ErrorContext(mock_ctx, mock_error)
        assert context.command == "!admin config profanity on"
        assert context.help_command == "!help admin config profanity on"

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_command_error.Errors._send_error_message')
    async def test_handle_command_error(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling CommandError."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "Command failed"

        await errors_cog._handle_command_error(context, True)

        expected_msg = "CommandError: Command failed"
        mock_send_error.assert_called_once_with(mock_ctx, expected_msg, True)

    def test_build_bad_argument_gw2_server(self, mock_ctx, mock_error):
        """Test bad argument message for GW2 server."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "BadArgument_Gw2ConfigServer"
        context.bad_argument = "invalid server"

        from src.gw2.constants import gw2_messages

        result = ErrorMessageBuilder.build_bad_argument(context)

        assert f"{gw2_messages.GW2_SERVER_NOT_FOUND}: `invalid server`" in result
        assert f"{gw2_messages.GW2_SERVER_MORE_INFO}: `!gw2 worlds`" in result
        assert f"{messages.HELP_COMMAND_MORE_INFO}: `!help testcommand`" in result
