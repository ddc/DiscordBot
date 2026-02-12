"""Comprehensive tests for member join, member remove, and user update event cogs."""

# Mock problematic imports before importing the module
import discord
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.events.on_member_join import (
    MemberJoinHandler,
    OnMemberJoin,
    WelcomeMessageBuilder,
)
from src.bot.cogs.events.on_member_remove import (
    FarewellMessageBuilder,
    MemberLeaveHandler,
    OnMemberRemove,
)
from src.bot.cogs.events.on_user_update import OnUserUpdate
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
    bot.user.id = 99999
    bot.user.avatar = MagicMock()
    bot.user.avatar.url = "https://example.com/bot.png"
    bot.event = MagicMock(side_effect=lambda func: func)
    bot.add_cog = AsyncMock()
    return bot


@pytest.fixture
def mock_member():
    """Create a mock member instance for join/leave events."""
    member = MagicMock()
    member.id = 12345
    member.name = "TestUser"
    member.display_name = "TestUser"
    member.bot = False
    member.avatar = MagicMock()
    member.avatar.url = "https://example.com/avatar.png"
    member.guild = MagicMock()
    member.guild.id = 67890
    member.guild.name = "Test Server"
    member.__str__ = MagicMock(return_value="TestUser#1234")
    return member


# ============================================================
# Tests for on_member_join.py - WelcomeMessageBuilder
# ============================================================


