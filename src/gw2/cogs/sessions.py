import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.tools import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.database.dal.gw2.gw2_session_chars_dal import Gw2SessionCharsDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


class GW2Session(GuildWars2):
    """(Commands related to GW2 player last game session)"""

    def __init__(self, bot):
        super().__init__(bot)


@GW2Session.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Session.seconds, BucketType.user)
async def session(ctx):
    """(Info about the gw2 player last game session)

    Your API Key needs to have the following permissions:
    Account, Characters, Progression, Wallet
    60 secs default cooldown

    Requirements:
    1) Start discord, make sure you are not set to invisible
    1) Add GW2 API Key (gw2 key add api_key)
    2) Need to show, on discord, that you are playing Guild Wars 2, change this on options
    3) Start gw2

    gw2 session
    """

    user_id = ctx.message.author.id
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    rs_api_key = await gw2_key_dal.get_api_key_by_user(user_id)
    if not rs_api_key:
        msg = gw2_messages.NO_API_KEY
        msg += gw2_messages.KEY_ADD_INFO_HELP.format(ctx.prefix)
        msg += gw2_messages.KEY_MORE_INFO_HELP.format(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)

    gw2_configs = Gw2ConfigsDal(ctx.bot.db_session, ctx.bot.log)
    rs_gw2_sc = await gw2_configs.get_gw2_server_configs(ctx.guild.id)
    if len(rs_gw2_sc) == 0 or (len(rs_gw2_sc) > 0 and not rs_gw2_sc[0]["session"]):
        return await bot_utils.send_warning_msg(ctx, gw2_messages.SESSION_NOT_ACTIVE.format(ctx.prefix))

    api_key = rs_api_key[0]["key"]
    gw2_server = rs_api_key[0]["server"]
    key_permissions = rs_api_key[0]["permissions"]
    account = True
    wallet = True
    progression = True
    characters = True

    if "account" not in key_permissions:
        account = False
    if "wallet" not in key_permissions:
        wallet = False
    if "progression" not in key_permissions:
        progression = False
    if "characters" not in key_permissions:
        characters = False

    if not any([account, wallet, progression, characters]):
        error_msg = f"{gw2_messages.SESSION_MISSING_PERMISSIONS_TITLE}:\n"
        error_msg += "- account is OK\n" if account is True else "- account is MISSING\n"
        error_msg += "- characters is OK\n" if characters is True else "- characters is MISSING\n"
        error_msg += "- progression is OK\n" if progression is True else "- progression is MISSING\n"
        error_msg += "- wallet is OK\n" if wallet is True else "- wallet is MISSING\n"
        error_msg += (
            f"{gw2_messages.ADD_RIGHT_API_KEY_PERMISSIONS}\n"
            f"{gw2_messages.KEY_ADD_INFO_HELP}"
            f"{gw2_messages.KEY_MORE_INFO_HELP.format(ctx.prefix)}"
        )
        return await bot_utils.send_error_msg(ctx, error_msg)

    gw2_session_dal = Gw2SessionsDal(ctx.bot.db_session, ctx.bot.log)
    rs_session = await gw2_session_dal.get_user_last_session(user_id)
    if not rs_session:
        return await bot_utils.send_error_msg(ctx, gw2_messages.USER_NO_SESSION_FOUND, True)

    rs_start = rs_session[0]["start"]
    rs_end = rs_session[0]["end"]

    if rs_end["date"] is None:
        return await bot_utils.send_error_msg(ctx, gw2_messages.SESSION_SAVE_ERROR, True)

    await ctx.message.channel.typing()
    color = ctx.bot.settings["gw2"]["EmbedColor"]
    start_time = bot_utils.convert_str_to_datetime_short(rs_start["date"])
    end_time = bot_utils.convert_str_to_datetime_short(rs_end["date"])

    time_passed = gw2_utils.get_time_passed(start_time, end_time)
    player_wait_minutes = 1
    if time_passed.hours == 0 and time_passed.minutes < player_wait_minutes:
        wait_time = str(player_wait_minutes - time_passed.minutes)
        m = "minute" if wait_time == "1" else "minutes"
        return await gw2_utils.send_msg(
            ctx, f"{gw2_messages.SESSION_BOT_STILL_UPDATING}\n {gw2_messages.WAITING_TIME}: `{wait_time} {m}`"
        )

    acc_name = rs_session[0]["acc_name"]
    embed = discord.Embed(color=color)
    embed.set_author(
        name=f"{ctx.message.author.display_name}'s {gw2_messages.SESSION_TITLE} ({rs_start['date'].split()[0]})",
        icon_url=ctx.message.author.avatar.url,
    )
    embed.add_field(name=gw2_messages.ACCOUNT_NAME, value=chat_formatting.inline(acc_name))
    embed.add_field(name=gw2_messages.SERVER, value=chat_formatting.inline(gw2_server))
    embed.add_field(name=gw2_messages.TOTAL_PLAYED_TIME, value=chat_formatting.inline(str(time_passed.timedelta)))

    if rs_start["gold"] != rs_end["gold"]:
        full_gold = str(rs_end["gold"] - rs_start["gold"])
        formatted_gold = gw2_utils.format_gold(full_gold)
        if int(full_gold) > 0:
            embed.add_field(
                name=gw2_messages.GAINED_GOLD,
                value=chat_formatting.inline(f"+{formatted_gold}"),
                inline=False,
            )
        elif int(full_gold) < 0:
            final_result = f"{formatted_gold}"
            if formatted_gold[0] != "-":
                final_result = f"-{formatted_gold}"
            embed.add_field(name=gw2_messages.LOST_GOLD, value=chat_formatting.inline(str(final_result)), inline=False)

    gw2_session_chars_dal = Gw2SessionCharsDal(ctx.bot.db_session, ctx.bot.log)
    rs_chars_start = await gw2_session_chars_dal.get_all_start_characters(user_id)
    if rs_chars_start:
        rs_chars_end = await gw2_session_chars_dal.get_all_end_characters(user_id)
        prof_names = ""
        total_deaths = 0

        for _, char_start in rs_chars_start.items():
            for _, char_end in rs_chars_end.items():
                if char_start["name"] == char_end["name"]:
                    if char_start["deaths"] != char_end["deaths"]:
                        name = char_start["name"]
                        profession = char_start["profession"]
                        time_deaths = int(char_end["deaths"]) - int(char_start["deaths"])
                        total_deaths += time_deaths
                        prof_names += f"({profession}:{name}:{time_deaths})"

        if len(prof_names) > 0:
            deaths_msg = f"{prof_names} [Total:{total_deaths}]"
            embed.add_field(name=gw2_messages.TIMES_YOU_DIED, value=chat_formatting.inline(deaths_msg), inline=False)

    if rs_start["karma"] != rs_end["karma"]:
        final_result = str(rs_end["karma"] - rs_start["karma"])
        field_name = gw2_messages.GAINED_KARMA if int(final_result) > 0 else gw2_messages.LOST_KARMA
        embed.add_field(name=field_name, value=chat_formatting.inline(f"+{final_result}"))

    if rs_start["laurels"] != rs_end["laurels"]:
        final_result = str(rs_end["laurels"] - rs_start["laurels"])
        field_name = gw2_messages.GAINED_LAURElS if int(final_result) > 0 else gw2_messages.LOST_LAURElS
        embed.add_field(name=field_name, value=chat_formatting.inline(f"+{final_result}"))

    if rs_start["wvw_rank"] != rs_end["wvw_rank"]:
        final_result = str(rs_end["wvw_rank"] - rs_start["wvw_rank"])
        embed.add_field(name=gw2_messages.GAINED_WVW_RANKS, value=chat_formatting.inline(str(final_result)))

    if rs_start["yaks"] != rs_end["yaks"]:
        final_result = str(rs_end["yaks"] - rs_start["yaks"])
        embed.add_field(name=gw2_messages.YAKS_KILLED, value=chat_formatting.inline(str(final_result)))

    if rs_start["yaks_scorted"] != rs_end["yaks_scorted"]:
        final_result = str(rs_end["yaks_scorted"] - rs_start["yaks_scorted"])
        embed.add_field(name=gw2_messages.YAKS_SCORTED, value=chat_formatting.inline(str(final_result)))

    if rs_start["players"] != rs_end["players"]:
        final_result = str(rs_end["players"] - rs_start["players"])
        embed.add_field(name=gw2_messages.PLAYERS_KILLED, value=chat_formatting.inline(str(final_result)))

    if rs_start["keeps"] != rs_end["keeps"]:
        final_result = str(rs_end["keeps"] - rs_start["keeps"])
        embed.add_field(name=gw2_messages.KEEPS_CAPTURED, value=chat_formatting.inline(str(final_result)))

    if rs_start["towers"] != rs_end["towers"]:
        final_result = str(rs_end["towers"] - rs_start["towers"])
        embed.add_field(name=gw2_messages.TOWERS_CAPTURED, value=chat_formatting.inline(str(final_result)))

    if rs_start["camps"] != rs_end["camps"]:
        final_result = str(rs_end["camps"] - rs_start["camps"])
        embed.add_field(name=gw2_messages.CAMPS_CAPTURED, value=chat_formatting.inline(str(final_result)))

    if rs_start["castles"] != rs_end["castles"]:
        final_result = str(rs_end["castles"] - rs_start["castles"])
        embed.add_field(name=gw2_messages.SMC_CAPTURED, value=chat_formatting.inline(str(final_result)))

    if rs_start["wvw_tickets"] != rs_end["wvw_tickets"]:
        final_result = str(rs_end["wvw_tickets"] - rs_start["wvw_tickets"])
        field_name = gw2_messages.GAINED_WVW_TICKETS if int(final_result) > 0 else gw2_messages.LOST_WVW_TICKETS
        embed.add_field(name=field_name, value=chat_formatting.inline(f"+{final_result}"))

    if rs_start["proof_heroics"] != rs_end["proof_heroics"]:
        final_result = str(rs_end["proof_heroics"] - rs_start["proof_heroics"])
        field_name = gw2_messages.GAINED_PROOF_HEROICS if int(final_result) > 0 else gw2_messages.LOST_PROOF_HEROICS
        embed.add_field(name=field_name, value=chat_formatting.inline(f"+{final_result}"))

    if rs_start["badges_honor"] != rs_end["badges_honor"]:
        final_result = str(rs_end["badges_honor"] - rs_start["badges_honor"])
        field_name = gw2_messages.GAINED_BADGES_HONOR if int(final_result) > 0 else gw2_messages.LOST_BADGES_HONOR
        embed.add_field(name=field_name, value=chat_formatting.inline(f"+{final_result}"))

    if rs_start["guild_commendations"] != rs_end["guild_commendations"]:
        final_result = str(rs_end["guild_commendations"] - rs_start["guild_commendations"])
        field_name = (
            gw2_messages.GAINED_GUILD_COMMENDATIONS if int(final_result) > 0 else gw2_messages.LOST_GUILD_COMMENDATIONS
        )
        embed.add_field(name=field_name, value=chat_formatting.inline(f"+{final_result}"))

    if (
        not (isinstance(ctx.channel, discord.DMChannel))
        and hasattr(ctx.message.author, "activity")
        and ctx.message.author.activity is not None
        and "guild wars 2" in str(ctx.message.author.activity.name).lower()
    ):
        still_playing_msg = f"{ctx.message.author.mention}\n {gw2_messages.SESSION_USER_STILL_PLAYING}"
        await ctx.message.channel.typing()
        await gw2_utils.end_session(ctx.bot, ctx.message.author, api_key)
        await ctx.send(still_playing_msg)

    await bot_utils.send_embed(ctx, embed)
    return None


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Session(bot))
