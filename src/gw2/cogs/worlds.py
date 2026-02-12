import asyncio
import discord
from discord.ext import commands
from src.bot.tools import bot_utils, chat_formatting
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


class GW2Worlds(GuildWars2):
    """(Guild Wars 2 List of Worlds Commands)"""

    def __init__(self, bot):
        super().__init__(bot)


@GW2Worlds.gw2.group()
async def worlds(ctx):
    """(List all worlds)
    gw2 worlds na
    gw2 worlds eu
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 worlds")


@worlds.command(name="na")
@commands.cooldown(1, GW2CoolDowns.Worlds.seconds, commands.BucketType.user)
async def worlds_na(ctx):
    """(List all NA worlds and wvw tier)
    gw2 worlds na
    """

    result, worlds_ids = await gw2_utils.get_worlds_ids(ctx)
    if not result:
        return None

    gw2_api = Gw2Client(ctx.bot)
    embed_na = discord.Embed(description=chat_formatting.inline(gw2_messages.NA_SERVERS_TITLE))

    failed_worlds = []

    for world in worlds_ids:
        wid = world["id"]
        try:
            await ctx.message.channel.typing()
            matches = await gw2_api.call_api(f"wvw/matches?world={wid}")
            if wid < 2001:
                tier_number = matches["id"].replace("1-", "")
                embed_na.add_field(
                    name=world["name"],
                    value=chat_formatting.inline(f"T{tier_number} {world['population']}"),
                )
        except Exception as e:
            # Log the error but continue with other worlds
            failed_worlds.append(f"{world['name']} (ID: {wid})")
            ctx.bot.log.warning(f"Failed to fetch WvW data for world {world['name']} (ID: {wid}): {e}")
            continue

    # Add footer if some worlds failed
    if failed_worlds:
        embed_na.set_footer(
            text=f"⚠️ Failed to load: {', '.join(failed_worlds[:3])}" + ("..." if len(failed_worlds) > 3 else "")
        )

    await _send_paginated_worlds_embed(ctx, embed_na)
    return None


@worlds.command(name="eu")
@commands.cooldown(1, GW2CoolDowns.Worlds.seconds, commands.BucketType.user)
async def worlds_eu(ctx):
    """(List all EU worlds and wvw tier)
    gw2 worlds eu
    """

    result, worlds_ids = await gw2_utils.get_worlds_ids(ctx)
    if not result:
        return None

    gw2_api = Gw2Client(ctx.bot)
    embed_eu = discord.Embed(description=chat_formatting.inline(gw2_messages.EU_SERVERS_TITLE))

    failed_worlds = []

    for world in worlds_ids:
        wid = world["id"]
        try:
            await ctx.message.channel.typing()
            matches = await gw2_api.call_api(f"wvw/matches?world={wid}")
            if wid > 2001:
                tier_number = matches["id"].replace("2-", "")
                embed_eu.add_field(
                    name=world["name"],
                    value=chat_formatting.inline(f"T{tier_number} {world['population']}"),
                )
        except Exception as e:
            # Log the error but continue with other worlds
            failed_worlds.append(f"{world['name']} (ID: {wid})")
            ctx.bot.log.warning(f"Failed to fetch WvW data for world {world['name']} (ID: {wid}): {e}")
            continue

    # Add footer if some worlds failed
    if failed_worlds:
        embed_eu.set_footer(
            text=f"⚠️ Failed to load: {', '.join(failed_worlds[:3])}" + ("..." if len(failed_worlds) > 3 else "")
        )

    await _send_paginated_worlds_embed(ctx, embed_eu)
    return None


async def _send_paginated_worlds_embed(ctx, embed):
    """
    Send worlds with pagination using reactions for navigation
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

        # Check if we're in a DM for the footer message
        if isinstance(ctx.channel, discord.DMChannel):
            footer_text = (
                f"Page {page_number}/{total_pages} • Use reactions to navigate (reactions won't disappear in DMs)"
            )
        else:
            footer_text = f"Page {page_number}/{total_pages}"

        page_embed.set_footer(text=footer_text)
        pages.append(page_embed)

    if len(pages) == 1:
        await ctx.send(embed=pages[0])
        return

    # Check if we're in a DM channel
    is_dm = isinstance(ctx.channel, discord.DMChannel)

    # Send first page with reactions
    current_page = 0
    message = await ctx.send(embed=pages[current_page])

    # Add reaction controls with small delays to ensure they're all added
    try:
        await message.add_reaction("⬅️")
        await asyncio.sleep(0.2)
        await message.add_reaction("➡️")
        await asyncio.sleep(0.2)
    except discord.HTTPException as e:
        ctx.bot.log.error(f"Failed to add pagination reactions: {e}")
        # Send without pagination if reactions fail
        await ctx.send(embed=pages[0])
        return

    def check(react, react_user):
        return (
            react_user == ctx.author
            and react.message.id == message.id
            and str(react.emoji) in ["⬅️", "➡️"]
            and not react_user.bot  # Ensure it's not a bot reaction
        )

    timeout = 60

    try:
        while True:
            reaction, user = await ctx.bot.wait_for("reaction_add", timeout=timeout, check=check)

            emoji_str = str(reaction.emoji)

            if emoji_str == "➡️" and current_page < len(pages) - 1:
                current_page += 1
                await message.edit(embed=pages[current_page])
            elif emoji_str == "⬅️" and current_page > 0:
                current_page -= 1
                await message.edit(embed=pages[current_page])

            # Remove user's reaction to keep the interface clean (skip in DM channels)
            if not is_dm:
                try:
                    await message.remove_reaction(reaction.emoji, user)
                except discord.Forbidden, discord.NotFound, discord.HTTPException:
                    pass  # Silently handle permission issues

    except TimeoutError:
        pass  # Silently handle timeout

    # Clean up by removing all reactions (skip in DM channels)
    if not is_dm:
        try:
            await message.clear_reactions()
        except discord.Forbidden:
            pass  # Silently handle permission issues


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Worlds(bot))
