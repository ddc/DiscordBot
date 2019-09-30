#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.databases.databases import Databases


class Gw2KeySql:
    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def get_api_key(self, discord_server_id: int, key: str):
        sql = f"""SELECT * FROM gw2_Keys WHERE
                discord_server_id = {discord_server_id}
                and key = '{key}';"""
        databases = Databases(self.bot)
        return await databases.select(sql)

    ################################################################################
    async def get_server_user_api_key(self, discord_server_id: int, discord_user_id: int):
        sql = f"""SELECT * FROM gw2_Keys WHERE
                discord_server_id = {discord_server_id}
                and discord_user_id = {discord_user_id};"""
        databases = Databases(self.bot)
        return await databases.select(sql)

    ################################################################################
    async def get_all_user_api_key(self, discord_user_id: int):
        sql = f"""SELECT * FROM gw2_Keys WHERE
                discord_user_id = {discord_user_id};"""
        databases = Databases(self.bot)
        return await databases.select(sql)

    ################################################################################
    async def update_api_key(self, updateObject: object):
        sql = f"""UPDATE gw2_Keys SET 
            gw2_acc_name = '{updateObject.gw2_acc_name}',
            server_name = '{updateObject.server_name}',
            key_name = '{updateObject.key_name}',
            permissions = '{updateObject.permissions}',
            key = '{updateObject.key}'
            WHERE
            discord_server_id = {updateObject.discord_server_id}
            and discord_user_id = {updateObject.discord_user_id};
            """
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def insert_api_key(self, insertObject: object):
        sql = f"""INSERT INTO gw2_Keys
                (discord_server_id,
                discord_user_id,
                gw2_acc_name,
                server_name,
                key_name,
                permissions,
                key)
                VALUES (
                {insertObject.discord_server_id},
                {insertObject.discord_user_id},
                '{insertObject.gw2_acc_name}',
                '{insertObject.server_name}',
                '{insertObject.key_name}',
                '{insertObject.permissions}',
                '{insertObject.key}');"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def delete_server_user_api_key(self, discord_server_id: int, discord_user_id: int):
        sql = f"""DELETE from gw2_Keys where 
                discord_server_id = {discord_server_id}
                and discord_user_id = {discord_user_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def delete_all_user_api_key(self, discord_user_id: int):
        sql = f"""DELETE from gw2_Keys where 
                discord_user_id = {discord_user_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)
