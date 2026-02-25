"""Comprehensive tests for GW2 utilities module."""

import discord
import pytest
from datetime import datetime, timedelta
from src.gw2.constants.gw2_currencies import WALLET_DISPLAY_NAMES, WALLET_MAPPING
from src.gw2.tools.gw2_exceptions import APIConnectionError
from src.gw2.tools.gw2_utils import (
    TimeObject,
    _calculate_earned_points,
    _create_initial_user_stats,
    _fetch_achievement_data_in_batches,
    _get_non_custom_activity,
    _get_wvw_rank_prefix,
    _handle_gw2_activity_change,
    _is_gw2_activity_detected,
    _retry_session_later,
    _update_achievement_stats,
    _update_wallet_stats,
    calculate_user_achiev_points,
    check_gw2_game_activity,
    convert_timedelta_to_obj,
    delete_api_key,
    earned_ap,
    end_session,
    format_gold,
    format_seconds_to_time,
    get_pvp_rank_title,
    get_time_passed,
    get_user_stats,
    get_world_id,
    get_world_name,
    get_world_name_population,
    get_worlds_ids,
    get_wvw_rank_title,
    insert_gw2_server_configs,
    insert_session_char,
    is_private_message,
    max_ap,
    send_msg,
    start_session,
)
from unittest.mock import AsyncMock, MagicMock, patch


