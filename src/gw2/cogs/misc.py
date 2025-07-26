import re
import discord
from bs4 import BeautifulSoup
from src.bot.tools import bot_utils
from src.gw2.tools import gw2_utils
from src.gw2.constants import gw2_variables
from src.gw2.cogs.gw2 import GuildWars2
from discord.ext import commands
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns
from discord.ext.commands.cooldowns import BucketType
from src.gw2.constants import gw2_messages


class GW2Misc(GuildWars2):
    """(Commands related to GW2)"""
    def __init__(self, bot):
        super().__init__(bot)


@GW2Misc.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Misc.value, BucketType.user)
async def wiki(ctx, *, search):
    """ (Search the Guild wars 2 wiki)
            gw2 wiki name_to_search
    """

    if len(search) > 300:
        await ctx.send(gw2_messages.LONG_SEARCH)
        return

    len_eb_fields = 0
    wiki_url = gw2_variables.WIKI_URL
    search = search.replace(" ", "+")
    full_wiki_url = f"{wiki_url}/index.php?title=Special%3ASearch&search={search}&fulltext=Search"

    await ctx.message.channel.typing()
    async with ctx.bot.aiosession.get(full_wiki_url) as r:
        results = await r.text()
        soup = BeautifulSoup(results, 'html.parser')
        posts = soup.find_all("div", {"class": "mw-search-result-heading"})[:50]
        total_posts = len(posts)
        if not posts:
            await bot_utils.send_error_msg(ctx, gw2_messages.NO_RESULTS)
            return

        embed = discord.Embed(title=gw2_messages.WIKI_SEARCH_RESULTS, color=ctx.bot.settings["gw2"]["EmbedColor"])

        if total_posts > 0:
            i = 0

            # discord only supports 25 embed fields
            times_to_run = 25 if total_posts > 25 else total_posts

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
                                embed.add_field(name=post["title"], value=f"[{gw2_messages.CLICK_HERE}]({url})")
                                len_eb_fields += 1
                        elif "/history" not in post["title"]:
                            embed.add_field(name=post["title"], value=f"[{gw2_messages.CLICK_HERE}]({url})")
                            len_eb_fields += 1
                    i += 1
            except IndexError:
                pass

            embed.description = gw2_messages.DISPLAYIN_WIKI_SEARCH_TITLE.format(len(embed.fields), keyword.title())
        else:
            embed.add_field(name=gw2_messages.NO_RESULTS, value=f"[{gw2_messages.CLICK_HERE}]({full_wiki_url})")

        embed.set_thumbnail(url=gw2_variables.GW2_WIKI_ICON_URL)
        await bot_utils.send_embed(ctx, embed)


@GW2Misc.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Misc.value, BucketType.user)
async def info(ctx, *, skill):
    """ (Information about a given name/skill/rune)
            gw2 info info_to_search
    """

    await ctx.message.channel.typing()

    wiki_url = gw2_variables.WIKI_URL
    skill = skill.replace(" ", "_")
    skill_sanitized = str(re.escape(skill)).title()
    skill_sanitized = skill_sanitized.replace("Of", "of")
    skill_sanitized = skill_sanitized.replace("The", "the")
    full_wiki_url = f"{wiki_url}/wiki/{skill_sanitized}"

    async with ctx.bot.aiosession.get(full_wiki_url) as r:
        if r.status != 200:
            return await bot_utils.send_error_msg(ctx, gw2_messages.NO_RESULTS)

        skill_url = str(r.url)
        skill_name = str(r.url).split("/")[-1:][0].replace("_", " ")
        skill_icon_url = ""

        results = await r.text()
        soup = BeautifulSoup(results, 'html.parser')
        for br in soup.find_all("br"):
            br.replace_with("\n")

        for image in soup.findAll("img"):
            image_name = image.get("alt", "")
            if image_name.lower() == f"{skill_sanitized.replace('_', ' ').lower()}.png":
                try:
                    skill_icon_url = f"{wiki_url}{image['srcset'].split()[0]}"
                    break
                except KeyError:
                    pass

        skill_description = soup.find("blockquote")
        if skill_description is not None:
            skill_description = skill_description.get_text()[2:].split("—")[0]
            skill_description = skill_description.replace("?", "")
            color = ctx.bot.settings["gw2"]["EmbedColor"]

            myspans = soup.findAll("span", {"class": "gw2-tpprice"})
            if len(myspans) > 0:
                item_id = myspans[0]["data-id"]
            else:
                item_id = None

            if item_id is not None:
                gw2tp_url = f"https://www.gw2tp.com/item/{item_id}-{skill_sanitized.replace('_', '-').lower()}"
                async with ctx.bot.aiosession.get(gw2tp_url) as tp_r:
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
            skill_description = gw2_messages.CLICK_ON_LINK
            color = discord.Color.red()

        embed = discord.Embed(title=skill_name,
                              description=skill_description,
                              color=color,
                              url=skill_url)
        embed.set_thumbnail(url=skill_icon_url)
        embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
        await bot_utils.send_embed(ctx, embed)


# @GW2Misc.gw2.command()
# async def api_test(self, ctx):
#     from src.database.dal.gw2.gw2_key_sql import Gw2KeyDal
#     user_id = ctx.message.author.id
#     gw2Api = Gw2Client(self.bot)
#     gw2KeySql = Gw2KeyDal(self.bot.db_session, self.bot.log)
#     rs = await gw2KeySql.get_server_user_api_key(ctx.guild.id, user_id)
#     api_key = rs[0]["key"]
#     uri = "/wvw/matches/1-3"
#     api_req = await gw2Api.call_api(uri, api_key)
#     return api_req


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Misc(bot))
