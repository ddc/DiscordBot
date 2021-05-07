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


class ServersSql:
    def __init__(self, bot):
        self.bot = bot

    async def insert_default_initial_server_configs(self, servers: discord.Guild):
        databases = Databases(self.bot)
        for server in servers:
            icon_url = str(server.icon_url)
            current_server = await self.get_server_by_id(server.id)
            if len(current_server) == 0:
                sql = f"""INSERT INTO servers (discord_server_id, server_owner_id, server_name, region, icon_url)
                      VALUES (
                      {server.id},
                      {server.owner_id},
                      '{server.name.replace("'","''")}',
                      '{server.region}',
                      '{icon_url}');
                      INSERT INTO server_configs (discord_server_id) VALUES ({server.id});"""
                await databases.execute(sql)


    async def update_server_changes(self, before: discord.Guild, after: discord.Guild):
        if str(before.name) != str(after.name) \
                or str(before.region) != str(after.region) \
                or str(before.icon_url) != str(after.icon_url) \
                or str(before.owner_id) != str(after.owner_id):
            icon_url = str(after.icon_url)
            sql = f"""UPDATE servers SET
                server_name = '{after.name.replace("'","''")}',
                region = '{after.region}',
                icon_url = '{icon_url}',
                server_owner_id = {after.owner_id}
                WHERE discord_server_id = {after.id};"""
            databases = Databases(self.bot)
            await databases.execute(sql)


    async def delete_server(self, discord_server_id: int):
        sql = f"DELETE from servers where discord_server_id = {discord_server_id};"
        databases = Databases(self.bot)
        await databases.execute(sql)


    async def get_all_servers(self):
        sql = """ SELECT servers.*,
                        users.user_name as owner_name
                  FROM  servers,
                        users
                  WHERE servers.server_owner_id = users.discord_user_id
                  ORDER BY server_name ASC;"""
        databases = Databases(self.bot)
        return await databases.select(sql)


    async def get_server(self, server: discord.Guild):
        sql = f""" SELECT servers.*,
                    users.user_name as owner_name
              FROM  servers,
                    users
              WHERE servers.server_owner_id = users.discord_user_id
              and servers.discord_server_id = {server.id}
              ORDER BY server_name ASC;"""
        databases = Databases(self.bot)
        return await databases.select(sql)


    async def get_server_by_id(self, discord_server_id: int):
        sql = f""" SELECT servers.*,
                    users.user_name as owner_name
              FROM  servers,
                    users
              WHERE servers.server_owner_id = users.discord_user_id
              and servers.discord_server_id = {discord_server_id}
              ORDER BY server_name ASC;"""
        databases = Databases(self.bot)
        return await databases.select(sql)
