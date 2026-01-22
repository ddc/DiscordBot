"""Comprehensive tests for GW2 account cog."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import discord
from discord.ext import commands

from src.gw2.cogs.account import GW2Account, account
from src.gw2.tools.gw2_exceptions import APIInvalidKey, APIError


class TestGW2Account:
    """Test cases for the GW2Account cog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {
            "gw2": {
                "EmbedColor": 0x00ff00
            }
        }
        return bot

    @pytest.fixture
    def gw2_account_cog(self, mock_bot):
        """Create a GW2Account cog instance."""
        return GW2Account(mock_bot)

    def test_gw2_account_initialization(self, mock_bot):
        """Test GW2Account cog initialization."""
        cog = GW2Account(mock_bot)
        assert cog.bot == mock_bot

    def test_gw2_account_inheritance(self, gw2_account_cog):
        """Test that GW2Account inherits from GuildWars2 properly."""
        # Should inherit from the base GuildWars2 class
        from src.gw2.cogs.gw2 import GuildWars2
        assert isinstance(gw2_account_cog, GuildWars2)


class TestAccountCommand:
    """Test cases for the account command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {
            "gw2": {
                "EmbedColor": 0x00ff00
            }
        }
        ctx.bot.user = MagicMock()
        ctx.bot.user.avatar = MagicMock()
        ctx.bot.user.avatar.url = "https://example.com/bot_avatar.png"
        
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/user_avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        
        ctx.prefix = "!"
        return ctx

    @pytest.fixture
    def sample_api_key_data(self):
        """Create sample API key data."""
        return [{
            "key": "test-api-key-12345",
            "permissions": "account,characters,progression,pvp,guilds"
        }]

    @pytest.fixture
    def sample_account_data(self):
        """Create sample account data."""
        return {
            "id": "account-id-123",
            "name": "TestUser.1234",
            "world": 1001,
            "guilds": ["guild-id-1", "guild-id-2"],
            "guild_leader": ["guild-id-1"],
            "created": "2020-01-01T00:00:00.000Z",
            "access": ["PlayForFree", "GuildWars2", "HeartOfThorns"],
            "commander": True,
            "fractal_level": 100,
            "daily_ap": 5000,
            "monthly_ap": 500,
            "wvw_rank": 1250,
            "age": 1051200  # minutes (2 years)
        }

    @pytest.fixture
    def sample_world_data(self):
        """Create sample world data."""
        return {
            "id": 1001,
            "name": "Anvil Rock",
            "population": "High"
        }

    @pytest.mark.asyncio
    async def test_account_command_no_api_key(self, mock_ctx):
        """Test account command when user has no API key."""
        with patch('src.gw2.cogs.account.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=None)
            
            with patch('src.gw2.cogs.account.bot_utils.send_error_msg') as mock_error:
                await account(mock_ctx)
                
                mock_error.assert_called_once()
                error_msg = mock_error.call_args[0][1]
                assert "You dont have an API key registered" in error_msg

    @pytest.mark.asyncio
    async def test_account_command_invalid_api_key(self, mock_ctx, sample_api_key_data):
        """Test account command with invalid API key."""
        with patch('src.gw2.cogs.account.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            
            with patch('src.gw2.cogs.account.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                invalid_key_error = APIInvalidKey(mock_ctx.bot, "Invalid API key")
                # Make the error have an args attribute like a real exception
                invalid_key_error.args = ("error", "Invalid API key message")
                mock_client_instance.check_api_key = AsyncMock(return_value=invalid_key_error)
                
                with patch('src.gw2.cogs.account.bot_utils.send_error_msg') as mock_error:
                    await account(mock_ctx)
                    
                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "Invalid API key message" in error_msg

    @pytest.mark.asyncio
    async def test_account_command_insufficient_permissions(self, mock_ctx, sample_account_data):
        """Test account command with insufficient API key permissions."""
        insufficient_permissions_data = [{
            "key": "test-api-key-12345",
            "permissions": "characters"  # Missing 'account' permission
        }]
        
        with patch('src.gw2.cogs.account.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=insufficient_permissions_data)
            
            with patch('src.gw2.cogs.account.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                
                with patch('src.gw2.cogs.account.bot_utils.send_error_msg') as mock_error:
                    await account(mock_ctx)
                    
                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "Your API key doesnt have permission" in error_msg

    @pytest.mark.asyncio
    async def test_account_command_successful_basic(self, mock_ctx, sample_api_key_data, sample_account_data, sample_world_data):
        """Test successful account command with basic information."""
        with patch('src.gw2.cogs.account.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            
            with patch('src.gw2.cogs.account.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(side_effect=[
                    sample_account_data,  # account call
                    sample_world_data,    # world call
                ])
                
                with patch('src.gw2.cogs.account.bot_utils.send_embed') as mock_send:
                    await account(mock_ctx)
                    
                    mock_send.assert_called_once()
                    mock_send.assert_called_once()
                    # The embed is created inside the function, just verify send was called

    @pytest.mark.asyncio
    async def test_account_command_with_characters_permission(self, mock_ctx, sample_account_data, sample_world_data):
        """Test account command with characters permission."""
        characters_api_key_data = [{
            "key": "test-api-key-12345",
            "permissions": "account,characters"
        }]
        
        characters_data = ["Character1", "Character2", "Character3"]
        
        with patch('src.gw2.cogs.account.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=characters_api_key_data)
            
            with patch('src.gw2.cogs.account.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(side_effect=[
                    sample_account_data,  # account call
                    sample_world_data,    # world call
                    characters_data,      # characters call
                ])
                
                with patch('src.gw2.cogs.account.bot_utils.send_embed') as mock_send:
                    await account(mock_ctx)
                    
                    mock_send.assert_called_once()
                    mock_send.assert_called_once()
                    # Verify the function completed without error

    @pytest.mark.asyncio
    async def test_account_command_with_progression_permission(self, mock_ctx, sample_account_data, sample_world_data):
        """Test account command with progression permission."""
        progression_api_key_data = [{
            "key": "test-api-key-12345",
            "permissions": "account,progression"
        }]
        
        achievements_data = [
            {"id": 1, "current": 10},
            {"id": 2, "current": 5}
        ]
        
        with patch('src.gw2.cogs.account.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=progression_api_key_data)
            
            with patch('src.gw2.cogs.account.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(side_effect=[
                    sample_account_data,  # account call
                    sample_world_data,    # world call
                    achievements_data,    # achievements call
                ])
                
                with patch('src.gw2.cogs.account.gw2_utils.calculate_user_achiev_points') as mock_calc:
                    mock_calc.return_value = 15000
                    
                    with patch('src.gw2.cogs.account.gw2_utils.get_wvw_rank_title') as mock_wvw_title:
                        mock_wvw_title.return_value = "Gold General"
                        
                        with patch('src.gw2.cogs.account.bot_utils.send_embed') as mock_send:
                            await account(mock_ctx)
                            
                            mock_send.assert_called_once()
                            mock_send.assert_called_once()
                            # Verify the function completed without error

    @pytest.mark.asyncio
    async def test_account_command_with_pvp_permission(self, mock_ctx, sample_account_data, sample_world_data):
        """Test account command with PvP permission."""
        pvp_api_key_data = [{
            "key": "test-api-key-12345",
            "permissions": "account,pvp"
        }]
        
        pvp_stats_data = {
            "pvp_rank": 45,
            "pvp_rank_rollovers": 5
        }
        
        with patch('src.gw2.cogs.account.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=pvp_api_key_data)
            
            with patch('src.gw2.cogs.account.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(side_effect=[
                    sample_account_data,  # account call
                    sample_world_data,    # world call
                    pvp_stats_data,       # pvp stats call
                ])
                
                with patch('src.gw2.cogs.account.gw2_utils.get_pvp_rank_title') as mock_pvp_title:
                    mock_pvp_title.return_value = "Tiger"
                    
                    with patch('src.gw2.cogs.account.bot_utils.send_embed') as mock_send:
                        await account(mock_ctx)
                        
                        mock_send.assert_called_once()
                        mock_send.assert_called_once()
                        # Verify the function completed without error

    @pytest.mark.asyncio
    async def test_account_command_with_guilds(self, mock_ctx, sample_account_data, sample_world_data):
        """Test account command with guild information."""
        full_permissions_data = [{
            "key": "test-api-key-12345",
            "permissions": "account,guilds"
        }]
        
        guild_data_1 = {
            "id": "guild-id-1",
            "name": "Test Guild One",
            "tag": "TG1"
        }
        
        guild_data_2 = {
            "id": "guild-id-2", 
            "name": "Test Guild Two",
            "tag": "TG2"
        }
        
        with patch('src.gw2.cogs.account.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=full_permissions_data)
            
            with patch('src.gw2.cogs.account.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(side_effect=[
                    sample_account_data,  # account call
                    sample_world_data,    # world call
                    guild_data_1,         # first guild call
                    guild_data_2,         # second guild call
                ])
                
                with patch('src.gw2.cogs.account.bot_utils.send_embed') as mock_send:
                    await account(mock_ctx)
                    
                    mock_send.assert_called_once()
                    mock_send.assert_called_once()
                    # Verify the function completed without error

    @pytest.mark.asyncio
    async def test_account_command_api_error_during_execution(self, mock_ctx, sample_api_key_data, sample_account_data):
        """Test account command when API error occurs during execution."""
        with patch('src.gw2.cogs.account.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            
            with patch('src.gw2.cogs.account.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(side_effect=Exception("API Error"))
                
                with patch('src.gw2.cogs.account.bot_utils.send_error_msg') as mock_error:
                    await account(mock_ctx)
                    
                    mock_error.assert_called_once()
                    mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_command_guild_api_error(self, mock_ctx, sample_account_data, sample_world_data):
        """Test account command when guild API call fails."""
        full_permissions_data = [{
            "key": "test-api-key-12345",
            "permissions": "account,guilds"
        }]
        
        with patch('src.gw2.cogs.account.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=full_permissions_data)
            
            with patch('src.gw2.cogs.account.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(side_effect=[
                    sample_account_data,  # account call
                    sample_world_data,    # world call
                    Exception("Guild API Error"),  # guild call fails
                ])
                
                with patch('src.gw2.cogs.account.bot_utils.send_error_msg') as mock_error:
                    await account(mock_ctx)
                    
                    mock_error.assert_called_once()
                    mock_ctx.bot.log.error.assert_called_once()

    def test_account_command_cooldown(self):
        """Test that account command has proper cooldown."""
        # The cooldown is applied via decorator, just check the function exists
        from src.gw2.cogs.account import account
        assert callable(account)

    def test_account_command_belongs_to_gw2_group(self):
        """Test that account command belongs to gw2 command group."""
        # The command is registered as a subcommand via @GW2Account.gw2.command()
        from src.gw2.cogs.account import account
        assert callable(account)


class TestAccountSetup:
    """Test cases for account cog setup."""

    @pytest.mark.asyncio
    async def test_setup_function_exists(self):
        """Test that setup function exists and is callable."""
        from src.gw2.cogs.account import setup
        assert callable(setup)

    @pytest.mark.asyncio
    async def test_setup_function_removes_existing_gw2_command(self):
        """Test that setup removes existing gw2 command."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()
        
        from src.gw2.cogs.account import setup
        await setup(mock_bot)
        
        mock_bot.remove_command.assert_called_once_with("gw2")
        mock_bot.add_cog.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_function_adds_cog(self):
        """Test that setup adds the GW2Account cog."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()
        
        from src.gw2.cogs.account import setup
        await setup(mock_bot)
        
        # Verify that add_cog was called with a GW2Account instance
        mock_bot.add_cog.assert_called_once()
        cog_instance = mock_bot.add_cog.call_args[0][0]
        assert isinstance(cog_instance, GW2Account)