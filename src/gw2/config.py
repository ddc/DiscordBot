# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.bot.utils import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal


class GW2Config(commands.Cog):
    """(GW2 configuration commands - Admin)"""
    def __init__(self, bot):
        self.bot = bot

    async def config(self, ctx, sub_command: str):
        err_missing_arg = "Missing required argument!!!\n" \
                          f"For more info on this command use: {ctx.prefix}help {ctx.command}"

        command = str(sub_command.replace(f"{ctx.prefix}gw2 config ", "")).split(' ', 1)[0]
        if command == "list":
            new_status = ctx.message.clean_content.replace(f"{ctx.prefix}gw2 config list", "")
            if len(new_status) > 0:
                raise commands.BadArgument(message="BadArgument")
            await _list(self, ctx)
        elif command == "lastsession":
            new_status = ctx.message.clean_content.replace(f"{ctx.prefix}gw2 config lastsession ", "")
            if new_status == f"{ctx.prefix}gw2 config lastsession":
                await bot_utils.send_error_msg(ctx, err_missing_arg)
                return
            if new_status.lower() != "on" and new_status.lower() != "off":
                raise commands.BadArgument(message="BadArgument")
            await _lastsession(self, ctx, new_status)
        else:
            msg = ("Wrong command.\n"
                   "Command needs to be [list | lastsession | apiroles | serverprefix]\n"
                   "Please try again.")
            await bot_utils.send_error_msg(ctx, msg)


async def _list(self, ctx):
    """(List all gw2 configurations in the current server)

    Example:
    gw2 config list
    """

    color = self.bot.gw2_settings["EmbedColor"]
    embed = discord.Embed(color=color)
    embed.set_thumbnail(url=f"{ctx.message.channel.guild.icon.url}")
    embed.set_author(name=f"Guild Wars 2 configurations for {ctx.message.channel.guild.name}",
                     icon_url=f"{ctx.message.channel.guild.icon.url}")
    embed.set_footer(text=f"For more info: {ctx.prefix}help gw2 config")

    gw2_configs = Gw2ConfigsDal(self.bot.db_session, self.bot.log)
    rs = await gw2_configs.get_gw2_server_configs(ctx.message.channel.guild.id)
    last_session = rs[0]["last_session"] if len(rs) == 0 else False

    on = chat_formatting.green_text("ON")
    off = chat_formatting.red_text("OFF")
    embed.add_field(name="Bot should record gw2 users last sessions",
                    value=f"{on}" if last_session else f"{off}", inline=False)
    await bot_utils.send_embed(ctx, embed, True)


async def _lastsession(self, ctx, new_status: str):
    """(Configure if the bot should record users last sessions)

    Example:
    gw2 config lastsession on
    gw2 config lastsession off
    """

    await ctx.message.channel.typing()
    if new_status.lower() == "on":
        new_status = "Y"
        color = discord.Color.green()
        msg = "Last session `ACTIVATED`\nBot will now record Gw2 users last sessions."
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = "Last session `DEACTIVATED`\nBot will `NOT` record Gw2 users last sessions."
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    gw2_configs = Gw2ConfigsDal(self.bot.db_session, self.bot.log)
    rs = await gw2_configs.get_gw2_server_configs(ctx.message.channel.guild.id)
    if rs[0]["last_session"] != new_status:
        await gw2_configs.update_gw2_last_session(ctx.message.channel.guild.id, new_status)

    await bot_utils.send_embed(ctx, embed)
