"""gw2_sessions

Revision ID: 0009
Revises: 0008
Create Date: 2024-12-01 15:25:38.088952

"""

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence
from datetime import datetime
from sqlalchemy.dialects import postgresql
from typing import Any
from uuid import UUID

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gw2_sessions",
        sa.Column[UUID]("id", sa.Uuid[UUID](), nullable=False, server_default=sa.text("uuidv7()")),
        sa.Column[int]("user_id", sa.BigInteger(), nullable=False),
        sa.Column[str]("acc_name", sa.String(), nullable=False),
        sa.Column[dict[str, Any]]("start", postgresql.JSONB[dict[str, Any]](astext_type=sa.Text()), nullable=False),
        sa.Column[dict[str, Any]]("end", postgresql.JSONB[dict[str, Any]](astext_type=sa.Text()), nullable=True),
        sa.Column[datetime]("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column[datetime]("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
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