class TestWelcomeMessageBuilder:
    """Test cases for WelcomeMessageBuilder class."""

    def test_init(self, mock_bot):
        """Test WelcomeMessageBuilder initialization."""
        builder = WelcomeMessageBuilder(mock_bot)
        assert builder.bot == mock_bot

    @patch('src.bot.cogs.events.on_member_join.bot_utils.get_current_date_time_str_long')
    def test_create_join_embed_with_avatar(self, mock_datetime, mock_bot, mock_member):
        """Test create_join_embed when member has an avatar."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        builder = WelcomeMessageBuilder(mock_bot)

        result = builder.create_join_embed(mock_member)

        assert isinstance(result, discord.Embed)
        assert result.color == discord.Color.green()
        assert result.description == str(mock_member)
        assert result.thumbnail.url == mock_member.avatar.url
        assert result.author.name == messages.JOINED_THE_SERVER
        assert result.footer.text == "2023-06-15 10:30:00 UTC"
        assert result.footer.icon_url == mock_bot.user.avatar.url

    @patch('src.bot.cogs.events.on_member_join.bot_utils.get_current_date_time_str_long')
    def test_create_join_embed_without_avatar(self, mock_datetime, mock_bot, mock_member):
        """Test create_join_embed when member has no avatar."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        mock_member.avatar = None
        builder = WelcomeMessageBuilder(mock_bot)

        result = builder.create_join_embed(mock_member)

        assert isinstance(result, discord.Embed)
        assert result.color == discord.Color.green()
        assert result.description == str(mock_member)
        # Thumbnail should not be set when avatar is None
        assert result.thumbnail.url is None

    @patch('src.bot.cogs.events.on_member_join.bot_utils.get_current_date_time_str_long')
    def test_create_join_embed_with_exception(self, mock_datetime, mock_bot, mock_member):
        """Test create_join_embed when an exception occurs."""
        mock_datetime.side_effect = Exception("DateTime error")
        builder = WelcomeMessageBuilder(mock_bot)

        result = builder.create_join_embed(mock_member)

        # Should return fallback embed
        assert isinstance(result, discord.Embed)
        assert result.color == discord.Color.green()
        assert "joined the server!" in result.description
        mock_bot.log.error.assert_called_once()

    @patch('src.bot.cogs.events.on_member_join.bot_utils.get_current_date_time_str_long')
    def test_create_join_message_success(self, mock_datetime, mock_bot, mock_member):
        """Test create_join_message with successful execution."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        builder = WelcomeMessageBuilder(mock_bot)

        result = builder.create_join_message(mock_member)

        expected = f"TestUser {messages.JOINED_THE_SERVER}\n2023-06-15 10:30:00"
        assert result == expected

    @patch('src.bot.cogs.events.on_member_join.bot_utils.get_current_date_time_str_long')
    def test_create_join_message_exception(self, mock_datetime, mock_bot, mock_member):
        """Test create_join_message when an exception occurs."""
        mock_datetime.side_effect = Exception("DateTime error")
        builder = WelcomeMessageBuilder(mock_bot)

        result = builder.create_join_message(mock_member)

        assert result == "TestUser joined the server!"
        mock_bot.log.error.assert_called_once()


# ============================================================
# Tests for on_member_join.py - MemberJoinHandler
# ============================================================


class TestMemberJoinHandler:
    """Test cases for MemberJoinHandler class."""

    def test_init(self, mock_bot):
        """Test MemberJoinHandler initialization."""
        handler = MemberJoinHandler(mock_bot)
        assert handler.bot == mock_bot
        assert isinstance(handler.message_builder, WelcomeMessageBuilder)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_join.ServersDal')
    async def test_process_member_join_no_config(self, mock_dal_class, mock_bot, mock_member):
        """Test process_member_join when no server config is found."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = None

        handler = MemberJoinHandler(mock_bot)
        await handler.process_member_join(mock_member)

        mock_dal.get_server.assert_called_once_with(mock_member.guild.id)
        mock_bot.log.warning.assert_called_once()
        assert "No server config found" in mock_bot.log.warning.call_args[0][0]

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_join.ServersDal')
    async def test_process_member_join_msg_on_join_false(self, mock_dal_class, mock_bot, mock_member):
        """Test process_member_join when msg_on_join is False."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_join": False}

        handler = MemberJoinHandler(mock_bot)
        await handler.process_member_join(mock_member)

        mock_dal.get_server.assert_called_once_with(mock_member.guild.id)
        # Should not log info about sending welcome message
        mock_bot.log.info.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_join.bot_utils.send_msg_to_system_channel', new_callable=AsyncMock)
    @patch('src.bot.cogs.events.on_member_join.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_member_join.ServersDal')
    async def test_process_member_join_msg_on_join_true(
        self, mock_dal_class, mock_datetime, mock_send_msg, mock_bot, mock_member
    ):
        """Test process_member_join when msg_on_join is True."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_join": True}

        handler = MemberJoinHandler(mock_bot)
        await handler.process_member_join(mock_member)

        mock_dal.get_server.assert_called_once_with(mock_member.guild.id)
        mock_send_msg.assert_called_once()
        mock_bot.log.info.assert_called_once()
        assert "Welcome message sent" in mock_bot.log.info.call_args[0][0]

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_join.ServersDal')
    async def test_process_member_join_exception(self, mock_dal_class, mock_bot, mock_member):
        """Test process_member_join when an exception occurs."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.side_effect = Exception("Database error")

        handler = MemberJoinHandler(mock_bot)
        await handler.process_member_join(mock_member)

        mock_bot.log.error.assert_called_once()
        assert "Error processing member join" in mock_bot.log.error.call_args[0][0]

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_join.bot_utils.send_msg_to_system_channel', new_callable=AsyncMock)
    @patch('src.bot.cogs.events.on_member_join.bot_utils.get_current_date_time_str_long')
    async def test_send_welcome_message_success(self, mock_datetime, mock_send_msg, mock_bot, mock_member):
        """Test _send_welcome_message with successful execution."""
        mock_datetime.return_value = "2023-06-15 10:30:00"

        handler = MemberJoinHandler(mock_bot)
        await handler._send_welcome_message(mock_member)

        mock_send_msg.assert_called_once()
        call_args = mock_send_msg.call_args[0]
        assert call_args[0] == mock_bot.log
        assert call_args[1] == mock_member.guild
        assert isinstance(call_args[2], discord.Embed)
        assert isinstance(call_args[3], str)
        mock_bot.log.info.assert_called_once()
        assert "Welcome message sent" in mock_bot.log.info.call_args[0][0]

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_join.bot_utils.send_msg_to_system_channel', new_callable=AsyncMock)
    @patch('src.bot.cogs.events.on_member_join.bot_utils.get_current_date_time_str_long')
    async def test_send_welcome_message_exception(self, mock_datetime, mock_send_msg, mock_bot, mock_member):
        """Test _send_welcome_message when an exception occurs."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        mock_send_msg.side_effect = Exception("Send error")

        handler = MemberJoinHandler(mock_bot)
        await handler._send_welcome_message(mock_member)

        mock_bot.log.error.assert_called_once()
        assert "Failed to send welcome message" in mock_bot.log.error.call_args[0][0]


