"""Comprehensive tests for GW2 key cog."""

import pytest
from src.gw2.cogs.key import GW2Key, add, info, key, remove, update
from src.gw2.constants import gw2_messages
from src.gw2.tools.gw2_exceptions import APIInvalidKey
from unittest.mock import AsyncMock, MagicMock, patch


class TestGW2Key:
    """Test cases for the GW2Key cog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def gw2_key_cog(self, mock_bot):
        """Create a GW2Key cog instance."""
        return GW2Key(mock_bot)

    def test_gw2_key_initialization(self, mock_bot):
        """Test GW2Key cog initialization."""
        cog = GW2Key(mock_bot)
        assert cog.bot == mock_bot

    def test_gw2_key_inheritance(self, gw2_key_cog):
        """Test that GW2Key inherits from GuildWars2 properly."""
        from src.gw2.cogs.gw2 import GuildWars2

        assert isinstance(gw2_key_cog, GuildWars2)


class TestKeyGroupCommand:
    """Test cases for the key group command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.invoked_subcommand = None
        return ctx

    @pytest.mark.asyncio
    async def test_key_group_invokes_subcommand(self, mock_ctx):
        """Test that key group command calls invoke_subcommand."""
        with patch("src.gw2.cogs.key.bot_utils.invoke_subcommand") as mock_invoke:
            mock_invoke.return_value = None
            await key(mock_ctx)
            mock_invoke.assert_called_once_with(mock_ctx, "gw2 key")


