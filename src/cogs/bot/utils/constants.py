# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path


DEBUG = False
TIME_BEFORE_START = 5
INTERACTIVE_MODE = not len(sys.argv) > 1
PYTHON_OK = sys.version_info >= (3, 6)
IS_WINDOWS = os.name == "nt"
#import platform
#IS_MAC = sys.platform == "darwin"
#IS_64BIT = platform.machine().endswith("64")
###############################################################################
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
SETTINGS_FILENAME = os.path.join(BASE_DIR, "config", "settings.ini")
TOKEN_FILENAME = os.path.join(BASE_DIR, "config", "token.txt")
SWEAR_WORDS_FILENAME = os.path.join(BASE_DIR, "data", "swear_words")
DATABASE_FILENAME = os.path.join(BASE_DIR, "data", "database.db")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SQL_DIRPATH = os.path.join(BASE_DIR, "data", "sql")
###############################################################################
_versionFile = open(os.path.join(BASE_DIR, "VERSION"), encoding="utf-8", mode="r")
VERSION = _versionFile.read().split('\n', 1)[0].strip('\n')
_versionFile.close()
INTRO = f"{20*'='}\nDiscord Bot v{VERSION}\n{20*'='}"
###############################################################################
DESCRIPTION = "A Multifunction Bot for Discord"
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
###############################################################################
DATE_FORMATTER = "%Y-%m-%d"
TIME_FORMATTER = "%H:%M:%S"
###############################################################################
PROFANITY_FILTER_MSG = "Your message was removed.\nPlease don't say offensive words in this channel"
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
        "src.cogs.gw2.gw2"]
