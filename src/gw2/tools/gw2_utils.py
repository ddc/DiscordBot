"""GW2 utilities module with improved structure and error handling."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import discord
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
from src.database.dal.gw2.gw2_session_chars_dal import Gw2SessionCharsDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.constants import gw2_messages

if TYPE_CHECKING:
    from discord.ext import commands


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


async def send_msg(ctx: "commands.Context", description: str, dm: bool = False) -> None:
    """Send a GW2-themed embed message."""
    color = ctx.bot.settings["gw2"]["EmbedColor"]
    embed = discord.Embed(color=color, description=description)
    await bot_utils.send_embed(ctx, embed, dm)


async def insert_gw2_server_configs(bot: "commands.Bot", server: discord.Guild) -> None:
    """Insert GW2 server configs if they don't exist."""
    gw2_configs_dal = Gw2ConfigsDal(bot.db_session, bot.log)
    server_config = await gw2_configs_dal.get_gw2_server_configs(server.id)
    if not server_config:
        await gw2_configs_dal.insert_gw2_server_configs(server.id)


async def calculate_user_achiev_points(
    ctx: "commands.Context", api_req_acc_achiev: List[Dict], api_req_acc: Dict
) -> int:
    """Calculate total achievement points for a user."""
    gw2_api = Gw2Client(ctx.bot)
    total = api_req_acc["daily_ap"] + api_req_acc["monthly_ap"]

    # Fetch achievement data in batches
    achievement_data = await _fetch_achievement_data_in_batches(gw2_api, api_req_acc_achiev)

    # Calculate earned points
    total += _calculate_earned_points(api_req_acc_achiev, achievement_data)

    return total


async def _fetch_achievement_data_in_batches(gw2_api: Gw2Client, user_achievements: List[Dict]) -> List[Dict]:
    """Fetch achievement data from API in batches of 200."""
    batch_size = 200
    all_achievement_data = []

    for i in range(0, len(user_achievements), batch_size):
        batch = user_achievements[i : i + batch_size]
        achievement_ids = [str(ach["id"]) for ach in batch]
        ids_string = ",".join(achievement_ids)

        api_response = await gw2_api.call_api(f"achievements?ids={ids_string}")
        all_achievement_data.extend(api_response)

    return all_achievement_data


def _calculate_earned_points(user_achievements: List[Dict], achievement_data: List[Dict]) -> int:
    """Calculate total earned achievement points."""
    total_earned = 0
    achievement_lookup = {doc["id"]: doc for doc in achievement_data}

    for user_ach in user_achievements:
        achievement_doc = achievement_lookup.get(user_ach["id"])
        if achievement_doc:
            total_earned += earned_ap(achievement_doc, user_ach)

    return total_earned


def earned_ap(achievement: Dict, user_progress: Dict) -> int:
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


def max_ap(achievement: Optional[Dict], repeatable: bool = False) -> int:
    """Calculate maximum achievement points for an achievement."""
    if not achievement:
        return 0

    if repeatable:
        return achievement.get("point_cap", 0)

    tiers = achievement.get("tiers", [])
    return sum(tier.get("points", 0) for tier in tiers)


async def get_world_id(bot: "commands.Bot", world: Optional[str]) -> Optional[int]:
    """Get world ID by world name."""
    if not world:
        return None

    try:
        gw2_api = Gw2Client(bot)
        results = await gw2_api.call_api("worlds?ids=all")

        for world_data in results:
            if world_data["name"].lower() == world.lower():
                return world_data["id"]

    except Exception as e:
        bot.log.error(f"Error fetching world ID for {world}: {e}")

    return None


async def get_world_name_population(ctx: "commands.Context", world_ids: str) -> Optional[List[str]]:
    """Get world names and population data."""
    try:
        gw2_api = Gw2Client(ctx.bot)
        results = await gw2_api.call_api(f"worlds?ids={world_ids}")

        if not results:
            return None

        return [world["name"] for world in results]

    except Exception as e:
        ctx.bot.log.error(f"Error fetching world names for IDs {world_ids}: {e}")
        return None


