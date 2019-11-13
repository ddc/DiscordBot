#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import math
import discord
from discord.ext import commands
from src.cogs.bot.utils import chat_formatting as Formatting
from src.cogs.bot.utils import bot_utils as BotUtils
from src.cogs.gw2.utils import gw2_utils as Gw2Utils
from src.sql.gw2.gw2_configs_sql import Gw2ConfigsSql
from src.sql.gw2.gw2_roles_sql import Gw2RolesSql
from src.sql.gw2.gw2_key_sql import Gw2KeySql


class GW2Config(commands.Cog):
    """(GW2 configuration commands - Admin)"""

    def __init__(self, bot):
        self.bot = bot

    ################################################################################
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
                await BotUtils.send_error_msg(self, ctx, err_missing_arg)
                return
            if new_status.lower() != "on" and new_status.lower() != "off":
                raise commands.BadArgument(message="BadArgument")
            await _lastsession(self, ctx, new_status)
        elif command == "roletimer":
            role_timer = ctx.message.clean_content.replace(f"{ctx.prefix}gw2 config roletimer ", "")
            if role_timer == f"{ctx.prefix}gw2 config roletimer":
                await BotUtils.send_error_msg(self, ctx, err_missing_arg)
            else:
                await _roletimer(self, ctx, role_timer)
        elif command == "apirole":
            stats_sever = ctx.message.clean_content.replace(f"{ctx.prefix}gw2 config apirole ", "")
            if stats_sever == f"{ctx.prefix}gw2 config apirole":
                await BotUtils.send_error_msg(self, ctx, err_missing_arg)
            else:
                await _apirole(self, ctx, stats_sever)
        else:
            msg = "Wrong command.\nCommand needs to be [list | lastsession | apiroles | serverprefix]\nPlease try again."
            await BotUtils.send_error_msg(self, ctx, msg)


################################################################################
async def _list(self, ctx):
    """(List all gw2 configurations in the current server)
    
    Example:
    gw2 config list
    """

    color = self.bot.gw2_settings["EmbedColor"]
    embed = discord.Embed(color=color)
    embed.set_thumbnail(url=f"{ctx.message.channel.guild.icon_url}")
    embed.set_author(name=f"Guild Wars 2 configurations for {ctx.message.channel.guild.name}",
                     icon_url=f"{ctx.message.channel.guild.icon_url}")
    embed.set_footer(text=f"For more info: {ctx.prefix}help gw2 config")

    gw2Configs = Gw2ConfigsSql(self.bot)
    rs = await gw2Configs.get_gw2_server_configs(ctx.message.channel.guild.id)

    if len(rs) == 0:
        last_session = "N"
        role_timer = f"{self.bot.gw2_settings['BGRoleTimer']} secs (Default)"
    else:
        last_session = rs[0]["last_session"]
        role_timer = f"{rs[0]['role_timer']} secs"

    on = Formatting.green_text("ON")
    off = Formatting.red_text("OFF")
    embed.add_field(name="Bot should record gw2 users last sessions",
                    value=f"{on}" if last_session == "Y" else f"{off}", inline=False)
    embed.add_field(name="Timer the bot should check for api roles in seconds", value=f"{Formatting.box(role_timer)}",
                    inline=False)

    await BotUtils.send_embed(self, ctx, embed, True)


################################################################################
async def _lastsession(self, ctx, new_status: str):
    """(Configure if the bot should record users last sessions)
    
    Example:
    gw2 config lastsession on
    gw2 config lastsession off
    """

    await ctx.message.channel.trigger_typing()
    if new_status.lower() == "on":
        new_status = "Y"
        color = discord.Color.green()
        msg = f"Last session `ACTIVATED`\nBot will now record users last sessions."
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = f"Last session `DEACTIVATED`\nBot will `NOT` record users last sessions."
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    gw2Configs = Gw2ConfigsSql(self.bot)
    rs = await gw2Configs.get_gw2_server_configs(ctx.message.channel.guild.id)
    if len(rs) == 0:
        await gw2Configs.insert_gw2_last_session(ctx.message.channel.guild.id, new_status)
    elif rs[0]["last_session"] != new_status:
        await gw2Configs.update_gw2_last_session(ctx.message.channel.guild.id, new_status)

    await BotUtils.send_embed(self, ctx, embed, False, msg)


################################################################################
async def _roletimer(self, ctx, role_timer: int):
    """(Configure the timer the bot should check for api roles in seconds)
         
    Example:
    gw2 config roletimer 3600
    """

    await ctx.message.channel.trigger_typing()
    err_msg_number = "Wrong option!!!\n" \
                     "Timer must be in seconds and higher than 3600 secs (1hour)."

    try:
        role_timer = int(role_timer)
        if not math.isnan(role_timer):
            if role_timer < 3600:
                await BotUtils.send_error_msg(self, ctx, err_msg_number)
                return
    except Exception:
        await BotUtils.send_error_msg(self, ctx, err_msg_number)
        return

    color = discord.Color.green()
    msg = f"Timer changed to: `{role_timer} seconds`"
    embed = discord.Embed(description=msg, color=color)
    gw2Configs = Gw2ConfigsSql(self.bot)
    rs = await gw2Configs.get_gw2_server_configs(ctx.message.channel.guild.id)
    if len(rs) == 0:
        await gw2Configs.insert_gw2_role_timer(ctx.message.channel.guild.id, role_timer)
    elif int(rs[0]["role_timer"]) != role_timer:
        await gw2Configs.update_gw2_role_timer(ctx.message.channel.guild.id, role_timer)

    await BotUtils.send_embed(self, ctx, embed, False, msg)


