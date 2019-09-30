#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from discord.ext import commands
from .utils import bot_utils as utils


class Errors(commands.Cog):
    """(Commands error handler)"""

    def __init__(self, bot):
        self.bot = bot

        ################################################################################
        @bot.event
        async def on_command_error(ctx, error):
            if ctx.subcommand_passed is None:
                command = f"{ctx.prefix}{ctx.invoked_with}"
                help_command = f"{ctx.prefix}help {ctx.invoked_with}"
            else:
                cmd = ctx.view.buffer.split(' ', 1)[0][1:]
                command = f"{ctx.prefix}{cmd} {ctx.subcommand_passed}"
                help_command = f"{ctx.prefix}help {cmd} {ctx.subcommand_passed}"

            errorMsg = _get_error_msg(error)
            errorObj = utils.Object()
            errorObj.errorMsg = errorMsg
            errorObj.command = command
            errorObj.help_command = help_command

            if isinstance(error, commands.NoPrivateMessage):
                return await _noPrivateMessage(self, ctx, errorObj)
            elif isinstance(error, commands.CommandNotFound):
                return await _commandNotFound(self, ctx, errorObj)
            elif isinstance(error, commands.MissingRequiredArgument):
                return await _missingRequiredArgument(self, ctx, errorObj)
            elif isinstance(error, commands.CheckFailure):
                return await _checkFailure(self, ctx, errorObj)
            elif isinstance(error, commands.BadArgument):
                if errorObj.errorMsg == "BadArgument_Gw2ConfigStatus":
                    errorObj.bad_argument = ctx.message.clean_content.split()[3]
                    errorObj.errorMsg = "BadArgument"
                elif errorObj.errorMsg == "BadArgument_Gw2ConfigServer":
                    bad_server_list = ctx.message.clean_content.split()[4:]
                    errorObj.bad_argument = ' '.join(bad_server_list)
                else:
                    l = len(ctx.message.clean_content.split()) - 1
                    errorObj.bad_argument = ctx.message.clean_content.split()[l]
                return await _badArgument(self, ctx, errorObj)
            elif isinstance(error, commands.CommandInvokeError):
                return await _commandInvokeError(self, ctx, errorObj)
            elif isinstance(error, commands.CommandOnCooldown):
                return await _commandOnCooldown(self, ctx, errorObj)
            elif isinstance(error, commands.TooManyArguments):
                return await _tooManyArguments(self, ctx, errorObj)
            elif "FORBIDDEN" in errorMsg:
                return await _forbidden(self, ctx, errorObj)
            elif isinstance(error, commands.CommandError):
                return await _commandError(self, ctx, errorObj)
            else:
                _log_msg_error(self, ctx, errorMsg)


################################################################################
async def _forbidden(self, ctx, errorObj: object):
    if "Cannot execute action on a DM channel" in errorObj.errorMsg:
        await utils.send_error_msg(self, ctx, "Cannot execute that command on a DM channel")
    else:
        await utils.send_error_msg(self, ctx, "Your Privilege is too low.")
    _log_msg_error(self, ctx, errorObj.errorMsg)


################################################################################
async def _noPrivateMessage(self, ctx, errorObj: object):
    await utils.send_error_msg(self, ctx, errorObj.errorMsg)
    _log_msg_error(self, ctx, errorObj.errorMsg)


################################################################################
async def _commandNotFound(self, ctx, errorObj: object):
    await utils.send_error_msg(self, ctx, f"Command not found:\n`{errorObj.command}`")
    # errorMsg = errorObj.errorMsg.replace("is ","")
    errorMsg = "Command not found"
    _log_msg_error(self, ctx, errorMsg)


################################################################################
async def _missingRequiredArgument(self, ctx, errorObj: object):
    msg = f"Missing required argument!!!\nFor more info on this command use: `{ctx.prefix}help {ctx.command}`"
    await utils.send_error_msg(self, ctx, msg)
    # await ctx.send(formatting.error_inline(msg))
    # await ctx.send(formatting.box(ctx.command.help))
    _log_msg_error(self, ctx, errorObj.errorMsg)


################################################################################
async def _checkFailure(self, ctx, errorObj: object):
    if "not admin" in errorObj.errorMsg:
        user_msg = f"You are not an Admin to use this command:\n`{errorObj.command}`"
        errorMsg = "CheckFailure: Not Admin"
        await utils.send_error_msg(self, ctx, user_msg)
        _log_msg_error(self, ctx, errorMsg)
    elif "not owner" in errorObj.errorMsg:
        user_msg = f"Only the bot owner can use this command."
        errorMsg = "CheckFailure: Not Owner"
        await utils.send_error_msg(self, ctx, user_msg)
        _log_msg_error(self, ctx, errorMsg)
    elif "not music user" in errorObj.errorMsg:
        user_msg = "You are not allowed to use any music related commands.\n" \
                   "Please talk to an Admin to add you to the whitelist."
        errorMsg = "CheckFailure: Not a Music User"
        await utils.send_error_msg(self, ctx, user_msg)
        _log_msg_error(self, ctx, errorMsg)
    else:
        await utils.send_error_msg(self, ctx, errorObj.errorMsg)
        _log_msg_error(self, ctx, errorObj.errorMsg)


