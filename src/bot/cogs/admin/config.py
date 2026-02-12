import discord
from discord.ext import commands
from src.bot.cogs.admin.admin import Admin
from src.bot.constants import messages
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils, chat_formatting
from src.bot.tools.cooldowns import CoolDowns
from src.database.dal.bot.profanity_filters_dal import ProfanityFilterDal
from src.database.dal.bot.servers_dal import ServersDal


class Config(Admin):
    """Admin configuration commands for server settings management."""

    def __init__(self, bot: Bot) -> None:
        super().__init__(bot)


@Config.admin.group()
async def config(ctx: commands.Context) -> commands.Command | None:
    """Server configuration commands for managing bot behavior.

    Available subcommands:
        admin config list - Show all current server configurations
        admin config joinmessage [on | off] - Toggle join messages
        admin config leavemessage [on | off] - Toggle leave messages
        admin config servermessage [on | off] - Toggle server update messages
        admin config membermessage [on | off] - Toggle member update messages
        admin config blockinvisible [on | off] - Block invisible members
        admin config botreactions [on | off] - Enable bot word reactions
        admin config pfilter [on | off] <channel_id> - Configure profanity filter
    """
    return await bot_utils.invoke_subcommand(ctx, "admin config")


@config.command(name="joinmessage")
@commands.cooldown(1, CoolDowns.Config.value, commands.BucketType.user)
async def config_join_message(ctx: commands.Context, *, status: str) -> None:
    """Toggle messages when users join the server.

    Usage:
        admin config joinmessage on
        admin config joinmessage off
    """

    await ctx.message.channel.typing()

    new_status, color = _get_switch_status(status)
    msg = f"{messages.CONFIG_JOIN} is now: `{status.upper()}`"

    # Update database
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_join(ctx.guild.id, new_status, ctx.author.id)

    # Send confirmation
    embed = discord.Embed(description=msg, color=color)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="leavemessage")
@commands.cooldown(1, CoolDowns.Config.value, commands.BucketType.user)
async def config_leave_message(ctx: commands.Context, *, status: str) -> None:
    """Toggle messages when users leave the server.

    Usage:
        admin config leavemessage on
        admin config leavemessage off
    """

    await ctx.message.channel.typing()

    new_status, color = _get_switch_status(status)
    msg = f"{messages.CONFIG_LEAVE} is now: `{status.upper()}`"

    # Update database
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_leave(ctx.guild.id, new_status, ctx.author.id)

    # Send confirmation
    embed = discord.Embed(description=msg, color=color)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="servermessage")
@commands.cooldown(1, CoolDowns.Config.value, commands.BucketType.user)
async def config_server_message(ctx: commands.Context, *, status: str) -> None:
    """Toggle messages when server settings are updated.

    Usage:
        admin config servermessage on
        admin config servermessage off
    """

    await ctx.message.channel.typing()

    new_status, color = _get_switch_status(status)
    msg = f"{messages.CONFIG_SERVER} is now: `{status.upper()}`"

    # Update database
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_server_update(ctx.guild.id, new_status, ctx.author.id)

    # Send confirmation
    embed = discord.Embed(description=msg, color=color)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="membermessage")
@commands.cooldown(1, CoolDowns.Config.value, commands.BucketType.user)
async def config_member_message(ctx: commands.Context, *, status: str) -> None:
    """Toggle messages when members update their profiles.

    Usage:
        admin config membermessage on
        admin config membermessage off
    """

    await ctx.message.channel.typing()

    new_status, color = _get_switch_status(status)
    msg = f"{messages.CONFIG_MEMBER} is now: `{status.upper()}`"

    # Update database
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_msg_on_member_update(ctx.guild.id, new_status, ctx.author.id)

    # Send confirmation
    embed = discord.Embed(description=msg, color=color)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="blockinvisible")
@commands.cooldown(1, CoolDowns.Config.value, commands.BucketType.user)
async def config_block_invis_members(ctx: commands.Context, *, status: str) -> None:
    """Block messages from invisible members.

    Usage:
        admin config blockinvisible on
        admin config blockinvisible off
    """

    await ctx.message.channel.typing()

    new_status, color = _get_switch_status(status)
    msg = f"{messages.CONFIG_BLOCK_INVIS_MEMBERS} is now: `{status.upper()}`"

    # Update database
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_block_invis_members(ctx.guild.id, new_status, ctx.author.id)

    # Send confirmation
    embed = discord.Embed(description=msg, color=color)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="botreactions")
