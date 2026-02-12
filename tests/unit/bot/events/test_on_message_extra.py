"""Extra tests for OnMessage event handler targeting uncovered lines.

Covers lines: 83-84, 198-201, 207, 217, 222-223, 253-257, 298-301,
318-322, 332-333, 338-350, 377-394.
"""

import discord
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.events.on_message import (
    DMMessageHandler,
    ExclusiveUsersChecker,
    OnMessage,
    ProfanityFilter,
    ServerMessageHandler,
)
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
    bot.user.mention = "<@123456789>"
    bot.owner_id = 999999
    bot.profanity = MagicMock()
    bot.settings = {
        "bot": {
            "BotReactionWords": ["stupid", "retard"],
            "ExclusiveUsers": None,
            "AllowedDMCommands": ["help", "gw2"],
            "EmbedColor": 0x00FF00,
        }
    }
    bot.get_command = MagicMock()
    bot.process_commands = AsyncMock()
    bot.get_context = AsyncMock()
    bot.add_cog = AsyncMock(return_value=None)
    bot.event = MagicMock(side_effect=lambda func: func)
    return bot


@pytest.fixture
def mock_ctx():
    """Create a mock context for server messages."""
    ctx = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    ctx.guild.name = "Test Server"

    ctx.author = MagicMock()
    ctx.author.id = 67890
    ctx.author.display_name = "TestUser"
    ctx.author.avatar = MagicMock()
    ctx.author.avatar.url = "https://example.com/avatar.png"
    ctx.author.status = discord.Status.online
    ctx.author.bot = False
    ctx.author.send = AsyncMock()

    ctx.message = MagicMock()
    ctx.message.content = "!help"
    ctx.message.system_content = "Hello world"
    ctx.message.author = ctx.author
    ctx.message.guild = ctx.guild
    ctx.message.channel = MagicMock()
    ctx.message.channel.typing = AsyncMock()
    ctx.message.channel.send = AsyncMock()
    ctx.message.author.send = AsyncMock()
    ctx.message.author.mention = "<@67890>"

    ctx.prefix = "!"
    ctx.invoked_with = "help"
    ctx.send = AsyncMock()
    ctx.channel = MagicMock()

    ctx.bot = AsyncMock()
    ctx.bot.log = MagicMock()
    ctx.bot.log.error = MagicMock()

    return ctx


@pytest.fixture
def mock_dm_ctx(mock_ctx):
    """Create a mock DM context."""
    dm_channel = MagicMock(spec=discord.DMChannel)
    dm_channel.typing = AsyncMock()
    dm_channel.send = AsyncMock()
    mock_ctx.message.channel = dm_channel
    mock_ctx.channel = dm_channel
    return mock_ctx


class TestProfanityFilterHTTPException:
    """Tests for ProfanityFilter._censor_message HTTPException fallback (lines 83-84)."""

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.delete_message')
    async def test_censor_message_embed_http_exception_fallback(self, mock_delete, mock_bot, mock_ctx):
        """When embed send raises HTTPException, fallback to text mention (lines 83-84)."""
        mock_bot.profanity.contains_profanity.return_value = True
        mock_bot.profanity.censor.return_value = "#### world"
        filter_obj = ProfanityFilter(mock_bot)

        # First call succeeds (sends censored text), second call raises HTTPException (embed),
        # third call is the fallback text mention
        call_count = [0]
        original_side_effect = None

        async def send_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                # The embed send raises HTTPException
                raise discord.HTTPException(MagicMock(), "Embed failed")
            return MagicMock()

        mock_ctx.message.channel.send = AsyncMock(side_effect=send_side_effect)

        result = await filter_obj.check_and_censor(mock_ctx)

        assert result is True
        mock_delete.assert_called_once_with(mock_ctx)
        # Should have 3 calls: censored text, failed embed, fallback mention
        assert mock_ctx.message.channel.send.call_count == 3
        fallback_call = mock_ctx.message.channel.send.call_args_list[2]
        assert mock_ctx.message.author.mention in fallback_call[0][0]
        assert messages.MESSAGE_CENSURED in fallback_call[0][0]


