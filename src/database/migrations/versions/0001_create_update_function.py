"""create_update_function

Revision ID: 0001
Revises:
Create Date: 2023-11-22 21:37:13.445078

"""

from typing import Sequence, Union
from alembic import op


revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    This function is responsible for update the column 'updated_at'
    """
    op.execute(
        """
        CREATE or REPLACE FUNCTION updated_at_column_func()
            RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN
                NEW.updated_at = now() at time zone 'utc';
                return NEW;
            END $$;
    """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS updated_at_column_func")
