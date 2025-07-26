"""Comprehensive tests for the OnMessage event cog."""

# Mock problematic imports before importing the module
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import discord
import pytest
from discord.ext import commands


sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.events.on_message import (
    OnMessage,
    MessageValidator,
    ProfanityFilter,
    CustomReactionHandler,
    DMMessageHandler,
    ServerMessageHandler,
    MessageContext,
    ExclusiveUsersChecker,
)
from src.bot.constants import messages


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.log = MagicMock()
    # Ensure log methods are not coroutines
    bot.log.error = MagicMock()
    bot.db_session = MagicMock()
    bot.user = MagicMock()
    bot.user.mention = "<@123456789>"
    bot.owner_id = 999999
    bot.profanity = MagicMock()
    bot.settings = {
        "bot": {"BotReactionWords": ["bad", "ugly"], "ExclusiveUsers": None, "AllowedDMCommands": ["help", "info"]}
    }
    # Make get_command a regular method, not async
    bot.get_command = MagicMock()
    bot.process_commands = AsyncMock()
    # Ensure add_cog doesn't return a coroutine
    bot.add_cog = AsyncMock(return_value=None)
    # Mock the event decorator to prevent coroutine issues
    bot.event = MagicMock(side_effect=lambda func: func)
    return bot


@pytest.fixture
def on_message_cog(mock_bot):
    """Create an OnMessage cog instance."""
    return OnMessage(mock_bot)


@pytest.fixture
def mock_ctx():
    """Create a mock context."""
    ctx = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    ctx.guild.name = "Test Server"

    ctx.author = MagicMock()
    ctx.author.id = 67890
    ctx.author.display_name = "TestUser"
    ctx.author.avatar = MagicMock()
    ctx.author.avatar.url = "https://example.com/avatar.png"
    ctx.author.status = MagicMock()
    ctx.author.status.name = "online"
    ctx.author.bot = False
    ctx.author.guild = ctx.guild
    ctx.author.send = AsyncMock()

    ctx.message = MagicMock()
    ctx.message.content = "Hello world"
    ctx.message.system_content = "Hello world"
    ctx.message.clean_content = "Hello world"
    ctx.message.author = ctx.author
    ctx.message.guild = ctx.guild
    ctx.message.channel = MagicMock()
    ctx.message.channel.typing = AsyncMock()
    ctx.message.channel.send = AsyncMock()
    # Make sure message.author.send is also async
    ctx.message.author.send = AsyncMock()

    ctx.prefix = "!"
    ctx.invoked_with = "testcommand"
    ctx.send = AsyncMock()

    # Setup ctx.bot with proper mock configuration for bot_utils
    ctx.bot = AsyncMock()
    ctx.bot.log = MagicMock()
    ctx.bot.log.error = MagicMock()

    return ctx


@pytest.fixture
def mock_dm_ctx(mock_ctx):
    """Create a mock DM context."""
    dm_channel = MagicMock(spec=discord.DMChannel)
    mock_ctx.message.channel = dm_channel
    mock_ctx.channel = dm_channel
    return mock_ctx


@pytest.fixture
def server_configs():
    """Create mock server configurations."""
    return {"block_invis_members": False, "profanity_filter": False, "bot_word_reactions": False}


class TestMessageContext:
    """Test cases for MessageContext class."""

    def test_init_server_message(self, mock_ctx):
        """Test MessageContext initialization for server message."""
        context = MessageContext(mock_ctx, True)

        assert context.ctx == mock_ctx
        assert context.is_command is True
        assert context.is_dm is False
        assert context.server_configs is None

    def test_init_dm_message(self, mock_dm_ctx):
        """Test MessageContext initialization for DM message."""
        context = MessageContext(mock_dm_ctx, False)

        assert context.ctx == mock_dm_ctx
        assert context.is_command is False
        assert context.is_dm is True


