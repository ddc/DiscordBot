# -*- coding: utf-8 -*-
import glob
import os
import sys
from pathlib import Path


IS_DEBUG = True
DEFAULT_PREFIX = "!"
ALLOWED_PREFIXES = "!$%^&?><.;"
TIME_BEFORE_START = 5 if IS_DEBUG is False else 0
INTERACTIVE_MODE = len(sys.argv) <= 1
PYTHON_OK = sys.version_info >= (3, 6)
IS_WINDOWS = os.name == "nt"
###############################################################################
BASE_DIR = f"{Path(__file__).resolve().parent.parent.parent.parent}/"
SETTINGS_FILENAME = os.path.join(BASE_DIR, "config", "settings.ini")
ALEMBIC_CONFIG_FILE_PATH = os.path.join(BASE_DIR, "config", "alembic.ini")
DATABASE_FILENAME = os.path.join(BASE_DIR, "data", "database.db")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SQL_DIRPATH = os.path.join(BASE_DIR, "data", "sql")
###############################################################################
_versionFile = open(os.path.join(BASE_DIR, "VERSION"), encoding="utf-8", mode="r")
VERSION = _versionFile.read().split('\n', 1)[0].strip('\n')
_versionFile.close()
###############################################################################
DESCRIPTION = "A Multifunction Bot for Discord"
AUTHOR_ID = "195615080665055232"
PAYPAL_URL = "https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=38E66BHC4623Y"
BOT_WEBPAGE_URL = "https://ddc.github.io/DiscordBot"
VERSION_URL_FILE = "https://raw.github.com/ddc/DiscordBot/master/VERSION"
SETTINGS_URL_FILE = "https://raw.githubusercontent.com/ddc/DiscordBot/master/config/settings.ini"
DISCORDPY_URL = "https://github.com/Rapptz/discord.py"
###############################################################################
DATE_FORMATTER = "%Y-%m-%d"
TIME_FORMATTER = "%H:%M:%S.%f"
###############################################################################
GAMES_INCLUDED = ("Guild Wars 2",)
###############################################################################
APIS_INCLUDED = ()
###############################################################################
BOT_COGS = [
    x for x in glob.glob(os.path.join("src", "bot", "*.py"))
]
BOT_COGS.sort(key=lambda x: x.split("/")[2])

EVENTS_COGS = [
    x for x in glob.glob(os.path.join("src", "bot", "events", "*.py"))
]
EVENTS_COGS.sort(key=lambda x: x.split("/")[3])

ADMIN_COGS = [
    x for x in glob.glob(os.path.join("src", "bot", "admin", "*.py"))
]
ADMIN_COGS.sort(key=lambda x: x.split("/")[3])

OTHER_COGS = [
    os.path.join("src", "gw2", "gw2.py"),
]
###############################################################################
ALL_COGS = BOT_COGS + EVENTS_COGS + ADMIN_COGS + OTHER_COGS
###############################################################################