async def get_world_name(bot: "commands.Bot", world_ids: str) -> Optional[str]:
    """Get world name by world ID."""
    try:
        gw2_api = Gw2Client(bot)
        result = await gw2_api.call_api(f"worlds?ids={world_ids}")
        return result.get("name") if result else None

    except Exception as e:
        bot.log.error(f"Error fetching world name for ID {world_ids}: {e}")
        return None


async def delete_api_key(ctx: "commands.Context", message: bool = False) -> None:
    """Delete message containing API key for privacy."""
    if not isinstance(ctx.channel, discord.DMChannel):
        try:
            await ctx.message.delete()
            if message:
                await send_msg(ctx, gw2_messages.API_KEY_MESSAGE_REMOVED)
        except discord.HTTPException:
            await bot_utils.send_error_msg(ctx, gw2_messages.API_KEY_MESSAGE_REMOVED_DENIED)


def is_private_message(ctx: "commands.Context") -> bool:
    """Check if the context is a private message."""
    return isinstance(ctx.channel, discord.DMChannel)


async def check_gw2_game_activity(bot: "commands.Bot", before: discord.Member, after: discord.Member) -> None:
    """Check for GW2 game activity changes and manage sessions accordingly."""
    before_activity = _get_non_custom_activity(before.activities)
    after_activity = _get_non_custom_activity(after.activities)

    if _is_gw2_activity_detected(before_activity, after_activity):
        await _handle_gw2_activity_change(bot, after, before_activity, after_activity)


def _get_non_custom_activity(activities) -> Optional[discord.Activity]:
    """Get the first non-custom activity from a list of activities."""
    for activity in activities:
        if activity.type is not discord.ActivityType.custom:
            return activity
    return None


def _is_gw2_activity_detected(before_activity, after_activity) -> bool:
    """Check if Guild Wars 2 activity is detected in before or after states."""
    return (after_activity is not None and "guild wars 2" in str(after_activity.name).lower()) or (
        before_activity is not None and "guild wars 2" in str(before_activity.name).lower()
    )


async def _handle_gw2_activity_change(
    bot: "commands.Bot",
    member: discord.Member,
    before_activity,
    after_activity,
) -> None:
    """Handle GW2 activity changes and manage session tracking."""
    gw2_configs = Gw2ConfigsDal(bot.db_session, bot.log)
    server_configs = await gw2_configs.get_gw2_server_configs(member.guild.id)

    if not server_configs or not server_configs[0]["session"]:
        return

    gw2_key_dal = Gw2KeyDal(bot.db_session, bot.log)
    api_key_result = await gw2_key_dal.get_api_key_by_user(member.id)

    if not api_key_result:
        return

    api_key = api_key_result[0]["key"]

    if after_activity is not None:
        await start_session(bot, member, api_key)
    else:
        await end_session(bot, member, api_key)


async def start_session(bot: "commands.Bot", member: discord.Member, api_key: str) -> None:
    """Start a new GW2 session for a member."""
    session = await get_user_stats(bot, api_key)
    if not session:
        return

    session["user_id"] = member.id
    session["date"] = bot_utils.convert_datetime_to_str_short(bot_utils.get_current_date_time())

    gw2_session_dal = Gw2SessionsDal(bot.db_session, bot.log)
    session_id = await gw2_session_dal.insert_start_session(session)
    await insert_session_char(bot, member, api_key, session_id, "start")


async def end_session(bot: "commands.Bot", member: discord.Member, api_key: str) -> None:
    """End a GW2 session for a member."""
    session = await get_user_stats(bot, api_key)
    if not session:
        return

    session["user_id"] = member.id
    session["date"] = bot_utils.convert_datetime_to_str_short(bot_utils.get_current_date_time())

    gw2_session_dal = Gw2SessionsDal(bot.db_session, bot.log)
    session_id = await gw2_session_dal.update_end_session(session)
    await insert_session_char(bot, member, api_key, session_id, "end")


async def get_user_stats(bot: "commands.Bot", api_key: str) -> Optional[Dict]:
    """Get comprehensive user statistics from GW2 API."""
    gw2_api = Gw2Client(bot)

    try:
        # Fetch data from multiple endpoints
        account_data = await gw2_api.call_api("account", api_key)
        wallet_data = await gw2_api.call_api("account/wallet", api_key)
        achievements_data = await gw2_api.call_api("account/achievements", api_key)

    except Exception as e:
        bot.log.error(f"Error fetching user stats: {e}")
        return None

    user_stats = _create_initial_user_stats(account_data)
    _update_wallet_stats(user_stats, wallet_data)
    _update_achievement_stats(user_stats, achievements_data)

    return user_stats


