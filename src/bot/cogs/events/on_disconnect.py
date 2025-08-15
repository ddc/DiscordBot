from discord.ext import commands
from src.bot.constants import messages


class OnDisconnect(commands.Cog):
    """Handles bot disconnect events with proper logging."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the OnDisconnect cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

        @self.bot.event
        async def on_disconnect() -> None:
            """Handle bot disconnect event.

            Called when the client has disconnected from Discord,
            or a connection attempt to Discord has failed.
            This could happen through:
            - Internet disconnection
            - Explicit calls to close
            - Discord terminating the connection
            """
            try:
                bot.log.warning(
                    messages.BOT_DISCONNECTED.format(bot.user)
                    if hasattr(messages, 'BOT_DISCONNECTED')
                    else f"Bot {bot.user} disconnected from Discord"
                )
            except Exception as e:
                # Fallback logging in case of critical failure
                print(f"Bot disconnected - logging failed: {e}")


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OnDisconnect cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnDisconnect(bot))
