#! /usr/bin/env python3
#|*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
#|*****************************************************
# # -*- coding: utf-8 -*-

import os
import sys
import platform
import logging
################################################################################
################################################################################
################### CAUTION CHANGING ANY OF THESE VARS #########################
################################################################################
################################################################################
versionFile = open("VERSION", encoding="utf-8", mode="r")
VERSION = versionFile.read().split('\n', 1)[0].strip('\n')
versionFile.close()
################################################################################
IS_WINDOWS          = os.name == "nt"
IS_MAC              = sys.platform == "darwin"
IS_64BIT            = platform.machine().endswith("64")
INTERACTIVE_MODE    = not len(sys.argv) > 1
PYTHON_OK           = sys.version_info >= (3,6)
INTRO = (f"====================\nDiscord Bot v{VERSION}\n====================")
################################################################################
description         = "A Multifunction Bot for Discord"
paypal_url          = "https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=38E66BHC4623Y"
bot_webpage_url     = "https://ddc.github.io/DiscordBot"
version_url_file    = "https://raw.github.com/ddc/DiscordBot/master/VERSION"
settings_url_file   = "https://raw.githubusercontent.com/ddc/DiscordBot/master/config/settings.ini"
python_url          = "https://www.python.org/"
discordpy_url       = "https://github.com/Rapptz/discord.py"
git_url             = "https://git-scm.com"
sqlite3_url         = "https://sqlite.org"
postgresql_url      = "https://www.postgresql.org"
default_prefix      = "?"
################################################################################
settings_filename   = "config/settings.ini"
token_filename      = "config/token.txt"
swear_words_filename= "data/swear_words"
database_filename   = "data/database.db"
logs_filename       = "logs/bot.log"
sql_dirpath         = "data/sql"
###############################################################################
date_formatter      = "%b/%d/%Y"
time_formatter      = "%H:%M:%S"
LOG_LEVEL           = logging.INFO #INFO or DEBUG
LOG_FORMATTER       = logging.Formatter('%(asctime)s:[%(levelname)s]:[%(filename)s:%(funcName)s:%(lineno)d]:%(message)s',
                      datefmt=f"[{date_formatter} {time_formatter}]")
################################################################################
profanity_filter_msg = "Your message was removed.\nPlease don't say offensive words in this channel."
###############################################################################
games_included = ["Guild Wars 2"]
###############################################################################
apis_included = []
###############################################################################
cogs = ["src.cogs.bot.admin",
        "src.cogs.bot.config",
        "src.cogs.bot.errors",
        "src.cogs.bot.events",
        "src.cogs.bot.misc",
        "src.cogs.bot.owner",
        "src.cogs.gw2.gw2"
        ]
###############################################################################