def _create_initial_user_stats(account_data: Dict) -> Dict:
    """Create initial user stats structure."""
    return {
        "acc_name": account_data["name"],
        "wvw_rank": account_data["wvw_rank"],
        "gold": 0,
        "karma": 0,
        "laurels": 0,
        "badges_honor": 0,
        "guild_commendations": 0,
        "wvw_tickets": 0,
        "proof_heroics": 0,
        "test_heroics": 0,
        "players": 0,
        "yaks_scorted": 0,
        "yaks": 0,
        "camps": 0,
        "castles": 0,
        "towers": 0,
        "keeps": 0,
    }


def _update_wallet_stats(user_stats: Dict, wallet_data: List[Dict]) -> None:
    """Update user stats with wallet information."""
    # Mapping of wallet IDs to stat names
    wallet_mapping = {
        1: "gold",
        2: "karma",
        3: "laurels",
        15: "badges_honor",
        16: "guild_commendations",
        26: "wvw_tickets",
        31: "proof_heroics",
        36: "test_heroics",
    }

    for wallet_item in wallet_data:
        wallet_id = wallet_item["id"]
        if wallet_id in wallet_mapping:
            stat_name = wallet_mapping[wallet_id]
            user_stats[stat_name] = wallet_item["value"]


def _update_achievement_stats(user_stats: Dict, achievements_data: List[Dict]) -> None:
    """Update user stats with achievement information."""
    # Mapping of achievement IDs to stat names
    achievement_mapping = {
        283: "players",
        285: "yaks_scorted",
        288: "yaks",
        291: "camps",
        294: "castles",
        297: "towers",
        300: "keeps",
    }

    for achievement in achievements_data:
        achievement_id = achievement["id"]
        if achievement_id in achievement_mapping:
            stat_name = achievement_mapping[achievement_id]
            user_stats[stat_name] = achievement.get("current", 0)


async def insert_session_char(
    bot: "commands.Bot", member: discord.Member, api_key: str, session_id: int, session_type: str
) -> None:
    """Insert session character data."""
    try:
        gw2_api = Gw2Client(bot)
        characters_data = await gw2_api.call_api("characters", api_key)

        insert_args = {
            "api_key": api_key,
            "session_id": session_id,
            "user_id": member.id,
            "start": session_type == "start",
            "end": session_type == "end",
        }

        gw2_session_chars_dal = Gw2SessionCharsDal(bot.db_session, bot.log)
        await gw2_session_chars_dal.insert_session_char(gw2_api, characters_data, insert_args)

    except Exception as e:
        bot.log.error(f"Error inserting session character data: {e}")


def get_wvw_rank_title(rank: int) -> str:
    """Get WvW rank title based on rank number."""
    prefix = _get_wvw_rank_prefix(rank)
    title = _get_wvw_rank_title(rank)
    return f"{prefix} {title}".strip()


def _get_wvw_rank_prefix(rank: int) -> str:
    """Get WvW rank prefix (Bronze, Silver, etc.)."""
    if 150 <= rank <= 619:
        return "Bronze"
    elif 620 <= rank <= 1394:
        return "Silver"
    elif 1395 <= rank <= 2544:
        return "Gold"
    elif 2545 <= rank <= 4094:
        return "Platinum"
    elif 4095 <= rank <= 6444:
        return "Mithril"
    elif rank >= 6445:
        return "Diamond"
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
    if 1 <= rank <= 9:
        return "Rabbit"
    elif 10 <= rank <= 19:
        return "Deer"
    elif 20 <= rank <= 29:
        return "Dolyak"
    elif 30 <= rank <= 39:
        return "Wolf"
    elif 40 <= rank <= 49:
        return "Tiger"
    elif 50 <= rank <= 59:
        return "Bear"
    elif 60 <= rank <= 69:
        return "Shark"
    elif 70 <= rank <= 79:
        return "Phoenix"
    elif rank >= 80:
        return "Dragon"
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


async def get_worlds_ids(ctx: "commands.Context") -> Tuple[bool, Optional[List[Dict]]]:
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
