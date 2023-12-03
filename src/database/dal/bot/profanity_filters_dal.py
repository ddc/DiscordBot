# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.bot_models import ProfanityFilters


class ProfanityFilterDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_profanity_filter_channel(self, server_id: int, channel_id: int, channel_name: str = None):
        stmt = ProfanityFilters(
           server_id=server_id,
           channel_id=channel_id,
           channel_name=channel_name,
        )
        await self.db_utils.add(stmt)

    async def delete_profanity_filter_channel(self, channel_id: int):
        stmt = sa.delete(ProfanityFilters).where(
            ProfanityFilters.channel_id == channel_id
        )
        await self.db_utils.execute(stmt)

    async def get_all_server_profanity_filter_channels(self, server_id: int):
        columns = [x for x in ProfanityFilters.__table__.columns]
        stmt = select(*columns).where(
            ProfanityFilters.server_id == server_id
        ).order_by(ProfanityFilters.channel_name.asc())
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_profanity_filter_channel(self, channel_id: int):
        columns = [x for x in ProfanityFilters.__table__.columns]
        stmt = select(*columns).where(ProfanityFilters.channel_id == channel_id)
        results = await self.db_utils.fetchall(stmt)
        return results
