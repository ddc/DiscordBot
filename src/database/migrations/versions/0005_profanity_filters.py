"""profanity_filters

Revision ID: 0005
Revises: 0004
Create Date: 2024-12-01 15:16:10.742871

"""

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profanity_filters",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("server_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_name", sa.String(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
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
