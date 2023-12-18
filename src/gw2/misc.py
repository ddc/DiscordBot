# -*- coding: utf-8 -*-
import re
import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from src.bot.utils import bot_utils, chat_formatting
from src.gw2.utils import gw2_utils, gw2_constants
from src.gw2.utils.gw2_api import Gw2Api


class GW2Misc(commands.Cog):
    """(Commands related to GW2)"""
    def __init__(self, bot):
        self.bot = bot

    async def wiki(self, ctx, search):
        if len(search) > 300:
            await ctx.send("Search too long")
            return

        posts = []
        len_eb_fields = 0
        wiki_url = gw2_constants.WIKI_URL
        search = search.replace(" ", "+")
        full_wiki_url = f"{wiki_url}/index.php?title=Special%3ASearch&search={search}&fulltext=Search"

        await ctx.message.channel.typing()
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
                total_posts = len(posts)
                if not posts:
                    await bot_utils.send_msg(ctx, "No results!")
                    return

                embed = discord.Embed(title="Wiki Search Results", color=ctx.bot.gw2_settings["EmbedColor"])

                if total_posts > 0:
                    i = 0

                    # discord only supports 25 embed fields
                    times_to_run = total_posts
                    if total_posts > 25:
                        times_to_run = 25

                    try:
                        while i <= times_to_run:
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

            embed.set_thumbnail(url=gw2_constants.GW2_WIKI_ICON_URL)
            await bot_utils.send_embed(ctx, embed)

    async def info(self, ctx, skill):
        wiki_url = gw2_constants.WIKI_URL
        skill = skill.replace(" ", "_")
        skill_sanitized = str(re.escape(skill)).title()
        skill_sanitized = skill_sanitized.replace("Of", "of")
        skill_sanitized = skill_sanitized.replace("The", "the")
        full_wiki_url = f"{wiki_url}/wiki/{skill_sanitized}"

        await ctx.message.channel.typing()
        async with self.bot.aiosession.get(full_wiki_url) as r:
            if r.status != 200:
                # info not found
                wrong_skill_name = str(skill_sanitized.replace('_', ' '))
                color = discord.Color.red()
                embed = discord.Embed(description=f"`{chat_formatting.NO_ENTRY}` Info not found: `{wrong_skill_name}`\n" \
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
                                tp_sell_price = gw2_utils.format_gold(sell_td[0]["data-price"])
                                tp_buy_price = gw2_utils.format_gold(buy_td[0]["data-price"])

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

            embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
            await bot_utils.send_embed(ctx, embed)

    async def worlds(self, ctx):
        """ (List all worlds)
            gw2 worlds
        """

        try:
            await ctx.message.channel.typing()
            endpoint = "worlds?ids=all"
            gw2_api = Gw2Api(self.bot)
            results = await gw2_api.call_api(endpoint)
        except Exception as e:
            await bot_utils.send_error_msg(ctx, e)
            return self.bot.log.error(ctx, e)

        color = self.bot.gw2_settings["EmbedColor"]
        desc_na = "~~~~~ NA Servers ~~~~~"
        embed_na = discord.Embed(color=color, description=chat_formatting.inline(desc_na))
        desc_eu = "~~~~~ EU Servers ~~~~~"
        embed_eu = discord.Embed(color=color, description=chat_formatting.inline(desc_eu))

        for world in results:
            try:
                await ctx.message.channel.typing()
                wid = world["id"]
                endpoint = f"wvw/matches?world={wid}"
                matches = await gw2_api.call_api(endpoint)
                if wid < 2001:
                    tier_number = matches["id"].replace("1-", "")
                    embed_na.add_field(name=world["name"],
                                       value=chat_formatting.inline(f"T{tier_number} {world['population']}"), inline=True)
                else:
                    tier_number = matches["id"].replace("2-", "")
                    embed_eu.add_field(name=world["name"],
                                       value=chat_formatting.inline(f"T{tier_number} {world['population']}"), inline=True)
            except Exception as e:
                await bot_utils.send_error_msg(ctx, e)
                return self.bot.log.error(ctx, e)

        await ctx.send(embed=embed_na)
        await ctx.send(embed=embed_eu)

    # async def api_test(self, ctx):
    #     from src.database.dal.gw2.gw2_key_sql import Gw2KeyDal
    #     user_id = ctx.message.author.id
    #     gw2Api = Gw2Api(self.bot)
    #     gw2KeySql = Gw2KeyDal(self.bot.db_session, self.bot.log)
    #     rs = await gw2KeySql.get_server_user_api_key(ctx.guild.id, user_id)
    #     api_key = rs[0]["key"]
    #
    #     endpoint = "/wvw/matches/1-3"
    #     api_req = await gw2Api.call_api(endpoint, key=api_key)
    #
    #     return api_req
