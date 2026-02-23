import pytest
from sqlalchemy.exc import IntegrityError
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

USER_ID = 400


def _make_key_args(user_id=USER_ID, key_name="Main Key", api_key="AAAA-BBBB-CCCC"):
    return {
        "user_id": user_id,
        "key_name": key_name,
        "gw2_acc_name": "TestAccount.1234",
        "server_name": "Anvil Rock",
        "permissions": "account,characters",
        "api_key": api_key,
    }


async def test_insert_and_get_by_key(db_session, log):
    dal = Gw2KeyDal(db_session, log)
    await dal.insert_api_key(_make_key_args())
    results = await dal.get_api_key("AAAA-BBBB-CCCC")
    assert len(results) == 1
    assert results[0]["key"] == "AAAA-BBBB-CCCC"
    assert results[0]["gw2_acc_name"] == "TestAccount.1234"


async def test_get_api_key_by_user(db_session, log):
    dal = Gw2KeyDal(db_session, log)
    await dal.insert_api_key(_make_key_args())
    results = await dal.get_api_key_by_user(USER_ID)
    assert len(results) == 1
    assert results[0]["user_id"] == USER_ID


async def test_get_api_key_by_name(db_session, log):
    dal = Gw2KeyDal(db_session, log)
    await dal.insert_api_key(_make_key_args())
    results = await dal.get_api_key_by_name("Main Key")
    assert len(results) == 1
    assert isinstance(results[0], dict)
    assert results[0]["name"] == "Main Key"


async def test_update_api_key(db_session, log):
    dal = Gw2KeyDal(db_session, log)
    await dal.insert_api_key(_make_key_args())
    update_args = _make_key_args(api_key="XXXX-YYYY-ZZZZ")
    update_args["server_name"] = "Yak's Bend"
    await dal.update_api_key(update_args)
    results = await dal.get_api_key_by_user(USER_ID)
    assert results[0]["key"] == "XXXX-YYYY-ZZZZ"
    assert results[0]["server"] == "Yak's Bend"


async def test_delete_user_api_key(db_session, log):
    dal = Gw2KeyDal(db_session, log)
    await dal.insert_api_key(_make_key_args())
    await dal.delete_user_api_key(USER_ID)
    results = await dal.get_api_key_by_user(USER_ID)
    assert len(results) == 0


async def test_unique_user_constraint(db_session, log):
    dal = Gw2KeyDal(db_session, log)
    await dal.insert_api_key(_make_key_args())
    with pytest.raises(IntegrityError):
        await dal.insert_api_key(_make_key_args(api_key="DIFFERENT-KEY"))


async def test_get_api_key_returns_empty_for_missing(db_session, log):
    dal = Gw2KeyDal(db_session, log)
    results = await dal.get_api_key("NONEXISTENT")
    assert len(results) == 0