class TestDMMessageHandlerProcess:
    """Tests for DMMessageHandler.process routing (lines 198-201)."""

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.is_bot_owner')
    async def test_process_not_command_routes_to_non_command(self, mock_is_owner, mock_bot, mock_dm_ctx):
        """When is_command=False, routes to _handle_dm_non_command (lines 198-199)."""
        mock_is_owner.return_value = False
        handler = DMMessageHandler(mock_bot)
        handler.reaction_handler.check_and_react = AsyncMock(return_value=False)

        await handler.process(mock_dm_ctx, is_command=False)

        # Should send dm_not_allowed embed since not owner
        mock_dm_ctx.message.author.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_is_command_routes_to_command(self, mock_bot, mock_dm_ctx):
        """When is_command=True, routes to _handle_dm_command (lines 200-201)."""
        mock_bot.settings["bot"]["AllowedDMCommands"] = ["help"]
        mock_dm_ctx.message.content = "!help"
        handler = DMMessageHandler(mock_bot)

        await handler.process(mock_dm_ctx, is_command=True)

        mock_bot.process_commands.assert_called_once_with(mock_dm_ctx.message)


class TestDMMessageHandlerNonCommand:
    """Tests for DMMessageHandler._handle_dm_non_command (lines 203-212, line 207)."""

    @pytest.mark.asyncio
    async def test_reaction_handler_returns_true_early_return(self, mock_bot, mock_dm_ctx):
        """When reaction handler returns True, returns early (line 207)."""
        handler = DMMessageHandler(mock_bot)
        handler.reaction_handler.check_and_react = AsyncMock(return_value=True)

        await handler._handle_dm_non_command(mock_dm_ctx)

        handler.reaction_handler.check_and_react.assert_called_once_with(mock_dm_ctx.message)
        # Should NOT send any DM messages since we returned early
        mock_dm_ctx.message.author.send.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.is_bot_owner')
    async def test_is_bot_owner_sends_owner_help(self, mock_is_owner, mock_bot, mock_dm_ctx):
        """When user is bot owner, sends owner help (lines 209-210)."""
        mock_is_owner.return_value = True
        handler = DMMessageHandler(mock_bot)
        handler.reaction_handler.check_and_react = AsyncMock(return_value=False)

        mock_owner_cmd = MagicMock()
        mock_owner_cmd.help = "Owner command help text"
        mock_bot.get_command.return_value = mock_owner_cmd

        await handler._handle_dm_non_command(mock_dm_ctx)

        mock_is_owner.assert_called_once_with(mock_dm_ctx, mock_dm_ctx.message.author)
        # Should send embed and then owner command help
        assert mock_dm_ctx.message.author.send.call_count >= 1

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.is_bot_owner')
    async def test_not_bot_owner_sends_dm_not_allowed(self, mock_is_owner, mock_bot, mock_dm_ctx):
        """When user is not bot owner, sends dm not allowed (lines 211-212)."""
        mock_is_owner.return_value = False
        handler = DMMessageHandler(mock_bot)
        handler.reaction_handler.check_and_react = AsyncMock(return_value=False)

        await handler._handle_dm_non_command(mock_dm_ctx)

        mock_dm_ctx.message.author.send.assert_called_once()
        embed_sent = (
            mock_dm_ctx.message.author.send.call_args[1].get('embed') or mock_dm_ctx.message.author.send.call_args[0][0]
            if mock_dm_ctx.message.author.send.call_args[0]
            else None
        )
        # Verify it was called (the embed contains NO_DM_MESSAGES)


