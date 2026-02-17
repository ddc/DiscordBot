import discord
from discord.ext import commands
from src.bot.tools import bot_utils, chat_formatting
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


class EmbedPaginatorView(discord.ui.View):
    """Interactive pagination view for embed pages with Previous/Next buttons."""

    def __init__(self, pages: list[discord.Embed], author_id: int):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = 0
        self.author_id = author_id
        self.message: discord.Message | None = None
        self._update_buttons()

    def _update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.page_indicator.label = f"{self.current_page + 1}/{len(self.pages)}"
        self.next_button.disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(label="\u25c0", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                "Only the command invoker can use these buttons.", ephemeral=True
            )
        self.current_page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="\u25b6", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                "Only the command invoker can use these buttons.", ephemeral=True
            )
        self.current_page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.NotFound, discord.HTTPException:
            pass


class GW2Worlds(GuildWars2):
    """Guild Wars 2 commands for listing worlds and WvW tiers."""

    def __init__(self, bot):
        super().__init__(bot)


@GW2Worlds.gw2.group()
async def worlds(ctx):
    """List all Guild Wars 2 worlds by region.

    Available subcommands:
        gw2 worlds na - List all NA worlds with WvW tier
        gw2 worlds eu - List all EU worlds with WvW tier
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 worlds")


@worlds.command(name="na")
@commands.cooldown(1, GW2CoolDowns.Worlds.seconds, commands.BucketType.user)
async def worlds_na(ctx):
    """List all North American worlds with WvW tier and population.

    Usage:
        gw2 worlds na
    """

    result, worlds_ids = await gw2_utils.get_worlds_ids(ctx)
    if not result:
        return None

    gw2_api = Gw2Client(ctx.bot)
    embed_na = discord.Embed(description=chat_formatting.inline(gw2_messages.NA_SERVERS_TITLE))

    failed_worlds = []

    for world in worlds_ids:
        wid = world["id"]
        try:
            await ctx.message.channel.typing()
            matches = await gw2_api.call_api(f"wvw/matches?world={wid}")
            if wid < 2001:
                tier_number = matches["id"].replace("1-", "")
                embed_na.add_field(
                    name=world["name"],
                    value=chat_formatting.inline(f"T{tier_number} {world['population']}"),
                )
        except Exception as e:
            # Log the error but continue with other worlds
            failed_worlds.append(f"{world['name']} (ID: {wid})")
            ctx.bot.log.warning(f"Failed to fetch WvW data for world {world['name']} (ID: {wid}): {e}")
            continue

    # Add footer if some worlds failed
    if failed_worlds:
        embed_na.set_footer(
            text=f"⚠️ Failed to load: {', '.join(failed_worlds[:3])}" + ("..." if len(failed_worlds) > 3 else "")
        )

    await _send_paginated_worlds_embed(ctx, embed_na)
    return None


@worlds.command(name="eu")
@commands.cooldown(1, GW2CoolDowns.Worlds.seconds, commands.BucketType.user)
async def worlds_eu(ctx):
    """List all European worlds with WvW tier and population.

    Usage:
        gw2 worlds eu
    """

    result, worlds_ids = await gw2_utils.get_worlds_ids(ctx)
    if not result:
        return None

    gw2_api = Gw2Client(ctx.bot)
    embed_eu = discord.Embed(description=chat_formatting.inline(gw2_messages.EU_SERVERS_TITLE))

    failed_worlds = []

    for world in worlds_ids:
        wid = world["id"]
        try:
            await ctx.message.channel.typing()
            matches = await gw2_api.call_api(f"wvw/matches?world={wid}")
            if wid > 2001:
                tier_number = matches["id"].replace("2-", "")
                embed_eu.add_field(
                    name=world["name"],
                    value=chat_formatting.inline(f"T{tier_number} {world['population']}"),
                )
        except Exception as e:
            # Log the error but continue with other worlds
            failed_worlds.append(f"{world['name']} (ID: {wid})")
            ctx.bot.log.warning(f"Failed to fetch WvW data for world {world['name']} (ID: {wid}): {e}")
            continue

    # Add footer if some worlds failed
    if failed_worlds:
        embed_eu.set_footer(
            text=f"⚠️ Failed to load: {', '.join(failed_worlds[:3])}" + ("..." if len(failed_worlds) > 3 else "")
        )

    await _send_paginated_worlds_embed(ctx, embed_eu)
    return None


async def _send_paginated_worlds_embed(ctx, embed):
    """
    Send worlds with pagination using buttons for navigation
    """
    max_fields = 25
    color = ctx.bot.settings["gw2"]["EmbedColor"]

    if len(embed.fields) <= max_fields:
        # No pagination needed
        embed.color = color
        await ctx.send(embed=embed)
        return

    # Split fields into pages
    pages = []
    total_fields = len(embed.fields)

    for i in range(0, total_fields, max_fields):
        page_embed = discord.Embed(color=color, description=embed.description)
        page_fields = embed.fields[i : i + max_fields]

        for field in page_fields:
            page_embed.add_field(name=field.name, value=field.value)

        page_number = (i // max_fields) + 1
        total_pages = (total_fields + max_fields - 1) // max_fields
        page_embed.set_footer(text=f"Page {page_number}/{total_pages}")
        pages.append(page_embed)

    if len(pages) == 1:
        await ctx.send(embed=pages[0])
        return

    view = EmbedPaginatorView(pages, ctx.author.id)
    msg = await ctx.send(embed=pages[0], view=view)
    view.message = msg


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Worlds(bot))
