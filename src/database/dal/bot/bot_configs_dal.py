# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.bot_models import BotConfigs


class BotConfigsDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def update_bot_prefix(self, prefix: str):
        stmt = sa.update(BotConfigs).where(BotConfigs.id == 1).values(prefix=prefix)
        await self.db_utils.execute(stmt)

    async def update_bot_description(self, description: str):
        stmt = sa.update(BotConfigs).where(BotConfigs.id == 1).values(description=description)
        await self.db_utils.execute(stmt)

    async def get_bot_configs(self):
        columns = [x for x in BotConfigs.__table__.columns]
        stmt = select(*columns)
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_bot_prefix(self):
        stmt = select(BotConfigs.prefix).where(BotConfigs.id == 1)
        results = await self.db_utils.fetch_value(stmt)
        return results
