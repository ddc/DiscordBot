"""gw2_keys

Revision ID: 0007
Revises: 0006
Create Date: 2024-12-01 15:25:06.158294

"""

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gw2_keys",
        sa.Column[UUID]("id", sa.Uuid[UUID](), nullable=False, server_default=sa.text("uuidv7()")),
        sa.Column[int]("user_id", sa.BigInteger(), nullable=False),
        sa.Column[str]("name", sa.String(), nullable=True),
        sa.Column[str]("gw2_acc_name", sa.String(), nullable=False),
        sa.Column[str]("server", sa.String(), nullable=False),
        sa.Column[str]("permissions", sa.String(), nullable=False),
        sa.Column[str]("key", sa.String(), nullable=False),
        sa.Column[datetime]("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column[datetime]("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("user_id"),
        schema="gw2",
    )
    op.execute("""
        CREATE TRIGGER before_update_gw2_keys_tr
            BEFORE UPDATE ON gw2.gw2_keys
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS before_update_gw2_keys_tr ON gw2.gw2_keys")
    op.drop_table("gw2_keys", schema="gw2")