# ============================================================
# Tests for on_member_join.py - OnMemberJoin
# ============================================================


class TestOnMemberJoin:
    """Test cases for OnMemberJoin cog."""

    def test_init(self, mock_bot):
        """Test OnMemberJoin cog initialization."""
        cog = OnMemberJoin(mock_bot)
        assert cog.bot == mock_bot
        assert isinstance(cog.join_handler, MemberJoinHandler)
        # Verify event was registered
        mock_bot.event.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function for OnMemberJoin."""
        from src.bot.cogs.events.on_member_join import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnMemberJoin)
        assert added_cog.bot == mock_bot


# ============================================================
# Tests for on_member_remove.py - FarewellMessageBuilder
# ============================================================


class TestFarewellMessageBuilder:
    """Test cases for FarewellMessageBuilder class."""

    def test_init(self, mock_bot):
        """Test FarewellMessageBuilder initialization."""
        builder = FarewellMessageBuilder(mock_bot)
        assert builder.bot == mock_bot

    @patch('src.bot.cogs.events.on_member_remove.bot_utils.get_current_date_time_str_long')
    def test_create_leave_embed_with_avatar(self, mock_datetime, mock_bot, mock_member):
        """Test create_leave_embed when member has an avatar."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        builder = FarewellMessageBuilder(mock_bot)

        result = builder.create_leave_embed(mock_member)

        assert isinstance(result, discord.Embed)
        assert result.color == discord.Color.red()
        assert result.description == str(mock_member)
        assert result.thumbnail.url == mock_member.avatar.url
        assert result.author.name == messages.LEFT_THE_SERVER
        assert result.footer.text == "2023-06-15 10:30:00 UTC"
        assert result.footer.icon_url == mock_bot.user.avatar.url

    @patch('src.bot.cogs.events.on_member_remove.bot_utils.get_current_date_time_str_long')
    def test_create_leave_embed_without_avatar(self, mock_datetime, mock_bot, mock_member):
        """Test create_leave_embed when member has no avatar."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        mock_member.avatar = None
        builder = FarewellMessageBuilder(mock_bot)

        result = builder.create_leave_embed(mock_member)

        assert isinstance(result, discord.Embed)
        assert result.color == discord.Color.red()
        assert result.description == str(mock_member)
        # Thumbnail should not be set when avatar is None
        assert result.thumbnail.url is None

    @patch('src.bot.cogs.events.on_member_remove.bot_utils.get_current_date_time_str_long')
    def test_create_leave_embed_with_exception(self, mock_datetime, mock_bot, mock_member):
        """Test create_leave_embed when an exception occurs."""
        mock_datetime.side_effect = Exception("DateTime error")
        builder = FarewellMessageBuilder(mock_bot)

        result = builder.create_leave_embed(mock_member)

        # Should return fallback embed
        assert isinstance(result, discord.Embed)
        assert result.color == discord.Color.red()
        assert "left the server!" in result.description
        mock_bot.log.error.assert_called_once()

    @patch('src.bot.cogs.events.on_member_remove.bot_utils.get_current_date_time_str_long')
    def test_create_leave_message_success(self, mock_datetime, mock_bot, mock_member):
        """Test create_leave_message with successful execution."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        builder = FarewellMessageBuilder(mock_bot)

        result = builder.create_leave_message(mock_member)

        expected = f"TestUser {messages.LEFT_THE_SERVER}\n2023-06-15 10:30:00"
        assert result == expected

    @patch('src.bot.cogs.events.on_member_remove.bot_utils.get_current_date_time_str_long')
    def test_create_leave_message_exception(self, mock_datetime, mock_bot, mock_member):
        """Test create_leave_message when an exception occurs."""
        mock_datetime.side_effect = Exception("DateTime error")
        builder = FarewellMessageBuilder(mock_bot)

        result = builder.create_leave_message(mock_member)

        assert result == "TestUser left the server!"
        mock_bot.log.error.assert_called_once()


