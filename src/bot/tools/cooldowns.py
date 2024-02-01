# -*- coding: utf-8 -*-
from enum import Enum
from ddcUtils import FileUtils
from src.bot.constants import variables


file_values = FileUtils().get_file_section_values(variables.SETTINGS_FILENAME, "Cooldowns")


class CoolDowns(Enum):
    Admin = 1 if variables.DEBUG else int(file_values["Admin"])
    CustomComand = 1 if variables.DEBUG else int(file_values["CustomCmd"])
    Config = 1 if variables.DEBUG else int(file_values["Config"])
    Misc = 1 if variables.DEBUG else int(file_values["Misc"])
    Owner = 1 if variables.DEBUG else int(file_values["Owner"])
    DiceRolls = 1 if variables.DEBUG else int(file_values["DiceRolls"])
