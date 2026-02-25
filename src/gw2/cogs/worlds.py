import asyncio
import discord
from discord.ext import commands
from src.bot.tools import bot_utils, chat_formatting
from src.bot.tools.bot_utils import EmbedPaginatorView
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


class GW2Worlds(GuildWars2):
    """Guild Wars 2 commands for listing worlds and WvW tiers."""

    def __init__(self, bot):
        super().__init__(bot)


@GW2Worlds.gw2.group()
async def worlds(ctx):
    """List all Guild Wars 2 worlds by region.

    Available subcommands:
        gw2 worlds na - List all NA worlds with WvW tier
        gw2 worlds eu - List all EU worlds with WvW tier
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 worlds")


@worlds.command(name="na")
@commands.cooldown(1, GW2CoolDowns.Worlds.seconds, commands.BucketType.user)
async def worlds_na(ctx):
    """List all North American worlds with WvW tier and population.

    Usage:
        gw2 worlds na
    """

    result, worlds_ids = await gw2_utils.get_worlds_ids(ctx)
    if not result:
        return None

    progress_msg = await gw2_utils.send_progress_embed(
        ctx, "Please wait, I'm fetching NA world data... (this may take a moment)"
    )

    na_worlds = [w for w in worlds_ids if w["id"] < 2001]
    embed_na, _ = await _fetch_worlds_matches(ctx, na_worlds, gw2_messages.NA_SERVERS_TITLE, "1-")

    await progress_msg.delete()
    await _send_paginated_worlds_embed(ctx, embed_na)
    return None


@worlds.command(name="eu")
@commands.cooldown(1, GW2CoolDowns.Worlds.seconds, commands.BucketType.user)
async def worlds_eu(ctx):
    """List all European worlds with WvW tier and population.

    Usage:
        gw2 worlds eu
    """

    result, worlds_ids = await gw2_utils.get_worlds_ids(ctx)
    if not result:
        return None

    progress_msg = await gw2_utils.send_progress_embed(
        ctx, "Please wait, I'm fetching EU world data... (this may take a moment)"
    )

    eu_worlds = [w for w in worlds_ids if w["id"] > 2001]
    embed_eu, _ = await _fetch_worlds_matches(ctx, eu_worlds, gw2_messages.EU_SERVERS_TITLE, "2-")

    await progress_msg.delete()
    await _send_paginated_worlds_embed(ctx, embed_eu)
    return None


async def _fetch_worlds_matches(ctx, worlds, title, region_prefix):
    """Fetch WvW match data for a list of worlds in parallel."""
    gw2_api = Gw2Client(ctx.bot)
    embed = discord.Embed(description=chat_formatting.inline(title))
    failed_worlds = []
    sem = asyncio.Semaphore(5)

    async def _fetch_match(world):
        async with sem:
            return await gw2_api.call_api(f"wvw/matches?world={world['id']}")

    tasks = [_fetch_match(w) for w in worlds]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for world, result in zip(worlds, results, strict=True):
        if isinstance(result, Exception):
            failed_worlds.append(f"{world['name']} (ID: {world['id']})")
            ctx.bot.log.warning(f"Failed to fetch WvW data for world {world['name']} (ID: {world['id']}): {result}")
            continue
        tier_number = result["id"].replace(region_prefix, "")
        embed.add_field(
            name=world["name"],
            value=chat_formatting.inline(f"T{tier_number} {world['population']}"),
        )

    if failed_worlds:
        embed.set_footer(
            text=f"\u26a0\ufe0f Failed to load: {', '.join(failed_worlds[:3])}"
            + ("..." if len(failed_worlds) > 3 else "")
        )

    return embed, failed_worlds


async def _send_paginated_worlds_embed(ctx, embed):
    """
    Send worlds with pagination using buttons for navigation
    """
    max_fields = 25
    color = ctx.bot.settings["gw2"]["EmbedColor"]

    if len(embed.fields) <= max_fields:
        # No pagination needed
        embed.color = color
        await ctx.send(embed=embed)
        return

    # Split fields into pages
    pages = []
    total_fields = len(embed.fields)

    for i in range(0, total_fields, max_fields):
        page_embed = discord.Embed(color=color, description=embed.description)
        page_fields = embed.fields[i : i + max_fields]

        for field in page_fields:
            page_embed.add_field(name=field.name, value=field.value)

        page_number = (i // max_fields) + 1
        total_pages = (total_fields + max_fields - 1) // max_fields
        page_embed.set_footer(text=f"Page {page_number}/{total_pages}")
        pages.append(page_embed)

    if len(pages) == 1:
        await ctx.send(embed=pages[0])
        return

    view = EmbedPaginatorView(pages, ctx.author.id)
    msg = await ctx.send(embed=pages[0], view=view)
    view.message = msg


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Worlds(bot))