@commands.cooldown(1, CoolDowns.Config.value, commands.BucketType.user)
async def config_bot_word_reactions(ctx: commands.Context, *, status: str) -> None:
    """Toggle bot reactions to specific words from members.

    Usage:
        admin config botreactions on
        admin config botreactions off
    """

    await ctx.message.channel.typing()

    new_status, color = _get_switch_status(status)
    msg = f"{messages.CONFIG_BOT_WORD_REACTIONS} is now: `{status.upper()}`"

    # Update database
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    await servers_dal.update_bot_word_reactions(ctx.guild.id, new_status, ctx.author.id)

    # Send confirmation
    embed = discord.Embed(description=msg, color=color)
    await bot_utils.send_embed(ctx, embed)


@config.command(name="pfilter")
@commands.cooldown(1, CoolDowns.Config.value, commands.BucketType.user)
async def config_pfilter(ctx: commands.Context, *, subcommand_passed: str) -> None:
    """Configure profanity filter for specific channels.

    Bot requires Manage Messages permission to delete offensive content.

    Usage:
        admin config pfilter on [channel_name_or_id]
        admin config pfilter off [channel_name_or_id]

    If no channel is specified, it uses the current channel.
    """

    await ctx.message.channel.typing()

    # Parse arguments
    help_command = (
        f"{messages.HELP_COMMAND_MORE_INFO}: {chat_formatting.inline(f'{ctx.prefix}help admin config pfilter')}"
    )
    subcommands = subcommand_passed.split()
    if len(subcommands) < 1:
        return await bot_utils.send_error_msg(ctx, f"{messages.MISING_REUIRED_ARGUMENT}\n{help_command}")

    new_status = subcommands[0]

    # If no channel specified, use current channel
    if len(subcommands) == 1:
        channel = ctx.channel
    else:
        channel_input = subcommands[1]

        # Try to find channel by ID first, then by name
        channel = None
        if channel_input.isnumeric():
            channel = ctx.guild.get_channel(int(channel_input))

        if not channel:
            # Search by channel name (case-insensitive)
            channel = discord.utils.get(ctx.guild.text_channels, name=channel_input.lower())

        if not channel:
            return await bot_utils.send_error_msg(
                ctx, f"{messages.CHANNEL_ID_NOT_FOUND}: {chat_formatting.inline(channel_input)}"
            )

    profanity_filter_dal = ProfanityFilterDal(ctx.bot.db_session, ctx.bot.log)

    match new_status:
        case "on" | "ON":
            # Check bot permissions
            if not ctx.guild.me.guild_permissions.administrator and not ctx.guild.me.guild_permissions.manage_messages:
                msg = f"{messages.CONFIG_NOT_ACTIVATED_ERROR} {messages.BOT_MISSING_MANAGE_MESSAGES_PERMISSION}"
                return await bot_utils.send_error_msg(ctx, msg)

            status = "ACTIVATED"
            color = discord.Color.green()
            await profanity_filter_dal.insert_profanity_filter_channel(
                ctx.guild.id, channel.id, channel.name, ctx.author.id
            )
        case "off" | "OFF":
            status = "DEACTIVATED"
            color = discord.Color.red()
            await profanity_filter_dal.delete_profanity_filter_channel(channel.id)
        case _:
            raise commands.BadArgument(message="BadArgument")

    msg = messages.CONFIG_PFILTER.format(status.upper(), channel.name)
    embed = discord.Embed(description=msg, color=color)
    await bot_utils.send_embed(ctx, embed)
    return None


