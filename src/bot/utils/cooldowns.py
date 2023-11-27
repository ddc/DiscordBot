# -*- coding: utf-8 -*-
from enum import Enum
from src.bot.utils import bot_utils, constants


file_values = bot_utils.get_all_ini_file_settings(constants.SETTINGS_FILENAME)


class CoolDowns(Enum):
    AdminCooldown = 1 if constants.IS_DEBUG else int(file_values["AdminCooldown"])
    BlacklistCooldown = 1 if constants.IS_DEBUG else int(file_values["BlacklistCooldown"])
    CustomCmdCooldown = 1 if constants.IS_DEBUG else int(file_values["CustomCmdCooldown"])
    ConfigCooldown = 1 if constants.IS_DEBUG else int(file_values["ConfigCooldown"])
    MiscCooldown = 1 if constants.IS_DEBUG else int(file_values["MiscCooldown"])
    MuteCooldown = 1 if constants.IS_DEBUG else int(file_values["MuteCooldown"])
    OwnerCooldown = 1 if constants.IS_DEBUG else int(file_values["OwnerCooldown"])
    RollDiceCooldown = 1 if constants.IS_DEBUG else int(file_values["RollDiceCooldown"])
