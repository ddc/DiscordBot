#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import discord
from src.databases.databases import Databases


class ServerConfigsSql:
    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def get_server_configs(self, discord_server_id: int):
        sql = f"SELECT * FROM server_configs where discord_server_id = {discord_server_id};"
        databases = Databases(self.bot)
        return await databases.select(sql)

    ################################################################################
    async def update_msg_on_join(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE server_configs
                SET msg_on_join = '{new_status}'
                WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_msg_on_leave(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE server_configs
          SET msg_on_leave = '{new_status}'
          WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_msg_on_server_update(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE server_configs
          SET msg_on_server_update = '{new_status}'
          WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_msg_on_member_update(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE server_configs
          SET msg_on_member_update = '{new_status}'
          WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_blacklist_admins(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE server_configs
          SET blacklist_admins = '{new_status}'
          WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_mute_admins(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE server_configs
          SET mute_admins = '{new_status}'
          WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_block_invis_members(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE server_configs
          SET block_invis_members = '{new_status}'
          WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_mention_everyone_pool_cmd(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE server_configs
          SET mention_everyone_pool_cmd = '{new_status}'
          WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_default_text_channel(self, discord_server_id: int, text_channel: str):
        sql = "UPDATE server_configs"
        if text_channel == "None":
            sql += " SET default_text_channel = Null"
        else:
            sql += f" SET default_text_channel = '{text_channel}'"
        sql += f" WHERE discord_server_id = {discord_server_id};"
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_anonymous_pool(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE server_configs
          SET anonymous_pool = '{new_status}'
          WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_bot_word_reactions(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE server_configs SET bot_word_reactions = '{new_status}'
            WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def get_user_channel_configs(self, user: discord.User, channel_id: int):
        sql = f"""SELECT users.user_name,
                        (SELECT 'Y' FROM blacklists WHERE discord_user_id = {user.id} and discord_server_id = {user.guild.id}) as blacklisted,
                        (SELECT reason FROM blacklists WHERE discord_user_id = {user.id} and discord_server_id = {user.guild.id}) as blacklisted_reason,
                        (SELECT 'Y' FROM mutes WHERE discord_user_id = {user.id} and discord_server_id = {user.guild.id}) as muted,
                        (SELECT reason FROM mutes WHERE discord_user_id = {user.id} and discord_server_id = {user.guild.id}) as muted_reason,
                        server_configs.msg_on_join,
                        server_configs.msg_on_leave,
                        server_configs.msg_on_server_update,
                        server_configs.msg_on_member_update,
                        server_configs.blacklist_admins,
                        server_configs.block_invis_members,
                        server_configs.bot_word_reactions,
                        profanity_filters.channel_name,
                        (SELECT 'Y' FROM profanity_filters where channel_id = {channel_id}) as profanity_filter
                    FROM users,
                         server_configs
                    left join profanity_filters on profanity_filters.channel_id = {channel_id}
                    WHERE users.discord_user_id = {user.id}
                          AND server_configs.discord_server_id = {user.guild.id};"""

        databases = Databases(self.bot)
        return await databases.select(sql)