@config.command(name="list")
@commands.cooldown(1, CoolDowns.Config.value, commands.BucketType.user)
async def config_list(ctx: commands.Context) -> None:
    """Display all current bot configurations for this server.

    Usage:
        admin config list
    """

    await ctx.message.channel.typing()

    cmd_prefix = f"{ctx.prefix}admin config"

    # Get server configurations
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    sc = await servers_dal.get_server(ctx.guild.id)

    # Get profanity filter channels
    profanity_filter_dal = ProfanityFilterDal(ctx.bot.db_session, ctx.bot.log)
    pf = await profanity_filter_dal.get_all_server_profanity_filter_channels(ctx.guild.id)

    # Format channel names
    if pf:
        channel_names_lst = [channel['channel_name'] for channel in pf]
        channel_names = "\n".join(channel_names_lst)
    else:
        channel_names = messages.NO_CHANNELS_LISTED

    # Format status indicators
    on = chat_formatting.green_text("ON")
    off = chat_formatting.red_text("OFF")

    # Create embed
    embed = discord.Embed()
    guild_icon_url = ctx.guild.icon.url if ctx.guild.icon else None
    embed.set_thumbnail(url=guild_icon_url)
    embed.set_author(name=f"Configurations for {ctx.guild.name}", icon_url=guild_icon_url)

    embed.add_field(
        name=f"📥 {messages.CONFIG_JOIN}",
        value=f"{on}" if sc["msg_on_join"] else f"{off}",
        inline=True,
    )
    embed.add_field(
        name=f"📤 {messages.CONFIG_LEAVE}",
        value=f"{on}" if sc["msg_on_leave"] else f"{off}",
        inline=True,
    )
    embed.add_field(
        name=f"🔄 {messages.CONFIG_SERVER}",
        value=f"{on}" if sc["msg_on_server_update"] else f"{off}",
        inline=True,
    )
    embed.add_field(
        name=f"👤 {messages.CONFIG_MEMBER}",
        value=f"{on}" if sc["msg_on_member_update"] else f"{off}",
        inline=True,
    )
    embed.add_field(
        name=f"👻 {messages.CONFIG_BLOCK_INVIS_MEMBERS}",
        value=f"{on}" if sc["block_invis_members"] else f"{off}",
        inline=True,
    )
    embed.add_field(
        name=f"🎭 {messages.CONFIG_BOT_WORD_REACTIONS.format(ctx.guild.name)}",
        value=f"{on}" if sc["bot_word_reactions"] else f"{off}",
        inline=True,
    )
    embed.add_field(
        name=f"{messages.CONFIG_PFILTER_CHANNELS}\n*`{cmd_prefix} pfilter on/off <channel_name>`*",
        value=chat_formatting.inline(channel_names),
        inline=False,
    )

    embed.set_footer(text=f"{messages.MORE_INFO}: {ctx.prefix}help admin config")

    # Create interactive view with buttons
    view = ConfigView(ctx, sc)

    # Set initial button styles based on current config
    view.toggle_join_messages.style = discord.ButtonStyle.success if sc["msg_on_join"] else discord.ButtonStyle.danger
    view.toggle_leave_messages.style = discord.ButtonStyle.success if sc["msg_on_leave"] else discord.ButtonStyle.danger
    view.toggle_server_messages.style = (
        discord.ButtonStyle.success if sc["msg_on_server_update"] else discord.ButtonStyle.danger
    )
    view.toggle_member_messages.style = (
        discord.ButtonStyle.success if sc["msg_on_member_update"] else discord.ButtonStyle.danger
    )
    view.toggle_block_invisible.style = (
        discord.ButtonStyle.success if sc["block_invis_members"] else discord.ButtonStyle.danger
    )
    view.toggle_bot_reactions.style = (
        discord.ButtonStyle.success if sc["bot_word_reactions"] else discord.ButtonStyle.danger
    )

    # Send the embed with interactive buttons to DM
    message = await ctx.author.send(embed=embed, view=view)
    view.message = message

    # Send notification in channel
    notification_embed = discord.Embed(
        description="📬 Interactive configuration sent to your DM", color=discord.Color.green()
    )
    notification_embed.set_author(
        name=ctx.author.display_name,
        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url,
    )
    await ctx.send(embed=notification_embed)


def _get_switch_status(status: str) -> tuple[bool, discord.Color]:
    """Convert status string to boolean and appropriate color.

    Args:
        status: The status string ('on', 'off', case-insensitive)

    Returns:
        Tuple of (boolean_status, color)

    Raises:
        commands.BadArgument: If status is not 'on' or 'off'
    """
    match status.lower():
        case "on":
            return True, discord.Color.green()
        case "off":
            return False, discord.Color.red()
        case _:
            raise commands.BadArgument(message="BadArgument")


