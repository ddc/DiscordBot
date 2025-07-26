import os
import sys
from pathlib import Path
from typing import Final
from ddcUtils import ConfFileUtils
from pythonLogs.settings import get_log_settings
from src.bot.constants.settings import get_bot_settings


# Debug and basic configuration
DEBUG: Final[bool] = get_log_settings().level == "DEBUG"

# Bot metadata
DESCRIPTION: Final[str] = "A Bot for Discord"
AUTHOR_ID: Final[str] = "195615080665055232"
PAYPAL_URL: Final[str] = "https://www.paypal.com/ncp/payment/6G9Z78QHUD4RJ"
BOT_WEBPAGE_URL: Final[str] = "https://ddc.github.io/DiscordBot"
DISCORDPY_URL: Final[str] = "https://github.com/Rapptz/discord.py"
LMGTFY_URL: Final[str] = "https://lmgtfy.com"

# Date and time formatting
DATE_TIME_FORMATTER_STR: Final[str] = "%a %b %m %Y %X"
DATE_FORMATTER: Final[str] = "%Y-%m-%d"
TIME_FORMATTER: Final[str] = "%H:%M:%S.%f"

# Games and command configuration
PREFIX: Final[str] = get_bot_settings().prefix
DM_HELP_COMMAND: Final[bool] = True
ALLOWED_PREFIXES: Final[tuple[str, ...]] = ("!", "?", "$", "%", "&", ".")
GAMES_INCLUDED: Final[tuple[str, ...]] = ("Guild Wars 2",)

# Runtime configuration
TIME_BEFORE_START: Final[int] = 0 if DEBUG else 5
INTERACTIVE_MODE: Final[bool] = len(sys.argv) <= 1
IS_WINDOWS: Final[bool] = os.name == "nt"
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent.parent


# Python version validation
def _get_python_version_info() -> tuple[int, int]:
    """Extract required Python version from pyproject.toml."""
    conf_utils = ConfFileUtils()
    python_req = conf_utils.get_value(
        str(BASE_DIR / "pyproject.toml"),
        "tool.poetry.dependencies",
        "python",
    )
    version_parts = python_req.replace("^", "").split(".")
    return int(version_parts[0]), int(version_parts[1])


_PYTHON_MAJOR, _PYTHON_MINOR = _get_python_version_info()
PYTHON_OK: Final[bool] = sys.version_info >= (_PYTHON_MAJOR, _PYTHON_MINOR)

# Project metadata and paths
VERSION: Final[str] = ConfFileUtils().get_value(str(BASE_DIR / "pyproject.toml"), "tool.poetry", "version")

# Configuration file paths
SETTINGS_FILENAME: Final[str] = str(BASE_DIR / "config" / "bot_settings.ini")
ALEMBIC_CONFIG_FILE_PATH: Final[str] = str(BASE_DIR / "config" / "alembic.ini")
DATABASE_FILENAME: Final[str] = str(BASE_DIR / "data" / "database.db")
LOGS_DIR: Final[str] = str(BASE_DIR / "logs")
SQL_DIRPATH: Final[str] = str(BASE_DIR / "data" / "sql")


# Cog discovery and loading order
def _discover_cogs() -> list[str]:
    """Discover and return all cog file paths in the correct loading order."""
    bot_cogs_dir = Path("src") / "bot" / "cogs"
    # Bot cogs - admin.py loads first for command group registration
    bot_cogs = [str(bot_cogs_dir / "admin" / "admin.py")]
    bot_cogs.extend(str(p) for p in bot_cogs_dir.glob("*.py"))
    bot_cogs.extend(str(p) for p in (bot_cogs_dir / "events").glob("*.py"))
    # Add remaining admin cogs (excluding admin.py already added)
    admin_cogs = [str(p) for p in (bot_cogs_dir / "admin").glob("*.py")]
    bot_cogs.extend(cog for cog in admin_cogs if cog not in bot_cogs)

    # GW2 cogs - gw2.py loads first for command group registration
    gw2_cogs_dir = Path("src") / "gw2" / "cogs"
    gw2_cogs = [str(gw2_cogs_dir / "gw2.py")]
    remaining_gw2 = [str(p) for p in gw2_cogs_dir.glob("*.py")]
    gw2_cogs.extend(cog for cog in remaining_gw2 if cog not in gw2_cogs)

    return bot_cogs + gw2_cogs


ALL_COGS: Final[list[str]] = _discover_cogs()
