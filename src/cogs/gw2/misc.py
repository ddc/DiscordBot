# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import re
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
from src.cogs.gw2.utils.gw2_api import Gw2Api
from src.cogs.bot.utils import bot_utils as BotUtils
from src.cogs.gw2.utils import gw2_utils as Gw2Utils
from src.cogs.bot.utils import chat_formatting as Formatting
import src.cogs.gw2.utils.gw2_constants as Gw2Constants


class GW2Misc(commands.Cog):
    """(Commands related to GW2)"""
    def __init__(self, bot):
        self.bot = bot


    async def gw2_wiki(self, ctx, search):
        if len(search) > 300:
            await ctx.send("Search too long")
            return

        posts = []
        len_eb_fields = 0
        wiki_url = Gw2Constants.WIKI_URL
        search = search.replace(" ", "+")
        full_wiki_url = (f"{wiki_url}/index.php?title=Special%3ASearch&search={search}&fulltext=Search")

        await ctx.message.channel.trigger_typing()
        async with self.bot.aiosession.get(full_wiki_url) as r:
            if r.history:
                soup = BeautifulSoup(await r.text(), 'html.parser')
                color = discord.Color.red()
                embed = discord.Embed(title=soup.title.get_text(),
                                      color=color,
                                      url=str(r.url))
            else:
                results = await r.text()
                soup = BeautifulSoup(results, 'html.parser')
                posts = soup.find_all("div", {"class": "mw-search-result-heading"})[:50]
                totalPosts = len(posts)
                color = self.bot.gw2_settings["EmbedColor"]
                if not posts:
                    await BotUtils.send_msg(self, ctx, color, "No results!")
                    return

                embed = discord.Embed(title="Wiki Search Results", color=color)

                if totalPosts > 0:
                    i = 0

                    # discord only supports 25 embed fields
                    timesToRun = totalPosts
                    if totalPosts > 25:
                        timesToRun = 25

                    try:
                        while i <= timesToRun:
                            post = posts[i]
                            post = post.a
                            url = wiki_url + post['href']
                            url = url.replace(")", "\\)")
                            keyword = search.lower().replace("+", " ")
                            found = False

                            if keyword in str(post["title"]).lower():
                                if len_eb_fields > 0:
                                    for eb_field in embed.fields:
                                        if keyword.title() == eb_field.name:
                                            found = True
                                            break
                                    if not found and "/history" not in post["title"]:
                                        embed.add_field(name=post["title"], value=f"[Click here]({url})", inline=True)
                                        len_eb_fields += 1
                                elif "/history" not in post["title"]:
                                    embed.add_field(name=post["title"], value=f"[Click here]({url})", inline=True)
                                    len_eb_fields += 1
                            i += 1
                    except IndexError:
                        pass

                    embed.description = f"Displaying **{len(embed.fields)}** closest titles that matches **{keyword.title()}**"
                else:
                    embed.add_field(name="No results", value=f"[Click here]({full_wiki_url})")

            embed.set_thumbnail(url=Gw2Constants.GW2_WIKI_ICON_URL)
            await BotUtils.send_embed(self, ctx, embed, False)


    async def gw2_info(self, ctx, skill):
        wiki_url = Gw2Constants.WIKI_URL
        skill = skill.replace(" ", "_")
        skill_sanitized = str(re.escape(skill)).title()
        skill_sanitized = skill_sanitized.replace("Of", "of")
        skill_sanitized = skill_sanitized.replace("The", "the")
        full_wiki_url = (f"{wiki_url}/wiki/{skill_sanitized}")

        await ctx.message.channel.trigger_typing()
        async with self.bot.aiosession.get(full_wiki_url) as r:
            if r.status != 200:
                # info not found
                wrong_skill_name = str(skill_sanitized.replace('_', ' '))
                color = discord.Color.red()
                embed = discord.Embed(description=f"`{Formatting.NO_ENTRY}` Info not found: `{wrong_skill_name}`\n" \
                                                  "Please check your spelling and try again!",
                                      color=color)
            else:
                skill_url = str(r.url)
                skill_name = str(r.url).split("/")[-1:][0].replace("_", " ")
                skill_icon_url = ""

                results = await r.text()
                soup = BeautifulSoup(results, 'html.parser')
                for br in soup.find_all("br"):
                    br.replace_with("\n")

                for image in soup.findAll("img"):
                    image_name = image.get('alt', '')
                    if image_name.lower() == f"{skill_sanitized.replace('_', ' ').lower()}.png":
                        try:
                            skill_icon_url = f"{wiki_url}{image['srcset'].split()[0]}"
                            break
                        except KeyError:
                            pass

                skill_description = soup.find('blockquote')
                if skill_description is not None:
                    skill_description = skill_description.get_text()[2:].split("—")[0]
                    skill_description = skill_description.replace("?", "")
                    color = self.bot.gw2_settings["EmbedColor"]

                    myspans = soup.findAll("span", {"class": "gw2-tpprice"})
                    if len(myspans) > 0:
                        item_id = myspans[0]["data-id"]
                    else:
                        item_id = None

                    if item_id is not None:
                        gw2tp_url = f"https://www.gw2tp.com/item/{item_id}-{skill_sanitized.replace('_', '-').lower()}"
                        async with self.bot.aiosession.get(gw2tp_url) as tp_r:
                            if tp_r.status == 200:
                                gw2bltc_url = f"https://www.gw2bltc.com/en/item/{item_id}-{skill_sanitized.replace('_', '-').lower()}"
                                tp_results = await tp_r.text()
                                sell_td = BeautifulSoup(tp_results, 'html.parser').findAll("td", {"id": "sell-price"})
                                buy_td = BeautifulSoup(tp_results, 'html.parser').findAll("td", {"id": "buy-price"})
                                tp_sell_price = Gw2Utils.format_gold(sell_td[0]["data-price"])
                                tp_buy_price = Gw2Utils.format_gold(buy_td[0]["data-price"])

                                skill_description = f"{skill_description}\n" \
                                                    "**Trading Post:**\n" \
                                                    f"Sell: *{tp_sell_price}*\n" \
                                                    f"Buy: *{tp_buy_price}*\n" \
                                                    f"[Gw2tp]({gw2tp_url}) / [Gw2bltc]({gw2bltc_url})"
                else:
                    skill_description = "Click on link above for more info !!!"
                    color = discord.Color.red()

                embed = discord.Embed(title=skill_name,
                                      description=skill_description,
                                      color=color,
                                      url=skill_url)
                embed.set_thumbnail(url=skill_icon_url)

            embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar_url)
            await BotUtils.send_embed(self, ctx, embed, False)


    async def gw2_worlds(self, ctx):
        """ (List all worlds)

        Example:
        gw2 worlds
        """

        try:
            await ctx.message.channel.trigger_typing()
            endpoint = "worlds?ids=all"
            gw2Api = Gw2Api(self.bot)
            results = await gw2Api.call_api(endpoint)
        except Exception as e:
            await BotUtils.send_error_msg(self, ctx, e)
            return self.bot.log.error(ctx, e)

        color = self.bot.gw2_settings["EmbedColor"]
        desc_na = "~~~~~ NA Servers ~~~~~"
        embed_na = discord.Embed(color=color, description=Formatting.inline(desc_na))
        desc_eu = "~~~~~ EU Servers ~~~~~"
        embed_eu = discord.Embed(color=color, description=Formatting.inline(desc_eu))

        for world in results:
            try:
                await ctx.message.channel.trigger_typing()
                wid = world["id"]
                endpoint = f"wvw/matches?world={wid}"
                matches = await gw2Api.call_api(endpoint)
                if wid < 2001:
                    tier_number = matches["id"].replace("1-", "")
                    embed_na.add_field(name=world["name"],
                                       value=Formatting.inline(f"T{tier_number} {world['population']}"), inline=True)
                else:
                    tier_number = matches["id"].replace("2-", "")
                    embed_eu.add_field(name=world["name"],
                                       value=Formatting.inline(f"T{tier_number} {world['population']}"), inline=True)
            except Exception as e:
                await BotUtils.send_error_msg(self, ctx, e)
                return self.bot.log.error(ctx, e)

        await ctx.send(embed=embed_na)
        await ctx.send(embed=embed_eu)


    # async def api_test(self, ctx):
    #     from src.sql.gw2.gw2_key_sql import Gw2KeySql
    #     discord_user_id = ctx.message.author.id
    #     gw2Api = Gw2Api(self.bot)
    #     gw2KeySql = Gw2KeySql(self.bot.log)
    #     rs = await gw2KeySql.get_server_user_api_key(ctx.guild.id, discord_user_id)
    #     api_key = rs[0]["key"]
    #
    #     endpoint = "/wvw/matches/1-3"
    #     api_req = await gw2Api.call_api(endpoint, key=api_key)
    #
    #     return api_req


    # async def praise_joko(self, ctx):
    #     """To defy his Eminence is to defy life itself"""
    #     praise_art = (
    #         "```fix\nP R A I S E\nR J     O S\nA   O K   I\nI   O K   "
    #         "A\nS J     O R\nE S I A R P```")
    #     await ctx.send(random.choice([praise_art, "Praise joko " * 40]))


    # async def gw2_ping(self, ctx, *,world_name:str):
    #     """ (Ping a world)
    #
    #     This command is actually measuring RTT (round trip time).
    #     RTT is always going to be a little bit higher than ping.
    #     Ping = Time for a packet to reach the server and be sent back.
    #     RTT = Time for a packet to reach the server, get processed and be sent back.
    #
    #
    #     [WORLDS_IP]
    #     EBG     = "18.210.69.163"
    #     REDBL   = "52.203.251.203"
    #     BLUEBL  = "35.169.27.155"
    #     GREENBL = "52.201.192.50"
    #     OS      = "54.89.202.110"
    #
    #
    #     Example:
    #     gw2 ping world name
    #
    #     gw2 ping ebg
    #     gw2 ping redbl
    #     gw2 ping bluebl
    #     gw2 ping greenbl
    #     gw2 ping os
    #
    #     """
    #
    #     await ctx.message.channel.trigger_typing()
    #     if (BotUtils.is_nping_installed()):
    #         max_rtt = None
    #         min_rtt = None
    #         avg_rtt = None
    #         world_name = str(world_name.replace(ctx.prefix+"gw2 ping ", "")).split(' ', 1)[0]
    #         ip = bot.gw2_settings[world_name.upper()] # BotUtils.get_ini_settings(Gw2Constants.GW2_SETTINGS_FILENAME, "WORLDS_IP", world_name.upper())
    #         result = subprocess.Popen(['nping','-c3','--tcp-connect','-p6112',ip], shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #         for line in result.stdout.readlines():
    #             if "Max rtt" in str(line, 'utf-8'):
    #                 if max_rtt is None:
    #                     max_rtt = str(line).split("|")[0].split(":")[1].strip(' ').split(".")[0] + " ms"
    #                 if min_rtt is None:
    #                     min_rtt = str(line).split("|")[1].split(":")[1].strip(' ').split(".")[0] + " ms"
    #                 if avg_rtt is None:
    #                     avg_rtt = str(line).split("|")[2].split(":")[1].strip(' ').split(".")[0] + " ms"
    #     else:
    #         msg = "Unable to ping GW2 servers.\nPlease contact a Bot Admin."
    #         raise commands.CommandInvokeError(msg)
    #
    #     if avg_rtt is None or avg_rtt == "N/A ms":
    #         msg = "IP Address not valid.\nPlease contact a Bot Admin to update the ip config file."
    #         raise commands.CommandInvokeError(msg)
    #
    #     if(world_name.upper() == "REDBL"):
    #         color = discord.Color.red()
    #     elif(world_name.upper() == "BLUEBL"):
    #         color = discord.Color.blue()
    #     elif(world_name.upper() == "GREENBL"):
    #         color = discord.Color.green()
    #     else:
    #         color = BotUtils.get_random_color()
    #
    #     msg = f"IP: {ip}\n"
    #     msg += f"Max: {max_rtt}\n"
    #     msg += f"Min: {min_rtt}\n"
    #     msg += f"Avg: {avg_rtt}"
    #     embed = discord.Embed(color=color,description=world_name.upper()+"\n"+Formatting.inline(msg))
    #     embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar_url)
    #     embed.set_footer(text=f"For more info: {ctx.prefix}help gw2 ping")
    #     await BotUtils.send_embed(self, ctx, embed, False, msg)