class ConfigView(discord.ui.View):
    """Interactive view for configuration settings with clickable buttons."""

    def __init__(self, ctx: commands.Context, server_config: dict):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.ctx = ctx
        self.server_config = server_config
        self._updating = False  # Prevent spam clicking
        self.message = None  # Will be set when message is sent

    async def _handle_update(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
        config_key: str,
        update_method,
        success_message: str,
    ):
        """Generic method to handle button updates with cooldown protection."""
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "Only the command invoker can use these buttons.", ephemeral=True
            )

        # Prevent spam clicking
        if self._updating:
            return await interaction.response.send_message("⏳ Please wait, updating configuration...", ephemeral=True)

        # Set updating state and disable all buttons
        self._updating = True
        for item in self.children:
            if hasattr(item, 'disabled'):
                item.disabled = True
                if hasattr(item, 'style'):
                    item.style = discord.ButtonStyle.gray

        # Defer the response to allow editing the original message
        await interaction.response.defer()

        # Show processing state by editing the original message
        await interaction.edit_original_response(content="⏳ Updating configuration...", view=self)

        try:
            # Update database
            self.ctx.bot.log.info(
                f"Updating bot config {config_key} "
                f"for {self.ctx.guild.name}:{self.ctx.guild.id} "
                f"by {self.ctx.author.name}"
            )
            servers_dal = ServersDal(self.ctx.bot.db_session, self.ctx.bot.log)
            new_status = not self.server_config[config_key]
            await update_method(servers_dal, self.ctx.guild.id, new_status, self.ctx.author.id)
            self.server_config[config_key] = new_status
            self.ctx.bot.log.info(
                f"Successfully updated bot config {config_key} "
                f"for {self.ctx.guild.name}:{self.ctx.guild.id} "
                f"by {self.ctx.author.name} "
                f"to {new_status}"
            )

            # Update button appearance
            status_text = "ON" if new_status else "OFF"
            button.style = discord.ButtonStyle.success if new_status else discord.ButtonStyle.danger

            # Re-enable buttons with original colors
            await self._restore_buttons()

            # Update the embed with new configuration
            updated_embed = await self._create_updated_embed()

            # Show success message with updated embed
            await interaction.edit_original_response(
                content=f"✅ {success_message}: **{status_text}**", embed=updated_embed, view=self
            )

        except Exception as e:
            # Handle errors
            await self._restore_buttons()
            await interaction.edit_original_response(content=f"❌ Error updating configuration: {e}", view=self)
        finally:
            self._updating = False

    async def _restore_buttons(self):
        """Restore button states and colors."""
        for item in self.children:
            if hasattr(item, 'disabled'):
                item.disabled = False

        # Restore original button colors
        self.toggle_join_messages.style = (
            discord.ButtonStyle.success if self.server_config["msg_on_join"] else discord.ButtonStyle.danger
        )
        self.toggle_leave_messages.style = (
            discord.ButtonStyle.success if self.server_config["msg_on_leave"] else discord.ButtonStyle.danger
        )
        self.toggle_bot_reactions.style = (
            discord.ButtonStyle.success if self.server_config["bot_word_reactions"] else discord.ButtonStyle.danger
        )
        self.toggle_server_messages.style = (
            discord.ButtonStyle.success if self.server_config["msg_on_server_update"] else discord.ButtonStyle.danger
        )
        self.toggle_member_messages.style = (
            discord.ButtonStyle.success if self.server_config["msg_on_member_update"] else discord.ButtonStyle.danger
        )
        self.toggle_block_invisible.style = (
            discord.ButtonStyle.success if self.server_config["block_invis_members"] else discord.ButtonStyle.danger
        )

    async def _create_updated_embed(self):
        """Create updated configuration embed with current settings."""
        from src.bot.constants import messages
        from src.bot.tools import chat_formatting

        # Get profanity filter channels
        profanity_filter_dal = ProfanityFilterDal(self.ctx.bot.db_session, self.ctx.bot.log)
        pf = await profanity_filter_dal.get_all_server_profanity_filter_channels(self.ctx.guild.id)

        # Format channel names
        if pf:
            channel_names_lst = [channel['channel_name'] for channel in pf]
            channel_names = "\n".join(channel_names_lst)
        else:
            channel_names = messages.NO_CHANNELS_LISTED

        # Format status indicators
        on = chat_formatting.green_text("ON")
        off = chat_formatting.red_text("OFF")

        cmd_prefix = f"{self.ctx.prefix}admin config"

        # Create embed
        embed = discord.Embed()
        guild_icon_url = self.ctx.guild.icon.url if self.ctx.guild.icon else None
        embed.set_thumbnail(url=guild_icon_url)
        embed.set_author(name=f"Configurations for {self.ctx.guild.name}", icon_url=guild_icon_url)

        embed.add_field(
            name=f"📥 {messages.CONFIG_JOIN}",
            value=f"{on}" if self.server_config["msg_on_join"] else f"{off}",
            inline=True,
        )
        embed.add_field(
            name=f"📤 {messages.CONFIG_LEAVE}",
            value=f"{on}" if self.server_config["msg_on_leave"] else f"{off}",
            inline=True,
        )
        embed.add_field(
            name=f"🔄 {messages.CONFIG_SERVER}",
            value=f"{on}" if self.server_config["msg_on_server_update"] else f"{off}",
            inline=True,
        )
        embed.add_field(
            name=f"👤 {messages.CONFIG_MEMBER}",
            value=f"{on}" if self.server_config["msg_on_member_update"] else f"{off}",
            inline=True,
        )
        embed.add_field(
            name=f"👻 {messages.CONFIG_BLOCK_INVIS_MEMBERS}",
            value=f"{on}" if self.server_config["block_invis_members"] else f"{off}",
            inline=True,
        )
        embed.add_field(
            name=f"🎭 {messages.CONFIG_BOT_WORD_REACTIONS.format(self.ctx.guild.name)}",
            value=f"{on}" if self.server_config["bot_word_reactions"] else f"{off}",
            inline=True,
        )
        embed.add_field(
            name=f"{messages.CONFIG_PFILTER_CHANNELS}\n*`{cmd_prefix} pfilter on <channel_id>`*",
            value=chat_formatting.inline(channel_names),
            inline=False,
        )

        embed.set_footer(text=f"{messages.MORE_INFO}: {self.ctx.prefix}help admin config")
        return embed

    @discord.ui.button(label="Join Messages", emoji="📥", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_join_messages(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_update(
            interaction,
            button,
            "msg_on_join",
            lambda dal, guild_id, status, user_id: dal.update_msg_on_join(guild_id, status, user_id),
            "Join Messages",
        )

    @discord.ui.button(label="Leave Messages", emoji="📤", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_leave_messages(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_update(
            interaction,
            button,
            "msg_on_leave",
            lambda dal, guild_id, status, user_id: dal.update_msg_on_leave(guild_id, status, user_id),
            "Leave Messages",
        )

    @discord.ui.button(label="Server Messages", emoji="🔄", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_server_messages(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_update(
            interaction,
            button,
            "msg_on_server_update",
            lambda dal, guild_id, status, user_id: dal.update_msg_on_server_update(guild_id, status, user_id),
            "Server Messages",
        )

    @discord.ui.button(label="Member Messages", emoji="👤", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_member_messages(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_update(
            interaction,
            button,
            "msg_on_member_update",
            lambda dal, guild_id, status, user_id: dal.update_msg_on_member_update(guild_id, status, user_id),
            "Member Messages",
        )

    @discord.ui.button(label="Block Invisible", emoji="👻", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_block_invisible(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_update(
            interaction,
            button,
            "block_invis_members",
            lambda dal, guild_id, status, user_id: dal.update_block_invis_members(guild_id, status, user_id),
            "Block Invisible",
        )

    @discord.ui.button(label="Bot Reactions", emoji="🎭", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_bot_reactions(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_update(
            interaction,
            button,
            "bot_word_reactions",
            lambda dal, guild_id, status, user_id: dal.update_bot_word_reactions(guild_id, status, user_id),
            "Bot Reactions",
        )

    async def on_timeout(self):
        # Disable all buttons when view times out
        for item in self.children:
            item.disabled = True

        try:
            await self.message.edit(view=self)
        except discord.NotFound, discord.HTTPException:
            pass  # Message might be deleted or no longer accessible


async def setup(bot: Bot) -> None:
    """Setup function to add the Config cog to the bot."""
    bot.remove_command("admin")
    await bot.add_cog(Config(bot))
