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
    """(Admin Config Commands)"""
    def __init__(self, bot):
        super().__init__(bot)


@Config.admin.group()
async def config(ctx):
    """(Server configurations commands)
        admin config list
        admin config joinmessage     [on | off]
        admin config leavemessage    [on | off]
        admin config servermessage   [on | off]
        admin config membermessage   [on | off]
        admin config blockinvisible  [on | off]
        admin config botreactions    [on | off]
        admin config pfilter         [on | off] <channel_id>
    """

    await bot_utils.invoke_subcommand(ctx, "admin config")


@config.command(name="joinmessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_join_message(ctx, *, status: str):
    """(Show message when a user joins the server)
            admin config joinmessage on
            admin config joinmessage off
    """

    match status:
        case "on" | "ON":
            new_status = True
            color = discord.Color.green()
            msg = "Display a message when someone joins the server is now: `ON`"
        case "off" | "OFF":
            new_status = False
            color = discord.Color.red()
            msg = "Display a message when someone joins the server is now: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    await ctx.message.channel.typing()
    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_join(ctx.guild.id, new_status, ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="leavemessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_leave_message(ctx, *, status: str):
    """(Show message when a user leaves the server)
            admin config leavemessage on
            admin config leavemessage off
    """

    match status:
        case "on | ON":
            new_status = True
            color = discord.Color.green()
            msg = "Display a message when a member leaves the server is now: `ON`"
        case "off | OFF":
            new_status = False
            color = discord.Color.red()
            msg = "Display a message when a member leaves the server is now: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_leave(ctx.guild.id, new_status, ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="servermessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_server_message(ctx, *, status: str):
    """(Show message when a server gets updated)
            admin config servermessage on
            admin config servermessage off
    """

    match status:
        case "on" | "ON":
            new_status = True
            color = discord.Color.green()
            msg = "Display a message when server gets updated is now: `ON`"
        case "off | OFF":
            new_status = False
            color = discord.Color.red()
            msg = "Display a message when server gets updated is now: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_server_update(ctx.guild.id, new_status, ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="membermessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_member_message(ctx, *, status: str):
    """(Show message when a member make changes on his/her profile)
            admin config membermessage on
            admin config membermessage off
    """

    match status:
        case "on" | "ON":
            new_status = True
            color = discord.Color.green()
            msg = "Display a message when someone changes profile is now: `ON`"
        case "off | OFF":
            new_status = False
            color = discord.Color.red()
            msg = "Display a message when someone changes profile is now: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_member_update(ctx.guild.id, new_status, ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="blockinvisible")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_block_invis_members(ctx, *, status: str):
    """(Block messages from invisible members)
            admin config blockinvisible on
            admin config blockinvisible off
    """

    match status:
        case "on" | "ON":
            new_status = True
            color = discord.Color.green()
            msg = "Block messages from invisible members is now: `ON`"
        case "off | OFF":
            new_status = False
            color = discord.Color.red()
            msg = "Block messages from invisible members is now: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_block_invis_members(ctx.guild.id, new_status, ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="botreactions")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_bot_word_reactions(ctx, *, status: str):
    """(Bot will react to member words)
            admin config botreactions on
            admin config botreactions off
    """

    match status:
        case "on" | "ON":
            new_status = True
            color = discord.Color.green()
            msg = "Bot Reactions: `ON`"
        case "off | OFF":
            new_status = False
            color = discord.Color.red()
            msg = "Bot Reactions: `OFF`"
        case _:
            raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_bot_word_reactions(ctx.guild.id, new_status, ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="pfilter")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_pfilter(ctx, *, subcommand_passed):
    """(Block offensive words by users)
        Bot needs to have a permission to Manage Messages
            admin config pfilter on <channel_id>
            admin config pfilter off <channel_id>
    """

    help_command = f"For more info on this command: {chat_formatting.inline(f'{ctx.prefix}help admin config pfilter')}"
    subcommands = subcommand_passed.split()
    if len(subcommands) < 2:
        return await bot_utils.send_error_msg(ctx, "Missing required argument!!!\n"
                                                   f"{help_command}")

    new_status = subcommand_passed.split()[0]
    new_channel_id = subcommand_passed.split()[1]

    if not new_channel_id.isnumeric():
        return await bot_utils.send_error_msg(ctx, "Chnanel id should be used instead of its name!!!\n"
                                                   f"{help_command}")
    if new_channel_id not in [str(x.id) for x in ctx.guild.text_channels]:
        return await bot_utils.send_error_msg(ctx, f"Channel id not found: {chat_formatting.inline(new_channel_id)}")

    embed = discord.Embed()
    profanity_filter_dal = ProfanityFilterDal(ctx.bot.db_session, ctx.bot.log)
    channel = [x for x in ctx.guild.text_channels if x.id == int(new_channel_id)][0]

    match new_status:
        case "on" | "ON":
            # check if bot has permission to delete messages
            if not ctx.guild.me.guild_permissions.administrator or not ctx.guild.me.guild_permissions.manage_messages:
                msg = ("Profanity Filter could not be activated.\n"
                       "Bot does not have permission to \"Manage Messages\".")
                return await bot_utils.send_error_msg(ctx, msg)

            embed.color = discord.Color.green()
            embed.description = f"Profanity Filter `ACTIVATED`\nChannel: `{channel.name}`"
            await profanity_filter_dal.insert_profanity_filter_channel(ctx.guild.id, channel.id, channel.name, ctx.author.id)
        case "off" | "OFF":
            embed.color = discord.Color.green()
            embed.description = f"Profanity Filter `DEACTIVATED`\nChannel: `{channel.name}`"
            await profanity_filter_dal.delete_profanity_filter_channel(channel.id)
        case _:
            raise commands.BadArgument(message="BadArgument")

    await bot_utils.send_embed(ctx, embed)


@config.command(name="list")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_list(ctx):
    """(List all bot configurations)
            admin config list
    """

    cmd_prefix = f"{ctx.prefix}admin config"
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    sc = await servers_dal.get_server(ctx.guild.id)

    profanity_filter_dal = ProfanityFilterDal(ctx.bot.db_session, ctx.bot.log)
    pf = await profanity_filter_dal.get_all_server_profanity_filter_channels(ctx.guild.id)

    if len(pf) > 0:
        channel_names_lst = [x['channel_name'] for x in pf]
        channel_names = "\n".join(channel_names_lst)
    else:
        channel_names = "No channels listed"

    on = chat_formatting.green_text("ON")
    off = chat_formatting.red_text("OFF")

    embed = discord.Embed()
    embed.set_thumbnail(url=f"{ctx.guild.icon.url}")
    embed.set_author(name=f"Configurations for {ctx.guild.name}", icon_url=f"{ctx.guild.icon.url}")

    embed.add_field(
        name=f"Display a message when someone joins the server\n*`{cmd_prefix} joinmessage [on | off]`*",
        value=f"{on}" if sc["msg_on_join"] else f"{off}", inline=False)
    embed.add_field(
        name=f"Display a message when someone leaves the server\n*`{cmd_prefix} leavemessage [on | off]`*",
        value=f"{on}" if sc["msg_on_leave"] else f"{off}", inline=False)
    embed.add_field(
        name=f"Display a message when the server gets updated\n*`{cmd_prefix} servermessage [on | off]`*",
        value=f"{on}" if sc["msg_on_server_update"] else f"{off}", inline=False)
    embed.add_field(
        name=f"Display a message when someone changes their profile\n*`{cmd_prefix} membermessage [on | off]`*",
        value=f"{on}" if sc["msg_on_member_update"] else f"{off}", inline=False)
    embed.add_field(name=f"Block messages from invisible members\n*`{cmd_prefix} blockinvisible [on | off]`*",
                    value=f"{on}" if sc["block_invis_members"] else f"{off}", inline=False)
    embed.add_field(
        name=f"Bot will react to member words\n*`{cmd_prefix} botreactions [on | off]`*",
        value=f"{on}" if sc["bot_word_reactions"] else f"{off}", inline=False)
    embed.add_field(
        name="Channels with profanity filter activated\n"
             f"*`{cmd_prefix} pfilter on <channel_id>`*",
        value=chat_formatting.inline(channel_names),
        inline=False
    )

    embed.set_footer(text=f"For more info: {ctx.prefix}help admin config")
    await bot_utils.send_embed(ctx, embed, True)


async def setup(bot):
    bot.remove_command("admin")
    await bot.add_cog(Config(bot))
