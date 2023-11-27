# -*- coding: utf-8 -*-
from enum import Enum
from src.bot.utils import bot_utils, constants
from src.gw2.utils import gw2_constants


file_values = bot_utils.get_all_ini_file_settings(gw2_constants.GW2_SETTINGS_FILENAME)


class GW2CoolDowns(Enum):
    AccountCooldown = 1 if constants.IS_DEBUG else int(file_values["AccountCooldown"])
    ApiKeysCooldown = 1 if constants.IS_DEBUG else int(file_values["ApiKeysCooldown"])
    DailyCooldown = 1 if constants.IS_DEBUG else int(file_values["DailyCooldown"])
    LastSessionCooldown = 1 if constants.IS_DEBUG else int(file_values["LastSessionCooldown"])
    MiscCooldown = 1 if constants.IS_DEBUG else int(file_values["MiscCooldown"])
    WvwCooldown = 1 if constants.IS_DEBUG else int(file_values["WvwCooldown"])
