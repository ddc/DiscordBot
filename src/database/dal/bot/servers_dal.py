import discord
import sqlalchemy as sa
from ddcDatabases import DBUtilsAsync
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select
from src.database.models.bot_models import ProfanityFilters, Servers


class ServersDal:
    def __init__(self, db_session, log):
        self.columns = list(Servers.__table__.columns.values())
        self.db_utils = DBUtilsAsync(db_session)
        self.log = log

    async def insert_server(self, server_id: int, name: str):
        stmt = insert(Servers).values(
            id=server_id,
            name=name,
        )
        # On conflict, update the name in case it changed
        stmt = stmt.on_conflict_do_update(index_elements=['id'], set_={'name': name})
        await self.db_utils.execute(stmt)

    async def update_server(self, before: discord.Guild, after: discord.Guild):
        if str(before.name) != str(after.name):
            stmt = sa.update(Servers).where(Servers.id == after.id).values(server_name=after.name)
            await self.db_utils.execute(stmt)

    async def delete_server(self, server_id: int):
        stmt = sa.delete(Servers).where(Servers.id == server_id)
        await self.db_utils.execute(stmt)

    async def update_msg_on_join(self, server_id: int, new_status: bool, updated_by: int):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(msg_on_join=new_status, updated_by=updated_by)
        await self.db_utils.execute(stmt)

    async def update_msg_on_leave(self, server_id: int, new_status: bool, updated_by: int):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(msg_on_leave=new_status, updated_by=updated_by)
        await self.db_utils.execute(stmt)

    async def update_msg_on_server_update(self, server_id: int, new_status: bool, updated_by: int):
        stmt = (
            sa.update(Servers)
            .where(Servers.id == server_id)
            .values(msg_on_server_update=new_status, updated_by=updated_by)
        )
        await self.db_utils.execute(stmt)

    async def update_msg_on_member_update(self, server_id: int, new_status: bool, updated_by: int):
        stmt = (
            sa.update(Servers)
            .where(Servers.id == server_id)
            .values(msg_on_member_update=new_status, updated_by=updated_by)
        )
        await self.db_utils.execute(stmt)

    async def update_block_invis_members(self, server_id: int, new_status: bool, updated_by: int):
        stmt = (
            sa.update(Servers)
            .where(Servers.id == server_id)
            .values(block_invis_members=new_status, updated_by=updated_by)
        )
        await self.db_utils.execute(stmt)

    async def update_bot_word_reactions(self, server_id: int, new_status: bool, updated_by: int):
        stmt = (
            sa.update(Servers)
            .where(Servers.id == server_id)
            .values(bot_word_reactions=new_status, updated_by=updated_by)
        )
        await self.db_utils.execute(stmt)

    async def get_server(self, server_id=None, channel_id=None):
        if channel_id:
            stmt = select(*self.columns, ProfanityFilters.id.label("profanity_filter")).join(
                ProfanityFilters,
                ProfanityFilters.channel_id == channel_id,
                isouter=True,
            )
        else:
            stmt = select(*self.columns)

        if server_id:
            stmt = stmt.where(Servers.id == server_id)
            stmt = stmt.order_by(Servers.name.asc())
            resp = await self.db_utils.fetchall(stmt, True)
            results = resp[0] if len(resp) > 0 else None
        else:
            stmt = stmt.order_by(Servers.name.asc())
            results = await self.db_utils.fetchall(stmt, True)

        return results
