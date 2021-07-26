# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.databases.databases import Databases
import discord


class Gw2ConfigsSql:
    def __init__(self, bot):
        self.bot = bot


    async def get_gw2_server_configs(self, discord_server_id: int):
        sql = f"SELECT * FROM gw2_configs WHERE discord_server_id = {discord_server_id};"
        databases = Databases(self.bot)
        return await databases.select(sql)


    async def insert_gw2_last_session(self, discord_server_id: int, new_status: str, role_timer: int):
        sql = f"""INSERT INTO gw2_configs (discord_server_id, last_session, role_timer)
                VALUES ({discord_server_id}, '{new_status}', {role_timer});"""
        databases = Databases(self.bot)
        await databases.execute(sql)


    async def update_gw2_last_session(self, discord_server_id: int, new_status: str):
        sql = f"""UPDATE gw2_configs
                SET last_session = '{new_status}'
                WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)


    async def insert_gw2_role_timer(self, discord_server_id: int, role_timer: int):
        sql = f"""INSERT INTO gw2_configs (discord_server_id, role_timer)
                VALUES ({discord_server_id}, '{role_timer}');"""
        databases = Databases(self.bot)
        await databases.execute(sql)


    async def update_gw2_role_timer(self, discord_server_id: int, role_timer: int):
        sql = f"""UPDATE gw2_configs
                SET role_timer = '{role_timer}'
                WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)



    async def insert_default_initial_gw2_server_configs(self, servers: discord.Guild, role_timer: int):
        databases = Databases(self.bot)
        for server in servers:
            current_server = await self.get_gw2_server_configs(server.id)
            if len(current_server) == 0:
                sql = f"""INSERT INTO gw2_configs (discord_server_id, role_timer)
                        VALUES ({server.id}, '{role_timer}');"""
                await databases.execute(sql)
