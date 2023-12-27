# -*- coding: utf-8 -*-
from discord.ext import commands
from src.bot.utils import bot_utils, constants


class Errors(commands.Cog):
    """(Commands error handler)"""
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_command_error(ctx, error):
            command = str(ctx.command)
            if ctx.subcommand_passed is not None:
                command = f"{command} {ctx.subcommand_passed}"

            error_msg = _get_error_msg(error)
            error_dict = {
                "error_msg": error_msg,
                "command": f"{ctx.prefix}{command}",
                "help_command": f"{ctx.prefix}help {command}",
                "bad_argument": None,
            }

            if isinstance(error, commands.NoPrivateMessage):
                return await _no_private_message(self, ctx, error_dict)
            elif isinstance(error, commands.CommandNotFound):
                return await _command_not_found(self, ctx, error_dict)
            elif isinstance(error, commands.MissingRequiredArgument):
                return await _missing_required_argument(self, ctx, error_dict)
            elif isinstance(error, commands.CheckFailure):
                return await _check_failure(self, ctx, error_dict)
            elif isinstance(error, commands.BadArgument):
                if error_dict["error_msg"] == "BadArgument_Gw2ConfigStatus":
                    error_dict["bad_argument"] = ctx.message.clean_content.split()[3]
                    error_dict["error_msg"] = "BadArgument"
                elif error_dict["error_msg"] == "BadArgument_Gw2ConfigServer":
                    bad_server_list = ctx.message.clean_content.split()[4:]
                    error_dict["bad_argument"] = ' '.join(bad_server_list)
                else:
                    error_dict["bad_argument"] = ctx.message.clean_content.replace(error_dict["command"], "").strip()
                return await _bad_argument(self, ctx, error_dict)
            elif isinstance(error, commands.CommandInvokeError):
                return await _command_invoke_error(self, ctx, error_dict)
            elif isinstance(error, commands.CommandOnCooldown):
                return await _command_on_cooldown(ctx, error_dict)
            elif isinstance(error, commands.TooManyArguments):
                return await _too_many_arguments(self, ctx, error_dict)
            elif "FORBIDDEN" in error_msg:
                return await _forbidden(self, ctx, error_dict)
            elif isinstance(error, commands.CommandError):
                return await _command_error(self, ctx, error_dict)
            else:
                _log_msg_error(self, ctx, error_msg)


async def _forbidden(self, ctx, error_dict):
    if "Cannot execute action on a DM channel" in error_dict["error_msg"]:
        await bot_utils.send_error_msg(ctx, "Cannot execute that command on a DM channel")
    else:
        await bot_utils.send_error_msg(ctx, "Your Privilege is too low.")
    _log_msg_error(self, ctx, error_dict["error_msg"])


async def _no_private_message(self, ctx, error_dict):
    await bot_utils.send_error_msg(ctx, error_dict["error_msg"])
    _log_msg_error(self, ctx, error_dict["error_msg"])


async def _command_not_found(self, ctx, error_dict):
    await bot_utils.send_error_msg(ctx, f"Command not found:\n`{error_dict['command']}`")
    error_msg = "Command not found"
    _log_msg_error(self, ctx, error_msg)


async def _missing_required_argument(self, ctx, error_dict):
    msg = f"Missing required argument!!!\nFor more info on this command: `{ctx.prefix}help {ctx.command}`"
    await bot_utils.send_error_msg(ctx, msg)
    _log_msg_error(self, ctx, error_dict["error_msg"])


async def _check_failure(self, ctx, error_dict):
    if "not admin" in error_dict["error_msg"]:
        user_msg = f"You are not an Admin to use this command:\n`{error_dict['command']}`"
        error_msg = "CheckFailure: Not Admin"
        await bot_utils.send_error_msg(ctx, user_msg)
        _log_msg_error(self, ctx, error_msg)
    elif "not owner" in error_dict["error_msg"]:
        user_msg = "Only bot owners can use this command."
        error_msg = "CheckFailure: Not Owner"
        await bot_utils.send_error_msg(ctx, user_msg)
        _log_msg_error(self, ctx, error_msg)
    elif "not music user" in error_dict["error_msg"]:
        user_msg = "You are not allowed to use any music related commands.\n" \
                   "Please talk to an Admin to add you to the whitelist."
        error_msg = "CheckFailure: Not a Music User"
        await bot_utils.send_error_msg(ctx, user_msg)
        _log_msg_error(self, ctx, error_msg)
    else:
        await bot_utils.send_error_msg(ctx, error_dict["error_msg"])
        _log_msg_error(self, ctx, error_dict["error_msg"])


