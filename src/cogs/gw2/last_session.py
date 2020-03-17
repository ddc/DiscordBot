#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import discord
from datetime import datetime
from discord.ext import commands
from src.sql.gw2.gw2_last_session_sql import Gw2LastSessionSql
from src.sql.gw2.gw2_chars_end_sql import Gw2CharsEndSql
from src.sql.gw2.gw2_chars_start_sql import Gw2CharsStartSql
from src.sql.gw2.gw2_key_sql import Gw2KeySql
from src.cogs.gw2.utils import gw2_utils as Gw2Utils
from src.cogs.bot.utils import bot_utils as BotUtils
from src.cogs.bot.utils import constants
from src.cogs.bot.utils import chat_formatting as Formatting


class GW2LastSession(commands.Cog):
    """(Commands related to GW2 player last session)"""

    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def gw2_lastSession(self, ctx):
        """(Info about the gw2 player last game session)
        
        Your API Key needs to have the following permissions:
        Account, Characters, Progression, Wallet 
        60 secs default cooldown
        
        Requirements:
        1) Start discord, make sure you are not set to invisible
        1) Add GW2 API Key (gw2 key add api_key)
        2) Need to show, on discord, that you are playing Guild Wars 2, change this on options
        3) Start gw2
        
        Example:
        gw2 lastsession
        """

        await ctx.message.channel.trigger_typing()
        discord_user_id = ctx.message.author.id
        gw2KeySql = Gw2KeySql(self.bot)
        rs_api_key = await gw2KeySql.get_server_user_api_key(ctx.guild.id, discord_user_id)

        if len(rs_api_key) == 0:
            return await BotUtils.send_error_msg(self, ctx,
                                              "You dont have an API key registered in this server.\n" \
                                              f"To add or replace an API key use: `{ctx.prefix}gw2 key add`\n"
                                              f"To check your API key use: `{ctx.prefix}gw2 key info`")

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
            prefix = str(self.bot.command_prefix[0])
            error_msg = "To use this command your API key needs to have the following permissions:\n"
            error_msg += "- account is OK\n" if account is True else "- account is MISSING\n"
            error_msg += "- characters is OK\n" if characters is True else "- characters is MISSING\n"
            error_msg += "- progression is OK\n" if progression is True else "- progression is MISSING\n"
            error_msg += "- wallet is OK\n" if wallet is True else "- wallet is MISSING\n"
            error_msg += "Please add another API key with permissions that are MISSING if you want to use this command.\n" \
                         f"To add or replace an API key use: `{prefix}gw2 key add <api_key>`\n" \
                         f"To check your API key use: `{ctx.prefix}gw2 key info`"
            return await BotUtils.send_error_msg(self, ctx, error_msg)

        gw2LastSessionSql = Gw2LastSessionSql(self.bot)
        rs_last_session = await gw2LastSessionSql.get_user_last_session(discord_user_id)

        if len(rs_last_session) > 0:
            st_date = rs_last_session[0]["start_date"].split()[0]
            acc_name = rs_last_session[0]["acc_name"]
            color = self.bot.gw2_settings["EmbedColor"]
            embed = discord.Embed(color=color)
            embed.set_author(name=f"{ctx.message.author.display_name}'s GW2 Last Session ({st_date})",
                             icon_url=ctx.message.author.avatar_url)
            embed.add_field(name="Account Name", value=Formatting.inline(acc_name), inline=True)
            embed.add_field(name="Server", value=Formatting.inline(gw2_server), inline=True)

            if rs_last_session[0]["end_date"] is None:
                rs_last_session[0]["end_date"] = BotUtils.get_todays_date_time()

            st_time = rs_last_session[0]["start_date"].split()[1]
            ed_time = rs_last_session[0]["end_date"].split()[1]
            # time_passed = BotUtils.get_time_passed(str(ed_time))

            still_playing_msg = None
            if not (isinstance(ctx.channel, discord.DMChannel)):
                if hasattr(ctx.message.author, "activity") \
                        and ctx.message.author.activity is not None \
                        and str(ctx.message.author.activity.name) == "Guild Wars 2":
                    still_playing_msg = f"{ctx.message.author.mention} You are playing Guild Wars 2 at the moment.\n" \
                                        "Your stats may NOT be accurate."
            #                 else:
            #                     if time_passed.hour == 0:
            #                         if time_passed.minute < 2:
            #                             wait_time = str(2-time_passed.minute)
            #                             m = "minutes"
            #                             if wait_time == "1":
            #                                 m = "minute"
            #                             return await BotUtils.send_msg(self, ctx, color,
            #                                   f"{ctx.message.author.mention} Anet API still updating your stats!\n"\
            #                                   f"Please wait {wait_time} more {m} to try again.")

            # getting stats
            try:
                await ctx.message.channel.trigger_typing()
                object_end = await Gw2Utils.get_last_session_user_stats(self, ctx, api_key)
            except Exception as e:
                await BotUtils.send_error_msg(self, ctx, e)
                return self.bot.log.error(ctx, e)

            # inserting characters
            try:
                await ctx.message.channel.trigger_typing()
                await Gw2Utils.insert_characters(self, ctx.message.author, api_key, "end", ctx)
            except Exception as e:
                await BotUtils.send_error_msg(self, ctx, e)
                return self.bot.log.error(ctx, e)

                # update stats
            await ctx.message.channel.trigger_typing()
            object_end.discord_user_id = discord_user_id
            await gw2LastSessionSql.update_last_session_end(object_end)

            # get new stats
            await ctx.message.channel.trigger_typing()
            updated_last_session = await gw2LastSessionSql.get_user_last_session(discord_user_id)

            FMT = constants.time_formatter
            total_played_time = datetime.strptime(ed_time, FMT) - datetime.strptime(st_time, FMT)
            if total_played_time.days < 0:
                total_played_time = str(total_played_time).split(",")[1].strip()
            embed.add_field(name="Total played time", value=Formatting.inline(total_played_time), inline=True)

            if updated_last_session[0]["start_gold"] != updated_last_session[0]["end_gold"]:
                full_gold = str(updated_last_session[0]["end_gold"] - updated_last_session[0]["start_gold"])
                formatted_gold = Gw2Utils.format_gold(full_gold)
                if int(full_gold) > 0:
                    embed.add_field(name="Gained gold", value=Formatting.inline(f"+{formatted_gold}"), inline=False)
                elif int(full_gold) < 0:
                    if formatted_gold[0] != "-":
                        final_result = f"-{formatted_gold}"
                    embed.add_field(name="Lost gold", value=Formatting.inline(str(formatted_gold)), inline=False)

            gw2CharsStartSql = Gw2CharsStartSql(self.bot)
            rs_chars_start = await gw2CharsStartSql.get_all_start_characters(discord_user_id)
            if len(rs_chars_start) > 0:
                gw2CharsEndSql = Gw2CharsEndSql(self.bot)
                rs_chars_end = await gw2CharsEndSql.get_all_end_characters(discord_user_id)
                prof_names = ""
                total_deaths = 0

                for keysA, char_start in rs_chars_start.items():
                    for keysB, char_end in rs_chars_end.items():
                        if char_start["name"] == char_end["name"]:
                            if char_start["deaths"] != char_end["deaths"]:
                                name = char_start["name"]
                                profession = char_start["profession"]
                                time_deaths = int(char_end["deaths"]) - int(char_start["deaths"])
                                total_deaths += time_deaths
                                prof_names += f"({profession}:{name}:{time_deaths})"

                if len(prof_names) > 0:
                    deaths_msg = f"{prof_names} [Total:{total_deaths}]"
                    embed.add_field(name="Times you died", value=Formatting.inline(deaths_msg), inline=False)
                # else:
                #    deaths_msg = "0"
                #    embed.add_field(name="Times you died", value=Formatting.inline(deaths_msg), inline=True)

            if updated_last_session[0]["start_karma"] != updated_last_session[0]["end_karma"]:
                final_result = str(updated_last_session[0]["end_karma"] - updated_last_session[0]["start_karma"])
                if int(final_result) > 0:
                    embed.add_field(name="Gained karma", value=Formatting.inline(f"+{final_result}"), inline=True)
                elif int(final_result) < 0:
                    embed.add_field(name="Lost karma", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_laurels"] != updated_last_session[0]["end_laurels"]:
                final_result = str(updated_last_session[0]["end_laurels"] - updated_last_session[0]["start_laurels"])
                if int(final_result) > 0:
                    embed.add_field(name="Gained laurels", value=Formatting.inline(f"+{final_result}"), inline=True)
                elif int(final_result) < 0:
                    embed.add_field(name="Lost laurels", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_wvw_rank"] != updated_last_session[0]["end_wvw_rank"]:
                final_result = str(updated_last_session[0]["end_wvw_rank"] - updated_last_session[0]["start_wvw_rank"])
                embed.add_field(name="Gained wvw ranks", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_yaks"] != updated_last_session[0]["end_yaks"]:
                final_result = str(updated_last_session[0]["end_yaks"] - updated_last_session[0]["start_yaks"])
                embed.add_field(name="Yaks killed", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_yaks_scorted"] != updated_last_session[0]["end_yaks_scorted"]:
                final_result = str(
                    updated_last_session[0]["end_yaks_scorted"] - updated_last_session[0]["start_yaks_scorted"])
                embed.add_field(name="Yaks scorted", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_players"] != updated_last_session[0]["end_players"]:
                final_result = str(updated_last_session[0]["end_players"] - updated_last_session[0]["start_players"])
                embed.add_field(name="Players killed", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_keeps"] != updated_last_session[0]["end_keeps"]:
                final_result = str(updated_last_session[0]["end_keeps"] - updated_last_session[0]["start_keeps"])
                embed.add_field(name="Keeps captured", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_towers"] != updated_last_session[0]["end_towers"]:
                final_result = str(updated_last_session[0]["end_towers"] - updated_last_session[0]["start_towers"])
                embed.add_field(name="Towers captured", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_camps"] != updated_last_session[0]["end_camps"]:
                final_result = str(updated_last_session[0]["end_camps"] - updated_last_session[0]["start_camps"])
                embed.add_field(name="Camps captured", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_castles"] != updated_last_session[0]["end_castles"]:
                final_result = str(updated_last_session[0]["end_castles"] - updated_last_session[0]["start_castles"])
                embed.add_field(name="SMC captured", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_wvw_tickets"] != updated_last_session[0]["end_wvw_tickets"]:
                final_result = str(
                    updated_last_session[0]["end_wvw_tickets"] - updated_last_session[0]["start_wvw_tickets"])
                if int(final_result) > 0:
                    embed.add_field(name="Gained wvw tickets", value=Formatting.inline(f"+{final_result}"), inline=True)
                elif int(final_result) < 0:
                    embed.add_field(name="Lost wvw tickets", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_test_heroics"] != updated_last_session[0]["end_test_heroics"]:
                final_result = str(
                    updated_last_session[0]["end_test_heroics"] - updated_last_session[0]["start_test_heroics"])
                if int(final_result) > 0:
                    embed.add_field(name="Gained test. heroics", value=Formatting.inline(f"+{final_result}"),
                                    inline=True)
                elif int(final_result) < 0:
                    embed.add_field(name="Lost test. heroics", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_proof_heroics"] != updated_last_session[0]["end_proof_heroics"]:
                final_result = str(
                    updated_last_session[0]["end_proof_heroics"] - updated_last_session[0]["start_proof_heroics"])
                if int(final_result) > 0:
                    embed.add_field(name="Gained proof heroics", value=Formatting.inline(f"+{final_result}"),
                                    inline=True)
                elif int(final_result) < 0:
                    embed.add_field(name="Lost proof heroics", value=Formatting.inline(str(final_result)), inline=True)

            if updated_last_session[0]["start_badges_honor"] != updated_last_session[0]["end_badges_honor"]:
                final_result = str(
                    updated_last_session[0]["end_badges_honor"] - updated_last_session[0]["start_badges_honor"])
                if int(final_result) > 0:
                    embed.add_field(name="Gained badges of honor", value=Formatting.inline(f"+{final_result}"),
                                    inline=True)
                elif int(final_result) < 0:
                    embed.add_field(name="Lost badges of honor", value=Formatting.inline(str(final_result)),
                                    inline=True)

            if updated_last_session[0]["start_guild_commendations"] != updated_last_session[0][
                "end_guild_commendations"]:
                final_result = str(updated_last_session[0]["end_guild_commendations"] - updated_last_session[0][
                    "start_guild_commendations"])
                if int(final_result) > 0:
                    embed.add_field(name="Gained guild commendations", value=Formatting.inline(f"+{final_result}"),
                                    inline=True)
                elif int(final_result) < 0:
                    embed.add_field(name="Lost guild commendations", value=Formatting.inline(str(final_result)),
                                    inline=True)

            if still_playing_msg is not None:
                await ctx.send(still_playing_msg)
            await BotUtils.send_embed(self, ctx, embed, False)
        else:
            await BotUtils.send_error_msg(self, ctx,
                                       "No records were found in your name.\n" \
                                       "Make sure your status is not set to invisible in discord.\n" \
                                       "Make sure \"Display current running game as a status message\" is ON.\n" \
                                       "Make sure to start discord on your Desktop first before you start Guild Wars 2.")
