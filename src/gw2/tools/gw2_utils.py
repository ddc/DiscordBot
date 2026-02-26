import asyncio
import discord
from datetime import datetime, timedelta
from discord.ext import commands
from enum import Enum
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils


class TimeObject:
    """Simple object to store time components."""

    def __init__(self):
        self.timedelta: timedelta = timedelta()
        self.days: int = 0
        self.hours: int = 0
        self.minutes: int = 0
        self.seconds: int = 0


from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.database.dal.gw2.gw2_session_chars_dal import Gw2SessionCharDeathsDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal
from src.gw2.constants import gw2_messages
from src.gw2.constants.gw2_currencies import ACHIEVEMENT_MAPPING, WALLET_MAPPING
from src.gw2.constants.gw2_settings import get_gw2_settings
from src.gw2.constants.gw2_teams import get_team_name, is_wr_team_id
from src.gw2.tools.gw2_client import Gw2Client

_gw2_settings = get_gw2_settings()
_background_tasks: set[asyncio.Task] = set()
_processing_sessions: dict[int, str | None] = {}
_achievement_cache: dict[int, dict] = {}


class Gw2Servers(Enum):
    Anvil_Rock = "Anvil Rock"
    Borlis_Pass = "Borlis Pass"
    Yaks_Bend = "Yak's Bend"
    Henge_of_Denravi = "Henge of Denravi"
    Maguuma = "Maguuma"
    Sorrows_Furnace = "Sorrow's Furnace"
    Gate_of_Madness = "Gate of Madness"
    Jade_Quarry = "Jade Quarry"
    Fort_Aspenwood = "Fort Aspenwood"
    Ehmry_Bay = "Ehmry Bay"
    Stormbluff_Isle = "Stormbluff Isle"
    Darkhaven = "Darkhaven"
    Sanctum_of_Rall = "Sanctum of Rall"
    Crystal_Desert = "Crystal Desert"
    Isle_of_Janthir = "Isle of Janthir"
    Sea_of_Sorrows = "Sea of Sorrows"
    Tarnished_Coast = "Tarnished Coast"
    Northern_Shiverpeaks = "Northern Shiverpeaks"
    Blackgate = "Blackgate"
    Fergusons_Crossing = "Ferguson's Crossing"
    Dragonbrand = "Dragonbrand"
    Kaineng = "Kaineng"
    Devonas_Rest = "Devona's Rest"
    Eredon_Terrace = "Eredon Terrace"
    Fissure_of_Woe = "Fissure of Woe"
    Desolation = "Desolation"
    Gandara = "Gandara"
    Blacktide = "Blacktide"
    Ring_of_Fire = "Ring of Fire"
    Underworld = "Underworld"
    Far_Shiverpeaks = "Far Shiverpeaks"
    Whiteside_Ridge = "Whiteside Ridge"
    Ruins_of_Surmia = "Ruins of Surmia"
    Seafarers_Rest = "Seafarer's Rest"
    Vabbi = "Vabbi"
    Piken_Square = "Piken Square"
    Aurora_Glade = "Aurora Glade"
    Gunnars_Hold = "Gunnar's Hold"
    Jade_Sea = "Jade Sea [FR]"
    Fort_Ranik = "Fort Ranik [FR]"
    Augury_Rock = "Augury Rock [FR]"
    Vizunah_Square = "Vizunah Square [FR]"
    Arborstone = "Arborstone [FR]"
    Kodash = "Kodash [DE]"
    Riverside = "Riverside [DE]"
    Elona_Reach = "Elona Reach [DE]"
    Abaddons_Mouth = "Abaddon's Mouth [DE]"
    Drakkar_Lake = "Drakkar Lake [DE]"
    Millers_Sound = "Miller's Sound [DE]"


async def send_progress_embed(
    ctx: commands.Context, message: str = "Please wait, I'm fetching data from GW2 API... (this may take a moment)"
) -> discord.Message:
    """Send a progress embed that can be deleted when the operation completes."""
    color = ctx.bot.settings["gw2"]["EmbedColor"]
    embed = discord.Embed(description=f"\U0001f504 **{message}**", color=color)
    embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.display_avatar.url)
    return await ctx.send(embed=embed)


