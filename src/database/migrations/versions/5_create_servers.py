"""create_servers

Revision ID: 5
Revises: 4
Create Date: 2023-11-12 17:37:26.691023

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5'
down_revision: Union[str, None] = '4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'servers',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('msg_on_join', sa.Boolean(), nullable=False, server_default="1"),
        sa.Column('msg_on_leave', sa.Boolean(), nullable=False, server_default="1"),
        sa.Column('msg_on_server_update', sa.Boolean(), nullable=False, server_default="1"),
        sa.Column('msg_on_member_update', sa.Boolean(), nullable=False, server_default="1"),
        sa.Column('block_invis_members', sa.Boolean(), nullable=False, server_default="0"),
        sa.Column('bot_word_reactions', sa.Boolean(), nullable=False, server_default="1"),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(now() at time zone \'utc\')'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(now() at time zone \'utc\')'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )
    op.create_index(op.f('ix_servers_id'), 'servers', ['id'], unique=True)
    op.execute("""
        CREATE TRIGGER before_update_servers_tr
            BEFORE UPDATE ON servers
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP TRIGGER IF EXISTS before_update_servers_tr ON servers')
    op.drop_index(op.f('ix_servers_id'), table_name='servers')
    op.drop_table('servers')
    # ### end Alembic commands ###
