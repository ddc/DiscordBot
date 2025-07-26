from discord.ext import commands
from src.bot.tools import bot_utils


class GuildWars2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="gw2")
    async def gw2(self, ctx):
        """(Guild Wars 2 Commands)
            gw2 config list
            gw2 config session [on | off]
            gw2 wvw [match | info | kdr] world_name
            gw2 key [add | remove | info] api_key
            gw2 account
            gw2 worlds
            gw2 wiki name_to_search
            gw2 info info_to_search
        """

        await bot_utils.invoke_subcommand(ctx, "gw2")


async def setup(bot):
    await bot.add_cog(GuildWars2(bot))