async def send_msg(ctx: commands.Context, description: str, dm: bool = False) -> None:
    """Send a GW2-themed embed message."""
    color = ctx.bot.settings["gw2"]["EmbedColor"]
    embed = discord.Embed(color=color, description=description)
    await bot_utils.send_embed(ctx, embed, dm)


async def insert_gw2_server_configs(bot: Bot, server: discord.Guild) -> None:
    """Insert GW2 server configs if they don't exist."""
    gw2_configs_dal = Gw2ConfigsDal(bot.db_session, bot.log)
    server_config = await gw2_configs_dal.get_gw2_server_configs(server.id)
    if not server_config:
        await gw2_configs_dal.insert_gw2_server_configs(server.id)


async def calculate_user_achiev_points(ctx: commands.Context, api_req_acc_achiev: list[dict], api_req_acc: dict) -> int:
    """Calculate total achievement points for a user."""
    gw2_api = Gw2Client(ctx.bot)
    total = api_req_acc["daily_ap"] + api_req_acc["monthly_ap"]

    # Fetch achievement data in batches
    achievement_data = await _fetch_achievement_data_in_batches(gw2_api, api_req_acc_achiev)

    # Calculate earned points
    total += _calculate_earned_points(api_req_acc_achiev, achievement_data)

    return total


async def _fetch_achievement_data_in_batches(gw2_api: Gw2Client, user_achievements: list[dict]) -> list[dict]:
    """Fetch achievement data from API in parallel batches of 200, with in-memory cache.

    Achievement definitions (tiers, points) are static game data that rarely change,
    so caching them avoids 18+ API calls on every `gw2 account` invocation.
    """
    needed_ids = [ach["id"] for ach in user_achievements if ach["id"] not in _achievement_cache]

    if needed_ids:
        batch_size = 200
        sem = asyncio.Semaphore(5)

        async def _fetch_batch(batch_ids):
            async with sem:
                ids_string = ",".join(str(aid) for aid in batch_ids)
                return await gw2_api.call_api(f"achievements?ids={ids_string}")

        batch_tasks = []
        for i in range(0, len(needed_ids), batch_size):
            batch = needed_ids[i : i + batch_size]
            batch_tasks.append(_fetch_batch(batch))

        results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                continue
            for ach in result:
                _achievement_cache[ach["id"]] = ach

    return [_achievement_cache[ach["id"]] for ach in user_achievements if ach["id"] in _achievement_cache]


def _calculate_earned_points(user_achievements: list[dict], achievement_data: list[dict]) -> int:
    """Calculate total earned achievement points."""
    total_earned = 0
    achievement_lookup = {doc["id"]: doc for doc in achievement_data}

    for user_ach in user_achievements:
        achievement_doc = achievement_lookup.get(user_ach["id"])
        if achievement_doc:
            total_earned += earned_ap(achievement_doc, user_ach)

    return total_earned


def earned_ap(achievement: dict, user_progress: dict) -> int:
    """Calculate earned achievement points for a specific achievement."""
    if not achievement:
        return 0

    earned = 0
    repeats = user_progress.get("repeated", 0)
    max_possible = max_ap(achievement, repeats)

    # Calculate points from completed tiers
    if "tiers" in achievement:
        for tier in achievement["tiers"]:
            if user_progress.get("current", 0) >= tier["count"]:
                earned += tier["points"]

    # Add points from repeated completions
    earned += max_ap(achievement) * repeats

    # Cap at maximum possible points
    return min(earned, max_possible)


def max_ap(achievement: dict | None, repeatable: bool = False) -> int:
    """Calculate maximum achievement points for an achievement."""
    if not achievement:
        return 0

    if repeatable:
        return achievement.get("point_cap", 0)

    tiers = achievement.get("tiers", [])
    return sum(tier.get("points", 0) for tier in tiers)


