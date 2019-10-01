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


class ProfanityFilterSql:
    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def insert_profanity_filter_channel(self, channel: discord.TextChannel):
        sql = f"""INSERT INTO profanity_filters (channel_id, discord_server_id, channel_name)
                VALUES (
                {channel.id},
                {channel.guild.id},
                '{channel.name}'
                );\n"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def delete_profanity_filter_channel(self, channel: discord.TextChannel):
        sql = f"""DELETE from profanity_filters where channel_id = {channel.id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def get_all_server_profanity_filter_channels(self, discord_server_id: int):
        sql = f"""SELECT * FROM profanity_filters
                where discord_server_id = {discord_server_id}
                ORDER BY channel_name ASC;"""
        databases = Databases(self.bot)
        return await databases.select(sql)

    ################################################################################
    async def get_profanity_filter_channel(self, channel: discord.TextChannel):
        sql = f"""SELECT * FROM profanity_filters where channel_id = {channel.id};"""
        databases = Databases(self.bot)
        return await databases.select(sql)
