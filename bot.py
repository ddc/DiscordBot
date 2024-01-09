# -*- coding: utf-8 -*-
import asyncio
import os
import random
import sys
import time
import traceback
import discord
from aiohttp import ClientSession
from better_profanity import profanity
from discord.ext import commands
from src.bot.tools import bot_utils
from src.bot.constants import variables, messages
from src.bot.tools.log import Log
from src.database.dal.bot.bot_configs_dal import BotConfigsDal
from src.database.db import Database
from src.gw2.constants import gw2_variables


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        profanity.load_censor_words()
        self.aiosession = kwargs.get("aiosession")
        self.db_session = kwargs.get("db_session")
        self.start_time = bot_utils.get_current_date_time()
        self.log = kwargs.get("log")
        self.profanity = profanity
        self.settings = {}
        self.set_bot_custom_settings(*args, **kwargs)
        self.set_other_cogs_settings(*args, **kwargs)

    async def setup_hook(self):
        """ This will be called after login"""
        await bot_utils.load_cogs(self)

    def set_bot_custom_settings(self, *args, **kwargs):
        self.settings["bot"] = bot_utils.get_ini_section_settings(variables.SETTINGS_FILENAME, "Bot")
        self.settings["bot"]["EmbedColor"] = bot_utils.get_color_settings(self.settings["bot"]["EmbedColor"])
        self.settings["bot"]["EmbedOwnerColor"] = bot_utils.get_color_settings(self.settings["bot"]["EmbedOwnerColor"])

    def set_other_cogs_settings(self, *args, **kwargs):
        self.settings["gw2"] = bot_utils.get_ini_section_settings(gw2_variables.GW2_SETTINGS_FILENAME, "Gw2")
        self.settings["gw2"]["EmbedColor"] = bot_utils.get_color_settings(self.settings["gw2"]["EmbedColor"])


async def main():
    # run alembic migrations
    await bot_utils.run_alembic_migrations()
    database = Database()
    database_engine = database.get_db_engine()

    async with ClientSession() as client_session, database.get_db_session(database_engine) as db_session:
        # init log
        log = Log(variables.LOGS_DIR, variables.IS_DEBUG).setup_logging()

        # check BOT_TOKEN env
        if not os.environ.get("BOT_TOKEN"):
            log.error(messages.BOT_TOKEN_NOT_FOUND)
            sys.exit(1)

        # get prefix from database and set it
        bot_configs_sql = BotConfigsDal(db_session, log)
        db_prefix = await bot_configs_sql.get_bot_prefix()
        command_prefix = variables.DEFAULT_PREFIX if not db_prefix else db_prefix
        intents = discord.Intents.all()

        # set bot description
        help_cmd = f"{command_prefix}help"
        system_random = random.SystemRandom()
        game = system_random.choice(variables.GAMES_INCLUDED)
        random_game_desc = f"{game} | {help_cmd}"
        exclusive_users = bot_utils.get_ini_settings(variables.SETTINGS_FILENAME, "Bot", "ExclusiveUsers")
        bot_game_desc = f"PRIVATE BOT | {help_cmd}" if exclusive_users is not None else random_game_desc
        activity = discord.Game(name=bot_game_desc)

        bot_kwargs = {
            "command_prefix": command_prefix,
            "description": variables.DESCRIPTION,
            "activity": activity,
            "intents": intents,
            "aiosession": client_session,
            "db_session": db_session,
            "owner_id": int(variables.AUTHOR_ID),
            "log": log,
        }
        async with Bot(**bot_kwargs) as bot:
            try:
                await bot_utils.init_background_tasks(bot)
                await bot.start(os.environ.get("BOT_TOKEN"))
            except discord.LoginFailure:
                formatted_lines = traceback.format_exc().splitlines()
                [bot.log.error(x) for x in formatted_lines if x.startswith("discord")]
            except Exception as ex:
                bot.log.error(f"{messages.BOT_TERMINATED} | {ex}]")
            finally:
                await bot.close()

    await database_engine.dispose()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        print(messages.BOT_STARTING.format(variables.TIME_BEFORE_START))
        time.sleep(variables.TIME_BEFORE_START)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print(messages.BOT_STOPPED_CTRTC)
    except Exception as e:
        print(str(e.args))
    finally:
        print(messages.CLOSING_LOOP)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.stop()
        loop.close()