################################################################################
async def _apirole(self, ctx, stats_sever: str):
    """(Configure if the bot should add role that matches gw2 servers)
    
    Categories with "Public" names in it wont be affect it.
    
    Example:
    Public Chat
    Public Raids
    Public Informations
    
    Example:
    gw2 config apirole on Blackgate
    gw2 config apirole off Blackgate
    """

    await ctx.message.channel.trigger_typing()
    new_status = stats_sever.split()[0]
    new_server_list = stats_sever.split()[1:]
    new_server = ' '.join(new_server_list)

    if new_status.lower() == "on":
        new_status = "Y"
    elif new_status.lower() == "off":
        new_status = "N"
    else:
        raise commands.BadArgument(message="BadArgument_Gw2ConfigStatus")

    # check gw2 server name passed by user
    correct_gw2_server_name = Gw2Utils.check_gw2_server_name_role(new_server)
    if correct_gw2_server_name is False:
        raise commands.BadArgument(message="BadArgument_Gw2ConfigServer")

    # check if server already has gw2 server role name
    server_has_role_already = BotUtils.check_server_has_role(self, ctx.guild, new_server)

    if new_status == "Y":
        if server_has_role_already is None:
            new_role = await ctx.guild.create_role(name=new_server,
                                                   permissions=discord.Permissions(permissions=116771904))
        else:
            new_role = server_has_role_already

        new_role_overwrites = discord.PermissionOverwrite()
        everyone_role_overwrites = discord.PermissionOverwrite()
        everyone_role = BotUtils.get_server_everyone_role(ctx.guild)

        # hide all text and voice channels from public
        # but the first one and categories with public names in it
        everyone_role_overwrites.read_messages = False
        # text
        new_role_overwrites.add_reactions = True
        new_role_overwrites.attach_files = True
        new_role_overwrites.change_nickname = True
        new_role_overwrites.embed_links = True
        new_role_overwrites.external_emojis = True
        new_role_overwrites.read_message_history = True
        new_role_overwrites.read_messages = True
        new_role_overwrites.send_messages = True
        # voice
        new_role_overwrites.connect = True
        new_role_overwrites.deafen_members = True
        new_role_overwrites.mute_members = True
        new_role_overwrites.speak = True
        new_role_overwrites.use_voice_activation = True

        # assign new role to channels
        role_found = False
        for chan in ctx.guild.channels:
            if isinstance(chan, discord.CategoryChannel):
                if "public" not in chan.name.lower():
                    for rol in chan.overwrites:
                        if rol[0].name.lower() == new_role.name.lower():
                            role_found = True
                            break
                    if role_found is False:
                        await chan.set_permissions(everyone_role, overwrite=everyone_role_overwrites)
                        await chan.set_permissions(new_role, overwrite=new_role_overwrites)
                    role_found = False

        gw2Roles = Gw2RolesSql(self.bot)
        rs = await gw2Roles.get_gw2_server_role(ctx.message.channel.guild.id, new_role.name.lower())
        if len(rs) == 0:
            await gw2Roles.insert_gw2_server_role(ctx.message.channel.guild.id, new_role.name.lower())

        color = discord.Color.green()
        msg = f"Guild Wars 2 API server roles `ACTIVATED`\n" \
              f"Role: `{new_role.name}`\n" \
              f"Members that have Gw2 API key on `{new_role.name}` will now have access to all channels."
        gw2KeySql = Gw2KeySql(self.bot)
        for member in ctx.message.channel.guild.members:
            if not member.bot:
                rs_api_key = await gw2KeySql.get_server_user_api_key(ctx.message.channel.guild.id, member.id)
                if len(rs_api_key) > 0:
                    api_key = rs_api_key[0]["key"]
                    await Gw2Utils.assignGw2GuildRoles(self, ctx, member, new_role, api_key)
    elif new_status == "N":
        color = discord.Color.red()
        if server_has_role_already is None:
            msg = f"Role `{new_server}` not found.\n" \
                  "Please activate that role before trying to deactivate it.\n" \
                  f"{ctx.prefix}gw2 config apirole on {new_server}"
        else:
            new_role = server_has_role_already
            msg = "Guild Wars 2 API server roles `DEACTIVATED`\n" \
                  "Role `REMOVED` from server.\n" \
                  f"Role: `{new_role.name}`"
            gw2Roles = Gw2RolesSql(self.bot)
            await gw2Roles.delete_gw2_server_roles(ctx.message.channel.guild.id, new_role.name.lower())
            for member in ctx.message.channel.guild.members:
                await Gw2Utils.removeGw2RoleFromServer(self, ctx.guild, new_role)

    embed = discord.Embed(description=msg, color=color)
    await BotUtils.send_embed(self, ctx, embed, False, msg)
