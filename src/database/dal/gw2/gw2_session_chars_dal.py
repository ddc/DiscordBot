from ddcDatabases import DBUtilsAsync
from sqlalchemy import update
from sqlalchemy.future import select
from src.database.models.gw2_models import Gw2SessionCharDeaths


class Gw2SessionCharDeathsDal:
    def __init__(self, db_session, log):
        self.columns = list(Gw2SessionCharDeaths.__table__.columns.values())
        self.db_utils = DBUtilsAsync(db_session)
        self.log = log

    async def insert_start_char_deaths(self, session_id, user_id: int, characters_data: list[dict]):
        for char in characters_data:
            stmt = Gw2SessionCharDeaths(
                session_id=session_id,
                user_id=user_id,
                name=char["name"],
                profession=char["profession"],
                start=char["deaths"],
                end=None,
            )
            await self.db_utils.insert(stmt)

    async def update_end_char_deaths(self, session_id, user_id: int, characters_data: list[dict]):
        for char in characters_data:
            stmt = (
                update(Gw2SessionCharDeaths)
                .where(
                    Gw2SessionCharDeaths.session_id == session_id,
                    Gw2SessionCharDeaths.name == char["name"],
                )
                .values(end=char["deaths"])
            )
            await self.db_utils.execute(stmt)

    async def get_char_deaths(self, user_id: int):
        stmt = select(*self.columns).where(Gw2SessionCharDeaths.user_id == user_id)
        results = await self.db_utils.fetchall(stmt, True)
        return results
