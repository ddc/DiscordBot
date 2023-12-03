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
    async def admin(self, ctx):
        """(Admin Commands)

        admin botgame <game>
        admin kick member#1234 reason
        admin ban member#1234 reason
        admin unban member#1234
        admin banlist

        """

        if ctx.invoked_subcommand:
            return ctx.invoked_subcommand
        else:
            if ctx.command is not None:
                cmd = ctx.command
            else:
                cmd = self.bot.get_command("admin")
            await bot_utils.send_help_msg(self, ctx, cmd)

    @admin.command(name="botgame")
    @commands.cooldown(1, CoolDowns.Admin.value, BucketType.user)
    async def botgame(self, ctx, *, game: str):
        """(Change game that bot is playing)

        Example:
        admin botgame <game>
        """

        # bot_utils.delete_channel_message(self, ctx)
        await ctx.message.channel.typing()
        prefix = self.bot.command_prefix[0]
        bot_game_desc = f"{game} | {prefix}help"
        color = self.bot.settings["EmbedOwnerColor"]
        msg = f"```I'm now playing: {game}```"
        await self.bot.change_presence(activity=discord.Game(name=bot_game_desc))

        embed = discord.Embed(color=color)
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar.url)
        embed.description = f"```I'm now playing: {game}```"
        await bot_utils.send_embed(self, ctx, embed, False, msg)

        if self.bot.settings["BGChangeGame"].lower() == "yes":
            bg_task_warning = (f"Background task that update bot activity is ON\n"
                               f"Activity will change after "
                               f"{self.bot.settings['BGActivityTimer']} secs.")
            embed.description = bg_task_warning
            await bot_utils.send_embed(self, ctx, embed, True, msg)


async def setup(bot):
    bot.remove_command("admin")
    await bot.add_cog(Admin(bot))
