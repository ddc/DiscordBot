# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.database.dal.bot.bot_configs_dal import BotConfigsDal
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.tools import bot_utils
from src.bot.constants import variables, messages
from src.bot.tools.checks import Checks
from src.bot.tools.cooldowns import CoolDowns


class Owner(commands.Cog):
    """(Bot owner commands)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @Checks.check_is_bot_owner()
    @commands.cooldown(1, CoolDowns.Owner.value, BucketType.user)
    async def owner(self, ctx):
        """(Bot Owner Commands)

        owner servers
        owner prefix <new_prefix>
        owner botdescription <new_description>
        """

        await bot_utils.invoke_subcommand(ctx, "owner")

    @owner.command(name="prefix")
    async def owner_change_prefix(self, ctx, *, new_prefix: str):
        """(Change bot prefix for commands)
            Possible prefixes: ! $ % ^ & ? > < . ;
                owner prefix <new_prefix>
        """

        await ctx.message.channel.typing()
        if new_prefix not in variables.ALLOWED_PREFIXES:
            raise commands.BadArgument(message="BadArgument_bot_prefix")

        bot_user = ctx.me
        if hasattr(bot_user, "activity") and bot_user.activity is not None:
            if bot_user.activity.type == discord.ActivityType.playing:
                game = str(bot_user.activity.name).split("|")[0].strip()
                bot_game_desc = f"{game} | {new_prefix}help"
                await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name=bot_game_desc))

        bot_configs_sql = BotConfigsDal(self.bot.db_session, self.bot.log)
        await bot_configs_sql.update_bot_prefix(new_prefix, ctx.message.author.id)
        self.bot.command_prefix = (new_prefix,)

        color = self.bot.settings["bot"]["EmbedOwnerColor"]
        msg = f"{messages.BOT_PREFIX_CHANGED}: `{new_prefix}`"
        embed = discord.Embed(description=msg, color=color)
        await bot_utils.send_embed(ctx, embed,)

    @owner.command(name="botdescription")
    async def owner_description(self, ctx, *, desc: str):
        """(Change bot description)
            owner botdescription <new_description>
        """

        await bot_utils.delete_message(ctx)
        await ctx.message.channel.typing()
        bot_configs_sql = BotConfigsDal(self.bot.db_session, self.bot.log)
        await bot_configs_sql.update_bot_description(desc, ctx.message.author.id)
        self.bot.description = desc

        color = self.bot.settings["bot"]["EmbedOwnerColor"]
        msg = f"{messages.BOT_DESCRIPTION_CHANGED}: `{desc}`"
        embed = discord.Embed(description=msg, color=color)
        await bot_utils.send_embed(ctx, embed)

    @owner.command(name="servers")
    async def owner_servers(self, ctx):
        """(Display all servers in database)
            owner servers
        """

        await ctx.message.channel.typing()
        servers_sql = ServersDal(self.bot.db_session, self.bot.log)
        rs = await servers_sql.get_server()
        color = self.bot.settings["bot"]["EmbedOwnerColor"]
        embed = discord.Embed(description="Database servers", color=color)
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar.url)

        id_list = []
        name_list = []
        for value in rs:
            id_list.append(str(value["id"]))
            name_list.append(value["name"])

        ids = "\n".join(id_list)
        names = "\n".join(name_list)
        embed.add_field(name="ID", value=ids)
        embed.add_field(name="Name", value=names)
        await bot_utils.send_embed(ctx, embed, True)


async def setup(bot):
    await bot.add_cog(Owner(bot))
