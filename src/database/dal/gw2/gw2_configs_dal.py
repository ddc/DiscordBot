# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.gw2_models import Gw2Configs


class Gw2ConfigsDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_gw2_server_configs(self, server_id: int):
        stmt = Gw2Configs(server_id=server_id)
        await self.db_utils.add(stmt)

    async def update_gw2_session_config(self, server_id: int, new_status: bool, updated_by: int):
        stmt = sa.update(Gw2Configs).where(Gw2Configs.server_id == server_id).values(
            session=new_status,
            updated_by=updated_by
        )
        await self.db_utils.execute(stmt)

    async def get_gw2_server_configs(self, server_id: int):
        columns = [x for x in Gw2Configs.__table__.columns]
        stmt = select(*columns).where(Gw2Configs.server_id == server_id)
        results = await self.db_utils.fetchall(stmt)
        return results
