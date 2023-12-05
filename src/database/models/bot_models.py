# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import ForeignKey, BigInteger, CHAR, CheckConstraint, DateTime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import text
from src.bot.utils import constants


class BotBase(AsyncAttrs, DeclarativeBase):
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("(now() at time zone 'utc')"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("(now() at time zone 'utc')"))


class BotConfigs(BotBase):
    __tablename__ = "bot_configs"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    prefix: Mapped[CHAR] = mapped_column(CHAR(1), server_default=constants.DEFAULT_PREFIX)
    author_id: Mapped[int] = mapped_column(BigInteger, server_default=constants.AUTHOR_ID)
    url: Mapped[str] = mapped_column(server_default=constants.BOT_WEBPAGE_URL)
    description: Mapped[str] = mapped_column(server_default=constants.DESCRIPTION)
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)


class Servers(BotBase):
    __tablename__ = "servers"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True, index=True)
    name: Mapped[str] = mapped_column(nullable=True)
    msg_on_join: Mapped[CHAR] = mapped_column(CHAR(1), server_default="Y")
    msg_on_leave: Mapped[CHAR] = mapped_column(CHAR(1), server_default="Y")
    msg_on_server_update: Mapped[CHAR] = mapped_column(CHAR(1), server_default="Y")
    msg_on_member_update: Mapped[CHAR] = mapped_column(CHAR(1), server_default="Y")
    block_invis_members: Mapped[CHAR] = mapped_column(CHAR(1), server_default="N")
    bot_word_reactions: Mapped[CHAR] = mapped_column(CHAR(1), server_default="Y")
    default_text_channel: Mapped[str] = mapped_column(nullable=True)
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    CheckConstraint("msg_on_join IN ('Y','N')", name="check_msg_on_join_y_n")
    CheckConstraint("msg_on_leave IN ('Y','N')", name="check_msg_on_leave_y_n")
    CheckConstraint("msg_on_server_update IN ('Y','N')", name="check_msg_on_server_update_y_n")
    CheckConstraint("msg_on_member_update IN ('Y','N')", name="check_msg_on_member_update_y_n")
    CheckConstraint("block_invis_members IN ('Y','N')", name="check_block_invis_members_y_n")
    CheckConstraint("bot_word_reactions IN ('Y','N')", name="check_bot_word_reactions_y_n")


class CustomCommands(BotBase):
    __tablename__ = "custom_commands"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    servers = relationship(Servers, foreign_keys="CustomCommands.server_id")


class ProfanityFilters(BotBase):
    __tablename__ = "profanity_filters"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    channel_name: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    servers = relationship(Servers, foreign_keys="ProfanityFilters.server_id")


class DiceRolls(BotBase):
    __tablename__ = "dice_rolls"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    roll: Mapped[int] = mapped_column()
    dice_size: Mapped[int] = mapped_column()
    servers = relationship(Servers, foreign_keys="DiceRolls.server_id")
