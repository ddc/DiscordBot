# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import discord
from src.databases.databases import Databases


class DiceRollsSql:
    def __init__(self, bot):
        self.bot = bot


    async def get_user_dice_rolls(self, user: discord.User, dice_size: int):
        sql = f"""SELECT * FROM dice_rolls where
            discord_server_id= {user.guild.id}
            and discord_user_id= {user.id}
            and dice_size= {dice_size};"""
        databases = Databases(self.bot)
        return await databases.select(sql)


    async def get_all_user_dice_rolls(self, discord_server_id: int, discord_user_id: int):
        sql = f"""SELECT * FROM dice_rolls where
            discord_server_id= {discord_server_id}
            and discord_user_id= {discord_user_id}
            ORDER BY dice_size ASC;"""
        databases = Databases(self.bot)
        return await databases.select(sql)


    async def get_all_server_dice_rolls(self, discord_server_id: int, dice_size: int):
        sql = f"""SELECT dice_rolls.*,
                    users.user_name
                 FROM dice_rolls,
                    users
                WHERE dice_rolls.discord_server_id = {discord_server_id}
                    AND dice_rolls.dice_size = {dice_size}
                    AND dice_rolls.discord_user_id = users.discord_user_id
                 ORDER BY roll DESC;"""
        databases = Databases(self.bot)
        return await databases.select(sql)


    async def get_server_max_dice_roll(self, discord_server_id: int, dice_size: int):
        sql = f"""SELECT
                   dice_rolls.roll as max_roll
                    ,users.user_name as username
                FROM
                    dice_rolls,
                    users 
                WHERE
                    discord_server_id = {discord_server_id} 
                    AND dice_size = {dice_size} 
                    AND dice_rolls.discord_user_id = users.discord_user_id
                ORDER BY max_roll DESC 
                limit 1;"""
        databases = Databases(self.bot)
        return await databases.select(sql)


    async def insert_user_dice_roll(self, user: discord.User, dice_size: int, roll: int):
        sql = f"""INSERT INTO dice_rolls (discord_server_id, discord_user_id, dice_size, roll)
            VALUES (
            {user.guild.id},
            {user.id},
            {dice_size},
            {roll});"""
        databases = Databases(self.bot)
        await databases.execute(sql)


    async def update_user_dice_roll(self, user: discord.User, dice_size: int, roll: int):
        sql = f"""UPDATE dice_rolls
            SET roll = {roll}
            WHERE discord_server_id = {user.guild.id}
            and discord_user_id = {user.id}
            and dice_size = {dice_size};"""
        databases = Databases(self.bot)
        await databases.execute(sql)


    async def delete_all_server_dice_rolls(self, discord_server_id: int):
        sql = f"""DELETE from dice_rolls where 
            discord_server_id = {discord_server_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)