async def get_world_id(bot: Bot, world: str | None) -> int | None:
    """Get world ID by world name."""
    if not world:
        return None

    try:
        gw2_api = Gw2Client(bot)
        results = await gw2_api.call_api("worlds?ids=all")

        # Create a dictionary for O(1) lookup instead of O(n) linear search
        # Also support partial matches as a fallback
        world_lower = world.lower()
        world_map = {w["name"].lower(): w["id"] for w in results}

        # Try exact match first (O(1))
        if world_lower in world_map:
            return world_map[world_lower]

        # If no exact match, try partial match (case-insensitive)
        # This allows users to type "jade" instead of "Jade Quarry" for example
        for world_name, world_id in world_map.items():
            if world_lower in world_name:
                return world_id

    except Exception as e:
        bot.log.error(f"Error fetching world ID for {world}: {e}")

    return None


async def get_world_name_population(ctx: commands.Context, world_ids: str) -> list[str] | None:
    """Get world names and population data.

    Handles both legacy world IDs (1xxx/2xxx) via /v2/worlds API and
    World Restructuring team IDs (11xxx/12xxx) via hardcoded lookup.
    """
    try:
        id_list = [int(wid.strip()) for wid in world_ids.split(",") if wid.strip()]
        if not id_list:
            return None

        legacy_ids = [wid for wid in id_list if not is_wr_team_id(wid)]

        # Build name lookup from API for legacy IDs
        legacy_names: dict[int, str] = {}
        if legacy_ids:
            gw2_api = Gw2Client(ctx.bot)
            legacy_ids_str = ",".join(str(wid) for wid in legacy_ids)
            results = await gw2_api.call_api(f"worlds?ids={legacy_ids_str}")
            if results:
                for world in results:
                    legacy_names[world["id"]] = world["name"]

        # Resolve all IDs in original order
        names: list[str] = []
        for wid in id_list:
            if is_wr_team_id(wid):
                name = get_team_name(wid)
                names.append(name if name else f"Team {wid}")
            elif wid in legacy_names:
                names.append(legacy_names[wid])

        return names if names else None

    except Exception as e:
        ctx.bot.log.error(f"Error fetching world names for IDs {world_ids}: {e}")
        return None


async def get_world_name(bot: Bot, world_ids: str) -> str | None:
    """Get world name by world ID."""
    try:
        gw2_api = Gw2Client(bot)
        result = await gw2_api.call_api(f"worlds?ids={world_ids}")
        return result.get("name") if result else None

    except Exception as e:
        bot.log.error(f"Error fetching world name for ID {world_ids}: {e}")
        return None


async def delete_api_key(ctx: commands.Context, message: bool = False) -> None:
    """Delete message containing API key for privacy."""
    if not isinstance(ctx.channel, discord.DMChannel):
        try:
            await ctx.message.delete()
            if message:
                await send_msg(ctx, gw2_messages.API_KEY_MESSAGE_REMOVED)
        except discord.HTTPException:
            await bot_utils.send_error_msg(ctx, gw2_messages.API_KEY_MESSAGE_REMOVED_DENIED)


def is_private_message(ctx: commands.Context) -> bool:
    """Check if the context is a private message."""
    return isinstance(ctx.channel, discord.DMChannel)


async def check_gw2_game_activity(bot: Bot, before: discord.Member, after: discord.Member) -> None:
    """Check for GW2 game activity changes and manage sessions accordingly."""
    before_activity = _get_non_custom_activity(before.activities)
    after_activity = _get_non_custom_activity(after.activities)

    if not _is_gw2_activity_detected(before_activity, after_activity):
        return

    before_is_gw2 = (
        before_activity is not None and gw2_messages.GW2_FULL_NAME.lower() in str(before_activity.name).lower()
    )
    after_is_gw2 = after_activity is not None and gw2_messages.GW2_FULL_NAME.lower() in str(after_activity.name).lower()

    bot.log.debug(
        f"GW2 activity detected for {after.id}: "
        f"before={before_activity.name if before_activity else None}, "
        f"after={after_activity.name if after_activity else None}"
    )

    if before_is_gw2 and after_is_gw2:
        bot.log.debug(f"User {after.id} still playing GW2, no session change needed")
        return

    action = "start" if after_is_gw2 else "end"
    await _handle_gw2_activity_change(bot, after, action)


def _get_non_custom_activity(activities) -> discord.Activity | None:
    """Get the first non-custom activity from a list of activities."""
    for activity in activities:
        if activity.type is not discord.ActivityType.custom:
            return activity
    return None


