# -*- coding: utf-8 -*-
import configparser
import json
import logging.handlers
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum
from operator import attrgetter
from random import choice
import discord
from alembic import command
from alembic.config import Config
from src.bot.utils import chat_formatting, constants
from src.bot.utils.background_tasks import BackGroundTasks
from src.database.dal.bot.servers_dal import ServersDal
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal


class Object:
    def __init__(self):
        self._created = datetime.now(timezone.utc).isoformat()

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def to_dict(self):
        json_string = json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        json_dict = json.loads(json_string)
        return json_dict


class Colors(Enum):
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


async def run_alembic_migrations():
    alembic_cfg = Config(constants.ALEMBIC_CONFIG_FILE_PATH)
    command.upgrade(alembic_cfg, "head")


async def insert_default_initial_configs(bot, server):
    servers_dal = ServersDal(bot.db_session, bot.log)
    await servers_dal.insert_server(server.id, server.name)

    gw2_configs_dal = Gw2ConfigsDal(bot.db_session, bot.log)
    await gw2_configs_dal.insert_gw2_server_configs(server.id)


async def init_background_tasks(bot):
    if bot.settings["BGChangeGame"].lower() == "yes":
        bg_tasks = BackGroundTasks(bot)
        bot.loop.create_task(bg_tasks.bgtask_change_presence(bot.settings["BGActivityTimer"]))


async def load_cogs(bot):
    bot.log.debug("Loading Bot Extensions...")
    for ext in constants.ALL_COGS:
        cog_name = ".".join(ext.split("/")[-4:])[:-3]
        try:
            await bot.load_extension(cog_name)
            bot.log.debug(f"\t {cog_name}")
        except Exception as e:
            bot.log.error(f"ERROR: FAILED to load extension: {cog_name}")
            bot.log.error(f"\t{e.__class__.__name__}: {e}\n")


async def send_msg(ctx, msg):
    color = ctx.bot.settings["EmbedColor"]
    embed = discord.Embed(color=color, description=msg)
    embed.set_author(name=get_member_name_by_id(ctx), icon_url=ctx.message.author.avatar.url)
    await send_embed(ctx, embed)


async def send_warning_msg(ctx, msg):
    embed = discord.Embed(color=discord.Color.orange(), description=chat_formatting.warning(msg))
    embed.set_author(name=get_member_name_by_id(ctx), icon_url=ctx.message.author.avatar.url)
    await send_embed(ctx, embed)


async def send_info_msg(ctx, msg):
    embed = discord.Embed(color=discord.Color.blue(), description=chat_formatting.info(msg))
    embed.set_author(name=get_member_name_by_id(ctx), icon_url=ctx.message.author.avatar.url)
    await send_embed(ctx, embed)


async def send_error_msg(ctx, msg):
    embed = discord.Embed(color=discord.Color.red(), description=chat_formatting.error(msg))
    embed.set_author(name=get_member_name_by_id(ctx), icon_url=ctx.message.author.avatar.url)
    await send_embed(ctx, embed)


async def send_private_msg(ctx, color, msg):
    embed = discord.Embed(color=color, description=msg)
    await send_embed(ctx, embed, True)


async def send_private_warning_msg(ctx, msg):
    embed = discord.Embed(color=discord.Color.orange(), description=chat_formatting.warning(msg))
    await send_embed(ctx, embed, True)


async def send_private_info_msg(ctx, msg):
    embed = discord.Embed(color=discord.Color.blue(), description=chat_formatting.info(msg))
    await send_embed(ctx, embed, True)


async def send_private_error_msg(ctx, msg):
    embed = discord.Embed(color=discord.Color.red(), description=chat_formatting.error(msg))
    await send_embed(ctx, embed, True)


async def send_help_msg(ctx, cmd):
    if ctx.bot.help_command.dm_help:
        await ctx.author.send(chat_formatting.box(cmd.help))
    else:
        await ctx.send(chat_formatting.box(cmd.help))


async def send_embed(ctx, embed, dm=False):
    try:
        if not embed.color:
            embed.color = ctx.bot.settings["EmbedColor"]

        if dm:
            await ctx.author.send(embed=embed)
        else:
            await ctx.message.channel.typing()
            await ctx.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        msg = "Direct messages are disable in your configuration.\n" \
              "If you want to receive messages from Bots, " \
              "you need to enable this option under Privacy & Safety:\n" \
              "\"Allow direct messages from server members.\"\n"
        await send_error_msg(ctx, msg)


