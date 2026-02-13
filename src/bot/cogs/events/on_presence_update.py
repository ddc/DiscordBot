from discord.ext import commands
from src.gw2.tools import gw2_utils


class OnPresenceUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        """
        Called when a Member updates their presence.
        This is called when one or more of the following things change:
            status
            activity
        :param before: discord.Member
        :param after: discord.Member
        :return: None
        """
        if after.bot:
            return

        await gw2_utils.check_gw2_game_activity(self.bot, before, after)


async def setup(bot):
    await bot.add_cog(OnPresenceUpdate(bot))