class TestAddCommand:
    """Test cases for the key add command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.avatar = MagicMock()
        ctx.bot.user.avatar.url = "https://example.com/bot_avatar.png"
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.message.channel.guild = MagicMock()
        ctx.message.channel.guild.id = 99999
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.guild.icon = MagicMock()
        ctx.guild.icon.url = "https://example.com/icon.png"
        ctx.guild.name = "TestGuild"
        ctx.prefix = "!"
        ctx.author = MagicMock()
        ctx.author.id = 12345
        ctx.author.name = "TestUser"
        ctx.author.display_name = "TestUser"
        ctx.author.avatar = MagicMock()
        ctx.author.avatar.url = "https://example.com/avatar.png"
        ctx.author.send = AsyncMock()
        ctx.send = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_add_deletes_message_for_privacy(self, mock_ctx):
        """Test that add command deletes the user's message for privacy."""
        api_key = "test-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message") as mock_delete:
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                invalid_error = APIInvalidKey(mock_ctx.bot, f"(400) {gw2_messages.INVALID_APIKEY_MSG}")
                mock_client_instance.check_api_key = AsyncMock(return_value=invalid_error)
                with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                    mock_error.return_value = None
                    await add(mock_ctx, api_key)
                    mock_delete.assert_called_once_with(mock_ctx, warning=True)

    @pytest.mark.asyncio
    async def test_add_invalid_api_key_sends_error(self, mock_ctx):
        """Test add command with invalid API key sends error message."""
        api_key = "invalid-key"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                invalid_error = APIInvalidKey(mock_ctx.bot, f"(400) {gw2_messages.INVALID_APIKEY_MSG}")
                mock_client_instance.check_api_key = AsyncMock(return_value=invalid_error)
                with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                    mock_error.return_value = None
                    await add(mock_ctx, api_key)
                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert gw2_messages.INVALID_APIKEY_MSG in error_msg
                    assert api_key in error_msg

    @pytest.mark.asyncio
    async def test_add_account_info_api_fails(self, mock_ctx):
        """Test add command when account info API call fails."""
        api_key = "valid-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(
                    return_value={"name": "TestKey", "permissions": ["account", "characters"]}
                )
                mock_client_instance.call_api = AsyncMock(side_effect=Exception("Account API error"))
                with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                    await add(mock_ctx, api_key)
                    mock_error.assert_called_once()
                    mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_server_name_api_fails(self, mock_ctx):
        """Test add command when server name API call fails."""
        api_key = "valid-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(
                    return_value={"name": "TestKey", "permissions": ["account", "characters"]}
                )
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        {"name": "TestUser.1234", "world": 1001},  # account call
                        Exception("Server API error"),  # world call
                    ]
                )
                with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                    result = await add(mock_ctx, api_key)
                    mock_error.assert_called_once()
                    mock_ctx.bot.log.error.assert_called_once()
                    assert result is None

    @pytest.mark.asyncio
    async def test_add_user_already_has_key_shows_error_with_options(self, mock_ctx):
        """Test add command when user already has a key registered."""
        api_key = "valid-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(
                    return_value={"name": "TestKey", "permissions": ["account", "characters"]}
                )
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        {"name": "TestUser.1234", "world": 1001},
                        {"name": "Anvil Rock"},
                    ]
                )
                with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                    mock_instance = mock_dal.return_value
                    mock_instance.get_api_key_by_user = AsyncMock(
                        return_value=[{"name": "OldKey", "gw2_acc_name": "TestUser.1234"}]
                    )
                    with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                        result = await add(mock_ctx, api_key)
                        mock_error.assert_called_once()
                        error_msg = mock_error.call_args[0][1]
                        assert "You already have an API key registered" in error_msg
                        assert "update" in error_msg
                        assert "info" in error_msg
                        assert "remove" in error_msg
                        assert result is None

    @pytest.mark.asyncio
    async def test_add_key_already_in_use_by_someone_else(self, mock_ctx):
        """Test add command when the API key is already in use by another user."""
        api_key = "valid-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(
                    return_value={"name": "TestKey", "permissions": ["account", "characters"]}
                )
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        {"name": "TestUser.1234", "world": 1001},
                        {"name": "Anvil Rock"},
                    ]
                )
                with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                    mock_instance = mock_dal.return_value
                    mock_instance.get_api_key_by_user = AsyncMock(return_value=None)
                    mock_instance.get_api_key = AsyncMock(return_value=[{"user_id": 99999, "key": api_key}])
                    with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                        result = await add(mock_ctx, api_key)
                        mock_error.assert_called_once()
                        error_msg = mock_error.call_args[0][1]
                        assert "already in use" in error_msg
                        assert result is None

    @pytest.mark.asyncio
    async def test_add_successful_insert(self, mock_ctx):
        """Test add command with successful key insertion."""
        api_key = "valid-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(
                    return_value={"name": "TestKey", "permissions": ["account", "characters"]}
                )
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        {"name": "TestUser.1234", "world": 1001},
                        {"name": "Anvil Rock"},
                    ]
                )
                with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                    mock_instance = mock_dal.return_value
                    mock_instance.get_api_key_by_user = AsyncMock(return_value=None)
                    mock_instance.get_api_key = AsyncMock(return_value=None)
                    mock_instance.insert_api_key = AsyncMock()
                    with patch("src.gw2.cogs.key.bot_utils.send_msg") as mock_send:
                        result = await add(mock_ctx, api_key)
                        mock_instance.insert_api_key.assert_called_once()
                        insert_args = mock_instance.insert_api_key.call_args[0][0]
                        assert insert_args["user_id"] == 12345
                        assert insert_args["key_name"] == "TestKey"
                        assert insert_args["gw2_acc_name"] == "TestUser.1234"
                        assert insert_args["server_name"] == "Anvil Rock"
                        assert insert_args["permissions"] == "account,characters"
                        assert insert_args["api_key"] == api_key
                        mock_send.assert_called_once()
                        msg = mock_send.call_args[0][1]
                        assert "TestKey" in msg
                        assert "Anvil Rock" in msg
                        assert result is None

    @pytest.mark.asyncio
    async def test_add_insert_raises_exception(self, mock_ctx):
        """Test add command when database insert raises an exception."""
        api_key = "valid-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(
                    return_value={"name": "TestKey", "permissions": ["account", "characters"]}
                )
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        {"name": "TestUser.1234", "world": 1001},
                        {"name": "Anvil Rock"},
                    ]
                )
                with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                    mock_instance = mock_dal.return_value
                    mock_instance.get_api_key_by_user = AsyncMock(return_value=None)
                    mock_instance.get_api_key = AsyncMock(return_value=None)
                    mock_instance.insert_api_key = AsyncMock(side_effect=Exception("DB insert error"))
                    with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                        result = await add(mock_ctx, api_key)
                        mock_error.assert_called_once()
                        error_msg = mock_error.call_args[0][1]
                        assert "Failed to add API key" in error_msg
                        mock_ctx.bot.log.error.assert_called_once()
                        assert result is None


