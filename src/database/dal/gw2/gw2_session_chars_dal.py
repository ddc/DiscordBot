from ddcDatabases import DBUtilsAsync
from sqlalchemy import delete
from sqlalchemy.future import select
from src.database.models.gw2_models import Gw2SessionChars


class Gw2SessionCharsDal:
    def __init__(self, db_session, log):
        self.columns = list(Gw2SessionChars.__table__.columns.values())
        self.db_utils = DBUtilsAsync(db_session)
        self.log = log

    async def insert_session_char(self, characters_data: list[dict], insert_args: dict):
        for char in characters_data:
            stmt = Gw2SessionChars(
                session_id=insert_args["session_id"],
                user_id=insert_args["user_id"],
                name=char["name"],
                profession=char["profession"],
                deaths=char["deaths"],
                start=insert_args["start"],
                end=insert_args["end"],
            )
            await self.db_utils.insert(stmt)

    async def delete_end_characters(self, session_id: int):
        stmt = delete(Gw2SessionChars).where(
            Gw2SessionChars.session_id == session_id,
            Gw2SessionChars.end.is_(True),
        )
        await self.db_utils.execute(stmt)

    async def get_all_start_characters(self, user_id: int):
        stmt = select(*self.columns).where(Gw2SessionChars.user_id == user_id, Gw2SessionChars.start.is_(True))
        results = await self.db_utils.fetchall(stmt, True)
        return results

    async def get_all_end_characters(self, user_id: int):
        stmt = select(*self.columns).where(Gw2SessionChars.user_id == user_id, Gw2SessionChars.end.is_(True))
        results = await self.db_utils.fetchall(stmt, True)
        return results
