# -*- encoding: utf-8 -*-
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """ settings defined here with fallback to reading ENV variables """
    load_dotenv()

    prefix: Optional[str] = Field(default="!")
    token: Optional[str] = Field(default=None)

    openai_model: Optional[str] = Field(default="gpt-4o-mini")

    model_config = SettingsConfigDict(env_prefix="BOT_", env_file=".env", extra="allow")