class TestSendMsg:
    """Test cases for send_msg function."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x123456}}
        return ctx

    @pytest.mark.asyncio
    async def test_send_msg_default_settings(self, mock_ctx):
        """Test send_msg with default settings."""
        with patch("src.gw2.tools.gw2_utils.bot_utils.send_embed") as mock_send:
            await send_msg(mock_ctx, "Test message")

            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            ctx, _, dm = args[0], args[1], args[2]

            assert ctx == mock_ctx
            assert args[1].description == "Test message"
            assert args[1].color.value == 0x123456
            assert dm is False

    @pytest.mark.asyncio
    async def test_send_msg_with_dm(self, mock_ctx):
        """Test send_msg with DM option."""
        with patch("src.gw2.tools.gw2_utils.bot_utils.send_embed") as mock_send:
            await send_msg(mock_ctx, "DM message", dm=True)

            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            _, _, dm = args[0], args[1], args[2]
            assert dm is True


class TestInsertGw2ServerConfigs:
    """Test cases for insert_gw2_server_configs function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def mock_server(self):
        """Create a mock Discord server."""
        server = MagicMock()
        server.id = 12345
        return server

    @pytest.mark.asyncio
    async def test_insert_configs_when_not_exists(self, mock_bot, mock_server):
        """Test inserting configs when they don't exist."""
        with patch("src.gw2.tools.gw2_utils.Gw2ConfigsDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=None)
            mock_instance.insert_gw2_server_configs = AsyncMock(return_value=None)

            await insert_gw2_server_configs(mock_bot, mock_server)

            mock_instance.get_gw2_server_configs.assert_called_once_with(12345)
            mock_instance.insert_gw2_server_configs.assert_called_once_with(12345)

    @pytest.mark.asyncio
    async def test_skip_insert_when_configs_exist(self, mock_bot, mock_server):
        """Test skipping insert when configs already exist."""
        with patch("src.gw2.tools.gw2_utils.Gw2ConfigsDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value={"existing": "config"})
            mock_instance.insert_gw2_server_configs = AsyncMock(return_value=None)

            await insert_gw2_server_configs(mock_bot, mock_server)

            mock_instance.get_gw2_server_configs.assert_called_once_with(12345)
            mock_instance.insert_gw2_server_configs.assert_not_called()


class TestFetchAchievementDataInBatches:
    """Test cases for _fetch_achievement_data_in_batches function."""

    @pytest.mark.asyncio
    async def test_single_batch_under_200(self):
        """Test fetching with fewer than 200 achievements (single batch)."""
        mock_gw2_api = MagicMock()
        user_achievements = [{"id": i} for i in range(50)]
        expected_response = [{"id": i, "name": f"ach_{i}"} for i in range(50)]

        mock_gw2_api.call_api = AsyncMock(return_value=expected_response)

        result = await _fetch_achievement_data_in_batches(mock_gw2_api, user_achievements)

        assert result == expected_response
        mock_gw2_api.call_api.assert_called_once()
        call_args = mock_gw2_api.call_api.call_args[0][0]
        assert call_args.startswith("achievements?ids=")

    @pytest.mark.asyncio
    async def test_multiple_batches(self):
        """Test fetching with more than 200 achievements (multiple batches)."""
        mock_gw2_api = MagicMock()
        user_achievements = [{"id": i} for i in range(450)]

        batch_1_response = [{"id": i, "name": f"ach_{i}"} for i in range(200)]
        batch_2_response = [{"id": i, "name": f"ach_{i}"} for i in range(200, 400)]
        batch_3_response = [{"id": i, "name": f"ach_{i}"} for i in range(400, 450)]

        mock_gw2_api.call_api = AsyncMock(side_effect=[batch_1_response, batch_2_response, batch_3_response])

        result = await _fetch_achievement_data_in_batches(mock_gw2_api, user_achievements)

        assert len(result) == 450
        assert mock_gw2_api.call_api.call_count == 3

    @pytest.mark.asyncio
    async def test_exactly_200_items(self):
        """Test fetching with exactly 200 achievements (one full batch)."""
        mock_gw2_api = MagicMock()
        user_achievements = [{"id": i} for i in range(200)]
        expected_response = [{"id": i, "name": f"ach_{i}"} for i in range(200)]

        mock_gw2_api.call_api = AsyncMock(return_value=expected_response)

        result = await _fetch_achievement_data_in_batches(mock_gw2_api, user_achievements)

        assert len(result) == 200
        mock_gw2_api.call_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_list(self):
        """Test fetching with empty achievements list."""
        mock_gw2_api = MagicMock()
        mock_gw2_api.call_api = AsyncMock()

        result = await _fetch_achievement_data_in_batches(mock_gw2_api, [])

        assert result == []
        mock_gw2_api.call_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_ids_joined_correctly(self):
        """Test that achievement IDs are comma-joined in the API call."""
        mock_gw2_api = MagicMock()
        user_achievements = [{"id": 10}, {"id": 20}, {"id": 30}]

        mock_gw2_api.call_api = AsyncMock(return_value=[])

        await _fetch_achievement_data_in_batches(mock_gw2_api, user_achievements)

        call_args = mock_gw2_api.call_api.call_args[0][0]
        assert call_args == "achievements?ids=10,20,30"


class TestCalculateEarnedPoints:
    """Test cases for _calculate_earned_points function."""

    def test_basic_calculation(self):
        """Test basic earned points calculation."""
        user_achievements = [
            {"id": 1, "current": 10, "repeated": 0},
            {"id": 2, "current": 5, "repeated": 0},
        ]
        achievement_data = [
            {"id": 1, "tiers": [{"count": 5, "points": 10}, {"count": 10, "points": 20}]},
            {"id": 2, "tiers": [{"count": 3, "points": 5}, {"count": 8, "points": 15}]},
        ]

        result = _calculate_earned_points(user_achievements, achievement_data)

        # Achievement 1: current=10 >= count=5 (10pts) + current=10 >= count=10 (20pts) = 30
        # Achievement 2: current=5 >= count=3 (5pts) + current=5 < count=8 = 5
        assert result == 35

    def test_missing_achievement_in_lookup(self):
        """Test that unknown achievement IDs are skipped."""
        user_achievements = [
            {"id": 1, "current": 10, "repeated": 0},
            {"id": 999, "current": 5, "repeated": 0},  # Not in data
        ]
        achievement_data = [
            {"id": 1, "tiers": [{"count": 5, "points": 10}]},
        ]

        result = _calculate_earned_points(user_achievements, achievement_data)

        # Only achievement 1 contributes: 10 points
        assert result == 10

    def test_empty_user_achievements(self):
        """Test with empty user achievements list."""
        result = _calculate_earned_points([], [{"id": 1, "tiers": [{"count": 5, "points": 10}]}])
        assert result == 0

    def test_empty_achievement_data(self):
        """Test with empty achievement data list."""
        user_achievements = [{"id": 1, "current": 10, "repeated": 0}]
        result = _calculate_earned_points(user_achievements, [])
        assert result == 0

    def test_with_repeated_achievements(self):
        """Test calculation with repeated achievements."""
        user_achievements = [
            {"id": 1, "current": 10, "repeated": 2},
        ]
        achievement_data = [
            {"id": 1, "tiers": [{"count": 5, "points": 5}], "point_cap": 50},
        ]

        result = _calculate_earned_points(user_achievements, achievement_data)

        # earned_ap will compute: tier points (5) + base*repeats (5*2) = 15, capped at max_ap(ach, repeats=2)=50
        assert result == 15


class TestCalculateUserAchievPoints:
    """Test cases for calculate_user_achiev_points function."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        return ctx

    @pytest.fixture
    def sample_user_achievements(self):
        """Create sample user achievement data."""
        return [{"id": 1, "current": 10, "repeated": 0}, {"id": 2, "current": 5, "repeated": 1}]

    @pytest.fixture
    def sample_account_data(self):
        """Create sample account data."""
        return {"daily_ap": 100, "monthly_ap": 50}

    @pytest.mark.asyncio
    async def test_calculate_achievement_points(self, mock_ctx, sample_user_achievements, sample_account_data):
        """Test calculating achievement points."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client"):
            with patch("src.gw2.tools.gw2_utils._fetch_achievement_data_in_batches") as mock_fetch:
                mock_fetch.return_value = [
                    {"id": 1, "tiers": [{"count": 5, "points": 10}, {"count": 10, "points": 20}]},
                    {"id": 2, "tiers": [{"count": 3, "points": 5}]},
                ]

                with patch("src.gw2.tools.gw2_utils._calculate_earned_points") as mock_calc:
                    mock_calc.return_value = 75

                    result = await calculate_user_achiev_points(mock_ctx, sample_user_achievements, sample_account_data)

                    assert result == 225  # 100 + 50 + 75
                    mock_fetch.assert_called_once()
                    mock_calc.assert_called_once()


class TestEarnedAp:
    """Test cases for earned_ap function."""

    def test_earned_ap_with_no_achievement(self):
        """Test earned_ap with None achievement."""
        result = earned_ap(None, {"current": 10})
        assert result == 0

    def test_earned_ap_with_empty_achievement(self):
        """Test earned_ap with empty achievement."""
        result = earned_ap({}, {"current": 10})
        assert result == 0

    def test_earned_ap_with_tiers(self):
        """Test earned_ap with achievement tiers."""
        achievement = {"tiers": [{"count": 5, "points": 10}, {"count": 10, "points": 20}, {"count": 15, "points": 30}]}
        user_progress = {"current": 12, "repeated": 0}

        result = earned_ap(achievement, user_progress)
        # Tiers completed: count=5 (10pts) + count=10 (20pts) = 30
        # max_ap(achievement, repeats=0) = sum of tiers = 60 (since repeatable=False, returns sum)
        # min(30, 60) = 30
        assert result == 30

    def test_earned_ap_with_repeats(self):
        """Test earned_ap with repeated achievements."""
        achievement = {
            "tiers": [{"count": 5, "points": 10}],
            "point_cap": 100,
        }
        user_progress = {"current": 6, "repeated": 2}

        result = earned_ap(achievement, user_progress)
        # Tier points: 10 (current=6 >= count=5)
        # max_ap(achievement) without repeatable = sum of tiers = 10
        # earned += 10 * 2 = 20 => total earned = 30
        # max_possible = max_ap(achievement, repeats=2) = point_cap = 100
        # min(30, 100) = 30
        assert result == 30

    def test_earned_ap_capped_at_max(self):
        """Test earned_ap is capped at max possible points."""
        achievement = {
            "tiers": [{"count": 1, "points": 10}],
            "point_cap": 15,
        }
        user_progress = {"current": 5, "repeated": 3}

        result = earned_ap(achievement, user_progress)
        # Tier: 10 (current=5 >= count=1)
        # max_ap(achievement) = 10 (sum of tiers)
        # earned += 10 * 3 = 30 => total = 40
        # max_possible = max_ap(achievement, 3) = point_cap = 15
        # min(40, 15) = 15
        assert result == 15

    def test_earned_ap_no_current_progress(self):
        """Test earned_ap with no current progress."""
        achievement = {"tiers": [{"count": 5, "points": 10}]}
        user_progress = {"repeated": 0}

        result = earned_ap(achievement, user_progress)
        # current defaults to 0, 0 < 5, no tier points earned
        assert result == 0


class TestMaxAp:
    """Test cases for max_ap function."""

    def test_max_ap_with_none(self):
        """Test max_ap with None achievement."""
        result = max_ap(None)
        assert result == 0

    def test_max_ap_with_empty_achievement(self):
        """Test max_ap with empty achievement."""
        result = max_ap({})
        assert result == 0

    def test_max_ap_repeatable(self):
        """Test max_ap with repeatable achievement."""
        achievement = {"point_cap": 500}
        result = max_ap(achievement, repeatable=True)
        assert result == 500

    def test_max_ap_repeatable_no_cap(self):
        """Test max_ap with repeatable but no point_cap."""
        achievement = {"tiers": [{"points": 10}]}
        result = max_ap(achievement, repeatable=True)
        assert result == 0

    def test_max_ap_with_tiers(self):
        """Test max_ap with achievement tiers."""
        achievement = {"tiers": [{"points": 10}, {"points": 20}, {"points": 30}]}
        result = max_ap(achievement)
        assert result == 60

    def test_max_ap_with_empty_tiers(self):
        """Test max_ap with empty tiers list."""
        achievement = {"tiers": []}
        result = max_ap(achievement)
        assert result == 0


class TestGetWorldId:
    """Test cases for get_world_id function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.mark.asyncio
    async def test_get_world_id_exact_match(self, mock_bot):
        """Test successful world ID retrieval with exact match."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(
                return_value=[{"id": 1001, "name": "Anvil Rock"}, {"id": 1002, "name": "Borlis Pass"}]
            )

            result = await get_world_id(mock_bot, "Anvil Rock")
            assert result == 1001

    @pytest.mark.asyncio
    async def test_get_world_id_case_insensitive(self, mock_bot):
        """Test world ID retrieval with case-insensitive match."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(
                return_value=[
                    {"id": 1001, "name": "Anvil Rock"},
                ]
            )

            result = await get_world_id(mock_bot, "anvil rock")
            assert result == 1001

    @pytest.mark.asyncio
    async def test_get_world_id_partial_match(self, mock_bot):
        """Test world ID retrieval with partial match (line 196)."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(
                return_value=[
                    {"id": 1001, "name": "Anvil Rock"},
                    {"id": 1006, "name": "Jade Quarry"},
                    {"id": 1007, "name": "Jade Sea [FR]"},
                ]
            )

            # Partial match: "jade" should match "jade quarry" first
            result = await get_world_id(mock_bot, "jade")
            assert result in (1006, 1007)  # Either Jade world is valid

    @pytest.mark.asyncio
    async def test_get_world_id_not_found(self, mock_bot):
        """Test world ID not found."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(return_value=[{"id": 1001, "name": "Anvil Rock"}])

            result = await get_world_id(mock_bot, "Non-existent World")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_world_id_with_none_world(self, mock_bot):
        """Test get_world_id with None world."""
        result = await get_world_id(mock_bot, None)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_world_id_api_error(self, mock_bot):
        """Test get_world_id with API error."""
        mock_bot.log.error = MagicMock()

        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(side_effect=Exception("API Error"))

            result = await get_world_id(mock_bot, "Anvil Rock")
            assert result is None
            mock_bot.log.error.assert_called_once()


class TestGetWorldNamePopulation:
    """Test cases for get_world_name_population function."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.log = MagicMock()
        return ctx

    @pytest.mark.asyncio
    async def test_successful_retrieval(self, mock_ctx):
        """Test successful world name population retrieval for legacy IDs."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(
                return_value=[
                    {"id": 1001, "name": "Anvil Rock", "population": "High"},
                    {"id": 1002, "name": "Borlis Pass", "population": "Medium"},
                ]
            )

            result = await get_world_name_population(mock_ctx, "1001,1002")

            assert result == ["Anvil Rock", "Borlis Pass"]
            mock_client.call_api.assert_called_once_with("worlds?ids=1001,1002")

    @pytest.mark.asyncio
    async def test_empty_results(self, mock_ctx):
        """Test when API returns empty results (line 211)."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(return_value=[])

            result = await get_world_name_population(mock_ctx, "9999")

            assert result is None

    @pytest.mark.asyncio
    async def test_none_results(self, mock_ctx):
        """Test when API returns None."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(return_value=None)

            result = await get_world_name_population(mock_ctx, "9999")

            assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self, mock_ctx):
        """Test that exception returns None (lines 215-217)."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(side_effect=Exception("API Error"))

            result = await get_world_name_population(mock_ctx, "1001")

            assert result is None
            mock_ctx.bot.log.error.assert_called_once()


