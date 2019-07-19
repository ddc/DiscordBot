#! /usr/bin/env python3
#|*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
#|*****************************************************
# # -*- coding: utf-8 -*-

import discord
from src.cogs.bot.utils import bot_utils as utils
from src.databases.databases import Databases
################################################################################
################################################################################
################################################################################ 
class CommandsSql():
    def __init__(self, log):
        self.log = log
################################################################################
################################################################################
################################################################################                 
    async def get_all_commands(self, discord_server_id:int):
        sql = f"""SELECT commands.*,
                    users.user_name
            FROM   commands,
                    users
            WHERE  commands.discord_server_id = {discord_server_id}
                    AND users.discord_user_id = commands.discord_author_id
            ORDER BY commands.command_name ASC;"""
        databases = Databases(self.log)
        return await databases.select(sql)
################################################################################
################################################################################
################################################################################                 
    async def get_command(self, discord_server_id:int, command_name:str):
        sql = f"""SELECT * FROM commands where
            discord_server_id = {discord_server_id}
            and command_name = '{command_name}';"""
        databases = Databases(self.log)
        return await databases.select(sql)
################################################################################
################################################################################
################################################################################   
    async def insert_command(self, user:discord.User, command_name:str, text:str):
        todays_date = utils.get_todays_date_time()
        sql = f""" INSERT INTO commands (discord_server_id, discord_author_id, command_name, description, date)
            VALUES (
            {user.guild.id},
            {user.id},
            '{command_name}',
            '{text}',
            '{todays_date}');"""
        databases = Databases(self.log)
        await databases.execute(sql)
################################################################################
################################################################################
################################################################################         
    async def update_command(self, discord_server_id:int, command_name:str, description:str):
        sql = f"""UPDATE commands
            SET description = '{description}'
            WHERE discord_server_id = {discord_server_id}
            and command_name = '{command_name}';"""
        databases = Databases(self.log)
        await databases.execute(sql)
################################################################################
################################################################################
################################################################################ 
    async def delete_command(self, discord_server_id:int, command_name:str):
        sql = f"""DELETE from commands where 
            discord_server_id = {discord_server_id}
            and command_name = '{command_name}';"""
        databases = Databases(self.log)
        await databases.execute(sql)
################################################################################
################################################################################
################################################################################ 
    async def delete_all_commands(self, discord_server_id:int):
        sql = f"""DELETE from commands where
            discord_server_id = {discord_server_id};"""
        databases = Databases(self.log)
        await databases.execute(sql)
################################################################################
################################################################################
################################################################################ 
