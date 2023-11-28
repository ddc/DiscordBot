"""create_gw2_configs

Revision ID: 11
Revises: 10
Create Date: 2023-11-13 17:53:15.516358

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11'
down_revision: Union[str, None] = '10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gw2_configs',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('server_id', sa.BigInteger(), nullable=False),
    sa.Column('last_session', sa.CHAR(length=1), server_default='N', nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
    sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('server_id')
    )
    op.create_unique_constraint(None, 'gw2_configs', ['id'])
    op.execute("""
        CREATE TRIGGER before_update_gw2_configs_tr
            BEFORE UPDATE ON gw2_configs
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP TRIGGER IF EXISTS before_update_gw2_configs_tr ON bot_configs')
    op.drop_constraint(None, 'gw2_configs', type_='unique')
    op.drop_table('gw2_configs')
    # ### end Alembic commands ###