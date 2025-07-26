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

    model_config = SettingsConfigDict(env_prefix="BOT_", env_file=".env", extra="allow")


@lru_cache(maxsize=1)
def get_bot_settings() -> BotSettings:
    """Get cached settings instance to avoid repeated instantiation"""
    global _dotenv_loaded
    if not _dotenv_loaded:
        load_dotenv()
        _dotenv_loaded = True
    return BotSettings()
