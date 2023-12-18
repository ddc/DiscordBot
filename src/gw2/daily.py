# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.bot.utils import bot_utils, chat_formatting
from src.gw2.utils.gw2_api import Gw2Api


class GW2Daily(commands.Cog):
    """(Commands related to GW2 Dailies)"""
    def __init__(self, bot):
        self.bot = bot

    async def daily(self, ctx, daily_type: str):
        match daily_type:
            case "pve":
                await _daily_embed(self, ctx, "pve")
            case "pvp":
                await _daily_embed(self, ctx, "pvp")
            case "wvw":
                await _daily_embed(self, ctx, "wvw")
            case "fractals":
                await _daily_embed(self, ctx, "fractals")
            case _:
                msg = "Wrong type.\n Types need to be pve, pvp, wvw, fractals.\nPlease try again."
                await bot_utils.send_error_msg(ctx, msg)


async def _daily_embed(self, ctx, daily_type: str):
    await ctx.message.channel.typing()
    achiev_id_lst = []
    todays_date = discord.utils.utcnow().strftime("%c")
    gw2_api = Gw2Api(self.bot)

    try:
        endpoint = "achievements/daily"
        api_all_dailies = await gw2_api.call_api(endpoint)
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e)
        return self.bot.log.error(ctx, e)

    for achiev_id in api_all_dailies[daily_type]:
        achiev_id_lst.append(str(achiev_id["id"]))

    try:
        achiev_ids = ','.join(achiev_id_lst)
        endpoint = f"achievements?ids={achiev_ids}"
        api_daily_desc = await gw2_api.call_api(endpoint)
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e)
        return self.bot.log.error(ctx, e)

    color = self.bot.gw2_settings["EmbedColor"]
    embed = discord.Embed(color=color)
    embed.set_author(name=f"Today's {daily_type.upper()} Dailies ({todays_date})",
                     icon_url=self.bot.user.avatar.url)

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
            await bot_utils.send_error_msg(ctx, e)
            return self.bot.log.error(ctx, e)

        name = f"{x + 1}) {name} ({reward_amount} {reward_name})"
        value = chat_formatting.inline(requirement)
        embed.add_field(name=name, value=value, inline=False)

    await bot_utils.send_embed(ctx, embed)
