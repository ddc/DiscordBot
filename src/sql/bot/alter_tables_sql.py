#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

# from src.databases.databases import Databases
from src.cogs.bot.utils import bot_utils as utils


class AlterTablesSql:
    def __init__(self, bot):
        self.bot = bot
        self.database_in_use = self.bot.settings["database_in_use"]

    ################################################################################
    async def alter_sqlite_tables(self):
        if self.database_in_use.lower() == "sqlite":
            pass
        elif self.database_in_use.lower() == "postgresql":
            pass
