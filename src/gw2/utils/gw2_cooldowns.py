# -*- coding: utf-8 -*-
from enum import Enum
from src.bot.utils import bot_utils, constants
from src.gw2.utils import gw2_constants


file_values = bot_utils.get_all_ini_file_settings(gw2_constants.GW2_SETTINGS_FILENAME)


class GW2CoolDowns(Enum):
    Account = 1 if constants.IS_DEBUG else int(file_values["Account"])
    ApiKeys = 1 if constants.IS_DEBUG else int(file_values["ApiKeys"])
    Daily = 1 if constants.IS_DEBUG else int(file_values["Daily"])
    LastSession = 1 if constants.IS_DEBUG else int(file_values["LastSession"])
    Misc = 1 if constants.IS_DEBUG else int(file_values["Misc"])
    Wvw = 1 if constants.IS_DEBUG else int(file_values["Wvw"])
