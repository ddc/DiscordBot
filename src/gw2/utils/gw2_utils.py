# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from enum import Enum
import discord
from src.bot.utils import bot_utils
from src.bot.utils import constants
from src.bot.utils.bot_utils import Object
from src.database.dal.gw2.gw2_chars_end_dal import Gw2CharsEndDal
from src.database.dal.gw2.gw2_chars_start_dal import Gw2CharsStartDal
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal
from src.gw2.utils.gw2_api import Gw2Api


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


async def send_msg(ctx, msg):
    color = ctx.bot.gw2_settings["EmbedColor"]
    embed = discord.Embed(color=color, description=msg)
    embed.set_author(name=bot_utils.get_member_name_by_id(ctx), icon_url=ctx.message.author.avatar.url)
    await bot_utils.send_embed(ctx, embed)


async def insert_gw2_server_configs(bot, server):
    gw2_configs_dal = Gw2ConfigsDal(bot.db_session, bot.log)
    server_config = await gw2_configs_dal.get_gw2_server_configs(server.id)
    if not server_config:
        await gw2_configs_dal.insert_gw2_server_configs(server.id)


async def calculate_user_achiev_points(self, api_req_acc_achiev, api_req_acc):
    doc_user_achiev_id = []
    temp_achiv = []
    counter = 0
    gw2_api = Gw2Api(self.bot)
    total = api_req_acc["daily_ap"] + api_req_acc["monthly_ap"]

    for ach in api_req_acc_achiev:
        temp_achiv.insert(counter, str(ach["id"]))
        counter = counter + 1
        if counter == 200:
            all_user_achievs_ids = ','.join(temp_achiv)
            endpoint = f"achievements?ids={all_user_achievs_ids}"
            api_achiev = await gw2_api.call_api(endpoint)
            doc_user_achiev_id += api_achiev
            counter = 0
            temp_achiv = []

    for ach in api_req_acc_achiev:
        for doc in doc_user_achiev_id:
            if ach["id"] == doc["id"]:
                total += earned_ap(doc, ach)

    return total


def earned_ap(ach, res):
    earned = 0
    repeats = res["repeated"] if "repeated" in res else 0
    max_possible = max_ap(ach, repeats)
    for tier in ach["tiers"]:
        if res["current"] >= tier["count"]:
            earned += tier["points"]
    earned += max_ap(ach) * repeats
    if earned > max_possible:
        earned = max_possible
    return earned


def max_ap(ach, repeatable=False):
    if ach is None:
        return 0
    if repeatable:
        return ach["point_cap"]
    return sum([t["points"] for t in ach["tiers"]])


async def get_world_id(self, world):
    if world is None:
        return None
    gw2_api = Gw2Api(self.bot)
    results = await gw2_api.call_api("worlds?ids=all")
    for name in results:
        if name["name"].lower() == world.lower():
            return name["id"]
    return None


async def get_world_name_population(self, wids: str):
    try:
        name = []
        endpoint = f"worlds?ids={wids}"
        gw2_api = Gw2Api(self.bot)
        results = await gw2_api.call_api(endpoint)
        if len(results) == 0:
            return None
        else:
            for x in results:
                name.append(x["name"])
                # name.append(x["name"]+" ("+x["population"]+")")
    except:
        name = None
    return name


async def get_world_name(self, wids: str):
    try:
        endpoint = f"worlds?ids={wids}"
        gw2_api = Gw2Api(self.bot)
        results = await gw2_api.call_api(endpoint)
        if len(results) == 0:
            return None
        else:
            name = results["name"]
    except:
        name = None
    return name


async def delete_api_key(ctx, message=False):
    if not isinstance(ctx.channel, discord.DMChannel):
        try:
            await ctx.message.delete()
            if message:
                await send_msg(ctx, "Your message with your API Key was removed for privacy.")
        except:
            await bot_utils.send_error_msg(ctx,
                                           "Bot does not have permission to delete the message with your API key.\n"
                                           "Missing bot permission: `Manage Messages`")


def is_private_message(ctx):
    return True if isinstance(ctx.channel, discord.DMChannel) else False


