# -*- coding: utf-8 -*-
from discord.ext import commands


class OnCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_command(ctx):
            pass


async def setup(bot):
    await bot.add_cog(OnCommand(bot))
