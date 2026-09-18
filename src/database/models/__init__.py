import importlib
from datetime import datetime
from pathlib import Path
from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BotBase(AsyncAttrs, DeclarativeBase):
    """Base model class with common timestamp fields."""

    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.timezone("utc", func.now()))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.timezone("utc", func.now()))


# Auto-import all model modules to register them with SQLAlchemy
for model_file in Path(__file__).parent.glob("*_models.py"):
    importlib.import_module(f"src.database.models.{model_file.stem}")
