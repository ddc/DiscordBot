# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.databases.databases import Databases


class Gw2CharsStartSql:
    def __init__(self, bot):
        self.bot = bot


    async def insert_character(self, insert_obj: object, api_req_characters):
        sql = ""
        discord_user_id = insert_obj.discord_user_id
        for char_name in api_req_characters:
            if insert_obj.ctx is not None:
                await insert_obj.ctx.message.channel.trigger_typing()
            endpoint = f"characters/{char_name}/core"
            current_char = await insert_obj.gw2Api.call_api(endpoint, key=insert_obj.api_key)
            name = current_char["name"]
            profession = current_char["profession"]
            deaths = current_char["deaths"]
            sql += f"""INSERT INTO gw2_chars_start (
                        discord_user_id
                        ,name
                        ,profession
                        ,deaths
                    )VALUES(
                    {discord_user_id},
                    '{name}',
                    '{profession}',
                    '{deaths}');"""
        databases = Databases(self.bot)
        await databases.execute(sql)


    async def get_all_start_characters(self, discord_user_id: int):
        sql = f"SELECT * FROM gw2_chars_start WHERE discord_user_id = {discord_user_id};\n"
        databases = Databases(self.bot)
        return await databases.select(sql)
