# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.database.dal.bot.bot_configs_dal import BotConfigsDal
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.utils import bot_utils, constants, chat_formatting
from src.bot.utils.checks import Checks
from src.bot.utils.cooldowns import CoolDowns


class Owner(commands.Cog):
    """(Bot owner commands)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @Checks.check_is_bot_owner()
    async def owner(self, ctx):
        """(Bot Owner Commands)

        owner servers
        owner reloadallcogs
        owner prefix <new_prefix>
        owner reloadcog <cog_name>
        owner botdescription <new_description>
        """

        if ctx.invoked_subcommand:
            return ctx.invoked_subcommand
        else:
            if ctx.command is not None:
                cmd = ctx.command
            else:
                cmd = self.bot.get_command("owner")
            await bot_utils.send_help_msg(self, ctx, cmd)

    @owner.command(name="prefix")
    @commands.cooldown(1, CoolDowns.Owner.value, BucketType.user)
    async def owner_change_prefix(self, ctx, *, new_prefix: str):
        """(Change bot prefix for commands)

        Possible prefixes: ! $ % ^ & ? > < . ;

        Example:
        owner prefix <new_prefix>
        """

        await ctx.message.channel.typing()
        if new_prefix not in constants.ALLOWED_PREFIXES:
            raise commands.BadArgument(message="BadArgument_bot_prefix")

        bot_user = ctx.me
        if hasattr(bot_user, "activity") and bot_user.activity is not None:
            if bot_user.activity.type == discord.ActivityType.playing:
                game = str(bot_user.activity.name).split("|")[0].strip()
                bot_game_desc = f"{game} | {new_prefix}help"
                await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name=bot_game_desc))

        bot_configs_sql = BotConfigsDal(self.bot.db_session, self.bot.logs)
        await bot_configs_sql.update_bot_prefix(new_prefix)
        self.bot.command_prefix = (new_prefix,)

        color = self.bot.settings["EmbedOwnerColor"]
        msg = f"Bot prefix has been changed to: `{new_prefix}`"
        embed = discord.Embed(description=msg, color=color)
        await bot_utils.send_embed(self, ctx, embed, False, msg)

    @owner.command(name="botdescription")
    @commands.cooldown(1, CoolDowns.Owner.value, BucketType.user)
    async def owner_description(self, ctx, *, desc: str):
        """(Change bot description)

        Example:
        owner botdescription <new_description>
        """

        # bot_utils.delete_channel_message(self, ctx)
        await ctx.message.channel.typing()
        bot_configs_sql = BotConfigsDal(self.bot.db_session, self.bot.logs)
        await bot_configs_sql.update_bot_description(desc)
        self.bot.description = desc

        color = self.bot.settings["EmbedOwnerColor"]
        msg = f"Bot description changed to: \"`{desc}`\""
        embed = discord.Embed(description=msg, color=color)
        await bot_utils.send_embed(self, ctx, embed, False, msg)

    @owner.command(name="servers")
    @commands.cooldown(1, CoolDowns.Owner.value, BucketType.user)
    async def owner_servers(self, ctx):
        """(Display all servers in database)

        Example:
        owner servers
        """

        # bot_utils.delete_channel_message(self, ctx)
        await ctx.message.channel.typing()
        servers_sql = ServersDal(self.bot.db_session, self.bot.log)
        rs = await servers_sql.get_all_servers()
        color = self.bot.settings["EmbedOwnerColor"]
        embed = discord.Embed(description="Displaying all servers using the bot", color=color)
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar.url)

        name_list = []
        owner_list = []
        for value in rs:
            name_list.append(value["server_name"])
            owner_list.append(value["owner_name"])

        names = '\n'.join(name_list)
        owners = '\n'.join(owner_list)
        embed.add_field(name="Name", value=chat_formatting.inline(names), inline=True)
        embed.add_field(name="Owner", value=chat_formatting.inline(owners), inline=True)
        msg = f"Servers:\n`{names}`"
        await bot_utils.send_embed(self, ctx, embed, True, msg)

    @owner.command(name="reloadallcogs")
    @commands.cooldown(1, CoolDowns.Owner.value, BucketType.user)
    async def owner_reload(self, ctx):
        """(Command to reload all bot cogs)

        Example:
        owner reloadallcogs
        """

        # bot_utils.delete_channel_message(self, ctx)
        await bot_utils.reload_cogs(self)

        color = self.bot.settings["EmbedOwnerColor"]
        msg = "All cogs have been loaded successfully"
        embed = discord.Embed(description=msg, color=color)
        await bot_utils.send_embed(self, ctx, embed, False, msg)

    @owner.command(name="reloadcog")
    @commands.cooldown(1, CoolDowns.Owner.value, BucketType.user)
    async def owner_reload_cog(self, ctx, *, name: str):
        """(Command to reload a module)

        Example:
        owner reloadcog <cog_name>
        """

        # bot_utils.delete_channel_message(self, ctx)
        await ctx.message.channel.typing()
        color = self.bot.settings["EmbedOwnerColor"]
        full_cog_name = f"src.bot.{name}"

        try:
            self.bot.reload_extension(full_cog_name)
        except Exception as e:
            msg = e.msg
        else:
            msg = f'**`RELOAD SUCCESS`**\nCog: {name}'

        embed = discord.Embed(description=msg, color=color)
        await bot_utils.send_embed(self, ctx, embed, False, msg)


async def setup(bot):
    await bot.add_cog(Owner(bot))
