# -*- coding: utf-8 -*-
from enum import Enum
from ddcUtils import ConfFileUtils
from src.bot.constants import variables


file_values = ConfFileUtils().get_section_values(variables.SETTINGS_FILENAME, "Cooldowns")


class CoolDowns(Enum):
    Admin = 1 if variables.DEBUG else int(file_values["Admin"])
    Config = 1 if variables.DEBUG else int(file_values["Config"])
    CustomComand = 1 if variables.DEBUG else int(file_values["CustomCmd"])
    DiceRolls = 1 if variables.DEBUG else int(file_values["DiceRolls"])
    Misc = 1 if variables.DEBUG else int(file_values["Misc"])
    OpenAI = 1 if variables.DEBUG else int(file_values["OpenAI"])
    Owner = 1 if variables.DEBUG else int(file_values["Owner"])