class TestGetWorldName:
    """Test cases for get_world_name function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.mark.asyncio
    async def test_successful_retrieval(self, mock_bot):
        """Test successful world name retrieval (lines 222-225)."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(return_value={"name": "Anvil Rock", "id": 1001})

            result = await get_world_name(mock_bot, "1001")

            assert result == "Anvil Rock"

    @pytest.mark.asyncio
    async def test_no_result_returns_none(self, mock_bot):
        """Test that empty result returns None (line 225)."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(return_value=None)

            result = await get_world_name(mock_bot, "9999")

            assert result is None

    @pytest.mark.asyncio
    async def test_result_without_name_key(self, mock_bot):
        """Test result dict without name key."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(return_value={"id": 1001})

            result = await get_world_name(mock_bot, "1001")

            assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self, mock_bot):
        """Test that exception returns None (lines 227-229)."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(side_effect=Exception("API Error"))

            result = await get_world_name(mock_bot, "1001")

            assert result is None
            mock_bot.log.error.assert_called_once()


class TestCheckGw2GameActivity:
    """Test cases for check_gw2_game_activity function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.mark.asyncio
    async def test_gw2_activity_detected_triggers_handler(self, mock_bot):
        """Test that GW2 activity detected triggers handler (lines 250-254)."""
        before = MagicMock()
        after = MagicMock()

        gw2_activity = MagicMock()
        gw2_activity.type = discord.ActivityType.playing
        gw2_activity.name = "Guild Wars 2"

        before.activities = []
        after.activities = [gw2_activity]

        with patch("src.gw2.tools.gw2_utils._handle_gw2_activity_change") as mock_handle:
            mock_handle.return_value = None
            await check_gw2_game_activity(mock_bot, before, after)
            mock_handle.assert_called_once_with(mock_bot, after, gw2_activity)

    @pytest.mark.asyncio
    async def test_no_gw2_activity_does_nothing(self, mock_bot):
        """Test that non-GW2 activity does nothing (lines 250-254)."""
        before = MagicMock()
        after = MagicMock()

        other_activity = MagicMock()
        other_activity.type = discord.ActivityType.playing
        other_activity.name = "World of Warcraft"

        before.activities = []
        after.activities = [other_activity]

        with patch("src.gw2.tools.gw2_utils._handle_gw2_activity_change") as mock_handle:
            await check_gw2_game_activity(mock_bot, before, after)
            mock_handle.assert_not_called()

    @pytest.mark.asyncio
    async def test_custom_activity_ignored(self, mock_bot):
        """Test that custom activities are skipped."""
        before = MagicMock()
        after = MagicMock()

        custom_activity = MagicMock()
        custom_activity.type = discord.ActivityType.custom
        custom_activity.name = "Guild Wars 2"

        before.activities = [custom_activity]
        after.activities = [custom_activity]

        with patch("src.gw2.tools.gw2_utils._handle_gw2_activity_change") as mock_handle:
            await check_gw2_game_activity(mock_bot, before, after)
            mock_handle.assert_not_called()


class TestHandleGw2ActivityChange:
    """Test cases for _handle_gw2_activity_change function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def mock_member(self):
        """Create a mock member."""
        member = MagicMock()
        member.id = 12345
        member.guild = MagicMock()
        member.guild.id = 67890
        return member

    @pytest.mark.asyncio
    async def test_no_server_configs_returns(self, mock_bot, mock_member):
        """Test that no server configs returns early (line 281)."""
        with patch("src.gw2.tools.gw2_utils.Gw2ConfigsDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=None)

            after_activity = MagicMock()
            await _handle_gw2_activity_change(mock_bot, mock_member, after_activity)

            # Should not proceed to Gw2KeyDal
            with patch("src.gw2.tools.gw2_utils.Gw2KeyDal") as mock_key_dal:
                mock_key_dal.assert_not_called()

    @pytest.mark.asyncio
    async def test_session_not_active_returns(self, mock_bot, mock_member):
        """Test that inactive session returns early (line 281)."""
        with patch("src.gw2.tools.gw2_utils.Gw2ConfigsDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=[{"session": False}])

            after_activity = MagicMock()
            await _handle_gw2_activity_change(mock_bot, mock_member, after_activity)

    @pytest.mark.asyncio
    async def test_no_api_key_returns(self, mock_bot, mock_member):
        """Test that no API key returns early (lines 287-288)."""
        with patch("src.gw2.tools.gw2_utils.Gw2ConfigsDal") as mock_dal:
            mock_configs = mock_dal.return_value
            mock_configs.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])

            with patch("src.gw2.tools.gw2_utils.Gw2KeyDal") as mock_key_dal:
                mock_key_instance = mock_key_dal.return_value
                mock_key_instance.get_api_key_by_user = AsyncMock(return_value=None)

                after_activity = MagicMock()
                await _handle_gw2_activity_change(mock_bot, mock_member, after_activity)

    @pytest.mark.asyncio
    async def test_after_activity_not_none_starts_session(self, mock_bot, mock_member):
        """Test that non-None after_activity starts a session (lines 292-293)."""
        with patch("src.gw2.tools.gw2_utils.Gw2ConfigsDal") as mock_dal:
            mock_configs = mock_dal.return_value
            mock_configs.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])

            with patch("src.gw2.tools.gw2_utils.Gw2KeyDal") as mock_key_dal:
                mock_key_instance = mock_key_dal.return_value
                mock_key_instance.get_api_key_by_user = AsyncMock(return_value=[{"key": "test-api-key-123"}])

                with patch("src.gw2.tools.gw2_utils.start_session") as mock_start:
                    mock_start.return_value = None
                    after_activity = MagicMock()  # Not None

                    await _handle_gw2_activity_change(mock_bot, mock_member, after_activity)

                    mock_start.assert_called_once_with(mock_bot, mock_member, "test-api-key-123")

    @pytest.mark.asyncio
    async def test_after_activity_none_ends_session(self, mock_bot, mock_member):
        """Test that None after_activity ends a session (lines 294-295)."""
        with patch("src.gw2.tools.gw2_utils.Gw2ConfigsDal") as mock_dal:
            mock_configs = mock_dal.return_value
            mock_configs.get_gw2_server_configs = AsyncMock(return_value=[{"session": True}])

            with patch("src.gw2.tools.gw2_utils.Gw2KeyDal") as mock_key_dal:
                mock_key_instance = mock_key_dal.return_value
                mock_key_instance.get_api_key_by_user = AsyncMock(return_value=[{"key": "test-api-key-123"}])

                with patch("src.gw2.tools.gw2_utils.end_session") as mock_end:
                    mock_end.return_value = None

                    await _handle_gw2_activity_change(mock_bot, mock_member, None)

                    mock_end.assert_called_once_with(mock_bot, mock_member, "test-api-key-123")


class TestStartSession:
    """Test cases for start_session function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def mock_member(self):
        """Create a mock member."""
        member = MagicMock()
        member.id = 12345
        return member

    @pytest.mark.asyncio
    async def test_get_user_stats_returns_none_schedules_bg_retry(self, mock_bot, mock_member):
        """Test that None user stats schedules background retry task."""
        with patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats:
            mock_stats.return_value = None

            with patch("src.gw2.tools.gw2_utils.asyncio.create_task") as mock_create_task:
                mock_task = MagicMock()
                mock_create_task.return_value = mock_task

                await start_session(mock_bot, mock_member, "api-key")

                mock_create_task.assert_called_once()
                mock_task.add_done_callback.assert_called_once()
                mock_bot.log.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_start_session(self, mock_bot, mock_member):
        """Test successful session start (lines 304-309)."""
        session_data = {"acc_name": "TestUser.1234", "wvw_rank": 50, "gold": 1000}

        with patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats:
            mock_stats.return_value = session_data.copy()

            with patch("src.gw2.tools.gw2_utils.bot_utils.convert_datetime_to_str_short") as mock_convert:
                mock_convert.return_value = "2023-01-01"

                with patch("src.gw2.tools.gw2_utils.bot_utils.get_current_date_time") as mock_time:
                    mock_time.return_value = datetime(2023, 1, 1, 12, 0, 0)

                    with patch("src.gw2.tools.gw2_utils.Gw2SessionsDal") as mock_session_dal:
                        mock_instance = mock_session_dal.return_value
                        mock_instance.insert_start_session = AsyncMock(return_value=42)

                        with patch("src.gw2.tools.gw2_utils.insert_session_char") as mock_insert_char:
                            mock_insert_char.return_value = None

                            await start_session(mock_bot, mock_member, "api-key")

                            mock_instance.insert_start_session.assert_called_once()
                            call_arg = mock_instance.insert_start_session.call_args[0][0]
                            assert call_arg["user_id"] == 12345
                            assert call_arg["date"] == "2023-01-01"

                            mock_insert_char.assert_called_once_with(mock_bot, mock_member, "api-key", 42, "start")


