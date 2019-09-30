#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import discord
from src.cogs.gw2.utils.gw2_exceptions import APIKeyError
from src.sql.gw2.gw2_key_sql import Gw2KeySql
from src.cogs.gw2.utils import gw2_utils as gw2Utils
from src.cogs.bot.utils import bot_utils as utils
from src.cogs.gw2.utils.gw2_api import Gw2Api
from discord.ext import commands
from src.cogs.bot.utils import chat_formatting as formatting
import src.cogs.gw2.utils.gw2_constants as gw2Constants


class GW2WvW(commands.Cog):
    """(Commands related to GW2 World versus World)"""

    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def gw2_wvwinfo(self, ctx, world: str = None):
        discord_user_id = ctx.message.author.id
        await ctx.message.channel.trigger_typing()
        gw2Api = Gw2Api(self.bot)

        if not world:
            try:
                gw2KeySql = Gw2KeySql(self.bot)
                rs = await gw2KeySql.get_server_user_api_key(ctx.guild.id, discord_user_id)
                if len(rs) == 1:
                    api_key = rs[0]["key"]
                    results = await gw2Api.call_api("account", key=api_key)
                    wid = results["world"]
                else:
                    return await utils.send_error_msg(self,
                                                      ctx,
                                                      "You dont have an API key registered in this server.\n"
                                                      f"To add or replace an API key use: `{ctx.prefix}gw2 key add <api_key>`\n"
                                                      f"To check your API key use: `{ctx.prefix}gw2 key info`")
            except APIKeyError as e:
                return await utils.send_error_msg(self, ctx, "No world name or key associated with your account")
            except Exception as e:
                await utils.send_error_msg(self, ctx, e)
                return self.bot.log.error(ctx, e)
        else:
            wid = await gw2Utils.get_world_id(self, world)

        if not wid:
            return await utils.send_error_msg(self, ctx, f"Invalid world name\n{world}")

        try:
            await ctx.message.channel.trigger_typing()
            endpoint = f"wvw/matches?world={wid}"
            matches = await gw2Api.call_api(endpoint)

            endpoint = f"worlds?id={wid}"
            worldinfo = await gw2Api.call_api(endpoint)
        except Exception as e:
            await utils.send_error_msg(self, ctx, e)
            return self.bot.log.error(ctx, e)

        if wid < 2001:
            tier_number = matches["id"].replace("1-", "")
            tier = f"North America Tier {tier_number}"
        else:
            tier_number = matches["id"].replace("2-", "")
            tier = f"Europe Tier {tier_number}"

        for key, value in matches["all_worlds"].items():
            if wid in value:
                worldcolor = key
        if not worldcolor:
            await utils.send_error_msg(self, ctx, "Could not resolve world's color")
            return
        if worldcolor == "red":
            color = discord.Color.red()
        elif worldcolor == "green":
            color = discord.Color.green()
        else:
            color = self.bot.gw2_settings["EmbedColor"]

        ppt = 0
        score = format(matches["scores"][worldcolor], ',d')
        victoryp = matches["victory_points"][worldcolor]

        await ctx.message.channel.trigger_typing()
        for m in matches["maps"]:
            for objective in m["objectives"]:
                if objective["owner"].lower() == worldcolor:
                    ppt += objective["points_tick"]

        population = worldinfo["population"]

        if population == "VeryHigh":
            population = "Very high"

        kills = matches["kills"][worldcolor]
        deaths = matches["deaths"][worldcolor]

        if kills == 0 or deaths == 0:
            kd = "0.0"
        else:
            kd = round((kills / deaths), 3)

        skirmish_now = len(matches["skirmishes"]) - 1
        skirmish = format(matches["skirmishes"][skirmish_now]["scores"][worldcolor], ',d')

        kills = format(matches["kills"][worldcolor], ',d')
        deaths = format(matches["deaths"][worldcolor], ',d')
        _title = f"{worldinfo['name']}"

        embed = discord.Embed(title=_title, description=tier, color=color)
        embed.add_field(name="Score", value=formatting.inline(score), inline=True)
        embed.add_field(name="Points per tick", value=formatting.inline(ppt), inline=True)
        embed.add_field(name="Victory Points", value=formatting.inline(victoryp), inline=True)
        embed.add_field(name="Skirmish", value=formatting.inline(skirmish), inline=True)
        embed.add_field(name="Kills", value=formatting.inline(kills), inline=True)
        embed.add_field(name="Deaths", value=formatting.inline(deaths), inline=True)
        embed.add_field(name="K/D ratio", value=formatting.inline(str(kd)), inline=True)
        embed.add_field(name="Population", value=formatting.inline(population), inline=False)
        await utils.send_embed(self, ctx, embed, False)

    ################################################################################
    async def gw2_match(self, ctx, world: str = None):
        """(Info about a wvw match. Defaults to account's world)
        
        Example:
        gw2 match
        gw2 match world_name
        """

        discord_user_id = ctx.message.author.id
        await ctx.message.channel.trigger_typing()
        gw2Api = Gw2Api(self.bot)

        if not world:
            try:
                gw2KeySql = Gw2KeySql(self.bot)
                rs = await gw2KeySql.get_server_user_api_key(ctx.guild.id, discord_user_id)
                if len(rs) == 1:
                    api_key = rs[0]["key"]
                    results = await gw2Api.call_api("account", key=api_key)
                    wid = results["world"]
                else:
                    return await utils.send_error_msg(self, ctx,
                                                      "Missing World Name\n" \
                                                      f"Use `{ctx.prefix}gw2 match <world_name>`\n" \
                                                      "Or register an API key on your account.\n" \
                                                      f"To add or replace an API key use: `{ctx.prefix}gw2 key add <api_key>`")
            except APIKeyError as e:
                return await utils.send_error_msg(self, ctx, "No world name or API key associated with your account.")
            except Exception as e:
                await utils.send_error_msg(self, ctx, e)
                return self.bot.log.error(ctx, e)
        else:
            wid = await gw2Utils.get_world_id(self, world)

        if not wid:
            return await utils.send_error_msg(self, ctx, f"Invalid world: {world}")

        try:
            await ctx.message.channel.trigger_typing()
            endpoint = f"wvw/matches?world={wid}"
            matches = await gw2Api.call_api(endpoint)

            if wid < 2001:
                tier_number = matches["id"].replace("1-", "")
                tier = f"North America Tier {tier_number}"
            else:
                tier_number = matches["id"].replace("2-", "")
                tier = f"Europe Tier {tier_number}"

            green_worlds_names = await _get_map_names_embed_values(self, "green", matches)
            blue_worlds_names = await _get_map_names_embed_values(self, "blue", matches)
            red_worlds_names = await _get_map_names_embed_values(self, "red", matches)

            green_values = await _get_match_embed_values(self, "green", matches)
            blue_values = await _get_match_embed_values(self, "blue", matches)
            red_values = await _get_match_embed_values(self, "red", matches)
        except Exception as e:
            await utils.send_error_msg(self, ctx, e)
            return self.bot.log.error(ctx, e)

        color = self.bot.gw2_settings["EmbedColor"]
        embed = discord.Embed(title="WvW Score", description=tier, color=color)
        embed.add_field(name="Green", value=green_worlds_names, inline=True)
        embed.add_field(name="Blue", value=blue_worlds_names, inline=True)
        embed.add_field(name="Red", value=red_worlds_names, inline=True)
        embed.add_field(name="--------------------", value=green_values, inline=True)
        embed.add_field(name="--------------------", value=blue_values, inline=True)
        embed.add_field(name="--------------------", value=red_values, inline=True)
        await utils.send_embed(self, ctx, embed, False)

    ################################################################################
    async def gw2_kdr(self, ctx, world: str = None):
        """(Info about a wvw kdr match. Defaults to account's world)
        
        Example:
        gw2 kdr
        gw2 kdr world_name
        """

        discord_user_id = ctx.message.author.id
        await ctx.message.channel.trigger_typing()
        gw2Api = Gw2Api(self.bot)

        if not world:
            try:
                gw2KeySql = Gw2KeySql(self.bot)
                rs = await gw2KeySql.get_server_user_api_key(ctx.guild.id, discord_user_id)
                if len(rs) == 1:
                    api_key = rs[0]["key"]
                    results = await gw2Api.call_api("account", key=api_key)
                    wid = results["world"]
                else:
                    return await utils.send_error_msg(self, ctx,
                                                      f"""Invalid World Name
                                    Use {ctx.prefix}gw2 match <world_name>
                                    Or register an API key on your account.""")
            except APIKeyError as e:
                return await utils.send_error_msg(self, ctx, "No world name or key associated with your account")
            except Exception as e:
                await utils.send_error_msg(self, ctx, e)
                return self.bot.log.error(ctx, e)
        else:
            wid = await gw2Utils.get_world_id(self, world)

        if not wid:
            return await utils.send_error_msg(self, ctx, f"Invalid world: {world}")

        try:
            await ctx.message.channel.trigger_typing()
            endpoint = f"wvw/matches?world={wid}"
            matches = await gw2Api.call_api(endpoint)

            if wid < 2001:
                tier_number = matches["id"].replace("1-", "")
                tier = f"North America Tier {tier_number}"
            else:
                tier_number = matches["id"].replace("2-", "")
                tier = f"Europe Tier {tier_number}"

            green_worlds_names = await _get_map_names_embed_values(self, "green", matches)
            blue_worlds_names = await _get_map_names_embed_values(self, "blue", matches)
            red_worlds_names = await _get_map_names_embed_values(self, "red", matches)

            green_values = await _get_kdr_embed_values(self, "green", matches)
            blue_values = await _get_kdr_embed_values(self, "blue", matches)
            red_values = await _get_kdr_embed_values(self, "red", matches)
        except Exception as e:
            await utils.send_error_msg(self, ctx, e)
            return self.bot.log.error(ctx, e)

        color = self.bot.gw2_settings["EmbedColor"]
        embed = discord.Embed(title="WvW Kills/Death Ratings", description=tier, color=color)
        embed.add_field(name="Green", value=green_worlds_names, inline=True)
        embed.add_field(name="Blue", value=blue_worlds_names, inline=True)
        embed.add_field(name="Red", value=red_worlds_names, inline=True)
        embed.add_field(name="--------------------", value=green_values, inline=True)
        embed.add_field(name="--------------------", value=blue_values, inline=True)
        embed.add_field(name="--------------------", value=red_values, inline=True)
        await utils.send_embed(self, ctx, embed, False)


