import pytest
from ddcDatabases import DBUtilsAsync
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from src.database.dal.gw2.gw2_session_chars_dal import Gw2SessionCharsDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal
from src.database.models.gw2_models import Gw2SessionChars

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

USER_ID = 600
API_KEY = "TEST-API-KEY-1234"


async def _insert_char_directly(db_session, session_id, user_id, name, profession, deaths, start=True, end=None):
    """Insert a session char directly via SQL to bypass DAL's missing `start` field."""
    db_utils = DBUtilsAsync(db_session)
    stmt = Gw2SessionChars(
        session_id=session_id,
        user_id=user_id,
        name=name,
        profession=profession,
        deaths=deaths,
        start=start,
        end=end,
    )
    await db_utils.insert(stmt)


async def test_insert_session_char_with_start_field(db_session, log):
    """The DAL's insert_session_char now correctly sets start/end booleans."""
    sessions_dal = Gw2SessionsDal(db_session, log)
    chars_dal = Gw2SessionCharsDal(db_session, log)

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
    insert_args = {
        "session_id": session_id,
        "user_id": USER_ID,
        "start": True,
        "end": False,
    }
    # Should no longer raise IntegrityError now that start/end are passed
    await chars_dal.insert_session_char(characters_data, insert_args)

    # Verify the data was inserted correctly
    results = await chars_dal.get_all_start_characters(USER_ID)
    assert isinstance(results, list)
    assert len(results) >= 1


async def test_get_all_start_characters(db_session, log):
    sessions_dal = Gw2SessionsDal(db_session, log)

    session_id = await sessions_dal.insert_start_session(
        {
            "user_id": USER_ID,
            "acc_name": "StartChars.2222",
        }
    )

    await _insert_char_directly(db_session, session_id, USER_ID, "StartChar A", "Warrior", 5, start=True)

    chars_dal = Gw2SessionCharsDal(db_session, log)
    results = await chars_dal.get_all_start_characters(USER_ID)
    assert isinstance(results, list)


async def test_get_all_end_characters(db_session, log):
    sessions_dal = Gw2SessionsDal(db_session, log)

    session_id = await sessions_dal.insert_start_session(
        {
            "user_id": USER_ID,
            "acc_name": "EndChars.3333",
        }
    )

    await _insert_char_directly(db_session, session_id, USER_ID, "EndChar A", "Thief", 3, start=False, end=True)

    chars_dal = Gw2SessionCharsDal(db_session, log)
    results = await chars_dal.get_all_end_characters(USER_ID)
    assert isinstance(results, list)


async def test_insert_char_stores_correct_data(db_session, log):
    sessions_dal = Gw2SessionsDal(db_session, log)

    session_id = await sessions_dal.insert_start_session(
        {
            "user_id": USER_ID,
            "acc_name": "DataCheck.4444",
        }
    )

    await _insert_char_directly(db_session, session_id, USER_ID, "MyWarrior", "Guardian", 42, start=True)

    stmt = select(
        Gw2SessionChars.name,
        Gw2SessionChars.profession,
        Gw2SessionChars.deaths,
    ).where(Gw2SessionChars.user_id == USER_ID)
    db_utils = DBUtilsAsync(db_session)
    results = await db_utils.fetchall(stmt, True)
    assert len(results) == 1
    assert results[0]["name"] == "MyWarrior"
    assert results[0]["profession"] == "Guardian"
    assert results[0]["deaths"] == 42


async def test_fk_constraint_requires_session(db_session, log):
    """Inserting a char with a non-existent session_id should fail with FK violation."""
    with pytest.raises(IntegrityError):
        await _insert_char_directly(db_session, 999999, USER_ID, "Orphan", "Mesmer", 0, start=True)