def _is_gw2_activity_detected(before_activity, after_activity) -> bool:
    """Check if Guild Wars 2 activity is detected in before or after states."""
    return (after_activity is not None and gw2_messages.GW2_FULL_NAME.lower() in str(after_activity.name).lower()) or (
        before_activity is not None and gw2_messages.GW2_FULL_NAME.lower() in str(before_activity.name).lower()
    )


async def _handle_gw2_activity_change(
    bot: Bot,
    member: discord.Member,
    action: str,
) -> None:
    """Handle GW2 activity changes and manage session tracking.

    Uses a per-user pending-action queue so that end events arriving while
    a start is in progress are never silently dropped.
    """
    if member.id in _processing_sessions:
        _processing_sessions[member.id] = action
        bot.log.debug(f"Session operation in progress for user {member.id}, queuing '{action}' as pending")
        return

    _processing_sessions[member.id] = None
    try:
        while action is not None:
            await _execute_session_action(bot, member, action)
            # Check if a new action was queued while we were processing
            action = _processing_sessions[member.id]
            _processing_sessions[member.id] = None
            if action is not None:
                bot.log.debug(f"Processing pending '{action}' action for user {member.id}")
    finally:
        _processing_sessions.pop(member.id, None)


async def _execute_session_action(bot: Bot, member: discord.Member, action: str) -> None:
    """Execute a single session action (start or end)."""
    gw2_configs = Gw2ConfigsDal(bot.db_session, bot.log)
    server_configs = await gw2_configs.get_gw2_server_configs(member.guild.id)

    if not server_configs or not server_configs[0]["session"]:
        bot.log.debug(f"Session tracking not enabled for guild {member.guild.id}, skipping")
        return

    gw2_key_dal = Gw2KeyDal(bot.db_session, bot.log)
    api_key_result = await gw2_key_dal.get_api_key_by_user(member.id)

    if not api_key_result:
        bot.log.debug(f"No GW2 API key found for user {member.id}, skipping session")
        return

    api_key = api_key_result[0]["key"]

    if action == "start":
        bot.log.debug(f"Starting GW2 session for user {member.id}")
        await start_session(bot, member, api_key)
    else:
        bot.log.debug(f"Ending GW2 session for user {member.id}")
        await end_session(bot, member, api_key)


async def start_session(bot: Bot, member: discord.Member, api_key: str) -> None:
    """Start a new GW2 session for a member."""
    session = await get_user_stats(bot, api_key)
    if not session:
        bot.log.warning(f"Failed to start session for user {member.id}: unable to fetch stats from GW2 API")
        task = asyncio.create_task(_retry_session_later(bot, member, api_key, "start"))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        return

    await _do_start_session(bot, member, api_key, session)


async def _do_start_session(bot: Bot, member: discord.Member, api_key: str, session: dict) -> None:
    """Execute start session DB operations."""
    session["user_id"] = member.id
    session["date"] = bot_utils.convert_datetime_to_str_short(bot_utils.get_current_date_time())

    bot.log.debug(f"Attempting to insert start session into DB for user {member.id}")
    try:
        gw2_session_dal = Gw2SessionsDal(bot.db_session, bot.log)
        session_id = await gw2_session_dal.insert_start_session(session)
        bot.log.debug(f"Successfully inserted start session {session_id} for user {member.id}")
    except Exception as e:
        bot.log.error(f"Failed to insert start session into DB for user {member.id}: {e}")
        return
    await insert_start_char_deaths(bot, member, api_key, session_id)


async def end_session(bot: Bot, member: discord.Member, api_key: str) -> None:
    """End a GW2 session for a member."""
    session = await get_user_stats(bot, api_key)
    if not session:
        bot.log.warning(f"Failed to end session for user {member.id}: unable to fetch stats from GW2 API")
        task = asyncio.create_task(_retry_session_later(bot, member, api_key, "end"))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        return

    await _do_end_session(bot, member, api_key, session)


