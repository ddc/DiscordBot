import sqlalchemy as sa
from ddcDatabases import DBUtilsAsync
from sqlalchemy.future import select
from src.database.models.bot_models import BotConfigs


class BotConfigsDal:
    def __init__(self, db_session, log):
        self.columns = [x for x in BotConfigs.__table__.columns]
        self.db_utils = DBUtilsAsync(db_session)
        self.log = log

    async def update_bot_prefix(self, prefix: str, updated_by: int):
        stmt = sa.update(BotConfigs).where(BotConfigs.id == 1).values(prefix=prefix, updated_by=updated_by)
        await self.db_utils.execute(stmt)

    async def update_bot_description(self, description: str, updated_by: int):
        stmt = sa.update(BotConfigs).where(BotConfigs.id == 1).values(description=description, updated_by=updated_by)
        await self.db_utils.execute(stmt)

    async def get_bot_configs(self):
        stmt = select(*self.columns)
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_bot_prefix(self):
        stmt = select(BotConfigs.prefix).where(BotConfigs.id == 1)
        results = await self.db_utils.fetchvalue(stmt)
        return results
