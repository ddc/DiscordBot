# -*- coding: utf-8 -*-
from sqlalchemy.future import select
from src.database.db_utils import DBUtils
from src.database.models.gw2_models import Gw2SessionChars


class Gw2SessionCharsDal:
    def __init__(self, db_session, log):
        self.db_session = db_session
        self.log = log
        self.columns = [x for x in Gw2SessionChars.__table__.columns]
        self.db_utils = DBUtils(self.db_session, self.log)

    async def insert_session_char(self, gw2_api, api_characters, insert_args: dict):
        for char_name in api_characters:
            uri = f"characters/{char_name}/core"
            current_char = await gw2_api.call_api(uri, insert_args["api_key"])
            name = current_char["name"]
            profession = current_char["profession"]
            deaths = current_char["deaths"]

            stmt = Gw2SessionChars(
               session_id=insert_args["session_id"],
               user_id=insert_args["user_id"],
               name=name,
               profession=profession,
               deaths=deaths,
            )
            self.db_session.add(stmt)
        await self.db_session.commit()

    async def get_all_start_characters(self, user_id: int):
        stmt = select(*self.columns).where(Gw2SessionChars.user_id == user_id, Gw2SessionChars.start is True)
        results = await self.db_utils.fetchall(stmt)
        return results

    async def get_all_end_characters(self, user_id: int):
        stmt = select(*self.columns).where(Gw2SessionChars.user_id == user_id, Gw2SessionChars.end is True)
        results = await self.db_utils.fetchall(stmt)
        return results
