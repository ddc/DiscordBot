#! /usr/bin/env python3
#|*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
#|*****************************************************
# # -*- coding: utf-8 -*-

import sqlite3
#from _sqlite3 import Error
from src.cogs.bot.utils import constants
################################################################################
################################################################################
################################################################################ 
class Sqlite3():
    def __init__(self, log):
        self.log = log
        self.db_file = constants.database_filename
################################################################################
################################################################################
################################################################################ 
    async def create_connection(self):
        try:
            conn = sqlite3.connect(self.db_file)
        except Exception as e:
            conn = None
            msg = "sqlite3:({e.args})"
            #self.log.exception("sqlite3",exc_info=e)
            self.log.error(msg)
            print(msg)
            raise sqlite3.OperationalError(e)

        return conn
################################################################################
################################################################################
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
                self.log.exception("sqlite3",exc_info=e)
                self.log.error(f"sql:({sql})")
                raise sqlite3.OperationalError(e)
            finally:
                conn.commit()
                conn.close()
################################################################################
################################################################################
################################################################################
    async def select(self, sql):
        conn = await self.create_connection()
        if conn is not None:
            try:
                finalData = {}
                c = conn.cursor()
                c.execute(sql)
                resultSet = c.fetchall()
                columnNames = list(map(lambda x:x[0], c.description))
                for lineNumber, data in enumerate(resultSet):
                    finalData[lineNumber] = {}
                    for columnNumber, value in enumerate(data):
                        finalData[lineNumber][columnNames[columnNumber]] = value
            except Exception as e:
                self.log.exception("sqlite3",exc_info=e)
                self.log.error(f"sql:({sql})")
                raise sqlite3.OperationalError(e)
            finally:
                conn.commit()
                conn.close()
                return finalData
################################################################################
################################################################################
################################################################################
