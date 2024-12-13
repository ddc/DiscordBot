# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.tools import bot_utils, chat_formatting
from src.bot.tools.checks import Checks
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns
from src.gw2.constants import gw2_messages


class GW2Config(GuildWars2):
    """(Guild Wars 2 Configuration Commands - Admin)"""
    def __init__(self, bot):
        super().__init__(bot)


@GW2Config.gw2.group()
@Checks.check_is_admin()
async def config(ctx):
    """(Guild Wars 2 Configuration Commands - Admin)
            gw2 config list
            gw2 config session [on | off]
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 config")


@config.command(name="list")
@commands.cooldown(1, GW2CoolDowns.Config.value, BucketType.user)
async def config_list(ctx):
    """(List all Guild Wars 2 Current Server Configurations)
            gw2 config list
    """

    color = ctx.bot.settings["gw2"]["EmbedColor"]
    embed = discord.Embed(color=color)
    embed.set_thumbnail(url=f"{ctx.message.channel.guild.icon.url}")
    embed.set_author(name=f"{gw2_messages.CONFIG_TITLE} {ctx.message.channel.guild.name}",
                     icon_url=f"{ctx.message.channel.guild.icon.url}")
    embed.set_footer(text=gw2_messages.CONFIG_MORE_INFO.format(ctx.prefix))

    gw2_configs = Gw2ConfigsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await gw2_configs.get_gw2_server_configs(ctx.message.channel.guild.id)
    on = chat_formatting.green_text("ON")
    off = chat_formatting.red_text("OFF")
    embed.add_field(name=gw2_messages.USER_SESSION_TITLE, value=f"{on}" if rs[0]["session"] else f"{off}", inline=False)
    await bot_utils.send_embed(ctx, embed, dm=True)


@config.command(name="session")
@commands.cooldown(1, GW2CoolDowns.Config.value, BucketType.user)
async def config_session(ctx, subcommand_passed: str):
    """(Configure Guild Wars 2 Sessions)
        gw2 config session on
        gw2 config session off
    """

    match subcommand_passed:
        case "on" | "ON":
            new_status = True
            color = discord.Color.green()
            msg = gw2_messages.SESSION_ACTIVATED
        case "off" | "OFF":
            new_status = False
            color = discord.Color.red()
            msg = gw2_messages.SESSION_DEACTIVATED
        case _:
            raise commands.BadArgument(message="BadArgument")

    await ctx.message.channel.typing()
    embed = discord.Embed(description=msg, color=color)
    gw2_configs = Gw2ConfigsDal(ctx.bot.db_session, ctx.bot.log)
    await gw2_configs.update_gw2_session_config(ctx.message.channel.guild.id, new_status, ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Config(bot))
