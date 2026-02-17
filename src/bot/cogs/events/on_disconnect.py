from discord.ext import commands
from src.bot.constants import messages
from src.bot.discord_bot import Bot


class OnDisconnect(commands.Cog):
    """Handles bot disconnect events with proper logging."""

    def __init__(self, bot: Bot) -> None:
        """Initialize the OnDisconnect cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        """Handle bot disconnect event.

        Called when the client has disconnected from Discord,
        or a connection attempt to Discord has failed.
        This could happen through:
        - Internet disconnection
        - Explicit calls to close
        - Discord terminating the connection
        """
        try:
            self.bot.log.warning(messages.bot_disconnected(self.bot.user))
        except Exception as e:
            # Fallback logging in case of critical failure
            print(f"Bot disconnected - logging failed: {e}")


async def setup(bot: Bot) -> None:
    """Setup function to add the OnDisconnect cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnDisconnect(bot))
