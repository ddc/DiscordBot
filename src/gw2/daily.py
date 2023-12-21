# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.utils import bot_utils, chat_formatting
from src.gw2.gw2 import GuildWars2
from src.gw2.utils.gw2_api import Gw2Api
from src.gw2.utils.gw2_cooldowns import GW2CoolDowns


class GW2Daily(GuildWars2):
    """(Commands Related to GW2 Dailies)"""
    def __init__(self, bot):
        super().__init__(bot)


@GW2Daily.gw2.group()
async def daily(ctx):
    """(Show Dailies)
        gw2 daily pve
        gw2 daily pvp
        gw2 daily wvw
        gw2 daily fractals
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 config")


@daily.command(name="pve")
@commands.cooldown(1, GW2CoolDowns.Daily.value, BucketType.user)
async def pve(ctx):
    """(Show PVE Dailies)
            gw2 daily pve
    """

    await _daily_embed(ctx, "pve")


@daily.command(name="pvp")
@commands.cooldown(1, GW2CoolDowns.Daily.value, BucketType.user)
async def pvp(ctx):
    """(Show PVP Dailies)
            gw2 daily pvp
    """

    await _daily_embed(ctx, "pvp")


@daily.command(name="wvw")
@commands.cooldown(1, GW2CoolDowns.Daily.value, BucketType.user)
async def wvw(ctx):
    """(Show WVW Dailies)
            gw2 daily wvw
    """

    await _daily_embed(ctx, "wvw")


@daily.command(name="fractals")
@commands.cooldown(1, GW2CoolDowns.Daily.value, BucketType.user)
async def fractals(ctx):
    """(Show Fractals Dailies)
            gw2 daily fractals
    """

    await _daily_embed(ctx, "fractals")


async def _daily_embed(ctx, daily_type: str):
    await ctx.message.channel.typing()
    achiev_id_lst = []
    todays_date = bot_utils.get_current_date_time()
    gw2_api = Gw2Api(ctx.bot)

    try:
        endpoint = "achievements/daily"
        api_all_dailies = await gw2_api.call_api(endpoint)
    except Exception as e:
        err = e.args[1] if len(e.args) > 1 else str(e)
        await bot_utils.send_error_msg(ctx, err)
        return ctx.bot.log.error(ctx, e)

    for achiev_id in api_all_dailies[daily_type]:
        achiev_id_lst.append(str(achiev_id["id"]))

    try:
        achiev_ids = ",".join(achiev_id_lst)
        endpoint = f"achievements?ids={achiev_ids}"
        api_daily_desc = await gw2_api.call_api(endpoint)
    except Exception as e:
        err = e.args[1] if len(e.args) > 1 else str(e)
        await bot_utils.send_error_msg(ctx, err)
        return ctx.bot.log.error(ctx, e)

    color = ctx.bot.settings["gw2"]["EmbedColor"]
    embed = discord.Embed(color=color)
    embed.set_author(name=f"Today's {daily_type.upper()} Dailies ({todays_date})",
                     icon_url=ctx.bot.user.avatar.url)

    for x in range(0, len(api_all_dailies[daily_type])):
        await ctx.message.channel.typing()
        name = str(api_daily_desc[x]["name"])
        requirement = str(api_daily_desc[x]["requirement"])

        reward_id = str(api_daily_desc[x]["rewards"][0]["id"])
        try:
            endpoint = f"items/{reward_id}"
            api_items_desc = await gw2_api.call_api(endpoint)
            reward_name = api_items_desc["name"]
            reward_amount = str(api_daily_desc[x]["rewards"][0]["count"])
        except Exception as e:
            err = e.args[1] if len(e.args) > 1 else str(e)
            await bot_utils.send_error_msg(ctx, err)
            return ctx.bot.log.error(ctx, e)

        name = f"{x + 1}) {name} ({reward_amount} {reward_name})"
        value = chat_formatting.inline(requirement)
        embed.add_field(name=name, value=value, inline=False)

    await bot_utils.send_embed(ctx, embed)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Daily(bot))
