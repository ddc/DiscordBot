#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import os
import sys
import asyncio
import traceback
import aiohttp
import discord
import time
from src.cogs.bot.utils import constants
from src.cogs.bot.utils import bot_utils as BotUtils
import src.cogs.gw2.utils.gw2_constants as Gw2Constants
from discord.ext import commands
import datetime


class Bot:
    def __init__(self):
        pass


################################################################################
async def _initialize_bot(log):
    bot = await _init_bot(log)
    if bot.token is None or len(bot.token) == 0:
        bot.token = _insert_token()
    return bot


################################################################################
async def _init_bot(log):
    token = None
    if os.path.isfile(constants.TOKEN_FILENAME):
        tokenFile = open(constants.TOKEN_FILENAME, encoding="utf-8", mode="r")
        token = tokenFile.read().split('\n', 1)[0].strip('\n')
        tokenFile.close()

    bot = commands.Bot(command_prefix=constants.DEFAULT_PREFIX)
    bot.log = log
    bot.token = token
    return bot


################################################################################
def _insert_token():
    BotUtils.clear_screen()
    tokenFile = open(constants.TOKEN_FILENAME, encoding="utf-8", mode="w")
    print("Please insert your BOT TOKEN bellow:")
    token = BotUtils.read_token()
    tokenFile.write(token)
    tokenFile.close()
    return token


################################################################################
async def _set_bot_configs(bot):
    bot.uptime = datetime.datetime.now()
    bot.description = str(constants.DESCRIPTION)
    bot.help_command = commands.DefaultHelpCommand(dm_help=True)
    bot.settings = BotUtils.get_all_ini_file_settings(constants.SETTINGS_FILENAME)
    bot.settings["bot_webpage_url"] = str(constants.BOT_WEBPAGE_URL)
    bot.settings["version"] = constants.VERSION
    bot.settings["full_db_name"] = BotUtils.get_full_db_name(bot)
    bot.settings["EmbedOwnerColor"] = BotUtils.get_color_settings(bot.settings["EmbedOwnerColor"])
    bot.settings["EmbedColor"] = BotUtils.get_color_settings(bot.settings["EmbedColor"])


################################################################################
async def _set_other_cogs_configs(bot):
    bot.gw2_settings = BotUtils.get_all_ini_file_settings(Gw2Constants.GW2_SETTINGS_FILENAME)
    bot.gw2_settings["EmbedColor"] = BotUtils.get_color_settings(bot.gw2_settings["EmbedColor"])


################################################################################
async def init():
    log = BotUtils.setup_logging()
    bot = await _initialize_bot(log)
    bot.aiosession = aiohttp.ClientSession(loop=bot.loop)
    await _set_bot_configs(bot)
    await _set_other_cogs_configs(bot)
    bot.log.debug("Loading Bot Extensions...")
    await BotUtils.load_cogs(bot)
    bot.log.info("=====> INITIALIZING BOT <=====")

    try:
        await bot.login(str(bot.token))
        del bot.token
        await bot.connect()
    except discord.LoginFailure as e:
        for errorMsg in e.args:
            if "Improper token has been passed" in errorMsg:
                open(constants.TOKEN_FILENAME, 'w').close()
                formatted_lines = traceback.format_exc().splitlines()
                for err in formatted_lines:
                    if "discord." in err:
                        log.error(err)
                log.error(f"\n===> ERROR: Unable to login. {errorMsg}:{str(bot.token)}\n")
    except Exception as e:
        log.error(f"Bot has been terminated. {e}]")
        #loop.run_until_complete(bot.logout())


################################################################################
def init_loop():
    print(f"Starting Bot in {constants.TIME_BEFORE_START} secs...")
    time.sleep(constants.TIME_BEFORE_START)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(init())
    except Exception as e:
        print(str(e.args))
        loop.stop()
        loop.close()
        sys.exit(0)
    finally:
        loop.stop()
        loop.close()


################################################################################
if __name__ == '__main__':
    loop = None
    init_loop()