async def _bad_argument(self, ctx, error_dict):
    ba_list = ["Member", "Channel"]

    if any(x in error_dict["error_msg"] for x in ba_list) and "not found" in error_dict["error_msg"]:
        await bot_utils.send_error_msg(ctx, error_dict["error_msg"])
        _log_msg_error(self, ctx, error_dict["error_msg"])
    elif "BadArgument_bot_prefix" in error_dict["error_msg"]:
        user_msg = f"Prefixes can only be one of: {' '.join(constants.ALLOWED_PREFIXES)}"
        await bot_utils.send_error_msg(ctx, user_msg)
        _log_msg_error(self, ctx, f"BadArgument:[{error_dict['error_msg']}][{error_dict['help_command']}]")
    elif "BadArgument_Gw2ConfigServer" in error_dict["error_msg"]:
        user_msg = f"Guild Wars 2 server not found: `{error_dict['bad_argument']}`\n" \
                   f"For more info on gw2 server names: `{ctx.prefix}gw2 worlds`"
        await bot_utils.send_error_msg(ctx, user_msg)
        _log_msg_error(self, ctx, f"{error_dict['error_msg']} ({user_msg})")
    elif "BadArgument" in error_dict["error_msg"]:
        user_msg = f"Unknown option: `{error_dict['bad_argument']}`\nFor more info on this command: `{error_dict['help_command']}`"
        await bot_utils.send_error_msg(ctx, user_msg)
        _log_msg_error(self, ctx,
                       f"BadArgument:[{error_dict['bad_argument']}][{error_dict['error_msg']}][{error_dict['help_command']}]")
    else:
        await bot_utils.send_error_msg(ctx, error_dict["error_msg"])
        _log_msg_error(self, ctx, error_dict["error_msg"])


async def _command_on_cooldown(ctx, error_dict):
    lst_cmds = (
        "gw2 key add",
        "gw2 key remove",
        "gw2 key info",
        "gw2 key activate",
        "cc add",
        "cc edit",
        "customcom add",
        "customcom edit"
    )

    if any(x in ctx.message.content.lower() for x in lst_cmds):
        await bot_utils.delete_message(ctx)
    await bot_utils.send_error_msg(ctx, f"{error_dict['error_msg']}\nCommand: `{error_dict['command']}`")


async def _too_many_arguments(self, ctx, error_dict):
    await bot_utils.send_error_msg(ctx, f"Command ERROR!\nFor more info type: `{error_dict['help_command']}`")
    _log_msg_error(self, ctx, error_dict["error_msg"])


