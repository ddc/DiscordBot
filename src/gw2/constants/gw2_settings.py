from dotenv import load_dotenv
from functools import lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Lazy loading flag for dotenv
_dotenv_loaded = False


class Gw2Settings(BaseSettings):
    """GW2 settings defined here with fallback to reading ENV variables"""

    model_config = SettingsConfigDict(env_prefix="GW2_", env_file=".env", extra="allow")

    # GW2 configuration
    api_version: int | None = Field(default=2)
    embed_color: str | None = Field(default="green")

    # GW2 cooldowns
    account_cooldown: int | None = Field(default=20)
    api_keys_cooldown: int | None = Field(default=20)
    characters_cooldown: int | None = Field(default=20)
    config_cooldown: int | None = Field(default=20)
    daily_cooldown: int | None = Field(default=20)
    misc_cooldown: int | None = Field(default=20)
    session_cooldown: int | None = Field(default=60)
    worlds_cooldown: int | None = Field(default=20)
    wvw_cooldown: int | None = Field(default=20)

    # GW2 API retry
    api_retry_max_attempts: int | None = Field(default=5)
    api_retry_delay: float | None = Field(default=3.0)
    api_session_retry_bg_delay: float | None = Field(default=30.0)
    api_session_end_delay: float | None = Field(default=180.0)

    @model_validator(mode="after")
    def _clamp_session_end_delay(self) -> Gw2Settings:
        if self.api_session_end_delay is not None and self.api_session_end_delay < 180.0:
            self.api_session_end_delay = 180.0
        return self


@lru_cache(maxsize=1)
def get_gw2_settings() -> Gw2Settings:
    """Get cached GW2 settings instance to avoid repeated instantiation"""
    global _dotenv_loaded
    if not _dotenv_loaded:
        load_dotenv()
        _dotenv_loaded = True
    return Gw2Settings()
