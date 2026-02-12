import discord
from discord.ext import commands


class CustomHelpCommand(commands.DefaultHelpCommand):
    """Custom help command that sends DM notifications to the channel."""

    def __init__(self, **options):
        # Increase page size for bigger window
        options.setdefault('paginator', commands.Paginator(prefix='```', suffix='```', max_size=2000))
        super().__init__(**options)

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
        """Send paginated messages to user's DM."""
        for page_num, page in enumerate(self.paginator.pages, 1):
            if len(self.paginator.pages) > 1:
                # Add page numbers for multiple pages
                page_header = f"**Page {page_num}/{len(self.paginator.pages)}**\n"
                content = page_header + page
            else:
                content = page
            await self.context.author.send(content)

    async def _send_pages_to_destination(self, destination):
        """Send paginated messages to specified destination."""
        for page_num, page in enumerate(self.paginator.pages, 1):
            if len(self.paginator.pages) > 1:
                # Add page numbers for multiple pages
                page_header = f"**Page {page_num}/{len(self.paginator.pages)}**\n"
                content = page_header + page
            else:
                content = page
            await destination.send(content)
