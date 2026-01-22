from discord.ext import commands


class OnGuildChannelDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_guild_channel_delete(channel):
            """
            Called when a channel gets deleted
            :param channel: abc.GuildChannel
            :return: None
            """
            pass


async def setup(bot):
    await bot.add_cog(OnGuildChannelDelete(bot))
