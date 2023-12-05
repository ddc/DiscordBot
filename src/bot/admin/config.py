# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.database.dal.bot.profanity_filters_dal import ProfanityFilterDal
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.utils import bot_utils, chat_formatting
from src.bot.utils.cooldowns import CoolDowns
from src.bot.admin.admin import Admin


class Config(Admin):
    """(Admin Config commands)"""
    def __init__(self, bot):
        super().__init__(bot)


@Config.admin.group()
async def config(ctx, subcommand):
    """(Server configurations commands)

    Examples:

    admin config list
    admin config joinmessage     [on | off]
    admin config leavemessage    [on | off]
    admin config servermessage   [on | off]
    admin config membermessage   [on | off]
    admin config blockinvisible  [on | off]
    admin config botreactions    [on | off]
    admin config pfilter         [on | off] <channel_name>
    admin config defaultchannel  <channel_name>
    """

    match subcommand:
        case "joinmessage":
            await config_join_message(ctx)
        case "leavemessage":
            await config_leave_message(ctx)
        case "servermessage":
            await config_server_message(ctx)
        case "membermessage":
            await config_member_message(ctx)
        case "blockinvisible":
            await config_block_invis_members(ctx)
        case "botreactions":
            await config_bot_word_reactions(ctx)
        case "pfilter":
            await config_pfilter(ctx)
        case "defaultchannel":
            await config_default_text_channel(ctx)
        case "list":
            await config_list(ctx)
        case _:
            if ctx.command is not None:
                cmd = ctx.command
            else:
                cmd = ctx.bot.get_command("admin config")
            await bot_utils.send_help_msg(ctx, cmd)


