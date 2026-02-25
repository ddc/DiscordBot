from sqlalchemy import CHAR, BigInteger, Boolean, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.bot.constants import variables
from src.database.models import BotBase
from uuid import UUID
from uuid_utils import uuid7


class BotConfigs(BotBase):
    __tablename__ = "bot_configs"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    prefix: Mapped[CHAR] = mapped_column(CHAR(1), server_default=variables.PREFIX)
    author_id: Mapped[int] = mapped_column(BigInteger, server_default=variables.AUTHOR_ID)
    url: Mapped[str] = mapped_column(server_default=variables.BOT_WEBPAGE_URL)
    description: Mapped[str] = mapped_column(server_default=variables.DESCRIPTION)


class Servers(BotBase):
    __tablename__ = "servers"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(nullable=True)
    msg_on_join: Mapped[Boolean] = mapped_column(Boolean, server_default="1")
    msg_on_leave: Mapped[Boolean] = mapped_column(Boolean, server_default="1")
    msg_on_server_update: Mapped[Boolean] = mapped_column(Boolean, server_default="1")
    msg_on_member_update: Mapped[Boolean] = mapped_column(Boolean, server_default="1")
    block_invis_members: Mapped[Boolean] = mapped_column(Boolean, server_default="0")
    bot_word_reactions: Mapped[Boolean] = mapped_column(Boolean, server_default="1")
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)

    # Relationships
    custom_commands = relationship("CustomCommands", back_populates="servers")
    profanity_filters = relationship("ProfanityFilters", back_populates="servers")
    dice_rolls = relationship("DiceRolls", back_populates="servers")
    gw2_configs = relationship(
        "Gw2Configs",
        back_populates="servers",
        primaryjoin="foreign(Gw2Configs.server_id) == Servers.id",
    )


class CustomCommands(BotBase):
    __tablename__ = "custom_commands"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    servers = relationship("Servers", back_populates="custom_commands")


class ProfanityFilters(BotBase):
    __tablename__ = "profanity_filters"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    channel_name: Mapped[str] = mapped_column()
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    servers = relationship("Servers", back_populates="profanity_filters")


class DiceRolls(BotBase):
    __tablename__ = "dice_rolls"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    server_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(Servers.id, ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    roll: Mapped[int] = mapped_column()
    dice_size: Mapped[int] = mapped_column()
    servers = relationship("Servers", back_populates="dice_rolls")
