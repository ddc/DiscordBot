#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import sqlite3
# from _sqlite3 import Error
from src.cogs.bot.utils import constants


class Sqlite3:
    def __init__(self, bot):
        self.bot = bot
        self.db_file = constants.database_filename

    ################################################################################
    async def create_connection(self):
        try:
            conn = sqlite3.connect(self.db_file)
        except Exception as e:
            conn = None
            msg = "sqlite3:({e.args})"
            # self.bot.log.exception("sqlite3",exc_info=e)
            self.bot.log.error(msg)
            print(msg)
            raise sqlite3.OperationalError(e)

        return conn

    ################################################################################
    async def executescript(self, sql):
        conn = await self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                sql = f"""PRAGMA foreign_keys = ON;
                      BEGIN TRANSACTION;
                      {sql}
                      COMMIT TRANSACTION;\n"""
                c.executescript(sql)
            except Exception as e:
                self.bot.log.exception("sqlite3", exc_info=e)
                self.bot.log.error(f"sql:({sql})")
                raise sqlite3.OperationalError(e)
            finally:
                conn.commit()
                conn.close()

    ################################################################################
    async def select(self, sql):
        final_data = {}
        conn = await self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute(sql)
                result_set = c.fetchall()
                column_names = list(map(lambda x: x[0], c.description))
                for line_number, data in enumerate(result_set):
                    final_data[line_number] = {}
                    for column_number, value in enumerate(data):
                        final_data[line_number][column_names[column_number]] = value
            except Exception as e:
                self.bot.log.exception("sqlite3", exc_info=e)
                self.bot.log.error(f"sql:({sql})")
                raise sqlite3.OperationalError(e)
            finally:
                conn.commit()
                conn.close()
                return final_data
