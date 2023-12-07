# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import ForeignKey, BigInteger, Boolean, DateTime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import text
from src.database.models.bot_models import Servers


class Gw2Base(AsyncAttrs, DeclarativeBase):
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("(now() at time zone 'utc')"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("(now() at time zone 'utc')"))


class Gw2Configs(Gw2Base):
    __tablename__ = "gw2_configs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), unique=True)
    last_session: Mapped[Boolean] = mapped_column(Boolean, default=False)
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    servers = relationship(Servers, foreign_keys="Gw2Configs.server_id")


class Gw2Keys(Gw2Base):
    __tablename__ = "gw2_keys"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(nullable=True)
    gw2_acc_name: Mapped[str] = mapped_column()
    server_name: Mapped[str] = mapped_column()
    permissions: Mapped[str] = mapped_column()
    key: Mapped[str] = mapped_column()
    servers = relationship(Servers, foreign_keys="Gw2Keys.server_id")


class Gw2CharsStart(Gw2Base):
    __tablename__ = "gw2_chars_start"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(unique=True)
    profession: Mapped[str] = mapped_column()
    deaths: Mapped[int] = mapped_column()


class Gw2CharsEnd(Gw2Base):
    __tablename__ = "gw2_chars_end"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(unique=True)
    profession: Mapped[str] = mapped_column()
    deaths: Mapped[int] = mapped_column()


class Gw2Sessions(Gw2Base):
    __tablename__ = "gw2_sessions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    acc_name: Mapped[str] = mapped_column()
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    start_wvw_rank: Mapped[int] = mapped_column()
    end_wvw_rank: Mapped[int] = mapped_column(nullable=True)
    start_gold: Mapped[int] = mapped_column()
    end_gold: Mapped[int] = mapped_column(nullable=True)
    start_karma: Mapped[int] = mapped_column()
    end_karma: Mapped[int] = mapped_column(nullable=True)
    start_laurels: Mapped[int] = mapped_column()
    end_laurels: Mapped[int] = mapped_column(nullable=True)
    start_badges_honor: Mapped[int] = mapped_column()
    end_badges_honor: Mapped[int] = mapped_column(nullable=True)
    start_guild_commendations: Mapped[int] = mapped_column()
    end_guild_commendations: Mapped[int] = mapped_column(nullable=True)
    start_wvw_tickets: Mapped[int] = mapped_column()
    end_wvw_tickets: Mapped[int] = mapped_column(nullable=True)
    start_proof_heroics: Mapped[int] = mapped_column()
    end_proof_heroics: Mapped[int] = mapped_column(nullable=True)
    start_test_heroics: Mapped[int] = mapped_column()
    end_test_heroics: Mapped[int] = mapped_column(nullable=True)
    start_players: Mapped[int] = mapped_column()
    end_players: Mapped[int] = mapped_column(nullable=True)
    start_yaks_scorted: Mapped[int] = mapped_column()
    end_yaks_scorted: Mapped[int] = mapped_column(nullable=True)
    start_yaks: Mapped[int] = mapped_column()
    end_yaks: Mapped[int] = mapped_column(nullable=True)
    start_camps: Mapped[int] = mapped_column()
    end_camps: Mapped[int] = mapped_column(nullable=True)
    start_castles: Mapped[int] = mapped_column()
    end_castles: Mapped[int] = mapped_column(nullable=True)
    start_towers: Mapped[int] = mapped_column()
    end_towers: Mapped[int] = mapped_column(nullable=True)
    start_keeps: Mapped[int] = mapped_column()
    end_keeps: Mapped[int] = mapped_column(nullable=True)
