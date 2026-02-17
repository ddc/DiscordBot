from discord.ext import commands


class OnGuildChannelDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """
        Called when a channel gets deleted
        :param channel: abc.GuildChannel
        :return: None
        """
        pass


async def setup(bot):
    await bot.add_cog(OnGuildChannelDelete(bot))
