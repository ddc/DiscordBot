# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.bot_models import Muted, Servers


class MutedDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_mute_user(self, server_id: int, user_id: int, author_id: int, reason: str = None):
        stmt = Muted(
           server_id=server_id,
           user_id=user_id,
           author_id=author_id,
           reason=reason,
        )
        await self.db_utils.add(stmt)

    async def delete_mute_user(self, server_id: int, user_id: int):
        stmt = sa.delete(Muted).where(
            Muted.user_id == user_id,
            Muted.server_id == server_id
        )
        await self.db_utils.execute(stmt)

    async def delete_all_mute_users(self, server_id: int):
        stmt = sa.delete(Muted).where(
            Muted.server_id == server_id
        )
        await self.db_utils.execute(stmt)

    async def get_server_mute_user(self, server_id: int, user_id: int):
        stmt = select(
            Muted.id,
            Muted.server_id,
            Muted.user_id,
            Muted.created_by,
            Muted.reason,
            Muted.created_at,
            Muted.updated_at,
        ).where(
            Muted.user_id == user_id,
            Muted.server_id == server_id
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_all_server_mute_users(self, server_id: int):
        stmt = select(
            Servers.id.label("server_id"),
            Servers.name.label("server_name"),
            Muted.created_by,
            Muted.user_id,
            Muted.reason,
        ).join(
            Servers, Servers.id == Muted.server_id
        ).where(
            Servers.id == server_id,
            Muted.server_id == Servers.id
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_mute_user(self, user_id: int):
        stmt = select(
            Muted.id,
            Muted.server_id,
            Muted.user_id,
            Muted.created_by,
            Muted.reason,
            Muted.created_at,
            Muted.updated_at,
            Servers.name.label("server_name"),
        ).join(
            Servers, Servers.id == Muted.server_id
        ).where(
            Muted.user_id == user_id
        )
        results = await self.db_utils.fetchall(stmt)
        return results