################################################################################
# raise commands.BadArgument(message="BadArgument")
################################################################################
async def _badArgument(self, ctx, errorObj: object):
    if "Member" in errorObj.errorMsg and "not found" in errorObj.errorMsg:
        await utils.send_error_msg(self, ctx, errorObj.errorMsg)
        _log_msg_error(self, ctx, errorObj.errorMsg)
    elif "Channel" in errorObj.errorMsg and "not found" in errorObj.errorMsg:
        await utils.send_error_msg(self, ctx, errorObj.errorMsg)
        _log_msg_error(self, ctx, errorObj.errorMsg)
    elif "BadArgument_bot_prefix" in errorObj.errorMsg:
        user_msg = "Prefixes can only be one of: ! $ % ^ & ? > < . ;"
        await utils.send_error_msg(self, ctx, user_msg)
        _log_msg_error(self, ctx, f"BadArgument:[{errorObj.errorMsg}][{errorObj.help_command}]")
    elif "BadArgument_default_text_channel" in errorObj.errorMsg:
        user_msg = f"Channel not found:\n`{errorObj.bad_argument}`"
        await utils.send_error_msg(self, ctx, user_msg)
        _log_msg_error(self, ctx, f"{errorObj.errorMsg} ({user_msg})")
    elif "BadArgument_Gw2ConfigServer" in errorObj.errorMsg:
        user_msg = f"Guild Wars 2 server not found: `{errorObj.bad_argument}`\n" \
                   f"For more info on gw2 server names use: `{ctx.prefix}gw2 worlds`"
        await utils.send_error_msg(self, ctx, user_msg)
        _log_msg_error(self, ctx, f"{errorObj.errorMsg} ({user_msg})")
    elif "BadArgument" in errorObj.errorMsg:
        # user_msg = f"BadArgument: {errorObj.bad_argument} \nType {errorObj.help_command} for more info."
        user_msg = f"Unknown option: `{errorObj.bad_argument}`\nFor more info on this command use: `{errorObj.help_command}`"
        await utils.send_error_msg(self, ctx, user_msg)
        _log_msg_error(self, ctx,
                       f"BadArgument:[{errorObj.bad_argument}][{errorObj.errorMsg}][{errorObj.help_command}]")
    else:
        await utils.send_error_msg(self, ctx, errorObj.errorMsg)
        _log_msg_error(self, ctx, errorObj.errorMsg)


################################################################################
async def _commandOnCooldown(self, ctx, errorObj: object):
    if "gw2 key add" in ctx.message.content.lower() \
            or "gw2 key remove" in ctx.message.content.lower() \
            or "gw2 key info" in ctx.message.content.lower() \
            or "gw2 key activate" in ctx.message.content.lower() \
            or "cc add" in ctx.message.content.lower() \
            or "cc edit" in ctx.message.content.lower() \
            or "customcom add" in ctx.message.content.lower() \
            or "customcom edit" in ctx.message.content.lower() \
            or "pool" in ctx.message.content.lower():
        await utils.delete_last_channel_message(self, ctx)
    await utils.send_error_msg(self, ctx, f"{errorObj.errorMsg}\nCommand: `{errorObj.command}`")
    # _log_msg_error(self, ctx,"COOLDOWN")


################################################################################
async def _tooManyArguments(self, ctx, errorObj: object):
    await utils.send_error_msg(self, ctx, f"Command ERROR!\nFor more info type: `{errorObj.help_command}`")
    _log_msg_error(self, ctx, errorObj.errorMsg)


