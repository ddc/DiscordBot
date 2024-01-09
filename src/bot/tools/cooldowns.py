# -*- coding: utf-8 -*-
from enum import Enum
from src.bot.tools import bot_utils
from src.bot.constants import variables


file_values = bot_utils.get_ini_section_settings(variables.SETTINGS_FILENAME, "Cooldowns")


class CoolDowns(Enum):
    Admin = 1 if variables.IS_DEBUG else int(file_values["Admin"])
    CustomComand = 1 if variables.IS_DEBUG else int(file_values["CustomCmd"])
    Config = 1 if variables.IS_DEBUG else int(file_values["Config"])
    Misc = 1 if variables.IS_DEBUG else int(file_values["Misc"])
    Owner = 1 if variables.IS_DEBUG else int(file_values["Owner"])
    DiceRolls = 1 if variables.IS_DEBUG else int(file_values["DiceRolls"])
