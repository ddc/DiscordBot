from aiohttp import ClientSession
from better_profanity import profanity
from datetime import datetime
from discord.ext import commands
from src.bot.constants import messages
from src.bot.constants.settings import get_bot_settings
from src.bot.tools import bot_utils
from src.gw2.constants.gw2_settings import get_gw2_settings
from typing import Any


class Bot(commands.Bot):
    aiosession: ClientSession
    db_session: Any
    log: Any
    start_time: datetime
    settings: dict
    profanity: Any

    def __init__(self, *args, **kwargs):
        self.aiosession = kwargs.pop("aiosession")
        self.db_session = kwargs.pop("db_session")
        self.log = kwargs.pop("log")

        super().__init__(*args, **kwargs)

        # Initialize bot state
        self.start_time = bot_utils.get_current_date_time()
        self.settings = {}

        # Initialize profanity filter
        profanity.load_censor_words()
        self.profanity = profanity

        # Load settings
        self._load_settings()

    async def setup_hook(self) -> None:
        """Called after login - loads all cogs."""
        try:
            await bot_utils.load_cogs(self)
            self.log.info(messages.BOT_LOADED_ALL_COGS_SUCCESS)
        except Exception as e:
            self.log.error(f"{messages.BOT_LOAD_COGS_FAILED}: {e}")
            raise

    def _load_settings(self) -> None:
        """Load all bot and cog settings."""
        try:
            bot_settings = get_bot_settings()
            gw2_settings = get_gw2_settings()

            # Load bot settings from environment variables
            self.settings["bot"] = {
                "BGActivityTimer": bot_settings.bg_activity_timer,
                "AllowedDMCommands": bot_settings.allowed_dm_commands,
                "BotReactionWords": bot_settings.bot_reaction_words,
                "EmbedColor": bot_utils.get_color_settings(bot_settings.embed_color),
                "EmbedOwnerColor": bot_utils.get_color_settings(bot_settings.embed_owner_color),
                "ExclusiveUsers": bot_settings.exclusive_users,
            }

            # Load GW2 settings from environment variables
            self.settings["gw2"] = {
                "EmbedColor": bot_utils.get_color_settings(gw2_settings.embed_color),
            }

        except Exception as e:
            self.log.error(f"{messages.BOT_LOAD_SETTINGS_FAILED}: {e}")
            raise
