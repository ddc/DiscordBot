"""Comprehensive tests for the Owner cog."""

import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from discord.ext import commands
from datetime import datetime, timezone

# Mock problematic imports before importing the module
import sys
sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.owner import Owner
from src.bot.constants import messages, variables


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
    bot.user.activity = MagicMock()
    bot.user.activity.type = discord.ActivityType.playing
    bot.user.activity.name = "Test Game | !help"
    bot.command_prefix = ("!",)
    bot.description = "Test bot description"
    bot.settings = {
        "bot": {
            "EmbedOwnerColor": discord.Color.gold()
        }
    }
    return bot


@pytest.fixture
def owner_cog(mock_bot):
    """Create an Owner cog instance."""
    return Owner(mock_bot)


@pytest.fixture
def mock_ctx():
    """Create a mock context."""
    ctx = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    ctx.guild.name = "Test Server"
    
    author = MagicMock()
    author.id = 67890
    author.display_name = "TestUser"
    
    ctx.author = author
    ctx.message = MagicMock()
    ctx.message.channel = AsyncMock()
    ctx.prefix = "!"
    ctx.invoked_subcommand = None
    
    return ctx


@pytest.fixture
def mock_server_data():
    """Create mock server data."""
    return [
        {"id": 12345, "name": "Test Server 1"},
        {"id": 67890, "name": "Test Server 2"},
        {"id": 11111, "name": "Test Server 3"}
    ]


