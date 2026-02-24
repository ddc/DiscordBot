from sqlalchemy import BigInteger, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.models import BotBase
from src.database.models.bot_models import Servers
from typing import Any


class Gw2Keys(BotBase):
    __tablename__ = "gw2_keys"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(nullable=True)
    gw2_acc_name: Mapped[str] = mapped_column()
    server: Mapped[str] = mapped_column()
    permissions: Mapped[str] = mapped_column()
    key: Mapped[str] = mapped_column()


class Gw2Configs(BotBase):
    __tablename__ = "gw2_configs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), unique=True)
    session: Mapped[Boolean] = mapped_column(Boolean, server_default="0")
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    servers = relationship("Servers", back_populates="gw2_configs")


class Gw2Sessions(BotBase):
    __tablename__ = "gw2_sessions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    acc_name: Mapped[str] = mapped_column()
    start: Mapped[dict[str, Any]] = mapped_column(JSONB)
    end: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    session_chars = relationship("Gw2SessionChars", back_populates="session")


class Gw2SessionChars(BotBase):
    __tablename__ = "gw2_session_chars"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Gw2Sessions.id))
    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column()
    profession: Mapped[str] = mapped_column()
    deaths: Mapped[int] = mapped_column()
    start: Mapped[Boolean] = mapped_column(Boolean)
    end: Mapped[Boolean] = mapped_column(Boolean, nullable=True)
    session = relationship("Gw2Sessions", back_populates="session_chars")
