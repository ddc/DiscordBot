import os
import sys
import tomllib
from pathlib import Path
from pythonlogs import get_log_settings
from src.bot.constants.settings import get_bot_settings
from typing import Final, Literal
lazy from anthropic.types import WebSearchTool20260318Param as ANTHROPIC_WEB_SEARCH_TOOL_PARAM  # noqa: F401
lazy from src.gw2.cogs import discover_gw2_cogs

# Project root (the repository directory)
_base_dir: Final[Path] = Path(__file__).resolve().parent.parent.parent.parent


def _get_python_version_info() -> tuple[int, int]:
    with open(_base_dir / "pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)

    python_req = pyproject_data["project"]["requires-python"]
    version_str = python_req.lstrip("><=!~")
    version_parts = version_str.split(".")
    return int(version_parts[0]), int(version_parts[1])


def _get_project_version() -> str:
    with open(_base_dir / "pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)
    return pyproject_data["project"]["version"]


def _discover_cogs() -> list[str]:
    _init_py: Final[str] = "__init__.py"

    # Bot cogs - admin.py loads first for command group registration
    bot_cogs_dir = Path("src") / "bot" / "cogs"
    bot_cogs = [str(bot_cogs_dir / "admin" / "admin.py")]
    bot_cogs.extend(str(p) for p in bot_cogs_dir.glob("*.py") if p.name != _init_py)
    bot_cogs.extend(str(p) for p in (bot_cogs_dir / "events").glob("*.py") if p.name != _init_py)

    # Add remaining admin cogs (excluding admin.py already added)
    admin_cogs = [str(p) for p in (bot_cogs_dir / "admin").glob("*.py") if p.name != _init_py]
    bot_cogs.extend(cog for cog in admin_cogs if cog not in bot_cogs)

    return bot_cogs + discover_gw2_cogs()


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
DATE_TIME_FORMATTER_STR: Final[str] = "%a %b %d %Y %X"
DATE_FORMATTER: Final[str] = "%Y-%m-%d"
TIME_FORMATTER: Final[str] = "%H:%M:%S.%f"

# Games and command configuration
PREFIX: Final[str] = get_bot_settings().prefix
DM_HELP_COMMAND: Final[bool] = True
ALLOWED_PREFIXES: Final[tuple[str, ...]] = ("!", "?", "$", "%", "&", ".")
GAMES_INCLUDED: Final[tuple[str, ...]] = ("Guild Wars 2",)

# Supported AI models and their providers
AI_MODEL_PROVIDERS: Final[frozendict[str, str]] = frozendict(
    {"claude": "anthropic", "gpt": "openai", "gemini": "gemini"}
)

# HTTP status codes from an AI provider that get one retry (rate limit and server/gateway errors)
AI_PROVIDER_RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset[Literal[429, 500, 502, 503, 504]](
    {429, 500, 502, 503, 504}
)

# Anthropic web search tool used by `claudeweb`
ANTHROPIC_WEB_SEARCH_TOOL: Final = "web_search_20260318"

# Runtime configuration
TIME_BEFORE_START: Final[int] = 0 if DEBUG else 5
INTERACTIVE_MODE: Final[bool] = len(sys.argv) <= 1
IS_WINDOWS: Final[bool] = os.name == "nt"

# Python version validation
_python_major, _python_minor = _get_python_version_info()
PYTHON_OK: Final[bool] = sys.version_info >= (_python_major, _python_minor)

# Project metadata and paths
VERSION: Final[str] = _get_project_version()

# Configuration file paths
ALEMBIC_CONFIG_FILE_PATH: Final[str] = str(_base_dir / "config" / "alembic.ini")
DATABASE_FILENAME: Final[str] = str(_base_dir / "data" / "database.db")
LOGS_DIR: Final[str] = str(_base_dir / "logs")
SQL_DIRPATH: Final[str] = str(_base_dir / "data" / "sql")

# Cog discovery and loading order
ALL_COGS: Final[list[str]] = _discover_cogs()
