"""create_triggers_bot_configs

Revision ID: 4
Revises: 3
Create Date: 2023-11-12 18:04:32.246416

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '4'
down_revision: Union[str, None] = '3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
            CREATE or REPLACE FUNCTION before_insert_bot_configs_func()
                RETURNS TRIGGER LANGUAGE plpgsql AS $$
                BEGIN
                    RAISE unique_violation USING MESSAGE = 'CANNOT INSERT INTO BOT_CONFIGS TABLE ANYMORE';
                    return null;
                END $$;
            CREATE TRIGGER before_insert_bot_configs_tr
                BEFORE INSERT ON bot_configs
                FOR EACH ROW
                EXECUTE PROCEDURE before_insert_bot_configs_func();
            ------
            CREATE or REPLACE FUNCTION before_update_author_id_func()
                RETURNS TRIGGER LANGUAGE plpgsql AS $$
                BEGIN
                    RAISE unique_violation USING MESSAGE = 'CANNOT CHANGE BOT AUTHOR ID.';
                    return null;
                END $$;
            CREATE TRIGGER before_update_author_id_tr
                BEFORE UPDATE ON bot_configs
                FOR EACH ROW
                WHEN (OLD.author_id IS DISTINCT FROM NEW.author_id)
                EXECUTE PROCEDURE before_update_author_id_func();
            ------
            CREATE or REPLACE FUNCTION before_update_bot_url_func()
                RETURNS TRIGGER LANGUAGE plpgsql AS $$
                BEGIN
                    RAISE unique_violation USING MESSAGE = 'CANNOT CHANGE BOT URL.';
                    return null;
                END $$;
            CREATE TRIGGER before_update_bot_url_tr
                BEFORE UPDATE ON bot_configs
                FOR EACH ROW
                WHEN (OLD.url IS DISTINCT FROM NEW.url)
                EXECUTE PROCEDURE before_update_bot_url_func();
    """)


def downgrade() -> None:
    op.execute("""
        DROP TRIGGER IF EXISTS before_insert_bot_configs_tr ON bot_configs;
        DROP FUNCTION IF EXISTS before_insert_bot_configs_func;
        
        DROP TRIGGER IF EXISTS before_update_author_id_tr ON bot_configs;
        DROP FUNCTION IF EXISTS before_update_author_id_func;
        
        DROP TRIGGER IF EXISTS before_update_bot_url_tr ON bot_configs;
        DROP FUNCTION IF EXISTS before_update_bot_url_func;
    """)
