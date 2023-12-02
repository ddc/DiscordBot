# -*- coding: utf-8 -*-
from enum import Enum
from src.bot.utils import bot_utils, constants


file_values = bot_utils.get_all_ini_file_settings(constants.SETTINGS_FILENAME)


class CoolDowns(Enum):
    Admin = 1 if constants.IS_DEBUG else int(file_values["Admin"])
    Blacklist = 1 if constants.IS_DEBUG else int(file_values["Blacklist"])
    CustomComand = 1 if constants.IS_DEBUG else int(file_values["CustomCmd"])
    Config = 1 if constants.IS_DEBUG else int(file_values["Config"])
    Misc = 1 if constants.IS_DEBUG else int(file_values["Misc"])
    Mute = 1 if constants.IS_DEBUG else int(file_values["Mute"])
    Owner = 1 if constants.IS_DEBUG else int(file_values["Owner"])
    RollDice = 1 if constants.IS_DEBUG else int(file_values["RollDice"])