@config.command(name="joinmessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_join_message(ctx):
    """(Show message when a user joins the server)

    Example:
    admin config joinmessage [on | off]
    """

    match ctx.subcommand_passed:
        case "on" | "ON":
            new_status = "Y"
            color = discord.Color.green()
            msg = "Display a message when someone joins the server is now: `ON`"
        case "off" | "OFF":
            new_status = "N"
            color = discord.Color.red()
            msg = "Display a message when someone joins the server is now: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_join(ctx.guild.id, str(new_status), ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="leavemessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_leave_message(ctx):
    """(Show message when a user leaves the server)

    Example:
    admin config leavemessage [on | off]
    """

    match ctx.subcommand_passed:
        case "on | ON":
            new_status = "Y"
            color = discord.Color.green()
            msg = "Display a message when a member leaves the server is now: `ON`"
        case "off | OFF":
            new_status = "N"
            color = discord.Color.red()
            msg = "Display a message when a member leaves the server is now: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_leave(ctx.guild.id, str(new_status), ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="servermessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_server_message(ctx):
    """(Show message when a server gets updated)

    Example:
    admin config servermessage [on | off]
    """

    match ctx.subcommand_passed:
        case "on" | "ON":
            new_status = "Y"
            color = discord.Color.green()
            msg = "Display a message when server gets updated is now: `ON`"
        case "off | OFF":
            new_status = "N"
            color = discord.Color.red()
            msg = "Display a message when server gets updated is now: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_server_update(ctx.guild.id, str(new_status), ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="membermessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_member_message(ctx):
    """(Show message when a member make changes on his/her profile)

    Example:
    admin config membermessage [on | off]
    """

    match ctx.subcommand_passed:
        case "on" | "ON":
            new_status = "Y"
            color = discord.Color.green()
            msg = "Display a message when someone changes profile is now: `ON`"
        case "off | OFF":
            new_status = "N"
            color = discord.Color.red()
            msg = "Display a message when someone changes profile is now: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_member_update(ctx.guild.id, str(new_status), ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="blockinvisible")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_block_invis_members(ctx):
    """(Block messages from invisible members)

    Example:
    admin config blockinvisible [on | off]
    """

    match ctx.subcommand_passed:
        case "on" | "ON":
            new_status = "Y"
            color = discord.Color.green()
            msg = "Block messages from invisible members is now: `ON`"
        case "off | OFF":
            new_status = "N"
            color = discord.Color.red()
            msg = "Block messages from invisible members is now: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_block_invis_members(ctx.guild.id, str(new_status), ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="botreactions")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_bot_word_reactions(ctx):
    """(Bot will react to member words)

    Example:
    admin config botreactions [on | off]
    """

    match ctx.subcommand_passed:
        case "on" | "ON":
            new_status = "Y"
            color = discord.Color.green()
            msg = "Bot Reactions: `ON`"
        case "off | OFF":
            new_status = "N"
            color = discord.Color.red()
            msg = "Bot Reactions: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_bot_word_reactions(ctx.guild.id, str(new_status), ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="defaultchannel")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_default_text_channel(ctx):
    """(Set default text channel to be used for bot messages)

    Example:
    admin config defaultchannel <channel_name>
    """

    text_channel = ctx.subcommand_passed

    if not text_channel:
        return await bot_utils.send_error_msg(ctx, "Missing required channel!!!\n"
                                                   "For more info on this command use: "
                                                   f"{chat_formatting.inline('?help admin config defaultchannel')}")
    elif text_channel not in [x.name for x in ctx.guild.text_channels]:
        return await bot_utils.send_error_msg(ctx, f"Channel not found: {chat_formatting.inline(text_channel)}")
    else:
        msg = "Default text channel to be used for bot messages: "

    color = discord.Color.green()
    embed = discord.Embed(description=f"{msg} {chat_formatting.inline(text_channel)}", color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_default_text_channel(ctx.guild.id, str(text_channel), ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="pfilter")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_pfilter(ctx):
    """(Block offensive words by users)

    Example:
    admin config pfilter [on | off] <channel_name>
    """

    new_status = ctx.subcommand_passed
    text_channel = ctx.message.content.split()[-1]

    if not text_channel:
        return await bot_utils.send_error_msg(ctx, "Missing required channel!!!\n"
                                                   "For more info on this command use: "
                                                   f"{chat_formatting.inline('?help admin config pfilter')}")
    if text_channel not in [x.name for x in ctx.guild.text_channels]:
        return await bot_utils.send_error_msg(ctx, f"Channel not found: {chat_formatting.inline(text_channel)}")

    # get object channel from string
    channel = bot_utils.get_object_channel(ctx, text_channel)
    if channel is None:
        raise commands.BadArgument(message=f"Channel not found: `{text_channel}`")

    embed = discord.Embed()
    profanity_filter_dal = ProfanityFilterDal(ctx.bot.db_session, ctx.bot.log)

    match new_status:
        case "on" | "ON":
            # check if bot has permission to delete messages
            if not ctx.guild.me.guild_permissions.administrator or not ctx.guild.me.guild_permissions.manage_messages:
                msg = ("`Bot does not have permission to delete messages.\n"
                       "Profanity filter could not be activated.\n"
                       "Missing permission: \"Manage Messages\"`")
                return await bot_utils.send_error_msg(ctx, msg)

            embed.color = discord.Color.green()
            embed.description = f"Profanity Filter `ACTIVATED`\nChannel: `{text_channel}`"
            await profanity_filter_dal.insert_profanity_filter_channel(ctx.guild.id, channel.id, channel.name, ctx.author.id)
        case "off" | "OFF":
            embed.color = discord.Color.green()
            embed.description = f"Profanity Filter `DEACTIVATED`\nChannel: `{text_channel}`"
            await profanity_filter_dal.delete_profanity_filter_channel(channel.id)
        case _:
            raise commands.BadArgument(message="BadArgument")

    await bot_utils.send_embed(ctx, embed)


@config.command(name="list")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_list(ctx):
    """(List all bot configurations)

    Example:
    admin config list
    """

    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    sc = await servers_dal.get_server(ctx.guild.id)

    profanity_filter_dal = ProfanityFilterDal(ctx.bot.db_session, ctx.bot.log)
    pf = await profanity_filter_dal.get_all_server_profanity_filter_channels(ctx.guild.id)

    if len(pf) > 0:
        channel_names_lst = [x['channel_name'] for x in pf]
        channel_names = '\n'.join(channel_names_lst)
    else:
        channel_names = "No channels listed"

    on = chat_formatting.green_text("ON")
    off = chat_formatting.red_text("OFF")

    embed = discord.Embed()
    embed.set_thumbnail(url=f"{ctx.guild.icon.url}")
    embed.set_author(name=f"Configurations for {ctx.guild.name}", icon_url=f"{ctx.guild.icon.url}")

    embed.add_field(
        name=f"Display a message when someone joins the server\n*`{ctx.prefix}admin config joinmessage [on | off]`*",
        value=f"{on}" if sc[0]["msg_on_join"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name=f"Display a message when someone leaves the server\n*`{ctx.prefix}admin config leavemessage [on | off]`*",
        value=f"{on}" if sc[0]["msg_on_leave"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name=f"Display a message when the server gets updated\n*`{ctx.prefix}admin config servermessage [on | off]`*",
        value=f"{on}" if sc[0]["msg_on_server_update"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name=f"Display a message when someone changes their profile\n*`{ctx.prefix}admin config membermessage [on | off]`*",
        value=f"{on}" if sc[0]["msg_on_member_update"] == 'Y' else f"{off}", inline=False)
    embed.add_field(name=f"Block messages from invisible members\n*`{ctx.prefix}admin config blockinvisible [on | off]`*",
                    value=f"{on}" if sc[0]["block_invis_members"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name=f"Bot will react to member words\n*`{ctx.prefix}admin config botreactions [on | off]`*",
        value=f"{on}" if sc[0]["bot_word_reactions"] == 'Y' else f"{off}", inline=False)

    default_text_channel = "No default channel"
    if sc[0]["default_text_channel"] is not None and sc[0]["default_text_channel"] != "":
        default_text_channel = sc[0]["default_text_channel"]

    embed.add_field(
        name="Channel to display bot messages\n"
             f"*`{ctx.prefix}config defaultchannel <channel_name>`*",
        value=chat_formatting.inline(default_text_channel), inline=False)
    embed.add_field(
        name="Channels with profanity filter activated",
        value=chat_formatting.inline(channel_names),
        inline=False
    )

    embed.set_footer(text=f"For more info: {ctx.prefix}help admin config")
    await bot_utils.send_embed(ctx, embed, True)


async def setup(bot):
    bot.remove_command("admin")
    await bot.add_cog(Config(bot))
