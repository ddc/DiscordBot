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


class UsersSql:
    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def insert_all_server_users(self, servers: discord.Guild):
        databases = Databases(self.bot)
        for server in servers:
            for user in server.members:
                # if user.bot is False:
                current_user = await self.get_user(user.id)
                if len(current_user) == 0:
                    full_name = f"{user.display_name}#{user.discriminator}".replace("'", "''")
                    sql = f"""INSERT INTO users (discord_user_id, user_name, avatar_url)
                            VALUES ({user.id}, '{full_name}', '{user.avatar_url}');"""
                    await databases.execute(sql)

    ################################################################################
    async def insert_user(self, user: discord.User):
        # if user.bot is False:
        current_user = await self.get_user(user.id)
        if len(current_user) == 0:
            full_name = f"{user.display_name}#{user.discriminator}".replace("'", "''")
            sql = f"""INSERT INTO users (discord_user_id, user_name, avatar_url)
                    VALUES ({user.id}, '{full_name}', '{user.avatar_url}');"""
            databases = Databases(self.bot)
            await databases.execute(sql)
        ################################################################################

    async def update_user_changes(self, after: discord.Member):
        full_name = f"{after.display_name}#{after.discriminator}".replace("'", "''")
        sql = f"""UPDATE users SET
            user_name = '{full_name}',
            avatar_url = '{after.avatar_url}'
            WHERE discord_user_id = {after.id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def delete_user(self, user: discord.User):
        sql = f"DELETE from users where discord_user_id = {user.id};"
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def get_user(self, discord_user_id: int):
        sql = f"SELECT * from users where discord_user_id = {discord_user_id};"
        databases = Databases(self.bot)
        return await databases.select(sql)
