# -*- coding: utf-8 -*-
from discord.ext import commands


class OnDisconnect(commands.Cog):
    def __init__(self, bot):
        @bot.event
        async def on_disconnect():
            """
                Called when the client has disconnected from Discord,
                or a connection attempt to Discord has failed.
                This could happen either through the internet being disconnected,
                explicit calls to close, or Discord terminating the connection one way or the other.
            """
            pass


async def setup(bot):
    await bot.add_cog(OnDisconnect(bot))
