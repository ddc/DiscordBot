"""drop unique constraint on gw2_session_chars.name

Revision ID: 0011
Revises: 0010
Create Date: 2026-02-24 00:00:00.000000

"""

from alembic import op
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("gw2_session_chars_name_key", "gw2_session_chars", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("gw2_session_chars_name_key", "gw2_session_chars", ["name"])