# ============================================================
# Tests for on_member_remove.py - MemberLeaveHandler
# ============================================================


class TestMemberLeaveHandler:
    """Test cases for MemberLeaveHandler class."""

    def test_init(self, mock_bot):
        """Test MemberLeaveHandler initialization."""
        handler = MemberLeaveHandler(mock_bot)
        assert handler.bot == mock_bot
        assert isinstance(handler.message_builder, FarewellMessageBuilder)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_remove.ServersDal')
    async def test_process_member_leave_bot_is_member(self, mock_dal_class, mock_bot, mock_member):
        """Test process_member_leave when the bot itself is the member leaving."""
        mock_member.id = mock_bot.user.id  # Same ID as bot

        handler = MemberLeaveHandler(mock_bot)
        await handler.process_member_leave(mock_member)

        # Should return early, not call ServersDal
        mock_dal_class.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_remove.ServersDal')
    async def test_process_member_leave_no_config(self, mock_dal_class, mock_bot, mock_member):
        """Test process_member_leave when no server config is found."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = None

        handler = MemberLeaveHandler(mock_bot)
        await handler.process_member_leave(mock_member)

        mock_dal.get_server.assert_called_once_with(mock_member.guild.id)
        mock_bot.log.warning.assert_called_once()
        assert "No server config found" in mock_bot.log.warning.call_args[0][0]

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_remove.ServersDal')
    async def test_process_member_leave_msg_on_leave_false(self, mock_dal_class, mock_bot, mock_member):
        """Test process_member_leave when msg_on_leave is False."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_leave": False}

        handler = MemberLeaveHandler(mock_bot)
        await handler.process_member_leave(mock_member)

        mock_dal.get_server.assert_called_once_with(mock_member.guild.id)
        # Should not log info about sending farewell message
        mock_bot.log.info.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_remove.bot_utils.send_msg_to_system_channel', new_callable=AsyncMock)
    @patch('src.bot.cogs.events.on_member_remove.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_member_remove.ServersDal')
    async def test_process_member_leave_msg_on_leave_true(
        self, mock_dal_class, mock_datetime, mock_send_msg, mock_bot, mock_member
    ):
        """Test process_member_leave when msg_on_leave is True."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_leave": True}

        handler = MemberLeaveHandler(mock_bot)
        await handler.process_member_leave(mock_member)

        mock_dal.get_server.assert_called_once_with(mock_member.guild.id)
        mock_send_msg.assert_called_once()
        mock_bot.log.info.assert_called_once()
        assert "Farewell message sent" in mock_bot.log.info.call_args[0][0]

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_remove.ServersDal')
    async def test_process_member_leave_exception(self, mock_dal_class, mock_bot, mock_member):
        """Test process_member_leave when an exception occurs."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.side_effect = Exception("Database error")

        handler = MemberLeaveHandler(mock_bot)
        await handler.process_member_leave(mock_member)

        mock_bot.log.error.assert_called_once()
        assert "Error processing member leave" in mock_bot.log.error.call_args[0][0]

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_remove.bot_utils.send_msg_to_system_channel', new_callable=AsyncMock)
    @patch('src.bot.cogs.events.on_member_remove.bot_utils.get_current_date_time_str_long')
    async def test_send_farewell_message_success(self, mock_datetime, mock_send_msg, mock_bot, mock_member):
        """Test _send_farewell_message with successful execution."""
        mock_datetime.return_value = "2023-06-15 10:30:00"

        handler = MemberLeaveHandler(mock_bot)
        await handler._send_farewell_message(mock_member)

        mock_send_msg.assert_called_once()
        call_args = mock_send_msg.call_args[0]
        assert call_args[0] == mock_bot.log
        assert call_args[1] == mock_member.guild
        assert isinstance(call_args[2], discord.Embed)
        assert isinstance(call_args[3], str)
        mock_bot.log.info.assert_called_once()
        assert "Farewell message sent" in mock_bot.log.info.call_args[0][0]

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_member_remove.bot_utils.send_msg_to_system_channel', new_callable=AsyncMock)
    @patch('src.bot.cogs.events.on_member_remove.bot_utils.get_current_date_time_str_long')
    async def test_send_farewell_message_exception(self, mock_datetime, mock_send_msg, mock_bot, mock_member):
        """Test _send_farewell_message when an exception occurs."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        mock_send_msg.side_effect = Exception("Send error")

        handler = MemberLeaveHandler(mock_bot)
        await handler._send_farewell_message(mock_member)

        mock_bot.log.error.assert_called_once()
        assert "Failed to send farewell message" in mock_bot.log.error.call_args[0][0]


# ============================================================
# Tests for on_member_remove.py - OnMemberRemove
# ============================================================


class TestOnMemberRemove:
    """Test cases for OnMemberRemove cog."""

    def test_init(self, mock_bot):
        """Test OnMemberRemove cog initialization."""
        cog = OnMemberRemove(mock_bot)
        assert cog.bot == mock_bot
        assert isinstance(cog.leave_handler, MemberLeaveHandler)
        # Verify event was registered
        mock_bot.event.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function for OnMemberRemove."""
        from src.bot.cogs.events.on_member_remove import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnMemberRemove)
        assert added_cog.bot == mock_bot