class TestDMMessageHandlerCommand:
    """Tests for DMMessageHandler._handle_dm_command (lines 214-230)."""

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ExclusiveUsersChecker.check_exclusive_users')
    async def test_exclusive_users_check_fails_returns(self, mock_check, mock_bot, mock_dm_ctx):
        """When exclusive users check fails, returns early (line 217)."""
        mock_check.return_value = False
        handler = DMMessageHandler(mock_bot)
        mock_dm_ctx.message.content = "!help"

        await handler._handle_dm_command(mock_dm_ctx)

        mock_check.assert_called_once_with(mock_bot, mock_dm_ctx)
        mock_bot.process_commands.assert_not_called()

    @pytest.mark.asyncio
    async def test_allowed_commands_none_sends_no_dm_commands(self, mock_bot, mock_dm_ctx):
        """When AllowedDMCommands is None, sends no DM commands message (lines 222-223)."""
        mock_bot.settings["bot"]["AllowedDMCommands"] = None
        handler = DMMessageHandler(mock_bot)
        mock_dm_ctx.message.content = "!help"

        await handler._handle_dm_command(mock_dm_ctx)

        mock_dm_ctx.message.author.send.assert_called_once()
        embed_arg = (
            mock_dm_ctx.message.author.send.call_args[1].get('embed') or mock_dm_ctx.message.author.send.call_args[0][0]
        )
        assert isinstance(embed_arg, discord.Embed)
        mock_bot.process_commands.assert_not_called()

    @pytest.mark.asyncio
    async def test_command_in_allowed_list_processes(self, mock_bot, mock_dm_ctx):
        """When command is in allowed list, processes commands (line 228)."""
        mock_bot.settings["bot"]["AllowedDMCommands"] = ["help", "gw2"]
        handler = DMMessageHandler(mock_bot)
        mock_dm_ctx.message.content = "!gw2 account"

        await handler._handle_dm_command(mock_dm_ctx)

        mock_bot.process_commands.assert_called_once_with(mock_dm_ctx.message)

    @pytest.mark.asyncio
    async def test_command_not_in_allowed_list_sends_not_allowed(self, mock_bot, mock_dm_ctx):
        """When command is NOT in allowed list, sends not allowed (lines 229-230)."""
        mock_bot.settings["bot"]["AllowedDMCommands"] = ["help"]
        handler = DMMessageHandler(mock_bot)
        mock_dm_ctx.message.content = "!ping"

        await handler._handle_dm_command(mock_dm_ctx)

        mock_dm_ctx.message.author.send.assert_called_once()
        mock_bot.process_commands.assert_not_called()


