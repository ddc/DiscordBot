"""gw2_keys

Revision ID: 0007
Revises: 0006
Create Date: 2024-12-01 15:25:06.158294

"""

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gw2_keys",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("gw2_acc_name", sa.String(), nullable=False),
        sa.Column("server", sa.String(), nullable=False),
        sa.Column("permissions", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
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
