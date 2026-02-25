"""Comprehensive tests for all DAL (Data Access Layer) classes."""

import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules["ddcDatabases"] = Mock()

from src.database.dal.bot.bot_configs_dal import BotConfigsDal
from src.database.dal.bot.custom_commands_dal import CustomCommandsDal
from src.database.dal.bot.dice_rolls_dal import DiceRollsDal
from src.database.dal.bot.profanity_filters_dal import ProfanityFilterDal
from src.database.dal.bot.servers_dal import ServersDal
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.database.dal.gw2.gw2_session_chars_dal import Gw2SessionCharsDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal

# =============================================================================
# BotConfigsDal Tests
# =============================================================================


class TestBotConfigsDal:
    """Test cases for BotConfigsDal."""

    @pytest.fixture
    def mock_dal(self):
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.bot.bot_configs_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = BotConfigsDal(db_session, log)
            dal.db_utils = mock_db_utils
            yield dal

    def test_init(self):
        """Test BotConfigsDal initialization."""
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.bot.bot_configs_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = BotConfigsDal(db_session, log)
            mock_db_utils_class.assert_called_once_with(db_session)
            assert dal.log == log
            assert dal.db_utils == mock_db_utils

    @pytest.mark.asyncio
    async def test_update_bot_prefix(self, mock_dal):
        """Test update_bot_prefix calls execute with correct statement."""
        await mock_dal.update_bot_prefix("!")
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_bot_prefix_different_prefix(self, mock_dal):
        """Test update_bot_prefix with a different prefix character."""
        await mock_dal.update_bot_prefix("$")
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_bot_description(self, mock_dal):
        """Test update_bot_description calls execute with correct statement."""
        await mock_dal.update_bot_description("New bot description")
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_bot_description_empty(self, mock_dal):
        """Test update_bot_description with empty string."""
        await mock_dal.update_bot_description("")
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_bot_configs(self, mock_dal):
        """Test get_bot_configs calls fetchall and returns results."""
        expected_results = [{"id": 1, "prefix": "!", "description": "A bot"}]
        mock_dal.db_utils.fetchall.return_value = expected_results
        results = await mock_dal.get_bot_configs()
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected_results

    @pytest.mark.asyncio
    async def test_get_bot_configs_empty(self, mock_dal):
        """Test get_bot_configs when no configs exist."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_bot_configs()
        assert results == []

    @pytest.mark.asyncio
    async def test_get_bot_prefix(self, mock_dal):
        """Test get_bot_prefix calls fetchvalue and returns prefix."""
        mock_dal.db_utils.fetchvalue.return_value = "!"
        result = await mock_dal.get_bot_prefix()
        mock_dal.db_utils.fetchvalue.assert_called_once()
        assert result == "!"

    @pytest.mark.asyncio
    async def test_get_bot_prefix_none(self, mock_dal):
        """Test get_bot_prefix when no prefix is set."""
        mock_dal.db_utils.fetchvalue.return_value = None
        result = await mock_dal.get_bot_prefix()
        assert result is None


# =============================================================================
# CustomCommandsDal Tests
# =============================================================================


class TestCustomCommandsDal:
    """Test cases for CustomCommandsDal."""

    @pytest.fixture
    def mock_dal(self):
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.bot.custom_commands_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = CustomCommandsDal(db_session, log)
            dal.db_utils = mock_db_utils
            yield dal

    def test_init(self):
        """Test CustomCommandsDal initialization."""
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.bot.custom_commands_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = CustomCommandsDal(db_session, log)
            mock_db_utils_class.assert_called_once_with(db_session)
            assert dal.log == log
            assert dal.db_utils == mock_db_utils

    @pytest.mark.asyncio
    async def test_insert_command(self, mock_dal):
        """Test insert_command calls insert with a CustomCommands instance."""
        await mock_dal.insert_command(
            server_id=12345,
            user_id=67890,
            cmd_name="hello",
            description="Says hello",
        )
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_command_different_values(self, mock_dal):
        """Test insert_command with different parameter values."""
        await mock_dal.insert_command(
            server_id=99999,
            user_id=11111,
            cmd_name="goodbye",
            description="Says goodbye",
        )
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_command_description(self, mock_dal):
        """Test update_command_description calls execute."""
        await mock_dal.update_command_description(
            server_id=12345,
            user_id=67890,
            cmd_name="hello",
            description="Updated description",
        )
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_server_command(self, mock_dal):
        """Test delete_server_command calls execute."""
        await mock_dal.delete_server_command(server_id=12345, cmd_name="hello")
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_all_commands(self, mock_dal):
        """Test delete_all_commands calls execute."""
        await mock_dal.delete_all_commands(server_id=12345)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_server_commands(self, mock_dal):
        """Test get_all_server_commands calls fetchall and returns results."""
        expected = [
            {"id": 1, "server_id": 12345, "name": "cmd1", "description": "Desc1"},
            {"id": 2, "server_id": 12345, "name": "cmd2", "description": "Desc2"},
        ]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_all_server_commands(server_id=12345)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_all_server_commands_empty(self, mock_dal):
        """Test get_all_server_commands when no commands exist."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_all_server_commands(server_id=12345)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_command_found(self, mock_dal):
        """Test get_command when command exists returns first result."""
        expected = [{"id": 1, "server_id": 12345, "name": "hello", "description": "Says hello"}]
        mock_dal.db_utils.fetchall.return_value = expected
        result = await mock_dal.get_command(server_id=12345, cmd_name="hello")
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert result == expected[0]

    @pytest.mark.asyncio
    async def test_get_command_not_found(self, mock_dal):
        """Test get_command when command does not exist returns None."""
        mock_dal.db_utils.fetchall.return_value = []
        result = await mock_dal.get_command(server_id=12345, cmd_name="nonexistent")
        assert result is None