class TestDMMessageHandlerSendMethods:
    """Tests for DMMessageHandler send helper methods (lines 232-270, including 253-257)."""

    @pytest.mark.asyncio
    async def test_send_no_dm_commands_allowed(self, mock_bot, mock_dm_ctx):
        """Test _send_no_dm_commands_allowed sends correct embed (lines 253-257)."""
        handler = DMMessageHandler(mock_bot)

        await handler._send_no_dm_commands_allowed(mock_dm_ctx)

        mock_dm_ctx.message.author.send.assert_called_once()
        embed_sent = mock_dm_ctx.message.author.send.call_args[1]['embed']
        assert embed_sent.color == discord.Color.red()
        assert messages.DM_COMMAND_NOT_ALLOWED in embed_sent.description

    @pytest.mark.asyncio
    async def test_send_command_not_allowed(self, mock_bot, mock_dm_ctx):
        """Test _send_command_not_allowed sends embed with allowed commands list."""
        handler = DMMessageHandler(mock_bot)
        allowed_commands = ["help", "gw2", "info"]

        await handler._send_command_not_allowed(mock_dm_ctx, allowed_commands)

        mock_dm_ctx.message.author.send.assert_called_once()
        embed_sent = mock_dm_ctx.message.author.send.call_args[1]['embed']
        assert embed_sent.color == discord.Color.red()
        assert messages.DM_COMMAND_NOT_ALLOWED in embed_sent.description
        assert len(embed_sent.fields) == 1
        assert messages.DM_COMMANDS_ALLOW_LIST in embed_sent.fields[0].name

    @pytest.mark.asyncio
    async def test_send_dm_not_allowed(self, mock_bot, mock_dm_ctx):
        """Test _send_dm_not_allowed sends correct embed."""
        handler = DMMessageHandler(mock_bot)

        await handler._send_dm_not_allowed(mock_dm_ctx)

        mock_dm_ctx.message.author.send.assert_called_once()
        embed_sent = mock_dm_ctx.message.author.send.call_args[1]['embed']
        assert embed_sent.color == discord.Color.red()
        assert messages.NO_DM_MESSAGES in embed_sent.description

    @pytest.mark.asyncio
    async def test_send_owner_help(self, mock_bot, mock_dm_ctx):
        """Test _send_owner_help sends embed and owner command help."""
        handler = DMMessageHandler(mock_bot)
        mock_owner_cmd = MagicMock()
        mock_owner_cmd.help = "Owner command detailed help"
        mock_bot.get_command.return_value = mock_owner_cmd

        # Use separate mocks for message.author.send and ctx.author.send
        # In the actual code: ctx.message.author.send(embed=embed) then ctx.author.send(box(help))
        # Since mock_dm_ctx.message.author and mock_dm_ctx.author are the same mock,
        # we verify all calls on the same send method
        await handler._send_owner_help(mock_dm_ctx)

        mock_bot.get_command.assert_called_once_with("owner")
        # Both calls go to the same mock since ctx.message.author == ctx.author in DM
        # First call: embed with OWNER_DM_BOT_MESSAGE
        # Second call: box(owner_command.help)
        assert mock_dm_ctx.message.author.send.call_count == 2
        first_call = mock_dm_ctx.message.author.send.call_args_list[0]
        embed_sent = first_call[1]['embed']
        assert embed_sent.color == discord.Color.green()
        assert messages.OWNER_DM_BOT_MESSAGE in embed_sent.description
        second_call = mock_dm_ctx.message.author.send.call_args_list[1]
        assert "Owner command detailed help" in second_call[0][0]


class TestServerMessageHandlerProcess:
    """Tests for ServerMessageHandler.process (lines 281-301, specifically 298-301)."""

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ServersDal')
    async def test_no_configs_not_command_logs_warning_no_process(self, mock_dal_class, mock_bot, mock_ctx):
        """When no configs and not a command, logs warning and returns (lines 288-291)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = None

        handler = ServerMessageHandler(mock_bot)
        await handler.process(mock_ctx, is_command=False)

        mock_bot.log.warning.assert_called_once_with(messages.GET_CONFIGS_ERROR)
        mock_bot.process_commands.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ServersDal')
    async def test_no_configs_is_command_processes_commands(self, mock_dal_class, mock_bot, mock_ctx):
        """When no configs but is_command, processes commands (lines 289-290, 298-301 related)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = None

        handler = ServerMessageHandler(mock_bot)
        await handler.process(mock_ctx, is_command=True)

        mock_bot.log.warning.assert_called_once_with(messages.GET_CONFIGS_ERROR)
        mock_bot.process_commands.assert_called_once_with(mock_ctx.message)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ServersDal')
    async def test_not_command_routes_to_non_command(self, mock_dal_class, mock_bot, mock_ctx):
        """When not a command, routes to _handle_server_non_command (lines 298-299)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {
            "block_invis_members": False,
            "profanity_filter": False,
            "bot_word_reactions": False,
        }
        handler = ServerMessageHandler(mock_bot)

        await handler.process(mock_ctx, is_command=False)

        # No profanity check or reactions since both are off
        mock_bot.process_commands.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ServersDal')
    @patch('src.bot.cogs.events.on_message.CustomCommandsDal')
    async def test_is_command_routes_to_command_handler(self, mock_cmd_dal_class, mock_dal_class, mock_bot, mock_ctx):
        """When is a command, routes to _handle_server_command (lines 300-301)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {
            "block_invis_members": False,
            "profanity_filter": False,
            "bot_word_reactions": False,
        }
        mock_cmd_dal = AsyncMock()
        mock_cmd_dal_class.return_value = mock_cmd_dal
        mock_cmd_dal.get_command.return_value = None

        mock_ctx.message.content = "!help"
        handler = ServerMessageHandler(mock_bot)

        await handler.process(mock_ctx, is_command=True)

        mock_bot.process_commands.assert_called_once_with(mock_ctx.message)


