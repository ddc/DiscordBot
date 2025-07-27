from enum import Enum
from src.bot.constants import variables
from src.gw2.constants.gw2_settings import get_gw2_settings


# Load GW2 cooldown values from environment variables
_gw2_settings = get_gw2_settings()


class GW2CoolDowns(Enum):
    Account = 1 if variables.DEBUG else _gw2_settings.account_cooldown
    ApiKeys = 1 if variables.DEBUG else _gw2_settings.api_keys_cooldown
    Characters = 1 if variables.DEBUG else _gw2_settings.characters_cooldown
    Config = 1 if variables.DEBUG else _gw2_settings.config_cooldown
    Daily = 1 if variables.DEBUG else _gw2_settings.daily_cooldown
    Misc = 1 if variables.DEBUG else _gw2_settings.misc_cooldown
    Session = 1 if variables.DEBUG else _gw2_settings.session_cooldown
    Worlds = 1 if variables.DEBUG else _gw2_settings.worlds_cooldown
    Wvw = 1 if variables.DEBUG else _gw2_settings.wvw_cooldown
