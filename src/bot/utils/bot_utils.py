# -*- coding: utf-8 -*-
import configparser
import json
import logging.handlers
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum
from operator import attrgetter
from random import choice
import discord
from alembic import command
from alembic.config import Config
from src.bot.utils import chat_formatting, constants
from src.bot.utils.bg_tasks import BackGroundTasks
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


async def reload_cogs(self):
    self.bot.log.info("RE-Loading Bot Extensions...")
    for ext in constants.ALL_COGS:
        cog_name = ".".join(ext.split("/")[-4:])[:-3]
        try:
            if hasattr(self, "bot"):
                self.bot.reload_extension(cog_name)
            else:
                self.reload_extension(cog_name)
                self.log.debug(f"\t {cog_name}")
        except Exception as e:
            self.bot.log.error(f"ERROR: FAILED to load extension: {cog_name}")
            self.bot.log.error(f"\t{e.__class__.__name__}: {e}\n")


async def send_msg(self, ctx, color, msg):
    await ctx.message.channel.typing()
    embed = discord.Embed(color=color, description=msg)
    embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
    await send_embed(self, ctx, embed, False, msg)


async def send_warning_msg(self, ctx, msg):
    await ctx.message.channel.typing()
    embed = discord.Embed(color=discord.Color.orange(), description=chat_formatting.warning(msg))
    embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
    await send_embed(self, ctx, embed, False, msg)


async def send_info_msg(self, ctx, msg):
    await ctx.message.channel.typing()
    embed = discord.Embed(color=discord.Color.blue(), description=chat_formatting.info(msg))
    embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
    await send_embed(self, ctx, embed, False, msg)


async def send_error_msg(self, ctx, msg):
    await ctx.message.channel.typing()
    embed = discord.Embed(color=discord.Color.red(), description=chat_formatting.error(msg))
    embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
    await send_embed(self, ctx, embed, False, msg)


async def send_private_msg(self, ctx, color, msg):
    embed = discord.Embed(color=color, description=msg)
    # embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
    await send_embed(self, ctx, embed, True, msg)


async def send_private_warning_msg(self, ctx, msg):
    embed = discord.Embed(color=discord.Color.orange(), description=chat_formatting.warning(msg))
    # embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
    await send_embed(self, ctx, embed, True, msg)


async def send_private_info_msg(self, ctx, msg):
    embed = discord.Embed(color=discord.Color.blue(), description=chat_formatting.info(msg))
    # embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
    await send_embed(self, ctx, embed, True, msg)


async def send_private_error_msg(self, ctx, msg):
    embed = discord.Embed(color=discord.Color.red(), description=chat_formatting.error(msg))
    # embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
    await send_embed(self, ctx, embed, True, msg)


async def send_help_msg(self, ctx, cmd):
    if self.bot.help_command.dm_help:
        await ctx.author.send(chat_formatting.box(cmd.help))
    else:
        await ctx.send(chat_formatting.box(cmd.help))


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


async def send_embed(self, ctx, embed, dm=False, msg=None):
    try:
        if dm:
            if is_private_message(self, ctx):
                await ctx.send(embed=embed)
            else:
                await ctx.author.send(embed=embed)
        else:
            await ctx.send(embed=embed)
    except discord.HTTPException as err:
        # except discord.Forbidden as err:
        if "Cannot send messages to this user" in err.text:
            await ctx.send(f"{ctx.message.author.mention}\n")
            err_msg = "Direct messages are disable in your configuration.\n" \
                      "If you want to receive messages from Bots, " \
                      "you need to enable this option under Privacy & Safety:\n" \
                      "\"Allow direct messages from server members.\"\n"
            await ctx.send(chat_formatting.red_text(err_msg))
            if msg is not None:
                await ctx.send(chat_formatting.green_text(msg))
        else:
            await ctx.send(f"{ctx.message.author.mention}\n")
            if msg is not None:
                await ctx.send(f"{chat_formatting.green_text(msg)}")


async def delete_channel_message(self, ctx, warning=False):
    if not is_private_message(self, ctx):
        try:
            await ctx.message.delete()
            if warning:
                color = self.bot.settings["EmbedColor"]
                await send_msg(self, ctx, color, "Your message was removed for privacy.")
        except:
            # await send_info_msg(self, ctx, "Bot does not have permission to delete messages.\n"\
            #                                   "Missing permission: `Manage Messages`")
            return


def is_member_admin(member: discord.Member):
    if member is not None \
            and hasattr(member, "guild_permissions") \
            and member.guild_permissions.administrator:
        return True
    return False


def is_bot_owner(ctx, member: discord.Member):
    if ctx.bot.owner_id == member.id:
        return True
    return False


def is_server_owner(ctx, member: discord.Member):
    if member.id == ctx.guild.owner_id:
        return True
    return False


def is_private_message(self, ctx):
    return True if isinstance(ctx.channel, discord.DMChannel) else False


def convert_datetime_to_str(date: datetime):
    new_date = date.strftime(f"{constants.DATE_FORMATTER} {constants.TIME_FORMATTER}")
    return new_date


def convert_date_to_str(date: datetime):
    new_date = date.strftime(constants.DATE_FORMATTER)
    return new_date


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


def get_object_member_by_str(self, ctx, member_str: str):
    if not is_private_message(self, ctx):
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


