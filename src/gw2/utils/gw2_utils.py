# -*- coding: utf-8 -*-
from enum import Enum
import discord
from src.database.dal.gw2.gw2_chars_end_dal import Gw2CharsEndDal
from src.database.dal.gw2.gw2_chars_start_dal import Gw2CharsStartDal
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal
from src.bot.utils import bot_utils
from src.gw2.utils.gw2_api import Gw2Api


async def send_msg(ctx, msg):
    color = ctx.bot.gw2_settings["EmbedColor"]
    embed = discord.Embed(color=color, description=msg)
    embed.set_author(name=bot_utils.get_member_name_by_id(ctx), icon_url=ctx.message.author.avatar.url)
    await bot_utils.send_embed(ctx, embed)


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


async def delete_api_key(self, ctx, message=False):
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


async def last_session_gw2_event(bot, before: discord.Member, after: discord.Member):
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
        if len(rs_gw2_sc) > 0 and rs_gw2_sc[0]["last_session"] == "Y":
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
    prefix = ""
    title = ""

    if rank >= 150 < 620:
        prefix = "Bronze"
    if rank >= 620 < 1395:
        prefix = "Silver"
    if rank >= 1395 < 2545:
        prefix = "Gold"
    if rank >= 2545 < 4095:
        prefix = "Platinum"
    if rank >= 4095 < 6445:
        prefix = "Mithril"
    if rank >= 6445:
        prefix = "Diamond"

    if (rank >= 1 and rank < 5) or (rank >= 150 and rank < 180) or (rank >= 620 and rank < 670) or (
            rank >= 1395 and rank < 1470) or (rank >= 2545 and rank < 2645) or (rank >= 4095 and rank < 4245) or (
            rank >= 6445 and rank < 6695):
        title = "Invader"
    elif (rank >= 5 and rank < 10) or (rank >= 180 and rank < 210) or (rank >= 670 and rank < 720) or (
            rank >= 1470 and rank < 1545) or (rank >= 2645 and rank < 2745) or (rank >= 4245 and rank < 4395) or (
            rank >= 6695 and rank < 6945):
        title = "Assaulter"
    elif (rank >= 10 and rank < 15) or (rank >= 210 and rank < 240) or (rank >= 720 and rank < 770) or (
            rank >= 1545 and rank < 1620) or (rank >= 2745 and rank < 2845) or (rank >= 4395 and rank < 4545) or (
            rank >= 6945 and rank < 7195):
        title = "Raider"
    elif (rank >= 15 and rank < 20) or (rank >= 240 and rank < 270) or (rank >= 770 and rank < 820) or (
            rank >= 1620 and rank < 1695) or (rank >= 2845 and rank < 2945) or (rank >= 4545 and rank < 4695) or (
            rank >= 7195 and rank < 7445):
        title = "Recruit"
    elif (rank >= 20 and rank < 30) or (rank >= 270 and rank < 300) or (rank >= 820 and rank < 870) or (
            rank >= 1695 and rank < 1770) or (rank >= 2945 and rank < 3045) or (rank >= 4695 and rank < 4845) or (
            rank >= 7445 and rank < 7695):
        title = "Scout"
    elif (rank >= 30 and rank < 40) or (rank >= 300 and rank < 330) or (rank >= 840 and rank < 920) or (
            rank >= 1770 and rank < 1845) or (rank >= 3045 and rank < 3145) or (rank >= 4845 and rank < 4995) or (
            rank >= 7695 and rank < 7945):
        title = "Soldier"
    elif (rank >= 40 and rank < 50) or (rank >= 330 and rank < 360) or (rank >= 920 and rank < 970) or (
            rank >= 1845 and rank < 1920) or (rank >= 3145 and rank < 3245) or (rank >= 4995 and rank < 5145) or (
            rank >= 7945 and rank < 8195):
        title = "Squire"
    elif (rank >= 50 and rank < 60) or (rank >= 360 and rank < 390) or (rank >= 970 and rank < 1020) or (
            rank >= 1920 and rank < 1995) or (rank >= 3245 and rank < 3345) or (rank >= 5145 and rank < 5295) or (
            rank >= 8195 and rank < 8445):
        title = "Footman"
    elif (rank >= 60 and rank < 70) or (rank >= 390 and rank < 420) or (rank >= 1020 and rank < 1070) or (
            rank >= 1995 and rank < 2070) or (rank >= 3345 and rank < 3445) or (rank >= 5295 and rank < 5445) or (
            rank >= 8445 and rank < 8695):
        title = "Knight"
    elif (rank >= 70 and rank < 80) or (rank >= 420 and rank < 450) or (rank >= 1070 and rank < 1120) or (
            rank >= 2070 and rank < 2145) or (rank >= 3445 and rank < 3545) or (rank >= 5445 and rank < 5595) or (
            rank >= 8695 and rank < 8945):
        title = "Major"
    elif (rank >= 80 and rank < 90) or (rank >= 450 and rank < 480) or (rank >= 1120 and rank < 1170) or (
            rank >= 2145 and rank < 2220) or (rank >= 3545 and rank < 3645) or (rank >= 5595 and rank < 5745) or (
            rank >= 8945 and rank < 9195):
        title = "Colonel"
    elif (rank >= 90 and rank < 100) or (rank >= 480 and rank < 510) or (rank >= 1170 and rank < 1220) or (
            rank >= 2220 and rank < 2295) or (rank >= 3645 and rank < 3745) or (rank >= 5745 and rank < 5895) or (
            rank >= 9195 and rank < 9445):
        title = "General"
    elif (rank >= 100 and rank < 110) or (rank >= 510 and rank < 540) or (rank >= 1220 and rank < 1270) or (
            rank >= 2295 and rank < 2370) or (rank >= 3745 and rank < 3845) or (rank >= 5895 and rank < 6045) or (
            rank >= 9445 and rank < 9695):
        title = "Veteran"
    elif (rank >= 110 and rank < 120) or (rank >= 540 and rank < 570) or (rank >= 1270 and rank < 1320) or (
            rank >= 2370 and rank < 2445) or (rank >= 3845 and rank < 3945) or (rank >= 6045 and rank < 6195) or (
            rank >= 9695 and rank < 9945):
        title = "Champion"
    elif (rank >= 120) or (rank >= 570) or (rank >= 1320) or (rank >= 2445) or (rank >= 3945) or (rank >= 6195) or (
            rank >= 9945):
        title = "Legend"

    return f"{prefix} {title}"


def get_pvp_rank_title(rank: int):
    title = ""
    if rank >= 1 and rank < 10:
        title = "Rabbit"
    elif rank >= 10 and rank < 20:
        title = "Deer"
    elif rank >= 20 and rank < 30:
        title = "Dolyak"
    elif rank >= 30 and rank < 40:
        title = "Wolf"
    elif rank >= 40 and rank < 50:
        title = "Tiger"
    elif rank >= 50 and rank < 60:
        title = "Bear"
    elif rank >= 60 and rank < 70:
        title = "Shark"
    elif rank >= 70 and rank < 80:
        title = "Phoenix"
    elif rank >= 80:
        title = "Dragon"
    return f"{title}"


def check_gw2_server_name_role(role_name: str):
    for gw2_roles in Gw2_server_roles:
        if gw2_roles.value.lower() == role_name.lower():
            return True
    return False


class Gw2_server_roles(Enum):
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


def format_gold(currency: str):
    """
    Returns gold in string format
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
