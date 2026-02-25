from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.models import BotBase
from typing import Any
from uuid import UUID
from uuid_utils import uuid7


class Gw2Keys(BotBase):
    __tablename__ = "gw2_keys"
    __table_args__ = {"schema": "gw2"}
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(nullable=True)
    gw2_acc_name: Mapped[str] = mapped_column()
    server: Mapped[str] = mapped_column()
    permissions: Mapped[str] = mapped_column()
    key: Mapped[str] = mapped_column()


class Gw2Configs(BotBase):
    __tablename__ = "gw2_configs"
    __table_args__ = {"schema": "gw2"}
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("servers.id", ondelete="CASCADE"), unique=True)
    session: Mapped[Boolean] = mapped_column(Boolean, server_default="0")
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    servers = relationship(
        "Servers",
        back_populates="gw2_configs",
        primaryjoin="foreign(Gw2Configs.server_id) == Servers.id",
    )


class Gw2Sessions(BotBase):
    __tablename__ = "gw2_sessions"
    __table_args__ = {"schema": "gw2"}
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    user_id: Mapped[int] = mapped_column(BigInteger)
    acc_name: Mapped[str] = mapped_column()
    start: Mapped[dict[str, Any]] = mapped_column(JSONB)
    end: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    session_char_deaths = relationship("Gw2SessionCharDeaths", back_populates="session")


class Gw2SessionCharDeaths(BotBase):
    __tablename__ = "gw2_session_char_deaths"
    __table_args__ = {"schema": "gw2"}
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    session_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("gw2.gw2_sessions.id"))
    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column()
    profession: Mapped[str] = mapped_column()
    start: Mapped[int] = mapped_column(Integer)
    end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session = relationship("Gw2Sessions", back_populates="session_char_deaths")
