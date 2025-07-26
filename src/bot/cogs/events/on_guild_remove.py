"""Bot guild removal event handler with database cleanup."""

import discord
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal


class GuildCleanupHandler:
    """Handles guild-related cleanup operations when bot is removed from servers."""

    def __init__(self, bot: commands.Bot):
        """Initialize the guild cleanup handler.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

    async def cleanup_server_data(self, guild: discord.Guild) -> bool:
        """Clean up server data from database.

        Args:
            guild: The Discord guild that was removed

        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        try:
            servers_dal = ServersDal(self.bot.db_session, self.bot.log)
            await servers_dal.delete_server(guild.id)

            self.bot.log.info(f"Successfully cleaned up data for guild: {guild.name} (ID: {guild.id})")
            return True
        except Exception as e:
            self.bot.log.error(f"Failed to cleanup data for guild {guild.name} (ID: {guild.id}): {e}")
            return False


class OnGuildRemove(commands.Cog):
    """Handles guild removal events with proper cleanup and logging."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the OnGuildRemove cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.cleanup_handler = GuildCleanupHandler(bot)

        @self.bot.event
        async def on_guild_remove(guild: discord.Guild) -> None:
            """Handle guild removal event.

            Called when the bot is removed from a guild (server).
            This includes being kicked, banned, or the server being deleted.

            Args:
                guild: The Discord guild the bot was removed from
            """
            try:
                self.bot.log.info(f"Bot removed from guild: {guild.name} (ID: {guild.id})")

                # Clean up server data from database
                cleanup_success = await self.cleanup_handler.cleanup_server_data(guild)

                if not cleanup_success:
                    self.bot.log.warning(f"Database cleanup may be incomplete for guild: {guild.name}")
            except Exception as e:
                self.bot.log.error(f"Error handling guild removal for {guild.name}: {e}")


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OnGuildRemove cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnGuildRemove(bot))
