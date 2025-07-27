import asyncio
import random
import sys
import time
import traceback
import discord
from aiohttp import ClientSession
from better_profanity import profanity
from ddcDatabases import PostgreSQL
from discord.ext import commands
from pythonLogs import timed_rotating_logger
from src.bot.constants import messages, variables
from src.bot.constants.settings import get_bot_settings
from src.gw2.constants.gw2_settings import get_gw2_settings
from src.bot.tools import bot_utils
from src.database.dal.bot.bot_configs_dal import BotConfigsDal
from src.gw2.constants import gw2_variables


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        # Extract custom kwargs before calling super()
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
            self.log.info("Successfully loaded all cogs")
        except Exception as e:
            self.log.error(f"Failed to load cogs: {e}")
            raise

    def _load_settings(self) -> None:
        """Load all bot and cog settings."""
        try:
            bot_settings = get_bot_settings()
            gw2_settings = get_gw2_settings()

            # Load bot settings from environment variables
            self.settings["bot"] = {
                "BGActivityTimer": str(bot_settings.bg_activity_timer),
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
            self.log.error(f"Failed to load settings: {e}")
            raise


async def _get_command_prefix(database_session, log) -> str:
    """Get command prefix from database or use default."""
    try:
        bot_configs_dal = BotConfigsDal(database_session, log)
        db_prefix = await bot_configs_dal.get_bot_prefix()
        return db_prefix or variables.PREFIX
    except Exception as e:
        log.warning(f"Failed to get prefix from database, using default: {e}")
        return variables.PREFIX


def _create_bot_activity(command_prefix: str) -> discord.Game:
    """Create bot activity/status."""
    help_cmd = f"{command_prefix}help"

    # Check if bot is in exclusive mode
    bot_settings = get_bot_settings()
    exclusive_users = bot_settings.exclusive_users

    if exclusive_users:
        game_desc = f"PRIVATE BOT | {help_cmd}"
    else:
        system_random = random.SystemRandom()
        game = system_random.choice(variables.GAMES_INCLUDED)
        game_desc = f"{game} | {help_cmd}"

    return discord.Game(name=game_desc)


async def main() -> None:
    """Main bot initialization and startup function."""
    log = timed_rotating_logger()

    try:
        # Validate bot token early
        bot_token = get_bot_settings().token
        if not bot_token:
            log.error(messages.BOT_TOKEN_NOT_FOUND)
            sys.exit(1)

        async with ClientSession() as client_session:
            async with PostgreSQL() as database_session:
                # Get configuration
                command_prefix = await _get_command_prefix(database_session, log)
                activity = _create_bot_activity(command_prefix)

                # Configure bot
                bot_kwargs = {
                    "command_prefix": command_prefix,
                    "activity": activity,
                    "intents": discord.Intents.all(),
                    "help_command": commands.DefaultHelpCommand(dm_help=variables.DM_HELP_COMMAND),
                    "description": variables.DESCRIPTION,
                    "owner_id": int(variables.AUTHOR_ID),
                    "aiosession": client_session,
                    "db_session": database_session,
                    "log": log,
                }

                async with Bot(**bot_kwargs) as bot:
                    try:
                        bot_utils.init_background_tasks(bot)
                        log.info("Bot starting...")
                        await bot.start(bot_token)
                    except discord.LoginFailure as e:
                        log.error(f"Discord login failed: {e}")
                        formatted_lines = traceback.format_exc().splitlines()
                        for line in formatted_lines:
                            if line.startswith("discord"):
                                log.error(line)
                    except Exception as e:
                        log.error(f"{messages.BOT_TERMINATED} | {e}")
                        raise
                    finally:
                        log.info("Closing bot...")
                        await bot.close()

    except Exception as e:
        log.error(f"Fatal error in main(): {e}")
        raise


def run_bot() -> None:
    print(messages.BOT_STARTING.format(variables.TIME_BEFORE_START))
    time.sleep(variables.TIME_BEFORE_START)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(messages.BOT_STOPPED_CTRTC)
    except Exception as ex:
        print(f"Bot crashed: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    run_bot()
