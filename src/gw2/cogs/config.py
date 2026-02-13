import discord
from discord.ext import commands
from src.bot.tools import bot_utils, chat_formatting
from src.bot.tools.checks import Checks
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


class GW2Config(GuildWars2):
    """(Guild Wars 2 Configuration Commands - Admin)"""

    def __init__(self, bot):
        super().__init__(bot)


@GuildWars2.gw2.group()
@Checks.check_is_admin()
async def config(ctx):
    """(Guild Wars 2 Configuration Commands - Admin)
    gw2 config list
    gw2 config session [on | off]
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 config")


@config.command(name="list")
@commands.cooldown(1, GW2CoolDowns.Config.seconds, commands.BucketType.user)
async def config_list(ctx):
    """(List all Guild Wars 2 Current Server Configurations)
    gw2 config list
    """

    color = ctx.bot.settings["gw2"]["EmbedColor"]
    embed = discord.Embed(color=color)
    guild_icon_url = ctx.guild.icon.url if ctx.guild.icon else None
    embed.set_thumbnail(url=guild_icon_url)
    embed.set_author(
        name=f"{gw2_messages.CONFIG_TITLE} {ctx.guild.name}",
        icon_url=guild_icon_url,
    )
    embed.set_footer(text=gw2_messages.config_more_info(ctx.prefix))

    gw2_configs = Gw2ConfigsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await gw2_configs.get_gw2_server_configs(ctx.guild.id)
    on = chat_formatting.green_text("ON")
    off = chat_formatting.red_text("OFF")
    embed.add_field(name=gw2_messages.USER_SESSION_TITLE, value=f"{on}" if rs[0]["session"] else f"{off}", inline=False)

    # Create interactive view with buttons
    view = GW2ConfigView(ctx, rs[0])

    # Set initial button style based on current config
    view.toggle_session.style = discord.ButtonStyle.success if rs[0]["session"] else discord.ButtonStyle.danger

    # Send the embed with interactive buttons to DM
    message = await ctx.author.send(embed=embed, view=view)
    view.message = message

    # Send notification in channel
    notification_embed = discord.Embed(
        description="📬 Interactive GW2 configuration sent to your DM", color=discord.Color.green()
    )
    notification_embed.set_author(
        name=ctx.author.display_name,
        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url,
    )
    await ctx.send(embed=notification_embed)


@config.command(name="session")
@commands.cooldown(1, GW2CoolDowns.Config.seconds, commands.BucketType.user)
async def config_session(ctx, subcommand_passed: str):
    """(Configure Guild Wars 2 Sessions)
    gw2 config session on
    gw2 config session off
    """

    match subcommand_passed:
        case "on" | "ON":
            new_status = True
            color = discord.Color.green()
            msg = gw2_messages.SESSION_ACTIVATED
        case "off" | "OFF":
            new_status = False
            color = discord.Color.red()
            msg = gw2_messages.SESSION_DEACTIVATED
        case _:
            raise commands.BadArgument(message="BadArgument")

    await ctx.message.channel.typing()
    embed = discord.Embed(description=msg, color=color)
    gw2_configs = Gw2ConfigsDal(ctx.bot.db_session, ctx.bot.log)
    await gw2_configs.update_gw2_session_config(ctx.message.channel.guild.id, new_status, ctx.author.id)
    await bot_utils.send_embed(ctx, embed)


class GW2ConfigView(discord.ui.View):
    """Interactive view for GW2 configuration settings with clickable buttons."""

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
                f"Updating GW2 config {config_key} "
                f"for {self.ctx.guild.name}:{self.ctx.guild.id} "
                f"by {self.ctx.author.name}"
            )
            gw2_configs = Gw2ConfigsDal(self.ctx.bot.db_session, self.ctx.bot.log)
            new_status = not self.server_config[config_key]
            await gw2_configs.update_gw2_session_config(self.ctx.guild.id, new_status, self.ctx.author.id)
            self.server_config[config_key] = new_status
            self.ctx.bot.log.info(
                f"Successfully updated GW2 config {config_key} "
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

        except (discord.HTTPException, discord.NotFound) as e:
            # Handle Discord API errors
            await self._restore_buttons()
            await interaction.edit_original_response(content=f"❌ Discord error updating configuration: {e}", view=self)
        except Exception as e:
            # Handle any other errors (database, etc.)
            self.ctx.bot.log.error(f"Error in GW2 config update: {e}")
            await self._restore_buttons()
            try:
                await interaction.edit_original_response(content=f"❌ Error updating configuration: {e}", view=self)
            except Exception:
                # If we can't even edit the response, log it
                self.ctx.bot.log.error(f"Failed to edit response after error: {e}")
        finally:
            self._updating = False

    async def _restore_buttons(self):
        """Restore button states and colors."""
        for item in self.children:
            if hasattr(item, 'disabled'):
                item.disabled = False

        # Restore original button colors
        self.toggle_session.style = (
            discord.ButtonStyle.success if self.server_config["session"] else discord.ButtonStyle.danger
        )

    async def _create_updated_embed(self):
        """Create updated configuration embed with current settings."""
        color = self.ctx.bot.settings["gw2"]["EmbedColor"]
        embed = discord.Embed(color=color)
        guild_icon_url = self.ctx.guild.icon.url if self.ctx.guild.icon else None
        embed.set_thumbnail(url=guild_icon_url)
        embed.set_author(
            name=f"{gw2_messages.CONFIG_TITLE} {self.ctx.guild.name}",
            icon_url=guild_icon_url,
        )
        embed.set_footer(text=gw2_messages.config_more_info(self.ctx.prefix))

        # Format status indicators
        on = chat_formatting.green_text("ON")
        off = chat_formatting.red_text("OFF")

        embed.add_field(
            name=gw2_messages.USER_SESSION_TITLE,
            value=f"{on}" if self.server_config["session"] else f"{off}",
            inline=False,
        )

        return embed

    @discord.ui.button(label="Session Tracking", emoji="🎮", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_update(
            interaction,
            button,
            "session",
            "Session Tracking",
        )

    async def on_timeout(self):
        # Disable all buttons when view times out
        for item in self.children:
            item.disabled = True

        try:
            await self.message.edit(view=self)
        except discord.NotFound, discord.HTTPException:
            pass  # Message might be deleted or no longer accessible


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Config(bot))
