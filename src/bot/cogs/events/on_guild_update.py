import discord
from discord.ext import commands
from src.bot.constants import messages
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils
from src.database.dal.bot.servers_dal import ServersDal


class OnGuildUpdate(commands.Cog):
    """Handles guild update events with server change tracking."""

    def __init__(self, bot: Bot) -> None:
        """Initialize the OnGuildUpdate cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        """Handle guild update event.

        Called when a guild is updated (name, icon, owner changes, etc.).

        Args:
            before: The guild before the update
            after: The guild after the update
        """
        try:
            embed, msg = self._create_base_embed()

            # Check for changes and update embed/message
            self._handle_icon_changes(before, after, embed, msg)
            self._handle_name_changes(before, after, embed, msg)
            self._handle_owner_changes(before, after, embed, msg)

            # Send notification if changes were detected
            await self._send_notification_if_enabled(after, embed, msg)

        except Exception as e:
            self.bot.log.error(f"Error in on_guild_update for {after.name}: {e}")

    def _create_base_embed(self):
        """Create the base embed and message for guild updates."""
        msg = [f"{messages.NEW_SERVER_SETTINGS}\n"]

        # Create a simple context-like object for get_embed
        class SimpleContext:
            def __init__(self, bot):
                self.bot = bot

        ctx = SimpleContext(self.bot)
        embed = bot_utils.get_embed(ctx)
        embed.set_footer(
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None,
            text=f"{bot_utils.get_current_date_time_str_long()} UTC",
        )
        return embed, msg

    def _handle_icon_changes(self, before, after, embed, msg):
        """Handle guild icon changes."""
        if str(before.icon.url) != str(after.icon.url):
            self._set_thumbnail_if_icon_exists(after, embed)
            embed.add_field(name=messages.NEW_SERVER_ICON, value="")
            icon_url = after.icon.url if after.icon else 'None'
            msg.append(f"{messages.NEW_SERVER_ICON}: \n{icon_url}\n")

    @staticmethod
    def _handle_name_changes(before, after, embed, msg):
        """Handle guild name changes."""
        if str(before.name) != str(after.name):
            if before.name is not None:
                embed.add_field(name=messages.PREVIOUS_NAME, value=str(before.name))
            embed.add_field(name=messages.NEW_SERVER_NAME, value=str(after.name))
            msg.append(f"{messages.NEW_SERVER_NAME}: `{after.name}`\n")

    def _handle_owner_changes(self, before, after, embed, msg):
        """Handle guild owner changes."""
        if str(before.owner_id) != str(after.owner_id):
            self._set_thumbnail_if_icon_exists(after, embed)
            if before.owner_id is not None:
                embed.add_field(name=messages.PREVIOUS_SERVER_OWNER, value=str(before.owner))
            embed.add_field(name=messages.NEW_SERVER_OWNER, value=str(after.owner))
            msg.append(f"{messages.NEW_SERVER_OWNER}: `{after.owner}`\n")

    @staticmethod
    def _set_thumbnail_if_icon_exists(guild, embed):
        """Set embed thumbnail if guild has an icon."""
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

    async def _send_notification_if_enabled(self, guild, embed, msg):
        """Send notification if changes were detected and notifications are enabled."""
        if len(embed.fields) == 0:
            return

        try:
            servers_dal = ServersDal(self.bot.db_session, self.bot.log)
            server_config = await servers_dal.get_server(guild.id)

            if not (server_config and server_config.get("msg_on_server_update", False)):
                return

            await bot_utils.send_msg_to_system_channel(self.bot.log, guild, embed, "".join(msg))
            self.bot.log.info(f"Guild update notification sent for {guild.name}")

        except Exception as e:
            self.bot.log.error(f"Failed to send guild update notification: {e}")


async def setup(bot: Bot) -> None:
    """Setup function to add the OnGuildUpdate cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnGuildUpdate(bot))
