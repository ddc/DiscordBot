# -*- coding: utf-8 -*-
from enum import Enum
from src.bot.utils import bot_utils, constants
from src.gw2.utils import gw2_constants


file_values = bot_utils.get_ini_section_settings(gw2_constants.GW2_SETTINGS_FILENAME, "Cooldowns")


class GW2CoolDowns(Enum):
    Account = 1 if constants.IS_DEBUG else int(file_values["Account"])
    ApiKeys = 1 if constants.IS_DEBUG else int(file_values["ApiKeys"])
    Characters = 1 if constants.IS_DEBUG else int(file_values["Characters"])
    Config = 1 if constants.IS_DEBUG else int(file_values["Config"])
    Daily = 1 if constants.IS_DEBUG else int(file_values["Daily"])
    Misc = 1 if constants.IS_DEBUG else int(file_values["Misc"])
    Session = 1 if constants.IS_DEBUG else int(file_values["Session"])
    Worlds = 1 if constants.IS_DEBUG else int(file_values["Worlds"])
    Wvw = 1 if constants.IS_DEBUG else int(file_values["Wvw"])
