#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import asyncpg
from src.cogs.bot.utils import bot_utils as utils


class PostgreSQL:
    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def create_connection(self):
        try:
            conn = await asyncpg.connect(user=self.bot.settings["DBUsername"],
                                         password=self.bot.settings["DBPassword"],
                                         database=self.bot.settings["DBName"],
                                         port=self.bot.settings["DBPort"],
                                         host=self.bot.settings["DBHost"])
        except Exception as e:
            conn = None
            msg = f"PostgreSQL:({e.args})"
            self.bot.log.error(msg)
            print(msg)
            # self.log.exception("postgres",exc_info=e)
            # raise asyncpg.ConnectionFailureError(e)

        return conn

    ################################################################################
    async def execute(self, sql: str):
        conn = await self.create_connection()
        if conn is not None:
            try:
                await conn.execute(sql)
            except asyncpg.UniqueViolationError as e:
                condition_display_logs = ["gw2_chars_start" not in sql,
                                          "gw2_chars_end" not in sql]

                if all(condition_display_logs):
                    self.bot.log.warning(f"PostgreSQL:({e})")
                    self.bot.log.warning(f"Sql:({sql})")
            except Exception as e:
                self.bot.log.exception("PostgreSQL", exc_info=e)
                self.bot.log.error(f"Sql:({sql})")
                raise asyncpg.InvalidTransactionStateError(e)
            finally:
                await conn.close()

    ################################################################################
    async def select(self, sql: str):
        final_data = {}
        conn = await self.create_connection()
        if conn is not None:
            try:

                result_set = await conn.fetch(sql)
                for lineNumber, data in enumerate(result_set):
                    final_data[lineNumber] = dict(data)
            except Exception as e:
                self.bot.log.exception("PostgreSQL", exc_info=e)
                self.bot.log.error(f"Sql:({sql})")
            finally:
                await conn.close()
                return final_data
