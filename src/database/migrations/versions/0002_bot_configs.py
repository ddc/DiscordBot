"""bot_configs

Revision ID: 0002
Revises: 0001
Create Date: 2024-12-01 15:15:07.594600

"""

import sqlalchemy as sa
from alembic import op
from collections.abc import Sequence
from src.bot.constants import variables

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bot_configs",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("prefix", sa.CHAR(length=1), server_default=variables.PREFIX, nullable=False),
        sa.Column("author_id", sa.BigInteger(), server_default=variables.AUTHOR_ID, nullable=False),
        sa.Column("url", sa.String(), server_default=variables.BOT_WEBPAGE_URL, nullable=False),
        sa.Column("description", sa.String(), server_default=variables.DESCRIPTION, nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO bot_configs (prefix, author_id, url, description) "
            "VALUES (:prefix, :author_id, :url, :description)"
        ).bindparams(
            prefix=variables.PREFIX,
            author_id=int(variables.AUTHOR_ID),
            url=variables.BOT_WEBPAGE_URL,
            description=variables.DESCRIPTION,
        )
    )
    op.execute("""
        CREATE TRIGGER before_update_bot_configs_tr
            BEFORE UPDATE ON bot_configs
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS before_update_bot_configs_tr ON bot_configs")
    op.drop_table("bot_configs")
