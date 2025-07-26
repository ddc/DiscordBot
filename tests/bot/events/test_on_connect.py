"""Comprehensive tests for the OnConnect event cog."""

# Mock problematic imports before importing the module
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest


sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.events.on_connect import OnConnect, GuildSynchronizer, ConnectionHandler


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.log = MagicMock()
    # Ensure log methods are not coroutines
    bot.log.error = MagicMock()
    bot.db_session = MagicMock()
    bot.get_guild = MagicMock()
    
    # Configure fetch_guilds to return a proper async iterator
    async def mock_fetch_guilds(limit=None):
        # Return empty async iterator - no guilds by default
        return
        yield  # This line makes it an async generator but won't execute
    
    bot.fetch_guilds = mock_fetch_guilds
    # Ensure add_cog doesn't return a coroutine
    bot.add_cog = AsyncMock(return_value=None)
    # Mock the event decorator to prevent coroutine issues
    bot.event = MagicMock(side_effect=lambda func: func)
    return bot


@pytest.fixture
def guild_synchronizer(mock_bot):
    """Create a GuildSynchronizer instance."""
    return GuildSynchronizer(mock_bot)


@pytest.fixture
def connection_handler(mock_bot):
    """Create a ConnectionHandler instance."""
    return ConnectionHandler(mock_bot)


@pytest.fixture
def on_connect_cog(mock_bot):
    """Create an OnConnect cog instance."""
    return OnConnect(mock_bot)


@pytest.fixture
def mock_guild():
    """Create a mock guild instance."""
    guild = MagicMock()
    guild.id = 12345
    guild.name = "Test Server"
    return guild


@pytest.fixture
def mock_guilds():
    """Create mock guilds list."""
    guilds = []
    for i in range(3):
        guild = MagicMock()
        guild.id = 12345 + i
        guild.name = f"Test Server {i}"
        guilds.append(guild)
    return guilds


