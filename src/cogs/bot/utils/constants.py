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
import platform
import logging

abspath = os.path.abspath(__file__)
root_path = os.path.dirname(abspath).replace("\\src\\cogs\\bot\\utils", "")
_versionFile = open(f"{root_path}\\VERSION", encoding="utf-8", mode="r")
VERSION = _versionFile.read().split('\n', 1)[0].strip('\n')
_versionFile.close()
################################################################################
IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_64BIT = platform.machine().endswith("64")
INTERACTIVE_MODE = not len(sys.argv) > 1
PYTHON_OK = sys.version_info >= (3, 6)
INTRO = (f"====================\nDiscord Bot v{VERSION}\n====================")
################################################################################
DESCRIPTION = "A Multifunction Bot for Discord"
DEFAULT_PREFIX = "?"
AUTHOR_ID = 195615080665055232
PAYPAL_URL = "https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=38E66BHC4623Y"
BOT_WEBPAGE_URL = "https://ddc.github.io/DiscordBot"
BOT_REMOTE_GIT_URL = "https://github.com/ddc/DiscordBot.git"
VERSION_URL_FILE = "https://raw.github.com/ddc/DiscordBot/master/VERSION"
SETTINGS_URL_FILE = "https://raw.githubusercontent.com/ddc/DiscordBot/master/config/settings.ini"
PYTHON_URL = "https://www.python.org/"
DISCORDPY_URL = "https://github.com/Rapptz/discord.py"
GIT_URL = "https://git-scm.com"
SQLITE3_URL = "https://sqlite.org"
POSTGRESQL_URL = "https://www.postgresql.org"
################################################################################
SETTINGS_FILENAME = "config/settings.ini"
TOKEN_FILENAME = "config/token.txt"
SWEAR_WORDS_FILENAME = "data/swear_words"
DATABASE_FILENAME = "data/database.db"
LOGS_FILENAME = "logs/bot.log"
SQL_DIRPATH = "data/sql"
###############################################################################
DATE_FORMATTER = "%b/%d/%Y"
TIME_FORMATTER = "%H:%M:%S"
LOG_LEVEL = logging.INFO  # INFO or DEBUG
LOG_FORMATTER = logging.Formatter('%(asctime)s:[%(levelname)s]:[%(filename)s:%(funcName)s:%(lineno)d]:%(message)s',
                                  datefmt=f"[{DATE_FORMATTER} {TIME_FORMATTER}]")
################################################################################
PROFANITY_FILTER_MSG = "Your message was removed.\nPlease don't say offensive words in this channel."
###############################################################################
GAMES_INCLUDED = ["Guild Wars 2"]
###############################################################################
APIS_INCLUDED = []
###############################################################################
COGS = ["src.cogs.bot.admin",
        "src.cogs.bot.config",
        "src.cogs.bot.errors",
        "src.cogs.bot.events",
        "src.cogs.bot.misc",
        "src.cogs.bot.owner",
        "src.cogs.gw2.gw2"
        ]
