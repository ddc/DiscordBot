# -*- coding: utf-8 -*-
import sqlalchemy as sa
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.gw2_models import Gw2Sessions, Gw2CharsStart, Gw2CharsEnd


class Gw2SessionsDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def get_user_last_session(self, user_id: int):
        stmt = select(
            Gw2Sessions.id,
            Gw2Sessions.user_id,
            Gw2Sessions.acc_name,
            Gw2Sessions.start_date,
            Gw2Sessions.end_date,
            Gw2Sessions.start_wvw_rank,
            Gw2Sessions.end_wvw_rank,
            Gw2Sessions.start_gold,
            Gw2Sessions.end_gold,
            Gw2Sessions.start_karma,
            Gw2Sessions.end_karma,
            Gw2Sessions.start_laurels,
            Gw2Sessions.end_laurels,
            Gw2Sessions.start_badges_honor,
            Gw2Sessions.end_badges_honor,
            Gw2Sessions.start_guild_commendations,
            Gw2Sessions.end_guild_commendations,
            Gw2Sessions.start_wvw_tickets,
            Gw2Sessions.end_wvw_tickets,
            Gw2Sessions.start_proof_heroics,
            Gw2Sessions.end_proof_heroics,
            Gw2Sessions.start_test_heroics,
            Gw2Sessions.end_test_heroics,
            Gw2Sessions.start_players,
            Gw2Sessions.end_players,
            Gw2Sessions.start_yaks_scorted,
            Gw2Sessions.end_yaks_scorted,
            Gw2Sessions.start_yaks,
            Gw2Sessions.end_yaks,
            Gw2Sessions.start_camps,
            Gw2Sessions.end_camps,
            Gw2Sessions.start_castles,
            Gw2Sessions.end_castles,
            Gw2Sessions.start_towers,
            Gw2Sessions.end_towers,
            Gw2Sessions.start_keeps,
            Gw2Sessions.end_keeps,
            Gw2Sessions.created_at,
            Gw2Sessions.updated_at,
        ).where(
            Gw2Sessions.user_id == user_id,
        )
        results = await self.db_utils.fetchall(stmt)
        return results

    async def insert_start_session(self, user_stats: object):
        async with self.db_session.begin():
            stmt = sa.delete(Gw2Sessions).where(Gw2Sessions.user_id == user_stats.user_id,)
            await self.db_utils.execute(stmt)

            stmt = sa.delete(Gw2CharsStart).where(Gw2CharsStart.user_id == user_stats.user_id,)
            await self.db_utils.execute(stmt)

            stmt = sa.delete(Gw2CharsEnd).where(Gw2CharsEnd.user_id == user_stats.user_id,)
            await self.db_utils.execute(stmt)

            stmt = Gw2Sessions(
                user_id=user_stats.user_id,
                acc_name=user_stats.acc_name,
                start_date=user_stats.date,
                start_wvw_rank=user_stats.wvw_rank,
                start_gold=user_stats.gold,
                start_karma=user_stats.karma,
                start_laurels=user_stats.laurels,
                start_badges_honor=user_stats.badges_honor,
                start_guild_commendations=user_stats.guild_commendations,
                start_wvw_tickets=user_stats.wvw_tickets,
                start_proof_heroics=user_stats.proof_heroics,
                start_test_heroics=user_stats.test_heroics,
                start_players=user_stats.players,
                start_yaks_scorted=user_stats.yaks_scorted,
                start_yaks=user_stats.yaks,
                start_camps=user_stats.camps,
                start_castles=user_stats.castles,
                start_towers=user_stats.towers,
                start_keeps=user_stats.keeps,
            )
            await self.db_utils.add(stmt)

    async def update_end_session(self, user_stats: object):
        stmt = sa.update(Gw2Sessions).where(
            Gw2Sessions.user_id == user_stats.user_id,
        ).values(
            end_date=user_stats.date,
            end_wvw_rank=user_stats.wvw_rank,
            end_gold=user_stats.gold,
            end_karma=user_stats.karma,
            end_laurels=user_stats.laurels,
            end_badges_honor=user_stats.badges_honor,
            end_guild_commendations=user_stats.guild_commendations,
            end_wvw_tickets=user_stats.wvw_tickets,
            end_proof_heroics=user_stats.proof_heroics,
            end_test_heroics=user_stats.test_heroics,
            end_players=user_stats.players,
            end_yaks_scorted=user_stats.yaks_scorted,
            end_yaks=user_stats.yaks,
            end_camps=user_stats.camps,
            end_castles=user_stats.castles,
            end_towers=user_stats.towers,
            end_keeps=user_stats.keeps,
        )
        await self.db_utils.execute(stmt)