################################################################################
# raise commands.CommandInvokeError(e="Missing Permissions")
################################################################################
async def _commandInvokeError(self, ctx, errorObj: object):
    if "Missing Permissions" in errorObj.errorMsg:
        msg = f"Bot does not have permission to execute this command.\nCommand: `{errorObj.command}`"
        await utils.send_error_msg(self, ctx, msg)
        _log_msg_error(self, ctx, errorObj.errorMsg)
    elif "Cannot send messages to this user" in errorObj.errorMsg \
            or "status code: 403" in errorObj.errorMsg:
        msg = "Direct messages are disable in your configuration.\n" \
              "If you want to receive messages from Bots, " \
              "you need to enable this option under Privacy & Safety:" \
              "\"Allow direct messages from server members.\""
        await utils.send_error_msg(self, ctx, msg)
        _log_msg_error(self, ctx, errorObj.errorMsg)
    elif "object has no attribute" in errorObj.errorMsg:
        msg = f"There was an internal error with command:\n`{errorObj.command}`"
        await utils.send_error_msg(self, ctx, msg)
        _log_msg_error(self, ctx, "CommandInvokeError" + errorObj.errorMsg)
    elif "AttributeError" in errorObj.errorMsg:
        await utils.send_error_msg(self, ctx, f"Command error: `{errorObj.command}`\n" \
                                              f"For more info type: `{errorObj.help_command}`")
        _log_msg_error(self, ctx, f"CommandInvokeError|AttributeError {errorObj.errorMsg}")
    elif "No such file or directory" in errorObj.errorMsg:
        msg = f"There was an internal error with command:\n`{errorObj.command}`"
        await utils.send_error_msg(self, ctx, msg)
        _log_msg_error(self, ctx, f"CommandInvokeError|FileNotFoundError: {errorObj.errorMsg}")
    elif "OperationalError" in errorObj.errorMsg:
        if "owner loadsql" in errorObj.command:
            i = errorObj.errorMsg.split(":")[-2:][0]
            j = errorObj.errorMsg.split(":")[-2:][1]
            error_message = str(i + j).strip(' ')
            if len(self.bot.temp) > 0:
                msg = f"Error while executing SQL query inside the file: '{self.bot.temp['sqlFileName']}'"
                sql = self.bot.temp["sql"]
            else:
                msg = "Error while executing SQL query: "
                sql = ""
            await utils.send_private_error_msg(self, ctx, f"{msg}\n{error_message}")
            _log_msg_error(self, ctx, f"OperationalError|SQL error:({sql}){msg} {error_message}")
        else:
            msg = f"There was an internal error with command:\n`{errorObj.command}`"
            await utils.send_error_msg(self, ctx, msg)
            msg = f"OperationalError|SQL error: {errorObj.errorMsg}"
            _log_msg_error(self, ctx, msg)
    elif "IntegrityError" in errorObj.errorMsg:
        msg = f"There was an internal error with command:\n`{errorObj.command}`"
        await utils.send_error_msg(self, ctx, msg)
        msg = f"IntegrityError|SQL error: {errorObj.errorMsg}"
        _log_msg_error(self, ctx, msg)
    elif "NoOptionError" in errorObj.errorMsg:
        option_not_found = errorObj.errorMsg.split()[7]
        msg = f"No option found: `{option_not_found}`\n" \
              "Please check the help section for this command and try again.\n" \
              f"To get help type: `{errorObj.help_command}`"
        await utils.send_error_msg(self, ctx, msg)
        _log_msg_error(self, ctx, f"CommandInvokeError|NoOptionError: {errorObj.errorMsg}")
    elif "IP Address not valid." in errorObj.errorMsg:
        await utils.send_error_msg(self, ctx, errorObj.errorMsg)
        temp = errorObj.errorMsg.strip("\n")
        _log_msg_error(self, ctx, f"CommandInvokeError|ERROR: {temp}")
    elif "Unable to ping GW2 servers" in errorObj.errorMsg:
        msg = "Unable to ping GW2 servers. Software Nping not found."
        await utils.send_error_msg(self, ctx, errorObj.errorMsg)
        _log_msg_error(self, ctx, f"CommandInvokeError|ERROR: {msg}")
    elif "GW2 API" in errorObj.errorMsg:
        msg = str(errorObj.errorMsg).split(',')[1].strip().split('?')[0]
        await utils.send_error_msg(self, ctx, errorObj.errorMsg)
        _log_msg_error(self, ctx, f"GW2 API|ERROR: {msg}")
    else:
        msg = f"There was an internal error with command:\n`{errorObj.command}`"
        await utils.send_error_msg(self, ctx, msg)
        _log_msg_error(self, ctx, f"CommandInvokeError|ERROR: {errorObj.errorMsg}")


################################################################################
async def _commandError(self, ctx, errorObj: object):
    await utils.send_error_msg(self, ctx, str(errorObj.errorMsg))
    _log_msg_error(self, ctx, f"CommandError: {errorObj.errorMsg}")


################################################################################
def _get_error_msg(error):
    if hasattr(error, "args"):
        if len(error.args) > 0:
            if "Command raised an exception:" in str(error.args[0]):
                errorMsg = error.args[0].split("Command raised an exception:")[1]
            else:
                errorMsg = error.args[0]
        else:
            errorMsg = str(error)
    else:
        errorMsg = str(error.original.args[0])
    return errorMsg


################################################################################
def _log_msg_error(self, ctx, errorMsg: str):
    msg = f"({errorMsg})" \
          f"({ctx.message.content})" \
          f"({ctx.message.author})"
    if ctx.guild is not None:
        msg += f"(Server[{ctx.guild}:{ctx.guild.id}])"
    msg += f"(Channel[{ctx.message.channel}:{ctx.message.channel.id}])"
    self.bot.log.error(msg)


################################################################################
def setup(bot):
    bot.add_cog(Errors(bot))
