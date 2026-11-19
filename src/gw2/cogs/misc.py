import discord
import re
from discord.ext import commands
from src.bot.tools import bot_utils
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages, gw2_variables
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns
lazy from bs4 import BeautifulSoup

HTML_PARSER = "html.parser"
MAX_EMBED_FIELDS = 25  # Discord limit per embed


class GW2Misc(GuildWars2):
    """Guild Wars 2 miscellaneous commands for wiki search and item info."""

    def __init__(self, bot):
        super().__init__(bot)


def _add_wiki_results(embed: discord.Embed, posts, wiki_url: str, keyword: str) -> None:
    """Add one field per matching search result, skipping history pages and the exact-keyword duplicate."""
    for post in posts:
        if len(embed.fields) >= MAX_EMBED_FIELDS:
            break
        link = post.a
        title = str(link["title"])
        if keyword not in title.lower() or "/history" in title:
            continue
        if any(field.name == keyword.title() for field in embed.fields):
            continue
        url = (wiki_url + link["href"]).replace(")", "\\)")
        embed.add_field(name=link["title"], value=f"[{gw2_messages.Misc.CLICK_HERE}]({url})")


@GW2Misc.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Misc.seconds, commands.BucketType.user)
async def wiki(ctx, *, search):
    """Search the Guild Wars 2 wiki.

    Usage:
        gw2 wiki elementalist
        gw2 wiki ascended armor
    """

    if len(search) > 300:
        await ctx.send(gw2_messages.Misc.LONG_SEARCH)
        return

    wiki_url = gw2_variables.WIKI_URL
    search = search.replace(" ", "+")
    keyword = search.lower().replace("+", " ")
    full_wiki_url = f"{wiki_url}/index.php?title=Special%3ASearch&search={search}&fulltext=Search"

    await ctx.message.channel.typing()
    async with ctx.bot.aiosession.get(full_wiki_url) as r:
        results = await r.text()
        soup = BeautifulSoup(results, HTML_PARSER)
        posts = soup.find_all("div", {"class": "mw-search-result-heading"})[:50]
        if not posts:
            await bot_utils.send_error_msg(ctx, gw2_messages.Misc.NO_RESULTS)
            return

        embed = discord.Embed(title=gw2_messages.Misc.WIKI_SEARCH_RESULTS, color=ctx.bot.settings["gw2"]["EmbedColor"])
        _add_wiki_results(embed, posts, wiki_url, keyword)
        embed.description = gw2_messages.Misc.wiki_search_title(len(embed.fields), keyword.title())
        embed.set_thumbnail(url=gw2_variables.GW2_WIKI_ICON_URL)
        await bot_utils.send_embed(ctx, embed)


def _find_skill_icon_url(soup: BeautifulSoup, wiki_url: str, skill_sanitized: str) -> str:
    expected_alt = f"{skill_sanitized.replace('_', ' ').lower()}.png"
    for image in soup.find_all("img"):
        if image.get("alt", "").lower() == expected_alt and "srcset" in image.attrs:
            return f"{wiki_url}{image['srcset'].split()[0]}"
    return ""


async def _get_trading_post_text(ctx, soup: BeautifulSoup, skill_sanitized: str) -> str | None:
    """Return the Trading Post block for the item on this wiki page, or None when it has no TP price."""
    tp_spans = soup.find_all("span", {"class": "gw2-tpprice"})
    if not tp_spans:
        return None

    item_id = tp_spans[0]["data-id"]
    slug = skill_sanitized.replace("_", "-").lower()
    gw2tp_url = f"{gw2_variables.GW2TP_ITEM_URL}/{item_id}-{slug}"
    async with ctx.bot.aiosession.get(gw2tp_url) as tp_r:
        if tp_r.status != 200:
            return None
        gw2bltc_url = f"{gw2_variables.GW2BLTC_ITEM_URL}/{item_id}-{slug}"
        tp_soup = BeautifulSoup(await tp_r.text(), HTML_PARSER)
        tp_sell_price = gw2_utils.format_gold(tp_soup.find_all("td", {"id": "sell-price"})[0]["data-price"])
        tp_buy_price = gw2_utils.format_gold(tp_soup.find_all("td", {"id": "buy-price"})[0]["data-price"])
        return (
            "**Trading Post:**\n"
            f"Sell: *{tp_sell_price}*\n"
            f"Buy: *{tp_buy_price}*\n"
            f"[Gw2tp]({gw2tp_url}) / [Gw2bltc]({gw2bltc_url})"
        )


@GW2Misc.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Misc.seconds, commands.BucketType.user)
async def info(ctx, *, skill):
    """Display information about a given name, skill, or rune.

    Shows wiki description and Trading Post prices when available.

    Usage:
        gw2 info Eternity
        gw2 info Superior Rune of the Scholar
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
            return await bot_utils.send_error_msg(ctx, gw2_messages.Misc.NO_RESULTS)

        skill_url = str(r.url)
        skill_name = str(r.url).split("/")[-1:][0].replace("_", " ")

        soup = BeautifulSoup(await r.text(), HTML_PARSER)
        for br in soup.find_all("br"):
            br.replace_with("\n")

        skill_icon_url = _find_skill_icon_url(soup, wiki_url, skill_sanitized)

        blockquote = soup.find("blockquote")
        if blockquote is not None:
            skill_description = blockquote.get_text()[2:].split("—")[0].replace("?", "")
            color = ctx.bot.settings["gw2"]["EmbedColor"]
            tp_text = await _get_trading_post_text(ctx, soup, skill_sanitized)
            if tp_text:
                skill_description = f"{skill_description}\n{tp_text}"
        else:
            skill_description = gw2_messages.Misc.CLICK_ON_LINK
            color = discord.Color.red()

        embed = discord.Embed(title=skill_name, description=skill_description, color=color, url=skill_url)
        embed.set_thumbnail(url=skill_icon_url)
        embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.display_avatar.url)
        await bot_utils.send_embed(ctx, embed)
        return None


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Misc(bot))
