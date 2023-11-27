# -*- coding: utf-8 -*-
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal


class OnGuildRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_guild_remove(guild):
            servers_sql = ServersDal(self.bot.db_session, self.bot.log)
            await servers_sql.delete_server(guild)


async def setup(bot):
    await bot.add_cog(OnGuildRemove(bot))
