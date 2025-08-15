import random
from datetime import datetime, timezone
from enum import Enum
from operator import attrgetter
from typing import Optional
import discord
from discord.ext import commands
from src.bot.constants import messages, variables
from src.bot.tools import chat_formatting
from src.bot.tools.background_tasks import BackGroundTasks
from src.database.dal.bot.servers_dal import ServersDal


class Colors(Enum):
    black = discord.Color.default()
    teal = discord.Color.teal()
    dark_teal = discord.Color.dark_teal()
    green = discord.Color.green()
    dark_green = discord.Color.dark_green()
    blue = discord.Color.blue()
    dark_blue = discord.Color.dark_blue()
    purple = discord.Color.purple()
    dark_purple = discord.Color.dark_purple()
    magenta = discord.Color.magenta()
    dark_magenta = discord.Color.dark_magenta()
    gold = discord.Color.gold()
    dark_gold = discord.Color.dark_gold()
    orange = discord.Color.orange()
    dark_orange = discord.Color.dark_orange()
    red = discord.Color.red()
    dark_red = discord.Color.dark_red()
    lighter_grey = discord.Color.lighter_grey()
    dark_grey = discord.Color.dark_grey()
    light_grey = discord.Color.light_grey()
    darker_grey = discord.Color.darker_grey()
    blurple = discord.Color.blurple()
    greyple = discord.Color.greyple()


async def insert_server(bot: commands.Bot, server: discord.Guild) -> None:
    """Insert server information into database and initialize GW2 configs."""
    servers_dal = ServersDal(bot.db_session, bot.log)
    await servers_dal.insert_server(server.id, server.name)

    from src.gw2.tools import gw2_utils

    await gw2_utils.insert_gw2_server_configs(bot, server)


def init_background_tasks(bot: commands.Bot) -> None:
    """Initialize bot background tasks if configured."""
    bg_activity_timer = bot.settings["bot"]["BGActivityTimer"]
    if bg_activity_timer and bg_activity_timer > 0:
        bg_tasks = BackGroundTasks(bot)
        bot.loop.create_task(bg_tasks.change_presence_task(bg_activity_timer))


async def load_cogs(bot):
    bot.log.debug(messages.LOADING_EXTENSIONS)
    for ext in variables.ALL_COGS:
        cog_name = ext.replace("/", ".").replace(".py", "")
        try:
            await bot.load_extension(cog_name)
            bot.log.debug(f"{cog_name}")
        except Exception as e:
            bot.log.error(f"{messages.LOADING_EXTENSION_FAILED}: {cog_name}")
            bot.log.error(f"{e.__class__.__name__}: {e}\n")


async def invoke_subcommand(ctx, command_name: str):
    await ctx.message.channel.typing()
    if ctx.invoked_subcommand:
        return ctx.invoked_subcommand
    else:
        if ctx.command is not None:
            cmd = ctx.command
        else:
            cmd = ctx.bot.get_command(command_name)
        await send_help_msg(ctx, cmd)
        return None


def get_embed(ctx, description=None, color=None):
    if not color:
        color = ctx.bot.settings["bot"]["EmbedColor"]
    ebd = discord.Embed(color=color)
    if description:
        ebd.description = description
    return ebd


async def send_msg(ctx, description=None, dm=False, color=None):
    embed = get_embed(ctx, description, color)
    await send_embed(ctx, embed, dm)


async def send_warning_msg(ctx, description, dm=False):
    embed = get_embed(ctx, chat_formatting.warning(description), color=discord.Color.orange())
    await send_embed(ctx, embed, dm)


async def send_info_msg(ctx, description, dm=False):
    embed = get_embed(ctx, chat_formatting.info(description), discord.Color.blue())
    await send_embed(ctx, embed, dm)


async def send_error_msg(ctx, description, dm=False):
    embed = get_embed(ctx, chat_formatting.error(description), discord.Color.red())
    await send_embed(ctx, embed, dm)


async def send_help_msg(ctx, cmd):
    if ctx.bot.help_command.dm_help:
        await ctx.author.send(chat_formatting.box(cmd.help))
    else:
        await ctx.send(chat_formatting.box(cmd.help))


async def send_embed(ctx, embed, dm=False):
    try:
        if not embed.color:
            embed.color = ctx.bot.settings["bot"]["EmbedColor"]
        if not embed.author:
            embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)

        if is_private_message(ctx):
            # Already in DM, just send the embed
            await ctx.author.send(embed=embed)
        elif dm:
            # Send to DM and notify in channel
            await ctx.author.send(embed=embed)
            notification_embed = discord.Embed(description="📬 Response sent to your DM", color=discord.Color.green())
            notification_embed.set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url,
            )
            await ctx.send(embed=notification_embed)
        else:
            # Send to channel
            await ctx.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        await send_error_msg(ctx, messages.DISABLED_DM)
    except Exception as e:
        ctx.bot.logger.error(e)


