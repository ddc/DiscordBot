"""create_functions

Revision ID: 0001
Revises:
Create Date: 2023-11-22 21:37:13.445078

"""

from alembic import op
from collections.abc import Sequence
from ddcdatabases.postgresql import get_postgresql_settings
from sqlalchemy.schema import CreateSchema, DropSchema

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
db_schema = get_postgresql_settings().schema
_schemas = [s.strip() for s in (db_schema or "public").split(",")]


def upgrade() -> None:
    # This function is responsible for update the column 'updated_at'
    op.execute("""
        CREATE or REPLACE FUNCTION updated_at_column_func()
            RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN
                NEW.updated_at = now() at time zone 'utc';
                return NEW;
            END $$;
    """)
    # Create each non-public schema
    for s in _schemas:
        if s != "public":
            op.execute(CreateSchema(s, if_not_exists=True))


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS updated_at_column_func")
    for s in _schemas:
        if s != "public":
            op.execute(DropSchema(s, if_exists=True, cascade=True))
