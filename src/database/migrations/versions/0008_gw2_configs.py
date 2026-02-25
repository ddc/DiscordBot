"""gw2_configs

Revision ID: 0008
Revises: 0007
Create Date: 2024-12-01 15:25:21.853020

"""

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gw2_configs",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("server_id", sa.BigInteger(), nullable=False),
        sa.Column("session", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.ForeignKeyConstraint(["server_id"], ["public.servers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("server_id"),
        schema="gw2",
    )
    op.execute("""
        CREATE TRIGGER before_update_gw2_configs_tr
            BEFORE UPDATE ON gw2.gw2_configs
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS before_update_gw2_configs_tr ON gw2.gw2_configs")
    op.drop_table("gw2_configs", schema="gw2")