def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    logger = logging.getLogger()
    stderr_hdlr = logging.StreamHandler(stream=sys.stdout)
    stderr_hdlr.setLevel(logging.INFO)
    fmt = "[%(asctime)s.%(msecs)03d]:[%(levelname)s]:%(message)s"
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S")
    stderr_hdlr.setFormatter(formatter)
    logger.addHandler(stderr_hdlr)
    if issubclass(exc_type, KeyboardInterrupt) \
            or issubclass(exc_type, EOFError):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


async def delete_channel_message(ctx, warning=False):
    if not is_private_message(ctx):
        try:
            await ctx.message.delete()
            if warning:
                await send_msg(ctx, "Your message was removed for privacy.")
        except Exception as e:
            ctx.bot.log.error(str(e))


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


def convert_datetime_to_str(date: datetime):
    return date.strftime(f"{constants.DATE_FORMATTER} {constants.TIME_FORMATTER}")


def convert_date_to_str(date: datetime):
    return date.strftime(constants.DATE_FORMATTER)


def get_current_date_str():
    return str(datetime.now(timezone.utc).strftime(constants.DATE_FORMATTER))


def get_current_date_time():
    return datetime.now(timezone.utc)


def get_current_time():
    str_time = str(datetime.now(timezone.utc).strftime(constants.TIME_FORMATTER))
    return datetime.strptime(str_time, f"{constants.TIME_FORMATTER}")


def get_current_date_time_str():
    return str(datetime.now(timezone.utc).strftime(f"{constants.DATE_FORMATTER} {constants.TIME_FORMATTER}"))


def get_current_time_str():
    return str(datetime.now(timezone.utc).strftime(constants.TIME_FORMATTER))


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


def get_member_by_id(guild, member_id: int):
    member = guild.get_member(int(member_id))
    return member


def get_member_name_by_id(ctx, user_id: int = None):
    if user_id:
        member = ctx.guild.get_member(int(user_id))
    else:
        member = ctx.guild.get_member(int(ctx.message.author.id))

    if member is not None:
        member_name = str(member.nick) if member.nick is not None else member.display_name
        # member_name = (temp_name.encode('ascii', 'ignore')).decode("utf-8")
        return member_name
    else:
        return None


def get_object_channel(ctx, channel_str: str):
    for channel in ctx.guild.text_channels:
        if str(channel.name).lower() == channel_str.lower():
            return channel


async def channel_to_send_msg(bot, server: discord.Guild):
    servers_dal = ServersDal(bot.db_session, bot.log)
    rs = await servers_dal.get_server(server.id)
    default_text_channel = rs[0]["default_text_channel"]
    sorted_channels = sorted(server.text_channels, key=attrgetter('position'))
    if default_text_channel is None or default_text_channel == "" or len(default_text_channel) == 0:
        return get_server_first_public_text_channel(server)
    if default_text_channel in str(sorted_channels):
        for channel in sorted_channels:
            if channel.name == default_text_channel:
                return channel
    return None


def get_server_first_public_text_channel(server: discord.Guild):
    sorted_text_channels = sorted(server.text_channels, key=attrgetter('position'))
    general_channel = None
    public_channel = None

    for channel in sorted_text_channels:
        if hasattr(channel, 'overwrites') and len(channel.overwrites) > 0:
            for keys, values in channel.overwrites.items():
                if keys.name == "@everyone":
                    for value in values:
                        if value[0] == "read_messages" and value[1] is True or value[1] is None:
                            if "general" in channel.name.lower():
                                general_channel = channel
                            else:
                                if public_channel is None:
                                    public_channel = channel

    if general_channel is not None:
        return general_channel
    elif public_channel is not None:
        return public_channel
    else:
        return None


def get_member_first_public_text_channel(member: discord.Member):
    sorted_channels = sorted(member.guild.text_channels, key=attrgetter('position'))
    for channel in sorted_channels:
        if member.permissions_in(channel).read_messages is True:
            return channel
    return None


def get_server_everyone_role(server: discord.Guild):
    return server.default_role