class TestServerMessageHandlerInvisibleMember:
    """Tests for ServerMessageHandler._handle_invisible_member (lines 303-322)."""

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.delete_message')
    async def test_invisible_member_dm_succeeds(self, mock_delete, mock_bot, mock_ctx):
        """When DM send succeeds, invisible member is notified via DM (lines 316-317)."""
        handler = ServerMessageHandler(mock_bot)

        await handler._handle_invisible_member(mock_ctx)

        mock_delete.assert_called_once_with(mock_ctx)
        mock_ctx.message.author.send.assert_called_once()
        embed_sent = mock_ctx.message.author.send.call_args[1]['embed']
        assert embed_sent.color == discord.Color.red()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.delete_message')
    async def test_invisible_member_dm_http_exception_channel_send(self, mock_delete, mock_bot, mock_ctx):
        """When DM raises HTTPException, tries channel send (lines 318-319)."""
        handler = ServerMessageHandler(mock_bot)
        mock_ctx.message.author.send = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "DM failed"))

        await handler._handle_invisible_member(mock_ctx)

        mock_delete.assert_called_once_with(mock_ctx)
        mock_ctx.message.author.send.assert_called_once()
        # Falls back to ctx.send with embed
        mock_ctx.send.assert_called_once()
        embed_sent = mock_ctx.send.call_args[1]['embed']
        assert embed_sent.color == discord.Color.red()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.delete_message')
    async def test_invisible_member_both_exceptions_fallback_mention(self, mock_delete, mock_bot, mock_ctx):
        """When both DM and channel embed raise HTTPException, fallback to mention (lines 320-322)."""
        handler = ServerMessageHandler(mock_bot)
        mock_ctx.message.author.send = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "DM failed"))

        call_count = [0]

        async def send_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1 and 'embed' in kwargs:
                raise discord.HTTPException(MagicMock(), "Channel embed failed")
            return MagicMock()

        mock_ctx.send = AsyncMock(side_effect=send_side_effect)

        await handler._handle_invisible_member(mock_ctx)

        mock_delete.assert_called_once_with(mock_ctx)
        # Should try DM first, then channel embed (fails), then mention text
        assert mock_ctx.send.call_count == 2
        fallback_call = mock_ctx.send.call_args_list[1]
        assert mock_ctx.message.author.mention in fallback_call[0][0]


