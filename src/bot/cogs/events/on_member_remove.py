import discord
from discord.ext import commands
from src.bot.constants import messages
from src.bot.tools import bot_utils
from src.database.dal.bot.servers_dal import ServersDal


class FarewellMessageBuilder:
    """Handles creation of farewell messages and embeds for members who leave."""

    def __init__(self, bot: commands.Bot):
        """Initialize the farewell message builder.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

    def create_leave_embed(self, member: discord.Member) -> discord.Embed:
        """Create a farewell embed for a member who left.

        Args:
            member: The Discord member who left

        Returns:
            discord.Embed: The formatted farewell embed
        """
        try:
            now = bot_utils.get_current_date_time_str_long()

            embed = discord.Embed(color=discord.Color.red(), description=str(member))

            # Set member avatar as thumbnail
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)

            embed.set_author(name=messages.LEFT_THE_SERVER)
            embed.set_footer(icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None, text=f"{now} UTC")

            return embed
        except Exception as e:
            self.bot.log.error(f"Failed to create leave embed for {member}: {e}")
            # Return a basic embed as fallback
            return discord.Embed(color=discord.Color.red(), description=f"{member} left the server!")

    def create_leave_message(self, member: discord.Member) -> str:
        """Create a plain text farewell message for a member who left.

        Args:
            member: The Discord member who left

        Returns:
            str: The formatted farewell message
        """
        try:
            now = bot_utils.get_current_date_time_str_long()
            return f"{member.name} {messages.LEFT_THE_SERVER}\n{now}"
        except Exception as e:
            self.bot.log.error(f"Failed to create leave message for {member}: {e}")
            return f"{member.name} left the server!"


class MemberLeaveHandler:
    """Handles member leave processing and server configuration checks."""

    def __init__(self, bot: commands.Bot):
        """Initialize the member leave handler.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.message_builder = FarewellMessageBuilder(bot)

    async def process_member_leave(self, member: discord.Member) -> None:
        """Process a member leave event with proper error handling.

        Args:
            member: The Discord member who left
        """
        try:
            # Skip if the bot itself left (should not happen in this event)
            if self.bot.user.id == member.id:
                return

            # Get server configuration
            servers_dal = ServersDal(self.bot.db_session, self.bot.log)
            server_config = await servers_dal.get_server(member.guild.id)

            if not server_config:
                self.bot.log.warning(f"No server config found for guild: {member.guild.name}")
                return

            # Check if leave messages are enabled
            if not server_config.get("msg_on_leave", False):
                return

            await self._send_farewell_message(member)
        except Exception as e:
            self.bot.log.error(f"Error processing member leave for {member} in {member.guild.name}: {e}")

    async def _send_farewell_message(self, member: discord.Member) -> None:
        """Send a farewell message to system channel.

        Args:
            member: The Discord member who left
        """
        try:
            embed = self.message_builder.create_leave_embed(member)
            message = self.message_builder.create_leave_message(member)

            await bot_utils.send_msg_to_system_channel(self.bot.log, member.guild, embed, message)

            self.bot.log.info(f"Farewell message sent for {member} in {member.guild.name}")
        except Exception as e:
            self.bot.log.error(f"Failed to send farewell message for {member}: {e}")


class OnMemberRemove(commands.Cog):
    """Handles member leave events with farewell messages and logging."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the OnMemberRemove cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.leave_handler = MemberLeaveHandler(bot)

        @self.bot.event
        async def on_member_remove(member: discord.Member) -> None:
            """Handle member remove event.

            Called when a member leaves a guild where the bot is present.
            This includes being kicked, banned, or leaving voluntarily.
            Sends farewell messages if configured to do so.

            Args:
                member: The Discord member who left the guild
            """
            try:
                self.bot.log.info(f"Member left: {member} from guild: {member.guild.name}")
                await self.leave_handler.process_member_leave(member)
            except Exception as e:
                self.bot.log.error(f"Critical error in on_member_remove for {member}: {e}")


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OnMemberRemove cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnMemberRemove(bot))
