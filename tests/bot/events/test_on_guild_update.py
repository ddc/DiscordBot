"""Comprehensive tests for the OnGuildUpdate event cog."""

# Mock problematic imports before importing the module
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest


sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.events.on_guild_update import OnGuildUpdate
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
    bot.user.avatar = MagicMock()
    bot.user.avatar.url = "https://example.com/bot_avatar.png"
    # Ensure add_cog doesn't return a coroutine
    bot.add_cog = AsyncMock(return_value=None)
    # Mock the event decorator to prevent coroutine issues
    bot.event = MagicMock(side_effect=lambda func: func)
    return bot


@pytest.fixture
def on_guild_update_cog(mock_bot):
    """Create an OnGuildUpdate cog instance."""
    return OnGuildUpdate(mock_bot)


@pytest.fixture
def mock_guild():
    """Create a mock guild instance."""
    guild = MagicMock()
    guild.id = 12345
    guild.name = "Test Server"
    guild.icon = MagicMock()
    guild.icon.url = "https://example.com/icon.png"
    guild.owner_id = 98765
    guild.owner = MagicMock()
    guild.owner.__str__ = MagicMock(return_value="TestOwner#1234")
    return guild


@pytest.fixture
def mock_guild_before():
    """Create a mock guild before update."""
    guild = MagicMock()
    guild.id = 12345
    guild.name = "Old Test Server"
    guild.icon = MagicMock()
    guild.icon.url = "https://example.com/old_icon.png"
    guild.owner_id = 54321
    guild.owner = MagicMock()
    guild.owner.__str__ = MagicMock(return_value="OldOwner#5678")
    return guild


@pytest.fixture
def mock_embed():
    """Create a mock embed."""
    embed = MagicMock()
    embed.fields = []
    embed.add_field = MagicMock()
    embed.set_thumbnail = MagicMock()
    embed.set_footer = MagicMock()
    return embed


