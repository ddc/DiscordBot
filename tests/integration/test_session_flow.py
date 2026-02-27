"""Integration test for the full GW2 session start → end lifecycle.

Exercises start_session() and end_session() against a real PostgreSQL database
with mocked GW2 API responses to verify the full flow works end-to-end.
"""

import pytest
from src.database.dal.gw2.gw2_session_chars_dal import Gw2SessionCharDeathsDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal
from src.gw2.tools import gw2_utils
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

USER_ID = 700
API_KEY = "SESSION-FLOW-KEY-1234"

MOCK_ACCOUNT_DATA = {
    "name": "FlowTest.9999",
    "world": 1001,
    "access": ["GuildWars2"],
    "commander": False,
    "fractal_level": 50,
    "daily_ap": 3000,
    "monthly_ap": 200,
    "wvw_rank": 250,
    "age": 525600,
    "created": "2021-06-15T00:00:00.000Z",
}

MOCK_WALLET_DATA = [
    {"id": 1, "value": 100000},  # gold
    {"id": 2, "value": 50000},  # karma
    {"id": 3, "value": 10},  # laurels
    {"id": 15, "value": 200},  # badges_honor
    {"id": 16, "value": 5},  # guild_commendations
    {"id": 26, "value": 30},  # wvw_tickets
    {"id": 31, "value": 15},  # proof_heroics
    {"id": 36, "value": 3},  # test_heroics
]

MOCK_ACHIEVEMENTS_DATA = [
    {"id": 283, "current": 100},  # players
    {"id": 285, "current": 50},  # yaks_scorted
    {"id": 288, "current": 30},  # yaks
    {"id": 291, "current": 20},  # camps
    {"id": 294, "current": 5},  # castles
    {"id": 297, "current": 15},  # towers
    {"id": 300, "current": 10},  # keeps
]

MOCK_CHARACTERS_ALL = [
    {"name": "Warrior Prime", "profession": "Warrior", "deaths": 42},
    {"name": "Thief Shadow", "profession": "Thief", "deaths": 10},
]

# End-of-session data: wallet gold increased, character deaths increased
MOCK_WALLET_DATA_END = [
    {"id": 1, "value": 120000},  # gold increased
    {"id": 2, "value": 55000},  # karma increased
    {"id": 3, "value": 10},
    {"id": 15, "value": 200},
    {"id": 16, "value": 5},
    {"id": 26, "value": 30},
    {"id": 31, "value": 15},
    {"id": 36, "value": 3},
]

MOCK_ACHIEVEMENTS_DATA_END = [
    {"id": 283, "current": 105},  # players increased
    {"id": 285, "current": 50},
    {"id": 288, "current": 30},
    {"id": 291, "current": 20},
    {"id": 294, "current": 5},
    {"id": 297, "current": 15},
    {"id": 300, "current": 10},
]

MOCK_CHARACTERS_ALL_END = [
    {"name": "Warrior Prime", "profession": "Warrior", "deaths": 45},  # 3 more deaths
    {"name": "Thief Shadow", "profession": "Thief", "deaths": 12},  # 2 more deaths
]


def _mock_call_api_start(endpoint, api_key):
    """Mock call_api for start_session flow."""
    if endpoint == "account":
        return MOCK_ACCOUNT_DATA
    if endpoint == "account/wallet":
        return MOCK_WALLET_DATA
    if endpoint.startswith("account/achievements"):
        return MOCK_ACHIEVEMENTS_DATA
    if endpoint == "characters?ids=all":
        return MOCK_CHARACTERS_ALL
    raise ValueError(f"Unexpected endpoint: {endpoint}")


def _mock_call_api_end(endpoint, api_key):
    """Mock call_api for end_session flow."""
    if endpoint == "account":
        return MOCK_ACCOUNT_DATA
    if endpoint == "account/wallet":
        return MOCK_WALLET_DATA_END
    if endpoint.startswith("account/achievements"):
        return MOCK_ACHIEVEMENTS_DATA_END
    if endpoint == "characters?ids=all":
        return MOCK_CHARACTERS_ALL_END
    raise ValueError(f"Unexpected endpoint: {endpoint}")


