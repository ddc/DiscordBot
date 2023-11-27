"""insert_default_bot_configs

Revision ID: 3
Revises: 2
Create Date: 2023-11-12 18:03:55.035037

"""
from typing import Sequence, Union
from src.bot.utils import constants
from alembic import op
import sqlalchemy as sa
from src.database.models.bot_models import BotConfigs

revision: str = '3'
down_revision: Union[str, None] = '2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.insert(BotConfigs).values(
            id=1,
            prefix=constants.DEFAULT_PREFIX,
            author_id=constants.AUTHOR_ID,
            url=constants.BOT_WEBPAGE_URL,
            description=constants.DESCRIPTION
        )
    )


def downgrade() -> None:
    op.execute(
        sa.delete(BotConfigs).where(id=1)
    )
