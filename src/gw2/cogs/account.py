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


async def _fetch_guild_info_standalone(gw2_api, guild_id, api_key, ctx):
    """Helper to fetch individual guild information."""
    try:
        api_req_guild = await gw2_api.call_api(f"{gw2_variables.API_GUILD}/{guild_id}", api_key)
        name = api_req_guild["name"]
        tag = api_req_guild["tag"]
        return f"[{tag}] {name}", guild_id
    except Exception as e:
        ctx.bot.log.error(f"Error fetching guild {guild_id}: {e}")
        return None, guild_id


class GW2Account(GuildWars2):
    """Guild Wars 2 commands for account information."""

    def __init__(self, bot):
        super().__init__(bot)


def _key_help_msg(ctx, header: str) -> str:
    return header + gw2_messages.Key.add_info_help(ctx.prefix) + gw2_messages.Key.more_info_help(ctx.prefix)


def _format_access(access_list: list[str]) -> str:
    """Turn API access names like "GuildWars2" / "HeartOfThorns" into "Guild Wars 2" / "Heart Of Thorns"."""
    normalized = (
        "".join(f" {c.upper()}" if c.isupper() or c.isdigit() else c for c in each).lstrip() for each in access_list
    )
    return "\n".join(normalized)


async def _resolve_server(gw2_api, server_id, api_key) -> tuple[str, str]:
    """Return (server name, population), handling WR team IDs vs legacy worlds."""
    if is_wr_team_id(server_id):
        return get_team_name(server_id) or f"Team {server_id}", "N/A"
    api_req_server = await gw2_api.call_api(f"{gw2_variables.API_WORLDS}/{server_id}", api_key)
    return api_req_server["name"], api_req_server["population"]


def _build_base_embed(ctx, api_req_acc: dict, server_name: str, population: str) -> discord.Embed:
    color = ctx.bot.settings["gw2"]["EmbedColor"]
    avatar_url = ctx.message.author.display_avatar.url
    embed = discord.Embed(title="Account Name", description=chat_formatting.inline(api_req_acc["name"]), color=color)
    embed.set_thumbnail(url=avatar_url)
    embed.set_author(name=ctx.message.author.display_name, icon_url=avatar_url)
    embed.add_field(name="Access", value=chat_formatting.inline(_format_access(api_req_acc["access"])), inline=False)
    embed.add_field(name="Commander Tag", value=chat_formatting.inline("Yes" if api_req_acc["commander"] else "No"))
    embed.add_field(name="Server", value=chat_formatting.inline(f"{server_name} ({population})"))

    wvw_team_id = api_req_acc.get("wvw", {}).get("team_id")
    if wvw_team_id:
        team_name = get_team_name(wvw_team_id) or f"Team {wvw_team_id}"
        embed.add_field(name="WvW Team", value=chat_formatting.inline(team_name))
    return embed


async def _add_achievement_fields(ctx, embed: discord.Embed, achievements, api_req_acc: dict) -> None:
    embed.add_field(name="Fractal Level", value=chat_formatting.inline(api_req_acc["fractal_level"]), inline=False)

    achiev_points = await gw2_utils.calculate_user_achiev_points(ctx, achievements, api_req_acc)
    embed.add_field(name="Achievements Points", value=chat_formatting.inline(str(achiev_points)), inline=False)

    wvwrank = api_req_acc.get("wvw", {}).get("rank") or api_req_acc.get("wvw_rank", 0)
    wvw_title = gw2_utils.get_wvw_rank_title(int(wvwrank))
    embed.add_field(name="WvW Rank", value=chat_formatting.inline(f"{wvw_title} ({wvwrank})"), inline=False)


def _add_pvp_field(embed: discord.Embed, pvp_stats: dict) -> None:
    pvprank = pvp_stats["pvp_rank"] + pvp_stats["pvp_rank_rollovers"]
    pvp_title = str(gw2_utils.get_pvp_rank_title(pvprank))
    embed.add_field(name="PVP Rank", value=chat_formatting.inline(f"{pvp_title} ({pvprank})"), inline=False)


