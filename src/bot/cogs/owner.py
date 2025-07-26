"""Bot owner-only commands for administrative tasks and bot configuration."""

from typing import Optional
import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from src.bot.constants import messages, variables
from src.bot.tools import bot_utils
from src.bot.tools.checks import Checks
from src.bot.tools.cooldowns import CoolDowns
from src.database.dal.bot.bot_configs_dal import BotConfigsDal
from src.database.dal.bot.servers_dal import ServersDal




class Owner(commands.Cog):
    """Bot owner commands for administrative tasks and configuration management."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.group()
    @Checks.check_is_bot_owner()
    @commands.cooldown(1, CoolDowns.Owner.value, BucketType.user)
    async def owner(self, ctx: commands.Context) -> Optional[commands.Command]:
        """Bot owner commands for administrative tasks.

        Available subcommands:
            owner servers - List all servers in database
            owner prefix <new_prefix> - Change bot command prefix
            owner botdescription <new_description> - Update bot description
        """
        return await bot_utils.invoke_subcommand(ctx, "owner")

    @owner.command(name="prefix")
    async def owner_change_prefix(self, ctx: commands.Context, *, new_prefix: str) -> None:
        """Change the bot's command prefix.

        The prefix is used to trigger bot commands.
        Allowed prefixes: ! $ % ^ & ? > < . ;

        Usage:
            owner prefix !
            owner prefix $
        """
        await ctx.message.channel.typing()

        if new_prefix not in variables.ALLOWED_PREFIXES:
            allowed = ", ".join(variables.ALLOWED_PREFIXES)
            raise commands.BadArgument(f"Invalid prefix. Allowed prefixes: {allowed}")

        # Update bot presence if it has an activity
        await self._update_bot_activity_prefix(new_prefix)

        # Update prefix in database and bot instance
        bot_configs_dal = BotConfigsDal(self.bot.db_session, self.bot.log)
        await bot_configs_dal.update_bot_prefix(new_prefix, ctx.author.id)
        self.bot.command_prefix = (new_prefix,)

        # Send confirmation
        embed = self._create_owner_embed(f"{messages.BOT_PREFIX_CHANGED}: `{new_prefix}`")
        await bot_utils.send_embed(ctx, embed)

    @owner.command(name="botdescription")
    async def owner_description(self, ctx: commands.Context, *, desc: str) -> None:
        """Update the bot's description.

        This changes the description shown in the about command
        and other bot information displays.

        Usage:
            owner botdescription A helpful Discord bot
        """
        await bot_utils.delete_message(ctx)
        await ctx.message.channel.typing()

        # Update description in database and bot instance
        bot_configs_dal = BotConfigsDal(self.bot.db_session, self.bot.log)
        await bot_configs_dal.update_bot_description(desc, ctx.author.id)
        self.bot.description = desc

        # Send confirmation
        embed = self._create_owner_embed(f"{messages.BOT_DESCRIPTION_CHANGED}: `{desc}`")
        await bot_utils.send_embed(ctx, embed)

    @owner.command(name="servers")
    async def owner_servers(self, ctx: commands.Context) -> None:
        """Display all servers registered in the database.

        Shows a list of all Discord servers that the bot
        has joined and stored in the database.

        Usage:
            owner servers
        """
        await ctx.message.channel.typing()

        servers_dal = ServersDal(self.bot.db_session, self.bot.log)
        servers = await servers_dal.get_server()

        if not servers:
            embed = self._create_owner_embed("No servers found in database.")
            return await bot_utils.send_embed(ctx, embed, True)

        embed = self._create_owner_embed("Database servers")
        embed.set_author(
            name=self.bot.user.display_name, icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )

        # Split server data into ID and name lists
        server_ids = [str(server["id"]) for server in servers]
        server_names = [server["name"] for server in servers]

        # Truncate if too many servers to display
        max_servers = 25  # Discord embed field limit
        if len(server_ids) > max_servers:
            server_ids = server_ids[:max_servers] + ["..."]
            server_names = server_names[:max_servers] + ["..."]

        embed.add_field(name="ID", value="\n".join(server_ids))
        embed.add_field(name="Name", value="\n".join(server_names))
        embed.set_footer(text=f"Total servers: {len(servers)}")

        await bot_utils.send_embed(ctx, embed, True)
        return None

    async def _update_bot_activity_prefix(self, new_prefix: str) -> None:
        """Update bot activity to reflect the new prefix."""
        bot_user = self.bot.user

        if (
            hasattr(bot_user, "activity")
            and bot_user.activity is not None
            and bot_user.activity.type == discord.ActivityType.playing
        ):
            game_name = str(bot_user.activity.name).split("|")[0].strip()
            new_activity_desc = f"{game_name} | {new_prefix}help"

            activity = discord.Game(name=new_activity_desc)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)

    def _create_owner_embed(self, description: str) -> discord.Embed:
        """Create a standardized embed for owner commands."""
        color = self.bot.settings["bot"]["EmbedOwnerColor"]
        return discord.Embed(description=description, color=color)


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the Owner cog to the bot."""
    await bot.add_cog(Owner(bot))