class TestEndSession:
    """Test cases for end_session function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def mock_member(self):
        """Create a mock member."""
        member = MagicMock()
        member.id = 12345
        return member

    @pytest.mark.asyncio
    async def test_get_user_stats_returns_none_schedules_bg_retry(self, mock_bot, mock_member):
        """Test that None user stats schedules background retry task."""
        with patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats:
            mock_stats.return_value = None

            with patch("src.gw2.tools.gw2_utils.asyncio.create_task") as mock_create_task:
                mock_task = MagicMock()
                mock_create_task.return_value = mock_task

                await end_session(mock_bot, mock_member, "api-key")

                mock_create_task.assert_called_once()
                mock_task.add_done_callback.assert_called_once()
                mock_bot.log.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_end_session(self, mock_bot, mock_member):
        """Test successful session end (lines 318-323)."""
        session_data = {"acc_name": "TestUser.1234", "wvw_rank": 50, "gold": 1000}

        with patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats:
            mock_stats.return_value = session_data.copy()

            with patch("src.gw2.tools.gw2_utils.bot_utils.convert_datetime_to_str_short") as mock_convert:
                mock_convert.return_value = "2023-01-01"

                with patch("src.gw2.tools.gw2_utils.bot_utils.get_current_date_time") as mock_time:
                    mock_time.return_value = datetime(2023, 1, 1, 12, 0, 0)

                    with patch("src.gw2.tools.gw2_utils.Gw2SessionsDal") as mock_session_dal:
                        mock_instance = mock_session_dal.return_value
                        mock_instance.update_end_session = AsyncMock(return_value=42)

                        with patch("src.gw2.tools.gw2_utils.Gw2SessionCharsDal") as mock_chars_dal:
                            mock_chars_instance = mock_chars_dal.return_value
                            mock_chars_instance.delete_end_characters = AsyncMock()

                            with patch("src.gw2.tools.gw2_utils.insert_session_char") as mock_insert_char:
                                mock_insert_char.return_value = None

                                await end_session(mock_bot, mock_member, "api-key")

                                mock_instance.update_end_session.assert_called_once()
                                call_arg = mock_instance.update_end_session.call_args[0][0]
                                assert call_arg["user_id"] == 12345
                                assert call_arg["date"] == "2023-01-01"

                                mock_chars_instance.delete_end_characters.assert_called_once_with(42)
                                mock_insert_char.assert_called_once_with(mock_bot, mock_member, "api-key", 42, "end")

    @pytest.mark.asyncio
    async def test_end_session_no_active_session(self, mock_bot, mock_member):
        """Test end_session skips insert_session_char when no active session exists."""
        session_data = {"acc_name": "TestUser.1234", "wvw_rank": 50, "gold": 1000}

        with patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats:
            mock_stats.return_value = session_data.copy()

            with patch("src.gw2.tools.gw2_utils.bot_utils.convert_datetime_to_str_short") as mock_convert:
                mock_convert.return_value = "2023-01-01"

                with patch("src.gw2.tools.gw2_utils.bot_utils.get_current_date_time") as mock_time:
                    mock_time.return_value = datetime(2023, 1, 1, 12, 0, 0)

                    with patch("src.gw2.tools.gw2_utils.Gw2SessionsDal") as mock_session_dal:
                        mock_instance = mock_session_dal.return_value
                        mock_instance.update_end_session = AsyncMock(return_value=None)

                        with patch("src.gw2.tools.gw2_utils.insert_session_char") as mock_insert_char:
                            await end_session(mock_bot, mock_member, "api-key")

                            mock_instance.update_end_session.assert_called_once()
                            mock_insert_char.assert_not_called()
                            mock_bot.log.warning.assert_called_once()


class TestGetUserStats:
    """Test cases for get_user_stats function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.mark.asyncio
    async def test_api_exception_returns_none(self, mock_bot):
        """Test that API exception returns None (lines 336-338)."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(side_effect=Exception("API Error"))

            result = await get_user_stats(mock_bot, "api-key")

            assert result is None
            mock_bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_stats_retrieval(self, mock_bot):
        """Test successful user stats retrieval with legacy wvw_rank."""
        account_data = {"name": "TestUser.1234", "wvw_rank": 50, "age": 5000000}
        wallet_data = [
            {"id": 1, "value": 50000},  # gold
            {"id": 2, "value": 100000},  # karma
            {"id": 3, "value": 25},  # laurels
        ]
        achievements_data = [
            {"id": 283, "current": 150},  # players
            {"id": 291, "current": 42},  # camps
        ]

        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(side_effect=[account_data, wallet_data, achievements_data])

            result = await get_user_stats(mock_bot, "api-key")

            assert result is not None
            assert result["acc_name"] == "TestUser.1234"
            assert result["age"] == 5000000
            assert result["wvw_rank"] == 50
            assert result["gold"] == 50000
            assert result["karma"] == 100000
            assert result["laurels"] == 25
            assert result["players"] == 150
            assert result["camps"] == 42

    @pytest.mark.asyncio
    async def test_successful_stats_retrieval_new_wvw_format(self, mock_bot):
        """Test user stats retrieval with new wvw.rank format."""
        account_data = {"name": "TestUser.1234", "wvw": {"rank": 200}}
        wallet_data = []
        achievements_data = []

        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(side_effect=[account_data, wallet_data, achievements_data])

            result = await get_user_stats(mock_bot, "api-key")

            assert result is not None
            assert result["wvw_rank"] == 200

    @pytest.mark.asyncio
    async def test_stats_with_all_wallet_items(self, mock_bot):
        """Test stats with all wallet items populated."""
        account_data = {"name": "TestUser.1234", "wvw_rank": 100}
        wallet_data = [
            {"id": 1, "value": 10000},
            {"id": 2, "value": 20000},
            {"id": 3, "value": 30},
            {"id": 15, "value": 400},
            {"id": 16, "value": 50},
            {"id": 26, "value": 60},
            {"id": 31, "value": 70},
            {"id": 36, "value": 80},
            {"id": 23, "value": 150},  # spirit_shards
            {"id": 45, "value": 2000},  # volatile_magic
        ]
        achievements_data = []

        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(side_effect=[account_data, wallet_data, achievements_data])

            result = await get_user_stats(mock_bot, "api-key")

            assert result["gold"] == 10000
            assert result["karma"] == 20000
            assert result["laurels"] == 30
            assert result["badges_honor"] == 400
            assert result["guild_commendations"] == 50
            assert result["wvw_tickets"] == 60
            assert result["proof_heroics"] == 70
            assert result["test_heroics"] == 80
            assert result["spirit_shards"] == 150
            assert result["volatile_magic"] == 2000


class TestUpdateWalletStats:
    """Test cases for _update_wallet_stats function."""

    def _make_user_stats(self):
        """Create a user stats dict with all wallet keys initialized to 0."""
        stats = {}
        for key in WALLET_MAPPING.values():
            stats[key] = 0
        return stats

    def test_updates_known_wallet_ids(self):
        """Test that known wallet IDs update stats."""
        user_stats = self._make_user_stats()
        wallet_data = [
            {"id": 1, "value": 50000},
            {"id": 2, "value": 100000},
            {"id": 3, "value": 25},
            {"id": 15, "value": 200},
            {"id": 16, "value": 10},
            {"id": 26, "value": 30},
            {"id": 31, "value": 15},
            {"id": 36, "value": 5},
        ]

        _update_wallet_stats(user_stats, wallet_data)

        assert user_stats["gold"] == 50000
        assert user_stats["karma"] == 100000
        assert user_stats["laurels"] == 25
        assert user_stats["badges_honor"] == 200
        assert user_stats["guild_commendations"] == 10
        assert user_stats["wvw_tickets"] == 30
        assert user_stats["proof_heroics"] == 15
        assert user_stats["test_heroics"] == 5

    def test_updates_new_wallet_ids(self):
        """Test that new wallet IDs (spirit shards, volatile magic, etc.) update stats."""
        user_stats = self._make_user_stats()
        wallet_data = [
            {"id": 23, "value": 150},  # spirit_shards
            {"id": 18, "value": 42},  # transmutation_charges
            {"id": 45, "value": 2000},  # volatile_magic
            {"id": 32, "value": 800},  # unbound_magic
            {"id": 4, "value": 400},  # gems
        ]

        _update_wallet_stats(user_stats, wallet_data)

        assert user_stats["spirit_shards"] == 150
        assert user_stats["transmutation_charges"] == 42
        assert user_stats["volatile_magic"] == 2000
        assert user_stats["unbound_magic"] == 800
        assert user_stats["gems"] == 400

    def test_ignores_unknown_wallet_ids(self):
        """Test that unknown wallet IDs are ignored."""
        user_stats = self._make_user_stats()
        wallet_data = [
            {"id": 999, "value": 50000},  # Unknown ID
            {"id": 888, "value": 30000},  # Unknown ID
        ]

        _update_wallet_stats(user_stats, wallet_data)

        # All should remain at 0
        assert user_stats["gold"] == 0
        assert user_stats["karma"] == 0

    def test_empty_wallet_data(self):
        """Test with empty wallet data."""
        user_stats = self._make_user_stats()

        _update_wallet_stats(user_stats, [])

        assert user_stats["gold"] == 0

    def test_mixed_known_and_unknown_ids(self):
        """Test with a mix of known and unknown wallet IDs."""
        user_stats = self._make_user_stats()
        wallet_data = [
            {"id": 1, "value": 10000},  # Known - gold
            {"id": 999, "value": 5000},  # Unknown
            {"id": 2, "value": 20000},  # Known - karma
        ]

        _update_wallet_stats(user_stats, wallet_data)

        assert user_stats["gold"] == 10000
        assert user_stats["karma"] == 20000


class TestUpdateAchievementStats:
    """Test cases for _update_achievement_stats function."""

    def test_updates_known_achievement_ids(self):
        """Test that known achievement IDs update stats (lines 394-408)."""
        user_stats = {
            "players": 0,
            "yaks_scorted": 0,
            "yaks": 0,
            "camps": 0,
            "castles": 0,
            "towers": 0,
            "keeps": 0,
        }
        achievements_data = [
            {"id": 283, "current": 150},
            {"id": 285, "current": 50},
            {"id": 288, "current": 30},
            {"id": 291, "current": 42},
            {"id": 294, "current": 10},
            {"id": 297, "current": 25},
            {"id": 300, "current": 15},
        ]

        _update_achievement_stats(user_stats, achievements_data)

        assert user_stats["players"] == 150
        assert user_stats["yaks_scorted"] == 50
        assert user_stats["yaks"] == 30
        assert user_stats["camps"] == 42
        assert user_stats["castles"] == 10
        assert user_stats["towers"] == 25
        assert user_stats["keeps"] == 15

    def test_ignores_unknown_achievement_ids(self):
        """Test that unknown achievement IDs are ignored."""
        user_stats = {"players": 0, "yaks_scorted": 0, "yaks": 0, "camps": 0, "castles": 0, "towers": 0, "keeps": 0}
        achievements_data = [
            {"id": 9999, "current": 100},
            {"id": 8888, "current": 50},
        ]

        _update_achievement_stats(user_stats, achievements_data)

        assert user_stats["players"] == 0
        assert user_stats["camps"] == 0

    def test_achievement_without_current(self):
        """Test achievement data without 'current' field defaults to 0."""
        user_stats = {"players": 0, "yaks_scorted": 0, "yaks": 0, "camps": 0, "castles": 0, "towers": 0, "keeps": 0}
        achievements_data = [
            {"id": 283},  # No 'current' key
        ]

        _update_achievement_stats(user_stats, achievements_data)

        assert user_stats["players"] == 0

    def test_empty_achievements_data(self):
        """Test with empty achievements data."""
        user_stats = {"players": 0, "yaks_scorted": 0, "yaks": 0, "camps": 0, "castles": 0, "towers": 0, "keeps": 0}

        _update_achievement_stats(user_stats, [])

        assert user_stats["players"] == 0


class TestInsertSessionChar:
    """Test cases for insert_session_char function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def mock_member(self):
        """Create a mock member."""
        member = MagicMock()
        member.id = 12345
        return member

    @pytest.mark.asyncio
    async def test_successful_insert(self, mock_bot, mock_member):
        """Test successful session character insert (lines 415-428)."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            characters_data = [{"name": "CharName", "level": 80}]
            mock_client.call_api = AsyncMock(return_value=characters_data)

            with patch("src.gw2.tools.gw2_utils.Gw2SessionCharsDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.insert_session_char = AsyncMock()

                await insert_session_char(mock_bot, mock_member, "api-key", 42, "start")

                mock_client.call_api.assert_called_once_with("characters", "api-key")
                mock_instance.insert_session_char.assert_called_once()

                call_args = mock_instance.insert_session_char.call_args[0]
                assert call_args[0] == mock_client  # gw2_api
                assert call_args[1] == characters_data
                insert_args = call_args[2]
                assert insert_args["api_key"] == "api-key"
                assert insert_args["session_id"] == 42
                assert insert_args["user_id"] == 12345
                assert insert_args["start"] is True
                assert insert_args["end"] is False

    @pytest.mark.asyncio
    async def test_insert_end_session_type(self, mock_bot, mock_member):
        """Test insert with end session type."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(return_value=[])

            with patch("src.gw2.tools.gw2_utils.Gw2SessionCharsDal") as mock_dal:
                mock_instance = mock_dal.return_value
                mock_instance.insert_session_char = AsyncMock()

                await insert_session_char(mock_bot, mock_member, "api-key", 42, "end")

                call_args = mock_instance.insert_session_char.call_args[0]
                insert_args = call_args[2]
                assert insert_args["start"] is False
                assert insert_args["end"] is True

    @pytest.mark.asyncio
    async def test_exception_logs_error(self, mock_bot, mock_member):
        """Test that exception is caught and logged (lines 430-431)."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(side_effect=Exception("API Error"))

            await insert_session_char(mock_bot, mock_member, "api-key", 42, "start")

            mock_bot.log.error.assert_called_once()
            assert "Error inserting start session character data" in mock_bot.log.error.call_args[0][0]


class TestGetPvpRankTitle:
    """Test cases for get_pvp_rank_title function."""

    def test_rabbit_rank_lower_bound(self):
        """Test Rabbit PvP rank at lower bound."""
        assert get_pvp_rank_title(1) == "Rabbit"

    def test_rabbit_rank_upper_bound(self):
        """Test Rabbit PvP rank at upper bound."""
        assert get_pvp_rank_title(9) == "Rabbit"

    def test_deer_rank(self):
        """Test Deer PvP rank."""
        assert get_pvp_rank_title(15) == "Deer"

    def test_dolyak_rank(self):
        """Test Dolyak PvP rank (line 500)."""
        assert get_pvp_rank_title(20) == "Dolyak"

    def test_dolyak_rank_upper(self):
        """Test Dolyak PvP rank upper bound."""
        assert get_pvp_rank_title(29) == "Dolyak"

    def test_wolf_rank(self):
        """Test Wolf PvP rank (line 502)."""
        assert get_pvp_rank_title(30) == "Wolf"

    def test_wolf_rank_upper(self):
        """Test Wolf PvP rank upper bound."""
        assert get_pvp_rank_title(39) == "Wolf"

    def test_tiger_rank(self):
        """Test Tiger PvP rank (line 504)."""
        assert get_pvp_rank_title(40) == "Tiger"

    def test_tiger_rank_upper(self):
        """Test Tiger PvP rank upper bound."""
        assert get_pvp_rank_title(49) == "Tiger"

    def test_bear_rank(self):
        """Test Bear PvP rank (line 506)."""
        assert get_pvp_rank_title(50) == "Bear"

    def test_bear_rank_upper(self):
        """Test Bear PvP rank upper bound."""
        assert get_pvp_rank_title(59) == "Bear"

    def test_shark_rank(self):
        """Test Shark PvP rank (line 508)."""
        assert get_pvp_rank_title(60) == "Shark"

    def test_shark_rank_upper(self):
        """Test Shark PvP rank upper bound."""
        assert get_pvp_rank_title(69) == "Shark"

    def test_phoenix_rank(self):
        """Test Phoenix PvP rank (line 510)."""
        assert get_pvp_rank_title(70) == "Phoenix"

    def test_phoenix_rank_upper(self):
        """Test Phoenix PvP rank upper bound."""
        assert get_pvp_rank_title(79) == "Phoenix"

    def test_dragon_rank_at_80(self):
        """Test Dragon PvP rank at minimum."""
        assert get_pvp_rank_title(80) == "Dragon"

    def test_dragon_rank_high(self):
        """Test Dragon PvP rank at high value."""
        assert get_pvp_rank_title(100) == "Dragon"

    def test_dragon_rank_very_high(self):
        """Test Dragon PvP rank at very high value."""
        assert get_pvp_rank_title(500) == "Dragon"

    def test_invalid_pvp_rank_zero(self):
        """Test invalid PvP rank zero."""
        assert get_pvp_rank_title(0) == ""

    def test_invalid_pvp_rank_negative(self):
        """Test invalid PvP rank negative."""
        assert get_pvp_rank_title(-5) == ""


class TestGetWvwRankTitle:
    """Test cases for get_wvw_rank_title function."""

    def test_get_wvw_rank_title_bronze_invader(self):
        """Test Bronze Invader rank."""
        result = get_wvw_rank_title(155)
        assert result == "Bronze Invader"

    def test_get_wvw_rank_title_silver_assaulter(self):
        """Test Silver Assaulter rank."""
        result = get_wvw_rank_title(685)
        assert result == "Silver Assaulter"

    def test_get_wvw_rank_title_gold_raider(self):
        """Test Gold Raider rank."""
        result = get_wvw_rank_title(1555)
        assert result == "Gold Raider"

    def test_get_wvw_rank_title_diamond_legend(self):
        """Test Diamond Legend rank."""
        result = get_wvw_rank_title(10000)
        assert result == "Diamond Legend"

    def test_get_wvw_rank_title_low_rank(self):
        """Test low rank without prefix."""
        result = get_wvw_rank_title(5)
        assert result == "Assaulter"

    def test_get_wvw_rank_title_invalid_rank(self):
        """Test invalid rank."""
        result = get_wvw_rank_title(0)
        assert result == ""


class TestGetWvwRankPrefix:
    """Test cases for _get_wvw_rank_prefix function."""

    def test_bronze_prefix(self):
        """Test Bronze prefix range."""
        assert _get_wvw_rank_prefix(300) == "Bronze"

    def test_silver_prefix(self):
        """Test Silver prefix range."""
        assert _get_wvw_rank_prefix(800) == "Silver"

    def test_gold_prefix(self):
        """Test Gold prefix range."""
        assert _get_wvw_rank_prefix(2000) == "Gold"

    def test_platinum_prefix(self):
        """Test Platinum prefix range."""
        assert _get_wvw_rank_prefix(3000) == "Platinum"

    def test_mithril_prefix(self):
        """Test Mithril prefix range."""
        assert _get_wvw_rank_prefix(5000) == "Mithril"

    def test_diamond_prefix(self):
        """Test Diamond prefix range."""
        assert _get_wvw_rank_prefix(7000) == "Diamond"

    def test_no_prefix(self):
        """Test rank with no prefix."""
        assert _get_wvw_rank_prefix(50) == ""


class TestFormatGold:
    """Test cases for format_gold function."""

    def test_format_gold_full_amount(self):
        """Test formatting full gold amount."""
        result = format_gold("1234567")
        assert result == "123 Gold 45 Silver 67 Copper"

    def test_format_gold_no_gold(self):
        """Test formatting with no gold."""
        result = format_gold("4567")
        assert result == "45 Silver 67 Copper"

    def test_format_gold_no_copper(self):
        """Test formatting with no copper."""
        result = format_gold("123400")
        assert result == "12 Gold 34 Silver"

    def test_format_gold_only_copper(self):
        """Test formatting with only copper."""
        result = format_gold("67")
        assert result == "67 Copper"

    def test_format_gold_zero_copper(self):
        """Test formatting with zero copper."""
        result = format_gold("00")
        assert result == ""

    def test_format_gold_empty_string(self):
        """Test formatting empty string."""
        result = format_gold("")
        assert result == ""

    def test_format_gold_short_string(self):
        """Test formatting very short string (single char)."""
        result = format_gold("5")
        assert result == ""

    def test_format_gold_only_silver_and_copper(self):
        """Test formatting with only silver and copper."""
        result = format_gold("2550")
        assert result == "25 Silver 50 Copper"

    def test_format_gold_large_amount(self):
        """Test formatting large gold amount."""
        result = format_gold("999999999")
        assert result == "99999 Gold 99 Silver 99 Copper"

    def test_format_gold_none_input(self):
        """Test formatting None input."""
        result = format_gold(None)
        assert result == ""


class TestTimeFunctions:
    """Test cases for time-related functions."""

    def test_get_time_passed(self):
        """Test get_time_passed function."""
        start = datetime(2023, 1, 1, 10, 0, 0)
        end = datetime(2023, 1, 1, 12, 30, 45)

        result = get_time_passed(start, end)

        assert result.hours == 2
        assert result.minutes == 30
        assert result.seconds == 45
        assert result.days == 0

    def test_get_time_passed_with_days(self):
        """Test get_time_passed with multiple days."""
        start = datetime(2023, 1, 1, 10, 0, 0)
        end = datetime(2023, 1, 5, 15, 30, 20)

        result = get_time_passed(start, end)

        assert result.days == 4
        assert result.hours == 5
        assert result.minutes == 30
        assert result.seconds == 20

    def test_convert_timedelta_to_obj_with_days(self):
        """Test convert_timedelta_to_obj with days."""
        delta = timedelta(days=5, hours=3, minutes=15, seconds=30)

        result = convert_timedelta_to_obj(delta)

        assert result.days == 5
        assert result.hours == 3
        assert result.minutes == 15
        assert result.seconds == 30
        assert result.timedelta == delta

    def test_convert_timedelta_to_obj_no_days(self):
        """Test convert_timedelta_to_obj without days."""
        delta = timedelta(hours=2, minutes=45, seconds=20)

        result = convert_timedelta_to_obj(delta)

        assert result.days == 0
        assert result.hours == 2
        assert result.minutes == 45
        assert result.seconds == 20

    def test_convert_timedelta_to_obj_zero(self):
        """Test convert_timedelta_to_obj with zero timedelta."""
        delta = timedelta()

        result = convert_timedelta_to_obj(delta)

        assert result.days == 0
        assert result.hours == 0
        assert result.minutes == 0
        assert result.seconds == 0

    def test_time_object_init(self):
        """Test TimeObject initialization."""
        obj = TimeObject()

        assert obj.timedelta == timedelta()
        assert obj.days == 0
        assert obj.hours == 0
        assert obj.minutes == 0
        assert obj.seconds == 0


class TestDeleteApiKey:
    """Test cases for delete_api_key function."""

    @pytest.fixture
    def mock_ctx_guild(self):
        """Create a mock context in a guild channel."""
        ctx = MagicMock()
        ctx.channel = MagicMock()
        ctx.channel.__class__ = discord.TextChannel
        ctx.message = MagicMock()
        ctx.message.delete = AsyncMock(return_value=None)
        return ctx

    @pytest.fixture
    def mock_ctx_dm(self):
        """Create a mock context in a DM channel."""
        ctx = MagicMock()
        ctx.channel = MagicMock()
        ctx.channel.__class__ = discord.DMChannel
        return ctx

    @pytest.mark.asyncio
    async def test_delete_api_key_in_guild(self, mock_ctx_guild):
        """Test deleting API key message in guild."""
        with patch("src.gw2.tools.gw2_utils.send_msg") as mock_send:
            await delete_api_key(mock_ctx_guild, message=True)

            mock_ctx_guild.message.delete.assert_called_once()
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_api_key_in_dm(self, mock_ctx_dm):
        """Test deleting API key message in DM (should not delete)."""
        await delete_api_key(mock_ctx_dm, message=True)

    @pytest.mark.asyncio
    async def test_delete_api_key_http_exception(self, mock_ctx_guild):
        """Test handling HTTP exception when deleting."""
        mock_ctx_guild.message.delete = AsyncMock(
            side_effect=discord.HTTPException(response=MagicMock(), message="Forbidden")
        )

        with patch("src.gw2.tools.gw2_utils.bot_utils.send_error_msg") as mock_error:
            await delete_api_key(mock_ctx_guild, message=True)
            mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_api_key_no_message_flag(self, mock_ctx_guild):
        """Test delete without message flag."""
        with patch("src.gw2.tools.gw2_utils.send_msg") as mock_send:
            await delete_api_key(mock_ctx_guild, message=False)

            mock_ctx_guild.message.delete.assert_called_once()
            mock_send.assert_not_called()


class TestIsPrivateMessage:
    """Test cases for is_private_message function."""

    def test_is_private_message_dm(self):
        """Test is_private_message with DM channel."""
        ctx = MagicMock()
        ctx.channel = MagicMock()
        ctx.channel.__class__ = discord.DMChannel

        result = is_private_message(ctx)
        assert result is True

    def test_is_private_message_guild(self):
        """Test is_private_message with guild channel."""
        ctx = MagicMock()
        ctx.channel = MagicMock()
        ctx.channel.__class__ = discord.TextChannel

        result = is_private_message(ctx)
        assert result is False


class TestGetWorldsIds:
    """Test cases for get_worlds_ids function."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.message = MagicMock()
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock(return_value=None)
        return ctx

    @pytest.mark.asyncio
    async def test_get_worlds_ids_success(self, mock_ctx):
        """Test successful world IDs retrieval."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(return_value=[{"id": 1001, "name": "Anvil Rock"}])

            success, results = await get_worlds_ids(mock_ctx)

            assert success is True
            assert results == [{"id": 1001, "name": "Anvil Rock"}]
            mock_ctx.message.channel.typing.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_worlds_ids_api_error(self, mock_ctx):
        """Test get_worlds_ids with API error."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(side_effect=APIConnectionError(mock_ctx.bot, "API Error"))

            with patch("src.gw2.tools.gw2_utils.bot_utils.send_error_msg") as mock_error:
                success, results = await get_worlds_ids(mock_ctx)

                assert success is False
                assert results is None
                mock_error.assert_called_once()