async def test_session_start_end_lifecycle(db_session, log):
    """Full lifecycle: start_session → verify DB → end_session → verify DB."""
    mock_bot = MagicMock()
    mock_bot.db_session = db_session
    mock_bot.log = log

    mock_member = MagicMock()
    mock_member.id = USER_ID

    # ---- START SESSION ----
    mock_gw2_api_start = AsyncMock()
    mock_gw2_api_start.call_api = AsyncMock(side_effect=_mock_call_api_start)

    with patch("src.gw2.tools.gw2_utils.Gw2Client", return_value=mock_gw2_api_start):
        await gw2_utils.start_session(mock_bot, mock_member, API_KEY)

    # Verify session record was inserted
    sessions_dal = Gw2SessionsDal(db_session, log)
    sessions = await sessions_dal.get_user_last_session(USER_ID)
    assert len(sessions) == 1
    session = sessions[0]
    assert session["acc_name"] == "FlowTest.9999"
    assert session["start"]["gold"] == 100000
    assert session["start"]["karma"] == 50000
    assert session["start"]["wvw_rank"] == 250
    assert session["end"] is None  # Not ended yet

    # Verify start character deaths were inserted
    chars_dal = Gw2SessionCharDeathsDal(db_session, log)
    char_deaths = await chars_dal.get_char_deaths(USER_ID)
    assert len(char_deaths) == 2
    char_names = {c["name"] for c in char_deaths}
    assert char_names == {"Warrior Prime", "Thief Shadow"}
    warrior = next(c for c in char_deaths if c["name"] == "Warrior Prime")
    assert warrior["profession"] == "Warrior"
    assert warrior["start"] == 42
    assert warrior["end"] is None

    # ---- END SESSION ----
    mock_gw2_api_end = AsyncMock()
    mock_gw2_api_end.call_api = AsyncMock(side_effect=_mock_call_api_end)

    with patch("src.gw2.tools.gw2_utils.Gw2Client", return_value=mock_gw2_api_end):
        await gw2_utils.end_session(mock_bot, mock_member, API_KEY, skip_delay=True)

    # Verify session end JSONB was populated
    sessions = await sessions_dal.get_user_last_session(USER_ID)
    assert len(sessions) == 1
    session = sessions[0]
    assert session["end"] is not None
    assert session["end"]["gold"] == 120000
    assert session["end"]["karma"] == 55000

    # Verify end deaths were updated on the same rows
    char_deaths = await chars_dal.get_char_deaths(USER_ID)
    assert len(char_deaths) == 2
    end_warrior = next(c for c in char_deaths if c["name"] == "Warrior Prime")
    assert end_warrior["start"] == 42
    assert end_warrior["end"] == 45
    end_thief = next(c for c in char_deaths if c["name"] == "Thief Shadow")
    assert end_thief["start"] == 10
    assert end_thief["end"] == 12


async def test_end_session_without_start_is_noop(db_session, log):
    """end_session with no prior start should not crash and should log a warning."""
    mock_log = MagicMock()
    mock_bot = MagicMock()
    mock_bot.db_session = db_session
    mock_bot.log = mock_log

    mock_member = MagicMock()
    mock_member.id = 999888  # No session exists for this user

    mock_gw2_api = AsyncMock()
    mock_gw2_api.call_api = AsyncMock(side_effect=_mock_call_api_end)

    with patch("src.gw2.tools.gw2_utils.Gw2Client", return_value=mock_gw2_api):
        await gw2_utils.end_session(mock_bot, mock_member, API_KEY, skip_delay=True)

    mock_log.warning.assert_called_once()
    assert "999888" in mock_log.warning.call_args[0][0]

    # No session should exist
    sessions_dal = Gw2SessionsDal(db_session, log)
    sessions = await sessions_dal.get_user_last_session(999888)
    assert len(sessions) == 0
