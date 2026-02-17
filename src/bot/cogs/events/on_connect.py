from discord.ext import commands
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils
from src.database.dal.bot.servers_dal import ServersDal


class GuildSynchronizer:
    """Handles synchronization of guilds between Discord and the database."""

    def __init__(self, bot: Bot):
        """Initialize the guild synchronizer.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

    async def sync_guilds_with_database(self) -> None:
        """Synchronize guilds between Discord and database.

        Checks for any guilds the bot is in that are missing from the database
        and adds them. This ensures database consistency on bot connection.
        """
        try:
            # Get existing server IDs from database
            db_server_ids = await self._get_database_server_ids()

            # Get current guild IDs from Discord
            discord_guild_ids = await self._get_discord_guild_ids()

            # Find missing guilds and add them
            missing_guild_ids = discord_guild_ids - db_server_ids

            if missing_guild_ids:
                await self._add_missing_guilds(missing_guild_ids)
                self.bot.log.info(f"Added {len(missing_guild_ids)} missing guilds to database")
            else:
                self.bot.log.info("All guilds are already synchronized with database")
        except Exception as e:
            self.bot.log.error(f"Failed to synchronize guilds with database: {e}")

    async def _get_database_server_ids(self) -> set[int]:
        """Get server IDs from the database.

        Returns:
            Set[int]: Set of server IDs from the database
        """
        try:
            servers_dal = ServersDal(self.bot.db_session, self.bot.log)
            db_servers = await servers_dal.get_server()

            if not db_servers:
                return set()

            return {server["id"] for server in db_servers}
        except Exception as e:
            self.bot.log.error(f"Failed to get database server IDs: {e}")
            return set()

    async def _get_discord_guild_ids(self) -> set[int]:
        """Get guild IDs from Discord.

        Returns:
            Set[int]: Set of guild IDs from Discord
        """
        guild_ids = set()

        try:
            async for guild in self.bot.fetch_guilds(limit=None):
                guild_ids.add(guild.id)
        except Exception as e:
            self.bot.log.error(f"Failed to fetch guild IDs from Discord: {e}")

        return guild_ids

    async def _add_missing_guilds(self, missing_guild_ids: set[int]) -> None:
        """Add missing guilds to the database.

        Args:
            missing_guild_ids: Set of guild IDs that need to be added to the database
        """
        for guild_id in missing_guild_ids:
            try:
                guild = self.bot.get_guild(guild_id)
                if guild:
                    await bot_utils.insert_server(self.bot, guild)
                    self.bot.log.info(f"Added guild to database: {guild.name} (ID: {guild.id})")
                else:
                    self.bot.log.warning(f"Could not fetch guild with ID: {guild_id}")
            except Exception as e:
                self.bot.log.error(f"Failed to add guild {guild_id} to database: {e}")


class ConnectionHandler:
    """Handles bot connection processing and initialization tasks."""

    def __init__(self, bot: Bot):
        """Initialize the connection handler.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.guild_synchronizer = GuildSynchronizer(bot)

    async def process_connection(self) -> None:
        """Process bot connection with all necessary initialization tasks.

        This includes:
        - Logging connection status
        - Synchronizing guilds with database
        - Any other connection-related setup
        """
        try:
            self.bot.log.info("Bot connected to Discord - starting initialization tasks")

            # Synchronize guilds with database
            await self.guild_synchronizer.sync_guilds_with_database()

            self.bot.log.info("Bot connection initialization completed successfully")
        except Exception as e:
            self.bot.log.error(f"Error during connection processing: {e}")


class OnConnect(commands.Cog):
    """Handles bot connection events with database synchronization."""

    def __init__(self, bot: Bot) -> None:
        """Initialize the OnConnect cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        self.connection_handler = ConnectionHandler(bot)

    @commands.Cog.listener()
    async def on_connect(self) -> None:
        """Handle bot connection event.

        Called when the client has successfully connected to Discord.
        This is not the same as the client being fully prepared (see on_ready for that).

        This event handles:
        - Database synchronization
        - Guild verification
        - Connection logging
        """
        try:
            await self.connection_handler.process_connection()
        except Exception as e:
            self.bot.log.error(f"Critical error in on_connect event: {e}")


async def setup(bot: Bot) -> None:
    """Setup function to add the OnConnect cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnConnect(bot))