class TestActivityHelpers:
    """Test cases for activity helper functions."""

    def test_get_non_custom_activity_found(self):
        """Test _get_non_custom_activity when non-custom activity exists."""
        mock_activity = MagicMock()
        mock_activity.type = discord.ActivityType.playing

        mock_custom_activity = MagicMock()
        mock_custom_activity.type = discord.ActivityType.custom

        activities = [mock_custom_activity, mock_activity]

        result = _get_non_custom_activity(activities)
        assert result == mock_activity

    def test_get_non_custom_activity_not_found(self):
        """Test _get_non_custom_activity when only custom activities exist."""
        mock_custom_activity = MagicMock()
        mock_custom_activity.type = discord.ActivityType.custom

        activities = [mock_custom_activity]

        result = _get_non_custom_activity(activities)
        assert result is None

    def test_get_non_custom_activity_empty(self):
        """Test _get_non_custom_activity with empty activities."""
        result = _get_non_custom_activity([])
        assert result is None

    def test_is_gw2_activity_detected_after(self):
        """Test _is_gw2_activity_detected with GW2 in after activity."""
        mock_activity = MagicMock()
        mock_activity.name = "Guild Wars 2"

        result = _is_gw2_activity_detected(None, mock_activity)
        assert result is True

    def test_is_gw2_activity_detected_before(self):
        """Test _is_gw2_activity_detected with GW2 in before activity."""
        mock_activity = MagicMock()
        mock_activity.name = "Playing Guild Wars 2"

        result = _is_gw2_activity_detected(mock_activity, None)
        assert result is True

    def test_is_gw2_activity_detected_case_insensitive(self):
        """Test _is_gw2_activity_detected is case insensitive."""
        mock_activity = MagicMock()
        mock_activity.name = "GUILD WARS 2"

        result = _is_gw2_activity_detected(None, mock_activity)
        assert result is True

    def test_is_gw2_activity_detected_false(self):
        """Test _is_gw2_activity_detected with non-GW2 activities."""
        mock_activity = MagicMock()
        mock_activity.name = "World of Warcraft"

        result = _is_gw2_activity_detected(mock_activity, mock_activity)
        assert result is False

    def test_is_gw2_activity_detected_both_none(self):
        """Test _is_gw2_activity_detected with both None."""
        result = _is_gw2_activity_detected(None, None)
        assert result is False