class TestUpdateCommand:
    """Test cases for the key update command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.avatar = MagicMock()
        ctx.bot.user.avatar.url = "https://example.com/bot_avatar.png"
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.message.channel.guild = MagicMock()
        ctx.message.channel.guild.id = 99999
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.prefix = "!"
        ctx.author = MagicMock()
        ctx.author.id = 12345
        ctx.author.name = "TestUser"
        ctx.send = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_update_deletes_message_for_privacy(self, mock_ctx):
        """Test that update command deletes the user's message for privacy."""
        api_key = "new-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message") as mock_delete:
            with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.get_api_key_by_user = AsyncMock(return_value=None)
                with patch("src.gw2.cogs.key.bot_utils.send_error_msg"):
                    await update(mock_ctx, api_key)
                    mock_delete.assert_called_once_with(mock_ctx, warning=True)

    @pytest.mark.asyncio
    async def test_update_no_existing_key_sends_error(self, mock_ctx):
        """Test update command when user has no existing key."""
        api_key = "new-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.get_api_key_by_user = AsyncMock(return_value=None)
                with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                    result = await update(mock_ctx, api_key)
                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "You don't have an API key registered yet" in error_msg
                    assert "add" in error_msg
                    assert result is None

    @pytest.mark.asyncio
    async def test_update_invalid_api_key_sends_error(self, mock_ctx):
        """Test update command with invalid new API key."""
        api_key = "invalid-new-key"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.get_api_key_by_user = AsyncMock(return_value=[{"name": "OldKey", "key": "old-key-12345"}])
                with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                    mock_client_instance = mock_client.return_value
                    invalid_error = APIInvalidKey(mock_ctx.bot, f"(400) {gw2_messages.INVALID_APIKEY_MSG}")
                    mock_client_instance.check_api_key = AsyncMock(return_value=invalid_error)
                    with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                        mock_error.return_value = None
                        await update(mock_ctx, api_key)
                        mock_error.assert_called_once()
                        error_msg = mock_error.call_args[0][1]
                        assert gw2_messages.INVALID_APIKEY_MSG in error_msg

    @pytest.mark.asyncio
    async def test_update_account_info_api_fails(self, mock_ctx):
        """Test update command when account info API call fails."""
        api_key = "new-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.get_api_key_by_user = AsyncMock(return_value=[{"name": "OldKey", "key": "old-key-12345"}])
                with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                    mock_client_instance = mock_client.return_value
                    mock_client_instance.check_api_key = AsyncMock(
                        return_value={"name": "NewKey", "permissions": ["account", "characters"]}
                    )
                    mock_client_instance.call_api = AsyncMock(side_effect=Exception("Account API error"))
                    with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                        await update(mock_ctx, api_key)
                        mock_error.assert_called_once()
                        mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_server_name_api_fails(self, mock_ctx):
        """Test update command when server name API call fails."""
        api_key = "new-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.get_api_key_by_user = AsyncMock(return_value=[{"name": "OldKey", "key": "old-key-12345"}])
                with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                    mock_client_instance = mock_client.return_value
                    mock_client_instance.check_api_key = AsyncMock(
                        return_value={"name": "NewKey", "permissions": ["account", "characters"]}
                    )
                    mock_client_instance.call_api = AsyncMock(
                        side_effect=[
                            {"name": "TestUser.1234", "world": 1001},
                            Exception("Server API error"),
                        ]
                    )
                    with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                        result = await update(mock_ctx, api_key)
                        mock_error.assert_called_once()
                        mock_ctx.bot.log.error.assert_called_once()
                        assert result is None

    @pytest.mark.asyncio
    async def test_update_key_in_use_by_different_user(self, mock_ctx):
        """Test update command when the new API key is in use by another user."""
        api_key = "new-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.get_api_key_by_user = AsyncMock(return_value=[{"name": "OldKey", "key": "old-key-12345"}])
                mock_instance.get_api_key = AsyncMock(
                    return_value=[{"user_id": 99999, "key": api_key}]  # different user
                )
                with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                    mock_client_instance = mock_client.return_value
                    mock_client_instance.check_api_key = AsyncMock(
                        return_value={"name": "NewKey", "permissions": ["account", "characters"]}
                    )
                    mock_client_instance.call_api = AsyncMock(
                        side_effect=[
                            {"name": "TestUser.1234", "world": 1001},
                            {"name": "Anvil Rock"},
                        ]
                    )
                    with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                        result = await update(mock_ctx, api_key)
                        mock_error.assert_called_once()
                        error_msg = mock_error.call_args[0][1]
                        assert "already in use" in error_msg
                        assert result is None

    @pytest.mark.asyncio
    async def test_update_successful(self, mock_ctx):
        """Test update command with successful key update."""
        api_key = "new-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.get_api_key_by_user = AsyncMock(return_value=[{"name": "OldKey", "key": "old-key-12345"}])
                mock_instance.get_api_key = AsyncMock(return_value=None)
                mock_instance.update_api_key = AsyncMock()
                with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                    mock_client_instance = mock_client.return_value
                    mock_client_instance.check_api_key = AsyncMock(
                        return_value={"name": "NewKey", "permissions": ["account", "characters"]}
                    )
                    mock_client_instance.call_api = AsyncMock(
                        side_effect=[
                            {"name": "TestUser.1234", "world": 1001},
                            {"name": "Anvil Rock"},
                        ]
                    )
                    with patch("src.gw2.cogs.key.bot_utils.send_msg") as mock_send:
                        result = await update(mock_ctx, api_key)
                        mock_instance.update_api_key.assert_called_once()
                        update_args = mock_instance.update_api_key.call_args[0][0]
                        assert update_args["user_id"] == 12345
                        assert update_args["key_name"] == "NewKey"
                        assert update_args["gw2_acc_name"] == "TestUser.1234"
                        assert update_args["server_name"] == "Anvil Rock"
                        assert update_args["permissions"] == "account,characters"
                        assert update_args["api_key"] == api_key
                        mock_send.assert_called_once()
                        msg = mock_send.call_args[0][1]
                        assert "OldKey" in msg
                        assert "NewKey" in msg
                        assert "Anvil Rock" in msg
                        assert result is None

    @pytest.mark.asyncio
    async def test_update_same_user_key_allowed(self, mock_ctx):
        """Test update command when API key is already owned by same user (re-using own key)."""
        api_key = "same-user-api-key"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.get_api_key_by_user = AsyncMock(return_value=[{"name": "OldKey", "key": "old-key-12345"}])
                # Key is found but belongs to same user
                mock_instance.get_api_key = AsyncMock(return_value=[{"user_id": 12345, "key": api_key}])  # same user
                mock_instance.update_api_key = AsyncMock()
                with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                    mock_client_instance = mock_client.return_value
                    mock_client_instance.check_api_key = AsyncMock(
                        return_value={"name": "NewKey", "permissions": ["account"]}
                    )
                    mock_client_instance.call_api = AsyncMock(
                        side_effect=[
                            {"name": "TestUser.1234", "world": 1001},
                            {"name": "Anvil Rock"},
                        ]
                    )
                    with patch("src.gw2.cogs.key.bot_utils.send_msg") as mock_send:
                        result = await update(mock_ctx, api_key)
                        mock_instance.update_api_key.assert_called_once()
                        mock_send.assert_called_once()
                        assert result is None

    @pytest.mark.asyncio
    async def test_update_raises_exception_on_db_update(self, mock_ctx):
        """Test update command when database update raises an exception."""
        api_key = "new-api-key-12345"
        with patch("src.gw2.cogs.key.bot_utils.delete_message"):
            with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.get_api_key_by_user = AsyncMock(return_value=[{"name": "OldKey", "key": "old-key-12345"}])
                mock_instance.get_api_key = AsyncMock(return_value=None)
                mock_instance.update_api_key = AsyncMock(side_effect=Exception("DB update error"))
                with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                    mock_client_instance = mock_client.return_value
                    mock_client_instance.check_api_key = AsyncMock(
                        return_value={"name": "NewKey", "permissions": ["account"]}
                    )
                    mock_client_instance.call_api = AsyncMock(
                        side_effect=[
                            {"name": "TestUser.1234", "world": 1001},
                            {"name": "Anvil Rock"},
                        ]
                    )
                    with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                        result = await update(mock_ctx, api_key)
                        mock_error.assert_called_once()
                        error_msg = mock_error.call_args[0][1]
                        assert "Failed to update API key" in error_msg
                        mock_ctx.bot.log.error.assert_called_once()
                        assert result is None


