import discord
from discord.ext import commands
from src.bot.constants import messages
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils
from src.bot.tools.checks import Checks
from src.bot.tools.cooldowns import CoolDowns


class Admin(commands.Cog):
    """Admin commands for bot configuration and status management."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.group(aliases=["mod"])
    @Checks.check_is_admin()
    async def admin(self, ctx: commands.Context) -> commands.Command | None:
        """Admin commands for bot administration.

        Available subcommands:
            admin botgame <game> - Change the game that bot is playing
        """
        return await bot_utils.invoke_subcommand(ctx, "admin")

    @admin.command(name="botgame")
    @commands.cooldown(1, CoolDowns.Admin.value, commands.BucketType.user)
    async def botgame(self, ctx: commands.Context, *, game: str) -> None:
        """Change the game that bot is playing.

        Updates the bot's activity status to show it's playing the specified game.
        If the background activity timer is enabled, shows a warning about the setting.

        Usage:
            admin botgame Minecraft
        """

        await ctx.message.channel.typing()

        # Update bot game status
        prefix = self.bot.command_prefix[0]
        bot_game_desc = f"{game} | {prefix}help"
        activity = discord.Game(name=bot_game_desc)
        await self.bot.change_presence(activity=activity)

        # Create success embed
        embed = self._create_admin_embed(f"```{messages.bot_announce_playing(game)}```")
        embed.set_author(
            name=self.bot.user.display_name,
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None,
        )
        await bot_utils.send_embed(ctx, embed)

        # Warn about background activity timer if enabled
        await self._warn_about_bg_activity_timer(ctx)

    async def _warn_about_bg_activity_timer(self, ctx: commands.Context) -> None:
        """Show warning if background activity timer will override the game status."""
        bg_activity_timer = self.bot.settings["bot"]["BGActivityTimer"]
        if bg_activity_timer and bg_activity_timer > 0:
            bg_task_warning = messages.bg_task_warning(bg_activity_timer)
            warning_embed = self._create_admin_embed(bg_task_warning)
            await bot_utils.send_embed(ctx, warning_embed, False)

    @staticmethod
    def _create_admin_embed(description: str) -> discord.Embed:
        """Create a standardized embed for admin commands."""
        return discord.Embed(description=description)


async def setup(bot: Bot) -> None:
    """Setup function to add the Admin cog to the bot."""
    await bot.add_cog(Admin(bot))
