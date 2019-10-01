#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.cogs.bot.utils import constants
from src.sql.bot.bot_configs_sql import BotConfigsSql
from src.sql.bot.users_sql import UsersSql
from src.databases.databases import Databases


class InitialConfigsSql:
    def __init__(self, bot):
        self.bot = bot

    async def insert_initial_bot_configs(self, bot):
        usersSql = UsersSql(self.bot)
        botConfigsSql = BotConfigsSql(self.bot)

        rs_user = await usersSql.get_user(bot.settings['author_id'])
        if len(rs_user) == 0:
            author = bot.get_user(bot.settings['author_id'])
            author_avatar_url = str(author.avatar_url)
            sql = f"""INSERT INTO users (discord_user_id, user_name, avatar_url)
                   VALUES (
                  {bot.settings['author_id']},
                  '{bot.settings['author']}',
                  '{author_avatar_url}'
                  );"""
            databases = Databases(self.bot)
            await databases.execute(sql)

        rs_config = await botConfigsSql.get_bot_configs()
        if len(rs_config) == 0:
            sql = f"""INSERT INTO bot_configs (author_id, url, description)
                   VALUES (
                  {bot.settings['author_id']},
                  '{constants.BOT_WEBPAGE_URL}',
                  '{constants.DESCRIPTION}'
                  );"""
            databases = Databases(self.bot)
            await databases.execute(sql)
