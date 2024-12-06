# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import text
from src.database.models.bot_models import Servers


class Gw2Base(AsyncAttrs, DeclarativeBase):
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("(now() at time zone 'utc')"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("(now() at time zone 'utc')"))


class Gw2Keys(Gw2Base):
    __tablename__ = "gw2_keys"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(nullable=True)
    gw2_acc_name: Mapped[str] = mapped_column()
    server: Mapped[str] = mapped_column()
    permissions: Mapped[str] = mapped_column()
    key: Mapped[str] = mapped_column()


class Gw2Configs(Gw2Base):
    __tablename__ = "gw2_configs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), unique=True)
    session: Mapped[Boolean] = mapped_column(Boolean, server_default="0")
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    servers = relationship(Servers, foreign_keys="Gw2Configs.server_id")


class Gw2Sessions(Gw2Base):
    __tablename__ = "gw2_sessions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    acc_name: Mapped[str] = mapped_column()
    start: Mapped[str] = mapped_column(JSONB)
    end: Mapped[str] = mapped_column(JSONB, nullable=True)


class Gw2SessionChars(Gw2Base):
    __tablename__ = "gw2_session_chars"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Gw2Sessions.id))
    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(unique=True)
    profession: Mapped[str] = mapped_column()
    deaths: Mapped[int] = mapped_column()
    start: Mapped[Boolean] = mapped_column(Boolean)
    end: Mapped[Boolean] = mapped_column(Boolean, nullable=True)
