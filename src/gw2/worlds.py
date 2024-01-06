# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.tools import bot_utils, chat_formatting
from src.gw2.gw2 import GuildWars2
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns
from src.gw2.tools.gw2_api import Gw2Api
from src.gw2.tools import gw2_utils


class GW2Worlds(GuildWars2):
    """(Guild Wars 2 List of Worlds Commands)"""
    def __init__(self, bot):
        super().__init__(bot)


@GW2Worlds.gw2.group()
async def worlds(ctx):
    """ (List all worlds)
        gw2 worlds na
        gw2 worlds eu
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 worlds")


@worlds.command(name="na")
@commands.cooldown(1, GW2CoolDowns.Worlds.value, BucketType.user)
async def worlds_na(ctx):
    """(List all NA worlds and wvw tier)
            gw2 worlds na
    """

    result, worlds_ids = await gw2_utils.get_worlds_ids(ctx)
    if not result:
        return

    gw2_api = Gw2Api(ctx.bot)
    desc_na = "~~~~~ NA Servers ~~~~~"
    embed_na = discord.Embed(description=chat_formatting.inline(desc_na))

    for world in worlds_ids:
        try:
            await ctx.message.channel.typing()
            wid = world["id"]
            matches = await gw2_api.call_api(f"wvw/matches?world={wid}")
            if wid < 2001:
                tier_number = matches["id"].replace("1-", "")
                embed_na.add_field(name=world["name"],
                                   value=chat_formatting.inline(f"T{tier_number} {world['population']}"))
        except Exception as e:
            await bot_utils.send_error_msg(ctx, e)
            return ctx.bot.log.error(ctx, e)

    await _send_splited_worlds_embed(ctx, embed_na)


@worlds.command(name="eu")
@commands.cooldown(1, GW2CoolDowns.Worlds.value, BucketType.user)
async def worlds_eu(ctx):
    """(List all EU worlds and wvw tier)
            gw2 worlds eu
    """

    result, worlds_ids = await gw2_utils.get_worlds_ids(ctx)
    if not result:
        return

    gw2_api = Gw2Api(ctx.bot)
    desc_eu = "~~~~~ EU Servers ~~~~~"
    embed_eu = discord.Embed(description=chat_formatting.inline(desc_eu))

    for world in worlds_ids:
        try:
            await ctx.message.channel.typing()
            wid = world["id"]
            matches = await gw2_api.call_api(f"wvw/matches?world={wid}")
            if wid > 2001:
                tier_number = matches["id"].replace("2-", "")
                embed_eu.add_field(name=world["name"],
                                   value=chat_formatting.inline(f"T{tier_number} {world['population']}"))
        except Exception as e:
            await bot_utils.send_error_msg(ctx, e)
            return ctx.bot.log.error(ctx, e)

    await _send_splited_worlds_embed(ctx, embed_eu)


async def _send_splited_worlds_embed(ctx, embed):
    """
        discord.Embed can only be up to 25 fields
    """

    max_fields = 25
    color = ctx.bot.settings["gw2"]["EmbedColor"]
    temp_embed = discord.Embed(color=color, description=chat_formatting.inline(embed.description))

    for field in embed.fields:
        temp_embed.add_field(name=field.name, value=field.value)
        if len(temp_embed.fields) == max_fields:
            await ctx.send(embed=temp_embed)
            temp_embed.clear_fields()
    await ctx.send(embed=temp_embed)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Worlds(bot))
