# -*- coding: utf-8 -*-
import sys
from datetime import datetime
import discord
from discord.ext import commands
from src.bot.utils import bot_utils, constants
from src.database.dal.bot.servers_dal import ServersDal


class OnReady(commands.Cog):
    def __init__(self, bot):
        @bot.event
        async def on_ready():
            # check for any missing server in database
            servers_dal = ServersDal(bot.db_session, bot.log)
            db_servers = await servers_dal.get_server()
            db_server_ids = tuple(x["id"] for x in db_servers)
            for server in bot.guilds:
                if server.id not in db_server_ids:
                    await bot_utils.insert_default_initial_configs(bot, server)

            bot_stats = bot_utils.get_bot_stats(bot)
            bot.start_time = datetime.now()

            print(f"\n{20*'='}\nDiscord Bot v{constants.VERSION}\n{20*'='}")
            print("Python v{}.{}.{}".format(*sys.version_info[:3]))
            print(f"Discord API v{discord.__version__}")
            print("--------------------")
            print(f"{bot.user} (id:{bot.user.id})")
            print(f"Prefix: {bot.command_prefix}")
            print(f"Servers: {bot_stats['servers']}")
            print(f"Users: {bot_stats['users']}")
            print(f"Channels: {bot_stats['channels']}")
            print("--------------------")
            print(f"{bot.start_time.strftime('%c')}")
            bot.log.info(f"====> {bot.user} IS ONLINE AND CONNECTED TO DISCORD <====")


async def setup(bot):
    await bot.add_cog(OnReady(bot))
