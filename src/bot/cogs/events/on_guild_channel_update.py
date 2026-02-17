from discord.ext import commands


class OnGuildChannelUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """
        Called when a channel gets updated
        :param before: abc.GuildChannel
        :param after: abc.GuildChannel
        :return: None
        """
        pass


async def setup(bot):
    await bot.add_cog(OnGuildChannelUpdate(bot))
