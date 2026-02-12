from discord.ext import commands
from src.bot.discord_bot import Bot


class CommandLogger:
    """Handles command execution logging and monitoring."""

    def __init__(self, bot: Bot):
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
            # Get the full command string including subcommands and arguments
            command_parts = [ctx.command.name] if ctx.command else []

            # Add subcommand if it exists
            if ctx.invoked_subcommand:
                command_parts.append(ctx.invoked_subcommand.name)

            # Get the full message content after the prefix to include arguments
            if ctx.prefix and ctx.message.content.startswith(ctx.prefix):
                full_command = ctx.message.content[len(ctx.prefix) :]
            else:
                full_command = " ".join(command_parts)

            if ctx.guild:
                self.bot.log.info(
                    f"Command executed in '{ctx.guild.name}#{ctx.channel.name}' by {ctx.author}: {full_command}"
                )
            else:
                self.bot.log.info(f"DM Command executed by {ctx.author}: {full_command}")
        except Exception as e:
            self.bot.log.error(f"Failed to log command execution: {e}")


class OnCommand(commands.Cog):
    """Handles command execution events with logging and monitoring."""

    def __init__(self, bot: Bot) -> None:
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


async def setup(bot: Bot) -> None:
    """Setup function to add the OnCommand cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnCommand(bot))
