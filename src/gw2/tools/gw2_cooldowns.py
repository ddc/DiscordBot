from enum import Enum
from src.bot.constants import variables
from src.gw2.constants.gw2_settings import get_gw2_settings


# Load GW2 cooldown values from environment variables
_gw2_settings = get_gw2_settings()


class GW2CoolDowns(Enum):
    """GW2 command cooldown durations in seconds.

    In debug mode, all cooldowns are set to 1 second for faster testing.
    In production, values are loaded from environment variables.
    
    Note: To avoid enum value merging when multiple cooldowns have the same value,
    we use a tuple (value, unique_id) and access the actual cooldown via .value[0]
    """

    Account = (1 if variables.DEBUG else _gw2_settings.account_cooldown, 'account')
    ApiKeys = (1 if variables.DEBUG else _gw2_settings.api_keys_cooldown, 'api_keys')
    Characters = (1 if variables.DEBUG else _gw2_settings.characters_cooldown, 'characters')
    Config = (1 if variables.DEBUG else _gw2_settings.config_cooldown, 'config')
    Daily = (1 if variables.DEBUG else _gw2_settings.daily_cooldown, 'daily')
    Misc = (1 if variables.DEBUG else _gw2_settings.misc_cooldown, 'misc')
    Session = (1 if variables.DEBUG else _gw2_settings.session_cooldown, 'session')
    Worlds = (1 if variables.DEBUG else _gw2_settings.worlds_cooldown, 'worlds')
    Wvw = (1 if variables.DEBUG else _gw2_settings.wvw_cooldown, 'wvw')

    def __str__(self) -> str:
        """Return the cooldown value as a string."""
        return str(self.value[0])

    @property
    def seconds(self) -> int:
        """Get the cooldown duration in seconds."""
        return self.value[0]
