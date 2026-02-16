"""Comprehensive tests for the Errors event cog."""

# Mock problematic imports before importing the module
import pytest
import sys
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules["ddcDatabases"] = Mock()

from src.bot.cogs.events.on_command_error import ErrorContext, ErrorMessageBuilder, Errors
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
        assert hasattr(cog, "message_builder")

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_send_error_message_no_log(self, mock_send_error, mock_ctx):
        """Test sending error message without logging."""
        await Errors._send_error_message(mock_ctx, "Test error", False)

        mock_send_error.assert_called_once_with(mock_ctx, "Test error")
        mock_ctx.bot.log.error.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
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
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_no_private_message(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling NoPrivateMessage error."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "Test error"

        await errors_cog._handle_no_private_message(context, True)
        mock_send_error.assert_called_once_with(mock_ctx, "Test error", True)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_command_not_found(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling CommandNotFound error."""
        context = ErrorContext(mock_ctx, Exception())

        await errors_cog._handle_command_not_found(context, False)

        expected_msg = f"{messages.COMMAND_NOT_FOUND}:\n`!testcommand`"
        mock_send_error.assert_called_once_with(mock_ctx, expected_msg, False)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_bad_argument_gw2_config_status(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling BadArgument error for GW2 config status."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "BadArgument_Gw2ConfigStatus"
        mock_ctx.message.clean_content = "!gw2 config status invalid"

        await errors_cog._handle_bad_argument(context, False)

        assert context.bad_argument == "invalid"
        mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    @patch("src.bot.cogs.events.on_command_error.bot_utils.delete_message")
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
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    @patch("src.bot.cogs.events.on_command_error.bot_utils.delete_message")
    async def test_handle_command_on_cooldown_normal_command(self, mock_delete, mock_send_error, errors_cog, mock_ctx):
        """Test handling CommandOnCooldown for normal commands."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "Command is on cooldown"
        mock_ctx.message.content = "!ping"

        await errors_cog._handle_command_on_cooldown(context, False)

        mock_delete.assert_not_called()
        mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_too_many_arguments(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling TooManyArguments error."""
        context = ErrorContext(mock_ctx, Exception())

        await errors_cog._handle_too_many_arguments(context, False)

        expected_msg = f"{messages.COMMAND_ERROR}!\n {messages.HELP_COMMAND_MORE_INFO}: `!help testcommand`"
        mock_send_error.assert_called_once_with(mock_ctx, expected_msg, False)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
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
        assert hasattr(errors_cog, "bot")

    def test_error_context_with_complex_command(self, mock_ctx, mock_error):
        """Test ErrorContext with complex command structure."""
        mock_ctx.command.__str__ = MagicMock(return_value="admin config")
        mock_ctx.subcommand_passed = "profanity on"

        context = ErrorContext(mock_ctx, mock_error)
        assert context.command == "!admin config profanity on"
        assert context.help_command == "!help admin config profanity on"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
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


class TestErrorContextCommandNone:
    """Test cases for ErrorContext._build_command_string when ctx.command is None (lines 22-25)."""

    def test_build_command_string_command_none_with_message_parts(self, mock_ctx, mock_error):
        """Test _build_command_string when ctx.command is None and message has content (lines 22-24)."""
        mock_ctx.command = None
        mock_ctx.message.content = "!unknowncmd arg1 arg2"

        context = ErrorContext(mock_ctx, mock_error)
        assert context.command == "!unknowncmd"

    def test_build_command_string_command_none_empty_message(self, mock_ctx, mock_error):
        """Test _build_command_string when ctx.command is None and message is empty (line 25)."""
        mock_ctx.command = None
        mock_ctx.message.content = "   "
        mock_ctx.prefix = "!"

        context = ErrorContext(mock_ctx, mock_error)
        assert context.command == "!unknown"


class TestErrorContextHelpCommandProperty:
    """Test cases for ErrorContext.help_command property (line 52 area - already tested but ensuring coverage)."""

    def test_help_command_with_subcommand(self, mock_ctx, mock_error):
        """Test help_command property with subcommand passed."""
        mock_ctx.subcommand_passed = "sub"
        context = ErrorContext(mock_ctx, mock_error)
        assert context.help_command == "!help testcommand sub"


class TestErrorMessageBuilderFallthrough:
    """Test cases for ErrorMessageBuilder.get_error_message fallthrough (line 52)."""

    def test_get_error_message_no_args_no_original(self):
        """Test get_error_message when error has no args and no original attribute (line 52)."""

        class CustomError:
            """Custom error class without args or original."""

            def __str__(self):
                return "fallthrough error string"

        error = CustomError()
        result = ErrorMessageBuilder.get_error_message(error)
        assert result == "fallthrough error string"

    def test_get_error_message_empty_args_no_original(self):
        """Test get_error_message when error.args is empty and no original (line 52)."""
        error = MagicMock()
        error.args = []
        # Remove the 'original' attribute so it falls through to return str(error)
        del error.original
        error.__str__ = MagicMock(return_value="string representation")

        result = ErrorMessageBuilder.get_error_message(error)
        assert result == "string representation"


class TestBuildCommandInvokeErrorElse:
    """Test cases for build_command_invoke_error else branch (line 111)."""

    def test_build_command_invoke_error_no_matching_condition(self, mock_ctx, mock_error):
        """Test build_command_invoke_error when no error conditions match (line 111)."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "Some completely unrelated error that matches nothing"

        result = ErrorMessageBuilder.build_command_invoke_error(context)
        assert f"{messages.COMMAND_INTERNAL_ERROR}: `!testcommand`" in result
        assert f"{messages.HELP_COMMAND_MORE_INFO}: `!help testcommand`" in result

    def test_build_command_invoke_error_attribute_error(self, mock_ctx, mock_error):
        """Test build_command_invoke_error with AttributeError in message."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "AttributeError: 'NoneType' object has no attribute 'foo'"

        result = ErrorMessageBuilder.build_command_invoke_error(context)
        assert f"{messages.COMMAND_ERROR}: `!testcommand`" in result

    def test_build_command_invoke_error_missing_permissions(self, mock_ctx, mock_error):
        """Test build_command_invoke_error with Missing Permissions."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "Missing Permissions to do something"

        result = ErrorMessageBuilder.build_command_invoke_error(context)
        assert f"{messages.NO_PERMISSION_EXECUTE_COMMAND}: `!testcommand`" in result

    def test_build_command_invoke_error_no_option_error(self, mock_ctx, mock_error):
        """Test build_command_invoke_error with NoOptionError."""
        context = ErrorContext(mock_ctx, mock_error)
        # The code does: error_msg.split()[7] to get the option name
        # Indices:        0             1   2      3     4     5     6     7
        context.error_msg = "NoOptionError: no option 'optname' in section 'section' myoption"

        result = ErrorMessageBuilder.build_command_invoke_error(context)
        assert f"{messages.NO_OPTION_FOUND}: `myoption`" in result

    def test_build_command_invoke_error_gw2_api(self, mock_ctx, mock_error):
        """Test build_command_invoke_error with GW2 API error."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "GW2 API error, https://api.gw2.com/v2/account?access_token=xxx, details"

        result = ErrorMessageBuilder.build_command_invoke_error(context)
        assert "https://api.gw2.com/v2/account" in result

    def test_build_command_invoke_error_tts(self, mock_ctx, mock_error):
        """Test build_command_invoke_error with TTS error."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "No text to send to TTS API"

        result = ErrorMessageBuilder.build_command_invoke_error(context)
        assert messages.INVALID_MESSAGE in result

    def test_build_command_invoke_error_status_code_403(self, mock_ctx, mock_error):
        """Test build_command_invoke_error with status code 403."""
        context = ErrorContext(mock_ctx, mock_error)
        context.error_msg = "status code: 403 forbidden"

        result = ErrorMessageBuilder.build_command_invoke_error(context)
        assert messages.DIRECT_MESSAGES_DISABLED in result


class TestOnCommandErrorEventHandler:
    """Test cases for the on_command_error event handler (lines 133-151)."""

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_command_not_found(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches CommandNotFound properly (lines 133-151)."""
        cog = Errors(mock_bot)
        error = commands.CommandNotFound()
        mock_ctx.command = None
        mock_ctx.message.content = "!nonexistent arg1"

        # Get the on_command_error function registered via bot.event
        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()
        call_msg = mock_send_error.call_args[0][1]
        assert messages.COMMAND_NOT_FOUND in call_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_missing_required_argument(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches MissingRequiredArgument (lines 140, 175-176)."""
        cog = Errors(mock_bot)

        param = MagicMock()
        param.name = "arg_name"
        error = commands.MissingRequiredArgument(param)

        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()
        call_msg = mock_send_error.call_args[0][1]
        assert messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE in call_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_check_failure(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches CheckFailure (lines 141, 180-181)."""
        cog = Errors(mock_bot)
        error = commands.CheckFailure("not admin to use command")

        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()
        call_msg = mock_send_error.call_args[0][1]
        assert messages.NOT_ADMIN_USE_COMMAND in call_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_bad_argument_gw2_server(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches BadArgument for GW2 server (lines 142, 188-190)."""
        cog = Errors(mock_bot)
        error = commands.BadArgument("BadArgument_Gw2ConfigServer")
        # split()[4:] means everything from index 4 onwards forms the server name
        mock_ctx.message.clean_content = "!gw2 config server set My Server"

        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_bad_argument_else_branch(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches BadArgument else branch (lines 191-192)."""
        cog = Errors(mock_bot)
        error = commands.BadArgument("some other bad argument error")
        mock_ctx.message.clean_content = "!testcommand badvalue"

        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()
        call_msg = mock_send_error.call_args[0][1]
        assert messages.UNKNOWN_OPTION in call_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_command_invoke_error(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches CommandInvokeError (lines 144, 204-205)."""
        cog = Errors(mock_bot)
        original_error = Exception("Some unexpected error")
        error = commands.CommandInvokeError(original_error)

        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()
        call_msg = mock_send_error.call_args[0][1]
        assert messages.COMMAND_INTERNAL_ERROR in call_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_forbidden(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches discord.Forbidden (lines 147, 234-235)."""
        import discord

        cog = Errors(mock_bot)
        response = MagicMock()
        response.status = 403
        response.reason = "Forbidden"
        error = discord.Forbidden(response, "Cannot execute action on a DM channel")

        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()
        call_msg = mock_send_error.call_args[0][1]
        assert call_msg == messages.DM_CANNOT_EXECUTE_COMMAND

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_forbidden_privilege_low(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches discord.Forbidden with low privilege (lines 234-235)."""
        import discord

        cog = Errors(mock_bot)
        response = MagicMock()
        response.status = 403
        response.reason = "Forbidden"
        error = discord.Forbidden(response, "You do not have access")

        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()
        call_msg = mock_send_error.call_args[0][1]
        assert call_msg == messages.PRIVILEGE_LOW

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_no_private_message(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches NoPrivateMessage (line 138)."""
        cog = Errors(mock_bot)
        error = commands.NoPrivateMessage("This command cannot be used in DMs")

        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_command_error(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches CommandError (line 143)."""
        cog = Errors(mock_bot)
        error = commands.CommandError("Generic command error")

        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()
        call_msg = mock_send_error.call_args[0][1]
        assert "CommandError:" in call_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_on_command_error_unknown_error_type(self, mock_send_error, mock_bot, mock_ctx):
        """Test on_command_error dispatches unknown error type (line 150)."""
        cog = Errors(mock_bot)
        error = RuntimeError("Unknown runtime error")

        on_command_error_func = mock_bot.event.call_args[0][0]
        await on_command_error_func(mock_ctx, error)

        mock_send_error.assert_called_once()


class TestSendErrorMessageGuildNone:
    """Test cases for _send_error_message when guild is None (lines 204-205 logging branch)."""

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.bot_utils.send_error_msg")
    async def test_send_error_message_with_log_no_guild(self, mock_send_error, mock_ctx):
        """Test sending error message with logging when guild is None."""
        mock_ctx.guild = None

        await Errors._send_error_message(mock_ctx, "Test error", True)

        mock_send_error.assert_called_once_with(mock_ctx, "Test error")
        mock_ctx.bot.log.error.assert_called_once()

        log_call = mock_ctx.bot.log.error.call_args[0][0]
        assert "Test error" in log_call
        assert "Server[" not in log_call
        assert "Channel[" in log_call


class TestHandleBadArgumentBranches:
    """Test cases for _handle_bad_argument different branches (lines 188-192)."""

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_bad_argument_gw2_config_server(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling BadArgument for GW2 config server (lines 188-190)."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "BadArgument_Gw2ConfigServer"
        # split()[4:] means everything from index 4 onwards forms the server name
        # indices: 0='!gw2', 1='config', 2='server', 3='set', 4='Aurora', 5='Glade'
        mock_ctx.message.clean_content = "!gw2 config server set Aurora Glade"

        await errors_cog._handle_bad_argument(context, False)

        assert context.bad_argument == "Aurora Glade"
        mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_bad_argument_else_branch(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling BadArgument else branch (lines 191-192)."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "some_other_bad_argument"
        mock_ctx.message.clean_content = "!testcommand invalidarg"

        await errors_cog._handle_bad_argument(context, False)

        assert context.bad_argument == "invalidarg"
        mock_send_error.assert_called_once()


class TestHandleMissingArgument:
    """Test cases for _handle_missing_argument (lines 175-176)."""

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_missing_argument(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling MissingRequiredArgument (lines 175-176)."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "param is a required argument"

        await errors_cog._handle_missing_argument(context, False)

        expected_msg = f"{messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE}: `!help testcommand`"
        mock_send_error.assert_called_once_with(mock_ctx, expected_msg, False)


class TestHandleCheckFailure:
    """Test cases for _handle_check_failure (lines 180-181)."""

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_check_failure_not_owner(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling CheckFailure with not owner (lines 180-181)."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "not owner of the bot"

        await errors_cog._handle_check_failure(context, True)

        expected_msg = f"{messages.BOT_OWNERS_ONLY_COMMAND}: `!testcommand`"
        mock_send_error.assert_called_once_with(mock_ctx, expected_msg, True)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_check_failure_other(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling CheckFailure with generic error (lines 180-181)."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "some generic check failure"

        await errors_cog._handle_check_failure(context, True)

        mock_send_error.assert_called_once_with(mock_ctx, "some generic check failure", True)


class TestHandleCommandInvokeError:
    """Test cases for _handle_command_invoke_error (lines 204-205)."""

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_command_invoke_error(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling CommandInvokeError (lines 204-205)."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "Some random error that does not match any condition"

        await errors_cog._handle_command_invoke_error(context, True)

        mock_send_error.assert_called_once()
        call_args = mock_send_error.call_args[0]
        assert call_args[0] == mock_ctx
        assert messages.COMMAND_INTERNAL_ERROR in call_args[1]
        assert call_args[2] is True


class TestHandleForbidden:
    """Test cases for _handle_forbidden (lines 234-235)."""

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_forbidden_dm_channel(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling Forbidden for DM channel (lines 234-235)."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "Cannot execute action on a DM channel"

        await errors_cog._handle_forbidden(context, True)

        mock_send_error.assert_called_once_with(mock_ctx, messages.DM_CANNOT_EXECUTE_COMMAND, True)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.events.on_command_error.Errors._send_error_message")
    async def test_handle_forbidden_privilege_low(self, mock_send_error, errors_cog, mock_ctx):
        """Test handling Forbidden for low privilege (lines 234-235)."""
        context = ErrorContext(mock_ctx, Exception())
        context.error_msg = "You don't have permission"

        await errors_cog._handle_forbidden(context, True)

        mock_send_error.assert_called_once_with(mock_ctx, messages.PRIVILEGE_LOW, True)