async def _command_invoke_error(self, ctx, error_dict):
    if "Missing Permissions" in error_dict["error_msg"]:
        msg = f"Bot does not have permission to execute this command.\nCommand: `{error_dict['command']}`"
        await bot_utils.send_error_msg(ctx, msg)
        _log_msg_error(self, ctx, error_dict["error_msg"])
    elif "Cannot send messages to this user" in error_dict["error_msg"] \
            or "status code: 403" in error_dict["error_msg"]:
        msg = "Direct messages are disable in your configuration.\n" \
              "If you want to receive messages from Bots, " \
              "you need to enable this option under Privacy & Safety:" \
              "\"Allow direct messages from server members.\""
        await bot_utils.send_error_msg(ctx, msg)
        _log_msg_error(self, ctx, error_dict["error_msg"])
    elif "object has no attribute" in error_dict["error_msg"]:
        msg = f"There was an internal error with command:\n`{error_dict['command']}`"
        await bot_utils.send_error_msg(ctx, msg)
        _log_msg_error(self, ctx, "CommandInvokeError" + error_dict["error_msg"])
    elif "AttributeError" in error_dict["error_msg"]:
        await bot_utils.send_error_msg(ctx, f"Command error: `{error_dict['command']}`\n"
                                              f"For more info type: `{error_dict['help_command']}`")
        _log_msg_error(self, ctx, f"CommandInvokeError|AttributeError {error_dict['error_msg']}")
    elif "No such file or directory" in error_dict["error_msg"]:
        msg = f"There was an internal error with command:\n`{error_dict['command']}`"
        await bot_utils.send_error_msg(ctx, msg)
        _log_msg_error(self, ctx, f"CommandInvokeError|FileNotFoundError: {error_dict['error_msg']}")
    elif "OperationalError" in error_dict["error_msg"]:
        if "owner loadsql" in error_dict["command"]:
            i = error_dict["error_msg"].split(":")[-2:][0]
            j = error_dict["error_msg"].split(":")[-2:][1]
            error_message = str(i + j).strip(' ')
            if len(self.bot.temp) > 0:
                msg = f"Error while executing SQL query inside the file: '{self.bot.temp['sqlFileName']}'"
                sql = self.bot.temp["sql"]
            else:
                msg = "Error while executing SQL query: "
                sql = ""
            await bot_utils.send_error_msg(ctx, f"{msg}\n{error_message}", True)
            _log_msg_error(self, ctx, f"OperationalError|SQL error:({sql}){msg} {error_message}")
        else:
            msg = f"There was an internal error with command:\n`{error_dict['command']}`"
            await bot_utils.send_error_msg(ctx, msg)
            msg = f"OperationalError|SQL error: {error_dict['error_msg']}"
            _log_msg_error(self, ctx, msg)
    elif "IntegrityError" in error_dict["error_msg"]:
        msg = f"There was an internal error with command:\n`{error_dict['command']}`"
        await bot_utils.send_error_msg(ctx, msg)
        msg = f"IntegrityError|SQL error: {error_dict['error_msg']}"
        _log_msg_error(self, ctx, msg)
    elif "NoOptionError" in error_dict["error_msg"]:
        option_not_found = error_dict["error_msg"].split()[7]
        msg = f"No option found: `{option_not_found}`\n" \
              "Please check the help section for this command and try again.\n" \
              f"To get help type: `{error_dict['help_command']}`"
        await bot_utils.send_error_msg(ctx, msg)
        _log_msg_error(self, ctx, f"CommandInvokeError|NoOptionError: {error_dict['error_msg']}")
    elif "IP Address not valid." in error_dict["error_msg"]:
        await bot_utils.send_error_msg(ctx, error_dict["error_msg"])
        temp = error_dict["error_msg"].strip("\n")
        _log_msg_error(self, ctx, f"CommandInvokeError|ERROR: {temp}")
    elif "Unable to ping GW2 servers" in error_dict["error_msg"]:
        msg = "Unable to ping GW2 servers. Software Nping not found."
        await bot_utils.send_error_msg(ctx, error_dict["error_msg"])
        _log_msg_error(self, ctx, f"CommandInvokeError|ERROR: {msg}")
    elif "GW2 API" in error_dict["error_msg"]:
        msg = str(error_dict["error_msg"]).split(',')[1].strip().split('?')[0]
        await bot_utils.send_error_msg(ctx, error_dict["error_msg"])
        _log_msg_error(self, ctx, f"GW2 API|ERROR: {msg}")
    elif "No text to send to TTS API" in error_dict["error_msg"]:
        msg = "Invalid message."
        await bot_utils.send_error_msg(ctx, msg)
        _log_msg_error(self, ctx, f"CommandInvokeError|ERROR: {error_dict['error_msg']}|{msg}")
    else:
        msg = f"There was an internal error with command:\n`{error_dict['command']}`"
        await bot_utils.send_error_msg(ctx, msg)
        _log_msg_error(self, ctx, f"CommandInvokeError|ERROR: {error_dict['error_msg']}")


async def _command_error(self, ctx, error_dict):
    await bot_utils.send_error_msg(ctx, str(error_dict["error_msg"]))
    _log_msg_error(self, ctx, f"CommandError: {error_dict['error_msg']}")


def _get_error_msg(error):
    if hasattr(error, "args"):
        if len(error.args) > 0:
            if "Command raised an exception:" in str(error.args[0]):
                error_msg = error.args[0].split("Command raised an exception:")[1]
            else:
                error_msg = error.args[0]
        else:
            error_msg = str(error)
    else:
        error_msg = str(error.original.args[0])
    return error_msg


def _log_msg_error(self, ctx, error_msg: str):
    msg = f"({error_msg})" \
          f"({ctx.message.content})" \
          f"({ctx.message.author})"
    if ctx.guild is not None:
        msg += f"(Server[{ctx.guild}:{ctx.guild.id}])"
    msg += f"(Channel[{ctx.message.channel}:{ctx.message.channel.id}])"
    self.bot.log.error(msg)


async def setup(bot):
    await bot.add_cog(Errors(bot))
