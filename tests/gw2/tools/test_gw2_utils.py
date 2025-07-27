"""Comprehensive tests for GW2 utilities module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import discord
from discord.ext import commands

from src.gw2.tools.gw2_exceptions import APIConnectionError

from src.gw2.tools.gw2_utils import (
    send_msg,
    insert_gw2_server_configs,
    calculate_user_achiev_points,
    earned_ap,
    max_ap,
    get_world_id,
    get_world_name_population,
    get_world_name,
    delete_api_key,
    is_private_message,
    get_wvw_rank_title,
    get_pvp_rank_title,
    format_gold,
    get_time_passed,
    convert_timedelta_to_obj,
    get_worlds_ids,
    TimeObject,
    _get_wvw_rank_prefix,
    _get_wvw_rank_title,
    _get_non_custom_activity,
    _is_gw2_activity_detected,
)


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
        with patch('src.gw2.tools.gw2_utils.bot_utils.send_embed') as mock_send:
            await send_msg(mock_ctx, "Test message")
            
            mock_send.assert_called_once()
            # send_embed is called with (ctx, embed, dm) as positional args
            args = mock_send.call_args[0]
            ctx, _, dm = args[0], args[1], args[2]
            
            assert ctx == mock_ctx
            assert args[1].description == "Test message"
            assert args[1].color.value == 0x123456
            assert dm is False

    @pytest.mark.asyncio
    async def test_send_msg_with_dm(self, mock_ctx):
        """Test send_msg with DM option."""
        with patch('src.gw2.tools.gw2_utils.bot_utils.send_embed') as mock_send:
            await send_msg(mock_ctx, "DM message", dm=True)
            
            mock_send.assert_called_once()
            # send_embed is called with (ctx, embed, dm) as positional args
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
        with patch('src.gw2.tools.gw2_utils.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            
            # Use AsyncMock for async functions
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=None)
            mock_instance.insert_gw2_server_configs = AsyncMock(return_value=None)
            
            await insert_gw2_server_configs(mock_bot, mock_server)
            
            mock_instance.get_gw2_server_configs.assert_called_once_with(12345)
            mock_instance.insert_gw2_server_configs.assert_called_once_with(12345)

    @pytest.mark.asyncio
    async def test_skip_insert_when_configs_exist(self, mock_bot, mock_server):
        """Test skipping insert when configs already exist."""
        with patch('src.gw2.tools.gw2_utils.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            
            # Use AsyncMock for async functions
            mock_instance.get_gw2_server_configs = AsyncMock(return_value={"existing": "config"})
            mock_instance.insert_gw2_server_configs = AsyncMock(return_value=None)
            
            await insert_gw2_server_configs(mock_bot, mock_server)
            
            mock_instance.get_gw2_server_configs.assert_called_once_with(12345)
            mock_instance.insert_gw2_server_configs.assert_not_called()


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
        return [
            {"id": 1, "current": 10, "repeated": 0},
            {"id": 2, "current": 5, "repeated": 1}
        ]

    @pytest.fixture
    def sample_account_data(self):
        """Create sample account data."""
        return {"daily_ap": 100, "monthly_ap": 50}

    @pytest.mark.asyncio
    async def test_calculate_achievement_points(self, mock_ctx, sample_user_achievements, sample_account_data):
        """Test calculating achievement points."""
        with patch('src.gw2.tools.gw2_utils.Gw2Client'):
            with patch('src.gw2.tools.gw2_utils._fetch_achievement_data_in_batches') as mock_fetch:
                mock_fetch.return_value = [
                    {"id": 1, "tiers": [{"count": 5, "points": 10}, {"count": 10, "points": 20}]},
                    {"id": 2, "tiers": [{"count": 3, "points": 5}]}
                ]
                
                with patch('src.gw2.tools.gw2_utils._calculate_earned_points') as mock_calc:
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
        achievement = {
            "tiers": [
                {"count": 5, "points": 10},
                {"count": 10, "points": 20},
                {"count": 15, "points": 30}
            ]
        }
        user_progress = {"current": 12, "repeated": 0}
        
        with patch('src.gw2.tools.gw2_utils.max_ap') as mock_max:
            mock_max.side_effect = [50, 15]  # max_ap calls
            
            result = earned_ap(achievement, user_progress)
            assert result == 30  # Points from first two tiers (10 + 20)

    def test_earned_ap_with_repeats(self):
        """Test earned_ap with repeated achievements."""
        achievement = {
            "tiers": [{"count": 5, "points": 10}]
        }
        user_progress = {"current": 6, "repeated": 2}
        
        with patch('src.gw2.tools.gw2_utils.max_ap') as mock_max:
            # max_ap is called: first with repeats param (max_possible), then without (base points)
            mock_max.side_effect = [50, 15]  # max_possible=50, base_points=15 per repeat
            
            result = earned_ap(achievement, user_progress)
            # 10 (tier) + (15 * 2 repeats) = 40, capped at 50
            assert result == 40


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

    def test_max_ap_with_tiers(self):
        """Test max_ap with achievement tiers."""
        achievement = {
            "tiers": [
                {"points": 10},
                {"points": 20},
                {"points": 30}
            ]
        }
        result = max_ap(achievement)
        assert result == 60  # Sum of all tier points


class TestGetWorldId:
    """Test cases for get_world_id function."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.mark.asyncio
    async def test_get_world_id_success(self, mock_bot):
        """Test successful world ID retrieval."""
        with patch('src.gw2.tools.gw2_utils.Gw2Client') as mock_client_class:
            mock_client = mock_client_class.return_value
            
            mock_client.call_api = AsyncMock(return_value=[
                {"id": 1001, "name": "Anvil Rock"},
                {"id": 1002, "name": "Borlis Pass"}
            ])
            
            result = await get_world_id(mock_bot, "Anvil Rock")
            assert result == 1001

    @pytest.mark.asyncio
    async def test_get_world_id_not_found(self, mock_bot):
        """Test world ID not found."""
        with patch('src.gw2.tools.gw2_utils.Gw2Client') as mock_client_class:
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
        # Ensure log.error is a regular MagicMock, not AsyncMock
        mock_bot.log.error = MagicMock()
        
        with patch('src.gw2.tools.gw2_utils.Gw2Client') as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.call_api = AsyncMock(side_effect=Exception("API Error"))
            
            result = await get_world_id(mock_bot, "Anvil Rock")
            assert result is None
            mock_bot.log.error.assert_called_once()


