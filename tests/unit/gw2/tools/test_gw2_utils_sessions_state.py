"""Tests for gw2_utils session-state helpers and DB-failure paths not covered elsewhere."""

import pytest
from datetime import datetime, timedelta
from src.gw2.tools import gw2_utils
from unittest.mock import AsyncMock, MagicMock, patch

MODULE = "src.gw2.tools.gw2_utils"
USER_ID = 4242


@pytest.fixture
def processing_sessions(monkeypatch):
    """Give each test its own empty _processing_sessions dict."""
    state: dict = {}
    monkeypatch.setattr(gw2_utils, "_processing_sessions", state)
    return state


@pytest.fixture
def achievement_cache(monkeypatch):
    cache: dict = {}
    monkeypatch.setattr(gw2_utils, "_achievement_cache", cache)
    return cache


@pytest.fixture
def bot():
    bot = MagicMock()
    bot.log = MagicMock()
    return bot


@pytest.fixture
def member():
    member = MagicMock()
    member.id = USER_ID
    return member


class TestIsSessionEnding:
    def test_false_when_user_not_processing(self, processing_sessions):
        assert gw2_utils.is_session_ending(USER_ID) is False

    @pytest.mark.parametrize(
        ("state", "expected"),
        [
            ({"current": "end"}, True),
            ({"current": "start", "pending": "end"}, True),
            ({"current": "start", "pending": None}, False),
            ({"current": "start"}, False),
        ],
    )
    def test_reflects_current_or_pending_end(self, processing_sessions, state, expected):
        processing_sessions[USER_ID] = state
        assert gw2_utils.is_session_ending(USER_ID) is expected


class TestGetSessionEndRemainingSeconds:
    def test_none_when_user_not_processing(self, processing_sessions):
        assert gw2_utils.get_session_end_remaining_seconds(USER_ID) is None

    def test_none_when_delay_not_started(self, processing_sessions):
        processing_sessions[USER_ID] = {"current": "end"}
        assert gw2_utils.get_session_end_remaining_seconds(USER_ID) is None

    def test_none_when_not_ending(self, processing_sessions):
        processing_sessions[USER_ID] = {"current": "start", "delay_started_at": datetime.now()}
        assert gw2_utils.get_session_end_remaining_seconds(USER_ID) is None

    def test_counts_down_from_end_delay(self, processing_sessions, monkeypatch):
        monkeypatch.setattr(gw2_utils._gw2_settings, "api_session_end_delay", 180.0)
        processing_sessions[USER_ID] = {"current": "end", "delay_started_at": datetime.now() - timedelta(seconds=60)}
        remaining = gw2_utils.get_session_end_remaining_seconds(USER_ID)
        assert 118 <= remaining <= 120

    def test_never_negative(self, processing_sessions, monkeypatch):
        monkeypatch.setattr(gw2_utils._gw2_settings, "api_session_end_delay", 180.0)
        processing_sessions[USER_ID] = {"current": "end", "delay_started_at": datetime.now() - timedelta(hours=1)}
        assert gw2_utils.get_session_end_remaining_seconds(USER_ID) == 0


class TestEndSessionDelay:
    @pytest.mark.asyncio
    async def test_records_delay_start_for_processing_user(self, processing_sessions, monkeypatch, bot, member):
        monkeypatch.setattr(gw2_utils._gw2_settings, "api_session_end_delay", 180.0)
        processing_sessions[USER_ID] = {"current": "end"}
        with (
            patch(f"{MODULE}.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            patch(f"{MODULE}.get_user_stats", new_callable=AsyncMock, return_value={"gold": 1}),
            patch(f"{MODULE}._do_end_session", new_callable=AsyncMock) as mock_do_end,
        ):
            await gw2_utils.end_session(bot, member, "key")

        assert isinstance(processing_sessions[USER_ID]["delay_started_at"], datetime)
        mock_sleep.assert_awaited_once_with(180.0)
        mock_do_end.assert_awaited_once()


class TestSessionDbFailures:
    @pytest.mark.asyncio
    async def test_start_session_db_error_skips_char_deaths(self, bot, member):
        with (
            patch(f"{MODULE}.Gw2SessionsDal") as mock_dal,
            patch(f"{MODULE}.insert_start_char_deaths", new_callable=AsyncMock) as mock_chars,
        ):
            mock_dal.return_value.insert_start_session = AsyncMock(side_effect=RuntimeError("db down"))
            await gw2_utils._do_start_session(bot, member, "key", {"gold": 1})

        mock_chars.assert_not_awaited()
        assert "db down" in bot.log.error.call_args[0][0]

    @pytest.mark.asyncio
    async def test_end_session_db_error_skips_char_deaths(self, bot, member):
        with (
            patch(f"{MODULE}.Gw2SessionsDal") as mock_dal,
            patch(f"{MODULE}.update_end_char_deaths", new_callable=AsyncMock) as mock_chars,
        ):
            mock_dal.return_value.update_end_session = AsyncMock(side_effect=RuntimeError("db down"))
            await gw2_utils._do_end_session(bot, member, "key", {"gold": 1})

        mock_chars.assert_not_awaited()
        assert "db down" in bot.log.error.call_args[0][0]


class TestAchievementBatchFailure:
    @pytest.mark.asyncio
    async def test_failed_batch_is_skipped_and_others_cached(self, achievement_cache):
        user_achievements = [{"id": i} for i in range(1, 202)]
        gw2_api = MagicMock()

        async def fake_call_api(uri):
            if "ids=201" in uri:
                raise RuntimeError("batch failed")
            return [{"id": i} for i in range(1, 201)]

        gw2_api.call_api = fake_call_api
        result = await gw2_utils._fetch_achievement_data_in_batches(gw2_api, user_achievements)

        assert len(result) == 200
        assert 201 not in achievement_cache


class TestGetWorldNamePopulationEmpty:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("world_ids", ["", " , ,"])
    async def test_returns_none_for_empty_id_list(self, world_ids):
        ctx = MagicMock()
        assert await gw2_utils.get_world_name_population(ctx, world_ids) is None
