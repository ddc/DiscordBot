"""Comprehensive tests for the CustomCommand cog."""

import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from discord.ext import commands
from datetime import datetime

# Mock problematic imports before importing the module
import sys
sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.admin.custom_cmd import CustomCommand
from src.bot.constants import messages


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.db_session = MagicMock()
    bot.log = MagicMock()
    bot.commands = []
    # Configure remove_command to not return a coroutine
    bot.remove_command = MagicMock(return_value=None)
    # Ensure add_cog doesn't return a coroutine
    bot.add_cog = AsyncMock(return_value=None)
    return bot


@pytest.fixture
def custom_cmd_cog(mock_bot):
    """Create a CustomCommand cog instance."""
    return CustomCommand(mock_bot)


@pytest.fixture
def mock_ctx():
    """Create a mock context."""
    ctx = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    ctx.guild.name = "Test Server"
    ctx.guild.icon = MagicMock()
    ctx.guild.icon.url = "http://example.com/icon.png"
    
    author = MagicMock()
    author.id = 67890
    author.display_name = "TestUser"
    
    ctx.author = author
    ctx.message = MagicMock()
    ctx.prefix = "!"
    
    # Mock bot commands
    mock_command = MagicMock()
    mock_command.name = "help"
    ctx.bot = MagicMock()
    ctx.bot.commands = [mock_command]
    
    return ctx


@pytest.fixture
def mock_command_data():
    """Create mock command data."""
    hello_cmd = MagicMock()
    hello_cmd.name = "hello"
    hello_cmd.created_by = 67890
    hello_cmd.created_at = datetime.now()
    
    rules_cmd = MagicMock()
    rules_cmd.name = "rules"
    rules_cmd.created_by = 11111
    rules_cmd.created_at = datetime.now()
    
    return [hello_cmd, rules_cmd]


