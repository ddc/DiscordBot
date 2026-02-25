import asyncio
import discord
from discord.ext import commands
from src.bot.tools import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.constants.gw2_teams import get_team_name, is_wr_team_id
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


async def _keep_typing_alive(ctx, stop_event):
    """Helper to keep Discord typing indicator alive during long operations."""
    try:
        while not stop_event.is_set():
            try:
                await ctx.message.channel.typing()
                await asyncio.sleep(4)  # Renew every 4 seconds (Discord typing lasts ~5s)
            except asyncio.CancelledError:
                raise  # Re-raise CancelledError
            except discord.HTTPException, discord.Forbidden:
                # Handle Discord API errors gracefully and stop the loop
                break
    except asyncio.CancelledError:
        # Clean up and re-raise CancelledError as required
        raise


async def _fetch_guild_info_standalone(gw2_api, guild_id, api_key, ctx):
    """Helper to fetch individual guild information."""
    try:
        api_req_guild = await gw2_api.call_api(f"guild/{guild_id}", api_key)
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
        msg = gw2_messages.NO_API_KEY
        msg += gw2_messages.key_add_info_help(ctx.prefix)
        msg += gw2_messages.key_more_info_help(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)

    api_key = str(rs[0]["key"])
    permissions = str(rs[0]["permissions"])
    gw2_api = Gw2Client(ctx.bot)

    # Validate API key
    is_valid_key = await gw2_api.check_api_key(api_key)
    if not isinstance(is_valid_key, dict):
        msg = f"{is_valid_key.args[1]}\n"
        msg += gw2_messages.INVALID_API_KEY_HELP_MESSAGE
        msg += gw2_messages.key_add_info_help(ctx.prefix)
        msg += gw2_messages.key_more_info_help(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)

    if "account" not in permissions:
        return await bot_utils.send_error_msg(ctx, gw2_messages.API_KEY_NO_PERMISSION, True)

    # Initialize variables for cleanup
    stop_typing = None
    typing_task = None

    try:
        # Send progress message as embed
        color = ctx.bot.settings["gw2"]["EmbedColor"]
        progress_embed = discord.Embed(
            description="🔄 **Please wait, I'm fetching your account data from GW2 API...** (this may take a moment)",
            color=color,
        )
        progress_embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.display_avatar.url)
        progress_msg = await ctx.send(embed=progress_embed)

        # Start background typing keeper
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(_keep_typing_alive(ctx, stop_typing))

        # Fetch basic account info and server info in parallel
        account_task = gw2_api.call_api("account", api_key)

        # Wait for account info first since we need the server ID
        api_req_acc = await account_task
        server_id = api_req_acc["world"]

        # Prepare basic account data
        acc_name = api_req_acc["name"]
        access_normalized = []
        for each in api_req_acc["access"]:
            normalized = "".join([f" {c.upper()}" if c.isupper() or c.isdigit() else c for c in each]).lstrip()
            access_normalized.append(normalized)
        access = "\n".join(access_normalized)

        is_commander = "Yes" if api_req_acc["commander"] else "No"

        # Resolve server name and population (WR team IDs vs legacy worlds)
        if is_wr_team_id(server_id):
            server_name = get_team_name(server_id) or f"Team {server_id}"
            population = "N/A"
        else:
            api_req_server = await gw2_api.call_api(f"worlds/{server_id}", api_key)
            server_name = api_req_server["name"]
            population = api_req_server["population"]

        # Create base embed
        color = ctx.bot.settings["gw2"]["EmbedColor"]
        embed = discord.Embed(title="Account Name", description=chat_formatting.inline(acc_name), color=color)
        embed.set_thumbnail(url=ctx.message.author.display_avatar.url)
        embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.display_avatar.url)
        embed.add_field(name="Access", value=chat_formatting.inline(access), inline=False)
        embed.add_field(name="Commander Tag", value=chat_formatting.inline(is_commander))
        embed.add_field(name="Server", value=chat_formatting.inline(f"{server_name} ({population})"))

        # Add WvW Team field if available
        wvw_team_id = api_req_acc.get("wvw", {}).get("team_id")
        if wvw_team_id:
            team_name = get_team_name(wvw_team_id) or f"Team {wvw_team_id}"
            embed.add_field(name="WvW Team", value=chat_formatting.inline(team_name))

        # Prepare optional API calls based on permissions
        optional_tasks = []

        if "characters" in permissions:
            optional_tasks.append(("characters", gw2_api.call_api("characters", api_key)))

        if "progression" in permissions:
            optional_tasks.append(("achievements", gw2_api.call_api("account/achievements", api_key)))

        if "pvp" in permissions:
            optional_tasks.append(("pvp", gw2_api.call_api("pvp/stats", api_key)))

        # Execute optional API calls in parallel
        if optional_tasks:
            progress_embed.description = (
                "🔄 **Please wait, I'm fetching additional details...** (this may take a moment)"
            )
            await progress_msg.edit(embed=progress_embed)

            results = await asyncio.gather(*[task for _, task in optional_tasks], return_exceptions=True)

            # Process results
            for i, (task_name, _) in enumerate(optional_tasks):
                result = results[i]
                if isinstance(result, Exception):
                    ctx.bot.log.warning(f"Failed to fetch {task_name}: {result}")
                    continue

                if task_name == "characters":
                    embed.add_field(name="Characters", value=chat_formatting.inline(str(len(result))), inline=False)
                elif task_name == "achievements":
                    if "progression" in permissions:
                        fractallevel = api_req_acc["fractal_level"]
                        embed.add_field(name="Fractal Level", value=chat_formatting.inline(fractallevel), inline=False)

                        achiev_points = await gw2_utils.calculate_user_achiev_points(ctx, result, api_req_acc)
                        embed.add_field(
                            name="Achievements Points", value=chat_formatting.inline(str(achiev_points)), inline=False
                        )

                        wvwrank = api_req_acc.get("wvw", {}).get("rank") or api_req_acc.get("wvw_rank", 0)
                        wvw_title = gw2_utils.get_wvw_rank_title(int(wvwrank))
                        embed.add_field(
                            name="WvW Rank", value=chat_formatting.inline(f"{wvw_title} ({wvwrank})"), inline=False
                        )
                elif task_name == "pvp":
                    pvprank = result["pvp_rank"] + result["pvp_rank_rollovers"]
                    pvp_title = str(gw2_utils.get_pvp_rank_title(pvprank))
                    embed.add_field(
                        name="PVP Rank", value=chat_formatting.inline(f"{pvp_title} ({pvprank})"), inline=False
                    )

        # Handle guilds (most expensive operation)
        if "guilds" in api_req_acc and api_req_acc["guilds"]:
            guild_count = len(api_req_acc["guilds"])
            progress_embed.description = f"🔄 **Please wait, I'm fetching guild information...** ({guild_count} guilds)"
            await progress_msg.edit(embed=progress_embed)

            # Fetch guild info in parallel with limited concurrency to avoid rate limits
            guild_tasks = []
            for guild_id in api_req_acc["guilds"]:
                guild_tasks.append(_fetch_guild_info_standalone(gw2_api, guild_id, api_key, ctx))

            # Limit concurrent guild requests to avoid overwhelming the API
            sem = asyncio.Semaphore(3)  # Max 3 concurrent guild requests

            async def limited_guild_fetch(task):
                async with sem:
                    return await task

            guild_results = await asyncio.gather(
                *[limited_guild_fetch(task) for task in guild_tasks], return_exceptions=True
            )

            guilds_names = []
            guild_leader_names = []
            guild_leader_ids = set(api_req_acc.get("guild_leader", []))

            for result in guild_results:
                if isinstance(result, Exception):
                    continue
                guild_name, guild_id = result
                if guild_name:
                    guilds_names.append(guild_name)
                    if guild_id in guild_leader_ids:
                        guild_leader_names.append(guild_name)

            if guilds_names:
                embed.add_field(name="Guilds", value=chat_formatting.inline("\n".join(guilds_names)), inline=False)
            if guild_leader_names:
                embed.add_field(
                    name="Guild Leader",
                    value=chat_formatting.inline("\n".join(guild_leader_names)),
                    inline=False,
                )

        # Add account age
        days = (api_req_acc["age"] / 60) / 24
        created = api_req_acc["created"].split("T", 1)[0]
        embed.add_field(
            name="Created",
            value=chat_formatting.inline(f"{created} ({round(days)} days ago)"),
            inline=False,
        )

        embed.set_footer(
            icon_url=ctx.bot.user.display_avatar.url, text=f"{bot_utils.get_current_date_time_str_long()} UTC"
        )

        # Stop the background typing task
        stop_typing.set()
        typing_task.cancel()

        # Clean up progress message and send final result
        await progress_msg.delete()
        await bot_utils.send_embed(ctx, embed)

    except Exception as e:
        # Stop the background typing task if it exists
        if stop_typing is not None and typing_task is not None:
            try:
                stop_typing.set()
                typing_task.cancel()
            except AttributeError, RuntimeError:
                # Handle cases where task is already done or event is invalid
                pass
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Account(bot))
