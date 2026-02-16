import discord
import itertools
from discord.ext import commands


class HelpPaginatorView(discord.ui.View):
    """Interactive pagination view for help pages with Previous/Next buttons."""

    def __init__(self, pages: list[str], author_id: int):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = 0
        self.author_id = author_id
        self.message: discord.Message | None = None
        self._update_buttons()

    def _format_page(self) -> str:
        page_header = f"**Page {self.current_page + 1}/{len(self.pages)}**\n"
        return page_header + self.pages[self.current_page]

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
        await interaction.response.edit_message(content=self._format_page(), view=self)

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
        await interaction.response.edit_message(content=self._format_page(), view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.NotFound, discord.HTTPException:
            pass


class CustomHelpCommand(commands.DefaultHelpCommand):
    """Custom help command that sends DM notifications to the channel."""

    def __init__(self, **options):
        # Increase page size for bigger window
        options.setdefault("paginator", commands.Paginator(prefix="```", suffix="```", max_size=2000))
        super().__init__(**options)

    async def send_bot_help(self, mapping):
        """Override to add per-group subcommand pages after the overview page."""
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        no_category = f"\u200b{self.no_category}:"

        def get_category(command, *, _no_category=no_category):
            cog = command.cog
            return f"{cog.qualified_name}:" if cog is not None else _no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        groups = []
        for category, cmds in to_iterate:
            cmds = sorted(cmds, key=lambda c: c.name) if self.sort_commands else list(cmds)
            self.add_indented_commands(cmds, heading=category, max_size=max_size)
            for cmd in cmds:
                if isinstance(cmd, commands.Group):
                    groups.append(cmd)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        # Add a separate page for each group with its subcommands
        for group in groups:
            subcommands = await self.filter_commands(group.commands, sort=self.sort_commands)
            if subcommands:
                self.paginator.close_page()
                heading = f"{group.qualified_name} subcommands:"
                self.add_indented_commands(subcommands, heading=heading, max_size=self.get_max_size(subcommands))

        await self.send_pages()

    async def send_pages(self):
        """Override send_pages to send as paginated regular messages."""
        destination = self.get_destination()

        if not self.paginator.pages:
            await destination.send("No help available")
            return

        if self.dm_help and not isinstance(destination, discord.DMChannel):
            # Send pages to DM with pagination
            await self._send_pages_to_dm()

            # Show notification in channel with profile picture
            notification_embed = discord.Embed(description="📬 Response sent to your DM", color=discord.Color.green())
            notification_embed.set_author(
                name=self.context.author.display_name,
                icon_url=(
                    self.context.author.avatar.url
                    if self.context.author.avatar
                    else self.context.author.default_avatar.url
                ),
            )
            await self.context.send(embed=notification_embed)
        else:
            # Send pages to channel or DM
            await self._send_pages_to_destination(destination)

    async def _send_pages_to_dm(self):
        """Send help pages to user's DM with button pagination."""
        pages = self.paginator.pages
        if len(pages) == 1:
            await self.context.author.send(pages[0])
        else:
            view = HelpPaginatorView(pages, self.context.author.id)
            msg = await self.context.author.send(content=view._format_page(), view=view)
            view.message = msg

    async def _send_pages_to_destination(self, destination):
        """Send help pages to specified destination with button pagination."""
        pages = self.paginator.pages
        if len(pages) == 1:
            await destination.send(pages[0])
        else:
            view = HelpPaginatorView(pages, self.context.author.id)
            msg = await destination.send(content=view._format_page(), view=view)
            view.message = msg