# ============================================================
# Tests for on_user_update.py - OnUserUpdate
# ============================================================


class TestOnUserUpdate:
    """Test cases for OnUserUpdate cog."""

    def test_init(self, mock_bot):
        """Test OnUserUpdate cog initialization."""
        cog = OnUserUpdate(mock_bot)
        assert cog.bot == mock_bot
        # Verify event was registered
        mock_bot.event.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function for OnUserUpdate."""
        from src.bot.cogs.events.on_user_update import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnUserUpdate)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_user_update.bot_utils.get_embed')
    async def test_on_user_update_bot_user(self, mock_get_embed, mock_bot):
        """Test on_user_update with a bot user (should return early)."""
        before = MagicMock()
        after = MagicMock()
        after.bot = True

        OnUserUpdate(mock_bot)
        on_user_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_user_update_event(before, after)

        # Should not process bot users
        mock_get_embed.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_user_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_user_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_user_update.ServersDal')
    @patch('src.bot.cogs.events.on_user_update.bot_utils.send_msg_to_system_channel', new_callable=AsyncMock)
    async def test_on_user_update_avatar_change(
        self, mock_send_msg, mock_dal_class, mock_datetime, mock_get_embed, mock_bot
    ):
        """Test on_user_update when avatar changes."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        embed = discord.Embed()
        mock_get_embed.return_value = embed

        # Setup before/after with different avatars
        before = MagicMock()
        before.avatar = MagicMock()
        before.avatar.url = "https://example.com/old_avatar.png"
        before.name = "TestUser"
        before.discriminator = "1234"

        after = MagicMock()
        after.bot = False
        after.display_name = "TestUser"
        after.avatar = MagicMock()
        after.avatar.url = "https://example.com/new_avatar.png"
        after.name = "TestUser"
        after.discriminator = "1234"

        guild = MagicMock()
        guild.id = 67890
        after.mutual_guilds = [guild]

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_member_update": True}

        OnUserUpdate(mock_bot)
        on_user_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_user_update_event(before, after)

        # Verify embed has avatar field
        field_names = [f.name for f in embed.fields]
        assert messages.NEW_AVATAR in field_names
        assert embed.thumbnail.url == after.avatar.url

        # Verify message was sent
        mock_send_msg.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_user_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_user_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_user_update.ServersDal')
    @patch('src.bot.cogs.events.on_user_update.bot_utils.send_msg_to_system_channel', new_callable=AsyncMock)
    async def test_on_user_update_name_change(
        self, mock_send_msg, mock_dal_class, mock_datetime, mock_get_embed, mock_bot
    ):
        """Test on_user_update when name changes."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        embed = discord.Embed()
        mock_get_embed.return_value = embed

        # Setup before/after with different names
        before = MagicMock()
        before.avatar = MagicMock()
        before.avatar.url = "https://example.com/avatar.png"
        before.name = "OldName"
        before.discriminator = "1234"

        after = MagicMock()
        after.bot = False
        after.display_name = "NewName"
        after.avatar = MagicMock()
        after.avatar.url = "https://example.com/avatar.png"
        after.name = "NewName"
        after.discriminator = "1234"

        guild = MagicMock()
        guild.id = 67890
        after.mutual_guilds = [guild]

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_member_update": True}

        OnUserUpdate(mock_bot)
        on_user_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_user_update_event(before, after)

        # Verify embed has name fields
        field_names = [f.name for f in embed.fields]
        assert messages.PREVIOUS_NAME in field_names
        assert messages.NEW_NAME in field_names

        # Verify message was sent
        mock_send_msg.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_user_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_user_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_user_update.ServersDal')
    @patch('src.bot.cogs.events.on_user_update.bot_utils.send_msg_to_system_channel', new_callable=AsyncMock)
    async def test_on_user_update_discriminator_change(
        self, mock_send_msg, mock_dal_class, mock_datetime, mock_get_embed, mock_bot
    ):
        """Test on_user_update when discriminator changes."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        embed = discord.Embed()
        mock_get_embed.return_value = embed

        # Setup before/after with different discriminators
        before = MagicMock()
        before.avatar = MagicMock()
        before.avatar.url = "https://example.com/avatar.png"
        before.name = "TestUser"
        before.discriminator = "1234"

        after = MagicMock()
        after.bot = False
        after.display_name = "TestUser"
        after.avatar = MagicMock()
        after.avatar.url = "https://example.com/avatar.png"
        after.name = "TestUser"
        after.discriminator = "5678"

        guild = MagicMock()
        guild.id = 67890
        after.mutual_guilds = [guild]

        # Setup database mock
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_server.return_value = {"msg_on_member_update": True}

        OnUserUpdate(mock_bot)
        on_user_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_user_update_event(before, after)

        # Verify embed has discriminator fields
        field_names = [f.name for f in embed.fields]
        assert messages.PREVIOUS_DISCRIMINATOR in field_names
        assert messages.NEW_DISCRIMINATOR in field_names

        # Verify message was sent
        mock_send_msg.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_user_update.bot_utils.get_embed')
    @patch('src.bot.cogs.events.on_user_update.bot_utils.get_current_date_time_str_long')
    @patch('src.bot.cogs.events.on_user_update.ServersDal')
    @patch('src.bot.cogs.events.on_user_update.bot_utils.send_msg_to_system_channel', new_callable=AsyncMock)
    async def test_on_user_update_no_changes(
        self, mock_send_msg, mock_dal_class, mock_datetime, mock_get_embed, mock_bot
    ):
        """Test on_user_update with no changes (embed.fields == 0)."""
        mock_datetime.return_value = "2023-06-15 10:30:00"
        embed = discord.Embed()
        mock_get_embed.return_value = embed

        # Setup before/after with identical values
        before = MagicMock()
        before.avatar = MagicMock()
        before.avatar.url = "https://example.com/avatar.png"
        before.name = "TestUser"
        before.discriminator = "1234"

        after = MagicMock()
        after.bot = False
        after.display_name = "TestUser"
        after.avatar = MagicMock()
        after.avatar.url = "https://example.com/avatar.png"
        after.name = "TestUser"
        after.discriminator = "1234"

        OnUserUpdate(mock_bot)
        on_user_update_event = mock_bot.event.call_args_list[0][0][0]

        await on_user_update_event(before, after)

        # Verify no fields were added
        assert len(embed.fields) == 0

        # Should not send any message
        mock_send_msg.assert_not_called()
        mock_dal_class.assert_not_called()


