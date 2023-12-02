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
async def config(self, ctx):
    """(Server configurations commands)

    Examples:

    admin config list
    admin config bladmin         [on | off] (Only Bot Owner can execute this command)
    admin config muteadmin       [on | off] (Only Bot Owner can execute this command)
    admin config joinmessage     [on | off]
    admin config leavemessage    [on | off]
    admin config servermessage   [on | off]
    admin config membermessage   [on | off]
    admin config blockinvisible  [on | off]
    admin config mentionpool     [on | off]
    admin config anonymouspool   [on | off]
    admin config botreactions    [on | off]
    admin config pfilter         [on | off] <channel_name>
    admin config defaultchannel  <channel_name>
    """

    if ctx.invoked_subcommand:
        return ctx.invoked_subcommand
    else:
        if ctx.command is not None:
            cmd = ctx.command
        else:
            cmd = self.bot.get_command("admin config")
        await bot_utils.send_help_msg(self, ctx, cmd)


@config.command(name="bladmin")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_blacklist_admins(self, ctx, *, new_status: str):
    """(Able to blacklist server's admins)

    Only the Bot Owner can execute this command.

    Example:
    config bladmin [on | off]
    """

    await ctx.message.channel.typing()
    if new_status.lower() == "on":
        new_status = "Y"
        color = discord.Color.green()
        msg = "Admins can now be blacklisted: `ON`"
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = "Admins can no longer be blacklisted: `OFF`"
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if rs[0]["blacklist_admins"] != str(new_status):
        await server_configs_dal.update_blacklist_admins(ctx.guild.id, str(new_status))

    await bot_utils.send_embed(self, ctx, embed, False, msg)


@config.command(name="muteadmin")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_mute_admins(self, ctx, *, new_status: str):
    """(Able to mute server's admins)

    Only the Bot Owner can execute this command.

    Example:
    config muteadmin [on | off]
    """

    await ctx.message.channel.typing()
    if new_status.lower() == "on":
        new_status = "Y"
        color = discord.Color.green()
        msg = "Admins can now be muted: `ON`"
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = "Admins can no longer be muted: `OFF`"
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if rs[0]["mute_admins"] != str(new_status):
        await server_configs_dal.update_mute_admins(ctx.guild.id, str(new_status))

    await bot_utils.send_embed(self, ctx, embed, False, msg)