def get_member_name_by_id(self, ctx, user_id: int):
    member = ctx.guild.get_member(int(user_id))
    if member is not None:
        member_name = str(member.nick) if member.nick is not None else member.display_name
        # member_name = (temp_name.encode('ascii', 'ignore')).decode("utf-8")
        return member_name
    else:
        return None


def get_object_channel(self, ctx, channel_str: str):
    for channel in ctx.guild.text_channels:
        if str(channel.name).lower() == channel_str.lower():
            return channel


async def channel_to_send_msg(bot, server: discord.Guild):
    serverConfigsSql = ServersDal(bot.db_session, bot.log)
    rs = await serverConfigsSql.get_server_by_id(server.id)
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
    parser = configparser.ConfigParser(delimiters='=')
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
    parser = configparser.ConfigParser(delimiters='=', allow_no_value=True)
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


# def get_region_flag(region: str):
#     flag = ""
#     if "brazil" in str(region).lower():
#         flag = ":flag_br:"
#     elif "eu" in str(region).lower():
#         flag = ":flag_eu:"
#     elif "hong" in str(region).lower():
#         flag = ":flag_hk:"
#     elif "india" in str(region).lower():
#         flag = ":flag_in:"
#     elif "japan" in str(region).lower():
#         flag = ":flag_jp:"
#     elif "russia" in str(region).lower():
#         flag = ":flag_ru:"
#     elif "singapore" in str(region).lower():
#         flag = ":flag_sg:"
#     elif "southafrica" in str(region).lower():
#         flag = ":flag_za:"
#     elif "sydney" in str(region).lower():
#         flag = ":flag_au:"
#     elif "us" in str(region).lower():
#         flag = ":flag_us:"
#     return flag


def clear_screen():
    if constants.IS_WINDOWS:
        os.system("cls")
    else:
        os.system("clear")


def is_git_installed():
    try:
        subprocess.call(["git", "--version"], stdout=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return False
    else:
        return True


# def is_nping_installed():
#     try:
#         subprocess.call(["nping", "--version"], stdout=subprocess.DEVNULL,
#                                               stdin =subprocess.DEVNULL,
#                                               stderr=subprocess.DEVNULL)
#     except FileNotFoundError:
#         return False
#     else:
#         return True


def wait_return():
    try:
        input("Press enter to continue...").strip()
    except SyntaxError:
        pass


def user_choice():
    try:
        return input(">>> ").lower().strip()
    except SyntaxError:
        pass


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
    time_passed_delta = datetime.strptime(end_time_str, date_time_formatter) - \
                        datetime.strptime(start_time_str, date_time_formatter)

    time_passed_obj = convert_timedelta_toObj(time_passed_delta)
    return time_passed_obj


async def create_admin_commands_channel(self, guild: discord.Guild):
    for chan in guild.text_channels:
        if chan.name == 'bot-commands':
            return

    _overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    prefix = self.bot.command_prefix[0]
    msg = "Use this channel to type bot commands.\n" \
          f"If you are an admin and wish to list configurations: `{prefix}config list`\n" \
          f"To get a list of commands: `{prefix}help`"
    try:
        channel = await guild.create_text_channel("Bot Commands", overwrites=_overwrites)
        await channel.edit(topic=msg)
        await channel.edit(name="Bot Commands")
        await channel.send(f"{msg}")
    except discord.Forbidden as err:
        self.bot.log.info(f"(Server:{guild.name})(BOT IS NOT ADMIN)({err.text} to create channel: bot-commands)")
    except discord.HTTPException as err:
        self.bot.log.info(f"(Server:{guild.name})({err.text})")


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


def check_server_has_role(self, server: discord.Guild, role_name: str):
    for rol in server.roles:
        if rol.name.lower() == role_name.lower():
            return rol
    return None


def check_user_has_role(self, member: discord.Member, role_name: str):
    for rol in member.roles:
        if rol.name.lower() == role_name.lower():
            return rol
    return None


# async def skill_embed(self, skill):
#     description = None
#     if "description" in skill:
#         description = skill["description"]
#
#     url = f"https://wiki.guildwars2.com/wiki/{skill}"
#     async with self.bot.aiosession.head(url) as r:
#         if not r.status == 200:
#             url = None
#
#     data = discord.Embed(title=skill["name"], description=description, url=url)
#     if "icon" in skill:
#         data.set_thumbnail(url=skill["icon"])
#
#     if "professions" in skill:
#         if skill["professions"]:
#             professions = skill["professions"]
#             if len(professions) != 1:
#                 data.add_field(name="Professions", value=", ".join(professions))
#             elif len(professions) == 9:
#                 data.add_field(name="Professions", value="All")
#             else:
#                 data.add_field(name="Profession", value=", ".join(professions))
#
#     if "facts" in skill:
#         for fact in skill["facts"]:
#             try:
#                 if fact["type"] == "Recharge":
#                     data.add_field(name="Cooldown", value=fact["value"])
#                 if fact["type"] == "Distance" or fact["type"] == "Number":
#                     data.add_field(name=fact["text"], value=fact["value"])
#                 if fact["type"] == "ComboField":
#                     data.add_field(name=fact["text"], value=fact["field_type"])
#             except:
#                 pass
#
#     return data