class TestMessageValidator:
    """Test cases for MessageValidator class."""

    def test_has_content_true(self):
        """Test has_content with content."""
        message = MagicMock()
        message.content = "Hello"
        assert MessageValidator.has_content(message) is True

    def test_has_content_false(self):
        """Test has_content without content."""
        message = MagicMock()
        message.content = ""
        assert MessageValidator.has_content(message) is False

    def test_is_bot_message_true(self):
        """Test is_bot_message with bot user."""
        author = MagicMock()
        author.bot = True
        assert MessageValidator.is_bot_message(author) is True

    def test_is_bot_message_false(self):
        """Test is_bot_message with human user."""
        author = MagicMock()
        author.bot = False
        assert MessageValidator.is_bot_message(author) is False

    def test_is_command_true(self, mock_ctx):
        """Test is_command with prefix."""
        mock_ctx.prefix = "!"
        assert MessageValidator.is_command(mock_ctx) is True

    def test_is_command_false(self, mock_ctx):
        """Test is_command without prefix."""
        mock_ctx.prefix = None
        assert MessageValidator.is_command(mock_ctx) is False

    def test_is_member_invisible_true(self, mock_ctx):
        """Test is_member_invisible with offline status."""
        mock_ctx.author.status.name = "offline"
        assert MessageValidator.is_member_invisible(mock_ctx) is True

    def test_is_member_invisible_false(self, mock_ctx):
        """Test is_member_invisible with online status."""
        mock_ctx.author.status.name = "online"
        assert MessageValidator.is_member_invisible(mock_ctx) is False

    def test_has_double_prefix_true(self):
        """Test has_double_prefix with double prefix."""
        message = MagicMock()
        message.content = "!!"
        assert MessageValidator.has_double_prefix(message) is True

    def test_has_double_prefix_false(self):
        """Test has_double_prefix with normal command."""
        message = MagicMock()
        message.content = "!help"
        assert MessageValidator.has_double_prefix(message) is False

    def test_has_double_prefix_short_content(self):
        """Test has_double_prefix with short content."""
        message = MagicMock()
        message.content = "!"
        assert MessageValidator.has_double_prefix(message) is False


class TestProfanityFilter:
    """Test cases for ProfanityFilter class."""

    def test_init(self, mock_bot):
        """Test ProfanityFilter initialization."""
        filter_obj = ProfanityFilter(mock_bot)
        assert filter_obj.bot == mock_bot

    @pytest.mark.asyncio
    async def test_check_and_censor_no_profanity(self, mock_bot, mock_ctx):
        """Test check_and_censor with no profanity."""
        mock_bot.profanity.contains_profanity.return_value = False
        filter_obj = ProfanityFilter(mock_bot)

        result = await filter_obj.check_and_censor(mock_ctx)

        assert result is False
        mock_bot.profanity.contains_profanity.assert_called_once_with("Hello world")

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.delete_message')
    async def test_check_and_censor_with_profanity(self, mock_delete, mock_bot, mock_ctx):
        """Test check_and_censor with profanity."""
        mock_bot.profanity.contains_profanity.return_value = True
        mock_bot.profanity.censor.return_value = "#### world"
        filter_obj = ProfanityFilter(mock_bot)

        result = await filter_obj.check_and_censor(mock_ctx)

        assert result is True
        mock_delete.assert_called_once_with(mock_ctx)
        mock_ctx.message.channel.send.assert_called()

    @pytest.mark.asyncio
    async def test_check_and_censor_with_error(self, mock_bot, mock_ctx):
        """Test check_and_censor with exception during censoring."""
        mock_bot.profanity.contains_profanity.return_value = True
        mock_ctx.message.channel.send.side_effect = Exception("Test error")
        filter_obj = ProfanityFilter(mock_bot)

        result = await filter_obj.check_and_censor(mock_ctx)

        assert result is True  # Should still return True even with error


class TestCustomReactionHandler:
    """Test cases for CustomReactionHandler class."""

    def test_init(self, mock_bot):
        """Test CustomReactionHandler initialization."""
        handler = CustomReactionHandler(mock_bot)
        assert handler.bot == mock_bot

    @pytest.mark.asyncio
    async def test_check_and_react_no_reaction_word(self, mock_bot):
        """Test check_and_react without reaction word."""
        mock_bot.settings["bot"]["BotReactionWords"] = ["bad"]
        handler = CustomReactionHandler(mock_bot)

        message = MagicMock()
        message.system_content = "hello world"
        message.channel = MagicMock()

        result = await handler.check_and_react(message)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_and_react_no_bot_mention(self, mock_bot):
        """Test check_and_react without bot mention."""
        mock_bot.settings["bot"]["BotReactionWords"] = ["bad"]
        handler = CustomReactionHandler(mock_bot)

        message = MagicMock()
        message.system_content = "this is bad"
        message.channel = MagicMock()

        result = await handler.check_and_react(message)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_and_react_success(self, mock_bot):
        """Test successful reaction."""
        mock_bot.settings["bot"]["BotReactionWords"] = ["bad"]
        mock_bot.user.mention = "<@123456789>"
        handler = CustomReactionHandler(mock_bot)

        message = MagicMock()
        message.system_content = "bot is bad"
        message.channel = AsyncMock()
        message.author = MagicMock()
        message.author.display_name = "TestUser"
        message.author.avatar.url = "https://example.com/avatar.png"

        result = await handler.check_and_react(message)

        assert result is True
        message.channel.typing.assert_called_once()
        message.channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_and_react_dm_always_reacts(self, mock_bot):
        """Test that DM messages always react if reaction word present."""
        mock_bot.settings["bot"]["BotReactionWords"] = ["bad"]
        handler = CustomReactionHandler(mock_bot)

        message = MagicMock()
        message.system_content = "bad"
        message.channel = MagicMock(spec=discord.DMChannel)
        message.channel.typing = AsyncMock()
        message.channel.send = AsyncMock()
        message.author = MagicMock()
        message.author.display_name = "TestUser"
        message.author.avatar.url = "https://example.com/avatar.png"

        result = await handler.check_and_react(message)
        assert result is True

    def test_get_reaction_response_stupid(self):
        """Test reaction response for 'stupid'."""
        response = CustomReactionHandler._get_reaction_response("you are stupid")
        assert response == messages.BOT_REACT_STUPID

    def test_get_reaction_response_retard(self):
        """Test reaction response for 'retard'."""
        response = CustomReactionHandler._get_reaction_response("you are retard")
        assert response == messages.BOT_REACT_RETARD

    def test_get_reaction_response_default(self):
        """Test default reaction response."""
        response = CustomReactionHandler._get_reaction_response("you are bad")
        assert response == "fu ufk!!!"