async def check_gw2_game_activity(bot, before: discord.Member, after: discord.Member):
    before_activity = None
    after_activity = None

    for bact in before.activities:
        if bact.type is not discord.ActivityType.custom:
            before_activity = bact

    for aact in after.activities:
        if aact.type is not discord.ActivityType.custom:
            after_activity = aact

    if ((after_activity is not None and "guild wars 2" in str(after_activity.name).lower())
            and (after_activity.type == discord.ActivityType.playing or after_activity.type == discord.ActivityType.streaming)
            or (before_activity is not None and "guild wars 2" in str(before_activity.name).lower())
            and (before_activity.type == discord.ActivityType.playing or before_activity.type == discord.ActivityType.streaming)):
        gw2_configs = Gw2ConfigsDal(bot.db_session, bot.log)
        rs_gw2_sc = await gw2_configs.get_gw2_server_configs(after.guild.id)
        if len(rs_gw2_sc) > 0 and rs_gw2_sc[0]["last_session"]:
            gw2_key_sql = Gw2KeyDal(bot.db_session, bot.log)
            rs_api_key = await gw2_key_sql.get_server_user_api_key(after.guild.id, after.id)
            if len(rs_api_key) > 0:
                if after_activity is not None:
                    await insert_gw2_session_starts(bot, after, rs_api_key[0]["key"])
                else:
                    await update_gw2_session_ends(bot, before, rs_api_key[0]["key"])


async def insert_gw2_session_starts(bot, after: discord.Member, api_key):
    object_start = await get_last_session_user_stats(bot, None, api_key)
    object_start.user_id = after.id
    object_start.date = bot_utils.get_current_date_time_str()
    gw2_last_session_sql = Gw2SessionsDal(bot.db_session, bot.log)
    await gw2_last_session_sql.insert_start_session(object_start)
    await insert_characters(bot, after, api_key, "start")


async def update_gw2_session_ends(bot, before: discord.Member, api_key):
    object_end = await get_last_session_user_stats(bot, None, api_key)
    object_end.user_id = before.id
    object_end.date = bot_utils.get_current_date_time_str()
    gw2_last_session_sql = Gw2SessionsDal(bot.db_session, bot.log)
    await gw2_last_session_sql.update_end_session(object_end)
    await insert_characters(bot, before, api_key, "end")


async def get_last_session_user_stats(self, ctx, api_key):
    if not (hasattr(self, "bot")):
        self.bot = self
    gw2_api = Gw2Api(self.bot)
    user_obj = bot_utils.Object()
    user_obj.gold = 0
    user_obj.karma = 0
    user_obj.laurels = 0
    user_obj.badges_honor = 0
    user_obj.guild_commendations = 0
    user_obj.wvw_tickets = 0
    user_obj.proof_heroics = 0
    user_obj.test_heroics = 0
    user_obj.players = 0
    user_obj.yaks_scorted = 0
    user_obj.yaks = 0
    user_obj.camps = 0
    user_obj.castles = 0
    user_obj.towers = 0
    user_obj.keeps = 0

    try:
        api_req_acc = await gw2_api.call_api("account", key=api_key)
        api_req_wallet = await gw2_api.call_api("account/wallet", key=api_key)
        api_req_achiev = await gw2_api.call_api("account/achievements", key=api_key)
    except Exception as e:
        if ctx is not None:
            await bot_utils.send_info_msg(ctx, "GW2 API is currently down. Try again later...")
        return self.bot.log.error(e)

    user_obj.acc_name = api_req_acc["name"]
    user_obj.wvw_rank = api_req_acc["wvw_rank"]

    if len(api_req_wallet) > 0:
        for wallet in api_req_wallet:
            if wallet["id"] == 1:
                user_obj.gold = wallet["value"]
            if wallet["id"] == 2:
                user_obj.karma = wallet["value"]
            if wallet["id"] == 3:
                user_obj.laurels = wallet["value"]
            if wallet["id"] == 15:
                user_obj.badges_honor = wallet["value"]
            if wallet["id"] == 16:
                user_obj.guild_commendations = wallet["value"]
            if wallet["id"] == 26:
                user_obj.wvw_tickets = wallet["value"]
            if wallet["id"] == 31:
                user_obj.proof_heroics = wallet["value"]
            if wallet["id"] == 36:
                user_obj.test_heroics = wallet["value"]

    if len(api_req_achiev) > 0:
        for achiev in api_req_achiev:
            if achiev["id"] == 283:
                user_obj.players = achiev["current"]
            if achiev["id"] == 285:
                user_obj.yaks_scorted = achiev["current"]
            if achiev["id"] == 288:
                user_obj.yaks = achiev["current"]
            if achiev["id"] == 291:
                user_obj.camps = achiev["current"]
            if achiev["id"] == 294:
                user_obj.castles = achiev["current"]
            if achiev["id"] == 297:
                user_obj.towers = achiev["current"]
            if achiev["id"] == 300:
                user_obj.keeps = achiev["current"]

    return user_obj