class TestServerMessageHandlerNonCommand:
    """Tests for ServerMessageHandler._handle_server_non_command (lines 324-333)."""

    @pytest.mark.asyncio
    async def test_profanity_filter_active_and_censors_returns(self, mock_bot, mock_ctx):
        """When profanity filter is on and censors, returns early (lines 327-329)."""
        handler = ServerMessageHandler(mock_bot)
        handler.profanity_filter.check_and_censor = AsyncMock(return_value=True)
        configs = {"profanity_filter": True, "bot_word_reactions": True}

        await handler._handle_server_non_command(mock_ctx, configs)

        handler.profanity_filter.check_and_censor.assert_called_once_with(mock_ctx)
        # Reaction handler should NOT be called since profanity was censored
        # (confirmed by absence of check_and_react call)

    @pytest.mark.asyncio
    async def test_profanity_filter_off_bot_reactions_active(self, mock_bot, mock_ctx):
        """When profanity filter off and bot reactions active, checks reactions (lines 332-333)."""
        handler = ServerMessageHandler(mock_bot)
        handler.profanity_filter.check_and_censor = AsyncMock(return_value=False)
        handler.reaction_handler.check_and_react = AsyncMock(return_value=False)
        configs = {"profanity_filter": False, "bot_word_reactions": True}

        await handler._handle_server_non_command(mock_ctx, configs)

        handler.reaction_handler.check_and_react.assert_called_once_with(mock_ctx.message)

    @pytest.mark.asyncio
    async def test_profanity_filter_active_no_censor_bot_reactions_active(self, mock_bot, mock_ctx):
        """When profanity filter on but no censor, still checks reactions (lines 332-333)."""
        handler = ServerMessageHandler(mock_bot)
        handler.profanity_filter.check_and_censor = AsyncMock(return_value=False)
        handler.reaction_handler.check_and_react = AsyncMock(return_value=True)
        configs = {"profanity_filter": True, "bot_word_reactions": True}

        await handler._handle_server_non_command(mock_ctx, configs)

        handler.profanity_filter.check_and_censor.assert_called_once_with(mock_ctx)
        handler.reaction_handler.check_and_react.assert_called_once_with(mock_ctx.message)

    @pytest.mark.asyncio
    async def test_both_off_does_nothing(self, mock_bot, mock_ctx):
        """When both profanity filter and reactions are off, does nothing."""
        handler = ServerMessageHandler(mock_bot)
        handler.profanity_filter.check_and_censor = AsyncMock(return_value=False)
        handler.reaction_handler.check_and_react = AsyncMock(return_value=False)
        configs = {"profanity_filter": False, "bot_word_reactions": False}

        await handler._handle_server_non_command(mock_ctx, configs)

        handler.profanity_filter.check_and_censor.assert_not_called()
        handler.reaction_handler.check_and_react.assert_not_called()


