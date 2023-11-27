# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.gw2_models import Gw2Keys


class Gw2KeyDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_api_key(self, insertObject: object):
        stmt = Gw2Keys(
           server_id=insertObject.server_id,
           user_id=insertObject.user_id,
           gw2_acc_name=insertObject.gw2_acc_name,
           server_name=insertObject.server_name,
           key_name=insertObject.key_name,
           permissions=insertObject.permissions,
           key=insertObject.key,
        )
        await self.db_utils.add(stmt)

    async def get_api_key(self, server_id: int, key: str):
        stmt = select(
            Gw2Keys.id,
            Gw2Keys.server_id,
            Gw2Keys.user_id,
            Gw2Keys.name,
            Gw2Keys.gw2_acc_name,
            Gw2Keys.server_name,
            Gw2Keys.permissions,
            Gw2Keys.key,
            Gw2Keys.created_at,
            Gw2Keys.updated_at,
        ).where(
            Gw2Keys.server_id == server_id,
            Gw2Keys.key == key,
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_server_user_api_key(self, server_id: int, user_id: int):
        stmt = select(
            Gw2Keys.id,
            Gw2Keys.server_id,
            Gw2Keys.user_id,
            Gw2Keys.name,
            Gw2Keys.gw2_acc_name,
            Gw2Keys.server_name,
            Gw2Keys.permissions,
            Gw2Keys.key,
            Gw2Keys.created_at,
            Gw2Keys.updated_at,
        ).where(
            Gw2Keys.server_id == server_id,
            Gw2Keys.user_id == user_id,
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_all_user_api_key(self, user_id: int):
        stmt = select(
            Gw2Keys.id,
            Gw2Keys.server_id,
            Gw2Keys.user_id,
            Gw2Keys.name,
            Gw2Keys.gw2_acc_name,
            Gw2Keys.server_name,
            Gw2Keys.permissions,
            Gw2Keys.key,
            Gw2Keys.created_at,
            Gw2Keys.updated_at,
        ).where(
            Gw2Keys.user_id == user_id,
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def update_api_key(self, updateObject: object):
        stmt = sa.update(Gw2Keys).where(
            Gw2Keys.server_id == updateObject.server_id,
            Gw2Keys.user_id == updateObject.user_id,
        ).values(
            gw2_acc_name=updateObject.gw2_acc_name,
            server_name=updateObject.server_name,
            key_name=updateObject.key_name,
            permissions=updateObject.permissions,
            key=updateObject.key,
        )
        await self.db_utils.execute(stmt)

    async def delete_server_user_api_key(self, server_id: int, user_id: int):
        stmt = sa.delete(Gw2Keys).where(
            Gw2Keys.server_id == server_id,
            Gw2Keys.user_id == user_id
        )
        await self.db_utils.execute(stmt)

    async def delete_all_user_api_key(self, user_id: int):
        stmt = sa.delete(Gw2Keys).where(
            Gw2Keys.user_id == user_id
        )
        await self.db_utils.execute(stmt)
