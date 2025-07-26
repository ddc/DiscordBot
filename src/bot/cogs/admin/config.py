"""Bot configuration commands for server-specific settings and filters."""

from typing import Optional
import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from src.bot.cogs.admin.admin import Admin
from src.bot.constants import messages
from src.bot.tools import bot_utils, chat_formatting
from src.bot.tools.cooldowns import CoolDowns
from src.database.dal.bot.profanity_filters_dal import ProfanityFilterDal
from src.database.dal.bot.servers_dal import ServersDal


class Config(Admin):
    """Admin configuration commands for server settings management."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)


@Config.admin.group()
async def config(ctx: commands.Context) -> Optional[commands.Command]:
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
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
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
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
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
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
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
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
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
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
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
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
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
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
async def config_pfilter(ctx: commands.Context, *, subcommand_passed: str) -> None:
    """Configure profanity filter for specific channels.

    Bot requires Manage Messages permission to delete offensive content.

    Usage:
        admin config pfilter on <channel_id>
        admin config pfilter off <channel_id>
    """

    await ctx.message.channel.typing()

    # Validate arguments
    help_command = (
        f"{messages.HELP_COMMAND_MORE_INFO}: {chat_formatting.inline(f'{ctx.prefix}help admin config pfilter')}"
    )
    subcommands = subcommand_passed.split()
    if len(subcommands) < 2:
        return await bot_utils.send_error_msg(ctx, f"{messages.MISING_REUIRED_ARGUMENT}\n{help_command}")

    new_status = subcommands[0]
    new_channel_id = subcommands[1]

    # Validate channel ID
    if not new_channel_id.isnumeric():
        return await bot_utils.send_error_msg(ctx, f"{messages.CONFIG_CHANNEL_ID_INSTEAD_NAME}\n{help_command}")

    channel_ids = [str(channel.id) for channel in ctx.guild.text_channels]
    if new_channel_id not in channel_ids:
        return await bot_utils.send_error_msg(
            ctx, f"{messages.CHANNEL_ID_NOT_FOUND}: {chat_formatting.inline(new_channel_id)}"
        )

    # Get channel object
    channel = ctx.guild.get_channel(int(new_channel_id))
    if not channel:
        return await bot_utils.send_error_msg(
            ctx, f"{messages.CHANNEL_ID_NOT_FOUND}: {chat_formatting.inline(new_channel_id)}"
        )

    profanity_filter_dal = ProfanityFilterDal(ctx.bot.db_session, ctx.bot.log)

    match new_status:
        case "on" | "ON":
            # Check bot permissions
            if not ctx.guild.me.guild_permissions.administrator and not ctx.guild.me.guild_permissions.manage_messages:
                msg = f"{messages.CONFIG_NOT_ACTIVATED_ERROR} {messages.BOT_MISSING_MANAGE_MESSAGES_PERMISSION}"
                return await bot_utils.send_error_msg(ctx, msg)

            status = "ACTIVATED"
            color = discord.Color.red()
            await profanity_filter_dal.insert_profanity_filter_channel(
                ctx.guild.id, channel.id, channel.name, ctx.author.id
            )
        case "off" | "OFF":
            status = "DEACTIVATED"
            color = discord.Color.green()
            await profanity_filter_dal.delete_profanity_filter_channel(channel.id)
        case _:
            raise commands.BadArgument(message="BadArgument")

    msg = messages.CONFIG_PFILTER.format(status.upper(), channel.name)
    embed = discord.Embed(description=msg, color=color)
    await bot_utils.send_embed(ctx, embed)
    return None


@config.command(name="list")
@commands.cooldown(1, CoolDowns.Config.value, BucketType.user)
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
        name=f"{messages.CONFIG_JOIN}\n*`{cmd_prefix} joinmessage [on | off]`*",
        value=f"{on}" if sc["msg_on_join"] else f"{off}",
        inline=False,
    )
    embed.add_field(
        name=f"{messages.CONFIG_LEAVE}\n*`{cmd_prefix} leavemessage [on | off]`*",
        value=f"{on}" if sc["msg_on_leave"] else f"{off}",
        inline=False,
    )
    embed.add_field(
        name=f"{messages.CONFIG_SERVER}\n*`{cmd_prefix} servermessage [on | off]`*",
        value=f"{on}" if sc["msg_on_server_update"] else f"{off}",
        inline=False,
    )
    embed.add_field(
        name=f"{messages.CONFIG_MEMBER}\n*`{cmd_prefix} membermessage [on | off]`*",
        value=f"{on}" if sc["msg_on_member_update"] else f"{off}",
        inline=False,
    )
    embed.add_field(
        name=f"{messages.CONFIG_BLOCK_INVIS_MEMBERS}\n*`{cmd_prefix} blockinvisible [on | off]`*",
        value=f"{on}" if sc["block_invis_members"] else f"{off}",
        inline=False,
    )
    embed.add_field(
        name=f"{messages.CONFIG_BOT_WORD_REACTIONS}\n*`{cmd_prefix} botreactions [on | off]`*",
        value=f"{on}" if sc["bot_word_reactions"] else f"{off}",
        inline=False,
    )
    embed.add_field(
        name=f"{messages.CONFIG_PFILTER_CHANNELS}\n*`{cmd_prefix} pfilter on <channel_id>`*",
        value=chat_formatting.inline(channel_names),
        inline=False,
    )

    embed.set_footer(text=f"{messages.MORE_INFO}: {ctx.prefix}help admin config")
    await bot_utils.send_embed(ctx, embed, True)


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


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the Config cog to the bot."""
    bot.remove_command("admin")
    await bot.add_cog(Config(bot))