class TestOwner:
    """Test cases for Owner cog."""
    
    def test_init(self, mock_bot):
        """Test Owner cog initialization."""
        cog = Owner(mock_bot)
        assert cog.bot == mock_bot
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.bot_utils.invoke_subcommand')
    async def test_owner_group_command(self, mock_invoke, owner_cog, mock_ctx):
        """Test owner group command."""
        mock_invoke.return_value = "mock_command"
        
        result = await owner_cog.owner.callback(owner_cog, mock_ctx)
        
        mock_invoke.assert_called_once_with(mock_ctx, "owner")
        assert result == "mock_command"
    
    # Test prefix change command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.BotConfigsDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_change_prefix_success(self, mock_send_embed, mock_dal_class, 
                                             owner_cog, mock_ctx):
        """Test successful prefix change."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        
        await owner_cog.owner_change_prefix.callback(owner_cog, mock_ctx, new_prefix="$")
        
        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.update_bot_prefix.assert_called_once_with("$", 67890)
        
        # Verify bot prefix was updated
        assert owner_cog.bot.command_prefix == ("$",)
        
        mock_send_embed.assert_called_once()
        embed = mock_send_embed.call_args[0][1]
        assert messages.BOT_PREFIX_CHANGED in embed.description
        assert "$" in embed.description
    
    @pytest.mark.asyncio
    async def test_owner_change_prefix_invalid(self, owner_cog, mock_ctx):
        """Test prefix change with invalid prefix."""
        with pytest.raises(commands.BadArgument) as exc_info:
            await owner_cog.owner_change_prefix.callback(owner_cog, mock_ctx, new_prefix="#")
        
        error_msg = str(exc_info.value)
        assert "Invalid prefix" in error_msg
        assert ", ".join(variables.ALLOWED_PREFIXES) in error_msg
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.BotConfigsDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_change_prefix_with_activity_update(self, mock_send_embed, mock_dal_class, 
                                                           owner_cog, mock_ctx):
        """Test prefix change with bot activity update."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        
        await owner_cog.owner_change_prefix.callback(owner_cog, mock_ctx, new_prefix="%")
        
        # Verify activity was updated
        owner_cog.bot.change_presence.assert_called_once()
        activity_call = owner_cog.bot.change_presence.call_args[1]['activity']
        assert isinstance(activity_call, discord.Game)
        assert activity_call.name == "Test Game | %help"
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.BotConfigsDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_change_prefix_no_activity(self, mock_send_embed, mock_dal_class, 
                                                  owner_cog, mock_ctx):
        """Test prefix change when bot has no activity."""
        owner_cog.bot.user.activity = None
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        
        await owner_cog.owner_change_prefix.callback(owner_cog, mock_ctx, new_prefix="&")
        
        # Should not call change_presence when no activity
        owner_cog.bot.change_presence.assert_not_called()
        
        # But should still update prefix
        assert owner_cog.bot.command_prefix == ("&",)
        mock_send_embed.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.BotConfigsDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_change_prefix_non_playing_activity(self, mock_send_embed, mock_dal_class, 
                                                           owner_cog, mock_ctx):
        """Test prefix change when bot has non-playing activity."""
        owner_cog.bot.user.activity.type = discord.ActivityType.listening
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        
        await owner_cog.owner_change_prefix.callback(owner_cog, mock_ctx, new_prefix="?")
        
        # Should not update activity for non-playing activities
        owner_cog.bot.change_presence.assert_not_called()
        mock_send_embed.assert_called_once()
    
    # Test description update command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.BotConfigsDal')
    @patch('src.bot.cogs.owner.bot_utils.delete_message')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_description_success(self, mock_send_embed, mock_delete_msg, 
                                           mock_dal_class, owner_cog, mock_ctx):
        """Test successful description update."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        
        new_desc = "Updated bot description"
        await owner_cog.owner_description.callback(owner_cog, mock_ctx, desc=new_desc)
        
        mock_delete_msg.assert_called_once_with(mock_ctx)
        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.update_bot_description.assert_called_once_with(new_desc, 67890)
        
        # Verify bot description was updated
        assert owner_cog.bot.description == new_desc
        
        mock_send_embed.assert_called_once()
        embed = mock_send_embed.call_args[0][1]
        assert messages.BOT_DESCRIPTION_CHANGED in embed.description
        assert new_desc in embed.description
    
    # Test servers list command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.ServersDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_servers_success(self, mock_send_embed, mock_dal_class, 
                                       owner_cog, mock_ctx, mock_server_data):
        """Test successful servers list."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = mock_server_data
        
        await owner_cog.owner_servers.callback(owner_cog, mock_ctx)
        
        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.get_server.assert_called_once()
        mock_send_embed.assert_called_once()
        
        embed = mock_send_embed.call_args[0][1]
        assert embed.author.name == "TestBot"
        assert len(embed.fields) == 2  # ID and Name fields
        assert embed.footer.text == "Total servers: 3"
        
        # Check that dm=True is passed
        assert mock_send_embed.call_args[0][2] is True
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.ServersDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_servers_no_servers(self, mock_send_embed, mock_dal_class, 
                                          owner_cog, mock_ctx):
        """Test servers list with no servers."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = []
        
        result = await owner_cog.owner_servers.callback(owner_cog, mock_ctx)
        
        mock_send_embed.assert_called_once()
        embed = mock_send_embed.call_args[0][1]
        assert "No servers found in database" in embed.description
        
        # Check that dm=True is passed
        assert mock_send_embed.call_args[0][2] is True
        # Result should be the return value of send_embed (AsyncMock)
        assert result == mock_send_embed.return_value
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.ServersDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_servers_many_servers(self, mock_send_embed, mock_dal_class, 
                                            owner_cog, mock_ctx):
        """Test servers list with more than 25 servers (pagination)."""
        # Create 30 mock servers
        many_servers = [{"id": i, "name": f"Server {i}"} for i in range(30)]
        
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = many_servers
        
        await owner_cog.owner_servers.callback(owner_cog, mock_ctx)
        
        embed = mock_send_embed.call_args[0][1]
        
        # Check that only 25 servers + "..." are shown
        id_field = next(field for field in embed.fields if field.name == "ID")
        name_field = next(field for field in embed.fields if field.name == "Name")
        
        id_lines = id_field.value.split("\n")
        name_lines = name_field.value.split("\n")
        
        assert len(id_lines) == 26  # 25 servers + "..."
        assert len(name_lines) == 26  # 25 servers + "..."
        assert id_lines[-1] == "..."
        assert name_lines[-1] == "..."
        
        # Footer should still show total count
        assert embed.footer.text == "Total servers: 30"
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.ServersDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_servers_no_bot_avatar(self, mock_send_embed, mock_dal_class, 
                                             owner_cog, mock_ctx, mock_server_data):
        """Test servers list when bot has no avatar."""
        owner_cog.bot.user.avatar = None
        
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = mock_server_data
        
        await owner_cog.owner_servers.callback(owner_cog, mock_ctx)
        
        embed = mock_send_embed.call_args[0][1]
        assert embed.author.icon_url is None
        assert embed.author.name == "TestBot"
    
    # Test helper methods
    @pytest.mark.asyncio
    async def test_update_bot_activity_prefix_with_activity(self, owner_cog):
        """Test _update_bot_activity_prefix with existing activity."""
        await owner_cog._update_bot_activity_prefix("$")
        
        owner_cog.bot.change_presence.assert_called_once()
        activity_call = owner_cog.bot.change_presence.call_args[1]['activity']
        assert isinstance(activity_call, discord.Game)
        assert activity_call.name == "Test Game | $help"
        
        # Check status and activity parameters
        assert owner_cog.bot.change_presence.call_args[1]['status'] == discord.Status.online
    
    @pytest.mark.asyncio
    async def test_update_bot_activity_prefix_no_activity(self, owner_cog):
        """Test _update_bot_activity_prefix with no activity."""
        owner_cog.bot.user.activity = None
        
        await owner_cog._update_bot_activity_prefix("$")
        
        owner_cog.bot.change_presence.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_bot_activity_prefix_wrong_activity_type(self, owner_cog):
        """Test _update_bot_activity_prefix with wrong activity type."""
        owner_cog.bot.user.activity.type = discord.ActivityType.listening
        
        await owner_cog._update_bot_activity_prefix("$")
        
        owner_cog.bot.change_presence.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_bot_activity_prefix_no_bot_user_activity_attr(self, owner_cog):
        """Test _update_bot_activity_prefix when bot.user has no activity attribute."""
        # Remove activity attribute
        del owner_cog.bot.user.activity
        
        await owner_cog._update_bot_activity_prefix("$")
        
        owner_cog.bot.change_presence.assert_not_called()
    
    def test_create_owner_embed(self, owner_cog):
        """Test _create_owner_embed method."""
        description = "Test owner message"
        embed = owner_cog._create_owner_embed(description)
        
        assert isinstance(embed, discord.Embed)
        assert embed.description == description
        assert embed.color == discord.Color.gold()
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.BotConfigsDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_change_prefix_all_valid_prefixes(self, mock_send_embed, mock_dal_class, 
                                                         owner_cog, mock_ctx):
        """Test prefix change with all valid prefixes."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        
        for prefix in variables.ALLOWED_PREFIXES:
            await owner_cog.owner_change_prefix.callback(owner_cog, mock_ctx, new_prefix=prefix)
            assert owner_cog.bot.command_prefix == (prefix,)
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.BotConfigsDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_description_with_special_characters(self, mock_send_embed, mock_dal_class, 
                                                            owner_cog, mock_ctx):
        """Test description update with special characters."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        
        special_desc = "Bot with émojis 🤖 and spéciál chars & symbols!"
        
        with patch('src.bot.cogs.owner.bot_utils.delete_message'):
            await owner_cog.owner_description.callback(owner_cog, mock_ctx, desc=special_desc)
            
            assert owner_cog.bot.description == special_desc
            mock_dal.update_bot_description.assert_called_once_with(special_desc, 67890)
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.BotConfigsDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_description_empty_string(self, mock_send_embed, mock_dal_class, 
                                                 owner_cog, mock_ctx):
        """Test description update with empty string."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        
        with patch('src.bot.cogs.owner.bot_utils.delete_message'):
            await owner_cog.owner_description.callback(owner_cog, mock_ctx, desc="")
            
            assert owner_cog.bot.description == ""
            mock_dal.update_bot_description.assert_called_once_with("", 67890)
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.ServersDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_servers_exactly_25_servers(self, mock_send_embed, mock_dal_class, 
                                                   owner_cog, mock_ctx):
        """Test servers list with exactly 25 servers (edge case)."""
        # Create exactly 25 mock servers
        servers_25 = [{"id": i, "name": f"Server {i}"} for i in range(25)]
        
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = servers_25
        
        await owner_cog.owner_servers.callback(owner_cog, mock_ctx)
        
        embed = mock_send_embed.call_args[0][1]
        
        # Should not truncate with exactly 25 servers
        id_field = next(field for field in embed.fields if field.name == "ID")
        name_field = next(field for field in embed.fields if field.name == "Name")
        
        id_lines = id_field.value.split("\n")
        name_lines = name_field.value.split("\n")
        
        assert len(id_lines) == 25
        assert len(name_lines) == 25
        assert "..." not in id_lines
        assert "..." not in name_lines
    
    @pytest.mark.asyncio
    async def test_update_bot_activity_prefix_complex_game_name(self, owner_cog):
        """Test _update_bot_activity_prefix with complex game name containing pipe."""
        owner_cog.bot.user.activity.name = "Complex | Game | Name | !help"
        
        await owner_cog._update_bot_activity_prefix("$")
        
        # Should only take the first part before the first pipe
        activity_call = owner_cog.bot.change_presence.call_args[1]['activity']
        assert activity_call.name == "Complex | $help"
    
    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.owner import setup
        
        await setup(mock_bot)
        
        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, Owner)
        assert added_cog.bot == mock_bot
    
    def test_owner_cog_inheritance(self, owner_cog):
        """Test that Owner cog properly inherits from commands.Cog."""
        assert isinstance(owner_cog, commands.Cog)
        assert hasattr(owner_cog, 'bot')
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.ServersDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_servers_return_value_none_case(self, mock_send_embed, mock_dal_class, 
                                                       owner_cog, mock_ctx, mock_server_data):
        """Test that owner_servers returns None when servers exist."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = mock_server_data
        
        result = await owner_cog.owner_servers.callback(owner_cog, mock_ctx)
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.owner.BotConfigsDal')
    @patch('src.bot.cogs.owner.bot_utils.send_embed')
    async def test_owner_change_prefix_case_sensitivity(self, mock_send_embed, mock_dal_class, 
                                                       owner_cog, mock_ctx):
        """Test that prefix validation is case-sensitive."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        
        # Test that invalid prefixes (not in ALLOWED_PREFIXES) are rejected
        with pytest.raises(commands.BadArgument):
            await owner_cog.owner_change_prefix.callback(owner_cog, mock_ctx, new_prefix="#")  # Not allowed
        
        # This should work - "!" is allowed
        await owner_cog.owner_change_prefix.callback(owner_cog, mock_ctx, new_prefix="!")
        mock_send_embed.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_bot_activity_prefix_with_no_pipe_in_activity(self, owner_cog):
        """Test _update_bot_activity_prefix when activity name has no pipe."""
        owner_cog.bot.user.activity.name = "SimpleGameName"
        
        await owner_cog._update_bot_activity_prefix("$")
        
        activity_call = owner_cog.bot.change_presence.call_args[1]['activity']
        assert activity_call.name == "SimpleGameName | $help"
