# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import asyncio
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from bot import init_loop
from .utils import bot_utils as BotUtils
from .utils import chat_formatting as Formatting
from .utils.checks import Checks
from src.sql.bot.bot_configs_sql import BotConfigsSql
from src.sql.bot.servers_sql import ServersSql
from src.cogs.bot.utils.cooldowns import CoolDowns


class Owner(commands.Cog):
    """(Bot owner commands)"""
    def __init__(self, bot):
        self.bot = bot


    @commands.group()
    @Checks.check_is_bot_owner()
    async def owner(self, ctx):
        """(Bot Owner Commands)

        owner servers
        owner executesql
        owner reloadallcogs
        owner botgame <game>
        owner prefix <new_prefix>
        owner reloadcog <cog_name>
        owner bgtaskgame [on | off]
        owner botdescription <new_description>
        """

        if ctx.invoked_subcommand is None:
            if ctx.command is not None:
                cmd = ctx.command
            else:
                cmd = self.bot.get_command("owner")

            await BotUtils.send_help_msg(self, ctx, cmd)
            return

        ctx.invoked_subcommand


    @owner.command(name="prefix")
    @commands.cooldown(1, CoolDowns.OwnerCooldown.value, BucketType.user)
    async def owner_prefix(self, ctx, *, new_prefix: str):
        """(Change bot prefix for commands)

        Possible prefixes: ! $ % ^ & ? > < . ;

        Example:
        owner prefix <new_prefix>
        """

        # BotUtils.delete_last_channel_message(self, ctx)
        await ctx.message.channel.trigger_typing()
        possible_prefixes = "!$%^&?><.;"
        if new_prefix not in possible_prefixes:
            raise commands.BadArgument(message=f"BadArgument_bot_prefix")

        botConfigsSql = BotConfigsSql(self.bot)
        await botConfigsSql.update_bot_prefix(new_prefix)
        self.bot.command_prefix = new_prefix

        bot_user = ctx.me
        if bot_user.activity is not None:
            if bot_user.activity.type == discord.ActivityType.playing:
                game = str(bot_user.activity.name).split("|")[0].strip()
                bot_game_desc = f"{game} | {new_prefix}help"
                await self.bot.change_presence(activity=discord.Game(name=bot_game_desc))

        color = self.bot.settings["EmbedOwnerColor"]
        msg = f"Bot prefix has been changed to: `{new_prefix}`"
        embed = discord.Embed(description=msg, color=color)
        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @owner.command(name="botdescription")
    @commands.cooldown(1, CoolDowns.OwnerCooldown.value, BucketType.user)
    async def owner_description(self, ctx, *, desc: str):
        """(Change bot description)

        Example:
        owner botdescription <new_description>
        """

        # BotUtils.delete_last_channel_message(self, ctx)
        await ctx.message.channel.trigger_typing()
        botConfigsSql = BotConfigsSql(self.bot)
        await botConfigsSql.update_bot_description(desc)
        self.bot.description = desc

        color = self.bot.settings["EmbedOwnerColor"]
        msg = f"Bot description changed to: \"`{desc}`\""
        embed = discord.Embed(description=msg, color=color)
        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @owner.command(name="bgtaskgame")
    @commands.cooldown(1, CoolDowns.OwnerCooldown.value, BucketType.user)
    async def owner_bg_task_change_game(self, ctx, *, new_status: str):
        """(Background task to update the game bot is playing from time to time)

        ===> Need to restart the bot

        Example:
        owner bgtaskgame [on | off]
        """

        # BotUtils.delete_last_channel_message(self, ctx)
        await ctx.message.channel.trigger_typing()
        if new_status.lower() == "on":
            new_status = "Y"
            msg = "WARNING: Bot is restarting...\nBackground task that update bot activity is now: `ON`"
        elif new_status.lower() == "off":
            new_status = "N"
            msg = "WARNING: Bot is restarting...\nBackground task that update bot activity is now: `OFF`"
        else:
            raise commands.BadArgument(message="BadArgument")

        botConfigsSql = BotConfigsSql(self.bot)
        rs = await botConfigsSql.get_bot_configs()
        if rs[0]["bg_task_change_game"] != str(new_status):
            color = self.bot.settings["EmbedOwnerColor"]
            embed = discord.Embed(description=msg, color=color)
            await BotUtils.send_embed(self, ctx, embed, False, msg)
            self.bot.settings["BGChangeGame"] = str(new_status)

            # need to restart bot here to kill bg task
            self.bot.unload_extension("src.cogs.bot.events")
            self.bot.load_extension("src.cogs.bot.events")
            self.bot.loop.stop()
            self.bot.loop.close()
            self.bot.loop = asyncio.set_event_loop(asyncio.new_event_loop())
            init_loop()


    @owner.command(name="botgame")
    @commands.cooldown(1, CoolDowns.OwnerCooldown.value, BucketType.user)
    async def owner_botgame(self, ctx, *, game: str):
        """(Change game that bot is playing)

        Example:
        owner botgame <game>
        """

        # BotUtils.delete_last_channel_message(self, ctx)
        await ctx.message.channel.trigger_typing()
        prefix = self.bot.command_prefix[0]
        bot_game_desc = f"{game} | {prefix}help"
        color = self.bot.settings["EmbedOwnerColor"]
        embed = discord.Embed(color=color)
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        msg = f"```I'm now playing: {game}```"
        await self.bot.change_presence(activity=discord.Game(name=bot_game_desc))

        if self.bot.settings["BGChangeGame"].lower() == "yes":
            bg_task_warning = f"Background task that update bot activity is ON\nActivity will change after {self.bot.settings['BGActivityTimer']} secs."
            embed.description = bg_task_warning
            await BotUtils.send_embed(self, ctx, embed, True, msg)

        embed.description = f"```I'm now playing: {game}```"
        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @owner.command(name="reloadcog")
    @commands.cooldown(1, CoolDowns.OwnerCooldown.value, BucketType.user)
    async def owner_reload_cog(self, ctx, *, name: str):
        """(Command to reload a module)

        Example:
        owner reloadcog <cog_name>
        """

        # BotUtils.delete_last_channel_message(self, ctx)
        await ctx.message.channel.trigger_typing()
        color = self.bot.settings["EmbedOwnerColor"]
        full_cog_name = f"src.cogs.bot.{name}"

        try:
            self.bot.reload_extension(full_cog_name)
        except Exception as e:
            msg = e.msg
        else:
            msg = f'**`RELOAD SUCCESS`**\nCog: {name}'

        embed = discord.Embed(description=msg, color=color)
        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @owner.command(name="servers")
    @commands.cooldown(1, CoolDowns.OwnerCooldown.value, BucketType.user)
    async def owner_servers(self, ctx):
        """(Display all servers in database)

        Example:
        owner servers
        """

        # BotUtils.delete_last_channel_message(self, ctx)
        await ctx.message.channel.trigger_typing()
        serversSql = ServersSql(self.bot)
        rs = await serversSql.get_all_servers()
        color = self.bot.settings["EmbedOwnerColor"]
        embed = discord.Embed(description="Displaying all servers using the bot", color=color)
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)

        name_list = []
        region_list = []
        owner_list = []
        for key, value in rs.items():
            region = str(value["region"])
            region_flag = BotUtils.get_region_flag(region)
            name_list.append(value["server_name"])
            region_list.append(f"{region_flag} `{region}`")
            owner_list.append(value["owner_name"])

        names = '\n'.join(name_list)
        owners = '\n'.join(owner_list)
        regions = '\n'.join(region_list)

        embed.add_field(name="Name", value=Formatting.inline(names), inline=True)
        embed.add_field(name="Owner", value=Formatting.inline(owners), inline=True)
        embed.add_field(name="Voice Region", value=regions, inline=True)
        msg = f"Servers:\n`{names}`"
        await BotUtils.send_embed(self, ctx, embed, True, msg)


    @owner.command(name="reloadallcogs")
    @commands.cooldown(1, CoolDowns.OwnerCooldown.value, BucketType.user)
    async def owner_reload(self, ctx):
        """(Command to reload all bot cogs)

        Example:
        owner reloadallcogs
        """

        # BotUtils.delete_last_channel_message(self, ctx)
        await BotUtils.reload_cogs(self)

        color = self.bot.settings["EmbedOwnerColor"]
        msg = "All cogs have been loaded successfully"
        embed = discord.Embed(description=msg, color=color)
        await BotUtils.send_embed(self, ctx, embed, False, msg)


    @owner.command(name="executesql")
    @commands.cooldown(1, CoolDowns.OwnerCooldown.value, BucketType.user)
    async def owner_execute_sql(self, ctx):
        """(Command to execute all sql files inside data/sql directory)

        Example:
        owner executesql
        """

        # BotUtils.delete_last_channel_message(self, ctx)
        await ctx.message.channel.trigger_typing()
        await BotUtils.execute_all_sql_files(self)

        color = self.bot.settings["EmbedOwnerColor"]
        msg = "All SQL have been loaded successfully"
        embed = discord.Embed(description=msg, color=color)
        await BotUtils.send_embed(self, ctx, embed, True, msg)


def setup(bot):
    bot.add_cog(Owner(bot))
