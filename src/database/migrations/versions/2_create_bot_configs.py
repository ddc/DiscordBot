"""create_table_bot_configs

Revision ID: 2
Revises: 1
Create Date: 2023-11-12 16:50:06.294946

"""
from typing import (
    Sequence,
    Union,
)
from src.bot.constants import variables
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2'
down_revision: Union[str, None] = '1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'bot_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prefix', sa.CHAR(length=1), server_default=variables.DEFAULT_PREFIX, nullable=False),
        sa.Column('author_id', sa.BigInteger(), server_default=variables.AUTHOR_ID, nullable=False),
        sa.Column('url', sa.String(), server_default=variables.BOT_WEBPAGE_URL, nullable=False),
        sa.Column('description', sa.String(), server_default=variables.DESCRIPTION, nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
        )
    op.create_unique_constraint('bot_configs_id_key', 'bot_configs', ['id'])
    op.execute(
        """
                CREATE TRIGGER before_update_bot_configs_tr
                    BEFORE UPDATE ON bot_configs
                    FOR EACH ROW
                    EXECUTE PROCEDURE updated_at_column_func();
            """
        )  # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP TRIGGER IF EXISTS before_update_bot_configs_tr ON bot_configs')
    op.drop_constraint('bot_configs_id_key', 'bot_configs', type_='unique')
    op.drop_table('bot_configs')  # ### end Alembic commands ###