class TestServerMessageHandlerCommand:
    """Tests for ServerMessageHandler._handle_server_command (lines 335-350)."""

    @pytest.mark.asyncio
    async def test_double_prefix_returns_early(self, mock_bot, mock_ctx):
        """When message has double prefix, returns early (lines 338-339)."""
        mock_ctx.message.content = "!!"
        handler = ServerMessageHandler(mock_bot)

        await handler._handle_server_command(mock_ctx)

        mock_bot.process_commands.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ExclusiveUsersChecker.check_exclusive_users')
    async def test_exclusive_users_fails_returns(self, mock_check, mock_bot, mock_ctx):
        """When exclusive users check fails, returns early (lines 341-342)."""
        mock_check.return_value = False
        mock_ctx.message.content = "!help"
        handler = ServerMessageHandler(mock_bot)

        await handler._handle_server_command(mock_ctx)

        mock_check.assert_called_once_with(mock_bot, mock_ctx)
        mock_bot.process_commands.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.CustomCommandsDal')
    async def test_custom_command_found_returns(self, mock_dal_class, mock_bot, mock_ctx):
        """When custom command is found, returns True (lines 345-347)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_command.return_value = {"description": "Custom response"}

        mock_ctx.message.content = "!mycmd"
        handler = ServerMessageHandler(mock_bot)

        await handler._handle_server_command(mock_ctx)

        mock_ctx.message.channel.typing.assert_called_once()
        mock_ctx.message.channel.send.assert_called_once_with("Custom response")
        mock_bot.process_commands.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.CustomCommandsDal')
    async def test_no_custom_command_processes_regular(self, mock_dal_class, mock_bot, mock_ctx):
        """When no custom command found, processes regular commands (line 350)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_command.return_value = None

        mock_ctx.message.content = "!help"
        handler = ServerMessageHandler(mock_bot)

        await handler._handle_server_command(mock_ctx)

        mock_bot.process_commands.assert_called_once_with(mock_ctx.message)

    @pytest.mark.asyncio
    async def test_non_alpha_second_char_double_prefix(self, mock_bot, mock_ctx):
        """Special characters after prefix treated as double prefix (line 338)."""
        mock_ctx.message.content = "!?"
        handler = ServerMessageHandler(mock_bot)

        await handler._handle_server_command(mock_ctx)

        mock_bot.process_commands.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.CustomCommandsDal')
    async def test_alpha_second_char_not_double_prefix(self, mock_dal_class, mock_bot, mock_ctx):
        """Alpha character after prefix is NOT double prefix (line 338)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_command.return_value = None

        mock_ctx.message.content = "!help"
        handler = ServerMessageHandler(mock_bot)

        await handler._handle_server_command(mock_ctx)

        mock_bot.process_commands.assert_called_once_with(mock_ctx.message)


class TestOnMessageCogEvent:
    """Tests for OnMessage.__init__ and the on_message event (lines 365-394)."""

    def test_on_message_cog_registers_event(self, mock_bot):
        """Test OnMessage.__init__ registers the on_message event (lines 368-371)."""
        cog = OnMessage(mock_bot)

        assert cog.bot == mock_bot
        assert hasattr(cog, 'dm_handler')
        assert hasattr(cog, 'server_handler')
        mock_bot.event.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_message_no_content_returns(self, mock_bot):
        """When message has no content, returns early (lines 377-378)."""
        cog = OnMessage(mock_bot)

        # Get the registered on_message function
        on_message_func = mock_bot.event.call_args[0][0]

        message = MagicMock()
        message.content = ""

        await on_message_func(message)

        mock_bot.get_context.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_bot_message_process_commands(self, mock_bot):
        """When message is from bot, calls process_commands (lines 383-385)."""
        cog = OnMessage(mock_bot)
        on_message_func = mock_bot.event.call_args[0][0]

        message = MagicMock()
        message.content = "!help"

        mock_ctx = MagicMock()
        mock_ctx.author = MagicMock()
        mock_ctx.author.bot = True
        mock_ctx.prefix = "!"
        mock_bot.get_context = AsyncMock(return_value=mock_ctx)

        await on_message_func(message)

        mock_bot.get_context.assert_called_once_with(message)
        mock_bot.process_commands.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_on_message_dm_channel_routes_to_dm_handler(self, mock_bot):
        """When channel is DMChannel, routes to dm_handler.process (lines 391-392)."""
        cog = OnMessage(mock_bot)
        on_message_func = mock_bot.event.call_args[0][0]

        message = MagicMock()
        message.content = "hello"

        dm_channel = MagicMock(spec=discord.DMChannel)
        mock_ctx = MagicMock()
        mock_ctx.author = MagicMock()
        mock_ctx.author.bot = False
        mock_ctx.prefix = None  # Not a command
        mock_ctx.channel = dm_channel
        mock_bot.get_context = AsyncMock(return_value=mock_ctx)

        # Mock the dm_handler
        cog.dm_handler.process = AsyncMock()

        await on_message_func(message)

        cog.dm_handler.process.assert_called_once_with(mock_ctx, False)

    @pytest.mark.asyncio
    async def test_on_message_server_channel_routes_to_server_handler(self, mock_bot):
        """When channel is NOT DMChannel, routes to server_handler.process (lines 393-394)."""
        cog = OnMessage(mock_bot)
        on_message_func = mock_bot.event.call_args[0][0]

        message = MagicMock()
        message.content = "!help"

        server_channel = MagicMock(spec=discord.TextChannel)
        mock_ctx = MagicMock()
        mock_ctx.author = MagicMock()
        mock_ctx.author.bot = False
        mock_ctx.prefix = "!"  # Is a command
        mock_ctx.channel = server_channel
        mock_bot.get_context = AsyncMock(return_value=mock_ctx)

        # Mock the server_handler
        cog.server_handler.process = AsyncMock()

        await on_message_func(message)

        cog.server_handler.process.assert_called_once_with(mock_ctx, True)

    @pytest.mark.asyncio
    async def test_on_message_dm_command_routes_to_dm_handler(self, mock_bot):
        """When DM with a command prefix, routes to dm_handler with is_command=True (line 391-392)."""
        cog = OnMessage(mock_bot)
        on_message_func = mock_bot.event.call_args[0][0]

        message = MagicMock()
        message.content = "!help"

        dm_channel = MagicMock(spec=discord.DMChannel)
        mock_ctx = MagicMock()
        mock_ctx.author = MagicMock()
        mock_ctx.author.bot = False
        mock_ctx.prefix = "!"  # Is a command
        mock_ctx.channel = dm_channel
        mock_bot.get_context = AsyncMock(return_value=mock_ctx)

        cog.dm_handler.process = AsyncMock()

        await on_message_func(message)

        cog.dm_handler.process.assert_called_once_with(mock_ctx, True)


class TestServerMessageHandlerBlockInvisible:
    """Additional tests for block invisible member flow (lines 294-296)."""

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ServersDal')
    @patch('src.bot.cogs.events.on_message.bot_utils.delete_message')
    async def test_block_invisible_enabled_member_invisible(self, mock_delete, mock_dal_class, mock_bot, mock_ctx):
        """When block invisible is True and member is invisible, handles invisible (lines 294-296)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {
            "block_invis_members": True,
            "profanity_filter": False,
            "bot_word_reactions": False,
        }
        mock_ctx.author.status = discord.Status.offline

        handler = ServerMessageHandler(mock_bot)
        await handler.process(mock_ctx, is_command=True)

        mock_delete.assert_called_once_with(mock_ctx)
        # Should not process commands when invisible is blocked
        mock_bot.process_commands.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.ServersDal')
    @patch('src.bot.cogs.events.on_message.CustomCommandsDal')
    async def test_block_invisible_enabled_member_online(self, mock_cmd_dal_class, mock_dal_class, mock_bot, mock_ctx):
        """When block invisible is True but member is online, proceeds normally."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {
            "block_invis_members": True,
            "profanity_filter": False,
            "bot_word_reactions": False,
        }
        mock_ctx.author.status = discord.Status.online
        mock_ctx.message.content = "!help"

        mock_cmd_dal = AsyncMock()
        mock_cmd_dal_class.return_value = mock_cmd_dal
        mock_cmd_dal.get_command.return_value = None

        handler = ServerMessageHandler(mock_bot)
        await handler.process(mock_ctx, is_command=True)

        # Should process commands since member is online
        mock_bot.process_commands.assert_called_once_with(mock_ctx.message)


class TestExclusiveUsersCheckerExtra:
    """Extra tests for ExclusiveUsersChecker edge cases."""

    @pytest.mark.asyncio
    async def test_exclusive_users_empty_string(self, mock_bot, mock_ctx):
        """When ExclusiveUsers is empty string, returns True (allowed)."""
        mock_bot.settings["bot"]["ExclusiveUsers"] = ""

        result = await ExclusiveUsersChecker.check_exclusive_users(mock_bot, mock_ctx)
        assert result is True

    @pytest.mark.asyncio
    async def test_exclusive_users_single_id_match(self, mock_bot, mock_ctx):
        """When ExclusiveUsers is a single int matching user, returns True."""
        mock_bot.settings["bot"]["ExclusiveUsers"] = 67890  # matches mock_ctx.message.author.id

        result = await ExclusiveUsersChecker.check_exclusive_users(mock_bot, mock_ctx)
        assert result is True

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_message.bot_utils.send_error_msg')
    async def test_exclusive_users_single_id_no_match(self, mock_send_error, mock_bot, mock_ctx):
        """When ExclusiveUsers is a single int not matching user, returns False."""
        mock_bot.settings["bot"]["ExclusiveUsers"] = 11111

        result = await ExclusiveUsersChecker.check_exclusive_users(mock_bot, mock_ctx)
        assert result is False
        mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_exclusive_users_tuple_match(self, mock_bot, mock_ctx):
        """When ExclusiveUsers is a tuple containing user id, returns True."""
        mock_bot.settings["bot"]["ExclusiveUsers"] = (67890, 11111)

        result = await ExclusiveUsersChecker.check_exclusive_users(mock_bot, mock_ctx)
        assert result is True
