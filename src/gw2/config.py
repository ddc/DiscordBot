# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.bot.utils import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal


class GW2Config(commands.Cog):
    """(GW2 configuration commands - Admin)"""
    def __init__(self, bot):
        self.bot = bot

    async def gw2_config(self, ctx, sub_command: str):
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
        # elif command == "roletimer":
        #     role_timer = ctx.message.clean_content.replace(f"{ctx.prefix}gw2 config roletimer ", "")
        #     if role_timer == f"{ctx.prefix}gw2 config roletimer":
        #         await bot_utils.send_error_msg(ctx, err_missing_arg)
        #     else:
        #         await _roletimer(self, ctx, role_timer)
        # elif command == "apirole":
        #     stats_sever = ctx.message.clean_content.replace(f"{ctx.prefix}gw2 config apirole ", "")
        #     if stats_sever == f"{ctx.prefix}gw2 config apirole":
        #         await bot_utils.send_error_msg(ctx, err_missing_arg)
        #     else:
        #         await _apirole(self, ctx, stats_sever)
        else:
            msg = "Wrong command.\nCommand needs to be [list | lastsession | apiroles | serverprefix]\nPlease try again."
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

    gw2Configs = Gw2ConfigsDal(self.bot.db_session, self.bot.log)
    rs = await gw2Configs.get_gw2_server_configs(ctx.message.channel.guild.id)

    if len(rs) == 0:
        last_session = "N"
        # role_timer = f"{self.bot.gw2_settings['BGRoleTimer']} secs (Default)"
    else:
        last_session = rs[0]["last_session"]
        # role_timer = f"{rs[0]['role_timer']} secs"

    on = chat_formatting.green_text("ON")
    off = chat_formatting.red_text("OFF")
    embed.add_field(name="Bot should record gw2 users last sessions",
                    value=f"{on}" if last_session == "Y" else f"{off}", inline=False)
    #embed.add_field(name="Timer the bot should check for api roles in seconds", value=f"{chat_formatting.box(role_timer)}", inline=False)

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
        msg = f"Last session `ACTIVATED`\nBot will now record Gw2 users last sessions."
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = f"Last session `DEACTIVATED`\nBot will `NOT` record Gw2 users last sessions."
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    gw2Configs = Gw2ConfigsDal(self.bot.db_session, self.bot.log)
    rs = await gw2Configs.get_gw2_server_configs(ctx.message.channel.guild.id)
    if len(rs) == 0:
        # role_timer = self.bot.gw2_settings["BGRoleTimer"]
        role_timer = 1 # removed role timer
        await gw2Configs.insert_gw2_last_session(ctx.message.channel.guild.id, new_status, role_timer)
    elif rs[0]["last_session"] != new_status:
        await gw2Configs.update_gw2_last_session(ctx.message.channel.guild.id, new_status)

    await bot_utils.send_embed(ctx, embed)
