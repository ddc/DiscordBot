#! /usr/bin/env python3
#|*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
#|*****************************************************
# # -*- coding: utf-8 -*-

import sys
import asyncio
import logging.handlers
import traceback
import aiohttp
import discord
from src.cogs.bot.utils import constants
from src.cogs.bot.utils import bot_utils as utils
from src.sql.bot.initial_tables_sql import InitialTablesSql
from src.sql.gw2.gw2_initial_tables_sql import Gw2InitialTablesSql
################################################################################
################################################################################
################################################################################  
class Bot():
    def __init__(self):
        pass
################################################################################
################################################################################
###############################################################################  
async def _initialize_bot(log):
    bot = await utils.init_bot(log)
    if bot.settings["token"] is None or len(bot.settings["token"]) == 0:
        bot.settings["token"] = _insert_token()        
    return bot
################################################################################
################################################################################
###############################################################################
def setup_logging():
    formatter = constants.LOG_FORMATTER
    #logging.getLogger("discord").setLevel(constants.LOG_LEVEL)
    #logging.getLogger("discord.http").setLevel(constants.LOG_LEVEL)
    logger = logging.getLogger()
    logger.setLevel(constants.LOG_LEVEL)
    
    file_hdlr = logging.handlers.RotatingFileHandler(
        filename=constants.logs_filename,
        maxBytes=10 * 1024 * 1024,
        encoding="utf-8",
        backupCount=5,
        mode='a')
    file_hdlr.setFormatter(formatter)
    logger.addHandler(file_hdlr)
    
    stderr_hdlr = logging.StreamHandler()
    stderr_hdlr.setFormatter(formatter)
    stderr_hdlr.setLevel(constants.LOG_LEVEL)
    logger.addHandler(stderr_hdlr)
    
    sys.excepthook = utils.log_uncaught_exceptions
    return logger
################################################################################
################################################################################
###############################################################################
def _insert_token():
    utils.clear_screen()
    tokenFile = open(constants.token_filename, encoding="utf-8", mode="w")
    print("Please insert your BOT TOKEN bellow:")
    token = utils.read_token()
    tokenFile.write(token)
    tokenFile.close()  
    return token
################################################################################
################################################################################
################################################################################ 
async def _set_initial_sql_tables(log):
    initialTablesSql    = InitialTablesSql(log)
    gw2InitialTablesSql = Gw2InitialTablesSql(log)
    await initialTablesSql.create_initial_sqlite_bot_tables()
    await gw2InitialTablesSql.create_gw2_sqlite_tables()
################################################################################
################################################################################
################################################################################   
async def init():
    log = setup_logging()
    conn = await utils.check_database_connection(log)
    if conn is None:
        loop.exception() 
    await _set_initial_sql_tables(log)
    bot = await _initialize_bot(log)
    bot.aiosession = aiohttp.ClientSession(loop=bot.loop)
    await utils.load_cogs(bot)
    bot.log.info("=====> INITIALIZING BOT <=====")
    print("Logging in to Discord...")
    print("Checking Database Configs...")
    token = str(bot.settings["token"])
    
    try:
        await bot.login(token)
        await bot.connect()
    except discord.LoginFailure as e:
        for errorMsg in e.args:
            if "Improper token has been passed" in errorMsg:
                open(constants.token_filename, 'w').close()
                formatted_lines = traceback.format_exc().splitlines()
                for err in formatted_lines:
                    if "discord." in err:
                        log.error(err)
                log.error(f"\n===> ERROR: Unable to login. {errorMsg}:{token}\n")
    except:
        loop.run_until_complete(bot.logout())
################################################################################
################################################################################
################################################################################ 
def init_loop():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(init())
    except Exception:
        loop.stop()
        loop.close()
        sys.exit(0)
    finally:
        loop.stop()
        loop.close()
################################################################################
################################################################################
###############################################################################
if __name__ == '__main__':
    loop = None
    init_loop()
