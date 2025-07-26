from enum import Enum
from ddcUtils import ConfFileUtils
from src.bot.constants import variables
from src.gw2.constants import gw2_variables


file_values = ConfFileUtils().get_section_values(gw2_variables.GW2_SETTINGS_FILENAME, "Cooldowns")


class GW2CoolDowns(Enum):
    Account = 1 if variables.DEBUG else int(file_values["Account"])
    ApiKeys = 1 if variables.DEBUG else int(file_values["ApiKeys"])
    Characters = 1 if variables.DEBUG else int(file_values["Characters"])
    Config = 1 if variables.DEBUG else int(file_values["Config"])
    Daily = 1 if variables.DEBUG else int(file_values["Daily"])
    Misc = 1 if variables.DEBUG else int(file_values["Misc"])
    Session = 1 if variables.DEBUG else int(file_values["Session"])
    Worlds = 1 if variables.DEBUG else int(file_values["Worlds"])
    Wvw = 1 if variables.DEBUG else int(file_values["Wvw"])