async def _add_optional_fields(ctx, gw2_api, api_key, permissions, api_req_acc, embed, progress_msg, progress_embed):
    """Fetch the permission-gated endpoints in parallel and add their fields."""
    # (required permission, result name, endpoint)
    endpoints = (
        ("characters", "characters", gw2_variables.API_CHARACTERS),
        ("progression", "achievements", gw2_variables.API_ACCOUNT_ACHIEVEMENTS),
        ("pvp", "pvp", gw2_variables.API_PVP_STATS),
    )
    optional_tasks = [(name, gw2_api.call_api(uri, api_key)) for perm, name, uri in endpoints if perm in permissions]
    if not optional_tasks:
        return

    progress_embed.description = "🔄 **Please wait, I'm fetching additional details...** (this may take a moment)"
    await progress_msg.edit(embed=progress_embed)

    results = await asyncio.gather(*[task for _, task in optional_tasks], return_exceptions=True)
    for (name, _), result in zip(optional_tasks, results, strict=True):
        if isinstance(result, Exception):
            ctx.bot.log.warning(f"Failed to fetch {name}: {result}")
        elif name == "characters":
            embed.add_field(name="Characters", value=chat_formatting.inline(str(len(result))), inline=False)
        elif name == "achievements":
            await _add_achievement_fields(ctx, embed, result, api_req_acc)
        else:
            _add_pvp_field(embed, result)


async def _add_guild_fields(ctx, gw2_api, api_key, api_req_acc, embed, progress_msg, progress_embed):
    """Fetch guild names (the most expensive part) and add Guilds / Guild Leader fields."""
    guild_ids = api_req_acc.get("guilds")
    if not guild_ids:
        return

    progress_embed.description = f"🔄 **Please wait, I'm fetching guild information...** ({len(guild_ids)} guilds)"
    await progress_msg.edit(embed=progress_embed)

    # Limit concurrent guild requests to avoid overwhelming the API
    sem = asyncio.Semaphore(3)

    async def limited_guild_fetch(guild_id):
        async with sem:
            return await _fetch_guild_info_standalone(gw2_api, guild_id, api_key, ctx)

    guild_results = await asyncio.gather(*[limited_guild_fetch(gid) for gid in guild_ids], return_exceptions=True)

    guild_leader_ids = set(api_req_acc.get("guild_leader", []))
    named = [r for r in guild_results if not isinstance(r, Exception) and r[0]]
    guilds_names = [name for name, _ in named]
    guild_leader_names = [name for name, gid in named if gid in guild_leader_ids]

    if guilds_names:
        embed.add_field(name="Guilds", value=chat_formatting.inline("\n".join(guilds_names)), inline=False)
    if guild_leader_names:
        embed.add_field(name="Guild Leader", value=chat_formatting.inline("\n".join(guild_leader_names)), inline=False)


@GW2Account.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Account.seconds, commands.BucketType.user)
async def account(ctx):
    """Display general information about your Guild Wars 2 account.

    Required API permissions: account

    Usage:
        gw2 account
    """

    # Database and key validation
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    rs = await gw2_key_dal.get_api_key_by_user(ctx.message.author.id)
    if not rs:
        return await bot_utils.send_error_msg(ctx, _key_help_msg(ctx, gw2_messages.Key.NO_API_KEY))

    api_key = str(rs[0]["key"])
    permissions = str(rs[0]["permissions"])
    gw2_api = Gw2Client(ctx.bot)

    # Validate API key
    is_valid_key = await gw2_api.check_api_key(api_key)
    if not isinstance(is_valid_key, dict):
        header = f"{is_valid_key.message}\n{gw2_messages.Key.INVALID_KEY_HELP}"
        return await bot_utils.send_error_msg(ctx, _key_help_msg(ctx, header))

    if "account" not in permissions:
        return await bot_utils.send_error_msg(ctx, gw2_messages.Key.NO_ACCOUNT_PERMISSION, True)

    try:
        # Send progress message as embed
        progress_embed = discord.Embed(
            description="🔄 **Please wait, I'm fetching your account data from GW2 API...** (this may take a moment)",
            color=ctx.bot.settings["gw2"]["EmbedColor"],
        )
        progress_embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.display_avatar.url)
        progress_msg = await bot_utils.send_with_retry(ctx, ctx.send, embed=progress_embed)

        api_req_acc = await gw2_api.call_api(gw2_variables.API_ACCOUNT, api_key)
        server_name, population = await _resolve_server(gw2_api, api_req_acc["world"], api_key)
        embed = _build_base_embed(ctx, api_req_acc, server_name, population)

        progress = (progress_msg, progress_embed)
        await _add_optional_fields(ctx, gw2_api, api_key, permissions, api_req_acc, embed, *progress)
        await _add_guild_fields(ctx, gw2_api, api_key, api_req_acc, embed, *progress)

        created = api_req_acc["created"].split("T", 1)[0]
        embed.add_field(name="Created", value=chat_formatting.inline(created), inline=False)
        embed.set_footer(
            icon_url=ctx.bot.user.display_avatar.url,
            text=f"{bot_utils.get_current_date_time_str_long()} UTC",
        )

        # Clean up progress message and send final result
        await progress_msg.delete()
        await bot_utils.send_embed(ctx, embed)

    except Exception as e:
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Account(bot))
