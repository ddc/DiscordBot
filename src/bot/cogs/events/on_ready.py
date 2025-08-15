import sys
import discord
from discord.ext import commands
from src.bot.constants import messages, variables
from src.bot.tools import bot_utils


class StartupInfoDisplay:
    """Handles the display of bot startup information."""

    @staticmethod
    def print_startup_banner(version: str) -> None:
        """Print the startup banner."""
        separator = "=" * 20
        print(f"\n{separator}\nDiscord Bot v{version}\n{separator}")

    @staticmethod
    def print_version_info() -> None:
        """Print version information for Python and Discord API."""
        python_version = "Python v{}.{}.{}".format(*sys.version_info[:3])
        discord_version = f"Discord API v{discord.__version__}"
        print(python_version)
        print(discord_version)

    @staticmethod
    def print_bot_info(bot: commands.Bot) -> None:
        """Print bot-specific information."""
        print("--------------------")
        print(f"{bot.user} (id:{bot.user.id})")
        print(f"Prefix: {bot.command_prefix}")

    @staticmethod
    def print_bot_stats(stats: dict) -> None:
        """Print bot statistics."""
        print(f"Servers: {stats['servers']}")
        print(f"Users: {stats['users']}")
        print(f"Channels: {stats['channels']}")

    @staticmethod
    def print_timestamp() -> None:
        """Print current timestamp."""
        print("--------------------")
        print(f"{bot_utils.get_current_date_time_str_long()}")


class OnReady(commands.Cog):
    """Bot ready event handler with improved organization."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.info_display = StartupInfoDisplay()

        @self.bot.event
        async def on_ready() -> None:
            """Handle bot ready event with comprehensive startup information."""
            try:
                # Get bot statistics
                bot_stats = bot_utils.get_bot_stats(bot)

                # Display startup information
                self.info_display.print_startup_banner(variables.VERSION)
                self.info_display.print_version_info()
                self.info_display.print_bot_info(bot)
                self.info_display.print_bot_stats(bot_stats)
                self.info_display.print_timestamp()

                # Log bot online status
                bot.log.info(messages.BOT_ONLINE.format(bot.user))
            except Exception as e:
                # Display startup information even if stats fail
                self.info_display.print_startup_banner(variables.VERSION)
                self.info_display.print_version_info()
                self.info_display.print_bot_info(bot)
                self.info_display.print_timestamp()

                # Log error and bot online status
                bot.log.error(f"Failed to get bot stats during startup: {e}")
                bot.log.info(messages.BOT_ONLINE.format(bot.user))


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OnReady cog to the bot."""
    await bot.add_cog(OnReady(bot))
