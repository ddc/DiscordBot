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
    prefix: str = Field(default="!")
    token: str | None = Field(default=None)
    bg_activity_timer: int = Field(default=0)
    allowed_dm_commands: str = Field(default="owner, about, gw2")
    bot_reaction_words: str = Field(default="stupid, retard, retarded, noob")
    embed_color: str = Field(default="green")
    embed_owner_color: str = Field(default="dark_purple")
    exclusive_users: str = Field(default="")

    # OpenAi
    openai_model: str = Field(default="gpt-5.4", description="https://developers.openai.com/api/docs/models")
    openai_api_key: str | None = Field(default=None)

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
