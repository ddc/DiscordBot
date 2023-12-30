# -*- coding: utf-8 -*-
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.gw2_models import Gw2CharsStart


class Gw2CharsStartDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_character(self, ctx, gw2_api, api_req_characters, insert_args: dict):
        for char_name in api_req_characters:
            if ctx is not None:
                await ctx.message.channel.typing()

            uri = f"characters/{char_name}/core"
            current_char = await gw2_api.call_api(uri, insert_args["api_key"])
            name = current_char["name"]
            profession = current_char["profession"]
            deaths = current_char["deaths"]

            stmt = Gw2CharsStart(
               user_id=insert_args["user_id"],
               name=name,
               profession=profession,
               deaths=deaths,
            )
            self.db_session.add(stmt)
        await self.db_session.commit()

    async def get_all_start_characters(self, user_id: int):
        columns = [x for x in Gw2CharsStart.__table__.columns]
        stmt = select(*columns).where(Gw2CharsStart.user_id == user_id)
        results = await self.db_utils.fetchall(stmt)
        return results
