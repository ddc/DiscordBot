# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-


class AlterTablesSql:
    def __init__(self, bot):
        self.bot = bot
        self.database_in_use = self.bot.settings["DatabaseInUse"]


    async def alter_sqlite_tables(self):
        if self.database_in_use.lower() in ("sqlite", "postgres"):
            pass