async def _do_end_session(bot: Bot, member: discord.Member, api_key: str, session: dict) -> None:
    """Execute end session DB operations."""
    session["user_id"] = member.id
    session["date"] = bot_utils.convert_datetime_to_str_short(bot_utils.get_current_date_time())

    bot.log.debug(f"Attempting to update end session in DB for user {member.id}")
    try:
        gw2_session_dal = Gw2SessionsDal(bot.db_session, bot.log)
        session_id = await gw2_session_dal.update_end_session(session)
    except Exception as e:
        bot.log.error(f"Failed to update end session in DB for user {member.id}: {e}")
        return
    if session_id is None:
        bot.log.warning(f"No active session found for user {member.id}, skipping end session chars")
        return
    bot.log.debug(f"Successfully updated end session {session_id} for user {member.id}")
    await update_end_char_deaths(bot, member, api_key, session_id)


async def _retry_session_later(bot: Bot, member: discord.Member, api_key: str, session_type: str) -> None:
    """Background task: wait and retry session, DM user on final failure."""
    bg_delay = _gw2_settings.api_session_retry_bg_delay
    max_attempts = _gw2_settings.api_retry_max_attempts

    bot.log.warning(
        f"Scheduling background retry for {session_type} session "
        f"for user {member.id} ({max_attempts} attempts, {bg_delay}s delay)"
    )

    for attempt in range(1, max_attempts + 1):
        await asyncio.sleep(bg_delay)

        session = await get_user_stats(bot, api_key)
        if session:
            bot.log.info(
                f"Background retry succeeded for {session_type} session "
                f"for user {member.id} on attempt {attempt}/{max_attempts}"
            )
            if session_type == "start":
                await _do_start_session(bot, member, api_key, session)
            else:
                await _do_end_session(bot, member, api_key, session)
            return

        bot.log.warning(
            f"Background retry {attempt}/{max_attempts} failed for {session_type} session for user {member.id}"
        )

    bot.log.error(f"All background retries exhausted for {session_type} session for user {member.id}")
    try:
        await member.send(gw2_messages.SESSION_API_DOWN_DM)
    except discord.HTTPException:
        bot.log.warning(f"Could not DM user {member.id} about GW2 API failure")


async def get_user_stats(bot: Bot, api_key: str) -> dict | None:
    """Get comprehensive user statistics from GW2 API."""
    gw2_api = Gw2Client(bot)

    try:
        achievement_ids = ",".join(str(k) for k in ACHIEVEMENT_MAPPING)
        account_data, wallet_data, achievements_data = await asyncio.gather(
            gw2_api.call_api("account", api_key),
            gw2_api.call_api("account/wallet", api_key),
            gw2_api.call_api(f"account/achievements?ids={achievement_ids}", api_key),
        )

    except Exception as e:
        bot.log.error(f"Error fetching user stats: {e}")
        return None

    user_stats = _create_initial_user_stats(account_data)
    _update_wallet_stats(user_stats, wallet_data)
    _update_achievement_stats(user_stats, achievements_data)

    return user_stats


def _create_initial_user_stats(account_data: dict) -> dict:
    """Create initial user stats structure."""
    wvw_rank = account_data.get("wvw", {}).get("rank") or account_data.get("wvw_rank", 0)
    stats = {
        "acc_name": account_data["name"],
        "wvw_rank": wvw_rank,
        "players": 0,
        "yaks_scorted": 0,
        "yaks": 0,
        "camps": 0,
        "castles": 0,
        "towers": 0,
        "keeps": 0,
    }
    for key in WALLET_MAPPING.values():
        stats[key] = 0
    return stats


def _update_wallet_stats(user_stats: dict, wallet_data: list[dict]) -> None:
    """Update user stats with wallet information."""
    for wallet_item in wallet_data:
        wallet_id = wallet_item["id"]
        if wallet_id in WALLET_MAPPING:
            stat_name = WALLET_MAPPING[wallet_id]
            user_stats[stat_name] = wallet_item["value"]


def _update_achievement_stats(user_stats: dict, achievements_data: list[dict]) -> None:
    """Update user stats with achievement information."""
    for achievement in achievements_data:
        achievement_id = achievement["id"]
        if achievement_id in ACHIEVEMENT_MAPPING:
            stat_name = ACHIEVEMENT_MAPPING[achievement_id]
            user_stats[stat_name] = achievement.get("current", 0)


