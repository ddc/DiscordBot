# -*- coding: utf-8 -*-
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.gw2_models import Gw2CharsStart


class Gw2CharsStartDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_character(self, insert_obj: object, api_req_characters):
        user_id = insert_obj.user_id
        for char_name in api_req_characters:
            if insert_obj.ctx is not None:
                await insert_obj.ctx.message.channel.typing()

            endpoint = f"characters/{char_name}/core"
            current_char = await insert_obj.gw2Api.call_api(endpoint, key=insert_obj.api_key)
            name = current_char["name"]
            profession = current_char["profession"]
            deaths = current_char["deaths"]

            stmt = Gw2CharsStart(
               user_id=user_id,
               name=name,
               profession=profession,
               deaths=deaths,
            )
            self.db_session.add(stmt)
        await self.db_session.commit()

    async def get_all_start_characters(self, user_id: int):
        stmt = select(
            Gw2CharsStart.id,
            Gw2CharsStart.user_id,
            Gw2CharsStart.name,
            Gw2CharsStart.profession,
            Gw2CharsStart.deaths,
            Gw2CharsStart.created_at,
            Gw2CharsStart.updated_at,
        ).where(
            Gw2CharsStart.user_id == user_id,
        )

        results = await self.db_utils.fetchall(stmt)
        return results