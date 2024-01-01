# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.gw2_models import Gw2Sessions, Gw2SessionChars


class Gw2SessionsDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_start_session(self, user_stats: dict):
        stmt = sa.delete(Gw2Sessions).where(Gw2Sessions.user_id == user_stats["user_id"],)
        await self.db_utils.execute(stmt)

        stmt = sa.delete(Gw2SessionChars).where(Gw2SessionChars.user_id == user_stats["user_id"],)
        await self.db_utils.execute(stmt)

        stmt = Gw2Sessions(
            user_id=user_stats["user_id"],
            acc_name=user_stats["acc_name"],
            start=user_stats,
        )
        await self.db_utils.add(stmt)
        return stmt.id

    async def update_end_session(self, user_stats: dict):
        stmt = sa.update(Gw2Sessions).where(
            Gw2Sessions.user_id == user_stats["user_id"],
        ).values(
            end=user_stats
        )
        await self.db_utils.execute(stmt)

    async def get_user_last_session(self, user_id: int):
        columns = [x for x in Gw2Sessions.__table__.columns]
        stmt = select(*columns).where(Gw2Sessions.user_id == user_id)
        results = await self.db_utils.fetchall(stmt)
        return results
