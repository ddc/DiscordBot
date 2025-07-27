import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.tools import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns
from src.gw2.tools.gw2_exceptions import APIKeyError


class GW2WvW(GuildWars2):
    """(Commands related to GW2 World versus World)"""

    def __init__(self, bot):
        super().__init__(bot)


@GW2WvW.gw2.group()
async def wvw(ctx):
    """(Guild Wars 2 Configuration Commands - Admin)
    gw2 wvw info world_name
    gw2 wvw match world_name
    gw2 wvw kdr world_name
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 wvw")


@wvw.command(name="info")
@commands.cooldown(1, GW2CoolDowns.Wvw.value, BucketType.user)
async def info(ctx, *, world: str = None):
    await ctx.message.channel.typing()
    gw2_api = Gw2Client(ctx.bot)

    no_api_key_msg = gw2_messages.NO_API_KEY
    no_api_key_msg += gw2_messages.KEY_ADD_INFO_HELP.format(ctx.prefix)
    no_api_key_msg += gw2_messages.KEY_MORE_INFO_HELP.format(ctx.prefix)

    if not world:
        try:
            gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
            rs = await gw2_key_dal.get_api_key_by_user(ctx.message.author.id)
            if not rs:
                return await bot_utils.send_error_msg(ctx, no_api_key_msg)

            api_key = rs[0]["key"]
            results = await gw2_api.call_api("account", api_key)
            wid = results["world"]
        except APIKeyError:
            return await bot_utils.send_error_msg(ctx, no_api_key_msg)
        except Exception as e:
            await bot_utils.send_error_msg(ctx, e)
            return ctx.bot.log.error(ctx, e)
    else:
        wid = await gw2_utils.get_world_id(ctx, world)

    if not wid:
        return await bot_utils.send_error_msg(ctx, f"{gw2_messages.INVALID_WORLD_NAME}\n{world}")

    try:
        await ctx.message.channel.typing()
        matches = await gw2_api.call_api(f"wvw/matches?world={wid}")
        worldinfo = await gw2_api.call_api(f"worlds?id={wid}")
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)

    if wid < 2001:
        tier_number = matches["id"].replace("1-", "")
        tier = f"North America Tier {tier_number}"
    else:
        tier_number = matches["id"].replace("2-", "")
        tier = f"Europe Tier {tier_number}"

    worldcolor = None
    for key, value in matches["all_worlds"].items():
        if wid in value:
            worldcolor = key
    if not worldcolor:
        return await bot_utils.send_error_msg(ctx, gw2_messages.WORLD_COLOR_ERROR)

    match worldcolor:
        case "red":
            color = discord.Color.red()
        case "green":
            color = discord.Color.green()
        case "blue":
            color = discord.Color.blue()
        case _:
            color = discord.Color.default()

    ppt = 0
    score = format(matches["scores"][worldcolor], ',d')
    victoryp = matches["victory_points"][worldcolor]

    await ctx.message.channel.typing()
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
    title = f"{worldinfo['name']}"

    embed = discord.Embed(title=title, description=tier, color=color)
    embed.add_field(name="Score", value=chat_formatting.inline(score))
    embed.add_field(name="Points per tick", value=chat_formatting.inline(ppt))
    embed.add_field(name="Victory Points", value=chat_formatting.inline(victoryp))
    embed.add_field(name="Skirmish", value=chat_formatting.inline(skirmish))
    embed.add_field(name="Kills", value=chat_formatting.inline(kills))
    embed.add_field(name="Deaths", value=chat_formatting.inline(deaths))
    embed.add_field(name="K/D ratio", value=chat_formatting.inline(str(kd)))
    embed.add_field(name="Population", value=chat_formatting.inline(population), inline=False)
    await bot_utils.send_embed(ctx, embed)
    return None


@wvw.command(name="match")
@commands.cooldown(1, GW2CoolDowns.Wvw.value, BucketType.user)
async def match(ctx, *, world: str = None):
    """(Info about a wvw match. Defaults to account's world)

    gw2 match
    gw2 match world_name
    """

    await ctx.message.channel.typing()
    gw2_api = Gw2Client(ctx.bot)

    if not world:
        try:
            gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
            rs = await gw2_key_dal.get_api_key_by_user(ctx.message.author.id)
            if not rs:
                msg = gw2_messages.MISSING_WORLD_NAME
                msg += gw2_messages.MATCH_WORLD_NAME_HELP.format(ctx.prefix)
                msg += gw2_messages.KEY_ADD_INFO_HELP.format(ctx.prefix)
                msg += gw2_messages.KEY_MORE_INFO_HELP.format(ctx.prefix)
                return await bot_utils.send_error_msg(ctx, msg)

            api_key = rs[0]["key"]
            results = await gw2_api.call_api("account", api_key)
            wid = results["world"]
        except APIKeyError:
            return await bot_utils.send_error_msg(ctx, gw2_messages.NO_API_KEY)
        except Exception as e:
            await bot_utils.send_error_msg(ctx, e)
            return ctx.bot.log.error(ctx, e)
    else:
        wid = await gw2_utils.get_world_id(ctx, world)

    if not wid:
        return await bot_utils.send_error_msg(ctx, f"{gw2_messages.INVALID_WORLD_NAME}: {world}")

    try:
        await ctx.message.channel.typing()
        matches = await gw2_api.call_api(f"wvw/matches?world={wid}")

        if wid < 2001:
            tier_number = matches["id"].replace("1-", "")
            tier = f"North America Tier {tier_number}"
        else:
            tier_number = matches["id"].replace("2-", "")
            tier = f"Europe Tier {tier_number}"

        green_worlds_names = await _get_map_names_embed_values(ctx, "green", matches)
        blue_worlds_names = await _get_map_names_embed_values(ctx, "blue", matches)
        red_worlds_names = await _get_map_names_embed_values(ctx, "red", matches)

        green_values = await _get_match_embed_values("green", matches)
        blue_values = await _get_match_embed_values("blue", matches)
        red_values = await _get_match_embed_values("red", matches)
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)

    color = ctx.bot.settings["gw2"]["EmbedColor"]
    embed = discord.Embed(title="WvW Score", description=tier, color=color)
    embed.add_field(name="Green", value=green_worlds_names)
    embed.add_field(name="Blue", value=blue_worlds_names)
    embed.add_field(name="Red", value=red_worlds_names)
    embed.add_field(name="--------------------", value=green_values)
    embed.add_field(name="--------------------", value=blue_values)
    embed.add_field(name="--------------------", value=red_values)
    await bot_utils.send_embed(ctx, embed)
    return None


@wvw.command(name="kdr")
@commands.cooldown(1, GW2CoolDowns.Wvw.value, BucketType.user)
async def kdr(ctx, *, world: str = None):
    """(Info about a wvw kdr match. Defaults to account's world)
    gw2 kdr
    gw2 kdr world_name
    """

    await ctx.message.channel.typing()
    gw2_api = Gw2Client(ctx.bot)

    if not world:
        try:
            gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
            rs = await gw2_key_dal.get_api_key_by_user(ctx.message.author.id)
            if not rs:
                msg = gw2_messages.INVALID_WORLD_NAME
                msg += gw2_messages.MATCH_WORLD_NAME_HELP.format(ctx.prefix)
                msg += gw2_messages.KEY_ADD_INFO_HELP.format(ctx.prefix)
                msg += gw2_messages.KEY_MORE_INFO_HELP.format(ctx.prefix)
                return await bot_utils.send_error_msg(ctx, msg)
            api_key = rs[0]["key"]
            results = await gw2_api.call_api("account", api_key)
            wid = results["world"]
        except APIKeyError:
            return await bot_utils.send_error_msg(ctx, gw2_messages.NO_API_KEY)
        except Exception as e:
            await bot_utils.send_error_msg(ctx, e)
            return ctx.bot.log.error(ctx, e)
    else:
        wid = await gw2_utils.get_world_id(ctx, world)

    if not wid:
        return await bot_utils.send_error_msg(ctx, f"{gw2_messages.INVALID_WORLD_NAME}: {world}")

    try:
        await ctx.message.channel.typing()
        matches = await gw2_api.call_api(f"wvw/matches?world={wid}")

        if wid < 2001:
            tier_number = matches["id"].replace("1-", "")
            tier = f"{gw2_messages.NA_TIER_TITLE} {tier_number}"
        else:
            tier_number = matches["id"].replace("2-", "")
            tier = f"{gw2_messages.EU_TIER_TITLE}{tier_number}"

        green_worlds_names = await _get_map_names_embed_values(ctx, "green", matches)
        blue_worlds_names = await _get_map_names_embed_values(ctx, "blue", matches)
        red_worlds_names = await _get_map_names_embed_values(ctx, "red", matches)

        green_values = await _get_kdr_embed_values("green", matches)
        blue_values = await _get_kdr_embed_values("blue", matches)
        red_values = await _get_kdr_embed_values("red", matches)
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)

    color = ctx.bot.settings["gw2"]["EmbedColor"]
    embed = discord.Embed(title=gw2_messages.WVW_KDR_TITLE, description=tier, color=color)
    embed.add_field(name="Green", value=green_worlds_names)
    embed.add_field(name="Blue", value=blue_worlds_names)
    embed.add_field(name="Red", value=red_worlds_names)
    embed.add_field(name="--------------------", value=green_values)
    embed.add_field(name="--------------------", value=blue_values)
    embed.add_field(name="--------------------", value=red_values)
    await bot_utils.send_embed(ctx, embed)
    return None


async def _get_map_names_embed_values(ctx, map_color: str, matches):
    primary_server_id = []
    all_ids = matches["all_worlds"][map_color]
    primary_server_id.append(str(matches["worlds"][map_color]))

    for ids in all_ids:
        if str(ids) not in primary_server_id:
            primary_server_id.append(str(ids))

    match_ids = ",".join(primary_server_id)
    worlds_names = await gw2_utils.get_world_name_population(ctx, str(match_ids))
    worlds_names = "\n".join(worlds_names)

    return worlds_names


async def _get_kdr_embed_values(map_color: str, matches):
    kills = matches["kills"][map_color]
    deaths = matches["deaths"][map_color]
    activity = kills + deaths

    if kills == 0 or deaths == 0:
        kd = "0.0"
    else:
        kd = round((kills / deaths), 3)

    values = (
        f"Kills: `{format(kills, ',d')}`\n"
        f"Deaths: `{format(deaths, ',d')}`\n"
        f"Activity: `{format(activity, ',d')}`\n"
        f"K/D: `{kd}`"
    )

    return values


async def _get_match_embed_values(map_color: str, matches):
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
        pppt = "0.0"
        pppk = "0.0"
    else:
        ppt_points = int(score - (2 * kills))
        pppt = round((ppt_points * 100) / score, 3)
        pppk = round((2 * kills * 100) / score, 3)

    if matches["maps"][0]["kills"][map_color] == 0 or matches["maps"][0]["deaths"][map_color] == 0:
        kd_blue = "0.0"
    else:
        kd_blue = round((matches["maps"][0]["kills"][map_color] / matches["maps"][0]["deaths"][map_color]), 3)

    if matches["maps"][1]["kills"][map_color] == 0 or matches["maps"][1]["deaths"][map_color] == 0:
        kd_ebg = "0.0"
    else:
        kd_ebg = round((matches["maps"][1]["kills"][map_color] / matches["maps"][1]["deaths"][map_color]), 3)

    if matches["maps"][2]["kills"][map_color] == 0 or matches["maps"][2]["deaths"][map_color] == 0:
        kd_green = "0.0"
    else:
        kd_green = round((matches["maps"][2]["kills"][map_color] / matches["maps"][2]["deaths"][map_color]), 3)

    if matches["maps"][3]["kills"][map_color] == 0 or matches["maps"][3]["deaths"][map_color] == 0:
        kd_red = "0.0"
    else:
        kd_red = round((matches["maps"][3]["kills"][map_color] / matches["maps"][3]["deaths"][map_color]), 3)

    values = (
        f"Score: `{format(score, ',d')}`\n"
        f"Victory Pts: `{victoryp}`\n"
        f"PPT: `{ppt}`\n"
        "---\n"
        f"Skirmish: `{format(skirmish, ',d')}`\n"
        f"Yaks Dlv: `{format(yaks_delivered, ',d')}`\n"
        "---\n"
        f"Kills: `{format(kills, ',d')}`\n"
        f"Deaths: `{format(deaths, ',d')}`\n"
        f"Activity: `{format(activity, ',d')}`\n"
        f"K/D: `{kd}`\n"
        "---\n"
        f"K/D EBG: `{kd_ebg}`\n"
        f"K/D Green: `{kd_green}`\n"
        f"K/D Blue: `{kd_blue}`\n"
        f"K/D Red: `{kd_red}`\n"
        "---\n"
        f"%PPT~: `{pppt}`\n"
        f"%PPK~: `{pppk}`"
    )

    return values


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2WvW(bot))
