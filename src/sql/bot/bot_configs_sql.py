#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.databases.databases import Databases


class BotConfigsSql:
    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def get_bot_configs(self):
        sql = """SELECT bot_configs.*, users.user_name, users.avatar_url
                FROM bot_configs, users
                where bot_configs.author_id = users.discord_user_id;"""
        databases = Databases(self.bot)
        return await databases.select(sql)

    ################################################################################
    async def get_bot_prefix(self):
        sql = """SELECT prefix FROM bot_configs;"""
        databases = Databases(self.bot)
        return await databases.select(sql)

    ################################################################################
    async def update_bot_prefix(self, prefix: str):
        sql = f"""UPDATE bot_configs SET prefix = '{prefix}';"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_bot_description(self, desc: str):
        sql = f"""UPDATE bot_configs SET description = '{desc}';"""
        databases = Databases(self.bot)
        await databases.execute(sql)