################################################################################
async def _get_map_names_embed_values(self, map_color: str, matches):
    primary_server_id = []
    all_ids = matches["all_worlds"][map_color]
    primary_server_id.append(str(matches["worlds"][map_color]))

    for ids in all_ids:
        if str(ids) not in primary_server_id:
            primary_server_id.append(str(ids))

    match_ids = ','.join(primary_server_id)
    worlds_names = await gw2Utils.get_world_name_population(self, str(match_ids))
    worlds_names = '\n'.join(worlds_names)

    return worlds_names


################################################################################
async def _get_kdr_embed_values(self, map_color: str, matches):
    kills = matches["kills"][map_color]
    deaths = matches["deaths"][map_color]
    activity = kills + deaths

    if kills == 0 or deaths == 0:
        kd = "0.0"
    else:
        kd = round((kills / deaths), 3)

    values = f"Kills: `{format(kills, ',d')}`\n" \
             f"Deaths: `{format(deaths, ',d')}`\n" \
             f"Activity: `{format(activity, ',d')}`\n" \
             f"K/D: `{kd}`"

    return values


################################################################################
async def _get_match_embed_values(self, map_color: str, matches):
    skirmish_now = len(matches["skirmishes"]) - 1
    ppt = 0
    yaks_delivered = 0
    for m in matches["maps"]:
        for objective in m["objectives"]:
            if objective["owner"].lower() == map_color:
                ppt += objective["points_tick"]
                if "yaks_delivered" in objective:
                    yaks_delivered += objective["yaks_delivered"]

    score = matches["scores"][map_color]
    victoryp = matches["victory_points"][map_color]
    skirmish = matches["skirmishes"][skirmish_now]["scores"][map_color]
    kills = matches["kills"][map_color]
    deaths = matches["deaths"][map_color]
    activity = kills + deaths

    if kills == 0 or deaths == 0:
        kd = "0.0"
    else:
        kd = round((kills / deaths), 3)

    if score == 0:
        ppt_points = "0.0"
        pppt = "0.0"
        pppk = "0.0"
    else:
        ppt_points = int(score - (2 * kills))
        pppt = round((ppt_points * 100) / score, 3)
        pppk = round((2 * kills * 100) / score, 3)

    if matches["maps"][0]["kills"][map_color] == 0 \
            or matches["maps"][0]["deaths"][map_color] == 0:
        kd_blue = "0.0"
    else:
        kd_blue = round((matches["maps"][0]["kills"][map_color] / matches["maps"][0]["deaths"][map_color]), 3)

    if matches["maps"][1]["kills"][map_color] == 0 \
            or matches["maps"][1]["deaths"][map_color] == 0:
        kd_ebg = "0.0"
    else:
        kd_ebg = round((matches["maps"][1]["kills"][map_color] / matches["maps"][1]["deaths"][map_color]), 3)

    if matches["maps"][2]["kills"][map_color] == 0 \
            or matches["maps"][2]["deaths"][map_color] == 0:
        kd_green = "0.0"
    else:
        kd_green = round((matches["maps"][2]["kills"][map_color] / matches["maps"][2]["deaths"][map_color]), 3)

    if matches["maps"][3]["kills"][map_color] == 0 \
            or matches["maps"][3]["deaths"][map_color] == 0:
        kd_red = "0.0"
    else:
        kd_red = round((matches["maps"][3]["kills"][map_color] / matches["maps"][3]["deaths"][map_color]), 3)

    values = f"Score: `{format(score, ',d')}`\n" \
             f"Victory Pts: `{victoryp}`\n" \
             f"PPT: `{ppt}`\n" \
             "---\n" \
             f"Skirmish: `{format(skirmish, ',d')}`\n" \
             f"Yaks Dlv: `{format(yaks_delivered, ',d')}`\n" \
             "---\n" \
             f"Kills: `{format(kills, ',d')}`\n" \
             f"Deaths: `{format(deaths, ',d')}`\n" \
             f"Activity: `{format(activity, ',d')}`\n" \
             f"K/D: `{kd}`\n" \
             "---\n" \
             f"K/D EBG: `{kd_ebg}`\n" \
             f"K/D Green: `{kd_green}`\n" \
             f"K/D Blue: `{kd_blue}`\n" \
             f"K/D Red: `{kd_red}`\n" \
             "---\n" \
             f"%PPT~: `{pppt}`\n" \
             f"%PPK~: `{pppk}`"

    return values