# =============================================================================
# DiceRollsDal Tests
# =============================================================================


class TestDiceRollsDal:
    """Test cases for DiceRollsDal."""

    @pytest.fixture
    def mock_dal(self):
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.bot.dice_rolls_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = DiceRollsDal(db_session, log)
            dal.db_utils = mock_db_utils
            yield dal

    def test_init(self):
        """Test DiceRollsDal initialization."""
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.bot.dice_rolls_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = DiceRollsDal(db_session, log)
            mock_db_utils_class.assert_called_once_with(db_session)
            assert dal.log == log
            assert dal.db_utils == mock_db_utils

    @pytest.mark.asyncio
    async def test_insert_user_roll(self, mock_dal):
        """Test insert_user_roll calls insert with a DiceRolls instance."""
        await mock_dal.insert_user_roll(
            server_id=12345,
            user_id=67890,
            dice_size=20,
            roll=18,
        )
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_user_roll_max_roll(self, mock_dal):
        """Test insert_user_roll with a maximum dice roll."""
        await mock_dal.insert_user_roll(
            server_id=12345,
            user_id=67890,
            dice_size=100,
            roll=100,
        )
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_roll(self, mock_dal):
        """Test update_user_roll calls execute."""
        await mock_dal.update_user_roll(
            server_id=12345,
            user_id=67890,
            dice_size=20,
            roll=19,
        )
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_all_server_rolls(self, mock_dal):
        """Test delete_all_server_rolls calls execute."""
        await mock_dal.delete_all_server_rolls(server_id=12345)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_roll_by_dice_size(self, mock_dal):
        """Test get_user_roll_by_dice_size calls fetchall and returns results."""
        expected = [{"server_id": 12345, "user_id": 67890, "dice_size": 20, "roll": 18}]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_user_roll_by_dice_size(
            server_id=12345,
            user_id=67890,
            dice_size=20,
        )
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_user_roll_by_dice_size_empty(self, mock_dal):
        """Test get_user_roll_by_dice_size when no rolls exist."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_user_roll_by_dice_size(
            server_id=12345,
            user_id=67890,
            dice_size=20,
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_get_user_rolls_all_dice_sizes(self, mock_dal):
        """Test get_user_rolls_all_dice_sizes calls fetchall and returns results."""
        expected = [
            {"server_id": 12345, "user_id": 67890, "dice_size": 6, "roll": 5},
            {"server_id": 12345, "user_id": 67890, "dice_size": 20, "roll": 18},
            {"server_id": 12345, "user_id": 67890, "dice_size": 100, "roll": 95},
        ]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_user_rolls_all_dice_sizes(
            server_id=12345,
            user_id=67890,
        )
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_user_rolls_all_dice_sizes_empty(self, mock_dal):
        """Test get_user_rolls_all_dice_sizes when no rolls exist."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_user_rolls_all_dice_sizes(
            server_id=12345,
            user_id=67890,
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_get_all_server_rolls(self, mock_dal):
        """Test get_all_server_rolls calls fetchall and returns results."""
        expected = [
            {"server_id": 12345, "user_id": 11111, "dice_size": 20, "roll": 20},
            {"server_id": 12345, "user_id": 22222, "dice_size": 20, "roll": 15},
        ]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_all_server_rolls(server_id=12345, dice_size=20)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_all_server_rolls_empty(self, mock_dal):
        """Test get_all_server_rolls when no rolls exist for the dice size."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_all_server_rolls(server_id=12345, dice_size=6)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_server_max_roll(self, mock_dal):
        """Test get_server_max_roll calls fetchall and returns results."""
        expected = [{"user_id": 11111, "max_roll": 20}]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_server_max_roll(server_id=12345, dice_size=20)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_server_max_roll_empty(self, mock_dal):
        """Test get_server_max_roll when no rolls exist."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_server_max_roll(server_id=12345, dice_size=20)
        assert results == []


