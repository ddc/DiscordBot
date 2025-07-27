from functools import lru_cache
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Lazy loading flag for dotenv
_dotenv_loaded = False


class Gw2Settings(BaseSettings):
    """GW2 settings defined here with fallback to reading ENV variables"""

    # GW2 configuration
    embed_color: str = Field(default="green")
    
    # GW2 cooldowns
    account_cooldown: int = Field(default=20)
    api_keys_cooldown: int = Field(default=20)
    characters_cooldown: int = Field(default=20)
    config_cooldown: int = Field(default=20)
    daily_cooldown: int = Field(default=20)
    misc_cooldown: int = Field(default=20)
    session_cooldown: int = Field(default=60)
    worlds_cooldown: int = Field(default=20)
    wvw_cooldown: int = Field(default=20)

    model_config = SettingsConfigDict(env_prefix="GW2_", env_file=".env", extra="allow")


@lru_cache(maxsize=1)
def get_gw2_settings() -> Gw2Settings:
    """Get cached GW2 settings instance to avoid repeated instantiation"""
    global _dotenv_loaded
    if not _dotenv_loaded:
        load_dotenv()
        _dotenv_loaded = True
    return Gw2Settings()