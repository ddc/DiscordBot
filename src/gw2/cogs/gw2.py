from discord.ext import commands
from src.bot.tools import bot_utils


class GuildWars2(commands.Cog):
    """Guild Wars 2 commands for account management, WvW, and wiki search."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="gw2")
    async def gw2(self, ctx):
        """Guild Wars 2 commands.

        Available subcommands:
            gw2 config list - List all GW2 configurations
            gw2 config session [on | off] - Toggle session recording
            gw2 wvw [match | info | kdr] <world> - WvW match information
            gw2 key [add | update | info] <api_key> - Manage API keys
            gw2 key remove - Remove your API key
            gw2 account - Show account information
            gw2 characters - Show character information
            gw2 session - Show last game session
            gw2 worlds [na | eu] - List all worlds
            gw2 wiki <search> - Search the GW2 wiki
            gw2 info <search> - Info about a name/skill/rune
        """

        await bot_utils.invoke_subcommand(ctx, "gw2")


async def setup(bot):
    await bot.add_cog(GuildWars2(bot))
