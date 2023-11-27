"""create_gw2_keys

Revision ID: 12
Revises: 11
Create Date: 2023-11-13 17:54:14.919397

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12'
down_revision: Union[str, None] = '11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gw2_keys',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('server_id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('gw2_acc_name', sa.String(), nullable=False),
    sa.Column('server_name', sa.String(), nullable=False),
    sa.Column('permissions', sa.String(), nullable=False),
    sa.Column('key', sa.String(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
    sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_unique_constraint(None, 'gw2_keys', ['id'])
    op.execute("""
        CREATE TRIGGER before_update_gw2_keys_tr
            BEFORE UPDATE ON gw2_keys
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP TRIGGER IF EXISTS before_update_gw2_keys_tr ON bot_configs')
    op.drop_constraint(None, 'gw2_keys', type_='unique')
    op.drop_table('gw2_keys')
    # ### end Alembic commands ###
