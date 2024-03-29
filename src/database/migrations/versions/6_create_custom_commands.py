"""create_custom_commands

Revision ID: 6
Revises: 5
Create Date: 2023-11-12 17:47:05.174772

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6'
down_revision: Union[str, None] = '5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'custom_commands',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('server_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
        )
    op.create_unique_constraint('custom_commands_id_key', 'custom_commands', ['id'])
    op.create_index(op.f('ix_custom_commands_server_id'), 'custom_commands', ['server_id'], unique=False)
    op.execute("""
        CREATE TRIGGER before_update_custom_commands_tr
            BEFORE UPDATE ON custom_commands
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP TRIGGER IF EXISTS before_update_custom_commands_tr ON custom_commands')
    op.drop_index(op.f('ix_custom_commands_server_id'), table_name='custom_commands')
    op.drop_constraint('custom_commands_id_key', 'custom_commands', type_='unique')
    op.drop_table('custom_commands')
    # ### end Alembic commands ###
