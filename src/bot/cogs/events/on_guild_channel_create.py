from discord.ext import commands


class OnGuildChannelCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """
        Called when a channel gets created
        :param channel: abc.GuildChannel
        :return: None
        """
        pass


async def setup(bot):
    await bot.add_cog(OnGuildChannelCreate(bot))
