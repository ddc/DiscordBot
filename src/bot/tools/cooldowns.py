from enum import Enum
from src.bot.constants import variables
from src.bot.constants.settings import get_bot_settings

# Load cooldown values from environment variables
_bot_settings = get_bot_settings()


class CoolDowns(Enum):
    """Command cooldown durations in seconds.

    In debug mode, all cooldowns are set to 1 second for faster testing.
    In production, values are loaded from environment variables.
    """

    Admin = 1 if variables.DEBUG else _bot_settings.admin_cooldown
    Config = 1 if variables.DEBUG else _bot_settings.config_cooldown
    CustomCommand = 1 if variables.DEBUG else _bot_settings.custom_cmd_cooldown
    DiceRolls = 1 if variables.DEBUG else _bot_settings.dice_rolls_cooldown
    Misc = 1 if variables.DEBUG else _bot_settings.misc_cooldown
    OpenAI = 1 if variables.DEBUG else _bot_settings.openai_cooldown
    Owner = 1 if variables.DEBUG else _bot_settings.owner_cooldown

    def __str__(self) -> str:
        """Return the cooldown value as a string."""
        return str(self.value)

    @property
    def seconds(self) -> int:
        """Get the cooldown duration in seconds."""
        return self.value
