import sqlalchemy as sa
from ddcDatabases import DBUtilsAsync
from sqlalchemy.future import select
from src.database.models.bot_models import BotConfigs


class BotConfigsDal:
    def __init__(self, db_session, log):
        self.columns = list(BotConfigs.__table__.columns.values())
        self.db_utils = DBUtilsAsync(db_session)
        self.log = log

    async def update_bot_prefix(self, prefix: str):
        stmt = sa.update(BotConfigs).values(prefix=prefix)
        await self.db_utils.execute(stmt)

    async def update_bot_description(self, description: str):
        stmt = sa.update(BotConfigs).values(description=description)
        await self.db_utils.execute(stmt)

    async def get_bot_configs(self):
        stmt = select(*self.columns)
        results = await self.db_utils.fetchall(stmt, True)
        return results

    async def get_bot_prefix(self):
        stmt = select(BotConfigs.prefix)
        results = await self.db_utils.fetchvalue(stmt)
        return results
