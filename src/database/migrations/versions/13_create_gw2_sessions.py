"""create_gw2_sessions

Revision ID: 13
Revises: 12
Create Date: 2023-11-13 18:22:23.282929

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13'
down_revision: Union[str, None] = '12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gw2_sessions',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('acc_name', sa.String(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('start_wvw_rank', sa.Integer(), nullable=False),
    sa.Column('end_wvw_rank', sa.Integer(), nullable=True),
    sa.Column('start_gold', sa.Integer(), nullable=False),
    sa.Column('end_gold', sa.Integer(), nullable=True),
    sa.Column('start_karma', sa.Integer(), nullable=False),
    sa.Column('end_karma', sa.Integer(), nullable=True),
    sa.Column('start_laurels', sa.Integer(), nullable=False),
    sa.Column('end_laurels', sa.Integer(), nullable=True),
    sa.Column('start_badges_honor', sa.Integer(), nullable=False),
    sa.Column('end_badges_honor', sa.Integer(), nullable=True),
    sa.Column('start_guild_commendations', sa.Integer(), nullable=False),
    sa.Column('end_guild_commendations', sa.Integer(), nullable=True),
    sa.Column('start_wvw_tickets', sa.Integer(), nullable=False),
    sa.Column('end_wvw_tickets', sa.Integer(), nullable=True),
    sa.Column('start_proof_heroics', sa.Integer(), nullable=False),
    sa.Column('end_proof_heroics', sa.Integer(), nullable=True),
    sa.Column('start_test_heroics', sa.Integer(), nullable=False),
    sa.Column('end_test_heroics', sa.Integer(), nullable=True),
    sa.Column('start_players', sa.Integer(), nullable=False),
    sa.Column('end_players', sa.Integer(), nullable=True),
    sa.Column('start_yaks_scorted', sa.Integer(), nullable=False),
    sa.Column('end_yaks_scorted', sa.Integer(), nullable=True),
    sa.Column('start_yaks', sa.Integer(), nullable=False),
    sa.Column('end_yaks', sa.Integer(), nullable=True),
    sa.Column('start_camps', sa.Integer(), nullable=False),
    sa.Column('end_camps', sa.Integer(), nullable=True),
    sa.Column('start_castles', sa.Integer(), nullable=False),
    sa.Column('end_castles', sa.Integer(), nullable=True),
    sa.Column('start_towers', sa.Integer(), nullable=False),
    sa.Column('end_towers', sa.Integer(), nullable=True),
    sa.Column('start_keeps', sa.Integer(), nullable=False),
    sa.Column('end_keeps', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_unique_constraint(None, 'gw2_sessions', ['id'])
    op.execute("""
        CREATE TRIGGER before_update_gw2_sessions_tr
            BEFORE UPDATE ON gw2_sessions
            FOR EACH ROW
            EXECUTE PROCEDURE updated_at_column_func();
    """)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP TRIGGER IF EXISTS before_update_gw2_sessions_tr ON bot_configs')
    op.drop_constraint(None, 'gw2_sessions', type_='unique')
    op.drop_table('gw2_sessions')
    # ### end Alembic commands ###