class TestCreateInitialUserStats:
    """Test cases for _create_initial_user_stats function."""

    def test_creates_correct_structure(self):
        """Test that initial stats structure is correct with legacy wvw_rank."""
        account_data = {"name": "TestUser.1234", "wvw_rank": 75, "age": 5000000}

        result = _create_initial_user_stats(account_data)

        assert result["acc_name"] == "TestUser.1234"
        assert result["age"] == 5000000
        assert result["wvw_rank"] == 75
        assert result["gold"] == 0
        assert result["karma"] == 0
        assert result["laurels"] == 0
        assert result["badges_honor"] == 0
        assert result["guild_commendations"] == 0
        assert result["wvw_tickets"] == 0
        assert result["proof_heroics"] == 0
        assert result["test_heroics"] == 0
        assert result["players"] == 0
        assert result["yaks_scorted"] == 0
        assert result["yaks"] == 0
        assert result["camps"] == 0
        assert result["castles"] == 0
        assert result["towers"] == 0
        assert result["keeps"] == 0
        # New currencies
        assert result["spirit_shards"] == 0
        assert result["transmutation_charges"] == 0
        assert result["volatile_magic"] == 0
        assert result["unbound_magic"] == 0
        assert result["gems"] == 0

    def test_all_wallet_currencies_initialized(self):
        """Test that all currencies from WALLET_MAPPING are initialized to 0."""
        account_data = {"name": "TestUser.1234", "wvw_rank": 0}
        result = _create_initial_user_stats(account_data)
        for stat_name in WALLET_MAPPING.values():
            assert result[stat_name] == 0, f"{stat_name} should be initialized to 0"

    def test_age_defaults_to_zero(self):
        """Test that age defaults to 0 when not in account data."""
        account_data = {"name": "TestUser.1234", "wvw_rank": 0}
        result = _create_initial_user_stats(account_data)
        assert result["age"] == 0

    def test_new_wvw_rank_format(self):
        """Test that wvw.rank (new API format) is preferred over wvw_rank."""
        account_data = {"name": "TestUser.1234", "wvw": {"rank": 200}, "wvw_rank": 75}

        result = _create_initial_user_stats(account_data)

        assert result["wvw_rank"] == 200

    def test_fallback_to_legacy_wvw_rank(self):
        """Test fallback to wvw_rank when wvw.rank is absent."""
        account_data = {"name": "TestUser.1234", "wvw_rank": 75}

        result = _create_initial_user_stats(account_data)

        assert result["wvw_rank"] == 75

    def test_no_wvw_rank_defaults_to_zero(self):
        """Test that missing both wvw.rank and wvw_rank defaults to 0."""
        account_data = {"name": "TestUser.1234"}

        result = _create_initial_user_stats(account_data)

        assert result["wvw_rank"] == 0

    def test_wvw_rank_zero_in_new_format_falls_back(self):
        """Test that wvw.rank=0 (falsy) falls back to wvw_rank."""
        account_data = {"name": "TestUser.1234", "wvw": {"rank": 0}, "wvw_rank": 50}

        result = _create_initial_user_stats(account_data)

        # 0 is falsy, so it falls back to wvw_rank
        assert result["wvw_rank"] == 50


