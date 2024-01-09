# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.constants import messages
from src.bot.tools import bot_utils
from src.bot.tools.checks import Checks
from src.bot.tools.cooldowns import CoolDowns


class Admin(commands.Cog):
    """(Admin Commands)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["mod"])
    @Checks.check_is_admin()
    async def admin(self, ctx):
        """(Admin Commands)
                admin botgame <game>
        """

        await bot_utils.invoke_subcommand(ctx, "admin")

    @admin.command(name="botgame")
    @commands.cooldown(1, CoolDowns.Admin.value, BucketType.user)
    async def botgame(self, ctx, *, game: str):
        """(Change game that bot is playing)
                admin botgame <game>
        """

        prefix = self.bot.command_prefix[0]
        bot_game_desc = f"{game} | {prefix}help"
        await self.bot.change_presence(activity=discord.Game(name=bot_game_desc))

        embed = discord.Embed(description=f"```{messages.BOT_ANNOUNCE_PLAYING.format(game)}```")
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar.url)
        await bot_utils.send_embed(ctx, embed)

        bg_activity_timer = self.bot.settings["bot"]["BGActivityTimer"]
        if bg_activity_timer and bg_activity_timer > 0:
            bg_task_warning = messages.BG_TASK_WARNING.format(bg_activity_timer)
            embed.description = bg_task_warning
            await bot_utils.send_embed(ctx, embed, False)


async def setup(bot):
    await bot.add_cog(Admin(bot))
