import importlib
from datetime import datetime
from pathlib import Path
from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import text


class BotBase(AsyncAttrs, DeclarativeBase):
    """Base model class with common timestamp fields."""

    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("(now() at time zone 'utc')"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("(now() at time zone 'utc')"))


# Auto-import all model modules to register them with SQLAlchemy
for model_file in Path(__file__).parent.glob("*_models.py"):
    importlib.import_module(f"src.database.models.{model_file.stem}")
