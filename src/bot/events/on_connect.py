# -*- coding: utf-8 -*-
from discord.ext import commands
from src.bot.tools import bot_utils
from src.database.dal.bot.servers_dal import ServersDal


class OnConnect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_connect():
            """
                Called when the client has successfully connected to Discord.
                This is not the same as the client being fully prepared, see on_ready() for that.
            """

            # check for any missing server in database
            servers_dal = ServersDal(bot.db_session, bot.log)
            db_servers = await servers_dal.get_server()
            db_server_ids = tuple(x["id"] for x in db_servers)
            async for guild in bot.fetch_guilds(limit=None):
                if guild.id not in db_server_ids:
                    await bot_utils.insert_server(bot, guild)


async def setup(bot):
    await bot.add_cog(OnConnect(bot))
