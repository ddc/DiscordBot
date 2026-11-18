"""profanity_filters

Revision ID: 0005
Revises: 0004
Create Date: 2024-12-01 15:16:10.742871

"""

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profanity_filters",
        sa.Column[UUID]("id", sa.Uuid[UUID](), nullable=False, server_default=sa.text("uuidv7()")),
        sa.Column[int]("server_id", sa.BigInteger(), nullable=False),
        sa.Column[int]("channel_id", sa.BigInteger(), nullable=False),
        sa.Column[str]("channel_name", sa.String(), nullable=False),
        sa.Column[int]("created_by", sa.BigInteger(), nullable=True),
        sa.Column[datetime]("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column[datetime]("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_profanity_filters_server_id"), "profanity_filters", ["server_id"], unique=False)
    op.execute("""
        CREATE TRIGGER before_update_profanity_filters_tr
            BEFORE UPDATE ON profanity_filters
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS before_update_profanity_filters_tr ON profanity_filters")
    op.drop_index(op.f("ix_profanity_filters_server_id"), table_name="profanity_filters")
    op.drop_table("profanity_filters")