class TestGuildSynchronizer:
    """Test cases for GuildSynchronizer class."""

    def test_init(self, mock_bot):
        """Test GuildSynchronizer initialization."""
        synchronizer = GuildSynchronizer(mock_bot)
        assert synchronizer.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_connect.ServersDal')
    async def test_get_database_server_ids_success(self, mock_dal_class, guild_synchronizer):
        """Test getting database server IDs successfully."""
        # Setup mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = [{"id": 12345}, {"id": 12346}, {"id": 12347}]

        result = await guild_synchronizer._get_database_server_ids()

        assert result == {12345, 12346, 12347}
        mock_dal.get_server.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_connect.ServersDal')
    async def test_get_database_server_ids_empty(self, mock_dal_class, guild_synchronizer):
        """Test getting database server IDs when empty."""
        # Setup mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = None

        result = await guild_synchronizer._get_database_server_ids()

        assert result == set()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_connect.ServersDal')
    async def test_get_database_server_ids_error(self, mock_dal_class, guild_synchronizer):
        """Test getting database server IDs with error."""
        # Setup mock to raise exception
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.side_effect = Exception("Database error")

        result = await guild_synchronizer._get_database_server_ids()

        assert result == set()
        guild_synchronizer.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_discord_guild_ids_success(self, guild_synchronizer, mock_guilds):
        """Test getting Discord guild IDs successfully."""

        # Setup async generator mock
        async def mock_fetch_guilds(limit=None):
            for guild in mock_guilds:
                yield guild

        guild_synchronizer.bot.fetch_guilds = mock_fetch_guilds

        result = await guild_synchronizer._get_discord_guild_ids()

        expected_ids = {12345, 12346, 12347}
        assert result == expected_ids

    @pytest.mark.asyncio
    async def test_get_discord_guild_ids_error(self, guild_synchronizer):
        """Test getting Discord guild IDs with error."""
        # Setup mock to raise exception during iteration
        async def error_fetch_guilds(limit=None):
            raise Exception("Discord API error")
            # This line makes it an async generator but won't be reached
            yield
        
        guild_synchronizer.bot.fetch_guilds = error_fetch_guilds

        result = await guild_synchronizer._get_discord_guild_ids()

        assert result == set()
        guild_synchronizer.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_connect.bot_utils.insert_server')
    async def test_add_missing_guilds_success(self, mock_insert_server, guild_synchronizer, mock_guild):
        """Test adding missing guilds successfully."""
        missing_guild_ids = {12345}
        guild_synchronizer.bot.get_guild.return_value = mock_guild

        await guild_synchronizer._add_missing_guilds(missing_guild_ids)

        guild_synchronizer.bot.get_guild.assert_called_once_with(12345)
        mock_insert_server.assert_called_once_with(guild_synchronizer.bot, mock_guild)
        guild_synchronizer.bot.log.info.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_connect.bot_utils.insert_server')
    async def test_add_missing_guilds_guild_not_found(self, mock_insert_server, guild_synchronizer):
        """Test adding missing guilds when guild not found."""
        missing_guild_ids = {12345}
        guild_synchronizer.bot.get_guild.return_value = None

        await guild_synchronizer._add_missing_guilds(missing_guild_ids)

        guild_synchronizer.bot.get_guild.assert_called_once_with(12345)
        mock_insert_server.assert_not_called()
        guild_synchronizer.bot.log.warning.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_connect.bot_utils.insert_server')
    async def test_add_missing_guilds_insert_error(self, mock_insert_server, guild_synchronizer, mock_guild):
        """Test adding missing guilds with insert error."""
        missing_guild_ids = {12345}
        guild_synchronizer.bot.get_guild.return_value = mock_guild
        mock_insert_server.side_effect = Exception("Insert error")

        await guild_synchronizer._add_missing_guilds(missing_guild_ids)

        guild_synchronizer.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_guilds_with_database_no_missing(self, guild_synchronizer):
        """Test guild synchronization with no missing guilds."""
        # Mock methods to return same sets
        guild_synchronizer._get_database_server_ids = AsyncMock(return_value={12345, 12346})
        guild_synchronizer._get_discord_guild_ids = AsyncMock(return_value={12345, 12346})
        guild_synchronizer._add_missing_guilds = AsyncMock()

        await guild_synchronizer.sync_guilds_with_database()

        guild_synchronizer._add_missing_guilds.assert_not_called()
        guild_synchronizer.bot.log.info.assert_called_with("All guilds are already synchronized with database")

    @pytest.mark.asyncio
    async def test_sync_guilds_with_database_with_missing(self, guild_synchronizer):
        """Test guild synchronization with missing guilds."""
        # Mock methods to return different sets
        guild_synchronizer._get_database_server_ids = AsyncMock(return_value={12345})
        guild_synchronizer._get_discord_guild_ids = AsyncMock(return_value={12345, 12346, 12347})
        guild_synchronizer._add_missing_guilds = AsyncMock()

        await guild_synchronizer.sync_guilds_with_database()

        guild_synchronizer._add_missing_guilds.assert_called_once_with({12346, 12347})
        guild_synchronizer.bot.log.info.assert_called_with("Added 2 missing guilds to database")

    @pytest.mark.asyncio
    async def test_sync_guilds_with_database_error(self, guild_synchronizer):
        """Test guild synchronization with general error."""
        # Mock method to raise exception
        guild_synchronizer._get_database_server_ids = AsyncMock(side_effect=Exception("General error"))

        await guild_synchronizer.sync_guilds_with_database()

        guild_synchronizer.bot.log.error.assert_called_once()


