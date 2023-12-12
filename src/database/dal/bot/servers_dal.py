# -*- coding: utf-8 -*-
import discord
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.bot_models import Servers, ProfanityFilters


class ServersDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_server(self, server_id: int, name: str):
        stmt = Servers(
            id=server_id,
            name=name,
        )
        await self.db_utils.add(stmt)

    async def update_server(self, before: discord.Guild, after: discord.Guild):
        if str(before.name) != str(after.name):
            stmt = sa.update(Servers).where(Servers.id == after.id).values(
                server_name=after.name
            )
            await self.db_utils.execute(stmt)

    async def delete_server(self, server_id: str):
        stmt = (
            sa.delete(Servers)
            .where(Servers.id == server_id)
        )
        await self.db_utils.execute(stmt)

    async def update_msg_on_join(self, server_id: int, new_status: str, updated_by: int):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            msg_on_join=new_status,
            updated_by=updated_by
        )
        await self.db_utils.execute(stmt)

    async def update_msg_on_leave(self, server_id: int, new_status: str, updated_by: int):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            msg_on_leave=new_status,
            updated_by=updated_by
        )
        await self.db_utils.execute(stmt)

    async def update_msg_on_server_update(self, server_id: int, new_status: str, updated_by: int):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            msg_on_server_update=new_status,
            updated_by=updated_by
        )
        await self.db_utils.execute(stmt)

    async def update_msg_on_member_update(self, server_id: int, new_status: str, updated_by: int):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            msg_on_member_update=new_status,
            updated_by=updated_by
        )
        await self.db_utils.execute(stmt)

    async def update_block_invis_members(self, server_id: int, new_status: str, updated_by: int):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            block_invis_members=new_status,
            updated_by=updated_by
        )
        await self.db_utils.execute(stmt)

    async def update_default_text_channel(self, server_id: int, text_channel_id: int, updated_by: int):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            default_text_channel=None if text_channel_id == 0 else text_channel_id,
            updated_by=updated_by
        )
        await self.db_utils.execute(stmt)

    async def update_bot_word_reactions(self, server_id: int, new_status: str, updated_by: int):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            bot_word_reactions=new_status,
            updated_by=updated_by
        )
        await self.db_utils.execute(stmt)

    async def get_server(self, server_id=None, channel_id=None):
        columns = [x for x in Servers.__table__.columns]

        if channel_id:
            stmt = (select(*columns, ProfanityFilters.id.label("profanity_filter"))
                    .join(ProfanityFilters, ProfanityFilters.channel_id == channel_id, isouter=True))
        else:
            stmt = select(*columns)

        if server_id:
            stmt = stmt.where(Servers.id == server_id)
            stmt = stmt.order_by(Servers.name.asc())
            results = await self.db_utils.fetchone(stmt)
        else:
            stmt = stmt.order_by(Servers.name.asc())
            results = await self.db_utils.fetchall(stmt)

        return results
