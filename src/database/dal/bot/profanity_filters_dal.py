# -*- coding: utf-8 -*-
import sqlalchemy as sa
from ddcDatabases import DBUtilsAsync
from sqlalchemy.future import select
from src.database.models.bot_models import ProfanityFilters


class ProfanityFilterDal:
    def __init__(self, db_session, log):
        self.columns = [x for x in ProfanityFilters.__table__.columns]
        self.db_utils = DBUtilsAsync(db_session)
        self.log = log

    async def insert_profanity_filter_channel(self,
                                              server_id: int,
                                              channel_id: int,
                                              channel_name: str,
                                              created_by: int):
        stmt = ProfanityFilters(
           server_id=server_id,
           channel_id=channel_id,
           channel_name=channel_name,
           created_by=created_by
        )
        await self.db_utils.add(stmt)

    async def delete_profanity_filter_channel(self, channel_id: int):
        stmt = sa.delete(ProfanityFilters).where(
            ProfanityFilters.channel_id == channel_id
        )
        await self.db_utils.execute(stmt)

    async def get_all_server_profanity_filter_channels(self, server_id: int):
        stmt = select(*self.columns).where(
            ProfanityFilters.server_id == server_id
        ).order_by(ProfanityFilters.channel_name.asc())
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_profanity_filter_channel(self, channel_id: int):
        stmt = select(*self.columns).where(ProfanityFilters.channel_id == channel_id)
        results = await self.db_utils.fetchall(stmt)
        return results