class TestConnectionHandler:
    """Test cases for ConnectionHandler class."""

    def test_init(self, mock_bot):
        """Test ConnectionHandler initialization."""
        handler = ConnectionHandler(mock_bot)
        assert handler.bot == mock_bot
        assert isinstance(handler.guild_synchronizer, GuildSynchronizer)
        assert handler.guild_synchronizer.bot == mock_bot

    @pytest.mark.asyncio
    async def test_process_connection_success(self, connection_handler):
        """Test successful connection processing."""
        connection_handler.guild_synchronizer.sync_guilds_with_database = AsyncMock()

        await connection_handler.process_connection()

        connection_handler.bot.log.info.assert_any_call("Bot connected to Discord - starting initialization tasks")
        connection_handler.guild_synchronizer.sync_guilds_with_database.assert_called_once()
        connection_handler.bot.log.info.assert_any_call("Bot connection initialization completed successfully")

    @pytest.mark.asyncio
    async def test_process_connection_error(self, connection_handler):
        """Test connection processing with error."""
        connection_handler.guild_synchronizer.sync_guilds_with_database = AsyncMock(
            side_effect=Exception("Sync error")
        )

        await connection_handler.process_connection()

        connection_handler.bot.log.error.assert_called_once()
        error_call = connection_handler.bot.log.error.call_args[0][0]
        assert "Error during connection processing" in error_call


class TestOnConnect:
    """Test cases for OnConnect cog."""

    def test_init(self, mock_bot):
        """Test OnConnect cog initialization."""
        cog = OnConnect(mock_bot)
        assert cog.bot == mock_bot
        assert isinstance(cog.connection_handler, ConnectionHandler)
        assert cog.connection_handler.bot == mock_bot

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_connect import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnConnect)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_on_connect_event_success(self, mock_bot):
        """Test on_connect event handler success."""
        cog = OnConnect(mock_bot)
        cog.connection_handler.process_connection = AsyncMock()

        # Access the event handler directly
        on_connect_event = mock_bot.event.call_args_list[0][0][0]

        await on_connect_event()

        cog.connection_handler.process_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_connect_event_error(self, mock_bot):
        """Test on_connect event handler with error."""
        cog = OnConnect(mock_bot)
        cog.connection_handler.process_connection = AsyncMock(side_effect=Exception("Critical error"))

        # Access the event handler directly
        on_connect_event = mock_bot.event.call_args_list[0][0][0]

        await on_connect_event()

        mock_bot.log.error.assert_called_once()
        error_call = mock_bot.log.error.call_args[0][0]
        assert "Critical error in on_connect event" in error_call

    def test_on_connect_cog_inheritance(self, on_connect_cog):
        """Test that OnConnect cog properly inherits from commands.Cog."""
        from discord.ext import commands

        assert isinstance(on_connect_cog, commands.Cog)
        assert hasattr(on_connect_cog, 'bot')

    @pytest.mark.asyncio
    async def test_guild_synchronizer_integration(self, mock_bot):
        """Test integration between OnConnect and GuildSynchronizer."""
        # Create cog and verify connection handler setup
        cog = OnConnect(mock_bot)

        # Verify that connection handler has a guild synchronizer
        assert hasattr(cog.connection_handler, 'guild_synchronizer')
        assert isinstance(cog.connection_handler.guild_synchronizer, GuildSynchronizer)
        assert cog.connection_handler.guild_synchronizer.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_connect.ServersDal')
    @patch('src.bot.cogs.events.on_connect.bot_utils.insert_server')
    async def test_full_integration_sync_process(self, mock_insert_server, mock_dal_class, mock_bot, mock_guilds):
        """Test full integration of synchronization process."""
        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = [{"id": 12345}]  # Only first guild in DB

        # Setup Discord API mock
        async def mock_fetch_guilds(limit=None):
            for guild in mock_guilds:
                yield guild

        mock_bot.fetch_guilds = mock_fetch_guilds
        mock_bot.get_guild.side_effect = lambda guild_id: next((g for g in mock_guilds if g.id == guild_id), None)

        # Create and run connection process
        cog = OnConnect(mock_bot)
        await cog.connection_handler.process_connection()

        # Verify synchronization occurred
        mock_dal.get_server.assert_called_once()

        # Should insert missing guilds (12346, 12347)
        assert mock_insert_server.call_count == 2

        # Verify logging
        mock_bot.log.info.assert_any_call("Bot connected to Discord - starting initialization tasks")
        mock_bot.log.info.assert_any_call("Bot connection initialization completed successfully")