class TestDeleteApiKey:
    """Test cases for delete_api_key function."""

    @pytest.fixture
    def mock_ctx_guild(self):
        """Create a mock context in a guild channel."""
        ctx = MagicMock()
        ctx.channel = MagicMock()
        ctx.channel.__class__ = discord.TextChannel
        ctx.message = MagicMock()
        
        # Create proper async mock to avoid cleanup warnings
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
        with patch('src.gw2.tools.gw2_utils.send_msg') as mock_send:
            await delete_api_key(mock_ctx_guild, message=True)
            
            mock_ctx_guild.message.delete.assert_called_once()
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_api_key_in_dm(self, mock_ctx_dm):
        """Test deleting API key message in DM (should not delete)."""
        await delete_api_key(mock_ctx_dm, message=True)
        # Should not attempt to delete in DM

    @pytest.mark.asyncio
    async def test_delete_api_key_http_exception(self, mock_ctx_guild):
        """Test handling HTTP exception when deleting."""
        # Create proper async mock that raises exception to avoid cleanup warnings
        mock_ctx_guild.message.delete = AsyncMock(side_effect=discord.HTTPException(response=MagicMock(), message="Forbidden"))
        
        with patch('src.gw2.tools.gw2_utils.bot_utils.send_error_msg') as mock_error:
            await delete_api_key(mock_ctx_guild, message=True)
            mock_error.assert_called_once()


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


class TestGetPvpRankTitle:
    """Test cases for get_pvp_rank_title function."""

    def test_rabbit_rank(self):
        """Test Rabbit PvP rank."""
        result = get_pvp_rank_title(5)
        assert result == "Rabbit"

    def test_deer_rank(self):
        """Test Deer PvP rank."""
        result = get_pvp_rank_title(15)
        assert result == "Deer"

    def test_dragon_rank(self):
        """Test Dragon PvP rank."""
        result = get_pvp_rank_title(100)
        assert result == "Dragon"

    def test_invalid_pvp_rank(self):
        """Test invalid PvP rank."""
        result = get_pvp_rank_title(0)
        assert result == ""


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

    def test_format_gold_empty_string(self):
        """Test formatting empty string."""
        result = format_gold("")
        assert result == ""

    def test_format_gold_short_string(self):
        """Test formatting very short string."""
        result = format_gold("05")  # Need at least 2 chars for copper
        assert result == "05 Copper"  # Function returns copper as-is


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

    def test_convert_timedelta_to_obj_with_days(self):
        """Test convert_timedelta_to_obj with days."""
        delta = timedelta(days=5, hours=3, minutes=15, seconds=30)
        
        result = convert_timedelta_to_obj(delta)
        
        assert result.days == 5
        assert result.hours == 3
        assert result.minutes == 15
        assert result.seconds == 30

    def test_convert_timedelta_to_obj_no_days(self):
        """Test convert_timedelta_to_obj without days."""
        delta = timedelta(hours=2, minutes=45, seconds=20)
        
        result = convert_timedelta_to_obj(delta)
        
        assert result.days == 0
        assert result.hours == 2
        assert result.minutes == 45
        assert result.seconds == 20


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
        with patch('src.gw2.tools.gw2_utils.Gw2Client') as mock_client_class:
            mock_client = mock_client_class.return_value
            
            mock_client.call_api = AsyncMock(return_value=[{"id": 1001, "name": "Anvil Rock"}])
            
            success, results = await get_worlds_ids(mock_ctx)
            
            assert success is True
            assert results == [{"id": 1001, "name": "Anvil Rock"}]
            mock_ctx.message.channel.typing.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_worlds_ids_api_error(self, mock_ctx):
        """Test get_worlds_ids with API error."""
        with patch('src.gw2.tools.gw2_utils.Gw2Client') as mock_client_class:
            mock_client = mock_client_class.return_value
            
            mock_client.call_api = AsyncMock(side_effect=APIConnectionError(mock_ctx.bot, "API Error"))
            
            with patch('src.gw2.tools.gw2_utils.bot_utils.send_error_msg') as mock_error:
                success, results = await get_worlds_ids(mock_ctx)
                
                assert success is False
                assert results is None
                mock_error.assert_called_once()
                assert mock_ctx.bot.log.error.call_count == 2  # APIConnectionError logs + get_worlds_ids logs


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