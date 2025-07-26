"""Bot guild update event handler with server change tracking."""

import discord
from discord.ext import commands
from src.bot.constants import messages
from src.bot.tools import bot_utils
from src.database.dal.bot.servers_dal import ServersDal


class OnGuildUpdate(commands.Cog):
    """Handles guild update events with server change tracking."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the OnGuildUpdate cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

        @self.bot.event
        async def on_guild_update(before: discord.Guild, after: discord.Guild) -> None:
            """Handle guild update event.

            Called when a guild is updated (name, icon, owner changes, etc.).

            Args:
                before: The guild before the update
                after: The guild after the update
            """
            try:
                msg = f"{messages.NEW_SERVER_SETTINGS}\n"
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

                # Check for icon changes
                if str(before.icon.url) != str(after.icon.url):
                    if after.icon:
                        embed.set_thumbnail(url=after.icon.url)
                    embed.add_field(name=messages.NEW_SERVER_ICON, value="")
                    msg += f"{messages.NEW_SERVER_ICON}: \n{after.icon.url if after.icon else 'None'}\n"

                # Check for name changes
                if str(before.name) != str(after.name):
                    if before.name is not None:
                        embed.add_field(name=messages.PREVIOUS_NAME, value=str(before.name))
                    embed.add_field(name=messages.NEW_SERVER_NAME, value=str(after.name))
                    msg += f"{messages.NEW_SERVER_NAME}: `{after.name}`\n"

                # Check for owner changes
                if str(before.owner_id) != str(after.owner_id):
                    if after.icon:
                        embed.set_thumbnail(url=after.icon.url)
                    if before.owner_id is not None:
                        embed.add_field(name=messages.PREVIOUS_SERVER_OWNER, value=str(before.owner))
                    embed.add_field(name=messages.NEW_SERVER_OWNER, value=str(after.owner))
                    msg += f"{messages.NEW_SERVER_OWNER}: `{after.owner}`\n"

                # Send update message if there were changes and it's enabled
                if len(embed.fields) > 0:
                    try:
                        servers_dal = ServersDal(self.bot.db_session, self.bot.log)
                        server_config = await servers_dal.get_server(after.id)
                        if server_config and server_config.get("msg_on_server_update", False):
                            await bot_utils.send_msg_to_system_channel(self.bot.log, after, embed, msg)
                            self.bot.log.info(f"Guild update notification sent for {after.name}")
                    except Exception as e:
                        self.bot.log.error(f"Failed to send guild update notification: {e}")
            except Exception as e:
                self.bot.log.error(f"Error in on_guild_update for {after.name}: {e}")


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OnGuildUpdate cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnGuildUpdate(bot))
