import pytest
from ddcDatabases import DBUtilsAsync
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from src.database.dal.gw2.gw2_session_chars_dal import Gw2SessionCharDeathsDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal
from src.database.models.gw2_models import Gw2SessionCharDeaths
from uuid import uuid4

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

USER_ID = 600
API_KEY = "TEST-API-KEY-1234"


async def test_insert_start_char_deaths(db_session, log):
    """Test inserting start char deaths via the DAL."""
    sessions_dal = Gw2SessionsDal(db_session, log)
    chars_dal = Gw2SessionCharDeathsDal(db_session, log)

    session_id = await sessions_dal.insert_start_session(
        {
            "user_id": USER_ID,
            "acc_name": "CharTest.1111",
        }
    )

    characters_data = [
        {
            "name": "TestChar",
            "profession": "Warrior",
            "deaths": 10,
        }
    ]
    await chars_dal.insert_start_char_deaths(session_id, USER_ID, characters_data)

    results = await chars_dal.get_char_deaths(USER_ID)
    assert isinstance(results, list)
    assert len(results) >= 1
    assert results[0]["start"] == 10
    assert results[0]["end"] is None


async def test_update_end_char_deaths(db_session, log):
    """Test updating end char deaths via the DAL."""
    sessions_dal = Gw2SessionsDal(db_session, log)
    chars_dal = Gw2SessionCharDeathsDal(db_session, log)

    session_id = await sessions_dal.insert_start_session(
        {
            "user_id": USER_ID,
            "acc_name": "EndTest.2222",
        }
    )

    characters_data = [
        {"name": "EndChar A", "profession": "Thief", "deaths": 3},
    ]
    await chars_dal.insert_start_char_deaths(session_id, USER_ID, characters_data)

    end_characters_data = [
        {"name": "EndChar A", "deaths": 7},
    ]
    await chars_dal.update_end_char_deaths(session_id, USER_ID, end_characters_data)

    results = await chars_dal.get_char_deaths(USER_ID)
    assert isinstance(results, list)
    assert len(results) >= 1
    char = next(c for c in results if c["name"] == "EndChar A")
    assert char["start"] == 3
    assert char["end"] == 7


async def test_get_char_deaths(db_session, log):
    sessions_dal = Gw2SessionsDal(db_session, log)

    session_id = await sessions_dal.insert_start_session(
        {
            "user_id": USER_ID,
            "acc_name": "GetChars.3333",
        }
    )

    chars_dal = Gw2SessionCharDeathsDal(db_session, log)
    characters_data = [
        {"name": "GetChar A", "profession": "Warrior", "deaths": 5},
    ]
    await chars_dal.insert_start_char_deaths(session_id, USER_ID, characters_data)

    results = await chars_dal.get_char_deaths(USER_ID)
    assert isinstance(results, list)
    assert len(results) >= 1


async def test_insert_char_stores_correct_data(db_session, log):
    sessions_dal = Gw2SessionsDal(db_session, log)

    session_id = await sessions_dal.insert_start_session(
        {
            "user_id": USER_ID,
            "acc_name": "DataCheck.4444",
        }
    )

    chars_dal = Gw2SessionCharDeathsDal(db_session, log)
    characters_data = [
        {"name": "MyWarrior", "profession": "Guardian", "deaths": 42},
    ]
    await chars_dal.insert_start_char_deaths(session_id, USER_ID, characters_data)

    stmt = select(
        Gw2SessionCharDeaths.name,
        Gw2SessionCharDeaths.profession,
        Gw2SessionCharDeaths.start,
    ).where(Gw2SessionCharDeaths.user_id == USER_ID)
    db_utils = DBUtilsAsync(db_session)
    results = await db_utils.fetchall(stmt, True)
    assert len(results) == 1
    assert results[0]["name"] == "MyWarrior"
    assert results[0]["profession"] == "Guardian"
    assert results[0]["start"] == 42


async def test_fk_constraint_requires_session(db_session, log):
    """Inserting a char with a non-existent session_id should fail with FK violation."""
    db_utils = DBUtilsAsync(db_session)
    with pytest.raises(IntegrityError):
        stmt = Gw2SessionCharDeaths(
            session_id=uuid4(),
            user_id=USER_ID,
            name="Orphan",
            profession="Mesmer",
            start=0,
            end=None,
        )
        await db_utils.insert(stmt)
