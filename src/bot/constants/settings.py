from dotenv import load_dotenv
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Lazy loading flag for dotenv
_dotenv_loaded = False


class BotSettings(BaseSettings):
    """settings defined here with fallback to reading ENV variables"""

    model_config = SettingsConfigDict(env_prefix="BOT_", env_file=".env", extra="allow")

    # Bot
    prefix: str | None = Field(default="!")
    token: str | None = Field(default=None)
    bg_activity_timer: int | None = Field(default=0)
    allowed_dm_commands: str | None = Field(default="owner, about, gw2")
    bot_reaction_words: str | None = Field(default="stupid, retard, retarded, noob")
    embed_color: str | None = Field(default="green")
    embed_owner_color: str | None = Field(default="dark_purple")
    exclusive_users: str | None = Field(default="")

    # OpenAi
    openai_model: str | None = Field(default="gpt-4o-mini")
    openai_api_key: str | None = Field(default=None)

    # Cooldowns
    admin_cooldown: int | None = Field(default=20)
    config_cooldown: int | None = Field(default=20)
    custom_cmd_cooldown: int | None = Field(default=20)
    dice_rolls_cooldown: int | None = Field(default=10)
    misc_cooldown: int | None = Field(default=20)
    openai_cooldown: int | None = Field(default=10)
    owner_cooldown: int | None = Field(default=5)

    # Alembic migration settings
    alembic_version_table_name: str | None = Field(default="alembic_version")


@lru_cache(maxsize=1)
def get_bot_settings() -> BotSettings:
    """Get cached settings instance to avoid repeated instantiation"""
    global _dotenv_loaded
    if not _dotenv_loaded:
        load_dotenv()
        _dotenv_loaded = True
    return BotSettings()
