# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import asyncpg


class PostgreSQL:
    def __init__(self, bot):
        self.bot = bot


    async def create_connection(self):
        try:
            conn = await self._get_connection()
        except asyncpg.InvalidCatalogNameError as e:
            await self.create_database(self.bot.settings["DBName"])
            conn = await self._get_connection()
        except Exception as e:
            conn = None
            msg = f"PostgreSQL:({e.args})"
            self.bot.log.error(msg)
            # print(msg)
            # self.bot.log.exception("postgres",exc_info=e)
            # raise asyncpg.ConnectionFailureError(e)
        return conn


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


    async def select(self, sql: str):
        final_data = {}
        conn = await self.create_connection()
        if conn is not None:
            try:
                result_set = await conn.fetch(sql)
                for line_number, data in enumerate(result_set):
                    final_data[line_number] = dict(data)
            except Exception as e:
                self.bot.log.exception("PostgreSQL", exc_info=e)
                self.bot.log.error(f"Sql:({sql})")
            finally:
                await conn.close()
        return final_data


    async def create_database(self, db_name: str):
        conn = await self._get_connection(db_name=False)
        sql = f"CREATE DATABASE \"{db_name}\""
        if conn is not None:
            try:
                await conn.execute(sql)
                msg = f"Database: {db_name} created"
                self.bot.log.info(msg)
                print(msg)
            except Exception as e:
                self.bot.log.exception("PostgreSQL", exc_info=e)
                self.bot.log.error(f"Sql:({sql})")
                print(str(e))
            finally:
                await conn.close()


    async def _get_connection(self, db_name=True):
        if db_name:
            conn = await asyncpg.connect(user=self.bot.settings["DBUsername"],
                                         password=self.bot.settings["DBPassword"],
                                         database=self.bot.settings["DBName"],
                                         port=self.bot.settings["DBPort"],
                                         host=self.bot.settings["DBHost"])
        else:
            conn = await asyncpg.connect(user=self.bot.settings["DBUsername"],
                                         password=self.bot.settings["DBPassword"],
                                         port=self.bot.settings["DBPort"],
                                         host=self.bot.settings["DBHost"])
        return conn