class TestOnGuildUpdate:
    """Test cases for OnGuildUpdate cog."""

    def test_init(self, mock_bot):
        """Test OnGuildUpdate cog initialization."""
        cog = OnGuildUpdate(mock_bot)
        assert cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_guild_update import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnGuildUpdate)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_guild_update.ServersDal')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.send_msg_to_system_channel')
    async def test_on_guild_update_icon_change(
        self,
        mock_send_msg,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_guild_before,
        mock_guild,
        mock_embed,
    ):
        """Test on_guild_update with icon change."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"
        # Mock embed fields to simulate having fields after add_field is called
        mock_embed.fields = [MagicMock()]  # Simulate one field added

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_server_update": True}

        # Set different icons
        mock_guild_before.icon.url = "https://example.com/old_icon.png"
        mock_guild.icon.url = "https://example.com/new_icon.png"
        mock_guild_before.name = mock_guild.name  # Same name
        mock_guild_before.owner_id = mock_guild.owner_id  # Same owner

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Verify embed setup
        mock_embed.set_footer.assert_called_with(icon_url=mock_bot.user.avatar.url, text="2023-01-01 12:00:00 UTC")

        # Verify icon change handling
        mock_embed.set_thumbnail.assert_called_with(url=mock_guild.icon.url)
        mock_embed.add_field.assert_called_with(name=messages.NEW_SERVER_ICON, value="")

        # Verify message sent
        mock_send_msg.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_guild_update.ServersDal')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.send_msg_to_system_channel')
    async def test_on_guild_update_name_change(
        self,
        mock_send_msg,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_guild_before,
        mock_guild,
        mock_embed,
    ):
        """Test on_guild_update with name change."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"
        # Mock embed fields to simulate having fields after add_field is called
        mock_embed.fields = [MagicMock()]  # Simulate one field added

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_server_update": True}

        # Set different names
        mock_guild_before.name = "Old Test Server"
        mock_guild.name = "New Test Server"
        mock_guild_before.icon.url = mock_guild.icon.url  # Same icon
        mock_guild_before.owner_id = mock_guild.owner_id  # Same owner

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Verify name change handling
        mock_embed.add_field.assert_any_call(name=messages.PREVIOUS_NAME, value="Old Test Server")
        mock_embed.add_field.assert_any_call(name=messages.NEW_SERVER_NAME, value="New Test Server")

        # Verify message sent
        mock_send_msg.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_guild_update.ServersDal')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.send_msg_to_system_channel')
    async def test_on_guild_update_owner_change(
        self,
        mock_send_msg,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_guild_before,
        mock_guild,
        mock_embed,
    ):
        """Test on_guild_update with owner change."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"
        # Mock embed fields to simulate having fields after add_field is called
        mock_embed.fields = [MagicMock()]  # Simulate one field added

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_server_update": True}

        # Set different owners
        mock_guild_before.owner_id = 54321
        mock_guild.owner_id = 98765
        mock_guild_before.name = mock_guild.name  # Same name
        mock_guild_before.icon.url = mock_guild.icon.url  # Same icon

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Verify owner change handling
        mock_embed.set_thumbnail.assert_called_with(url=mock_guild.icon.url)
        mock_embed.add_field.assert_any_call(name=messages.PREVIOUS_SERVER_OWNER, value=str(mock_guild_before.owner))
        mock_embed.add_field.assert_any_call(name=messages.NEW_SERVER_OWNER, value=str(mock_guild.owner))

        # Verify message sent
        mock_send_msg.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_guild_update.ServersDal')
    async def test_on_guild_update_no_changes(
        self, mock_dal_class, mock_datetime, mock_get_embed, mock_bot, mock_guild_before, mock_guild, mock_embed
    ):
        """Test on_guild_update with no changes."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_server_update": True}

        # Set same values for both before and after
        mock_guild_before.name = mock_guild.name
        mock_guild_before.icon.url = mock_guild.icon.url
        mock_guild_before.owner_id = mock_guild.owner_id

        # Mock empty fields list
        mock_embed.fields = []

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Should not send a message if no changes
        mock_dal.get_server.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_guild_update.ServersDal')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.send_msg_to_system_channel')
    async def test_on_guild_update_disabled_notifications(
        self,
        mock_send_msg,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_guild_before,
        mock_guild,
        mock_embed,
    ):
        """Test on_guild_update with disabled notifications."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Setup database mock with disabled notifications
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_server_update": False}

        # Set different names to trigger change detection
        mock_guild_before.name = "Old Test Server"
        mock_guild.name = "New Test Server"
        mock_guild_before.icon.url = mock_guild.icon.url
        mock_guild_before.owner_id = mock_guild.owner_id

        # Mock fields being added
        mock_embed.fields = [MagicMock()]

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Should not send message if notifications disabled
        mock_send_msg.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_guild_update.ServersDal')
    async def test_on_guild_update_no_server_config(
        self,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_guild_before,
        mock_guild,
        mock_embed,
    ):
        """Test on_guild_update with no server config."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Setup database mock with no config
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = None

        # Set different names to trigger change detection
        mock_guild_before.name = "Old Test Server"
        mock_guild.name = "New Test Server"
        mock_guild_before.icon.url = mock_guild.icon.url
        mock_guild_before.owner_id = mock_guild.owner_id

        # Mock fields being added
        mock_embed.fields = [MagicMock()]

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Should get server config but not send message
        mock_dal.get_server.assert_called_once_with(mock_guild.id)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    async def test_on_guild_update_bot_no_avatar(
        self,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_guild_before,
        mock_guild,
        mock_embed,
    ):
        """Test on_guild_update with bot having no avatar."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Set bot to have no avatar
        mock_bot.user.avatar = None
        mock_guild_before.name = "Old Test Server"
        mock_guild.name = "New Test Server"
        mock_guild_before.icon.url = mock_guild.icon.url
        mock_guild_before.owner_id = mock_guild.owner_id

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Should set footer with None icon_url
        mock_embed.set_footer.assert_called_with(icon_url=None, text="2023-01-01 12:00:00 UTC")

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_guild_update.ServersDal')
    async def test_on_guild_update_database_error(
        self,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_guild_before,
        mock_guild,
        mock_embed,
    ):
        """Test on_guild_update with database error."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Setup database mock to raise exception
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.side_effect = Exception("Database error")

        # Set different names to trigger change detection
        mock_guild_before.name = "Old Test Server"
        mock_guild.name = "New Test Server"
        mock_guild_before.icon.url = mock_guild.icon.url
        mock_guild_before.owner_id = mock_guild.owner_id

        # Mock fields being added
        mock_embed.fields = [MagicMock()]

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Should log error
        mock_bot.log.error.assert_called()
        error_call = mock_bot.log.error.call_args[0][0]
        assert "Failed to send guild update notification" in error_call

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    async def test_on_guild_update_general_error(self, mock_get_embed, mock_bot, mock_guild_before, mock_guild):
        """Test on_guild_update with general error."""
        # Setup embed to raise exception
        mock_get_embed.side_effect = Exception("General error")

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Should log error
        mock_bot.log.error.assert_called()
        error_call = mock_bot.log.error.call_args[0][0]
        assert "Error in on_guild_update" in error_call
        assert mock_guild.name in error_call

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_guild_update.ServersDal')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.send_msg_to_system_channel')
    async def test_on_guild_update_icon_url_change(
        self,
        mock_send_msg,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_guild_before,
        mock_guild,
        mock_embed,
    ):
        """Test on_guild_update with icon URL changed."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"
        # Mock embed fields to simulate having fields after add_field is called
        mock_embed.fields = [MagicMock()]  # Simulate one field added

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_server_update": True}

        # Set guild to have different icon URL
        mock_guild_before.icon.url = "https://example.com/old_icon.png"
        mock_guild.icon = MagicMock()
        mock_guild.icon.url = "https://example.com/new_icon.png"  # Different URL to trigger change
        mock_guild_before.name = mock_guild.name
        mock_guild_before.owner_id = mock_guild.owner_id

        # Mock fields being added
        mock_embed.fields = [MagicMock()]

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Should handle icon change
        mock_embed.add_field.assert_called_with(name=messages.NEW_SERVER_ICON, value="")
        mock_send_msg.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    async def test_on_guild_update_null_name_before(
        self, mock_datetime, mock_get_embed, mock_bot, mock_guild_before, mock_guild, mock_embed
    ):
        """Test on_guild_update with null name before."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"
        # Mock embed fields to simulate having fields after add_field is called
        mock_embed.fields = [MagicMock()]  # Simulate one field added

        # Set before name to None
        mock_guild_before.name = None
        mock_guild.name = "New Test Server"
        mock_guild_before.icon.url = mock_guild.icon.url
        mock_guild_before.owner_id = mock_guild.owner_id

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Should only add new name field (not previous)
        mock_embed.add_field.assert_called_with(name=messages.NEW_SERVER_NAME, value="New Test Server")

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_guild_update.bot_utils.get_current_date_time_str_long')
    async def test_on_guild_update_null_owner_before(
        self,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_guild_before,
        mock_guild,
        mock_embed,
    ):
        """Test on_guild_update with null owner_id before."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"
        # Mock embed fields to simulate having fields after add_field is called
        mock_embed.fields = [MagicMock()]  # Simulate one field added

        # Set before owner_id to None
        mock_guild_before.owner_id = None
        mock_guild.owner_id = 98765
        mock_guild_before.name = mock_guild.name
        mock_guild_before.icon.url = mock_guild.icon.url

        cog = OnGuildUpdate(mock_bot)
        on_guild_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_guild_update_event(mock_guild_before, mock_guild)

        # Should only add new owner field (not previous)
        mock_embed.add_field.assert_called_with(name=messages.NEW_SERVER_OWNER, value=str(mock_guild.owner))
