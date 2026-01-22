"""Comprehensive tests for GW2 characters cog."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.gw2.cogs.characters import GW2Characters, characters
from src.gw2.tools.gw2_exceptions import APIInvalidKey


class TestGW2Characters:
    """Test cases for the GW2Characters cog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def gw2_characters_cog(self, mock_bot):
        """Create a GW2Characters cog instance."""
        return GW2Characters(mock_bot)

    def test_gw2_characters_initialization(self, mock_bot):
        """Test GW2Characters cog initialization."""
        cog = GW2Characters(mock_bot)
        assert cog.bot == mock_bot

    def test_gw2_characters_inheritance(self, gw2_characters_cog):
        """Test that GW2Characters inherits from GuildWars2 properly."""
        from src.gw2.cogs.gw2 import GuildWars2
        assert isinstance(gw2_characters_cog, GuildWars2)


class TestCharactersCommand:
    """Test cases for the characters command."""

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
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def sample_api_key_data(self):
        """Create sample API key data."""
        return [{
            "key": "test-api-key-12345",
            "permissions": "account,characters,progression"
        }]

    @pytest.fixture
    def sample_account_data(self):
        """Create sample account data."""
        return {
            "name": "TestUser.1234",
            "world": 1001
        }

    @pytest.fixture
    def sample_character_data(self):
        """Create sample character core data."""
        return {
            "name": "TestCharacter",
            "race": "Human",
            "gender": "Male",
            "profession": "Warrior",
            "level": 80,
            "deaths": 42,
            "age": 432000,  # seconds
            "created": "2020-01-15T10:30:00Z"
        }

    @pytest.mark.asyncio
    async def test_characters_no_api_key_sends_error(self, mock_ctx):
        """Test characters command when user has no API key."""
        with patch('src.gw2.cogs.characters.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=None)
            with patch('src.gw2.cogs.characters.bot_utils.send_error_msg') as mock_error:
                mock_error.return_value = None
                await characters(mock_ctx)
                mock_error.assert_called_once()
                error_msg = mock_error.call_args[0][1]
                assert "You dont have an API key registered" in error_msg

    @pytest.mark.asyncio
    async def test_characters_invalid_api_key_sends_error_with_help(self, mock_ctx, sample_api_key_data):
        """Test characters command with invalid API key sends error with help info."""
        with patch('src.gw2.cogs.characters.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch('src.gw2.cogs.characters.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                invalid_error = APIInvalidKey(mock_ctx.bot, "Invalid key")
                invalid_error.args = ("error", "This API Key is INVALID")
                mock_client_instance.check_api_key = AsyncMock(return_value=invalid_error)
                with patch('src.gw2.cogs.characters.bot_utils.send_error_msg') as mock_error:
                    mock_error.return_value = None
                    await characters(mock_ctx)
                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "This API Key is INVALID" in error_msg
                    assert "gw2 key add" in error_msg or "key add" in error_msg

    @pytest.mark.asyncio
    async def test_characters_missing_characters_permission_sends_error(self, mock_ctx):
        """Test characters command with missing characters permission."""
        no_chars_permission_data = [{
            "key": "test-api-key-12345",
            "permissions": "account,progression"  # Missing 'characters'
        }]
        with patch('src.gw2.cogs.characters.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=no_chars_permission_data)
            with patch('src.gw2.cogs.characters.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value={
                    "name": "TestKey",
                    "permissions": ["account", "progression"]
                })
                with patch('src.gw2.cogs.characters.bot_utils.send_error_msg') as mock_error:
                    mock_error.return_value = None
                    await characters(mock_ctx)
                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "permission" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_characters_missing_account_permission_sends_error(self, mock_ctx):
        """Test characters command with missing account permission."""
        no_account_permission_data = [{
            "key": "test-api-key-12345",
            "permissions": "characters,progression"  # Missing 'account'
        }]
        with patch('src.gw2.cogs.characters.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=no_account_permission_data)
            with patch('src.gw2.cogs.characters.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value={
                    "name": "TestKey",
                    "permissions": ["characters", "progression"]
                })
                with patch('src.gw2.cogs.characters.bot_utils.send_error_msg') as mock_error:
                    mock_error.return_value = None
                    await characters(mock_ctx)
                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "permission" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_characters_successful_with_character_data(
        self, mock_ctx, sample_api_key_data, sample_account_data, sample_character_data
    ):
        """Test successful characters command with character data creates embed with fields."""
        with patch('src.gw2.cogs.characters.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch('src.gw2.cogs.characters.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value={
                    "name": "TestKey",
                    "permissions": ["account", "characters", "progression"]
                })
                mock_client_instance.call_api = AsyncMock(side_effect=[
                    sample_account_data,          # account call
                    ["CharOne", "CharTwo"],        # characters list call
                    {                             # CharOne core data
                        "race": "Human",
                        "gender": "Male",
                        "profession": "Warrior",
                        "level": 80,
                        "deaths": 42,
                        "age": 432000,
                        "created": "2020-01-15T10:30:00Z"
                    },
                    {                             # CharTwo core data
                        "race": "Asura",
                        "gender": "Female",
                        "profession": "Elementalist",
                        "level": 80,
                        "deaths": 15,
                        "age": 216000,
                        "created": "2021-06-20T08:00:00Z"
                    },
                ])
                with patch('src.gw2.cogs.characters.bot_utils.send_embed') as mock_send:
                    with patch('src.gw2.cogs.characters.bot_utils.get_current_date_time_str_long') as mock_time:
                        mock_time.return_value = "2025-01-01 12:00:00"
                        await characters(mock_ctx)
                        mock_send.assert_called_once()
                        embed = mock_send.call_args[0][1]
                        assert embed.title == "Account Name"
                        assert "TestUser.1234" in embed.description
                        # Verify embed has fields for characters
                        assert len(embed.fields) == 2
                        # Verify character fields contain expected data
                        char_one_field = embed.fields[0]
                        assert char_one_field.name == "CharOne"
                        assert "Human" in char_one_field.value
                        assert "Warrior" in char_one_field.value
                        assert "80" in char_one_field.value
                        char_two_field = embed.fields[1]
                        assert char_two_field.name == "CharTwo"
                        assert "Asura" in char_two_field.value
                        assert "Elementalist" in char_two_field.value

    @pytest.mark.asyncio
    async def test_characters_successful_character_age_calculation(
        self, mock_ctx, sample_api_key_data, sample_account_data
    ):
        """Test that character age is correctly calculated in days."""
        with patch('src.gw2.cogs.characters.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch('src.gw2.cogs.characters.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value={
                    "name": "TestKey",
                    "permissions": ["account", "characters"]
                })
                # age = 144000 seconds => (144000/60)/24 = 100 days
                mock_client_instance.call_api = AsyncMock(side_effect=[
                    sample_account_data,
                    ["TestChar"],
                    {
                        "race": "Norn",
                        "gender": "Male",
                        "profession": "Guardian",
                        "level": 80,
                        "deaths": 10,
                        "age": 144000,  # 100 days in seconds/minutes -> (144000/60)/24 = 100
                        "created": "2022-03-01T00:00:00Z"
                    },
                ])
                with patch('src.gw2.cogs.characters.bot_utils.send_embed') as mock_send:
                    with patch('src.gw2.cogs.characters.bot_utils.get_current_date_time_str_long') as mock_time:
                        mock_time.return_value = "2025-01-01 12:00:00"
                        await characters(mock_ctx)
                        mock_send.assert_called_once()
                        embed = mock_send.call_args[0][1]
                        char_field = embed.fields[0]
                        assert "100" in char_field.value

    @pytest.mark.asyncio
    async def test_characters_successful_created_date_parsed(
        self, mock_ctx, sample_api_key_data, sample_account_data
    ):
        """Test that character created date is parsed correctly (only date portion before T)."""
        with patch('src.gw2.cogs.characters.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch('src.gw2.cogs.characters.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value={
                    "name": "TestKey",
                    "permissions": ["account", "characters"]
                })
                mock_client_instance.call_api = AsyncMock(side_effect=[
                    sample_account_data,
                    ["DateChar"],
                    {
                        "race": "Sylvari",
                        "gender": "Female",
                        "profession": "Ranger",
                        "level": 50,
                        "deaths": 5,
                        "age": 7200,
                        "created": "2023-07-15T14:30:00Z"
                    },
                ])
                with patch('src.gw2.cogs.characters.bot_utils.send_embed') as mock_send:
                    with patch('src.gw2.cogs.characters.bot_utils.get_current_date_time_str_long') as mock_time:
                        mock_time.return_value = "2025-01-01 12:00:00"
                        await characters(mock_ctx)
                        mock_send.assert_called_once()
                        embed = mock_send.call_args[0][1]
                        char_field = embed.fields[0]
                        assert "2023-07-15" in char_field.value

    @pytest.mark.asyncio
    async def test_characters_api_exception_during_execution(self, mock_ctx, sample_api_key_data):
        """Test characters command when API exception occurs during execution."""
        with patch('src.gw2.cogs.characters.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch('src.gw2.cogs.characters.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value={
                    "name": "TestKey",
                    "permissions": ["account", "characters"]
                })
                mock_client_instance.call_api = AsyncMock(
                    side_effect=Exception("API connection error")
                )
                with patch('src.gw2.cogs.characters.bot_utils.send_error_msg') as mock_error:
                    await characters(mock_ctx)
                    mock_error.assert_called_once()
                    mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_characters_triggers_typing_indicator(self, mock_ctx, sample_api_key_data):
        """Test that characters command triggers typing indicator."""
        with patch('src.gw2.cogs.characters.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=None)
            with patch('src.gw2.cogs.characters.bot_utils.send_error_msg'):
                await characters(mock_ctx)
                mock_ctx.message.channel.typing.assert_called()

    @pytest.mark.asyncio
    async def test_characters_embed_has_thumbnail_and_author(
        self, mock_ctx, sample_api_key_data, sample_account_data
    ):
        """Test that the characters embed has proper thumbnail and author set."""
        with patch('src.gw2.cogs.characters.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)
            with patch('src.gw2.cogs.characters.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value={
                    "name": "TestKey",
                    "permissions": ["account", "characters"]
                })
                mock_client_instance.call_api = AsyncMock(side_effect=[
                    sample_account_data,
                    ["SingleChar"],
                    {
                        "race": "Charr",
                        "gender": "Male",
                        "profession": "Engineer",
                        "level": 80,
                        "deaths": 0,
                        "age": 1440,
                        "created": "2024-01-01T00:00:00Z"
                    },
                ])
                with patch('src.gw2.cogs.characters.bot_utils.send_embed') as mock_send:
                    with patch('src.gw2.cogs.characters.bot_utils.get_current_date_time_str_long') as mock_time:
                        mock_time.return_value = "2025-01-01 12:00:00"
                        await characters(mock_ctx)
                        mock_send.assert_called_once()
                        embed = mock_send.call_args[0][1]
                        assert embed.thumbnail.url == "https://example.com/avatar.png"
                        assert embed.author.name == "TestUser"
                        assert embed.author.icon_url == "https://example.com/avatar.png"


class TestCharactersSetup:
    """Test cases for characters cog setup."""

    @pytest.mark.asyncio
    async def test_setup_function_exists(self):
        """Test that setup function exists and is callable."""
        from src.gw2.cogs.characters import setup
        assert callable(setup)

    @pytest.mark.asyncio
    async def test_setup_removes_existing_gw2_command(self):
        """Test that setup removes existing gw2 command."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        from src.gw2.cogs.characters import setup
        await setup(mock_bot)

        mock_bot.remove_command.assert_called_once_with("gw2")

    @pytest.mark.asyncio
    async def test_setup_adds_gw2_characters_cog(self):
        """Test that setup adds the GW2Characters cog."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        from src.gw2.cogs.characters import setup
        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        cog_instance = mock_bot.add_cog.call_args[0][0]
        assert isinstance(cog_instance, GW2Characters)
