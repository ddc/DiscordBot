#! /usr/bin/env python3
#|*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
#|*****************************************************
# # -*- coding: utf-8 -*-

import asyncpg
from src.cogs.bot.utils import bot_utils as utils
################################################################################
################################################################################
################################################################################ 
class PostgreSQL():
    def __init__(self, log):
        self.log = log
        self.pg_host             = utils.get_settings("Database", "Host")
        self.pg_port             = utils.get_settings("Database", "Port")
        self.pg_dbname           = utils.get_settings("Database", "DBname")
        self.pg_username         = utils.get_settings("Database", "Username")
        self.pg_password         = utils.get_settings("Database", "Password")
################################################################################
################################################################################
################################################################################ 
    async def create_connection(self):
        try:
            conn = await asyncpg.connect(user=self.pg_username,
                                         password=self.pg_password,
                                         database=self.pg_dbname,
                                         port=self.pg_port,
                                         host=self.pg_host)
        except Exception as e:
            conn = None
            msg = f"PostgreSQL:Cannot Create Database Connection ({self.pg_host}:{self.pg_port}) [{e.message}]"
            #self.log.exception("postgres",exc_info=e)
            self.log.error(msg)
            print(msg)
            raise asyncpg.ConnectionFailureError(e)

        return conn
################################################################################
################################################################################
################################################################################
    async def execute(self, sql:str):
        conn = await self.create_connection()
        if conn is not None:
            try:
                await conn.execute(sql)
            except asyncpg.UniqueViolationError as e:
                condition_display_logs = ["gw2_chars_start" not in sql,
                                          "gw2_chars_end" not in sql]
            
                if all(condition_display_logs):
                    self.log.warning(f"PostgreSQL:({e})")
                    self.log.warning(f"Sql:({sql})")
            except Exception as e:
                self.log.exception("PostgreSQL",exc_info=e)
                self.log.error(f"Sql:({sql})")
                raise asyncpg.InvalidTransactionStateError(e)

            if conn is not None:
                await conn.close()
################################################################################
################################################################################
################################################################################
    async def select(self, sql:str):
        conn = await self.create_connection()
        if conn is not None:
            try:
                finalData = {}
                resultSet = await conn.fetch(sql)
                for lineNumber, data in enumerate(resultSet):
                    finalData[lineNumber] = dict(data)
            except Exception as e:
                self.log.exception("PostgreSQL",exc_info=e)
                self.log.error(f"Sql:({sql})")

            if conn is not None:
                await conn.close()
            return finalData
################################################################################
################################################################################
################################################################################
