# -*- coding: utf-8 -*-
import sys
import discord
from discord.ext import commands
from src.bot.utils import bot_utils, constants


class OnReady(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_ready():
            bot_stats = bot_utils.get_bot_stats(bot)
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
            print(f"{bot_utils.get_current_date_time_str_long()}")
            bot.log.info(f"====> {bot.user} IS ONLINE AND CONNECTED TO DISCORD <====")


async def setup(bot):
    await bot.add_cog(OnReady(bot))