async def insert_characters(self, member: discord.Member, api_key, type_session: str, ctx=None):
    if not (hasattr(self, "bot")):
        self.bot = self

    try:
        gw2_api = Gw2Api(self.bot)
        api_req_characters = await gw2_api.call_api("characters", key=api_key)
        insert_obj = bot_utils.Object()
        insert_obj.api_key = api_key
        insert_obj.ctx = ctx
        insert_obj.gw2_api = gw2_api
        insert_obj.user_id = member.id

        if type_session == "start":
            gw2_chars_start_sql = Gw2CharsStartDal(self.bot.db_session, self.bot.log)
            await gw2_chars_start_sql.insert_character(insert_obj, api_req_characters)
        else:
            gw2_chars_end_sql = Gw2CharsEndDal(self.bot.db_session, self.bot.log)
            await gw2_chars_end_sql.insert_character(insert_obj, api_req_characters)

    except Exception as e:
        return self.bot.log.error(e)


def get_wvw_rank_title(rank: int):
    match rank:
        case num if num in range(150, 619):
            prefix = "Bronze"
        case num if num in range(620, 1394):
            prefix = "Silver"
        case num if num in range(1395, 2544):
            prefix = "Gold"
        case num if num in range(2545, 4094):
            prefix = "Platinum"
        case num if num in range(4095, 6444):
            prefix = "Mithril"
        case num if num >= 6445:
            prefix = "Diamond"
        case _:
            prefix = ""

    match rank:
        case num if num in range(1, 4) or num in range(150, 179) or num in range(620, 669) or num in range(1695, 1469) or num in range(2545, 2644) or num in range(4095, 4244) or num in range(6445, 6694):
            title = "Invader"
        case num if num in range(5, 9) or num in range(180, 209) or num in range(670, 719) or num in range(1470, 1544) or num in range(2645, 2744) or num in range(4245, 4394) or num in range(6695, 6944):
            title = "Assaulter"
        case num if num in range(10, 14) or num in range(210, 239) or num in range(720, 769) or num in range(1545, 1619) or num in range(2745, 2844) or num in range(4395, 4544) or num in range(6945, 7194):
            title = "Raider"
        case num if num in range(15, 19) or num in range(240, 269) or num in range(770, 819) or num in range(1620, 1694) or num in range(2845, 2944) or num in range(4545, 4694) or num in range(7195, 7444):
            title = "Recruit"
        case num if num in range(20, 29) or num in range(270, 299) or num in range(820, 869) or num in range(1695, 1769) or num in range(2945, 3044) or num in range(4695, 4844) or num in range(7445, 7694):
            title = "Scout"
        case num if num in range(30, 39) or num in range(300, 329) or num in range(840, 919) or num in range(1770, 1844) or num in range(3045, 3144) or num in range(4845, 4994) or num in range(7695, 7944):
            title = "Soldier"
        case num if num in range(40, 49) or num in range(330, 359) or num in range(920, 969) or num in range(1845, 1919) or num in range(3145, 3244) or num in range(4995, 5144) or num in range(7945, 8194):
            title = "Squire"
        case num if num in range(50, 59) or num in range(360, 389) or num in range(970, 1019) or num in range(1920, 1994) or num in range(3245, 3344) or num in range(5145, 5294) or num in range(8195, 8444):
            title = "Footman"
        case num if num in range(60, 69) or num in range(390, 419) or num in range(1020, 1069) or num in range(1995, 2069) or num in range(3345, 3444) or num in range(5295, 5444) or num in range(8445, 8694):
            title = "Knight"
        case num if num in range(70, 79) or num in range(420, 449) or num in range(1070, 1119) or num in range(2070, 2144) or num in range(3445, 3544) or num in range(5445, 5594) or num in range(8695, 8944):
            title = "Major"
        case num if num in range(80, 89) or num in range(450, 479) or num in range(1120, 1169) or num in range(2145, 2219) or num in range(3545, 3644) or num in range(5595, 5744) or num in range(8945, 9194):
            title = "Colonel"
        case num if num in range(90, 99) or num in range(480, 509) or num in range(1170, 1219) or num in range(2220, 2294) or num in range(3645, 3744) or num in range(5745, 5894) or num in range(9195, 9444):
            title = "General"
        case num if num in range(100, 109) or num in range(510, 539) or num in range(1220, 1269) or num in range(2295, 2369) or num in range(3745, 3844) or num in range(5895, 6044) or num in range(9445, 9694):
            title = "Veteran"
        case num if num in range(110, 119) or num in range(540, 569) or num in range(1270, 1319) or num in range(2370, 2444) or num in range(3845, 3944) or num in range(6045, 6194) or num in range(9695, 9944):
            title = "Champion"
        case num if num in range(rank >= 120) or num in range(rank >= 570) or num in range(rank >= 1320) or num in range(rank >= 2445) or num in range(rank >= 3945) or num in range(rank >= 6195) or num in range(rank >= 9945):
            title = "Legend"
        case _:
            title = ""

    return f"{prefix} {title}"


