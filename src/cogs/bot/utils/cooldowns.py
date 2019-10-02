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
from src.cogs.bot.utils import constants

file_values = BotUtils.get_all_ini_file_settings(constants.SETTINGS_FILENAME)


class CoolDowns(Enum):
    AdminCooldown = int(file_values["AdminCooldown"])
    BlacklistCooldown = int(file_values["BlacklistCooldown"])
    CustomCmdCooldown = int(file_values["CustomCmdCooldown"])
    ConfigCooldown = int(file_values["ConfigCooldown"])
    MiscCooldown = int(file_values["MiscCooldown"])
    MuteCooldown = int(file_values["MuteCooldown"])
    OwnerCooldown = int(file_values["OwnerCooldown"])
    RollDiceCooldown = int(file_values["RollDiceCooldown"])

