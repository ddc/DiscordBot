import sqlalchemy as sa
from ddcDatabases import DBUtilsAsync
from sqlalchemy.future import select
from src.database.models.gw2_models import Gw2SessionChars, Gw2Sessions


class Gw2SessionsDal:
    def __init__(self, db_session, log):
        self.columns = list(Gw2Sessions.__table__.columns.values())
        self.db_utils = DBUtilsAsync(db_session)
        self.log = log

    async def insert_start_session(self, session: dict):
        stmt = sa.delete(Gw2SessionChars).where(
            Gw2SessionChars.user_id == session["user_id"],
        )
        await self.db_utils.execute(stmt)

        stmt = sa.delete(Gw2Sessions).where(
            Gw2Sessions.user_id == session["user_id"],
        )
        await self.db_utils.execute(stmt)

        stmt = Gw2Sessions(
            user_id=session["user_id"],
            acc_name=session["acc_name"],
            start=session,
        )
        await self.db_utils.insert(stmt)
        return stmt.id

    async def update_end_session(self, session: dict):
        results = await self.db_utils.fetchall(
            select(Gw2Sessions.id).where(Gw2Sessions.user_id == session["user_id"]),
            True,
        )
        if not results:
            return None

        stmt = (
            sa.update(Gw2Sessions)
            .where(
                Gw2Sessions.user_id == session["user_id"],
            )
            .values(end=session)
        )
        await self.db_utils.execute(stmt)
        return results[0]["id"]

    async def get_user_last_session(self, user_id: int):
        stmt = select(*self.columns).where(Gw2Sessions.user_id == user_id)
        results = await self.db_utils.fetchall(stmt, True)
        return results
