from dotenv import load_dotenv
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

# Lazy loading flag for dotenv
_dotenv_loaded = False


class BotSettings(BaseSettings):
    """settings defined here with fallback to reading ENV variables"""

    model_config = SettingsConfigDict(env_prefix="BOT_", env_file=".env", extra="allow")

    # Bot
    prefix: str = Field(default="!")
    token: str | None = Field(default=None)
    bg_activity_timer: int = Field(default=0)
    allowed_dm_commands: str = Field(default="owner, about, gw2")
    bot_reaction_words: str = Field(default="stupid, retard, retarded, noob")
    embed_color: str = Field(default="green")
    embed_owner_color: str = Field(default="dark_purple")
    exclusive_users: str = Field(default="")

    # Default model for `ai` and `aiweb` commands
    default_ai_model: Literal["claude", "gpt", "gemini"] = Field(
        default="gpt", description="Model used by `ai` / `aiweb`: claude, gpt or gemini"
    )

    # OpenAI
    openai_model: str = Field(default="gpt-6.2-astra", description="https://developers.openai.com/api/docs/models")
    openai_api_key: str | None = Field(default=None)

    # Anthropic (Claude)
    anthropic_model: str = Field(
        default="claude-fable-5-2", description="https://docs.anthropic.com/en/docs/about-claude/models"
    )
    anthropic_api_key: str | None = Field(default=None)

    # Google (Gemini)
    gemini_model: str = Field(default="gemini-flash-latest", description="https://ai.google.dev/gemini-api/docs/models")
    gemini_api_key: str | None = Field(default=None)

    @field_validator("default_ai_model", mode="before")
    @classmethod
    def _normalize_default_ai_model(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    # Cooldowns
    admin_cooldown: int = Field(default=20)
    config_cooldown: int = Field(default=20)
    custom_cmd_cooldown: int = Field(default=20)
    dice_rolls_cooldown: int = Field(default=10)
    misc_cooldown: int = Field(default=20)
    openai_cooldown: int = Field(default=10)
    owner_cooldown: int = Field(default=5)

    # Alembic migration settings
    alembic_version_table_name: str = Field(default="alembic_version")


@lru_cache(maxsize=1)
def get_bot_settings() -> BotSettings:
    """Get cached settings instance to avoid repeated instantiation"""
    global _dotenv_loaded
    if not _dotenv_loaded:
        load_dotenv()
        _dotenv_loaded = True
    return BotSettings()