def get_pvp_rank_title(rank: int):
    match rank:
        case num if num in range(1, 9):
            title = "Rabbit"
        case num if num in range(10, 19):
            title = "Deer"
        case num if num in range(20, 29):
            title = "Dolyak"
        case num if num in range(30, 39):
            title = "Wolf"
        case num if num in range(40, 49):
            title = "Tiger"
        case num if num in range(50, 59):
            title = "Bear"
        case num if num in range(60, 69):
            title = "Shark"
        case num if num in range(70, 79):
            title = "Phoenix"
        case num if num >= 80:
            title = "Dragon"
        case _:
            title = ""
    return title


def format_gold(currency: str):
    """
        Returns gold in string format:
        20 Gold 35 Silver 15 Copper
    """

    formatted_gold = ""
    copper = str(currency[-2:])
    silver = str(currency[-4:][:-2])
    gold = str(currency[:-4])

    if len(gold) > 0 and gold != "-":
        formatted_gold += f"{gold} Gold "
    if len(silver) > 0:
        formatted_gold += f"{silver} Silver "
    if str(copper) != "00" and len(copper) > 0:
        formatted_gold += f"{copper} Copper"

    return formatted_gold


def get_time_passed(start_time_str, end_time_str):
    date_time_formatter = f"{constants.DATE_FORMATTER} {constants.TIME_FORMATTER}"
    time_passed_delta = (datetime.strptime(end_time_str, date_time_formatter) -
                         datetime.strptime(start_time_str, date_time_formatter))
    time_passed_obj = convert_timedelta_to_obj(time_passed_delta)
    return time_passed_obj


def convert_timedelta_to_obj(time_delta: timedelta):
    obj = Object()
    obj.timedelta = time_delta
    if "," in str(time_delta):
        obj.days = int(str(time_delta).split()[0].strip())
        obj.hours = int(str(time_delta).split(":")[0].split(",")[1].strip())
        obj.minutes = int(str(time_delta).split(":")[1].strip())
        obj.seconds = int(str(time_delta).split(":")[2].strip())
    else:
        obj.days = 0
        obj.hours = int(str(time_delta).split(":")[0].strip())
        obj.minutes = int(str(time_delta).split(":")[1].strip())
        obj.seconds = int(str(time_delta).split(":")[2].strip())
    return obj
