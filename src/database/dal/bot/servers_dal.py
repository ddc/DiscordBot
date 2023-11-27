# -*- coding: utf-8 -*-
import discord
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.bot_models import Servers


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
        stmt = sa.delete(Servers).where(Servers.id == server_id)
        await self.db_utils.execute(stmt)

    async def get_all_servers(self):
        stmt = select(
            Servers.id,
            Servers.name,
            Servers.msg_on_join,
            Servers.msg_on_leave,
            Servers.msg_on_server_update,
            Servers.msg_on_member_update,
            Servers.blacklist_admins,
            Servers.mute_admins,
            Servers.block_invis_members,
            Servers.bot_word_reactions,
            Servers.default_text_channel,
            Servers.created_at,
            Servers.updated_at,
        ).order_by(
            Servers.name.asc()
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_server_by_id(self, server_id: int):
        stmt = select(
            Servers.id,
            Servers.name,
            Servers.msg_on_join,
            Servers.msg_on_leave,
            Servers.msg_on_server_update,
            Servers.msg_on_member_update,
            Servers.blacklist_admins,
            Servers.mute_admins,
            Servers.block_invis_members,
            Servers.bot_word_reactions,
            Servers.default_text_channel,
            Servers.created_at,
            Servers.updated_at,
        ).where(
            Servers.id == server_id
        ).order_by(
            Servers.name.asc()
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def update_msg_on_join(self, server_id: int, new_status: str):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            msg_on_join=new_status
        )
        await self.db_utils.execute(stmt)

    async def update_msg_on_leave(self, server_id: int, new_status: str):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            msg_on_leave=new_status
        )
        await self.db_utils.execute(stmt)

    async def update_msg_on_server_update(self, server_id: int, new_status: str):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            msg_on_server_update=new_status
        )
        await self.db_utils.execute(stmt)

    async def update_msg_on_member_update(self, server_id: int, new_status: str):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            msg_on_member_update=new_status
        )
        await self.db_utils.execute(stmt)

    async def update_blacklist_admins(self, server_id: int, new_status: str):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            blacklist_admins=new_status
        )
        await self.db_utils.execute(stmt)

    async def update_mute_admins(self, server_id: int, new_status: str):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            mute_admins=new_status
        )
        await self.db_utils.execute(stmt)

    async def update_block_invis_members(self, server_id: int, new_status: str):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            block_invis_members=new_status
        )
        await self.db_utils.execute(stmt)

    async def update_default_text_channel(self, server_id: int, text_channel: str = None):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            default_text_channel=text_channel
        )
        await self.db_utils.execute(stmt)

    async def update_bot_word_reactions(self, server_id: int, new_status: str):
        stmt = sa.update(Servers).where(Servers.id == server_id).values(
            bot_word_reactions=new_status
        )
        await self.db_utils.execute(stmt)

    async def get_user_channel_configs(self, server_id: int, user_id: int, channel_id: int):
        stmt = f"""SELECT servers.msg_on_join,
                          servers.msg_on_leave,
                          servers.msg_on_server_update,
                          servers.msg_on_member_update,
                          servers.blacklist_admins,
                          servers.block_invis_members,
                          servers.bot_word_reactions,
                          profanity_filters.channel_name,
                          (SELECT 'Y' FROM blacklist WHERE user_id = {user_id} and server_id = {server_id}) as blacklisted,
                          (SELECT reason FROM blacklist WHERE user_id = {user_id} and server_id = {server_id}) as blacklisted_reason,
                          (SELECT 'Y' FROM muted WHERE user_id = {user_id} and server_id = {server_id}) as muted,
                          (SELECT reason FROM muted WHERE user_id = {user_id} and server_id = {server_id}) as muted_reason,
                          (SELECT 'Y' FROM profanity_filters where channel_id = {channel_id}) as profanity_filter
                    FROM servers
                    LEFT JOIN profanity_filters on profanity_filters.channel_id = {channel_id}
                    WHERE servers.id = {server_id};"""
        results = await self.db_utils.fetchall(sa.text(stmt))
        return results
