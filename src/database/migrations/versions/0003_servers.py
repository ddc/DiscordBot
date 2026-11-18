"""servers

Revision ID: 0003
Revises: 0002
Create Date: 2024-12-01 15:15:41.059350

"""

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "servers",
        sa.Column[int]("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column[str]("name", sa.String(), nullable=True),
        sa.Column[bool]("msg_on_join", sa.Boolean(), server_default="1", nullable=False),
        sa.Column[bool]("msg_on_leave", sa.Boolean(), server_default="1", nullable=False),
        sa.Column[bool]("msg_on_server_update", sa.Boolean(), server_default="1", nullable=False),
        sa.Column[bool]("msg_on_member_update", sa.Boolean(), server_default="1", nullable=False),
        sa.Column[bool]("block_invis_members", sa.Boolean(), server_default="0", nullable=False),
        sa.Column[bool]("bot_word_reactions", sa.Boolean(), server_default="1", nullable=False),
        sa.Column[int]("updated_by", sa.BigInteger(), nullable=True),
        sa.Column[datetime]("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column[datetime]("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.execute("""
        CREATE TRIGGER before_update_servers_tr
            BEFORE UPDATE ON servers
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS before_update_servers_tr ON servers")
    op.drop_table("servers")
