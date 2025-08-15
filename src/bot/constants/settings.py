from functools import lru_cache
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Lazy loading flag for dotenv
_dotenv_loaded = False


class BotSettings(BaseSettings):
    """settings defined here with fallback to reading ENV variables"""

    prefix: Optional[str] = Field(default="!")
    token: Optional[str] = Field(default=None)
    openai_model: Optional[str] = Field(default="gpt-4o-mini")
    openai_api_key: Optional[str] = Field(default=None)

    # Bot configuration
    bg_activity_timer: Optional[int] = Field(default=0)
    allowed_dm_commands: Optional[str] = Field(default="owner, about, gw2")
    bot_reaction_words: Optional[str] = Field(default="stupid, retard, retarded, noob")
    embed_color: Optional[str] = Field(default="green")
    embed_owner_color: Optional[str] = Field(default="dark_purple")
    exclusive_users: Optional[str] = Field(default="")

    # Cooldowns
    admin_cooldown: Optional[int] = Field(default=20)
    config_cooldown: Optional[int] = Field(default=20)
    custom_cmd_cooldown: Optional[int] = Field(default=20)
    dice_rolls_cooldown: Optional[int] = Field(default=10)
    misc_cooldown: Optional[int] = Field(default=20)
    openai_cooldown: Optional[int] = Field(default=10)
    owner_cooldown: Optional[int] = Field(default=5)

    model_config = SettingsConfigDict(env_prefix="BOT_", env_file=".env", extra="allow")


@lru_cache(maxsize=1)
def get_bot_settings() -> BotSettings:
    """Get cached settings instance to avoid repeated instantiation"""
    global _dotenv_loaded
    if not _dotenv_loaded:
        load_dotenv()
        _dotenv_loaded = True
    return BotSettings()
