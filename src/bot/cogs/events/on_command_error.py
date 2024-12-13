# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.bot.tools import bot_utils
from src.bot.constants import variables, messages
from src.gw2.constants import gw2_messages


class Errors(commands.Cog):
    """Commands error handler"""
    def __init__(self, bot):
        self.error = None

        @bot.event
        async def on_command_error(ctx, error):
            command = str(ctx.command)
            if ctx.subcommand_passed is not None:
                command = f"{command} {ctx.subcommand_passed}"

            self.error = {
                "error_msg": await self._get_error_msg(error),
                "command": f"{ctx.prefix}{command}",
                "help_command": f"{ctx.prefix}help {command}",
                "bad_argument": None,
            }

            match type(error):
                case commands.NoPrivateMessage:
                    return await self._no_private_message(ctx, True)
                case commands.CommandNotFound:
                    return await self._command_not_found(ctx, False)
                case commands.MissingRequiredArgument:
                    return await self._missing_required_argument(ctx, False)
                case commands.CheckFailure:
                    return await self._check_failure(ctx, True)
                case commands.BadArgument:
                    return await self._bad_argument(ctx, False)
                case commands.CommandError:
                    return await self._command_error(ctx, True)
                case commands.CommandInvokeError:
                    return await self._command_invoke_error(ctx, True)
                case commands.CommandOnCooldown:
                    return await self._command_on_cooldown(ctx, False)
                case commands.TooManyArguments:
                    return await self._too_many_arguments(ctx, False)
                case discord.Forbidden:
                    return await self._forbidden(ctx, True)
                case _:
                    await self._send_error_message(ctx, self.error["error_msg"], True)

    @staticmethod
    async def _get_error_msg(error):
        if hasattr(error, "args"):
            if len(error.args) > 0:
                if "Command raised an exception" in str(error.args[0]):
                    error_msg = error.args[0].split(f"{messages.COMMAND_RAISED_EXCEPTION}:")[1]
                else:
                    error_msg = error.args[0]
            else:
                error_msg = str(error)
        else:
            error_msg = str(error.original.args[0])
        return error_msg

    @staticmethod
    async def _send_error_message(ctx, error_msg: str, log: bool):
        await bot_utils.send_error_msg(ctx, error_msg)
        if log:
            log_msg = f"({error_msg})" \
                      f"({ctx.message.content})" \
                      f"({ctx.message.author})"
            if ctx.guild is not None:
                log_msg += f"(Server[{ctx.guild}:{ctx.guild.id}])"
            log_msg += f"(Channel[{ctx.message.channel}:{ctx.message.channel.id}])"
            ctx.bot.log.error(log_msg)

    async def _no_private_message(self, ctx, log):
        await self._send_error_message(ctx, self.error["error_msg"], log)

    async def _command_not_found(self, ctx, log):
        error_msg = f"{messages.COMMAND_NOT_FOUND}:\n`{self.error['command']}`"
        await self._send_error_message(ctx, error_msg, log)

    async def _missing_required_argument(self, ctx, log):
        error_msg = f"{messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE}: `{self.error['help_command']}`"
        await self._send_error_message(ctx, error_msg, log)

    async def _check_failure(self, ctx, log):
        match self.error["error_msg"]:
            case str(x) if "not admin" in x:
                error_msg = f"{messages.NOT_ADMIN_USE_COMMAND}: `{self.error['command']}`"
            case str(x) if "not owner" in x:
                error_msg = f"{messages.BOT_OWNERS_ONLY_COMMAND}: `{self.error['command']}`"
            case _:
                error_msg = self.error["error_msg"]
        await self._send_error_message(ctx, error_msg, log)

    async def _bad_argument(self, ctx, log):
        match self.error["error_msg"]:
            case "BadArgument_Gw2ConfigStatus":
                self.error["bad_argument"] = ctx.message.clean_content.split()[3]
            case "BadArgument_Gw2ConfigServer":
                bad_server_list = ctx.message.clean_content.split()[4:]
                self.error["bad_argument"] = " ".join(bad_server_list)
            case _:
                self.error["bad_argument"] = ctx.message.clean_content.replace(self.error["command"], "").strip()

        match self.error["error_msg"]:
            case str(x) if "bot_prefix" in x:
                error_msg = f"{messages.PREFIXES_CHOICE}: {' '.join(variables.ALLOWED_PREFIXES)}"
            case str(x) if "Gw2ConfigServer" in x:
                error_msg = (f"{gw2_messages.GW2_SERVER_NOT_FOUND}: `{self.error['bad_argument']}`\n"
                             f"{gw2_messages.GW2_SERVER_MORE_INFO}: `{ctx.prefix}gw2 worlds`")
            case _:
                error_msg = f"{messages.UNKNOWN_OPTION}: `{self.error['bad_argument']}`"

        error_msg += f"\n{messages.HELP_COMMAND_MORE_INFO}: `{self.error['help_command']}`"
        await self._send_error_message(ctx, error_msg, log)

    async def _command_error(self, ctx, log):
        await self._send_error_message(ctx, f"CommandError: {self.error['error_msg']}", log)

    async def _command_invoke_error(self, ctx, log):
        cmd = self.error["command"]

        match self.error["error_msg"]:
            case str(x) if any(z in x for z in ["Cannot send messages to this user", "status code: 403"]):
                error_msg = messages.DIRECT_MESSAGES_DISABLED
            case str(x) if "AttributeError" in x:
                error_msg = f"{messages.COMMAND_ERROR}: `{cmd}`"
            case str(x) if "Missing Permissions" in x:
                error_msg = f"{messages.NO_PERMISSION_EXECUTE_COMMAND}: `{cmd}`"
            case str(x) if "NoOptionError" in x:
                option_not_found = self.error["error_msg"].split()[7]
                error_msg = f"{messages.NO_OPTION_FOUND}: `{option_not_found}`"
            case str(x) if "GW2 API" in x:
                error_msg = str(self.error["error_msg"]).split(',')[1].strip().split('?')[0]
            case str(x) if "No text to send to TTS API" in x:
                error_msg = messages.INVALID_MESSAGE
            case _:
                error_msg = f"{messages.COMMAND_INTERNAL_ERROR}: `{cmd}`"

        error_msg += f"\n{messages.HELP_COMMAND_MORE_INFO}: `{self.error['help_command']}`"
        await self._send_error_message(ctx, error_msg, log)

    async def _command_on_cooldown(self, ctx, log):
        delete_lst_cmds = (
            "gw2 key add",
            "gw2 key remove",
            "gw2 key info",
            "gw2 key activate",
            "cc add",
            "cc edit",
            "customcom add",
            "customcom edit"
        )

        if any(x in ctx.message.content.lower() for x in delete_lst_cmds):
            await bot_utils.delete_message(ctx)

        error_msg = f"{self.error['error_msg']}\nCommand: `{self.error['command']}`"
        await self._send_error_message(ctx, error_msg, log)

    async def _too_many_arguments(self, ctx, log):
        error_msg = (f"{messages.COMMAND_ERROR}!\n"
                     f"{messages.HELP_COMMAND_MORE_INFO}: `{self.error['help_command']}`")
        await self._send_error_message(ctx, error_msg, log)

    async def _forbidden(self, ctx, log):
        if "Cannot execute action on a DM channel" in self.error["error_msg"]:
            error_msg = messages.DM_CANNOT_EXECUTE_COMMAND
        else:
            error_msg = messages.PRIVILEGE_LOW
        await self._send_error_message(ctx, error_msg, log)


async def setup(bot):
    await bot.add_cog(Errors(bot))