class TestExclusiveUsersChecker:
    """Test cases for ExclusiveUsersChecker class."""
    
    @pytest.mark.asyncio
    async def test_check_exclusive_users_none(self, mock_bot, mock_ctx):
        """Test exclusive users check when None."""
        mock_bot.settings["bot"]["ExclusiveUsers"] = None

        result = await ExclusiveUsersChecker.check_exclusive_users(mock_bot, mock_ctx)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_exclusive_users_allowed(self, mock_bot, mock_ctx):
        """Test exclusive users check when user is allowed."""
        mock_bot.settings["bot"]["ExclusiveUsers"] = [67890]

        result = await ExclusiveUsersChecker.check_exclusive_users(mock_bot, mock_ctx)
        assert result is True

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.send_error_msg')
    async def test_check_exclusive_users_not_allowed(self, mock_send_error, mock_bot, mock_ctx):
        """Test exclusive users check when user is not allowed."""
        mock_bot.settings["bot"]["ExclusiveUsers"] = [99999]

        result = await ExclusiveUsersChecker.check_exclusive_users(mock_bot, mock_ctx)

        assert result is False
        mock_send_error.assert_called_once()


class TestDMMessageHandler:
    """Test cases for DMMessageHandler class."""

    def test_init(self, mock_bot):
        """Test DMMessageHandler initialization."""
        handler = DMMessageHandler(mock_bot)
        assert handler.bot == mock_bot
        assert hasattr(handler, 'reaction_handler')

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.is_bot_owner')
    async def test_handle_dm_non_command_owner(self, mock_is_owner, mock_bot, mock_ctx):
        """Test DM non-command handling for bot owner."""
        mock_is_owner.return_value = True
        handler = DMMessageHandler(mock_bot)
        handler.reaction_handler.check_and_react = AsyncMock(return_value=False)
        
        # Create a proper mock command with help attribute
        mock_command = MagicMock()
        mock_command.help = "Owner help text"
        mock_bot.get_command.return_value = mock_command

        await handler._handle_dm_non_command(mock_ctx)

        mock_ctx.message.author.send.assert_called()
        mock_ctx.author.send.assert_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.is_bot_owner')
    async def test_handle_dm_non_command_not_owner(self, mock_is_owner, mock_bot, mock_ctx):
        """Test DM non-command handling for non-owner."""
        mock_is_owner.return_value = False
        handler = DMMessageHandler(mock_bot)
        handler.reaction_handler.check_and_react = AsyncMock(return_value=False)

        await handler._handle_dm_non_command(mock_ctx)

        mock_ctx.message.author.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_dm_command_allowed(self, mock_bot, mock_ctx):
        """Test DM command handling for allowed command."""
        mock_bot.settings["bot"]["AllowedDMCommands"] = ["help"]
        handler = DMMessageHandler(mock_bot)
        mock_ctx.message.content = "!help"

        await handler._handle_dm_command(mock_ctx)

        mock_bot.process_commands.assert_called_once_with(mock_ctx.message)

    @pytest.mark.asyncio
    async def test_handle_dm_command_not_allowed(self, mock_bot, mock_ctx):
        """Test DM command handling for not allowed command."""
        mock_bot.settings["bot"]["AllowedDMCommands"] = ["help"]
        handler = DMMessageHandler(mock_bot)
        mock_ctx.message.content = "!ping"

        await handler._handle_dm_command(mock_ctx)

        mock_ctx.message.author.send.assert_called_once()
        mock_bot.process_commands.assert_not_called()


