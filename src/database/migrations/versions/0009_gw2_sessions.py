"""gw2_sessions

Revision ID: 0009
Revises: 0008
Create Date: 2024-12-01 15:25:38.088952

"""

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gw2_sessions",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("acc_name", sa.String(), nullable=False),
        sa.Column("start", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("end", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        schema="gw2",
    )
    op.execute("""
        CREATE TRIGGER before_update_gw2_sessions_tr
            BEFORE UPDATE ON gw2.gw2_sessions
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS before_update_gw2_sessions_tr ON gw2.gw2_sessions")
    op.drop_table("gw2_sessions", schema="gw2")
