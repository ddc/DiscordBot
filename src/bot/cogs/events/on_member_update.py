"""Bot member update event handler with profile change tracking."""

import discord
from discord.ext import commands
from src.bot.constants import messages
from src.bot.tools import bot_utils
from src.database.dal.bot.servers_dal import ServersDal


class OnMemberUpdate(commands.Cog):
    """Handles member update events with profile change tracking."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the OnMemberUpdate cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

        @self.bot.event
        async def on_member_update(before: discord.Member, after: discord.Member) -> None:
            """Handle member update event.

            Called when a Member updates their profile.
            This includes changes to:
            - nickname
            - roles
            - pending status
            - flags

            Args:
                before: The member before the update
                after: The member after the update
            """
            try:
                # Skip bot members
                if after.bot:
                    return

                msg = f"{messages.PROFILE_CHANGES}:\n\n"
                # Create a simple context-like object for get_embed
                class SimpleContext:
                    def __init__(self, bot):
                        self.bot = bot
                
                ctx = SimpleContext(self.bot)
                embed = bot_utils.get_embed(ctx)

                # Set member info with null checks
                if after.avatar:
                    embed.set_author(name=after.display_name, icon_url=after.avatar.url)
                else:
                    embed.set_author(name=after.display_name)

                embed.set_footer(
                    icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None,
                    text=f"{bot_utils.get_current_date_time_str_long()} UTC",
                )

                # Check for nickname changes
                if before.nick != after.nick:
                    if before.nick is not None:
                        embed.add_field(name=messages.PREVIOUS_NICKNAME, value=str(before.nick))
                    embed.add_field(name=messages.NEW_NICKNAME, value=str(after.nick))
                    msg += f"{messages.NEW_NICKNAME}: `{after.nick}`\n"

                # Check for role changes
                if before.roles != after.roles:
                    if before.roles is not None:
                        embed.add_field(
                            name=messages.PREVIOUS_ROLES,
                            value=", ".join([role.name for role in before.roles]),
                        )
                    embed.add_field(name=messages.NEW_ROLES, value=", ".join([role.name for role in after.roles]))
                    msg += f"{messages.NEW_ROLES}: `{', '.join([role.name for role in after.roles])}`\n"

                # Send update message if there were changes and it's enabled
                if len(embed.fields) > 0:
                    try:
                        servers_dal = ServersDal(self.bot.db_session, self.bot.log)
                        server_config = await servers_dal.get_server(after.guild.id)

                        if server_config and server_config.get("msg_on_member_update", False):
                            await bot_utils.send_msg_to_system_channel(self.bot.log, after.guild, embed, msg)
                            self.bot.log.info(f"Member update notification sent for {after} in {after.guild.name}")
                    except Exception as e:
                        self.bot.log.error(f"Failed to send member update notification: {e}")
            except Exception as e:
                self.bot.log.error(f"Error in on_member_update for {after}: {e}")


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OnMemberUpdate cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnMemberUpdate(bot))