async def insert_start_char_deaths(bot: Bot, member: discord.Member, api_key: str, session_id) -> None:
    """Insert start session character death data."""
    bot.log.debug(f"Attempting to insert start char deaths for session {session_id}, user {member.id}")
    try:
        gw2_api = Gw2Client(bot)
        characters_data = await gw2_api.call_api("characters?ids=all", api_key)

        gw2_session_chars_dal = Gw2SessionCharDeathsDal(bot.db_session, bot.log)
        await gw2_session_chars_dal.insert_start_char_deaths(session_id, member.id, characters_data)
        bot.log.debug(f"Successfully inserted start char deaths for session {session_id}, user {member.id}")

    except Exception as e:
        bot.log.error(f"Error inserting start session character data for session {session_id}, user {member.id}: {e}")


async def update_end_char_deaths(bot: Bot, member: discord.Member, api_key: str, session_id) -> None:
    """Update end session character death data."""
    bot.log.debug(f"Attempting to update end char deaths for session {session_id}, user {member.id}")
    try:
        gw2_api = Gw2Client(bot)
        characters_data = await gw2_api.call_api("characters?ids=all", api_key)

        gw2_session_chars_dal = Gw2SessionCharDeathsDal(bot.db_session, bot.log)
        await gw2_session_chars_dal.update_end_char_deaths(session_id, member.id, characters_data)
        bot.log.debug(f"Successfully updated end char deaths for session {session_id}, user {member.id}")

    except Exception as e:
        bot.log.error(f"Error updating end session character data for session {session_id}, user {member.id}: {e}")


def get_wvw_rank_title(rank: int) -> str:
    """Get WvW rank title based on rank number."""
    prefix = _get_wvw_rank_prefix(rank)
    title = _get_wvw_rank_title(rank)
    return f"{prefix} {title}".strip()


def _get_wvw_rank_prefix(rank: int) -> str:
    """Get WvW rank prefix (Bronze, Silver, etc.)."""
    match rank:
        case r if 150 <= r <= 619:
            return "Bronze"
        case r if 620 <= r <= 1394:
            return "Silver"
        case r if 1395 <= r <= 2544:
            return "Gold"
        case r if 2545 <= r <= 4094:
            return "Platinum"
        case r if 4095 <= r <= 6444:
            return "Mithril"
        case r if r >= 6445:
            return "Diamond"
        case _:
            return ""


def _get_wvw_rank_title(rank: int) -> str:
    """Get WvW rank title (Invader, Assaulter, etc.)."""
    # Define rank ranges for each title across all tiers
    title_ranges = {
        "Invader": [(1, 4), (150, 179), (620, 669), (1395, 1469), (2545, 2644), (4095, 4244), (6445, 6694)],
        "Assaulter": [(5, 9), (180, 209), (670, 719), (1470, 1544), (2645, 2744), (4245, 4394), (6695, 6944)],
        "Raider": [(10, 14), (210, 239), (720, 769), (1545, 1619), (2745, 2844), (4395, 4544), (6945, 7194)],
        "Recruit": [(15, 19), (240, 269), (770, 819), (1620, 1694), (2845, 2944), (4545, 4694), (7195, 7444)],
        "Scout": [(20, 29), (270, 299), (820, 869), (1695, 1769), (2945, 3044), (4695, 4844), (7445, 7694)],
        "Soldier": [(30, 39), (300, 329), (870, 919), (1770, 1844), (3045, 3144), (4845, 4994), (7695, 7944)],
        "Squire": [(40, 49), (330, 359), (920, 969), (1845, 1919), (3145, 3244), (4995, 5144), (7945, 8194)],
        "Footman": [(50, 59), (360, 389), (970, 1019), (1920, 1994), (3245, 3344), (5145, 5294), (8195, 8444)],
        "Knight": [(60, 69), (390, 419), (1020, 1069), (1995, 2069), (3345, 3444), (5295, 5444), (8445, 8694)],
        "Major": [(70, 79), (420, 449), (1070, 1119), (2070, 2144), (3445, 3544), (5445, 5594), (8695, 8944)],
        "Colonel": [(80, 89), (450, 479), (1120, 1169), (2145, 2219), (3545, 3644), (5595, 5744), (8945, 9194)],
        "General": [(90, 99), (480, 509), (1170, 1219), (2220, 2294), (3645, 3744), (5745, 5894), (9195, 9444)],
        "Veteran": [(100, 109), (510, 539), (1220, 1269), (2295, 2369), (3745, 3844), (5895, 6044), (9445, 9694)],
        "Champion": [(110, 119), (540, 569), (1270, 1319), (2370, 2444), (3845, 3944), (6045, 6194), (9695, 9944)],
    }

    # Check each title's ranges
    for title, ranges in title_ranges.items():
        for start, end in ranges:
            if start <= rank <= end:
                return title

    # Legend rank (highest tier)
    legend_thresholds = [120, 570, 1320, 2445, 3945, 6195, 9945]
    for threshold in legend_thresholds:
        if rank >= threshold:
            return "Legend"

    return ""


