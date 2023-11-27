# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.models.bot_models import Blacklist, Servers
from src.database.db_utils import DBUtils


class BlacklistDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_blacklisted_user(self, server_id: int, user_id: int, author_id: int, reason: str = None):
        stmt = Blacklist(
           server_id=server_id,
           user_id=user_id,
           author_id=author_id,
           reason=reason,
        )
        await self.db_utils.add(stmt)

    async def delete_blacklisted_user(self, server_id: int, user_id: int):
        stmt = sa.delete(Blacklist).where(
            Blacklist.user_id == user_id,
            Blacklist.server_id == server_id
        )
        await self.db_utils.execute(stmt)

    async def delete_all_server_blacklisted_users(self, server_id: int):
        stmt = sa.delete(Blacklist).where(Blacklist.server_id == server_id)
        await self.db_utils.execute(stmt)

    async def get_server_blacklisted_user(self, server_id: int, user_id: int):
        stmt = select(
            Blacklist.id,
            Blacklist.server_id,
            Blacklist.user_id,
            Blacklist.created_by,
            Blacklist.reason,
            Blacklist.created_at,
            Blacklist.updated_at,
        ).where(
            Blacklist.user_id == user_id,
            Blacklist.server_id == server_id
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_all_server_blacklisted_users(self, server_id: int):
        stmt = select(
            Servers.id.label("server_id"),
            Servers.name.label("server_name"),
            Blacklist.created_by,
            Blacklist.user_id,
            Blacklist.reason,
        ).join(
            Servers, Servers.id == Blacklist.server_id
        ).where(
            Servers.id == server_id,
            Blacklist.server_id == Servers.id
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_blacklisted_user(self, user_id: int):
        stmt = select(
            Blacklist.id,
            Blacklist.server_id,
            Blacklist.user_id,
            Blacklist.created_by,
            Blacklist.reason,
            Blacklist.created_at,
            Blacklist.updated_at,
            Servers.name.label("server_name"),
        ).join(
            Servers, Servers.id == Blacklist.server_id
        ).where(
            Blacklist.user_id == user_id
        )
        results = await self.db_utils.fetchall(stmt)
        return results
