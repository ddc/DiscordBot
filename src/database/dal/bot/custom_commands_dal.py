# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.bot_models import CustomCommands


class CustomCommandsDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_command(self, server_id: int, user_id: int, cmd_name: str, description: str):
        stmt = CustomCommands(
           server_id=server_id,
           user_id=user_id,
           name=cmd_name,
           description=description,
        )
        await self.db_utils.add(stmt)

    async def get_all_server_commands(self, server_id: int):
        stmt = select(
            CustomCommands.id,
            CustomCommands.server_id,
            CustomCommands.created_by,
            CustomCommands.name,
            CustomCommands.description,
            CustomCommands.created_at,
            CustomCommands.updated_at
        ).where(
            CustomCommands.server_id == server_id
        ).order_by(
            CustomCommands.name.asc(),
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_command(self, server_id: int, cmd_name: str):
        stmt = select(
            CustomCommands.id,
            CustomCommands.server_id,
            CustomCommands.created_by,
            CustomCommands.name,
            CustomCommands.description,
            CustomCommands.created_at,
            CustomCommands.updated_at,
        ).where(
            CustomCommands.server_id == server_id,
            CustomCommands.name == cmd_name,
        ).order_by(
            CustomCommands.name.asc(),
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def update_command_description(self, server_id: int, cmd_name: str, description: str):
        stmt = sa.update(CustomCommands).where(
            CustomCommands.server_id == server_id,
            CustomCommands.name == cmd_name,
        ).values(
            description=description
        )
        await self.db_utils.execute(stmt)

    async def delete_server_command(self, server_id: int, cmd_name: str):
        stmt = sa.delete(CustomCommands).where(
            CustomCommands.server_id == server_id,
            CustomCommands.name == cmd_name,
        )
        await self.db_utils.execute(stmt)

    async def delete_all_commands(self, server_id: int):
        stmt = sa.delete(CustomCommands).where(
            CustomCommands.server_id == server_id,
        )
        await self.db_utils.execute(stmt)
