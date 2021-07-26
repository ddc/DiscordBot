# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import discord
from src.cogs.bot.utils import chat_formatting as Formatting
from src.cogs.gw2.utils.gw2_api import Gw2Api
from discord.ext import commands
from src.cogs.bot.utils import bot_utils as BotUtils


class GW2Daily(commands.Cog):
    """(Commands related to GW2 Dailies)"""
    def __init__(self, bot):
        self.bot = bot


    async def gw2_daily(self, ctx, daily_type: str):
        if daily_type == "pve":
            await _daily_embed(self, ctx, "pve")
        elif daily_type == "pvp":
            await _daily_embed(self, ctx, "pvp")
        elif daily_type == "wvw":
            await _daily_embed(self, ctx, "wvw")
        elif daily_type == "fractals":
            await _daily_embed(self, ctx, "fractals")
        else:
            msg = "Wrong type.\n Types need to be pve, pvp, wvw, fractals.\nPlease try again."
            await BotUtils.send_error_msg(self, ctx, msg)


async def _daily_embed(self, ctx, daily_type: str):
    import datetime as dt
    await ctx.message.channel.trigger_typing()
    achiev_id_lst = []
    todays_date = BotUtils.convert_date_toStr(dt.datetime.now())
    gw2Api = Gw2Api(self.bot)

    try:
        endpoint = "achievements/daily"
        api_all_dailies = await gw2Api.call_api(endpoint)
    except Exception as e:
        await BotUtils.send_error_msg(self, ctx, e)
        return self.bot.log.error(ctx, e)

    for achiev_id in api_all_dailies[daily_type]:
        achiev_id_lst.append(str(achiev_id["id"]))

    try:
        achiev_ids = ','.join(achiev_id_lst)
        endpoint = f"achievements?ids={achiev_ids}"
        api_daily_desc = await gw2Api.call_api(endpoint)
    except Exception as e:
        await BotUtils.send_error_msg(self, ctx, e)
        return self.bot.log.error(ctx, e)

    color = self.bot.gw2_settings["EmbedColor"]
    embed = discord.Embed(color=color)
    embed.set_author(name=f"Today's {daily_type.upper()} Dailies ({todays_date})",
                     icon_url=self.bot.user.avatar_url)

    for x in range(0, len(api_all_dailies[daily_type])):
        await ctx.message.channel.trigger_typing()
        name = str(api_daily_desc[x]["name"])
        requirement = str(api_daily_desc[x]["requirement"])

        reward_id = str(api_daily_desc[x]["rewards"][0]["id"])
        try:
            endpoint = f"items/{reward_id}"
            api_items_desc = await gw2Api.call_api(endpoint)
            reward_name = api_items_desc["name"]
            reward_amount = str(api_daily_desc[x]["rewards"][0]["count"])
        except Exception as e:
            await BotUtils.send_error_msg(self, ctx, e)
            return self.bot.log.error(ctx, e)

        dt = x + 1
        name = f"{dt}) {name} ({reward_amount} {reward_name})"
        value = Formatting.inline(requirement)

        embed.add_field(name=name, value=value, inline=False)

    await ctx.message.channel.trigger_typing()
    await BotUtils.send_embed(self, ctx, embed, False)
