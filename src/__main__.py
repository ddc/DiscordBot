import asyncio
import discord
import random
import sys
import time
import traceback
from aiohttp import ClientSession
from ddcDatabases import PostgreSQL
from pythonLogs import TimedRotatingLog
from src.bot.constants import messages, variables
from src.bot.constants.settings import get_bot_settings
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils
from src.bot.tools.custom_help import CustomHelpCommand
from src.database.dal.bot.bot_configs_dal import BotConfigsDal


async def _get_command_prefix(database_session, log) -> str:
    """Get command prefix from database or use default."""
    try:
        bot_configs_dal = BotConfigsDal(database_session, log)
        db_prefix = await bot_configs_dal.get_bot_prefix()
        return db_prefix or variables.PREFIX
    except Exception as e:
        log.warning(f"{messages.BOT_INIT_PREFIX_FAILED}: {e}")
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

    # using .env file, no log arguments needed
    log = TimedRotatingLog()

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
                    "help_command": CustomHelpCommand(dm_help=variables.DM_HELP_COMMAND),
                    "description": variables.DESCRIPTION,
                    "owner_id": int(variables.AUTHOR_ID),
                    "aiosession": client_session,
                    "db_session": database_session,
                    "log": log,
                }

                async with Bot(**bot_kwargs) as bot:
                    try:
                        bot_utils.init_background_tasks(bot)
                        await bot.start(bot_token)
                    except discord.LoginFailure as e:
                        log.error(f"{messages.BOT_LOGIN_FAILED}: {e}")
                        formatted_lines = traceback.format_exc().splitlines()
                        for line in formatted_lines:
                            if line.startswith("discord"):
                                log.error(line)
                    except Exception as e:
                        log.error(f"{messages.BOT_TERMINATED} | {e}")
                        raise
                    finally:
                        log.info(messages.BOT_CLOSING)
                        await bot.close()

    except Exception as e:
        log.error(f"{messages.BOT_FATAL_ERROR_MAIN}: {e}")
        raise


def run_bot() -> None:
    print(messages.bot_starting(variables.TIME_BEFORE_START))
    time.sleep(variables.TIME_BEFORE_START)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(messages.BOT_STOPPED_CTRTC)
    except Exception as ex:
        print(f"{messages.BOT_CRASHED}: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    run_bot()