def get_pvp_rank_title(rank: int) -> str:
    """Get PvP rank title based on rank number."""
    match rank:
        case r if 1 <= r <= 9:
            return "Rabbit"
        case r if 10 <= r <= 19:
            return "Deer"
        case r if 20 <= r <= 29:
            return "Dolyak"
        case r if 30 <= r <= 39:
            return "Wolf"
        case r if 40 <= r <= 49:
            return "Tiger"
        case r if 50 <= r <= 59:
            return "Bear"
        case r if 60 <= r <= 69:
            return "Shark"
        case r if 70 <= r <= 79:
            return "Phoenix"
        case r if r >= 80:
            return "Dragon"
        case _:
            return ""


def format_gold(currency: str) -> str:
    """Format currency string into readable gold format.

    Args:
        currency: Currency string (e.g., "1234567")

    Returns:
        Formatted string like "123 Gold 45 Silver 67 Copper"
    """
    if not currency or len(currency) < 2:
        return ""

    formatted_parts = []

    # Extract copper (last 2 digits)
    copper = currency[-2:] if len(currency) >= 2 else currency

    # Extract silver (2 digits before copper)
    silver = currency[-4:-2] if len(currency) >= 4 else ""

    # Extract gold (everything before silver)
    gold = currency[:-4] if len(currency) > 4 else ""

    # Add gold if present and not empty/dash
    if gold and gold != "-":
        formatted_parts.append(f"{gold} Gold")

    # Add silver if present and not empty
    if silver:
        formatted_parts.append(f"{silver} Silver")

    # Add copper if not zero and not empty
    if copper and copper != "00":
        formatted_parts.append(f"{copper} Copper")

    return " ".join(formatted_parts)


def get_time_passed(start_time: datetime, end_time: datetime) -> TimeObject:
    """Calculate time passed between two datetime objects."""
    time_passed_delta = end_time - start_time
    return convert_timedelta_to_obj(time_passed_delta)


def format_seconds_to_time(total_seconds: int) -> str:
    """Format seconds into a human-readable time string (e.g. '2h 30m 15s')."""
    if total_seconds <= 0:
        return "0s"

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def convert_timedelta_to_obj(time_delta: timedelta) -> TimeObject:
    """Convert timedelta to a structured object with individual time components."""
    obj = TimeObject()
    obj.timedelta = time_delta

    time_str = str(time_delta)

    if "," in time_str:
        # Format: "X days, H:M:S"
        parts = time_str.split(", ")
        obj.days = int(parts[0].split()[0])
        time_part = parts[1]
    else:
        # Format: "H:M:S"
        obj.days = 0
        time_part = time_str

    # Parse H:M:S part
    time_components = time_part.split(":")
    obj.hours = int(time_components[0])
    obj.minutes = int(time_components[1])
    obj.seconds = int(float(time_components[2]))  # Handle potential microseconds

    return obj


async def get_worlds_ids(ctx: commands.Context) -> tuple[bool, list[dict] | None]:
    """Get all world IDs from the GW2 API.

    Returns:
        Tuple of (success: bool, results: Optional[List[Dict]])
    """
    try:
        await ctx.message.channel.typing()
        gw2_api = Gw2Client(ctx.bot)
        results = await gw2_api.call_api("worlds?ids=all")
        return True, results
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e)
        ctx.bot.log.error(f"Error fetching world IDs: {e}")
        return False, None
