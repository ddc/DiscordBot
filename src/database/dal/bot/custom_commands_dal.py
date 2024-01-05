# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils_async import DBUtilsAsync
from src.database.models.bot_models import CustomCommands


class CustomCommandsDal:
    def __init__(self, db_session, log):
        self.columns = [x for x in CustomCommands.__table__.columns]
        self.db_utils = DBUtilsAsync(db_session, log)

    async def insert_command(self, server_id: int, user_id: int, cmd_name: str, description: str):
        stmt = CustomCommands(
           server_id=server_id,
           created_by=user_id,
           name=cmd_name,
           description=description,
        )
        await self.db_utils.add(stmt)

    async def update_command_description(self, server_id: int, user_id: int, cmd_name: str, description: str):
        stmt = sa.update(CustomCommands).where(
            CustomCommands.server_id == server_id,
            CustomCommands.name == cmd_name,
        ).values(
            description=description,
            updated_by=user_id
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

    async def get_all_server_commands(self, server_id: int):
        stmt = (select(*self.columns)
                .where(CustomCommands.server_id == server_id)
                .order_by(CustomCommands.name.asc()))
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_command(self, server_id: int, cmd_name: str):
        stmt = select(*self.columns).where(
            CustomCommands.server_id == server_id,
            CustomCommands.name == cmd_name,
        ).order_by(CustomCommands.name.asc())
        results = await self.db_utils.fetchone(stmt)
        return results
