# -*- coding: utf-8 -*-
import configparser
from datetime import datetime, timezone
from enum import Enum
import json
import logging.handlers
from operator import attrgetter
from random import choice
import sys
from alembic import command
from alembic.config import Config
import discord
from src.bot.utils import chat_formatting, constants
from src.bot.utils.background_tasks import BackGroundTasks
from src.database.dal.bot.servers_dal import ServersDal


class Object(object):
    def __init__(self):
        self._created = datetime.now(timezone.utc).isoformat()

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def to_dict(self):
        json_string = json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        json_dict = json.loads(json_string)
        return json_dict


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


async def run_alembic_migrations():
    alembic_cfg = Config(constants.ALEMBIC_CONFIG_FILE_PATH)
    command.upgrade(alembic_cfg, "head")


async def insert_server(bot, server: discord.Guild):
    servers_dal = ServersDal(bot.db_session, bot.log)
    await servers_dal.insert_server(server.id, server.name)

    from src.gw2.utils import gw2_utils
    await gw2_utils.insert_gw2_server_configs(bot, server)


async def init_background_tasks(bot):
    bg_activity_timer = bot.settings["bot"]["BGActivityTimer"]
    if bg_activity_timer and bg_activity_timer > 0:
        bg_tasks = BackGroundTasks(bot)
        bot.loop.create_task(bg_tasks.bgtask_change_presence(bg_activity_timer))


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
        msg = "Direct messages are disable in your configuration.\n" \
              "If you want to receive messages from Bots, " \
              "you need to enable this option under Privacy & Safety:\n" \
              "\"Allow direct messages from server members.\"\n"
        await send_error_msg(ctx, msg)
    except Exception as e:
        ctx.bot.logger.error(e)


async def delete_message(ctx, warning=False):
    if not is_private_message(ctx):
        try:
            color = None
            msg = "Your message was removed for privacy."
            await ctx.message.delete()
        except Exception as e:
            color = discord.Color.red()
            msg = "Bot does not have permission to delete messages."
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


def get_current_date_time_str():
    return convert_datetime_to_str(get_current_date_time())


def convert_datetime_to_str(date: datetime):
    return date.strftime(constants.DATE_TIME_FORMATTER_STR)


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
                if hasattr(key, "name") and key.name == "@everyone":
                    if value.read_messages in (True, None):
                        return channel
    return None


def get_all_ini_file_settings(file_name: str):
    dictionary = {}
    parser = configparser.ConfigParser(delimiters="=")
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
                            values.append(int(each.strip()) if each.strip().isnumeric() else each.strip())
                        value = values
                    if value is not None and type(value) is str:
                        if len(value) == 0:
                            value = None
                        elif value.isnumeric():
                            value = int(value)
                except:
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
                if value is not None and type(value) is str:
                    if len(value) == 0:
                        value = None
                    elif value.isnumeric():
                        value = int(value)
            except:
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
        if value is not None and type(value) is str:
            if len(value) == 0:
                value = None
            elif value.isnumeric():
                value = int(value)
    except:
        value = None
    return value


def get_color_settings(color: str):
    if str(color).lower() == "random":
        color = ''.join([choice('0123456789ABCDEF') for _ in range(6)])
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


def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    logger = logging.getLogger()
    stderr_hdlr = logging.StreamHandler(stream=sys.stdout)
    stderr_hdlr.setLevel(logging.INFO)
    fmt = "[%(asctime)s.%(msecs)03d]:[%(levelname)s]:%(message)s"
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S")
    stderr_hdlr.setFormatter(formatter)
    logger.addHandler(stderr_hdlr)
    if issubclass(exc_type, KeyboardInterrupt) or issubclass(exc_type, EOFError):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