# ============================================================
# Tests for on_member_join.py - Inner event function (lines 138-142)
# ============================================================


class TestOnMemberJoinEvent:
    """Test cases for the inner on_member_join event function registered in OnMemberJoin.__init__."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot instance."""
        bot = AsyncMock()
        bot.log = MagicMock()
        bot.log.error = MagicMock()
        bot.log.info = MagicMock()
        bot.log.warning = MagicMock()
        bot.db_session = MagicMock()
        bot.user = MagicMock()
        bot.user.id = 99999
        bot.user.avatar = MagicMock()
        bot.user.avatar.url = "https://example.com/bot.png"
        bot.event = MagicMock(side_effect=lambda func: func)
        bot.add_cog = AsyncMock()
        return bot

    @pytest.fixture
    def mock_member(self):
        """Create a mock member instance."""
        member = MagicMock()
        member.id = 12345
        member.name = "TestUser"
        member.display_name = "TestUser"
        member.bot = False
        member.avatar = MagicMock()
        member.avatar.url = "https://example.com/avatar.png"
        member.guild = MagicMock()
        member.guild.id = 67890
        member.guild.name = "Test Server"
        member.__str__ = MagicMock(return_value="TestUser#1234")
        return member

    @pytest.mark.asyncio
    async def test_on_member_join_event_calls_handler(self, mock_bot, mock_member):
        """Test that the on_member_join event calls the join handler."""
        cog = OnMemberJoin(mock_bot)
        # Get the registered event function
        on_member_join_event = mock_bot.event.call_args_list[0][0][0]

        with patch.object(cog.join_handler, 'process_member_join', new_callable=AsyncMock) as mock_process:
            await on_member_join_event(mock_member)
            mock_process.assert_called_once_with(mock_member)
            mock_bot.log.info.assert_called_once()
            assert "Member joined" in mock_bot.log.info.call_args[0][0]

    @pytest.mark.asyncio
    async def test_on_member_join_event_handles_exception(self, mock_bot, mock_member):
        """Test that on_member_join catches exceptions and logs critical error."""
        cog = OnMemberJoin(mock_bot)
        on_member_join_event = mock_bot.event.call_args_list[0][0][0]

        with patch.object(
            cog.join_handler, 'process_member_join', new_callable=AsyncMock, side_effect=RuntimeError("fail")
        ):
            await on_member_join_event(mock_member)
            mock_bot.log.error.assert_called_once()
            assert "Critical error" in mock_bot.log.error.call_args[0][0]


