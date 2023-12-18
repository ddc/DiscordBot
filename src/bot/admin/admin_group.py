# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.utils import bot_utils
from src.bot.utils.checks import Checks
from src.bot.utils.cooldowns import CoolDowns


class Admin(commands.Cog):
    """(Admin commands)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["mod"])
    @Checks.check_is_admin()
    async def admin_group(self, ctx):
        """(Admin Commands)
            admin botgame <game>
        """
        await bot_utils.invoke_subcommand(ctx, "admin")

    @admin_group.command(name="botgame")
    @commands.cooldown(1, CoolDowns.Admin.value, BucketType.user)
    async def botgame(self, ctx, *, game: str):
        """(Change game that bot is playing)
            admin botgame <game>
        """

        prefix = self.bot.command_prefix[0]
        bot_game_desc = f"{game} | {prefix}help"
        await self.bot.change_presence(activity=discord.Game(name=bot_game_desc))

        embed = discord.Embed(description=f"```I'm now playing: {game}```")
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar.url)
        await bot_utils.send_embed(ctx, embed)

        if self.bot.settings["bot"]["BGChangeGame"].lower() == "yes":
            bg_task_warning = (f"Background task running to update bot activity is ON\n"
                               f"Activity will change after "
                               f"{self.bot.settings['bot']['BGActivityTimer']} secs.")
            embed.description = bg_task_warning
            await bot_utils.send_embed(ctx, embed, True)


async def setup(bot):
    await bot.add_cog(Admin(bot))
