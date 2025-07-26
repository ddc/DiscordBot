"""Bot command cooldown configuration from settings file."""

from enum import Enum
from typing import Final
from ddcUtils import ConfFileUtils
from src.bot.constants import variables


# Load cooldown values from configuration file
_conf_utils = ConfFileUtils()
_cooldown_settings: Final[dict[str, str]] = _conf_utils.get_section_values(variables.SETTINGS_FILENAME, "Cooldowns")


class CoolDowns(Enum):
    """Command cooldown durations in seconds.

    In debug mode, all cooldowns are set to 1 second for faster testing.
    In production, values are loaded from the configuration file.
    """

    Admin = 1 if variables.DEBUG else int(_cooldown_settings["Admin"])
    Config = 1 if variables.DEBUG else int(_cooldown_settings["Config"])
    CustomCommand = 1 if variables.DEBUG else int(_cooldown_settings["CustomCmd"])
    DiceRolls = 1 if variables.DEBUG else int(_cooldown_settings["DiceRolls"])
    Misc = 1 if variables.DEBUG else int(_cooldown_settings["Misc"])
    OpenAI = 1 if variables.DEBUG else int(_cooldown_settings["OpenAI"])
    Owner = 1 if variables.DEBUG else int(_cooldown_settings["Owner"])

    def __str__(self) -> str:
        """Return the cooldown value as a string."""
        return str(self.value)

    @property
    def seconds(self) -> int:
        """Get the cooldown duration in seconds."""
        return self.value
