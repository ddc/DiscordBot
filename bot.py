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
from src.bot.utils import bot_utils, constants
from src.bot.utils.log import Log
from src.database.dal.bot.bot_configs_dal import BotConfigsDal
from src.database.db import Database
from src.gw2.utils import gw2_constants


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = kwargs.get("log")
        self.web_client = kwargs.get("web_client")
        self.db_session = kwargs.get("db_session")
        self.profanity = kwargs.get("profanity")
        self.start_time = None
        self.token = None
        self.settings = None
        self.gw2_settings = None

        if os.path.isfile(constants.TOKEN_FILENAME):
            with open(constants.TOKEN_FILENAME, encoding="UTF-8", mode="r") as token_file:
                self.token = token_file.read().split("\n", 1)[0].strip("\n")
        else:
            self.log.error(f"Token file was not found: {constants.TOKEN_FILENAME}")
            sys.exit(1)

        self.set_bot_custom_configs()
        self.set_other_cogs_configs()

    async def setup_hook(self):
        """ This will be called after login"""
        await bot_utils.load_cogs(self)

    def set_bot_custom_configs(self):
        self.description = str(constants.DESCRIPTION)
        self.help_command = commands.DefaultHelpCommand(dm_help=True)
        self.settings = bot_utils.get_all_ini_file_settings(constants.SETTINGS_FILENAME)
        self.settings["EmbedOwnerColor"] = bot_utils.get_color_settings(self.settings["EmbedOwnerColor"])
        self.settings["EmbedColor"] = bot_utils.get_color_settings(self.settings["EmbedColor"])

    def set_other_cogs_configs(self):
        self.gw2_settings = bot_utils.get_all_ini_file_settings(gw2_constants.GW2_SETTINGS_FILENAME)
        self.gw2_settings["EmbedColor"] = bot_utils.get_color_settings(self.gw2_settings["EmbedColor"])


async def main():
    # run alembic migrations
    await bot_utils.run_alembic_migrations()
    database = Database()
    database_engine = database.get_db_engine()

    async with ClientSession() as client_session, database.get_db_session(database_engine) as db_session:
        # init log
        log = Log(constants.LOGS_DIR, constants.IS_DEBUG).setup_logging()

        # get prefix from database and set it
        bot_configs_sql = BotConfigsDal(db_session, log)
        db_prefix = await bot_configs_sql.get_bot_prefix()
        command_prefix = constants.DEFAULT_PREFIX if not db_prefix else db_prefix
        intents = discord.Intents.all()

        # set bot description
        help_cmd = f"{command_prefix}help"
        game = str(random.choice(constants.GAMES_INCLUDED))
        random_game_desc = f"{game} | {help_cmd}"
        exclusive_users = bot_utils.get_ini_settings(constants.SETTINGS_FILENAME, "Bot", "ExclusiveUsers")
        bot_game_desc = f"PRIVATE BOT | {help_cmd}" if exclusive_users is not None else random_game_desc
        activity = discord.Game(name=bot_game_desc)

        # load profanity words
        profanity.load_censor_words()

        bot_kwargs = {
            "command_prefix": command_prefix,
            "activity": activity,
            "intents": intents,
            "log": log,
            "web_client": client_session,
            "db_session": db_session,
            "profanity": profanity,
            "owner_id": int(constants.AUTHOR_ID),
        }
        async with Bot(**bot_kwargs) as bot:
            try:
                await bot_utils.init_background_tasks(bot)
                await bot.start(bot.token)
            except discord.LoginFailure:
                formatted_lines = traceback.format_exc().splitlines()
                [bot.log.error(x) for x in formatted_lines if x.startswith("discord")]
            except Exception as ex:
                bot.log.error(f"Bot has been terminated. {ex}]")
            finally:
                await bot.close()

    await database_engine.dispose()


if __name__ == "__main__":
    print(f"Starting Bot in {constants.TIME_BEFORE_START} secs")
    time.sleep(constants.TIME_BEFORE_START)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except Exception as e:
        print(str(e.args))
        loop.stop()
        loop.close()
        sys.exit(0)
    finally:
        loop.stop()
        loop.close()
