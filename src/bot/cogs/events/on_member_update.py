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
                if after.bot:
                    return

                embed, msg = self._create_member_embed(after)
                
                # Check for changes and update embed/message
                self._handle_nickname_changes(before, after, embed, msg)
                self._handle_role_changes(before, after, embed, msg)
                
                # Send notification if changes were detected
                await self._send_notification_if_enabled(after, embed, msg)
                
            except Exception as e:
                self.bot.log.error(f"Error in on_member_update for {after}: {e}")

    def _create_member_embed(self, member):
        """Create the base embed and message for member updates."""
        msg = [f"{messages.PROFILE_CHANGES}:\n\n"]
        
        # Create a simple context-like object for get_embed
        class SimpleContext:
            def __init__(self, bot):
                self.bot = bot
        
        ctx = SimpleContext(self.bot)
        embed = bot_utils.get_embed(ctx)

        # Set member info with null checks
        if member.avatar:
            embed.set_author(name=member.display_name, icon_url=member.avatar.url)
        else:
            embed.set_author(name=member.display_name)

        embed.set_footer(
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None,
            text=f"{bot_utils.get_current_date_time_str_long()} UTC",
        )
        
        return embed, msg

    def _handle_nickname_changes(self, before, after, embed, msg):
        """Handle member nickname changes."""
        if before.nick != after.nick:
            if before.nick is not None:
                embed.add_field(name=messages.PREVIOUS_NICKNAME, value=str(before.nick))
            embed.add_field(name=messages.NEW_NICKNAME, value=str(after.nick))
            msg.append(f"{messages.NEW_NICKNAME}: `{after.nick}`\n")

    def _handle_role_changes(self, before, after, embed, msg):
        """Handle member role changes."""
        if before.roles != after.roles:
            self._add_previous_roles_field(before, embed)
            self._add_new_roles_field(after, embed, msg)

    def _add_previous_roles_field(self, before_member, embed):
        """Add previous roles field to embed if roles existed."""
        if before_member.roles is not None:
            role_names = ", ".join([role.name for role in before_member.roles])
            embed.add_field(name=messages.PREVIOUS_ROLES, value=role_names)

    def _add_new_roles_field(self, after_member, embed, msg):
        """Add new roles field to embed and message."""
        role_names = ", ".join([role.name for role in after_member.roles])
        embed.add_field(name=messages.NEW_ROLES, value=role_names)
        msg.append(f"{messages.NEW_ROLES}: `{role_names}`\n")

    async def _send_notification_if_enabled(self, member, embed, msg):
        """Send notification if changes were detected and notifications are enabled."""
        if len(embed.fields) == 0:
            return
            
        try:
            servers_dal = ServersDal(self.bot.db_session, self.bot.log)
            server_config = await servers_dal.get_server(member.guild.id)

            if not (server_config and server_config.get("msg_on_member_update", False)):
                return
                
            await bot_utils.send_msg_to_system_channel(self.bot.log, member.guild, embed, "".join(msg))
            self.bot.log.info(f"Member update notification sent for {member} in {member.guild.name}")
            
        except Exception as e:
            self.bot.log.error(f"Failed to send member update notification: {e}")


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OnMemberUpdate cog to the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(OnMemberUpdate(bot))