async def delete_message(ctx, warning=False):
    if not is_private_message(ctx):
        color = None
        msg = messages.MESSAGE_REMOVED_FOR_PRIVACY

        try:
            await ctx.message.delete()
        except Exception as e:
            color = discord.Color.red()
            msg = messages.DELETE_MESSAGE_NO_PERMISSION
            ctx.bot.log.error(f"{e}: {msg}")
        finally:
            if warning:
                await send_msg(ctx, msg, False, color)


def is_member_admin(member: Optional[discord.Member]) -> bool:
    """Check if a member has administrator permissions."""
    return member is not None and hasattr(member, "guild_permissions") and member.guild_permissions.administrator


def is_bot_owner(ctx: commands.Context, member: discord.Member) -> bool:
    """Check if a member is the bot owner."""
    return ctx.bot.owner_id == member.id


def is_server_owner(ctx: commands.Context, member: discord.Member) -> bool:
    """Check if a member is the server owner."""
    return member.id == ctx.guild.owner_id


def is_private_message(ctx: commands.Context) -> bool:
    """Check if the context is a private/DM message."""
    return isinstance(ctx.channel, discord.DMChannel)


def get_current_date_time():
    return datetime.now(timezone.utc)


def get_current_date_time_str_long():
    return convert_datetime_to_str_long(get_current_date_time())


def convert_datetime_to_str_long(date: datetime):
    return date.strftime(variables.DATE_TIME_FORMATTER_STR)


def convert_datetime_to_str_short(date: datetime):
    return date.strftime(f"{variables.DATE_FORMATTER} {variables.TIME_FORMATTER}")


def convert_str_to_datetime_short(date_str: str) -> datetime:
    """Convert short format string to datetime."""
    return datetime.strptime(date_str, f"{variables.DATE_FORMATTER} {variables.TIME_FORMATTER}")


def get_object_member_by_str(ctx: commands.Context, member_str: str) -> Optional[discord.Member]:
    """Find a guild member by name, display name, or nickname."""
    if is_private_message(ctx):
        return None

    for member in ctx.guild.members:
        if member_str in (member.name, member.display_name) or (
            member.nick is not None and member.nick.lower() == member_str.lower()
        ):
            return member

    return None


def get_user_by_id(bot: commands.Bot, user_id: int) -> Optional[discord.User]:
    """Get a user by their ID."""
    return bot.get_user(int(user_id))


def get_member_by_id(guild: discord.Guild, member_id: int) -> Optional[discord.Member]:
    """Get a guild member by their ID."""
    return guild.get_member(int(member_id))


async def send_msg_to_system_channel(log, server, embed, plain_msg=None):
    channel_to_send_msg = get_server_system_channel(server)
    if channel_to_send_msg:
        try:
            await channel_to_send_msg.send(embed=embed)
        except discord.HTTPException as e:
            log.error(e)
            if plain_msg:
                await channel_to_send_msg.send(plain_msg)


def get_server_system_channel(server: discord.Guild) -> Optional[discord.TextChannel]:
    """Get the server's system channel or find the first readable text channel."""
    if server.system_channel:
        return server.system_channel

    # Find the first publicly readable text channel
    sorted_channels = sorted(server.text_channels, key=attrgetter("position"))

    for channel in sorted_channels:
        if not hasattr(channel, "overwrites"):
            continue

        for target, permissions in channel.overwrites.items():
            if hasattr(target, "name") and target.name == "@everyone" and permissions.read_messages in (True, None):
                return channel

    return None


def get_color_settings(color: str) -> Optional[discord.Color]:
    """Get a Discord color from string name or generate random color."""
    color_lower = color.lower()

    if color_lower == "random":
        system_random = random.SystemRandom()
        hex_color = "".join(system_random.choice("0123456789ABCDEF") for _ in range(6))
        return discord.Color(int(hex_color, 16))

    for color_enum in Colors:
        if color_enum.name.lower() == color_lower:
            return color_enum.value

    return None


def get_bot_stats(bot: commands.Bot) -> dict[str, str | datetime]:
    """Get comprehensive bot statistics."""
    unique_users = sum(1 for user in bot.users if not user.bot)
    bot_users = sum(1 for user in bot.users if user.bot)

    text_channels = sum(
        1 for guild in bot.guilds for channel in guild.channels if isinstance(channel, discord.TextChannel)
    )

    voice_channels = sum(
        1 for guild in bot.guilds for channel in guild.channels if isinstance(channel, discord.VoiceChannel)
    )

    total_channels = text_channels + voice_channels

    return {
        "servers": f"{len(bot.guilds)} servers",
        "users": f"({unique_users} users)({bot_users} bots)[{len(bot.users)} total]",
        "channels": f"({text_channels} text)({voice_channels} voice)[{total_channels} total]",
        "start_time": getattr(bot, 'start_time', None) or get_current_date_time(),
    }
