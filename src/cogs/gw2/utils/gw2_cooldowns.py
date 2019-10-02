#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from enum import Enum
from src.cogs.bot.utils import bot_utils as BotUtils
import src.cogs.gw2.utils.gw2_constants as Gw2Constants

file_values = BotUtils.get_all_ini_file_settings(Gw2Constants.GW2_SETTINGS_FILENAME)


class GW2CoolDowns(Enum):
    AccountCooldown = int(file_values["AccountCooldown"])
    ApiKeysCooldown = int(file_values["ApiKeysCooldown"])
    DailyCooldown = int(file_values["DailyCooldown"])
    LastSessionCooldown = int(file_values["LastSessionCooldown"])
    MiscCooldown = int(file_values["MiscCooldown"])
    WvwCooldown = int(file_values["WvwCooldown"])