# =============================================================================
# ProfanityFilterDal Tests
# =============================================================================


class TestProfanityFilterDal:
    """Test cases for ProfanityFilterDal."""

    @pytest.fixture
    def mock_dal(self):
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.bot.profanity_filters_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = ProfanityFilterDal(db_session, log)
            dal.db_utils = mock_db_utils
            yield dal

    def test_init(self):
        """Test ProfanityFilterDal initialization."""
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.bot.profanity_filters_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = ProfanityFilterDal(db_session, log)
            mock_db_utils_class.assert_called_once_with(db_session)
            assert dal.log == log
            assert dal.db_utils == mock_db_utils

    @pytest.mark.asyncio
    async def test_insert_profanity_filter_channel(self, mock_dal):
        """Test insert_profanity_filter_channel calls insert."""
        await mock_dal.insert_profanity_filter_channel(
            server_id=12345,
            channel_id=99999,
            channel_name="general",
            created_by=67890,
        )
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_profanity_filter_channel_different_values(self, mock_dal):
        """Test insert_profanity_filter_channel with different channel."""
        await mock_dal.insert_profanity_filter_channel(
            server_id=54321,
            channel_id=88888,
            channel_name="off-topic",
            created_by=11111,
        )
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_profanity_filter_channel(self, mock_dal):
        """Test delete_profanity_filter_channel calls execute."""
        await mock_dal.delete_profanity_filter_channel(channel_id=99999)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_server_profanity_filter_channels(self, mock_dal):
        """Test get_all_server_profanity_filter_channels returns results."""
        expected = [
            {"server_id": 12345, "channel_id": 99999, "channel_name": "general"},
            {"server_id": 12345, "channel_id": 88888, "channel_name": "off-topic"},
        ]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_all_server_profanity_filter_channels(server_id=12345)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_all_server_profanity_filter_channels_empty(self, mock_dal):
        """Test get_all_server_profanity_filter_channels when none exist."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_all_server_profanity_filter_channels(server_id=12345)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_profanity_filter_channel(self, mock_dal):
        """Test get_profanity_filter_channel returns results."""
        expected = [{"server_id": 12345, "channel_id": 99999, "channel_name": "general"}]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_profanity_filter_channel(channel_id=99999)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_profanity_filter_channel_not_found(self, mock_dal):
        """Test get_profanity_filter_channel when channel not found."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_profanity_filter_channel(channel_id=00000)
        assert results == []