# ============================================================
# Tests for on_member_remove.py - Inner event function (lines 143-147)
# ============================================================


class TestOnMemberRemoveEvent:
    """Test cases for the inner on_member_remove event function registered in OnMemberRemove.__init__."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot instance."""
        bot = AsyncMock()
        bot.log = MagicMock()
        bot.log.error = MagicMock()
        bot.log.info = MagicMock()
        bot.log.warning = MagicMock()
        bot.db_session = MagicMock()
        bot.user = MagicMock()
        bot.user.id = 99999
        bot.user.avatar = MagicMock()
        bot.user.avatar.url = "https://example.com/bot.png"
        bot.event = MagicMock(side_effect=lambda func: func)
        bot.add_cog = AsyncMock()
        return bot

    @pytest.fixture
    def mock_member(self):
        """Create a mock member instance."""
        member = MagicMock()
        member.id = 12345
        member.name = "TestUser"
        member.display_name = "TestUser"
        member.bot = False
        member.avatar = MagicMock()
        member.avatar.url = "https://example.com/avatar.png"
        member.guild = MagicMock()
        member.guild.id = 67890
        member.guild.name = "Test Server"
        member.__str__ = MagicMock(return_value="TestUser#1234")
        return member

    @pytest.mark.asyncio
    async def test_on_member_remove_event_calls_handler(self, mock_bot, mock_member):
        """Test that the on_member_remove event calls the leave handler."""
        cog = OnMemberRemove(mock_bot)
        # Get the registered event function
        on_member_remove_event = mock_bot.event.call_args_list[0][0][0]

        with patch.object(cog.leave_handler, 'process_member_leave', new_callable=AsyncMock) as mock_process:
            await on_member_remove_event(mock_member)
            mock_process.assert_called_once_with(mock_member)
            mock_bot.log.info.assert_called_once()
            assert "Member left" in mock_bot.log.info.call_args[0][0]

    @pytest.mark.asyncio
    async def test_on_member_remove_event_handles_exception(self, mock_bot, mock_member):
        """Test that on_member_remove catches exceptions and logs critical error."""
        cog = OnMemberRemove(mock_bot)
        on_member_remove_event = mock_bot.event.call_args_list[0][0][0]

        with patch.object(
            cog.leave_handler, 'process_member_leave', new_callable=AsyncMock, side_effect=RuntimeError("fail")
        ):
            await on_member_remove_event(mock_member)
            mock_bot.log.error.assert_called_once()
            assert "Critical error" in mock_bot.log.error.call_args[0][0]
