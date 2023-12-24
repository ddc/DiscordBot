# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.bot_models import DiceRolls


class DiceRollsDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_user_roll(self, server_id: int, user_id: int, dice_size: int, roll: int):
        stmt = DiceRolls(
           server_id=server_id,
           user_id=user_id,
           dice_size=dice_size,
           roll=roll,
        )
        await self.db_utils.add(stmt)

    async def update_user_roll(self, server_id: int, user_id: int, dice_size: int, roll: int):
        stmt = sa.update(DiceRolls).where(
            DiceRolls.server_id == server_id,
            DiceRolls.user_id == user_id,
            DiceRolls.dice_size == dice_size,
        ).values(
            roll=roll
        )
        await self.db_utils.execute(stmt)

    async def delete_all_server_rolls(self, server_id: int):
        stmt = sa.delete(DiceRolls).where(DiceRolls.server_id == server_id)
        await self.db_utils.execute(stmt)

    async def get_user_roll_by_dice_size(self, server_id: int, user_id: int, dice_size: int):
        columns = [x for x in DiceRolls.__table__.columns]
        stmt = select(*columns).where(
            DiceRolls.server_id == server_id,
            DiceRolls.user_id == user_id,
            DiceRolls.dice_size == dice_size,
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_user_rolls_all_dice_sizes(self, server_id: int, user_id: int):
        columns = [x for x in DiceRolls.__table__.columns]
        stmt = select(*columns).where(
            DiceRolls.server_id == server_id,
            DiceRolls.user_id == user_id,
        ).order_by(DiceRolls.dice_size.asc())
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_all_server_rolls(self, server_id: int, dice_size: int):
        columns = [x for x in DiceRolls.__table__.columns]
        stmt = select(*columns).where(
            DiceRolls.server_id == server_id,
            DiceRolls.dice_size == dice_size,
        ).order_by(DiceRolls.roll.desc())
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_server_max_roll(self, server_id: int, dice_size: int):
        stmt = select(
            DiceRolls.user_id,
            DiceRolls.roll.label("max_roll"),
        ).where(
            DiceRolls.server_id == server_id,
            DiceRolls.dice_size == dice_size,
        ).order_by(
            DiceRolls.roll.desc()
        ).limit(1)
        results = await self.db_utils.fetchall(stmt)
        return results