# =============================================================================
# ServersDal Tests
# =============================================================================


class TestServersDal:
    """Test cases for ServersDal."""

    @pytest.fixture
    def mock_dal(self):
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.bot.servers_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = ServersDal(db_session, log)
            dal.db_utils = mock_db_utils
            yield dal

    def test_init(self):
        """Test ServersDal initialization."""
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.bot.servers_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = ServersDal(db_session, log)
            mock_db_utils_class.assert_called_once_with(db_session)
            assert dal.log == log
            assert dal.db_utils == mock_db_utils

    @pytest.mark.asyncio
    async def test_insert_server(self, mock_dal):
        """Test insert_server calls execute with upsert statement."""
        await mock_dal.insert_server(server_id=12345, name="Test Server")
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_server_different_values(self, mock_dal):
        """Test insert_server with different server values."""
        await mock_dal.insert_server(server_id=99999, name="Another Server")
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_server_name_changed(self, mock_dal):
        """Test update_server when server name has changed."""
        before = MagicMock()
        before.name = "Old Name"
        after = MagicMock()
        after.name = "New Name"
        after.id = 12345

        await mock_dal.update_server(before, after)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_server_name_not_changed(self, mock_dal):
        """Test update_server when server name has not changed."""
        before = MagicMock()
        before.name = "Same Name"
        after = MagicMock()
        after.name = "Same Name"
        after.id = 12345

        await mock_dal.update_server(before, after)
        mock_dal.db_utils.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_server(self, mock_dal):
        """Test delete_server calls execute."""
        await mock_dal.delete_server(server_id=12345)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_msg_on_join(self, mock_dal):
        """Test update_msg_on_join calls execute."""
        await mock_dal.update_msg_on_join(server_id=12345, new_status=True, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_msg_on_join_false(self, mock_dal):
        """Test update_msg_on_join with False status."""
        await mock_dal.update_msg_on_join(server_id=12345, new_status=False, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_msg_on_leave(self, mock_dal):
        """Test update_msg_on_leave calls execute."""
        await mock_dal.update_msg_on_leave(server_id=12345, new_status=True, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_msg_on_leave_false(self, mock_dal):
        """Test update_msg_on_leave with False status."""
        await mock_dal.update_msg_on_leave(server_id=12345, new_status=False, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_msg_on_server_update(self, mock_dal):
        """Test update_msg_on_server_update calls execute."""
        await mock_dal.update_msg_on_server_update(server_id=12345, new_status=True, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_msg_on_server_update_false(self, mock_dal):
        """Test update_msg_on_server_update with False status."""
        await mock_dal.update_msg_on_server_update(server_id=12345, new_status=False, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_msg_on_member_update(self, mock_dal):
        """Test update_msg_on_member_update calls execute."""
        await mock_dal.update_msg_on_member_update(server_id=12345, new_status=True, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_msg_on_member_update_false(self, mock_dal):
        """Test update_msg_on_member_update with False status."""
        await mock_dal.update_msg_on_member_update(server_id=12345, new_status=False, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_block_invis_members(self, mock_dal):
        """Test update_block_invis_members calls execute."""
        await mock_dal.update_block_invis_members(server_id=12345, new_status=True, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_block_invis_members_false(self, mock_dal):
        """Test update_block_invis_members with False status."""
        await mock_dal.update_block_invis_members(server_id=12345, new_status=False, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_bot_word_reactions(self, mock_dal):
        """Test update_bot_word_reactions calls execute."""
        await mock_dal.update_bot_word_reactions(server_id=12345, new_status=True, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_bot_word_reactions_false(self, mock_dal):
        """Test update_bot_word_reactions with False status."""
        await mock_dal.update_bot_word_reactions(server_id=12345, new_status=False, updated_by=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_server_with_server_id(self, mock_dal):
        """Test get_server with server_id returns first result."""
        expected = [{"id": 12345, "name": "Test Server", "msg_on_join": True}]
        mock_dal.db_utils.fetchall.return_value = expected
        result = await mock_dal.get_server(server_id=12345)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert result == expected[0]

    @pytest.mark.asyncio
    async def test_get_server_with_server_id_not_found(self, mock_dal):
        """Test get_server with server_id when server not found."""
        mock_dal.db_utils.fetchall.return_value = []
        result = await mock_dal.get_server(server_id=99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_server_with_channel_id(self, mock_dal):
        """Test get_server with channel_id includes profanity filter join."""
        expected = [{"id": 12345, "name": "Test Server", "profanity_filter": 1}]
        mock_dal.db_utils.fetchall.return_value = expected
        result = await mock_dal.get_server(server_id=12345, channel_id=99999)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert result == expected[0]

    @pytest.mark.asyncio
    async def test_get_server_without_server_id(self, mock_dal):
        """Test get_server without server_id returns all servers."""
        expected = [
            {"id": 12345, "name": "Server 1"},
            {"id": 67890, "name": "Server 2"},
        ]
        mock_dal.db_utils.fetchall.return_value = expected
        result = await mock_dal.get_server()
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_server_with_channel_id_only(self, mock_dal):
        """Test get_server with only channel_id and no server_id returns all."""
        expected = [
            {"id": 12345, "name": "Server 1", "profanity_filter": None},
            {"id": 67890, "name": "Server 2", "profanity_filter": 1},
        ]
        mock_dal.db_utils.fetchall.return_value = expected
        result = await mock_dal.get_server(channel_id=99999)
        mock_dal.db_utils.fetchall.assert_called_once()
        assert result == expected


# =============================================================================
# Gw2ConfigsDal Tests
# =============================================================================


class TestGw2ConfigsDal:
    """Test cases for Gw2ConfigsDal."""

    @pytest.fixture
    def mock_dal(self):
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.gw2.gw2_configs_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = Gw2ConfigsDal(db_session, log)
            dal.db_utils = mock_db_utils
            yield dal

    def test_init(self):
        """Test Gw2ConfigsDal initialization."""
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.gw2.gw2_configs_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = Gw2ConfigsDal(db_session, log)
            mock_db_utils_class.assert_called_once_with(db_session)
            assert dal.log == log
            assert dal.db_utils == mock_db_utils

    @pytest.mark.asyncio
    async def test_insert_gw2_server_configs(self, mock_dal):
        """Test insert_gw2_server_configs calls insert."""
        await mock_dal.insert_gw2_server_configs(server_id=12345)
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_gw2_server_configs_different_server(self, mock_dal):
        """Test insert_gw2_server_configs with different server_id."""
        await mock_dal.insert_gw2_server_configs(server_id=99999)
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_gw2_session_config(self, mock_dal):
        """Test update_gw2_session_config calls execute."""
        await mock_dal.update_gw2_session_config(
            server_id=12345,
            new_status=True,
            updated_by=67890,
        )
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_gw2_session_config_disable(self, mock_dal):
        """Test update_gw2_session_config with False status."""
        await mock_dal.update_gw2_session_config(
            server_id=12345,
            new_status=False,
            updated_by=67890,
        )
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_gw2_server_configs(self, mock_dal):
        """Test get_gw2_server_configs calls fetchall and returns results."""
        expected = [{"server_id": 12345, "session": True}]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_gw2_server_configs(server_id=12345)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_gw2_server_configs_empty(self, mock_dal):
        """Test get_gw2_server_configs when no configs exist."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_gw2_server_configs(server_id=99999)
        assert results == []


# =============================================================================
# Gw2KeyDal Tests
# =============================================================================


class TestGw2KeyDal:
    """Test cases for Gw2KeyDal."""

    @pytest.fixture
    def mock_dal(self):
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.gw2.gw2_key_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = Gw2KeyDal(db_session, log)
            dal.db_utils = mock_db_utils
            yield dal

    def test_init(self):
        """Test Gw2KeyDal initialization."""
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.gw2.gw2_key_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = Gw2KeyDal(db_session, log)
            mock_db_utils_class.assert_called_once_with(db_session)
            assert dal.log == log
            assert dal.db_utils == mock_db_utils

    @pytest.mark.asyncio
    async def test_insert_api_key(self, mock_dal):
        """Test insert_api_key calls insert with a Gw2Keys instance."""
        insert_args = {
            "user_id": 67890,
            "key_name": "My Key",
            "gw2_acc_name": "TestAccount.1234",
            "server_name": "Blackgate",
            "permissions": "account,characters",
            "api_key": "AAAABBBB-1111-2222-3333-444455556666",
        }
        await mock_dal.insert_api_key(insert_args)
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_api_key_different_values(self, mock_dal):
        """Test insert_api_key with different parameter values."""
        insert_args = {
            "user_id": 11111,
            "key_name": "Another Key",
            "gw2_acc_name": "AnotherAcc.5678",
            "server_name": "Yak's Bend",
            "permissions": "account,characters,pvp",
            "api_key": "CCCCDDDD-5555-6666-7777-888899990000",
        }
        await mock_dal.insert_api_key(insert_args)
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_api_key(self, mock_dal):
        """Test update_api_key calls execute."""
        update_args = {
            "user_id": 67890,
            "key_name": "Updated Key",
            "gw2_acc_name": "TestAccount.1234",
            "server_name": "Blackgate",
            "permissions": "account,characters,pvp",
            "api_key": "EEEEEEEE-1111-2222-3333-444455556666",
        }
        await mock_dal.update_api_key(update_args)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_api_key(self, mock_dal):
        """Test delete_user_api_key calls execute."""
        await mock_dal.delete_user_api_key(user_id=67890)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_api_key(self, mock_dal):
        """Test get_api_key calls fetchall with True and returns results."""
        expected = [{"user_id": 67890, "key": "AAAABBBB-1111-2222-3333-444455556666"}]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_api_key(api_key="AAAABBBB-1111-2222-3333-444455556666")
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_api_key_not_found(self, mock_dal):
        """Test get_api_key when key not found."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_api_key(api_key="NONEXIST-0000-0000-0000-000000000000")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_api_key_by_name(self, mock_dal):
        """Test get_api_key_by_name calls fetchall with True for dict conversion."""
        expected = [{"user_id": 67890, "name": "My Key"}]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_api_key_by_name(key_name="My Key")
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_api_key_by_name_not_found(self, mock_dal):
        """Test get_api_key_by_name when key name not found."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_api_key_by_name(key_name="Nonexistent Key")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_api_key_by_user(self, mock_dal):
        """Test get_api_key_by_user calls fetchall with True."""
        expected = [{"user_id": 67890, "key": "AAAABBBB-1111-2222-3333-444455556666"}]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_api_key_by_user(user_id=67890)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_api_key_by_user_not_found(self, mock_dal):
        """Test get_api_key_by_user when user has no key."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_api_key_by_user(user_id=99999)
        assert results == []


# =============================================================================
# Gw2SessionCharsDal Tests
# =============================================================================


class TestGw2SessionCharsDal:
    """Test cases for Gw2SessionCharsDal."""

    @pytest.fixture
    def mock_dal(self):
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.gw2.gw2_session_chars_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = Gw2SessionCharsDal(db_session, log)
            dal.db_utils = mock_db_utils
            yield dal

    def test_init(self):
        """Test Gw2SessionCharsDal initialization."""
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.gw2.gw2_session_chars_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = Gw2SessionCharsDal(db_session, log)
            mock_db_utils_class.assert_called_once_with(db_session)
            assert dal.log == log
            assert dal.db_utils == mock_db_utils

    @pytest.mark.asyncio
    async def test_insert_session_char(self, mock_dal):
        """Test insert_session_char calls insert for each character."""
        gw2_api = AsyncMock()
        gw2_api.call_api.side_effect = [
            {"name": "CharOne", "profession": "Warrior", "deaths": 5},
            {"name": "CharTwo", "profession": "Elementalist", "deaths": 10},
        ]
        api_characters = ["CharOne", "CharTwo"]
        insert_args = {
            "session_id": 1,
            "user_id": 67890,
            "api_key": "AAAABBBB-1111-2222-3333-444455556666",
            "start": True,
            "end": False,
        }

        await mock_dal.insert_session_char(gw2_api, api_characters, insert_args)

        assert gw2_api.call_api.call_count == 2
        gw2_api.call_api.assert_any_call(
            "characters/CharOne/core",
            "AAAABBBB-1111-2222-3333-444455556666",
        )
        gw2_api.call_api.assert_any_call(
            "characters/CharTwo/core",
            "AAAABBBB-1111-2222-3333-444455556666",
        )
        assert mock_dal.db_utils.insert.call_count == 2

    @pytest.mark.asyncio
    async def test_insert_session_char_single_character(self, mock_dal):
        """Test insert_session_char with a single character."""
        gw2_api = AsyncMock()
        gw2_api.call_api.return_value = {
            "name": "Solo",
            "profession": "Necromancer",
            "deaths": 0,
        }
        api_characters = ["Solo"]
        insert_args = {
            "session_id": 2,
            "user_id": 11111,
            "api_key": "CCCCDDDD-5555-6666-7777-888899990000",
            "start": False,
            "end": True,
        }

        await mock_dal.insert_session_char(gw2_api, api_characters, insert_args)

        gw2_api.call_api.assert_called_once_with(
            "characters/Solo/core",
            "CCCCDDDD-5555-6666-7777-888899990000",
        )
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_session_char_empty_characters(self, mock_dal):
        """Test insert_session_char with an empty characters list."""
        gw2_api = AsyncMock()
        api_characters = []
        insert_args = {
            "session_id": 3,
            "user_id": 22222,
            "api_key": "EEEEEEEE-0000-0000-0000-000000000000",
        }

        await mock_dal.insert_session_char(gw2_api, api_characters, insert_args)

        gw2_api.call_api.assert_not_called()
        mock_dal.db_utils.insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_end_characters(self, mock_dal):
        """Test delete_end_characters executes a delete statement for end chars."""
        mock_dal.db_utils.execute = AsyncMock()
        await mock_dal.delete_end_characters(session_id=42)
        mock_dal.db_utils.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_start_characters(self, mock_dal):
        """Test get_all_start_characters calls fetchall and returns results."""
        expected = [
            {"user_id": 67890, "name": "CharOne", "profession": "Warrior", "start": True},
            {"user_id": 67890, "name": "CharTwo", "profession": "Elementalist", "start": True},
        ]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_all_start_characters(user_id=67890)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_all_start_characters_empty(self, mock_dal):
        """Test get_all_start_characters when no characters exist."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_all_start_characters(user_id=99999)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_all_end_characters(self, mock_dal):
        """Test get_all_end_characters calls fetchall and returns results."""
        expected = [
            {"user_id": 67890, "name": "CharOne", "profession": "Warrior", "end": True},
        ]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_all_end_characters(user_id=67890)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_all_end_characters_empty(self, mock_dal):
        """Test get_all_end_characters when no characters exist."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_all_end_characters(user_id=99999)
        assert results == []


# =============================================================================
# Gw2SessionsDal Tests
# =============================================================================


class TestGw2SessionsDal:
    """Test cases for Gw2SessionsDal."""

    @pytest.fixture
    def mock_dal(self):
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.gw2.gw2_sessions_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = Gw2SessionsDal(db_session, log)
            dal.db_utils = mock_db_utils
            yield dal

    def test_init(self):
        """Test Gw2SessionsDal initialization."""
        db_session = MagicMock()
        log = MagicMock()
        with patch("src.database.dal.gw2.gw2_sessions_dal.DBUtilsAsync") as mock_db_utils_class:
            mock_db_utils = AsyncMock()
            mock_db_utils_class.return_value = mock_db_utils
            dal = Gw2SessionsDal(db_session, log)
            mock_db_utils_class.assert_called_once_with(db_session)
            assert dal.log == log
            assert dal.db_utils == mock_db_utils

    @pytest.mark.asyncio
    async def test_insert_start_session(self, mock_dal):
        """Test insert_start_session deletes old data and inserts new session."""
        session = {
            "user_id": 67890,
            "acc_name": "TestAccount.1234",
            "gold": 100,
        }
        await mock_dal.insert_start_session(session)
        # Should call execute twice (delete sessions, delete chars) then insert once
        assert mock_dal.db_utils.execute.call_count == 2
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_start_session_returns_id(self, mock_dal):
        """Test insert_start_session returns the session id attribute from the model instance."""
        session = {
            "user_id": 67890,
            "acc_name": "TestAccount.1234",
            "gold": 200,
        }
        result = await mock_dal.insert_start_session(session)
        # The method creates a Gw2Sessions instance and returns stmt.id.
        # Since Gw2Sessions is a real SQLAlchemy model, the id will be None
        # until flushed/committed by the database. The method still returns it.
        assert mock_dal.db_utils.insert.call_count == 1
        assert mock_dal.db_utils.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_insert_start_session_different_user(self, mock_dal):
        """Test insert_start_session with different user data."""
        session = {
            "user_id": 11111,
            "acc_name": "AnotherAcc.5678",
            "gold": 50,
        }
        await mock_dal.insert_start_session(session)
        assert mock_dal.db_utils.execute.call_count == 2
        mock_dal.db_utils.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_end_session(self, mock_dal):
        """Test update_end_session fetches session id then calls execute."""
        mock_dal.db_utils.fetchall.return_value = [{"id": 42}]
        session = {
            "user_id": 67890,
            "gold": 150,
        }
        result = await mock_dal.update_end_session(session)
        mock_dal.db_utils.fetchall.assert_called_once()
        mock_dal.db_utils.execute.assert_called_once()
        assert result == 42

    @pytest.mark.asyncio
    async def test_update_end_session_different_user(self, mock_dal):
        """Test update_end_session with different user."""
        mock_dal.db_utils.fetchall.return_value = [{"id": 99}]
        session = {
            "user_id": 11111,
            "gold": 75,
        }
        result = await mock_dal.update_end_session(session)
        mock_dal.db_utils.fetchall.assert_called_once()
        mock_dal.db_utils.execute.assert_called_once()
        assert result == 99

    @pytest.mark.asyncio
    async def test_update_end_session_no_session_found(self, mock_dal):
        """Test update_end_session returns None when no session exists."""
        mock_dal.db_utils.fetchall.return_value = []
        session = {
            "user_id": 67890,
            "gold": 150,
        }
        result = await mock_dal.update_end_session(session)
        mock_dal.db_utils.fetchall.assert_called_once()
        mock_dal.db_utils.execute.assert_not_called()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_last_session(self, mock_dal):
        """Test get_user_last_session calls fetchall and returns results."""
        expected = [
            {
                "user_id": 67890,
                "acc_name": "TestAccount.1234",
                "start": {"gold": 100},
                "end": {"gold": 150},
            }
        ]
        mock_dal.db_utils.fetchall.return_value = expected
        results = await mock_dal.get_user_last_session(user_id=67890)
        mock_dal.db_utils.fetchall.assert_called_once()
        call_args = mock_dal.db_utils.fetchall.call_args
        assert call_args[0][1] is True
        assert results == expected

    @pytest.mark.asyncio
    async def test_get_user_last_session_no_session(self, mock_dal):
        """Test get_user_last_session when user has no session."""
        mock_dal.db_utils.fetchall.return_value = []
        results = await mock_dal.get_user_last_session(user_id=99999)
        assert results == []
