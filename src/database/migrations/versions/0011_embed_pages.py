"""embed_pages

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-28 18:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "embed_pages",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("current_page", sa.Integer(), server_default="0", nullable=False),
        sa.Column("pages", JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("message_id"),
    )
    op.create_index(op.f("ix_embed_pages_message_id"), "embed_pages", ["message_id"], unique=True)
    op.execute("""
        CREATE TRIGGER before_update_embed_pages_tr
            BEFORE UPDATE ON embed_pages
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS before_update_embed_pages_tr ON embed_pages")
    op.drop_index(op.f("ix_embed_pages_message_id"), table_name="embed_pages")
    op.drop_table("embed_pages")
