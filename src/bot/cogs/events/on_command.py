"""Bot command execution event handler with logging and monitoring."""

from discord.ext import commands


class CommandLogger:
    """Handles command execution logging and monitoring."""

    def __init__(self, bot: commands.Bot):
        """Initialize the command logger.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

    def log_command_execution(self, ctx: commands.Context) -> None:
        """Log command execution details.

        Args:
            ctx: The command context
        """
        try:
            if ctx.guild:
                self.bot.log.info(
                    f"Command executed: '{ctx.command}' by {ctx.author} in {ctx.guild.name}#{ctx.channel.name}"
                )
            else:
                self.bot.log.info(f"DM Command executed: '{ctx.command}' by {ctx.author}")
        except Exception as e:
            self.bot.log.error(f"Failed to log command execution: {e}")


class OnCommand(commands.Cog):
    """Handles command execution events with logging and monitoring."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the OnCommand cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.command_logger = CommandLogger(bot)

        @self.bot.event
        async def on_command(ctx: commands.Context) -> None:
            """Handle command execution event.

            Called when a valid command gets executed successfully.
            This is useful for logging command usage and monitoring.

            Args:
                ctx: The command context containing information about the command execution
            """
            try:
                # Log command execution for monitoring purposes
                self.command_logger.log_command_execution(ctx)
                # Future: Add command usage statistics, rate limiting, etc.
            except Exception as e:
                self.bot.log.error(f"Error in on_command event: {e}")


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OnCommand cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnCommand(bot))
