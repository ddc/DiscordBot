#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.databases.databases import Databases


class Gw2RolesSql:
    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def get_all_gw2_server_roles(self, discord_server_id: int):
        sql = f"""SELECT * FROM gw2_roles
                WHERE discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        return await databases.select(sql)

    ################################################################################
    async def get_gw2_server_role(self, discord_server_id: int, role_name: str):
        sql = f"""SELECT * FROM gw2_roles 
                WHERE discord_server_id = {discord_server_id}
                AND role_name = '{role_name}';"""
        databases = Databases(self.bot)
        return await databases.select(sql)

    ################################################################################
    async def insert_gw2_server_role(self, discord_server_id: int, role_name: str):
        sql = f"""INSERT INTO gw2_roles( 
                discord_server_id,
                role_name
                )VALUES(
                {discord_server_id},
                '{role_name}'
                );"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def delete_gw2_server_roles(self, discord_server_id: int, role_name: str):
        sql = f"""DELETE from gw2_roles
                WHERE role_name = '{role_name}'
                AND discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)
