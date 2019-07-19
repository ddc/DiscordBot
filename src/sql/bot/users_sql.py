#! /usr/bin/env python3
#|*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
#|*****************************************************
# # -*- coding: utf-8 -*-

import discord
from src.databases.databases import Databases
################################################################################
################################################################################
################################################################################
class UsersSql():
    def __init__(self, log):
        self.log = log
################################################################################
################################################################################
################################################################################
    async def insert_all_server_users(self, servers:discord.Guild):
        databases = Databases(self.log)
        for server in servers:
            for user in server.members:
                #if user.bot == False:
                avatar_url = str(user.avatar_url)
                current_user = await self.get_user(user.id)
                if len(current_user) == 0:
                    sql = f"""INSERT INTO users (discord_user_id, user_name, avatar_url)
                            VALUES ({user.id}, '{user}', '{avatar_url}');"""
                    await databases.execute(sql)
################################################################################
################################################################################
###############################################################################
    async def insert_user(self, user:discord.User):
        #if user.bot == False:
        current_user = await self.get_user(user.id)
        if len(current_user) == 0:
            avatar_url = str(user.avatar_url)
            sql = f"""INSERT INTO users (discord_user_id, user_name, avatar_url)
                    VALUES ({user.id}, '{user}', '{avatar_url}');"""
            databases = Databases(self.log)
            await databases.execute(sql)       
################################################################################
################################################################################
################################################################################
    async def update_user_changes(self, before:discord.Member, user:discord.Member):       
        if str(before.name) != str(user.name)\
        or str(before.avatar_url) != str(user.avatar_url):
            avatar_url = str(user.avatar_url)
            sql = f"""UPDATE users SET
                user_name = '{user}',
                avatar_url = '{avatar_url}'
                WHERE discord_user_id = {user.id};"""
            databases = Databases(self.log)
            await databases.execute(sql)
################################################################################
################################################################################
################################################################################
    async def delete_user(self, user:discord.User):
        sql = f"DELETE from users where discord_user_id = {user.id};"  
        databases = Databases(self.log)
        await databases.execute(sql)
################################################################################
################################################################################
################################################################################
    async def get_user(self, discord_user_id:int):
        sql = f"SELECT * from users where discord_user_id = {discord_user_id};"  
        databases = Databases(self.log)
        return await databases.select(sql)
################################################################################
################################################################################
################################################################################
