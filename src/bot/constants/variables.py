# -*- coding: utf-8 -*-
import glob
import os
import sys
from pathlib import Path
from src.bot.constants.settings import BotSettings
from ddcLogs.settings import LogSettings
from ddcUtils import ConfFileUtils


DEBUG = True if LogSettings().level == "DEBUG" else False
###############################################################################
DESCRIPTION = "A Bot for Discord"
AUTHOR_ID = "195615080665055232"
PAYPAL_URL = "https://www.paypal.com/ncp/payment/6G9Z78QHUD4RJ"
BOT_WEBPAGE_URL = "https://ddc.github.io/DiscordBot"
DISCORDPY_URL = "https://github.com/Rapptz/discord.py"
LMGTFY_URL = "https://lmgtfy.com"
###############################################################################
DATE_TIME_FORMATTER_STR = "%a %b %m %Y %X"
DATE_FORMATTER = "%Y-%m-%d"
TIME_FORMATTER = "%H:%M:%S.%f"
###############################################################################
GAMES_INCLUDED = ("Guild Wars 2",)
###############################################################################
PREFIX = BotSettings().prefix
ALLOWED_PREFIXES = ("!", "?", "$", "%", "&", ".")
TIME_BEFORE_START = 0 if DEBUG else 5
INTERACTIVE_MODE = len(sys.argv) <= 1
IS_WINDOWS = os.name == "nt"
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
###############################################################################
_python_req_version = ConfFileUtils().get_value(os.path.join(BASE_DIR, "pyproject.toml"), "tool.poetry.dependencies", "python")
_major = int(_python_req_version.split(".")[0].replace("^", ""))
_minor = int(_python_req_version.split(".")[1])
PYTHON_OK = sys.version_info >= (_major, _minor)
###############################################################################
VERSION = ConfFileUtils().get_value(os.path.join(BASE_DIR, "pyproject.toml"), "tool.poetry", "version")
SETTINGS_FILENAME = os.path.join(BASE_DIR, "config", "bot_settings.ini")
ALEMBIC_CONFIG_FILE_PATH = os.path.join(BASE_DIR, "config", "alembic.ini")
DATABASE_FILENAME = os.path.join(BASE_DIR, "data", "database.db")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SQL_DIRPATH = os.path.join(BASE_DIR, "data", "sql")
###############################################################################
_bot_cogs = [os.path.join("src", "bot", "cogs", "admin", "admin.py")] # loading admin group cog first
_bot_cogs += [x for x in glob.glob(os.path.join("src", "bot", "cogs", "*.py"))]
_bot_cogs += [x for x in glob.glob(os.path.join("src", "bot", "cogs", "events", "*.py"))]
_bot_cogs += [x for x in glob.glob(os.path.join("src", "bot", "cogs", "admin", "*.py")) if x not in _bot_cogs]
###############################################################################
_gw2_cogs = [os.path.join("src", "gw2", "cogs", "gw2.py")] # loading gw2 group cog first
_gw2_cogs += [x for x in glob.glob(os.path.join("src", "gw2", "cogs", "*.py")) if x not in _gw2_cogs]
###############################################################################
ALL_COGS = _bot_cogs + _gw2_cogs
###############################################################################