def get_all_ini_file_settings(file_name: str):
    dictionary = {}
    parser = configparser.ConfigParser(delimiters='=')
    parser.optionxform = str
    parser._interpolation = configparser.ExtendedInterpolation()
    try:
        parser.read(file_name)
        for section in parser.sections():
            for option in parser.options(section):
                try:
                    value = parser.get(section, option).replace("\"", "")
                    lst_value = list(value.split(","))
                    if len(lst_value) > 1:
                        values = []
                        for each in lst_value:
                            values.append(each.strip())
                        value = values
                except Exception:
                    value = None
                if value is not None and len(value) == 0:
                    value = None
                dictionary[option] = value
        return dictionary
    except Exception as e:
        sys.stderr.write(str(e))


def get_ini_section_settings(file_name, section):
    final_data = {}
    parser = configparser.ConfigParser(delimiters="=")
    parser.optionxform = str
    parser._interpolation = configparser.ExtendedInterpolation()
    try:
        parser.read(file_name)
        for option in parser.options(section):
            try:
                value = parser.get(section, option).replace("\"", "")
            except Exception:
                value = None
            if value is not None and len(value) == 0:
                value = None
            final_data[option] = value
        return final_data
    except Exception as e:
        sys.stderr.write(str(e))


def get_ini_settings(file_name: str, section: str, config_name: str):
    parser = configparser.ConfigParser(delimiters="=", allow_no_value=True)
    parser.optionxform = str
    parser._interpolation = configparser.ExtendedInterpolation()
    try:
        parser.read(file_name)
        value = parser.get(section, config_name).replace("\"", "")
    except Exception:
        value = None
    if value is not None and len(value) == 0:
        value = None
    return value


def get_color_settings(color: str):
    if str(color).lower() == "random":
        return discord.Color(value=get_random_color())

    for cor in Colors:
        if cor.name.lower() == color.lower():
            return cor.value


def get_random_color():
    # color = discord.Color(value=get_random_color())
    color = ''.join([choice('0123456789ABCDEF') for _ in range(6)])
    color = int(color, 16)
    return color


def recursive_overwrite(src, dest, ignore=None):
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)
        if ignore is not None:
            ignored = ignore(src, files)
        else:
            ignored = set()
        for f in files:
            if f not in ignored:
                recursive_overwrite(os.path.join(src, f),
                                    os.path.join(dest, f),
                                    ignore)
    else:
        shutil.copyfile(src, dest)


def convert_timedelta_toObj(time_delta: timedelta):
    obj = Object()
    obj.timedelta = time_delta
    if "," in str(time_delta):
        obj.days = int(str(time_delta).split()[0].strip())
        obj.hours = int(str(time_delta).split(":")[0].split(",")[1].strip())
        obj.minutes = int(str(time_delta).split(":")[1].strip())
        obj.seconds = int(str(time_delta).split(":")[2].strip())
    else:
        obj.days = 0
        obj.hours = int(str(time_delta).split(":")[0].strip())
        obj.minutes = int(str(time_delta).split(":")[1].strip())
        obj.seconds = int(str(time_delta).split(":")[2].strip())
    return obj


def get_time_passed(start_time_str, end_time_str):
    date_time_formatter = f"{constants.DATE_FORMATTER} {constants.TIME_FORMATTER}"
    time_passed_delta = (datetime.strptime(end_time_str, date_time_formatter) -
                         datetime.strptime(start_time_str, date_time_formatter))

    time_passed_obj = convert_timedelta_toObj(time_passed_delta)
    return time_passed_obj


async def create_admin_commands_channel(bot, guild: discord.Guild):
    for chan in guild.text_channels:
        if chan.name == 'bot-commands':
            return

    _overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    prefix = bot.command_prefix[0]
    msg = "Use this channel to type bot commands.\n" \
          f"If you are an admin and wish to list configurations: `{prefix}config list`\n" \
          f"To get a list of commands: `{prefix}help`"
    try:
        channel = await guild.create_text_channel("Bot Commands", overwrites=_overwrites)
        await channel.edit(topic=msg)
        await channel.edit(name="Bot Commands")
        await channel.send(f"{msg}")
    except discord.Forbidden as err:
        bot.log.info(f"(Server:{guild.name})(BOT IS NOT ADMIN)({err.text} to create channel: bot-commands)")
    except discord.HTTPException as err:
        bot.log.info(f"(Server:{guild.name})({err.text})")


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

    servers = f"{len(bot.guilds)} servers"
    result['servers'] = servers

    users = f"({unique_users} users)({bot_users} bots)[{len(bot.users)} total]"
    result['users'] = users

    channels = f"({text_channels} text)({voice_channels} voice)[{int(text_channels + voice_channels)} total]"
    result['channels'] = channels

    return result