class TestRemoveCommand:
    """Test cases for the key remove command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.prefix = "!"
        ctx.send = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_remove_no_api_key_sends_error(self, mock_ctx):
        """Test remove command when user has no API key."""
        with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=None)
            with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                mock_error.return_value = None
                await remove(mock_ctx)
                mock_error.assert_called_once()
                error_msg = mock_error.call_args[0][1]
                assert gw2_messages.NO_API_KEY in error_msg

    @pytest.mark.asyncio
    async def test_remove_has_api_key_deletes_and_confirms(self, mock_ctx):
        """Test remove command when user has an API key."""
        with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=[{"key": "test-api-key", "name": "TestKey"}])
            mock_instance.delete_user_api_key = AsyncMock()
            with patch("src.gw2.cogs.key.bot_utils.send_msg") as mock_send:
                result = await remove(mock_ctx)
                mock_instance.delete_user_api_key.assert_called_once_with(12345)
                mock_send.assert_called_once()
                msg = mock_send.call_args[0][1]
                assert "deleted successfully" in msg
                assert result is None


class TestInfoCommand:
    """Test cases for the key info command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.avatar = MagicMock()
        ctx.bot.user.avatar.url = "https://example.com/bot_avatar.png"
        ctx.bot.user.display_avatar = MagicMock()
        ctx.bot.user.display_avatar.url = "https://example.com/bot_avatar.png"
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.author.display_avatar = MagicMock()
        ctx.message.author.display_avatar.url = "https://example.com/avatar.png"
        ctx.message.author.__str__ = MagicMock(return_value="TestUser#1234")
        ctx.prefix = "!"
        ctx.send = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_info_no_api_key_sends_error(self, mock_ctx):
        """Test info command when user has no API key."""
        with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=None)
            with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                await info(mock_ctx)
                mock_error.assert_called_once()
                error_msg = mock_error.call_args[0][1]
                assert "You don't have an API key registered" in error_msg
                assert "add" in error_msg

    @pytest.mark.asyncio
    async def test_info_valid_api_key_shows_embed(self, mock_ctx):
        """Test info command with a valid API key shows info embed."""
        with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(
                return_value=[
                    {
                        "key": "test-api-key-12345",
                        "name": "TestKey",
                        "gw2_acc_name": "TestUser.1234",
                        "server": "Anvil Rock",
                        "permissions": "account,characters,progression",
                    }
                ]
            )
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(
                    return_value={"name": "TestKey", "permissions": ["account", "characters", "progression"]}
                )
                with patch("src.gw2.cogs.key.bot_utils.send_embed") as mock_send:
                    with patch("src.gw2.cogs.key.bot_utils.get_current_date_time_str_long") as mock_time:
                        mock_time.return_value = "2025-01-01 12:00:00"
                        await info(mock_ctx)
                        mock_send.assert_called_once()
                        embed = mock_send.call_args[0][1]
                        assert embed.title == "Your GW2 Account"
                        assert "TestUser.1234" in embed.description
                        # Check dm=True
                        assert mock_send.call_args[1]["dm"] is True

    @pytest.mark.asyncio
    async def test_info_invalid_api_key_on_check_shows_no_valid(self, mock_ctx):
        """Test info command when API key is invalid on check shows NO valid with invalid name."""
        with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(
                return_value=[
                    {
                        "key": "expired-api-key",
                        "name": "OldKey",
                        "gw2_acc_name": "TestUser.1234",
                        "server": "Anvil Rock",
                        "permissions": "account",
                    }
                ]
            )
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                invalid_error = APIInvalidKey(mock_ctx.bot, f"(400) {gw2_messages.INVALID_APIKEY_MSG}")
                mock_client_instance.check_api_key = AsyncMock(return_value=invalid_error)
                with patch("src.gw2.cogs.key.bot_utils.send_embed") as mock_send:
                    with patch("src.gw2.cogs.key.bot_utils.get_current_date_time_str_long") as mock_time:
                        mock_time.return_value = "2025-01-01 12:00:00"
                        await info(mock_ctx)
                        mock_send.assert_called_once()
                        embed = mock_send.call_args[0][1]
                        # Check embed fields for "NO" valid
                        valid_field = None
                        for field in embed.fields:
                            if field.name == "Valid":
                                valid_field = field
                                break
                        assert valid_field is not None
                        assert "NO" in valid_field.value

    @pytest.mark.asyncio
    async def test_info_exception_during_check(self, mock_ctx):
        """Test info command when an exception occurs during API key check."""
        with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(
                return_value=[
                    {
                        "key": "test-api-key",
                        "name": "TestKey",
                        "gw2_acc_name": "TestUser.1234",
                        "server": "Anvil Rock",
                        "permissions": "account",
                    }
                ]
            )
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(side_effect=Exception("Connection error"))
                with patch("src.gw2.cogs.key.bot_utils.send_error_msg") as mock_error:
                    await info(mock_ctx)
                    mock_error.assert_called_once()
                    mock_ctx.bot.log.error.assert_called_once()


