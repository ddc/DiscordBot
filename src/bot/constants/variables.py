# -*- coding: utf-8 -*-
import glob
import os
import sys
from pathlib import Path
from src.bot.constants.configs import Configs
from ddcUtils import ConfFileUtils


_env_configs = Configs()
DEBUG = _env_configs.debug
###############################################################################
DESCRIPTION = "A Bot for Discord"
AUTHOR_ID = "195615080665055232"
PAYPAL_URL = "https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=38E66BHC4623Y"
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
DEFAULT_PREFIX = _env_configs.default_prefix
ALLOWED_PREFIXES = ("!", "?", "$", "%", "&", ".")
TIME_BEFORE_START = 5 if DEBUG is False else 0
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
_bot_cogs = [os.path.join("src", "bot", "admin", "admin.py")] # loading admin group cog first
_bot_cogs += [x for x in glob.glob(os.path.join("src", "bot", "*.py"))]
_bot_cogs += [x for x in glob.glob(os.path.join("src", "bot", "events", "*.py"))]
_bot_cogs += [x for x in glob.glob(os.path.join("src", "bot", "admin", "*.py")) if x not in _bot_cogs]
###############################################################################
_gw2_cogs = [os.path.join("src", "gw2", "gw2.py")] # loading gw2 group cog first
_gw2_cogs += [x for x in glob.glob(os.path.join("src", "gw2", "*.py")) if x not in _gw2_cogs]
###############################################################################
ALL_COGS = _bot_cogs + _gw2_cogs
###############################################################################
