#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.cogs.bot.utils import bot_utils as utils
from src.databases.sqlite3.connection import Sqlite3
from src.databases.postgres.connection import PostgreSQL


class Databases:
    def __init__(self, bot):
        self.bot = bot
        self.database_in_use = self.bot.settings["DatabaseInUse"]

    ################################################################################
    async def check_database_connection(self):
        if self.database_in_use.lower() == "sqlite":
            sqlite3 = Sqlite3(self.bot)
            return await sqlite3.create_connection()
        elif self.database_in_use.lower() == "postgres":
            postgreSQL = PostgreSQL(self.bot)
            return await postgreSQL.create_connection()

    ################################################################################
    async def execute(self, sql):
        if self.database_in_use.lower() == "sqlite":
            sqlite3 = Sqlite3(self.bot)
            await sqlite3.executescript(sql)
        elif self.database_in_use.lower() == "postgres":
            postgreSQL = PostgreSQL(self.bot)
            await postgreSQL.execute(sql)

    ################################################################################
    async def select(self, sql):
        if self.database_in_use.lower() == "sqlite":
            sqlite3 = Sqlite3(self.bot)
            return await sqlite3.select(sql)
        elif self.database_in_use.lower() == "postgres":
            postgreSQL = PostgreSQL(self.bot)
            return await postgreSQL.select(sql)

    ################################################################################
    async def set_primary_key_type(self):
        if self.database_in_use.lower() == "sqlite":
            return "INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE"
        elif self.database_in_use.lower() == "postgres":
            return "BIGSERIAL NOT NULL PRIMARY KEY UNIQUE"
