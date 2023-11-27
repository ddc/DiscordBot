# -*- coding: utf-8 -*-
from discord.ext import commands


class OnGuildChannelUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_guild_channel_update(before, after):
            pass


async def setup(bot):
    await bot.add_cog(OnGuildChannelUpdate(bot))
