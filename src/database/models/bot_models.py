from sqlalchemy import CHAR, BigInteger, Boolean, ForeignKey, Integer, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.bot.constants import variables
from src.database.models import BotBase
from typing import Any
from uuid import UUID
from uuid_utils.compat import uuid7


class BotConfigs(BotBase):
    __tablename__ = "bot_configs"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    prefix: Mapped[CHAR] = mapped_column(CHAR(1), server_default=variables.PREFIX)
    author_id: Mapped[int] = mapped_column(BigInteger, server_default=variables.AUTHOR_ID)
    url: Mapped[str] = mapped_column(server_default=variables.BOT_WEBPAGE_URL)
    description: Mapped[str] = mapped_column(server_default=variables.DESCRIPTION)


class Servers(BotBase):
    __tablename__ = "servers"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=True)
    msg_on_join: Mapped[Boolean] = mapped_column(Boolean, server_default="1")
    msg_on_leave: Mapped[Boolean] = mapped_column(Boolean, server_default="1")
    msg_on_server_update: Mapped[Boolean] = mapped_column(Boolean, server_default="1")
    msg_on_member_update: Mapped[Boolean] = mapped_column(Boolean, server_default="1")
    block_invis_members: Mapped[Boolean] = mapped_column(Boolean, server_default="0")
    bot_word_reactions: Mapped[Boolean] = mapped_column(Boolean, server_default="1")
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)


class CustomCommands(BotBase):
    __tablename__ = "custom_commands"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)


class ProfanityFilters(BotBase):
    __tablename__ = "profanity_filters"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    channel_name: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=True)


class DiceRolls(BotBase):
    __tablename__ = "dice_rolls"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    roll: Mapped[int] = mapped_column()
    dice_size: Mapped[int] = mapped_column()


class EmbedPages(BotBase):
    __tablename__ = "embed_pages"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    message_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    author_id: Mapped[int] = mapped_column(BigInteger)
    current_page: Mapped[int] = mapped_column(Integer, server_default="0")
    pages: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
