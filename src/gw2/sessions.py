# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.utils import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_chars_end_dal import Gw2CharsEndDal
from src.database.dal.gw2.gw2_chars_start_dal import Gw2CharsStartDal
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal
from src.gw2.gw2 import GuildWars2
from src.gw2.utils import gw2_utils
from src.gw2.utils.gw2_cooldowns import GW2CoolDowns


class GW2Session(GuildWars2):
    """(Commands related to GW2 player last game session)"""
    def __init__(self, bot):
        super().__init__(bot)


@GW2Session.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Session.value, BucketType.user)
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

    gw2_configs = Gw2ConfigsDal(ctx.bot.db_session, ctx.bot.log)
    rs_gw2_sc = await gw2_configs.get_gw2_server_configs(ctx.guild.id)
    if len(rs_gw2_sc) == 0 or (len(rs_gw2_sc) > 0 and not rs_gw2_sc[0]["session"]):
        return await bot_utils.send_error_msg(ctx, "Last session is not active on this server.\n"
                                                   f"To activate use: `{ctx.prefix}gw2 config session on`")

    user_id = ctx.message.author.id
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    rs_api_key = await gw2_key_dal.get_server_user_api_key(ctx.guild.id, user_id)
    if not rs_api_key:
        return await bot_utils.send_error_msg(ctx, "You dont have an API key registered.\n"
                                                   f"To add or replace an API key send a DM with: `{ctx.prefix}gw2 key add <api_key>`\n"
                                                   f"To check your API key: `{ctx.prefix}gw2 key info`")

    api_key = rs_api_key[0]["key"]
    gw2_server = rs_api_key[0]["server_name"]
    api_permissions = str(rs_api_key[0]["permissions"])
    account = True
    wallet = True
    progression = True
    characters = True

    if "account" not in api_permissions:
        account = False
    if "wallet" not in api_permissions:
        wallet = False
    if "progression" not in api_permissions:
        progression = False
    if "characters" not in api_permissions:
        characters = False

    if account is False or wallet is False or progression is False or characters is False:
        error_msg = "To use this command your API key needs to have the following permissions:\n"
        error_msg += "- account is OK\n" if account is True else "- account is MISSING\n"
        error_msg += "- characters is OK\n" if characters is True else "- characters is MISSING\n"
        error_msg += "- progression is OK\n" if progression is True else "- progression is MISSING\n"
        error_msg += "- wallet is OK\n" if wallet is True else "- wallet is MISSING\n"
        error_msg += "Please add another API key with permissions that are MISSING if you want to use this command.\n" \
                     f"To add or replace an API key send a DM with: `{ctx.prefix}gw2 key add <api_key>`\n" \
                     f"To check your API key: `{ctx.prefix}gw2 key info`"
        return await bot_utils.send_error_msg(ctx, error_msg)

    still_playing_msg = None
    if (not (isinstance(ctx.channel, discord.DMChannel))
            and hasattr(ctx.message.author, "activity")
            and ctx.message.author.activity is not None
            and "guild wars 2" in str(ctx.message.author.activity.name).lower()):
        still_playing_msg = f"{ctx.message.author.mention}\n "\
                            "You are playing Guild Wars 2 at the moment.\n" \
                            "Your stats may NOT be accurate."
        await ctx.message.channel.typing()
        await gw2_utils.update_gw2_session_ends(ctx.bot, ctx.message.author, api_key)

    gw2_session_dal = Gw2SessionsDal(ctx.bot.db_session, ctx.bot.log)
    rs_session = await gw2_session_dal.get_user_last_session(user_id)
    if len(rs_session) > 0:
        if rs_session[0]["end_date"] is None:
            return await bot_utils.send_error_msg(ctx,
                                                  "There was a problem trying to record your last finished session.\n"
                                                  "Please, do not close discord when the game is running.",
                                                  True)

        await ctx.message.channel.typing()
        color = ctx.bot.settings["gw2"]["EmbedColor"]
        st_time = rs_session[0]["start_date"]
        ed_time = rs_session[0]["end_date"]

        time_passed = gw2_utils.get_time_passed(ed_time, bot_utils.get_current_date_time_str())
        player_wait_minutes = 1
        if time_passed.hours == 0 and time_passed.minutes < player_wait_minutes:
            wait_time = str(player_wait_minutes - time_passed.minutes)
            m = "minutes"
            if wait_time == "1":
                m = "minute"
            return await gw2_utils.send_msg(ctx,
                                            f"{ctx.message.author.mention}\n Bot still updating your stats!\n"
                                            f"Please wait {wait_time} {m} and try again.")

        st_date = rs_session[0]["start_date"].split()[0]
        acc_name = rs_session[0]["acc_name"]
        embed = discord.Embed(color=color)
        embed.set_author(name=f"{ctx.message.author.display_name}'s GW2 Last Session ({st_date})",
                         icon_url=ctx.message.author.avatar.url)
        embed.add_field(name="Account Name", value=chat_formatting.inline(acc_name))
        embed.add_field(name="Server", value=chat_formatting.inline(gw2_server))

        total_played_time = gw2_utils.get_time_passed(st_time, ed_time)
        embed.add_field(name="Total played time", value=chat_formatting.inline(str(total_played_time.timedelta)))

        if rs_session[0]["start_gold"] != rs_session[0]["end_gold"]:
            full_gold = str(rs_session[0]["end_gold"] - rs_session[0]["start_gold"])
            formatted_gold = gw2_utils.format_gold(full_gold)
            if int(full_gold) > 0:
                embed.add_field(name="Gained gold", value=chat_formatting.inline(f"+{formatted_gold}"), inline=False)
            elif int(full_gold) < 0:
                final_result = f"{formatted_gold}"
                if formatted_gold[0] != "-":
                    final_result = f"-{formatted_gold}"
                embed.add_field(name="Lost gold", value=chat_formatting.inline(str(final_result)), inline=False)

        gw2_chars_start_dal = Gw2CharsStartDal(ctx.bot.db_session, ctx.bot.log)
        rs_chars_start = await gw2_chars_start_dal.get_all_start_characters(user_id)
        if len(rs_chars_start) > 0:
            gw2_chars_end_dal = Gw2CharsEndDal(ctx.bot.db_session, ctx.bot.log)
            rs_chars_end = await gw2_chars_end_dal.get_all_end_characters(user_id)
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
                embed.add_field(name="Times you died", value=chat_formatting.inline(deaths_msg), inline=False)
            # else:
            #    deaths_msg = "0"
            #    embed.add_field(name="Times you died", value=chat_formatting.inline(deaths_msg))

        if rs_session[0]["start_karma"] != rs_session[0]["end_karma"]:
            final_result = str(rs_session[0]["end_karma"] - rs_session[0]["start_karma"])
            if int(final_result) > 0:
                embed.add_field(name="Gained karma", value=chat_formatting.inline(f"+{final_result}"))
            elif int(final_result) < 0:
                embed.add_field(name="Lost karma", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_laurels"] != rs_session[0]["end_laurels"]:
            final_result = str(rs_session[0]["end_laurels"] - rs_session[0]["start_laurels"])
            if int(final_result) > 0:
                embed.add_field(name="Gained laurels", value=chat_formatting.inline(f"+{final_result}"))
            elif int(final_result) < 0:
                embed.add_field(name="Lost laurels", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_wvw_rank"] != rs_session[0]["end_wvw_rank"]:
            final_result = str(rs_session[0]["end_wvw_rank"] - rs_session[0]["start_wvw_rank"])
            embed.add_field(name="Gained wvw ranks", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_yaks"] != rs_session[0]["end_yaks"]:
            final_result = str(rs_session[0]["end_yaks"] - rs_session[0]["start_yaks"])
            embed.add_field(name="Yaks killed", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_yaks_scorted"] != rs_session[0]["end_yaks_scorted"]:
            final_result = str(rs_session[0]["end_yaks_scorted"] - rs_session[0]["start_yaks_scorted"])
            embed.add_field(name="Yaks scorted", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_players"] != rs_session[0]["end_players"]:
            final_result = str(rs_session[0]["end_players"] - rs_session[0]["start_players"])
            embed.add_field(name="Players killed", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_keeps"] != rs_session[0]["end_keeps"]:
            final_result = str(rs_session[0]["end_keeps"] - rs_session[0]["start_keeps"])
            embed.add_field(name="Keeps captured", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_towers"] != rs_session[0]["end_towers"]:
            final_result = str(rs_session[0]["end_towers"] - rs_session[0]["start_towers"])
            embed.add_field(name="Towers captured", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_camps"] != rs_session[0]["end_camps"]:
            final_result = str(rs_session[0]["end_camps"] - rs_session[0]["start_camps"])
            embed.add_field(name="Camps captured", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_castles"] != rs_session[0]["end_castles"]:
            final_result = str(rs_session[0]["end_castles"] - rs_session[0]["start_castles"])
            embed.add_field(name="SMC captured", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_wvw_tickets"] != rs_session[0]["end_wvw_tickets"]:
            final_result = str(rs_session[0]["end_wvw_tickets"] - rs_session[0]["start_wvw_tickets"])
            if int(final_result) > 0:
                embed.add_field(name="Gained wvw tickets", value=chat_formatting.inline(f"+{final_result}"))
            elif int(final_result) < 0:
                embed.add_field(name="Lost wvw tickets", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_test_heroics"] != rs_session[0]["end_test_heroics"]:
            final_result = str(rs_session[0]["end_test_heroics"] - rs_session[0]["start_test_heroics"])
            if int(final_result) > 0:
                embed.add_field(name="Gained test. heroics", value=chat_formatting.inline(f"+{final_result}"))
            elif int(final_result) < 0:
                embed.add_field(name="Lost test. heroics", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_proof_heroics"] != rs_session[0]["end_proof_heroics"]:
            final_result = str(rs_session[0]["end_proof_heroics"] - rs_session[0]["start_proof_heroics"])
            if int(final_result) > 0:
                embed.add_field(name="Gained proof heroics", value=chat_formatting.inline(f"+{final_result}"))
            elif int(final_result) < 0:
                embed.add_field(name="Lost proof heroics", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_badges_honor"] != rs_session[0]["end_badges_honor"]:
            final_result = str(rs_session[0]["end_badges_honor"] - rs_session[0]["start_badges_honor"])
            if int(final_result) > 0:
                embed.add_field(name="Gained badges of honor", value=chat_formatting.inline(f"+{final_result}"))
            elif int(final_result) < 0:
                embed.add_field(name="Lost badges of honor", value=chat_formatting.inline(str(final_result)))

        if rs_session[0]["start_guild_commendations"] != rs_session[0]["end_guild_commendations"]:
            final_result = str(rs_session[0]["end_guild_commendations"]-rs_session[0]["start_guild_commendations"])
            if int(final_result) > 0:
                embed.add_field(name="Gained guild commendations", value=chat_formatting.inline(f"+{final_result}"))
            elif int(final_result) < 0:
                embed.add_field(name="Lost guild commendations", value=chat_formatting.inline(str(final_result)))

        if still_playing_msg is not None:
            await ctx.send(still_playing_msg)
        await bot_utils.send_embed(ctx, embed)
    else:
        await bot_utils.send_error_msg(
            ctx,
            "No records were found in your name.\n"
            "You are probably trying to execute this command without playing the game.\n"
            "Make sure your status is NOT set to invisible in discord.\n"
            "Make sure \"Display current running game as a status message\" is ON.\n"
            "Make sure to start discord on your Desktop FIRST before starting Guild Wars 2.",
            True
        )


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Session(bot))