class TestGetWorldNamePopulationWithWR:
    """Test cases for get_world_name_population with WR team IDs."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.log = MagicMock()
        return ctx

    @pytest.mark.asyncio
    async def test_wr_team_ids_only(self, mock_ctx):
        """Test resolving only WR team IDs (no API call needed)."""
        result = await get_world_name_population(mock_ctx, "11001,12001")

        assert result is not None
        assert len(result) == 2
        assert "Team 1 (NA)" in result
        assert "Team 1 (EU)" in result

    @pytest.mark.asyncio
    async def test_mixed_legacy_and_wr_ids(self, mock_ctx):
        """Test resolving a mix of legacy world IDs and WR team IDs."""
        with patch("src.gw2.tools.gw2_utils.Gw2Client") as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(return_value=[{"id": 1001, "name": "Anvil Rock", "population": "High"}])

            result = await get_world_name_population(mock_ctx, "1001,11005")

            assert result is not None
            assert len(result) == 2
            assert result[0] == "Anvil Rock"
            assert result[1] == "Team 5 (NA)"

    @pytest.mark.asyncio
    async def test_unknown_wr_team_id(self, mock_ctx):
        """Test resolving an unknown WR team ID uses fallback name."""
        result = await get_world_name_population(mock_ctx, "11999")

        assert result is not None
        assert result[0] == "Team 11999"


class TestFormatSecondsToTime:
    """Test cases for format_seconds_to_time function."""

    def test_zero_seconds(self):
        assert format_seconds_to_time(0) == "0s"

    def test_negative_seconds(self):
        assert format_seconds_to_time(-5) == "0s"

    def test_seconds_only(self):
        assert format_seconds_to_time(45) == "45s"

    def test_minutes_and_seconds(self):
        assert format_seconds_to_time(125) == "2m 5s"

    def test_hours_minutes_seconds(self):
        assert format_seconds_to_time(9015) == "2h 30m 15s"

    def test_hours_only(self):
        assert format_seconds_to_time(7200) == "2h"

    def test_days_hours_minutes_seconds(self):
        assert format_seconds_to_time(90015) == "1d 1h 15s"

    def test_exact_day(self):
        assert format_seconds_to_time(86400) == "1d"

    def test_large_value(self):
        result = format_seconds_to_time(180000)
        assert "2d" in result

    def test_one_second(self):
        assert format_seconds_to_time(1) == "1s"

    def test_one_minute(self):
        assert format_seconds_to_time(60) == "1m"

    def test_one_hour(self):
        assert format_seconds_to_time(3600) == "1h"


class TestWalletMappingAndDisplayNames:
    """Test cases for WALLET_MAPPING and WALLET_DISPLAY_NAMES consistency."""

    def test_all_wallet_keys_have_display_names(self):
        """Every stat_name in WALLET_MAPPING should have a WALLET_DISPLAY_NAMES entry."""
        for wallet_id, stat_name in WALLET_MAPPING.items():
            assert stat_name in WALLET_DISPLAY_NAMES, (
                f"Wallet ID {wallet_id} maps to '{stat_name}' but has no display name"
            )

    def test_display_names_not_empty(self):
        """All display names should be non-empty strings."""
        for stat_name, display_name in WALLET_DISPLAY_NAMES.items():
            assert display_name, f"Display name for '{stat_name}' is empty"

    def test_gold_in_mapping(self):
        """Gold (ID 1) must be in the wallet mapping."""
        assert 1 in WALLET_MAPPING
        assert WALLET_MAPPING[1] == "gold"

    def test_known_currency_ids(self):
        """Verify well-known currency IDs are mapped correctly."""
        assert WALLET_MAPPING[2] == "karma"
        assert WALLET_MAPPING[3] == "laurels"
        assert WALLET_MAPPING[23] == "spirit_shards"
        assert WALLET_MAPPING[45] == "volatile_magic"
        assert WALLET_MAPPING[32] == "unbound_magic"
        assert WALLET_MAPPING[18] == "transmutation_charges"


class TestRetrySessionLater:
    """Test cases for _retry_session_later background retry function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def mock_member(self):
        """Create a mock member."""
        member = MagicMock()
        member.id = 12345
        member.send = AsyncMock()
        return member

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_first_bg_attempt_start(self, mock_bot, mock_member):
        """Test background retry succeeds on first attempt for start session."""
        session_data = {"acc_name": "TestUser.1234", "wvw_rank": 50}

        with (
            patch("src.gw2.tools.gw2_utils.asyncio.sleep") as mock_sleep,
            patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats,
            patch("src.gw2.tools.gw2_utils._do_start_session") as mock_do_start,
            patch("src.gw2.tools.gw2_utils._gw2_settings") as mock_settings,
        ):
            mock_settings.api_session_retry_bg_delay = 60.0
            mock_settings.api_retry_max_attempts = 5
            mock_stats.return_value = session_data
            mock_do_start.return_value = None

            await _retry_session_later(mock_bot, mock_member, "api-key", "start")

            mock_sleep.assert_called_once_with(60.0)
            mock_do_start.assert_called_once_with(mock_bot, mock_member, "api-key", session_data)
            mock_member.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_first_bg_attempt_end(self, mock_bot, mock_member):
        """Test background retry succeeds on first attempt for end session."""
        session_data = {"acc_name": "TestUser.1234", "wvw_rank": 50}

        with (
            patch("src.gw2.tools.gw2_utils.asyncio.sleep") as mock_sleep,
            patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats,
            patch("src.gw2.tools.gw2_utils._do_end_session") as mock_do_end,
            patch("src.gw2.tools.gw2_utils._gw2_settings") as mock_settings,
        ):
            mock_settings.api_session_retry_bg_delay = 60.0
            mock_settings.api_retry_max_attempts = 5
            mock_stats.return_value = session_data
            mock_do_end.return_value = None

            await _retry_session_later(mock_bot, mock_member, "api-key", "end")

            mock_sleep.assert_called_once_with(60.0)
            mock_do_end.assert_called_once_with(mock_bot, mock_member, "api-key", session_data)
            mock_member.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_third_attempt(self, mock_bot, mock_member):
        """Test background retry succeeds after multiple failed attempts."""
        session_data = {"acc_name": "TestUser.1234", "wvw_rank": 50}

        with (
            patch("src.gw2.tools.gw2_utils.asyncio.sleep") as mock_sleep,
            patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats,
            patch("src.gw2.tools.gw2_utils._do_start_session") as mock_do_start,
            patch("src.gw2.tools.gw2_utils._gw2_settings") as mock_settings,
        ):
            mock_settings.api_session_retry_bg_delay = 60.0
            mock_settings.api_retry_max_attempts = 5
            mock_stats.side_effect = [None, None, session_data]
            mock_do_start.return_value = None

            await _retry_session_later(mock_bot, mock_member, "api-key", "start")

            assert mock_sleep.call_count == 3
            mock_do_start.assert_called_once_with(mock_bot, mock_member, "api-key", session_data)
            mock_member.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_sends_dm(self, mock_bot, mock_member):
        """Test DM is sent when all background retries are exhausted."""
        with (
            patch("src.gw2.tools.gw2_utils.asyncio.sleep"),
            patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats,
            patch("src.gw2.tools.gw2_utils._gw2_settings") as mock_settings,
        ):
            mock_settings.api_session_retry_bg_delay = 60.0
            mock_settings.api_retry_max_attempts = 3
            mock_stats.return_value = None

            await _retry_session_later(mock_bot, mock_member, "api-key", "start")

            mock_member.send.assert_called_once()
            sent_msg = mock_member.send.call_args[0][0]
            assert "GW2 API was unreachable" in sent_msg
            mock_bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_dm_failure_handled_gracefully(self, mock_bot, mock_member):
        """Test that DM send failure is handled gracefully when user has DMs disabled."""
        with (
            patch("src.gw2.tools.gw2_utils.asyncio.sleep"),
            patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats,
            patch("src.gw2.tools.gw2_utils._gw2_settings") as mock_settings,
        ):
            mock_settings.api_session_retry_bg_delay = 60.0
            mock_settings.api_retry_max_attempts = 2
            mock_stats.return_value = None
            mock_member.send.side_effect = discord.HTTPException(MagicMock(), "Forbidden")

            await _retry_session_later(mock_bot, mock_member, "api-key", "end")

            mock_member.send.assert_called_once()
            mock_bot.log.warning.assert_called()

    @pytest.mark.asyncio
    async def test_retry_uses_correct_delay_and_attempts(self, mock_bot, mock_member):
        """Test that retry uses configured delay and max attempts."""
        with (
            patch("src.gw2.tools.gw2_utils.asyncio.sleep") as mock_sleep,
            patch("src.gw2.tools.gw2_utils.get_user_stats") as mock_stats,
            patch("src.gw2.tools.gw2_utils._gw2_settings") as mock_settings,
        ):
            mock_settings.api_session_retry_bg_delay = 120.0
            mock_settings.api_retry_max_attempts = 2
            mock_stats.return_value = None

            await _retry_session_later(mock_bot, mock_member, "api-key", "start")

            assert mock_sleep.call_count == 2
            mock_sleep.assert_called_with(120.0)
            assert mock_stats.call_count == 2
