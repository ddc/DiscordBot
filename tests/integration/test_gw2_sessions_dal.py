import pytest
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

USER_ID = 500


def _make_session(user_id=USER_ID):
    return {
        "user_id": user_id,
        "acc_name": "TestGw2.5678",
        "gold": 100,
        "karma": 5000,
    }


async def test_insert_start_session_returns_id(db_session, log):
    dal = Gw2SessionsDal(db_session, log)
    session_id = await dal.insert_start_session(_make_session())
    assert session_id is not None
    assert isinstance(session_id, int)


async def test_insert_start_session_stores_jsonb(db_session, log):
    dal = Gw2SessionsDal(db_session, log)
    session_data = _make_session()
    await dal.insert_start_session(session_data)
    results = await dal.get_user_last_session(USER_ID)
    assert len(results) == 1
    assert results[0]["acc_name"] == "TestGw2.5678"
    assert results[0]["start"]["gold"] == 100
    assert results[0]["start"]["karma"] == 5000
    assert results[0]["end"] is None


async def test_update_end_session(db_session, log):
    dal = Gw2SessionsDal(db_session, log)
    start_id = await dal.insert_start_session(_make_session())
    end_data = {"user_id": USER_ID, "gold": 200, "karma": 6000}
    end_id = await dal.update_end_session(end_data)
    assert end_id == start_id
    results = await dal.get_user_last_session(USER_ID)
    assert results[0]["end"]["gold"] == 200
    assert results[0]["end"]["karma"] == 6000


async def test_update_end_session_no_session(db_session, log):
    dal = Gw2SessionsDal(db_session, log)
    end_data = {"user_id": 999999, "gold": 200}
    result = await dal.update_end_session(end_data)
    assert result is None


async def test_insert_start_session_cleans_old_data(db_session, log):
    dal = Gw2SessionsDal(db_session, log)
    first_session = _make_session()
    first_session["gold"] = 50
    await dal.insert_start_session(first_session)
    second_session = _make_session()
    second_session["gold"] = 999
    await dal.insert_start_session(second_session)
    results = await dal.get_user_last_session(USER_ID)
    assert len(results) == 1
    assert results[0]["start"]["gold"] == 999


async def test_get_user_last_session_empty(db_session, log):
    dal = Gw2SessionsDal(db_session, log)
    results = await dal.get_user_last_session(999999)
    assert len(results) == 0


async def test_jsonb_round_trip_complex_data(db_session, log):
    dal = Gw2SessionsDal(db_session, log)
    complex_session = {
        "user_id": USER_ID,
        "acc_name": "Complex.1111",
        "characters": ["Warrior", "Thief"],
        "nested": {"pvp_rank": 50, "wvw_rank": 100},
        "achievements": [1, 2, 3],
    }
    await dal.insert_start_session(complex_session)
    results = await dal.get_user_last_session(USER_ID)
    start = results[0]["start"]
    assert start["characters"] == ["Warrior", "Thief"]
    assert start["nested"]["pvp_rank"] == 50
    assert start["achievements"] == [1, 2, 3]