class TestServerMessageHandler:
    """Test cases for ServerMessageHandler class."""

    def test_init(self, mock_bot):
        """Test ServerMessageHandler initialization."""
        handler = ServerMessageHandler(mock_bot)
        assert handler.bot == mock_bot
        assert hasattr(handler, 'profanity_filter')
        assert hasattr(handler, 'reaction_handler')

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ServersDal')
    async def test_process_no_configs(self, mock_dal_class, mock_bot, mock_ctx):
        """Test server message processing with no configs."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = None

        handler = ServerMessageHandler(mock_bot)

        await handler.process(mock_ctx, True)

        mock_bot.log.warning.assert_called_once()
        mock_bot.process_commands.assert_called_once_with(mock_ctx.message)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ServersDal')
    @patch('src.bot.cogs.events.on_message.bot_utils.delete_message')
    async def test_process_invisible_member_blocked(self, mock_delete, mock_dal_class, mock_bot, mock_ctx):
        """Test server message processing with invisible member blocked."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"block_invis_members": True}
        mock_ctx.author.status.name = "offline"

        handler = ServerMessageHandler(mock_bot)

        await handler.process(mock_ctx, False)

        mock_delete.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ServersDal')
    async def test_handle_server_non_command_profanity(self, mock_dal_class, mock_bot, mock_ctx):
        """Test handling server non-command with profanity filter."""
        configs = {"profanity_filter": True, "bot_word_reactions": False}
        handler = ServerMessageHandler(mock_bot)
        handler.profanity_filter.check_and_censor = AsyncMock(return_value=True)

        await handler._handle_server_non_command(mock_ctx, configs)

        handler.profanity_filter.check_and_censor.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.CustomCommandsDal')
    async def test_try_custom_command_found(self, mock_dal_class, mock_bot, mock_ctx):
        """Test trying custom command when found."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_command.return_value = {"description": "Custom command response"}

        handler = ServerMessageHandler(mock_bot)

        result = await handler._try_custom_command(mock_ctx)

        assert result is True
        mock_ctx.message.channel.typing.assert_called_once()
        mock_ctx.message.channel.send.assert_called_once_with("Custom command response")

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.CustomCommandsDal')
    async def test_try_custom_command_not_found(self, mock_dal_class, mock_bot, mock_ctx):
        """Test trying custom command when not found."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_command.return_value = None

        handler = ServerMessageHandler(mock_bot)

        result = await handler._try_custom_command(mock_ctx)

        assert result is False


class TestOnMessage:
    """Test cases for OnMessage cog."""

    def test_init(self, mock_bot):
        """Test OnMessage cog initialization."""
        cog = OnMessage(mock_bot)
        assert cog.bot == mock_bot
        assert hasattr(cog, 'dm_handler')
        assert hasattr(cog, 'server_handler')

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_message import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnMessage)
        assert added_cog.bot == mock_bot

    def test_on_message_cog_inheritance(self, on_message_cog):
        """Test that OnMessage cog properly inherits from commands.Cog."""
        assert isinstance(on_message_cog, commands.Cog)
        assert hasattr(on_message_cog, 'bot')

    def test_message_context_dm_detection(self, mock_dm_ctx):
        """Test MessageContext DM detection."""
        context = MessageContext(mock_dm_ctx, False)
        assert context.is_dm is True

    @pytest.mark.asyncio
    async def test_profanity_filter_log_error(self, mock_bot, mock_ctx):
        """Test profanity filter error logging."""
        filter_obj = ProfanityFilter(mock_bot)
        error = Exception("Test error")

        await filter_obj._log_filter_error(mock_ctx, "test message", error)

        mock_bot.log.info.assert_called_once()
        log_call = mock_bot.log.info.call_args[0][0]
        assert "Test Server" in log_call
        assert "test message" in log_call
        assert "Test error" in log_call

    def test_custom_reaction_handler_has_bot_mention(self, mock_bot):
        """Test custom reaction handler bot mention detection."""
        mock_bot.user.mention = "<@123456789>"
        handler = CustomReactionHandler(mock_bot)

        message = MagicMock()
        result = handler._has_bot_mention(message, "hello bot world")
        assert result is True

        result = handler._has_bot_mention(message, "hello world")
        assert result is False

    @pytest.mark.asyncio
    async def test_dm_handler_send_owner_help(self, mock_bot, mock_ctx):
        """Test DM handler sending owner help."""
        handler = DMMessageHandler(mock_bot)
        mock_owner_cmd = MagicMock()
        mock_owner_cmd.help = "Owner command help"
        mock_bot.get_command.return_value = mock_owner_cmd

        await handler._send_owner_help(mock_ctx)

        # Since ctx.message.author and ctx.author are the same object,
        # both calls go to the same send method, so call_count should be 2
        assert mock_ctx.message.author.send.call_count == 2
        assert mock_ctx.author.send.call_count == 2