@config.command(name="joinmessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_join_message(self, ctx, *, new_status: str):
    """(Show message when a user joins the server)

    Example:
    config joinmessage [on | off]
    """

    await ctx.message.channel.typing()
    if new_status.lower() == "on":
        new_status = "Y"
        color = discord.Color.green()
        msg = "Display a message when someone joins the server is now: `ON`"
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = "Display a message when someone joins the server is now: `OFF`"
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if rs[0]["msg_on_join"] != str(new_status):
        await server_configs_dal.update_msg_on_join(ctx.guild.id, str(new_status))

    await bot_utils.send_embed(self, ctx, embed, False, msg)


@config.command(name="leavemessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_leave_message(self, ctx, *, new_status: str):
    """(Show message when a user leaves the server)

    Example:
    config leavemessage [on | off]
    """

    await ctx.message.channel.typing()
    if new_status.lower() == "on":
        new_status = "Y"
        color = discord.Color.green()
        msg = "Display a message when a member leaves the server is now: `ON`"
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = "Display a message when a member leaves the server is now: `OFF`"
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if rs[0]["msg_on_leave"] != str(new_status):
        await server_configs_dal.update_msg_on_leave(ctx.guild.id, str(new_status))

    await bot_utils.send_embed(self, ctx, embed, False, msg)


@config.command(name="servermessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_server_message(self, ctx, *, new_status: str):
    """(Show message when a server gets updated)

    Example:
    config servermessage [on | off]
    """

    await ctx.message.channel.typing()
    if new_status.lower() == "on":
        new_status = "Y"
        color = discord.Color.green()
        msg = "Display a message when server gets updated is now: `ON`"
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = "Display a message when server gets updated is now: `OFF`"
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if rs[0]["msg_on_server_update"] != str(new_status):
        await server_configs_dal.update_msg_on_server_update(ctx.guild.id, str(new_status))

    await bot_utils.send_embed(self, ctx, embed, False, msg)


@config.command(name="membermessage")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_member_message(self, ctx, *, new_status: str):
    """(Show message when a member make changes on his/her profile)

    Example:
    config membermessage [on | off]
    """

    await ctx.message.channel.typing()
    if new_status.lower() == "on":
        new_status = "Y"
        color = discord.Color.green()
        msg = "Display a message when someone changes profile is now: `ON`"
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = "Display a message when someone changes profile is now: `OFF`"
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if rs[0]["msg_on_member_update"] != str(new_status):
        await server_configs_dal.update_msg_on_member_update(ctx.guild.id, str(new_status))

    await bot_utils.send_embed(self, ctx, embed, False, msg)


@config.command(name="blockinvisible")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_block_invis_members(self, ctx, *, new_status: str):
    """(Block messages from invisible members)

    Example:
    config blockinvisible [on | off]
    """

    await ctx.message.channel.typing()
    if new_status.lower() == "on":
        new_status = "Y"
        color = discord.Color.green()
        msg = "Block messages from invisible members is now: `ON`"
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = "Block messages from invisible members is now: `OFF`"
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if rs[0]["block_invis_members"] != str(new_status):
        await server_configs_dal.update_block_invis_members(ctx.guild.id, str(new_status))

    await bot_utils.send_embed(self, ctx, embed, False, msg)


@config.command(name="botreactions")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_bot_word_reactions(self, ctx, *, new_status: str):
    """(Bot will react to member words)

    Example:
    config botreactions [on | off]
    """

    await ctx.message.channel.typing()
    if new_status.lower() == "on":
        new_status = "Y"
        color = discord.Color.green()
        msg = "Bot Reactions: `ON`"
    elif new_status.lower() == "off":
        new_status = "N"
        color = discord.Color.red()
        msg = "Bot Reactions: `OFF`"
    else:
        raise commands.BadArgument(message="BadArgument")

    embed = discord.Embed(description=msg, color=color)
    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if rs[0]["bot_word_reactions"] != str(new_status):
        await server_configs_dal.update_bot_word_reactions(ctx.guild.id, str(new_status))

    await bot_utils.send_embed(self, ctx, embed, False, msg)


@config.command(name="defaultchannel")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_default_text_channel(self, ctx, *, text_channel: str):
    """(Set default text channel to be used for bot messages)

    Use "none" to use first public available channel

    Example:
    config defaultchannel <channel_name>
    config defaultchannel <none>
    """

    await ctx.message.channel.typing()
    channel_exists = False
    for channel in ctx.guild.text_channels:
        if text_channel.lower() == str(channel.name).lower():
            channel_exists = True

    if text_channel.lower() == "none":
        channel_exists = True
        text_channel = None

    if channel_exists is False:
        raise commands.BadArgument(message="BadArgument_default_text_channel")

    if text_channel is None:
        msg = "First public text channel is going to be used for bot messages"
    else:
        msg = f"Default text channel to be used for bot messages: {chat_formatting.inline(text_channel)}"

    color = discord.Color.green()
    embed = discord.Embed(description=msg, color=color)
    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if rs[0]["default_text_channel"] != str(text_channel):
        await server_configs_dal.update_default_text_channel(ctx.guild.id, str(text_channel))

    await bot_utils.send_embed(self, ctx, embed, False, msg)


@config.command(name="pfilter")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_pfilter(self, ctx, *, stats_channel: str):
    """(Block offensive words by users)

    Example:
    config pfilter [on | off] <channel_name>
    """

    await ctx.message.channel.typing()
    new_pf_status = stats_channel.split()[0]
    ch_name_list = stats_channel.split()[1:]
    ch_name = ' '.join(ch_name_list)

    if new_pf_status.lower() == "on":
        # check if bot has permission to delete messages
        has_perms = False
        if ctx.guild.me.guild_permissions.administrator:
            has_perms = True
        elif ctx.guild.me.guild_permissions.manage_messages:
            has_perms = True
        if not has_perms:
            msg = f"`{chat_formatting.NO_ENTRY} Bot does not have permission to delete messages.\n" \
                  "Profanity filter could not be activated.\n" \
                  "Missing permission: \"Manage Messages\"`"
            embed = discord.Embed(title="", color=discord.Color.red(), description=msg)
            await bot_utils.send_embed(self, ctx, embed, False, msg)
            return

        new_pf_status = "Y"
        color = discord.Color.green()
        msg = f"Profanity Filter `ACTIVATED`\nChannel: `{ch_name}`"
    elif new_pf_status.lower() == "off":
        new_pf_status = "N"
        color = discord.Color.red()
        msg = f"Profanity Filter `DEACTIVATED`\nChannel: `{ch_name}`"
    else:
        raise commands.BadArgument(message="BadArgument")

        # get object channel from string
    channel = bot_utils.get_object_channel(self, ctx, ch_name)
    if channel is None:
        raise commands.BadArgument(message=f"Channel not found: `{ch_name}`")

    embed = discord.Embed(description=msg, color=color)
    profanity_filter_dal = ProfanityFilterDal(self.bot.db_session, self.bot.log)
    rs = await profanity_filter_dal.get_profanity_filter_channel(channel)
    if len(rs) == 0 and new_pf_status == "Y":
        await profanity_filter_dal.insert_profanity_filter_channel(channel)
    elif len(rs) > 0 and new_pf_status == "N":
        await profanity_filter_dal.delete_profanity_filter_channel(channel)

    await bot_utils.send_embed(self, ctx, embed, False, msg)


@config.command(name="list")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_config_list(self, ctx):
    """(List all bot configurations)

    Example:
    config list
    """

    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    profanity_filter_dal = ProfanityFilterDal(self.bot.db_session, self.bot.log)

    sc = await server_configs_dal.get_server_by_id(ctx.guild.id)
    pf = await profanity_filter_dal.get_all_server_profanity_filter_channels(ctx.guild.id)

    if len(pf) > 0:
        channel_names_lst = []
        for key, value in pf.items():
            channel_names_lst.append(f"{value['channel_name']}")
        channel_names = '\n'.join(channel_names_lst)
    else:
        channel_names = "No channels listed"

    on = chat_formatting.green_text("ON")
    off = chat_formatting.red_text("OFF")
    color = self.bot.settings["EmbedColor"]

    embed = discord.Embed(color=color)
    embed.set_thumbnail(url=f"{ctx.guild.icon.url}")
    embed.set_author(name=f"Configurations for {ctx.guild.name}", icon_url=f"{ctx.guild.icon.url}")

    embed.add_field(
        name=f"Admins can be blacklisted (cannot use any commands)\n*`{ctx.prefix}config bladmin [on | off]`*",
        value=f"{on}" if sc[0]["blacklist_admins"] == 'Y' else f"{off}", inline=False)
    embed.add_field(name=f"Admins can be muted (cannot type anything)\n*`{ctx.prefix}config muteadmin [on | off]`*",
                    value=f"{on}" if sc[0]["mute_admins"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name=f"Display a message when someone joins the server\n*`{ctx.prefix}config joinmessage [on | off]`*",
        value=f"{on}" if sc[0]["msg_on_join"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name=f"Display a message when someone leaves the server\n*`{ctx.prefix}config leavemessage [on | off]`*",
        value=f"{on}" if sc[0]["msg_on_leave"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name=f"Display a message when the server gets updated\n*`{ctx.prefix}config servermessage [on | off]`*",
        value=f"{on}" if sc[0]["msg_on_server_update"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name=f"Display a message when someone changes their profile\n*`{ctx.prefix}config membermessage [on | off]`*",
        value=f"{on}" if sc[0]["msg_on_member_update"] == 'Y' else f"{off}", inline=False)
    embed.add_field(name=f"Block messages from invisible members\n*`{ctx.prefix}config blockinvisible [on | off]`*",
                    value=f"{on}" if sc[0]["block_invis_members"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name=f"Mention everyone when pool commands are used\n*`{ctx.prefix}config mentionpool [on | off]`*",
        value=f"{on}" if sc[0]["mention_everyone_pool_cmd"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name="Anonymous pools\n"
             "(hide the author's name from the pool command)\n"
             f"*`{ctx.prefix}config anonymouspool [on | off]`*",
        value=f"{on}" if sc[0]["anonymous_pool"] == 'Y' else f"{off}", inline=False)
    embed.add_field(
        name=f"Bot will react to member words\n*`{ctx.prefix}config botreactions [on | off] <channel_name>`*",
        value=f"{on}" if sc[0]["bot_word_reactions"] == 'Y' else f"{off}", inline=False)

    if sc[0]["default_text_channel"] is not None and sc[0]["default_text_channel"] != "":
        default_text_channel = sc[0]["default_text_channel"]
    else:
        default_text_channel = f"{bot_utils.get_server_first_public_text_channel(ctx.guild)}"

    embed.add_field(
        name="Text channel to display bot messages\n"
             "(defaults to the top first public channel)\n"
             f"*`{ctx.prefix}config defaultchannel <channel_name>`*",
        value=chat_formatting.inline(default_text_channel), inline=False)
    embed.add_field(
        name="Text channels with profanity filter activated",
        value=chat_formatting.inline(channel_names),
        inline=False
    )

    embed.set_footer(text=f"For more info: {ctx.prefix}help config")
    await bot_utils.send_embed(self, ctx, embed, True)


async def setup(bot):
    bot.remove_command("admin")
    await bot.add_cog(Config(bot))
