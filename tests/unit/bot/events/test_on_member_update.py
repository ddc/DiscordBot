"""Comprehensive tests for the OnMemberUpdate event cog."""

# Mock problematic imports before importing the module
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.events.on_member_update import OnMemberUpdate
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
    return bot


@pytest.fixture
def on_member_update_cog(mock_bot):
    """Create an OnMemberUpdate cog instance."""
    return OnMemberUpdate(mock_bot)


@pytest.fixture
def mock_member():
    """Create a mock member instance."""
    member = MagicMock()
    member.bot = False
    member.display_name = "TestUser"
    member.avatar = MagicMock()
    member.avatar.url = "https://example.com/avatar.png"
    member.nick = "TestNick"
    member.guild = MagicMock()
    member.guild.id = 12345
    member.guild.name = "Test Server"

    # Create mock roles
    role1 = MagicMock()
    role1.name = "Member"
    role2 = MagicMock()
    role2.name = "Verified"
    member.roles = [role1, role2]

    return member


@pytest.fixture
def mock_member_before():
    """Create a mock member before update."""
    member = MagicMock()
    member.bot = False
    member.display_name = "OldTestUser"
    member.avatar = MagicMock()
    member.avatar.url = "https://example.com/old_avatar.png"
    member.nick = "OldNick"
    member.guild = MagicMock()
    member.guild.id = 12345
    member.guild.name = "Test Server"

    # Create mock roles
    role1 = MagicMock()
    role1.name = "Member"
    member.roles = [role1]

    return member


@pytest.fixture
def mock_embed():
    """Create a mock embed."""
    embed = MagicMock()
    embed.fields = []
    embed.add_field = MagicMock()
    embed.set_author = MagicMock()
    embed.set_footer = MagicMock()
    return embed