class TestCustomCommand:
    """Test cases for CustomCommand cog."""
    
    def test_init(self, mock_bot):
        """Test CustomCommand cog initialization."""
        cog = CustomCommand(mock_bot)
        assert cog.bot == mock_bot
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.invoke_subcommand')
    async def test_custom_command_group(self, mock_invoke, custom_cmd_cog, mock_ctx):
        """Test custom_command group command."""
        mock_invoke.return_value = "mock_command"
        
        from src.bot.cogs.admin.custom_cmd import custom_command
        result = await custom_command(mock_ctx)
        
        mock_invoke.assert_called_once_with(mock_ctx, "admin cc")
        assert result == "mock_command"
    
    # Test add command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_msg')
    async def test_add_custom_command_success(self, mock_send_msg, mock_delete_msg, 
                                            mock_dal_class, custom_cmd_cog, mock_ctx):
        """Test successful custom command addition."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_command.return_value = None  # Command doesn't exist
        
        from src.bot.cogs.admin.custom_cmd import add_custom_command
        await add_custom_command(mock_ctx, subcommand_passed="hello Hello there!")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_dal.get_command.assert_called_once_with(12345, "hello")
        mock_dal.insert_command.assert_called_once_with(12345, 67890, "hello", "Hello there!")
        mock_send_msg.assert_called_once()
        
        success_msg = mock_send_msg.call_args[0][1]
        assert messages.CUSTOM_COMMAND_ADDED in success_msg
        assert "!hello" in success_msg
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg')
    async def test_add_custom_command_missing_args(self, mock_send_error, mock_delete_msg, 
                                                 custom_cmd_cog, mock_ctx):
        """Test add command with missing arguments."""
        from src.bot.cogs.admin.custom_cmd import add_custom_command
        await add_custom_command(mock_ctx, subcommand_passed="hello")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_send_error.assert_called_once()
        
        error_msg = mock_send_error.call_args[0][1]
        assert messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE in error_msg
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg')
    async def test_add_custom_command_name_too_long(self, mock_send_error, mock_delete_msg, 
                                                   custom_cmd_cog, mock_ctx):
        """Test add command with name too long."""
        long_name = "a" * 21  # 21 characters, exceeds limit of 20
        
        from src.bot.cogs.admin.custom_cmd import add_custom_command
        await add_custom_command(mock_ctx, subcommand_passed=f"{long_name} Some description")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_send_error.assert_called_once_with(mock_ctx, messages.COMMAND_LENGHT_ERROR)
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg')
    async def test_add_custom_command_conflicts_with_bot_command(self, mock_send_error, mock_delete_msg, 
                                                               custom_cmd_cog, mock_ctx):
        """Test add command that conflicts with existing bot command."""
        from src.bot.cogs.admin.custom_cmd import add_custom_command
        await add_custom_command(mock_ctx, subcommand_passed="help Some description")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_send_error.assert_called_once()
        
        error_msg = mock_send_error.call_args[0][1]
        assert messages.ALREADY_A_STANDARD_COMMAND in error_msg
        assert "!help" in error_msg
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_warning_msg')
    async def test_add_custom_command_already_exists(self, mock_send_warning, mock_delete_msg, 
                                                   mock_dal_class, custom_cmd_cog, mock_ctx):
        """Test add command that already exists."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_command.return_value = {"name": "hello"}  # Command exists
        
        from src.bot.cogs.admin.custom_cmd import add_custom_command
        await add_custom_command(mock_ctx, subcommand_passed="hello Hello there!")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_send_warning.assert_called_once()
        
        warning_msg = mock_send_warning.call_args[0][1]
        assert messages.COMMAND_ALREADY_EXISTS in warning_msg
        assert "!hello" in warning_msg
        assert "admin cc edit hello" in warning_msg
    
    # Test edit command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_msg')
    async def test_edit_custom_command_success(self, mock_send_msg, mock_delete_msg, 
                                             mock_dal_class, custom_cmd_cog, mock_ctx, mock_command_data):
        """Test successful custom command editing."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = mock_command_data
        
        from src.bot.cogs.admin.custom_cmd import edit_custom_command
        await edit_custom_command(mock_ctx, subcommand_passed="hello Updated greeting!")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_dal.get_all_server_commands.assert_called_once_with(12345)
        mock_dal.update_command_description.assert_called_once_with(12345, 67890, "hello", "Updated greeting!")
        mock_send_msg.assert_called_once()
        
        success_msg = mock_send_msg.call_args[0][1]
        assert messages.CUSTOM_COMMAND_EDITED in success_msg
        assert "!hello" in success_msg
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg')
    async def test_edit_custom_command_missing_args(self, mock_send_error, mock_delete_msg, 
                                                   custom_cmd_cog, mock_ctx):
        """Test edit command with missing arguments."""
        from src.bot.cogs.admin.custom_cmd import edit_custom_command
        await edit_custom_command(mock_ctx, subcommand_passed="hello")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_send_error.assert_called_once()
        
        error_msg = mock_send_error.call_args[0][1]
        assert messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE in error_msg
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg')
    async def test_edit_custom_command_no_commands_exist(self, mock_send_error, mock_delete_msg, 
                                                       mock_dal_class, custom_cmd_cog, mock_ctx):
        """Test edit command when no custom commands exist."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = []
        
        from src.bot.cogs.admin.custom_cmd import edit_custom_command
        await edit_custom_command(mock_ctx, subcommand_passed="hello Updated greeting!")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_send_error.assert_called_once_with(mock_ctx, messages.NO_CUSTOM_COMMANDS_FOUND)
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg')
    async def test_edit_custom_command_not_found(self, mock_send_error, mock_delete_msg, 
                                                mock_dal_class, custom_cmd_cog, mock_ctx, mock_command_data):
        """Test edit command that doesn't exist."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = mock_command_data
        
        from src.bot.cogs.admin.custom_cmd import edit_custom_command
        await edit_custom_command(mock_ctx, subcommand_passed="nonexistent Updated greeting!")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_send_error.assert_called_once()
        
        error_msg = mock_send_error.call_args[0][1]
        assert messages.COMMAND_NOT_FOUND in error_msg
        assert "!nonexistent" in error_msg
    
    # Test remove command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_msg')
    async def test_remove_custom_command_success(self, mock_send_msg, mock_dal_class, 
                                               custom_cmd_cog, mock_ctx, mock_command_data):
        """Test successful custom command removal."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = mock_command_data
        
        from src.bot.cogs.admin.custom_cmd import remove_custom_command
        await remove_custom_command(mock_ctx, cmd_name="hello")
        
        mock_dal.get_all_server_commands.assert_called_once_with(12345)
        mock_dal.delete_server_command.assert_called_once_with(12345, "hello")
        mock_send_msg.assert_called_once()
        
        success_msg = mock_send_msg.call_args[0][1]
        assert messages.CUSTOM_COMMAND_REMOVED in success_msg
        assert "!hello" in success_msg
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_warning_msg')
    async def test_remove_custom_command_no_commands_exist(self, mock_send_warning, mock_dal_class, 
                                                         custom_cmd_cog, mock_ctx):
        """Test remove command when no custom commands exist."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = []
        
        from src.bot.cogs.admin.custom_cmd import remove_custom_command
        await remove_custom_command(mock_ctx, cmd_name="hello")
        
        mock_send_warning.assert_called_once_with(mock_ctx, messages.NO_CUSTOM_COMMANDS_FOUND)
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg')
    async def test_remove_custom_command_not_found(self, mock_send_error, mock_dal_class, 
                                                  custom_cmd_cog, mock_ctx, mock_command_data):
        """Test remove command that doesn't exist."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = mock_command_data
        
        from src.bot.cogs.admin.custom_cmd import remove_custom_command
        await remove_custom_command(mock_ctx, cmd_name="nonexistent")
        
        mock_send_error.assert_called_once()
        
        error_msg = mock_send_error.call_args[0][1]
        assert messages.CUSTOM_COMMAND_UNABLE_REMOVE in error_msg
        assert messages.COMMAND_NOT_FOUND in error_msg
        assert "nonexistent" in error_msg
    
    # Test removeall command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_msg')
    async def test_remove_all_custom_commands_success(self, mock_send_msg, mock_dal_class, 
                                                    custom_cmd_cog, mock_ctx, mock_command_data):
        """Test successful removal of all custom commands."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = mock_command_data
        
        from src.bot.cogs.admin.custom_cmd import remove_all_custom_commands
        await remove_all_custom_commands(mock_ctx)
        
        mock_dal.get_all_server_commands.assert_called_once_with(12345)
        mock_dal.delete_all_commands.assert_called_once_with(12345)
        mock_send_msg.assert_called_once_with(mock_ctx, messages.CUSTOM_COMMAND_ALL_REMOVED)
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg')
    async def test_remove_all_custom_commands_no_commands_exist(self, mock_send_error, mock_dal_class, 
                                                              custom_cmd_cog, mock_ctx):
        """Test removeall when no custom commands exist."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = []
        
        from src.bot.cogs.admin.custom_cmd import remove_all_custom_commands
        await remove_all_custom_commands(mock_ctx)
        
        mock_send_error.assert_called_once_with(mock_ctx, messages.NO_CUSTOM_COMMANDS_FOUND)
    
    # Test list command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_embed')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.get_member_by_id')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.convert_datetime_to_str_short')
    @patch('src.bot.cogs.admin.custom_cmd.chat_formatting.inline')
    async def test_list_custom_commands_success(self, mock_inline, mock_convert_datetime, 
                                              mock_get_member, mock_send_embed, mock_dal_class, 
                                              custom_cmd_cog, mock_ctx):
        """Test successful listing of custom commands."""
        # Setup mock data
        mock_command_1 = {"name": "hello", "created_by": 67890, "created_at": datetime.now()}
        mock_command_2 = {"name": "rules", "created_by": 11111, "created_at": datetime.now()}
        
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = [mock_command_1, mock_command_2]
        
        # Setup member mocks
        mock_user1 = MagicMock()
        mock_user1.display_name = "TestUser"
        mock_user2 = MagicMock()
        mock_user2.display_name = "OtherUser"
        mock_get_member.side_effect = [mock_user1, mock_user2]
        
        mock_convert_datetime.return_value = "2023-01-01 12:00:00"
        mock_inline.side_effect = lambda x: f"inline({x})"
        
        from src.bot.cogs.admin.custom_cmd import list_custom_commands
        await list_custom_commands(mock_ctx)
        
        mock_dal.get_all_server_commands.assert_called_once_with(12345)
        mock_send_embed.assert_called_once()
        
        embed = mock_send_embed.call_args[0][1]
        assert embed.author.name == messages.CUSTOM_COMMANDS_SERVER
        assert embed.author.icon_url == "http://example.com/icon.png"
        assert len(embed.fields) == 3  # Command, Created by, Created at
        assert embed.footer.text == "For more info: !help admin cc"
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_warning_msg')
    async def test_list_custom_commands_no_commands_exist(self, mock_send_warning, mock_dal_class, 
                                                        custom_cmd_cog, mock_ctx):
        """Test list when no custom commands exist."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = []
        
        from src.bot.cogs.admin.custom_cmd import list_custom_commands
        await list_custom_commands(mock_ctx)
        
        mock_send_warning.assert_called_once_with(mock_ctx, messages.NO_CUSTOM_COMMANDS_FOUND)
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_embed')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.get_member_by_id')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.convert_datetime_to_str_short')
    @patch('src.bot.cogs.admin.custom_cmd.chat_formatting.inline')
    async def test_list_custom_commands_unknown_user(self, mock_inline, mock_convert_datetime, 
                                                    mock_get_member, mock_send_embed, mock_dal_class, 
                                                    custom_cmd_cog, mock_ctx):
        """Test list with unknown user (user no longer in server)."""
        mock_command = {"name": "hello", "created_by": 99999, "created_at": datetime.now()}
        
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = [mock_command]
        
        mock_get_member.return_value = None  # User not found
        mock_convert_datetime.return_value = "2023-01-01 12:00:00"
        mock_inline.side_effect = lambda x: f"inline({x})"
        
        from src.bot.cogs.admin.custom_cmd import list_custom_commands
        await list_custom_commands(mock_ctx)
        
        mock_send_embed.assert_called_once()
        embed = mock_send_embed.call_args[0][1]
        
        # Check that "Unknown User" is used when member is not found
        created_by_field = next(field for field in embed.fields if field.name == "Created by")
        assert "Unknown User" in created_by_field.value
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_embed')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.get_member_by_id')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.convert_datetime_to_str_short')
    @patch('src.bot.cogs.admin.custom_cmd.chat_formatting.inline')
    async def test_list_custom_commands_no_guild_icon(self, mock_inline, mock_convert_datetime, 
                                                     mock_get_member, mock_send_embed, mock_dal_class, 
                                                     custom_cmd_cog, mock_ctx):
        """Test list when guild has no icon."""
        mock_ctx.guild.icon = None
        
        mock_command = {"name": "hello", "created_by": 67890, "created_at": datetime.now()}
        
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_commands.return_value = [mock_command]
        
        mock_user = MagicMock()
        mock_user.display_name = "TestUser"
        mock_get_member.return_value = mock_user
        
        mock_convert_datetime.return_value = "2023-01-01 12:00:00"
        mock_inline.side_effect = lambda x: f"inline({x})"
        
        from src.bot.cogs.admin.custom_cmd import list_custom_commands
        await list_custom_commands(mock_ctx)
        
        embed = mock_send_embed.call_args[0][1]
        assert embed.author.icon_url is None
    
    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.admin.custom_cmd import setup
        
        await setup(mock_bot)
        
        mock_bot.remove_command.assert_called_once_with("admin")
        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, CustomCommand)
        assert added_cog.bot == mock_bot
    
    def test_custom_command_cog_inheritance(self, custom_cmd_cog):
        """Test that CustomCommand cog properly inherits from Admin."""
        from src.bot.cogs.admin.admin import Admin
        assert isinstance(custom_cmd_cog, Admin)
        assert hasattr(custom_cmd_cog, 'bot')
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_msg')
    async def test_add_custom_command_case_insensitive_conflict(self, mock_send_msg, mock_delete_msg, 
                                                              mock_dal_class, custom_cmd_cog, mock_ctx):
        """Test add command with case-insensitive bot command conflict."""
        # Add a command with mixed case to bot commands
        mock_command = MagicMock()
        mock_command.name = "Help"  # Different case than "help"
        mock_ctx.bot.commands = [mock_command]
        
        from src.bot.cogs.admin.custom_cmd import add_custom_command
        
        with patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg') as mock_send_error:
            await add_custom_command(mock_ctx, subcommand_passed="help Some description")
            
            mock_send_error.assert_called_once()
            error_msg = mock_send_error.call_args[0][1]
            assert messages.ALREADY_A_STANDARD_COMMAND in error_msg
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_msg')
    async def test_add_custom_command_with_spaces_in_description(self, mock_send_msg, mock_delete_msg, 
                                                               mock_dal_class, custom_cmd_cog, mock_ctx):
        """Test add command with multiple spaces in description."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_command.return_value = None
        
        from src.bot.cogs.admin.custom_cmd import add_custom_command
        await add_custom_command(mock_ctx, subcommand_passed="greet Hello there everyone! Welcome to our server!")
        
        mock_dal.insert_command.assert_called_once_with(
            12345, 67890, "greet", "Hello there everyone! Welcome to our server!"
        )
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.CustomCommandsDal')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_msg')
    async def test_add_custom_command_exact_20_chars(self, mock_send_msg, mock_delete_msg, 
                                                    mock_dal_class, custom_cmd_cog, mock_ctx):
        """Test add command with exactly 20 character name (should succeed)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_command.return_value = None
        
        name_20_chars = "a" * 20  # Exactly 20 characters
        
        from src.bot.cogs.admin.custom_cmd import add_custom_command
        await add_custom_command(mock_ctx, subcommand_passed=f"{name_20_chars} Description")
        
        mock_dal.insert_command.assert_called_once_with(12345, 67890, name_20_chars, "Description")
        mock_send_msg.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg')
    async def test_add_custom_command_empty_args(self, mock_send_error, mock_delete_msg, 
                                                custom_cmd_cog, mock_ctx):
        """Test add command with completely empty arguments."""
        from src.bot.cogs.admin.custom_cmd import add_custom_command
        await add_custom_command(mock_ctx, subcommand_passed="")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_send_error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.delete_message')
    @patch('src.bot.cogs.admin.custom_cmd.bot_utils.send_error_msg')
    async def test_edit_custom_command_empty_args(self, mock_send_error, mock_delete_msg, 
                                                 custom_cmd_cog, mock_ctx):
        """Test edit command with completely empty arguments."""
        from src.bot.cogs.admin.custom_cmd import edit_custom_command
        await edit_custom_command(mock_ctx, subcommand_passed="")
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_send_error.assert_called_once()
