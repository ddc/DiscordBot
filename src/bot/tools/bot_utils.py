# -*- coding: utf-8 -*-
import random
from datetime import datetime, timezone
from enum import Enum
from operator import attrgetter
import discord
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


async def insert_server(bot, server: discord.Guild):
    servers_dal = ServersDal(bot.db_session, bot.log)
    await servers_dal.insert_server(server.id, server.name)

    from src.gw2.tools import gw2_utils
    await gw2_utils.insert_gw2_server_configs(bot, server)


async def init_background_tasks(bot):
    bg_activity_timer = bot.settings["bot"]["BGActivityTimer"]
    if bg_activity_timer and bg_activity_timer > 0:
        bg_tasks = BackGroundTasks(bot)
        bot.loop.create_task(bg_tasks.bgtask_change_presence(bg_activity_timer))


async def load_cogs(bot):
    bot.log.debug(messages.LOADING_EXTENSIONS)
    for ext in variables.ALL_COGS:
        cog_name = ext.replace("/", ".").replace(".py", "")
        try:
            await bot.load_extension(cog_name)
            bot.log.debug(f"\t {cog_name}")
        except Exception as e:
            bot.log.error(f"{messages.LOADING_EXTENSION_FAILED}: {cog_name}")
            bot.log.error(f"\t{e.__class__.__name__}: {e}\n")


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
        if is_private_message(ctx) or dm:
            await ctx.author.send(embed=embed)
        else:
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
            ctx.bot.log.error(f"{str(e)}: {msg}")
        finally:
            if warning:
                await send_msg(ctx, msg, False, color)


def is_member_admin(member: discord.Member):
    if member is not None \
            and hasattr(member, "guild_permissions") \
            and member.guild_permissions.administrator:
        return True
    return False


def is_bot_owner(ctx, member: discord.Member):
    return True if ctx.bot.owner_id == member.id else False


def is_server_owner(ctx, member: discord.Member):
    return True if member.id == ctx.guild.owner_id else False


def is_private_message(ctx):
    return True if isinstance(ctx.channel, discord.DMChannel) else False


def get_current_date_time():
    return datetime.now(timezone.utc)


def get_current_date_time_str_long():
    return convert_datetime_to_str_long(get_current_date_time())


def convert_datetime_to_str_long(date: datetime):
    return date.strftime(variables.DATE_TIME_FORMATTER_STR)


def convert_datetime_to_str_short(date: datetime):
    return date.strftime(f"{variables.DATE_FORMATTER} {variables.TIME_FORMATTER}")


def convert_str_to_datetime_short(date_str: str):
    return datetime.strptime(date_str, f"{variables.DATE_FORMATTER} {variables.TIME_FORMATTER}")


def get_object_member_by_str(ctx, member_str: str):
    if not is_private_message(ctx):
        for member in ctx.guild.members:
            if (member_str in (member.name, member.display_name) or
                    (member.nick is not None and str(member.nick.lower()) == str(member_str.lower()))):
                return member
    return None


def get_user_by_id(bot, user_id: int):
    user = bot.get_user(int(user_id))
    return user


def get_member_by_id(guild: discord.Guild, member_id: int):
    member = guild.get_member(int(member_id))
    return member


async def send_msg_to_system_channel(log, server, embed, plain_msg=None):
    channel_to_send_msg = await get_server_system_channel(server)
    if channel_to_send_msg:
        try:
            await channel_to_send_msg.send(embed=embed)
        except discord.HTTPException as e:
            log.error(e)
            if plain_msg:
                await channel_to_send_msg.send(plain_msg)


async def get_server_system_channel(server: discord.Guild):
    if server.system_channel:
        return server.system_channel
    sorted_text_channels = sorted(server.text_channels, key=attrgetter("position"))
    for channel in sorted_text_channels:
        if hasattr(channel, "overwrites"):
            for key, value in channel.overwrites.items():
                if hasattr(key, "name") and key.name == "@everyone" and value.read_messages in (True, None):
                    return channel
    return None


def get_color_settings(color: str):
    if str(color).lower() == "random":
        system_random = random.SystemRandom()
        color = "".join([system_random.choice("0123456789ABCDEF") for _ in range(6)])
        color = int(color, 16)
        return color
    for cor in Colors:
        if cor.name.lower() == color.lower():
            return cor.value


def get_bot_stats(bot):
    result = {}
    unique_users = 0
    bot_users = 0
    text_channels = 0
    voice_channels = 0

    for u in bot.users:
        if u.bot is False:
            unique_users += 1
        if u.bot is True:
            bot_users += 1

    for g in bot.guilds:
        for c in g.channels:
            if isinstance(c, discord.TextChannel):
                text_channels += 1
            elif isinstance(c, discord.VoiceChannel):
                voice_channels += 1

    result["servers"] = f"{len(bot.guilds)} servers"
    result["users"] = f"({unique_users} users)({bot_users} bots)[{len(bot.users)} total]"
    result["channels"] = f"({text_channels} text)({voice_channels} voice)[{int(text_channels + voice_channels)} total]"

    if bot.start_time is None:
        result["start_time"] = get_current_date_time()
    else:
        result["start_time"] = bot.start_time

    return result