class TestKeyInfoNoAvatar:
    """Test that key info command works when user has no custom avatar."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context with avatar=None."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.avatar = None
        ctx.bot.user.display_avatar = MagicMock()
        ctx.bot.user.display_avatar.url = "https://example.com/default_bot.png"
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.avatar = None
        ctx.message.author.display_avatar = MagicMock()
        ctx.message.author.display_avatar.url = "https://example.com/default.png"
        ctx.message.author.__str__ = MagicMock(return_value="TestUser#1234")
        ctx.prefix = "!"
        ctx.send = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_key_info_author_no_avatar(self, mock_ctx):
        """Test info command does not crash when author has no custom avatar."""
        with patch("src.gw2.cogs.key.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(
                return_value=[
                    {
                        "key": "test-api-key-12345",
                        "name": "TestKey",
                        "gw2_acc_name": "TestUser.1234",
                        "server": "Anvil Rock",
                        "permissions": "account,characters,progression",
                    }
                ]
            )
            with patch("src.gw2.cogs.key.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(
                    return_value={"name": "TestKey", "permissions": ["account", "characters", "progression"]}
                )
                with patch("src.gw2.cogs.key.bot_utils.send_embed") as mock_send:
                    with patch("src.gw2.cogs.key.bot_utils.get_current_date_time_str_long") as mock_time:
                        mock_time.return_value = "2025-01-01 12:00:00"
                        await info(mock_ctx)
                        mock_send.assert_called_once()
                        embed = mock_send.call_args[0][1]
                        assert embed.author.icon_url == "https://example.com/default.png"


class TestKeySetup:
    """Test cases for key cog setup."""

    @pytest.mark.asyncio
    async def test_setup_function_exists(self):
        """Test that setup function exists and is callable."""
        from src.gw2.cogs.key import setup

        assert callable(setup)

    @pytest.mark.asyncio
    async def test_setup_removes_existing_gw2_command(self):
        """Test that setup removes existing gw2 command."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        from src.gw2.cogs.key import setup

        await setup(mock_bot)

        mock_bot.remove_command.assert_called_once_with("gw2")

    @pytest.mark.asyncio
    async def test_setup_adds_gw2_key_cog(self):
        """Test that setup adds the GW2Key cog."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        from src.gw2.cogs.key import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        cog_instance = mock_bot.add_cog.call_args[0][0]
        assert isinstance(cog_instance, GW2Key)


class TestInteractionHelpers:
    """Cover the Interaction branches of _get_user_id / _send_success / _send_error."""

    def test_get_user_id_from_interaction(self):
        import discord
        from src.gw2.cogs.key import _get_user_id

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user.id = 42
        assert _get_user_id(interaction) == 42

    @pytest.mark.asyncio
    async def test_send_success_via_interaction_followup(self):
        import discord
        from src.gw2.cogs.key import _send_success

        interaction = MagicMock(spec=discord.Interaction)
        interaction.followup.send = AsyncMock()

        await _send_success(interaction, "yay", 0x00FF00)

        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.call_args[1]
        assert isinstance(kwargs["embed"], discord.Embed)
        assert kwargs["embed"].description == "yay"
        assert kwargs["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_send_error_via_interaction_followup(self):
        import discord
        from src.gw2.cogs.key import _send_error

        interaction = MagicMock(spec=discord.Interaction)
        interaction.followup.send = AsyncMock()

        await _send_error(interaction, "boom")

        interaction.followup.send.assert_awaited_once()
        kwargs = interaction.followup.send.call_args[1]
        assert isinstance(kwargs["embed"], discord.Embed)
        assert kwargs["embed"].color == discord.Color.red()
        assert "boom" in kwargs["embed"].description
        assert kwargs["ephemeral"] is True


class TestApiKeyModal:
    """Cover ApiKeyModal init + on_submit dispatch (add vs update)."""

    @pytest.fixture
    def mock_bot(self):
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    def test_init_stores_attrs(self, mock_bot):
        from src.gw2.cogs.key import ApiKeyModal

        modal = ApiKeyModal(mock_bot, "add", "!")
        assert modal.bot is mock_bot
        assert modal.mode == "add"
        assert modal.prefix == "!"

    @pytest.mark.asyncio
    async def test_on_submit_add_mode_calls_process_add_key(self, mock_bot):
        import discord
        from src.gw2.cogs.key import ApiKeyModal

        modal = ApiKeyModal(mock_bot, "add", "!")
        modal.api_key_input = MagicMock()
        modal.api_key_input.value = "  test-key  "  # whitespace stripped by code

        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()

        with patch("src.gw2.cogs.key._process_add_key", new_callable=AsyncMock) as mock_add:
            await modal.on_submit(interaction)

            interaction.response.defer.assert_awaited_once_with(ephemeral=True)
            mock_add.assert_awaited_once_with(interaction, "test-key", mock_bot, "!")

    @pytest.mark.asyncio
    async def test_on_submit_update_mode_calls_process_update_key(self, mock_bot):
        import discord
        from src.gw2.cogs.key import ApiKeyModal

        modal = ApiKeyModal(mock_bot, "update", "!")
        modal.api_key_input = MagicMock()
        modal.api_key_input.value = "newkey"

        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()

        with patch("src.gw2.cogs.key._process_update_key", new_callable=AsyncMock) as mock_upd:
            await modal.on_submit(interaction)

            mock_upd.assert_awaited_once_with(interaction, "newkey", mock_bot, "!")


class TestApiKeyView:
    """Cover ApiKeyView init, button-callback, and on_timeout paths."""

    @pytest.fixture
    def mock_bot(self):
        bot = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    def test_init_stores_attrs(self, mock_bot):
        from src.gw2.cogs.key import ApiKeyView

        view = ApiKeyView(mock_bot, "add", "!")
        assert view.bot is mock_bot
        assert view.mode == "add"
        assert view.prefix == "!"
        assert view.message is None
        assert view.timeout == 300

    @pytest.mark.asyncio
    async def test_enter_key_button_sends_modal(self, mock_bot):
        import discord
        from src.gw2.cogs.key import ApiKeyView

        view = ApiKeyView(mock_bot, "update", "?")
        interaction = MagicMock(spec=discord.Interaction)
        interaction.response.send_modal = AsyncMock()

        await view.enter_key.callback(interaction)

        interaction.response.send_modal.assert_awaited_once()
        modal_arg = interaction.response.send_modal.call_args[0][0]
        assert modal_arg.mode == "update"
        assert modal_arg.prefix == "?"
        assert modal_arg.bot is mock_bot

    @pytest.mark.asyncio
    async def test_on_timeout_disables_children_and_edits(self, mock_bot):
        from src.gw2.cogs.key import ApiKeyView

        view = ApiKeyView(mock_bot, "add", "!")
        view.message = MagicMock()
        view.message.edit = AsyncMock()

        await view.on_timeout()

        # All button children disabled.
        assert all(item.disabled for item in view.children)
        view.message.edit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_on_timeout_no_message_skips_edit(self, mock_bot):
        from src.gw2.cogs.key import ApiKeyView

        view = ApiKeyView(mock_bot, "add", "!")
        view.message = None  # Never sent
        # Should not raise.
        await view.on_timeout()
        assert all(item.disabled for item in view.children)

    @pytest.mark.asyncio
    async def test_on_timeout_edit_failure_is_swallowed(self, mock_bot):
        import discord
        from src.gw2.cogs.key import ApiKeyView

        view = ApiKeyView(mock_bot, "add", "!")
        view.message = MagicMock()
        view.message.edit = AsyncMock(side_effect=discord.NotFound(MagicMock(), "gone"))
        # Should not raise — caught by except.
        await view.on_timeout()
        view.message.edit.assert_awaited_once()


class TestAddCommandInteractivePath:
    """Cover the `add` command's no-api-key branch (modal/view + DM notification)."""

    @pytest.fixture
    def mock_ctx(self):
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.prefix = "!"
        ctx.author = MagicMock()
        ctx.author.send = AsyncMock()
        ctx.send = AsyncMock()
        ctx.message = MagicMock()
        ctx.message.author = ctx.author
        return ctx

    @pytest.mark.asyncio
    async def test_add_without_key_in_channel_sends_dm_and_channel_notification(self, mock_ctx):
        sent_message = MagicMock()
        mock_ctx.author.send.return_value = sent_message

        with patch("src.gw2.cogs.key.bot_utils.is_private_message", return_value=False):
            await add.callback(mock_ctx, api_key=None)

        # DM was sent with the view.
        mock_ctx.author.send.assert_awaited_once()
        dm_kwargs = mock_ctx.author.send.call_args[1]
        assert "view" in dm_kwargs
        from src.gw2.cogs.key import ApiKeyView

        assert isinstance(dm_kwargs["view"], ApiKeyView)
        assert dm_kwargs["view"].mode == "add"
        assert dm_kwargs["view"].message is sent_message

        # Channel-side notification was posted.
        mock_ctx.send.assert_awaited_once()
        notif_embed = mock_ctx.send.call_args[1]["embed"]
        assert "DM" in notif_embed.description

    @pytest.mark.asyncio
    async def test_add_without_key_in_dm_skips_channel_notification(self, mock_ctx):
        sent_message = MagicMock()
        mock_ctx.author.send.return_value = sent_message

        with patch("src.gw2.cogs.key.bot_utils.is_private_message", return_value=True):
            await add.callback(mock_ctx, api_key=None)

        # DM message sent.
        mock_ctx.author.send.assert_awaited_once()
        # NO channel notification (we're already in DM).
        mock_ctx.send.assert_not_called()


