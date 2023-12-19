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

    async def insert_api_key(self, **kwargs):
        stmt = Gw2Keys(
            server_id=kwargs.get("server_id"),
            user_id=kwargs.get("user_id"),
            name=kwargs.get("key_name"),
            gw2_acc_name=kwargs.get("gw2_acc_name"),
            server=kwargs.get("server_name"),
            permissions=kwargs.get("permissions"),
            key=kwargs.get("api_key"),
        )
        await self.db_utils.add(stmt)

    async def update_api_key(self, **kwargs):
        stmt = sa.update(Gw2Keys).where(
            Gw2Keys.server_id == kwargs.get("server_id"),
            Gw2Keys.user_id == kwargs.get("user_id"),
        ).values(
            name=kwargs.get("key_name"),
            gw2_acc_name=kwargs.get("gw2_acc_name"),
            server=kwargs.get("server_name"),
            permissions=kwargs.get("permissions"),
            key=kwargs.get("api_key"),
        )
        await self.db_utils.execute(stmt)

    async def delete_server_user_api_key(self, server_id: int, user_id: int):
        stmt = sa.delete(Gw2Keys).where(
            Gw2Keys.server_id == server_id,
            Gw2Keys.user_id == user_id
        )
        await self.db_utils.execute(stmt)

    async def delete_all_user_api_key(self, user_id: int):
        stmt = sa.delete(Gw2Keys).where(Gw2Keys.user_id == user_id)
        await self.db_utils.execute(stmt)

    async def get_server_api_key(self, server_id: int, key: str):
        columns = [x for x in Gw2Keys.__table__.columns]
        stmt = select(*columns).where(
            Gw2Keys.server_id == server_id,
            Gw2Keys.key == key,
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_server_user_api_key(self, server_id: int, user_id: int):
        columns = [x for x in Gw2Keys.__table__.columns]
        stmt = select(*columns).where(
            Gw2Keys.server_id == server_id,
            Gw2Keys.user_id == user_id,
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_all_user_api_key(self, user_id: int):
        columns = [x for x in Gw2Keys.__table__.columns]
        stmt = select(*columns).where(Gw2Keys.user_id == user_id)
        results = await self.db_utils.fetchall(stmt)
        return results
