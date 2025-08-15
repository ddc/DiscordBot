import sys
import discord
from discord.ext import commands
from src.bot.constants import messages, variables
from src.bot.tools import bot_utils


class WelcomeMessageBuilder:
    """Builds welcome messages and embeds for new guilds."""

    @staticmethod
    def build_welcome_message(bot_name: str, prefix: str, games_included: str) -> str:
        """Build the welcome message text."""
        return messages.GUILD_JOIN_BOT_MESSAGE.format(bot_name, prefix, games_included, prefix, prefix)

    @staticmethod
    def build_welcome_embed(bot: commands.Bot, message: str) -> discord.Embed:
        """Build the welcome embed with bot information."""
        embed = discord.Embed(color=discord.Color.green(), description=message)

        # Set author information
        bot_avatar_url = bot.user.avatar.url if bot.user.avatar else None
        embed.set_author(
            name=f"{bot.user.name} v{variables.VERSION}",
            icon_url=bot_avatar_url,
            url=variables.BOT_WEBPAGE_URL,
        )

        # Set thumbnail
        if bot_avatar_url:
            embed.set_thumbnail(url=bot_avatar_url)

        # Set footer with developer info
        WelcomeMessageBuilder._set_footer(embed, bot)

        return embed

    @staticmethod
    def _set_footer(embed: discord.Embed, bot: commands.Bot) -> None:
        """Set footer with developer information."""
        try:
            author = bot.get_user(bot.owner_id)
            python_version = "Python {}.{}.{}".format(*sys.version_info[:3])

            if author and author.avatar:
                embed.set_footer(icon_url=author.avatar.url, text=f"Developed by {author} | {python_version}")
            else:
                embed.set_footer(text=f"Developed by Bot Owner | {python_version}")
        except (AttributeError, discord.HTTPException):
            # Fallback if owner information is not available or HTTP error occurs
            python_version = "Python {}.{}.{}".format(*sys.version_info[:3])
            embed.set_footer(text=f"Discord Bot | {python_version}")


class OnGuildJoin(commands.Cog):
    """Guild join event handler"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.message_builder = WelcomeMessageBuilder()

        @self.bot.event
        async def on_guild_join(guild: discord.Guild) -> None:
            """Handle bot joining a new guild."""
            # Register server in database
            await bot_utils.insert_server(bot, guild)

            # Build welcome message and embed
            games_included = "".join(variables.GAMES_INCLUDED)
            welcome_text = self.message_builder.build_welcome_message(
                bot.user.name,
                bot.command_prefix,
                games_included,
            )
            welcome_embed = self.message_builder.build_welcome_embed(bot, welcome_text)

            # Send welcome message to system channel
            await bot_utils.send_msg_to_system_channel(bot.log, guild, welcome_embed, welcome_text)


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OnGuildJoin cog to the bot."""
    await bot.add_cog(OnGuildJoin(bot))
