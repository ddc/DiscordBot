import asyncio
import discord
from discord.ext import commands
from src.bot.tools import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages, gw2_variables
from src.gw2.constants.gw2_teams import get_team_name, is_wr_team_id
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns
from src.gw2.tools.gw2_exceptions import APIKeyError


class GW2WvW(GuildWars2):
    """Guild Wars 2 World vs World commands."""

    def __init__(self, bot):
        super().__init__(bot)


@GW2WvW.gw2.group()
async def wvw(ctx):
    """Guild Wars 2 World vs World commands.

    Available subcommands:
        gw2 wvw info [world] - Info about a WvW world
        gw2 wvw match [world] - WvW match scores
        gw2 wvw kdr [world] - WvW kill/death ratios
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 wvw")


@wvw.command(name="info")
@commands.cooldown(1, GW2CoolDowns.Wvw.seconds, commands.BucketType.user)
async def info(ctx, *, world: str = None):
    """Display WvW information for a world. Defaults to your account's world.

    Usage:
        gw2 wvw info
        gw2 wvw info Blackgate
    """
    await ctx.message.channel.typing()
    gw2_api = Gw2Client(ctx.bot)

    no_api_key_msg = gw2_messages.Key.NO_API_KEY
    no_api_key_msg += gw2_messages.Key.add_info_help(ctx.prefix)
    no_api_key_msg += gw2_messages.Key.more_info_help(ctx.prefix)

    wid = await _resolve_wvw_world_id(ctx, gw2_api, world, no_api_key_msg)
    if not wid:
        if world:
            return await bot_utils.send_error_msg(ctx, f"{gw2_messages.Wvw.INVALID_WORLD_NAME}\n{world}")
        return None

    progress_msg = await gw2_utils.send_progress_embed(
        ctx, "Please wait, I'm fetching WvW info... (this may take a moment)"
    )

    try:
        # Fetch match data and world info in parallel when possible
        if is_wr_team_id(wid):
            matches = await gw2_api.call_api(f"{gw2_variables.API_WVW_MATCHES}?world={wid}")
            world_name = get_team_name(wid) or f"Team {wid}"
            population = "N/A"
        else:
            matches, worldinfo = await asyncio.gather(
                gw2_api.call_api(f"{gw2_variables.API_WVW_MATCHES}?world={wid}"),
                gw2_api.call_api(f"{gw2_variables.API_WORLDS}?id={wid}"),
            )
            world_name = worldinfo["name"]
            population = worldinfo["population"]
    except Exception as e:
        await progress_msg.delete()
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)

    tier = _resolve_tier(matches)

    worldcolor = _find_world_color(matches, wid)
    if not worldcolor:
        return await bot_utils.send_error_msg(ctx, gw2_messages.Wvw.WORLD_COLOR_ERROR)

    color = _discord_color(worldcolor)
    score = format(matches["scores"][worldcolor], ",d")
    victoryp = matches["victory_points"][worldcolor]

    await ctx.message.channel.typing()
    ppt, _ = _points_per_tick_and_yaks(matches, worldcolor)

    if population == "VeryHigh":
        population = "Very high"

    kd = _kd_ratio(matches["kills"][worldcolor], matches["deaths"][worldcolor])
    skirmish = format(matches["skirmishes"][-1]["scores"][worldcolor], ",d")
    kills = format(matches["kills"][worldcolor], ",d")
    deaths = format(matches["deaths"][worldcolor], ",d")

    embed = discord.Embed(title=world_name, description=tier, color=color)
    embed.add_field(name="Score", value=chat_formatting.inline(score))
    embed.add_field(name="Points per tick", value=chat_formatting.inline(ppt))
    embed.add_field(name="Victory Points", value=chat_formatting.inline(victoryp))
    embed.add_field(name="Skirmish", value=chat_formatting.inline(skirmish))
    embed.add_field(name="Kills", value=chat_formatting.inline(kills))
    embed.add_field(name="Deaths", value=chat_formatting.inline(deaths))
    embed.add_field(name="K/D ratio", value=chat_formatting.inline(str(kd)))
    embed.add_field(name="Population", value=chat_formatting.inline(population), inline=False)
    await progress_msg.delete()
    await bot_utils.send_embed(ctx, embed)
    return None


@wvw.command(name="match")
@commands.cooldown(1, GW2CoolDowns.Wvw.seconds, commands.BucketType.user)
async def match(ctx, *, world: str = None):
    """Display WvW match scores. Defaults to your account's world.

    Usage:
        gw2 wvw match
        gw2 wvw match Blackgate
    """

    await ctx.message.channel.typing()
    gw2_api = Gw2Client(ctx.bot)

    no_key_msg = gw2_messages.Wvw.MISSING_WORLD_NAME
    no_key_msg += gw2_messages.Wvw.match_world_name_help(ctx.prefix)
    no_key_msg += gw2_messages.Key.add_info_help(ctx.prefix)
    no_key_msg += gw2_messages.Key.more_info_help(ctx.prefix)

    wid = await _resolve_wvw_world_id(ctx, gw2_api, world, no_key_msg)
    if not wid:
        if world:
            return await bot_utils.send_error_msg(ctx, f"{gw2_messages.Wvw.INVALID_WORLD_NAME}: {world}")
        return None

    progress_msg = await gw2_utils.send_progress_embed(
        ctx, "Please wait, I'm fetching WvW match data... (this may take a moment)"
    )

    try:
        matches = await gw2_api.call_api(f"{gw2_variables.API_WVW_MATCHES}?world={wid}")

        tier = _resolve_tier(matches)

        green_worlds_names, blue_worlds_names, red_worlds_names = await asyncio.gather(
            _get_map_names_embed_values(ctx, "green", matches),
            _get_map_names_embed_values(ctx, "blue", matches),
            _get_map_names_embed_values(ctx, "red", matches),
        )
        green_values = _get_match_embed_values("green", matches)
        blue_values = _get_match_embed_values("blue", matches)
        red_values = _get_match_embed_values("red", matches)
    except Exception as e:
        await progress_msg.delete()
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
    await progress_msg.delete()
    await bot_utils.send_embed(ctx, embed)
    return None


@wvw.command(name="kdr")
@commands.cooldown(1, GW2CoolDowns.Wvw.seconds, commands.BucketType.user)
async def kdr(ctx, *, world: str = None):
    """Display WvW kill/death ratios. Defaults to your account's world.

    Usage:
        gw2 wvw kdr
        gw2 wvw kdr Blackgate
    """

    await ctx.message.channel.typing()
    gw2_api = Gw2Client(ctx.bot)

    no_key_msg = gw2_messages.Wvw.INVALID_WORLD_NAME
    no_key_msg += gw2_messages.Wvw.match_world_name_help(ctx.prefix)
    no_key_msg += gw2_messages.Key.add_info_help(ctx.prefix)
    no_key_msg += gw2_messages.Key.more_info_help(ctx.prefix)

    wid = await _resolve_wvw_world_id(ctx, gw2_api, world, no_key_msg)
    if not wid:
        if world:
            return await bot_utils.send_error_msg(ctx, f"{gw2_messages.Wvw.INVALID_WORLD_NAME}: {world}")
        return None

    progress_msg = await gw2_utils.send_progress_embed(
        ctx, "Please wait, I'm fetching WvW K/D data... (this may take a moment)"
    )

    try:
        matches = await gw2_api.call_api(f"{gw2_variables.API_WVW_MATCHES}?world={wid}")

        tier = _resolve_tier(matches)

        green_worlds_names, blue_worlds_names, red_worlds_names = await asyncio.gather(
            _get_map_names_embed_values(ctx, "green", matches),
            _get_map_names_embed_values(ctx, "blue", matches),
            _get_map_names_embed_values(ctx, "red", matches),
        )
        green_values = _get_kdr_embed_values("green", matches)
        blue_values = _get_kdr_embed_values("blue", matches)
        red_values = _get_kdr_embed_values("red", matches)
    except Exception as e:
        await progress_msg.delete()
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)

    color = ctx.bot.settings["gw2"]["EmbedColor"]
    embed = discord.Embed(title=gw2_messages.Wvw.KDR_TITLE, description=tier, color=color)
    embed.add_field(name="Green", value=green_worlds_names)
    embed.add_field(name="Blue", value=blue_worlds_names)
    embed.add_field(name="Red", value=red_worlds_names)
    embed.add_field(name="--------------------", value=green_values)
    embed.add_field(name="--------------------", value=blue_values)
    embed.add_field(name="--------------------", value=red_values)
    await progress_msg.delete()
    await bot_utils.send_embed(ctx, embed)
    return None


async def _resolve_wvw_world_id(ctx, gw2_api, world, error_msg):
    """Resolve a WvW world/team ID from world name or account data.

    Returns the world/team ID, or None if resolution failed (error already sent).
    """
    if world:
        return await gw2_utils.get_world_id(ctx.bot, world)

    try:
        gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
        rs = await gw2_key_dal.get_api_key_by_user(ctx.message.author.id)
        if not rs:
            await bot_utils.send_error_msg(ctx, error_msg)
            return None

        api_key = rs[0]["key"]
        results = await gw2_api.call_api(gw2_variables.API_ACCOUNT, api_key)
        # Prefer WR team_id over legacy world
        return results.get("wvw", {}).get("team_id") or results["world"]
    except APIKeyError:
        await bot_utils.send_error_msg(ctx, error_msg)
        return None
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e)
        ctx.bot.log.error(ctx, e)
        return None


def _resolve_tier(matches: dict) -> str:
    """Resolve tier string from match ID (works for both legacy and WR matches)."""
    match_id = matches["id"]
    if match_id.startswith("1-"):
        tier_number = match_id.replace("1-", "")
        return f"{gw2_messages.Wvw.NA_TIER_TITLE} {tier_number}"
    else:
        tier_number = match_id.replace("2-", "")
        return f"{gw2_messages.Wvw.EU_TIER_TITLE} {tier_number}"


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


def _find_world_color(matches: dict, wid) -> str | None:
    """Return the team color ("red"/"green"/"blue") that contains the given world/team ID."""
    world_color = None
    for color, world_ids in matches["all_worlds"].items():
        if wid in world_ids:
            world_color = color
    return world_color


def _discord_color(world_color: str) -> discord.Color:
    match world_color:
        case "red":
            return discord.Color.red()
        case "green":
            return discord.Color.green()
        case "blue":
            return discord.Color.blue()
        case _:
            return discord.Color.default()


def _kd_ratio(kills: int, deaths: int) -> float | str:
    """K/D rounded to 3 places, or "0.0" when either side is zero."""
    if kills == 0 or deaths == 0:
        return "0.0"
    return round(kills / deaths, 3)


def _points_per_tick_and_yaks(matches: dict, map_color: str) -> tuple[int, int]:
    """Sum points-per-tick and yaks delivered over all objectives owned by map_color."""
    ppt = 0
    yaks_delivered = 0
    for m in matches["maps"]:
        for objective in m["objectives"]:
            if objective["owner"].lower() == map_color:
                ppt += objective["points_tick"]
                yaks_delivered += objective.get("yaks_delivered", 0)
    return ppt, yaks_delivered


def _get_kdr_embed_values(map_color: str, matches):
    kills = matches["kills"][map_color]
    deaths = matches["deaths"][map_color]
    activity = kills + deaths
    kd = _kd_ratio(kills, deaths)

    values = (
        f"Kills: `{format(kills, ',d')}`\n"
        f"Deaths: `{format(deaths, ',d')}`\n"
        f"Activity: `{format(activity, ',d')}`\n"
        f"K/D: `{kd}`"
    )

    return values


def _get_match_embed_values(map_color: str, matches):
    ppt, yaks_delivered = _points_per_tick_and_yaks(matches, map_color)

    score = matches["scores"][map_color]
    victoryp = matches["victory_points"][map_color]
    skirmish = matches["skirmishes"][-1]["scores"][map_color]
    kills = matches["kills"][map_color]
    deaths = matches["deaths"][map_color]
    activity = kills + deaths
    kd = _kd_ratio(kills, deaths)

    if score == 0:
        pppt = "0.0"
        pppk = "0.0"
    else:
        ppt_points = int(score - (2 * kills))
        pppt = round((ppt_points * 100) / score, 3)
        pppk = round((2 * kills * 100) / score, 3)

    # Look maps up by type; the API returns them as Center, RedHome, BlueHome, GreenHome
    maps_by_type = {m.get("type"): m for m in matches["maps"]}

    def map_kd(map_type: str) -> float | str:
        wvw_map = maps_by_type.get(map_type)
        return _kd_ratio(wvw_map["kills"][map_color], wvw_map["deaths"][map_color]) if wvw_map else "0.0"

    kd_ebg, kd_green, kd_blue, kd_red = (map_kd(t) for t in ("Center", "GreenHome", "BlueHome", "RedHome"))

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
