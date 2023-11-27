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
        try:
            stmt = Gw2Configs(
               server_id=server_id,
            )
            await self.db_utils.add(stmt)
        except Exception as e:
            print(e)

    async def insert_gw2_last_session(self, server_id: int, new_status: str):
        stmt = Gw2Configs(
           server_id=server_id,
           last_session=new_status,
        )
        await self.db_utils.add(stmt)

    async def get_gw2_server_configs(self, server_id: int):
        stmt = select(
            Gw2Configs.id,
            Gw2Configs.server_id,
            Gw2Configs.last_session,
            Gw2Configs.created_at,
            Gw2Configs.updated_at,
        ).where(
            Gw2Configs.server_id == server_id
        )

        results = await self.db_utils.fetchall(stmt)
        return results

    async def update_gw2_last_session(self, server_id: int, new_status: str):
        stmt = sa.update(Gw2Configs).where(Gw2Configs.server_id == server_id).values(last_session=new_status)
        await self.db_utils.execute(stmt)
