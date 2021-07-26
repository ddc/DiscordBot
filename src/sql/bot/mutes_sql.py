# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import discord
from src.cogs.bot.utils import bot_utils as BotUtils
from src.databases.databases import Databases


class MutesSql:
    def __init__(self, bot):
        self.bot = bot


    async def insert_mute_user(self, user: discord.User, author: discord.user, reason: None):
        todays_date = BotUtils.get_current_date_time_str()
        sql = f"""INSERT INTO mutes 
                    (discord_server_id,
                    discord_user_id,
                    discord_author_id,
                    date"""
        if reason is not None:
            sql += ",reason"
        sql += f""")VALUES (
                {user.guild.id},
                {user.id},
                {author.id},
                '{todays_date}'"""
        if reason is not None:
            sql += f",'{reason}'"
        sql += ");"
        databases = Databases(self.bot)
        await databases.execute(sql)


    async def delete_mute_user(self, user: discord.User):
        sql = f"""DELETE from mutes where
             discord_user_id = {user.id}
             and discord_server_id = {user.guild.id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)


    async def get_all_server_mute_users(self, discord_server_id: int):
        sql = f"""SELECT servers.discord_server_id,
                        users.discord_user_id,
                        mutes.discord_author_id,
                        servers.server_name,
                        users.user_name,
                        (SELECT users.user_name FROM users
                        WHERE users.discord_user_id = mutes.discord_author_id)
                        AS blacklist_author,
                        mutes.reason
                FROM mutes,
                    users,
                    servers
                WHERE servers.discord_server_id = {discord_server_id}
                    AND mutes.discord_server_id = servers.discord_server_id
                    AND mutes.discord_user_id = users.discord_user_id
                ORDER BY users.user_name ASC;"""
        databases = Databases(self.bot)
        return await databases.select(sql)


    async def get_server_mute_user(self, user: discord.User):
        sql = f"""SELECT * FROM mutes where
            discord_server_id = {user.guild.id}
            and discord_user_id = {user.id};"""
        databases = Databases(self.bot)
        return await databases.select(sql)


    async def delete_all_mute_users(self, discord_server_id: int):
        sql = f"""DELETE from mutes where discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)


    async def get_mute_user(self, discord_user_id: int):
        sql = f"""SELECT mutes.*,
                users.user_name,
                servers.server_name,
                (SELECT users.user_name
                       FROM users
                      WHERE users.discord_user_id = mutes.discord_author_id)
                AS author_name
            FROM mutes,
                   servers,
                   users
            WHERE mutes.discord_user_id = {discord_user_id} 
                   AND mutes.discord_server_id = servers.discord_server_id 
                  AND mutes.discord_user_id = users.discord_user_id;"""
        databases = Databases(self.bot)
        return await databases.select(sql)