class TestUpdateCommandInteractivePath:
    """Cover the `update` command's no-api-key branch (modal/view + DM notification)."""

    @pytest.fixture
    def mock_ctx(self):
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.prefix = "!"
        ctx.author = MagicMock()
        ctx.author.send = AsyncMock()
        ctx.send = AsyncMock()
        ctx.message = MagicMock()
        ctx.message.author = ctx.author
        return ctx

    @pytest.mark.asyncio
    async def test_update_without_key_in_channel_sends_dm_and_channel_notification(self, mock_ctx):
        sent_message = MagicMock()
        mock_ctx.author.send.return_value = sent_message

        with patch("src.gw2.cogs.key.bot_utils.is_private_message", return_value=False):
            await update.callback(mock_ctx, api_key=None)

        mock_ctx.author.send.assert_awaited_once()
        dm_kwargs = mock_ctx.author.send.call_args[1]
        from src.gw2.cogs.key import ApiKeyView

        assert isinstance(dm_kwargs["view"], ApiKeyView)
        assert dm_kwargs["view"].mode == "update"
        assert dm_kwargs["view"].message is sent_message

        mock_ctx.send.assert_awaited_once()
        notif_embed = mock_ctx.send.call_args[1]["embed"]
        assert "DM" in notif_embed.description

    @pytest.mark.asyncio
    async def test_update_without_key_in_dm_skips_channel_notification(self, mock_ctx):
        sent_message = MagicMock()
        mock_ctx.author.send.return_value = sent_message

        with patch("src.gw2.cogs.key.bot_utils.is_private_message", return_value=True):
            await update.callback(mock_ctx, api_key=None)

        mock_ctx.author.send.assert_awaited_once()
        mock_ctx.send.assert_not_called()
