# -*- coding: utf-8 -*-
from enum import Enum
from src.bot.utils import bot_utils, constants


file_values = bot_utils.get_all_ini_file_settings(constants.SETTINGS_FILENAME)


class CoolDowns(Enum):
    Admin = 1 if constants.IS_DEBUG else int(file_values["Admin"])
    CustomComand = 1 if constants.IS_DEBUG else int(file_values["CustomCmd"])
    Config = 1 if constants.IS_DEBUG else int(file_values["Config"])
    Misc = 1 if constants.IS_DEBUG else int(file_values["Misc"])
    Owner = 1 if constants.IS_DEBUG else int(file_values["Owner"])
    DiceRolls = 1 if constants.IS_DEBUG else int(file_values["DiceRolls"])
