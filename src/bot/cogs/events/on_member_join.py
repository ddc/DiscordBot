import discord
from discord.ext import commands
from src.bot.constants import messages
from src.bot.tools import bot_utils
from src.database.dal.bot.servers_dal import ServersDal


class WelcomeMessageBuilder:
    """Handles creation of welcome messages and embeds for new members."""

    def __init__(self, bot: commands.Bot):
        """Initialize the welcome message builder.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

    def create_join_embed(self, member: discord.Member) -> discord.Embed:
        """Create a welcome embed for a new member.

        Args:
            member: The Discord member who joined

        Returns:
            discord.Embed: The formatted welcome embed
        """
        try:
            now = bot_utils.get_current_date_time_str_long()

            embed = discord.Embed(color=discord.Color.green(), description=str(member))

            # Set member avatar as thumbnail
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)

            embed.set_author(name=messages.JOINED_THE_SERVER)
            embed.set_footer(icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None, text=f"{now} UTC")

            return embed
        except Exception as e:
            self.bot.log.error(f"Failed to create join embed for {member}: {e}")
            # Return a basic embed as fallback
            return discord.Embed(color=discord.Color.green(), description=f"{member} joined the server!")

    def create_join_message(self, member: discord.Member) -> str:
        """Create a plain text welcome message for a new member.

        Args:
            member: The Discord member who joined

        Returns:
            str: The formatted welcome message
        """
        try:
            now = bot_utils.get_current_date_time_str_long()
            return f"{member.name} {messages.JOINED_THE_SERVER}\n{now}"
        except Exception as e:
            self.bot.log.error(f"Failed to create join message for {member}: {e}")
            return f"{member.name} joined the server!"


class MemberJoinHandler:
    """Handles member join processing and server configuration checks."""

    def __init__(self, bot: commands.Bot):
        """Initialize the member join handler.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.message_builder = WelcomeMessageBuilder(bot)

    async def process_member_join(self, member: discord.Member) -> None:
        """Process a member join event with proper error handling.

        Args:
            member: The Discord member who joined
        """
        try:
            # Get server configuration
            servers_dal = ServersDal(self.bot.db_session, self.bot.log)
            server_config = await servers_dal.get_server(member.guild.id)

            if not server_config:
                self.bot.log.warning(f"No server config found for guild: {member.guild.name}")
                return

            # Check if join messages are enabled
            if not server_config.get("msg_on_join", False):
                return

            await self._send_welcome_message(member)
        except Exception as e:
            self.bot.log.error(f"Error processing member join for {member} in {member.guild.name}: {e}")

    async def _send_welcome_message(self, member: discord.Member) -> None:
        """Send welcome message to system channel.

        Args:
            member: The Discord member who joined
        """
        try:
            embed = self.message_builder.create_join_embed(member)
            message = self.message_builder.create_join_message(member)

            await bot_utils.send_msg_to_system_channel(self.bot.log, member.guild, embed, message)

            self.bot.log.info(f"Welcome message sent for {member} in {member.guild.name}")
        except Exception as e:
            self.bot.log.error(f"Failed to send welcome message for {member}: {e}")


class OnMemberJoin(commands.Cog):
    """Handles member join events with welcome messages and logging."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the OnMemberJoin cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.join_handler = MemberJoinHandler(bot)

        @self.bot.event
        async def on_member_join(member: discord.Member) -> None:
            """Handle member join event.

            Called when a member joins a guild where the bot is present.
            Sends welcome messages if configured to do so.

            Args:
                member: The Discord member who joined the guild
            """
            try:
                self.bot.log.info(f"Member joined: {member} in guild: {member.guild.name}")
                await self.join_handler.process_member_join(member)
            except Exception as e:
                self.bot.log.error(f"Critical error in on_member_join for {member}: {e}")


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OnMemberJoin cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnMemberJoin(bot))
