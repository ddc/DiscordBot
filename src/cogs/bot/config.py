# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from .utils import bot_utils as BotUtils
from .utils import chat_formatting as Formatting
from .utils.checks import Checks
from src.sql.bot.profanity_filters_sql import ProfanityFilterSql
from src.sql.bot.server_configs_sql import ServerConfigsSql
from src.cogs.bot.utils.cooldowns import CoolDowns


class Config(commands.Cog):
    """(Server configuration commands - Admin)"""
    def __init__(self, bot):
        self.bot = bot


    @commands.group()
    @Checks.check_is_admin()
    async def config(self, ctx):
        """(Server configurations commands - Admin)

        Examples:

        config list
        config bladmin         [on | off] (Only Bot Owner can execute this command)
        config muteadmin       [on | off] (Only Bot Owner can execute this command)
        config joinmessage     [on | off]
        config leavemessage    [on | off]
        config servermessage   [on | off]
        config membermessage   [on | off]
        config blockinvisible  [on | off]
        config mentionpool     [on | off]
        config anonymouspool   [on | off]
        config botreactions    [on | off]
        config pfilter         [on | off] <channel_name>
        config defaultchannel  <channel_name>
        """

        if ctx.invoked_subcommand is None:
            if ctx.command is not None:
                cmd = ctx.command
            else:
                cmd = self.bot.get_command("config")

            await BotUtils.send_help_msg(self, ctx, cmd)
            return
        ctx.invoked_subcommand


    @config.command(name="bladmin")
    @Checks.check_is_bot_owner()
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_blacklist_admins(self, ctx, *, new_status: str):
        """(Able to blacklist server's admins)

        Only the Bot Owner can execute this command.

        Example:
        config bladmin [on | off]
        """

        await ctx.message.channel.trigger_typing()
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
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["blacklist_admins"] != str(new_status):
            await serverConfigsSql.update_blacklist_admins(ctx.guild.id, str(new_status))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="muteadmin")
    @Checks.check_is_bot_owner()
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_mute_admins(self, ctx, *, new_status: str):
        """(Able to mute server's admins)

        Only the Bot Owner can execute this command.

        Example:
        config muteadmin [on | off]
        """

        await ctx.message.channel.trigger_typing()
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
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["mute_admins"] != str(new_status):
            await  serverConfigsSql.update_mute_admins(ctx.guild.id, str(new_status))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="joinmessage")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_join_message(self, ctx, *, new_status: str):
        """(Show message when a user joins the server)

        Example:
        config joinmessage [on | off]
        """

        await ctx.message.channel.trigger_typing()
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
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["msg_on_join"] != str(new_status):
            await serverConfigsSql.update_msg_on_join(ctx.guild.id, str(new_status))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="leavemessage")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_leave_message(self, ctx, *, new_status: str):
        """(Show message when a user leaves the server)

        Example:
        config leavemessage [on | off]
        """

        await ctx.message.channel.trigger_typing()
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
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["msg_on_leave"] != str(new_status):
            await serverConfigsSql.update_msg_on_leave(ctx.guild.id, str(new_status))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="servermessage")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_server_message(self, ctx, *, new_status: str):
        """(Show message when a server gets updated)

        Example:
        config servermessage [on | off]
        """

        await ctx.message.channel.trigger_typing()
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
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["msg_on_server_update"] != str(new_status):
            await serverConfigsSql.update_msg_on_server_update(ctx.guild.id, str(new_status))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="membermessage")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_member_message(self, ctx, *, new_status: str):
        """(Show message when a member make changes on his/her profile)

        Example:
        config membermessage [on | off]
        """

        await ctx.message.channel.trigger_typing()
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
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["msg_on_member_update"] != str(new_status):
            await serverConfigsSql.update_msg_on_member_update(ctx.guild.id, str(new_status))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="blockinvisible")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_block_invis_members(self, ctx, *, new_status: str):
        """(Block messages from invisible members)

        Example:
        config blockinvisible [on | off]
        """

        await ctx.message.channel.trigger_typing()
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
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["block_invis_members"] != str(new_status):
            await serverConfigsSql.update_block_invis_members(ctx.guild.id, str(new_status))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="mentionpool")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_mention_everyone_pool_cmd(self, ctx, *, new_status: str):
        """(Mention everyone when the pool command is used)

        Example:
        config mentionpool [on | off]
        """

        await ctx.message.channel.trigger_typing()
        if new_status.lower() == "on":
            new_status = "Y"
            color = discord.Color.green()
            msg = "Mention everyone when the pool command is used is now: `ON`"
        elif new_status.lower() == "off":
            new_status = "N"
            color = discord.Color.red()
            msg = "Mention everyone when the pool command is used is now: `OFF`"
        else:
            raise commands.BadArgument(message="BadArgument")

        embed = discord.Embed(description=msg, color=color)
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["mention_everyone_pool_cmd"] != str(new_status):
            await serverConfigsSql.update_mention_everyone_pool_cmd(ctx.guild.id, str(new_status))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="anonymouspool")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_anonymous_pool(self, ctx, *, new_status: str):
        """(Hide the author's name from the pool command)

        Example:
        config anonymouspool [on | off]
        """

        await ctx.message.channel.trigger_typing()
        if new_status.lower() == "on":
            new_status = "Y"
            color = discord.Color.green()
            msg = "Anonymous pools: `ON`"
        elif new_status.lower() == "off":
            new_status = "N"
            color = discord.Color.red()
            msg = "Anonymous pools: `OFF`"
        else:
            raise commands.BadArgument(message="BadArgument")

        embed = discord.Embed(description=msg, color=color)
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["anonymous_pool"] != str(new_status):
            await serverConfigsSql.update_anonymous_pool(ctx.guild.id, str(new_status))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="botreactions")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_bot_word_reactions(self, ctx, *, new_status: str):
        """(Bot will react to member words)

        Example:
        config botreactions [on | off]
        """

        await ctx.message.channel.trigger_typing()
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
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["bot_word_reactions"] != str(new_status):
            await serverConfigsSql.update_bot_word_reactions(ctx.guild.id, str(new_status))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="defaultchannel")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_default_text_channel(self, ctx, *, text_channel: str):
        """(Set default text channel to be used for bot messages)

        Use "none" to use first public available channel

        Example:
        config defaultchannel <channel_name>
        config defaultchannel <none>
        """

        await ctx.message.channel.trigger_typing()
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
            msg = f"Default text channel to be used for bot messages: {Formatting.inline(text_channel)}"

        color = discord.Color.green()
        embed = discord.Embed(description=msg, color=color)
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["default_text_channel"] != str(text_channel):
            await serverConfigsSql.update_default_text_channel(ctx.guild.id, str(text_channel))

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="pfilter")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_pfilter(self, ctx, *, stats_channel: str):
        """(Block offensive words by users)

        Example:
        config pfilter [on | off] <channel_name>
        """

        await ctx.message.channel.trigger_typing()
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
                msg = f"`{Formatting.NO_ENTRY} Bot does not have permission to delete messages.\n" \
                      "Profanity filter could not be activated.\n" \
                      "Missing permission: \"Manage Messages\"`"
                embed = discord.Embed(title="", color=discord.Color.red(), description=msg)
                await BotUtils.send_embed(self, ctx, embed, False, msg)
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
        channel = BotUtils.get_object_channel(self, ctx, ch_name)
        if channel is None:
            raise commands.BadArgument(message=f"Channel not found: `{ch_name}`")

        embed = discord.Embed(description=msg, color=color)
        profanityFilterSql = ProfanityFilterSql(self.bot)
        rs = await profanityFilterSql.get_profanity_filter_channel(channel)
        if len(rs) == 0 and new_pf_status == "Y":
            await profanityFilterSql.insert_profanity_filter_channel(channel)
        elif len(rs) > 0 and new_pf_status == "N":
            await profanityFilterSql.delete_profanity_filter_channel(channel)

        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @config.command(name="list")
    @commands.cooldown(1, CoolDowns.ConfigCooldown.value, BucketType.user)
    async def config_config_list(self, ctx):
        """(List all bot configurations)

        Example:
        config list
        """

        serverConfigsSql = ServerConfigsSql(self.bot)
        profanityFilterSql = ProfanityFilterSql(self.bot)

        sc = await serverConfigsSql.get_server_configs(ctx.guild.id)
        pf = await profanityFilterSql.get_all_server_profanity_filter_channels(ctx.guild.id)

        if len(pf) > 0:
            channel_names_lst = []
            for key, value in pf.items():
                channel_names_lst.append(f"{value['channel_name']}")
            channel_names = '\n'.join(channel_names_lst)
        else:
            channel_names = "No channels listed"

        on = Formatting.green_text("ON")
        off = Formatting.red_text("OFF")
        color = self.bot.settings["EmbedColor"]

        embed = discord.Embed(color=color)
        embed.set_thumbnail(url=f"{ctx.guild.icon_url}")
        embed.set_author(name=f"Configurations for {ctx.guild.name}", icon_url=f"{ctx.guild.icon_url}")

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
            name=f"Anonymous pools\n(hide the author's name from the pool command)\n*`{ctx.prefix}config anonymouspool [on | off]`*",
            value=f"{on}" if sc[0]["anonymous_pool"] == 'Y' else f"{off}", inline=False)
        embed.add_field(
            name=f"Bot will react to member words\n*`{ctx.prefix}config botreactions [on | off] <channel_name>`*",
            value=f"{on}" if sc[0]["bot_word_reactions"] == 'Y' else f"{off}", inline=False)

        if sc[0]["default_text_channel"] is not None and sc[0]["default_text_channel"] != "":
            default_text_channel = sc[0]["default_text_channel"]
        else:
            default_text_channel = f"{BotUtils.get_server_first_public_text_channel(ctx.guild)}"

        embed.add_field(
            name=f"Text channel to display bot messages\n(defaults to the top first public channel)\n*`{ctx.prefix}config defaultchannel <channel_name>`*",
            value=Formatting.inline(default_text_channel), inline=False)
        embed.add_field(name="Text channels with profanity filter activated", value=Formatting.inline(channel_names),
                        inline=False)

        embed.set_footer(text=f"For more info: {ctx.prefix}help config")
        await BotUtils.send_embed(self, ctx, embed, True)


def setup(bot):
    bot.add_cog(Config(bot))