class TestOnMemberUpdate:
    """Test cases for OnMemberUpdate cog."""

    def test_init(self, mock_bot):
        """Test OnMemberUpdate cog initialization."""
        cog = OnMemberUpdate(mock_bot)
        assert cog.bot == mock_bot

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_member_update import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnMemberUpdate)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_member_update.ServersDal')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.send_msg_to_system_channel')
    async def test_on_member_update_bot_member(
        self,
        mock_send_msg,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
    ):
        """Test on_member_update with bot member (should be skipped)."""
        mock_member.bot = True
        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Should not process bot members
        mock_get_embed.assert_not_called()
        mock_send_msg.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_member_update.ServersDal')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.send_msg_to_system_channel')
    async def test_on_member_update_nickname_change(
        self,
        mock_send_msg,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
        mock_embed,
    ):
        """Test on_member_update with nickname change."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_member_update": True}

        # Set different nicknames
        mock_member_before.nick = "OldNick"
        mock_member.nick = "NewNick"
        mock_member_before.roles = mock_member.roles  # Same roles

        # Mock embed fields to simulate having fields after add_field is called
        mock_embed.fields = [MagicMock()]  # Simulate one field added

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Verify embed setup
        mock_embed.set_author.assert_called_with(name=mock_member.display_name, icon_url=mock_member.avatar.url)
        mock_embed.set_footer.assert_called_with(icon_url=mock_bot.user.avatar.url, text="2023-01-01 12:00:00 UTC")

        # Verify nickname fields added
        mock_embed.add_field.assert_any_call(name=messages.PREVIOUS_NICKNAME, value="OldNick")
        mock_embed.add_field.assert_any_call(name=messages.NEW_NICKNAME, value="NewNick")

        # Verify message sent
        mock_send_msg.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_member_update.ServersDal')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.send_msg_to_system_channel')
    async def test_on_member_update_role_change(
        self,
        mock_send_msg,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
        mock_embed,
    ):
        """Test on_member_update with role change."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_member_update": True}

        # Set same nicknames but different roles
        mock_member_before.nick = mock_member.nick
        role1 = MagicMock()
        role1.name = "Member"
        role2 = MagicMock()
        role2.name = "Verified"
        role3 = MagicMock()
        role3.name = "Admin"

        mock_member_before.roles = [role1]
        mock_member.roles = [role1, role2, role3]

        # Mock embed fields to simulate having fields after add_field is called
        mock_embed.fields = [MagicMock()]  # Simulate one field added

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Verify role fields added
        mock_embed.add_field.assert_any_call(name=messages.PREVIOUS_ROLES, value="Member")
        mock_embed.add_field.assert_any_call(name=messages.NEW_ROLES, value="Member, Verified, Admin")

        # Verify message sent
        mock_send_msg.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_member_update.ServersDal')
    async def test_on_member_update_no_changes(
        self,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
        mock_embed,
    ):
        """Test on_member_update with no changes."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_member_update": True}

        # Set same values for both before and after
        mock_member_before.nick = mock_member.nick
        mock_member_before.roles = mock_member.roles

        # Mock empty fields list
        mock_embed.fields = []

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Should not send message if no changes
        mock_dal.get_server.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_member_update.ServersDal')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.send_msg_to_system_channel')
    async def test_on_member_update_disabled_notifications(
        self,
        mock_send_msg,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
        mock_embed,
    ):
        """Test on_member_update with disabled notifications."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Setup database mock with disabled notifications
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_member_update": False}

        # Set different nicknames to trigger change detection
        mock_member_before.nick = "OldNick"
        mock_member.nick = "NewNick"
        mock_member_before.roles = mock_member.roles

        # Mock fields being added
        mock_embed.fields = [MagicMock()]

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Should not send message if notifications disabled
        mock_send_msg.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_member_update.ServersDal')
    async def test_on_member_update_no_server_config(
        self,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
        mock_embed,
    ):
        """Test on_member_update with no server config."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Setup database mock with no config
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = None

        # Set different nicknames to trigger change detection
        mock_member_before.nick = "OldNick"
        mock_member.nick = "NewNick"
        mock_member_before.roles = mock_member.roles

        # Mock fields being added
        mock_embed.fields = [MagicMock()]

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Should get server config but not send message
        mock_dal.get_server.assert_called_once_with(mock_member.guild.id)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    async def test_on_member_update_no_avatar(
        self,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
        mock_embed,
    ):
        """Test on_member_update with member having no avatar."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Set member to have no avatar
        mock_member.avatar = None
        mock_member_before.nick = "OldNick"
        mock_member.nick = "NewNick"
        mock_member_before.roles = mock_member.roles

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Should set author without icon_url
        mock_embed.set_author.assert_called_with(name=mock_member.display_name)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    async def test_on_member_update_bot_no_avatar(
        self,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
        mock_embed,
    ):
        """Test on_member_update with bot having no avatar."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Set bot to have no avatar
        mock_bot.user.avatar = None
        mock_member_before.nick = "OldNick"
        mock_member.nick = "NewNick"
        mock_member_before.roles = mock_member.roles

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Should set footer with None icon_url
        mock_embed.set_footer.assert_called_with(icon_url=None, text="2023-01-01 12:00:00 UTC")

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_member_update.ServersDal')
    async def test_on_member_update_database_error(
        self,
        mock_dal_class,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
        mock_embed,
    ):
        """Test on_member_update with database error."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Setup database mock to raise exception
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.side_effect = Exception("Database error")

        # Set different nicknames to trigger change detection
        mock_member_before.nick = "OldNick"
        mock_member.nick = "NewNick"
        mock_member_before.roles = mock_member.roles

        # Mock fields being added
        mock_embed.fields = [MagicMock()]

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Should log error
        mock_bot.log.error.assert_called()
        error_call = mock_bot.log.error.call_args[0][0]
        assert "Failed to send member update notification" in error_call

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    async def test_on_member_update_general_error(self, mock_get_embed, mock_bot, mock_member_before, mock_member):
        """Test on_member_update with general error."""
        # Setup embed to raise exception
        mock_get_embed.side_effect = Exception("General error")

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Should log error
        mock_bot.log.error.assert_called()
        error_call = mock_bot.log.error.call_args[0][0]
        assert "Error in on_member_update" in error_call
        assert str(mock_member) in error_call

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    async def test_on_member_update_null_nick_to_nick(
        self,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
        mock_embed,
    ):
        """Test on_member_update from null nickname to nickname."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Set before nick to None
        mock_member_before.nick = None
        mock_member.nick = "NewNick"
        mock_member_before.roles = mock_member.roles

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Should only add new nickname field (not previous)
        mock_embed.add_field.assert_called_with(name=messages.NEW_NICKNAME, value="NewNick")

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_member_update.bot_utils.get_current_date_time_str_long')
    async def test_on_member_update_null_roles(
        self,
        mock_datetime,
        mock_get_embed,
        mock_bot,
        mock_member_before,
        mock_member,
        mock_embed,
    ):
        """Test on_member_update with null roles before."""
        mock_get_embed.return_value = mock_embed
        mock_datetime.return_value = "2023-01-01 12:00:00"

        # Set before roles to None
        mock_member_before.roles = None
        role1 = MagicMock()
        role1.name = "Member"
        mock_member.roles = [role1]
        mock_member_before.nick = mock_member.nick

        cog = OnMemberUpdate(mock_bot)

        # Call the listener method directly
        await cog.on_member_update(mock_member_before, mock_member)

        # Should only add new roles field (not previous)
        mock_embed.add_field.assert_called_with(name=messages.NEW_ROLES, value="Member")
