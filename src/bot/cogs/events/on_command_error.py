import discord
from discord.ext import commands
from src.bot.constants import messages, variables
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils
from src.gw2.constants import gw2_messages


class ErrorContext:
    """Container for error context information."""

    def __init__(self, ctx: commands.Context, error: Exception):
        self.ctx = ctx
        self.error = error
        self.command = self._build_command_string(ctx)
        self.error_msg = ""
        self.bad_argument = None

    def _build_command_string(self, ctx: commands.Context) -> str:
        """Build the full command string including subcommands."""
        if ctx.command is None:
            # For non-existent commands, extract from message content
            message_parts = ctx.message.content.strip().split()
            if message_parts:
                return message_parts[0]  # Return the full command including prefix
            return f"{ctx.prefix}unknown"

        command = str(ctx.command)
        if ctx.subcommand_passed is not None:
            command = f"{command} {ctx.subcommand_passed}"
        return f"{ctx.prefix}{command}"

    @property
    def help_command(self) -> str:
        """Get the help command string."""
        base_command = self.command.replace(self.ctx.prefix, "")
        return f"{self.ctx.prefix}help {base_command}"


class ErrorMessageBuilder:
    """Builds appropriate error messages for different error types."""

    @staticmethod
    def get_error_message(error: Exception) -> str:
        """Extract error message from exception."""
        if hasattr(error, "args") and len(error.args) > 0:
            error_msg = error.args[0]
            if "Command raised an exception" in str(error_msg):
                return error_msg.split(f"{messages.COMMAND_RAISED_EXCEPTION}:")[1]
            return str(error_msg)
        elif hasattr(error, "original") and hasattr(error.original, "args"):
            return str(error.original.args[0])
        return str(error)

    @staticmethod
    def build_command_not_found(context: ErrorContext) -> str:
        """Build message for command not found error."""
        return f"{messages.COMMAND_NOT_FOUND}:\n`{context.command}`"

    @staticmethod
    def build_missing_argument(context: ErrorContext) -> str:
        """Build message for missing required argument error."""
        return f"{messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE}: `{context.help_command}`"

    @staticmethod
    def build_check_failure(context: ErrorContext) -> str:
        """Build message for check failure error."""
        if "not admin" in context.error_msg:
            return f"{messages.NOT_ADMIN_USE_COMMAND}: `{context.command}`"
        elif "not owner" in context.error_msg:
            return f"{messages.BOT_OWNERS_ONLY_COMMAND}: `{context.command}`"
        return context.error_msg

    @staticmethod
    def build_bad_argument(context: ErrorContext) -> str:
        """Build message for bad argument error."""
        if "bot_prefix" in context.error_msg:
            base_msg = f"{messages.PREFIXES_CHOICE}: {' '.join(variables.ALLOWED_PREFIXES)}"
        elif "Gw2ConfigServer" in context.error_msg:
            base_msg = (
                f"{gw2_messages.GW2_SERVER_NOT_FOUND}: `{context.bad_argument}`\n"
                f"{gw2_messages.GW2_SERVER_MORE_INFO}: `{context.ctx.prefix}gw2 worlds`"
            )
        else:
            base_msg = f"{messages.UNKNOWN_OPTION}: `{context.bad_argument}`"

        return f"{base_msg}\n{messages.HELP_COMMAND_MORE_INFO}: `{context.help_command}`"

    @staticmethod
    def build_command_invoke_error(context: ErrorContext) -> str:
        """Build message for command invoke error."""
        error_conditions = {
            ("Cannot send messages to this user", "status code: 403"): messages.DIRECT_MESSAGES_DISABLED,
            ("AttributeError",): f"{messages.COMMAND_ERROR}: `{context.command}`",
            ("Missing Permissions",): f"{messages.NO_PERMISSION_EXECUTE_COMMAND}: `{context.command}`",
            (
                "NoOptionError",
            ): f"{messages.NO_OPTION_FOUND}: `{context.error_msg.split()[7] if len(context.error_msg.split()) > 7 else 'unknown'}`",
            ("GW2 API",): (
                str(context.error_msg).split(',')[1].strip().split('?')[0]
                if ',' in str(context.error_msg) and len(str(context.error_msg).split(',')) > 1
                else str(context.error_msg)
            ),
            ("No text to send to TTS API",): messages.INVALID_MESSAGE,
        }

        for conditions, message in error_conditions.items():
            if any(condition in context.error_msg for condition in conditions):
                base_msg = message
                break
        else:
            base_msg = f"{messages.COMMAND_INTERNAL_ERROR}: `{context.command}`"

        return f"{base_msg}\n{messages.HELP_COMMAND_MORE_INFO}: `{context.help_command}`"

    @staticmethod
    def build_forbidden_error(context: ErrorContext) -> str:
        """Build message for forbidden error."""
        if "Cannot execute action on a DM channel" in context.error_msg:
            return messages.DM_CANNOT_EXECUTE_COMMAND
        return messages.PRIVILEGE_LOW


class Errors(commands.Cog):
    """Commands error handler with improved structure and maintainability."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.message_builder = ErrorMessageBuilder()

        @bot.event
        async def on_command_error(ctx: commands.Context, error: Exception) -> None:
            """Handle command errors with appropriate responses."""
            context = ErrorContext(ctx, error)
            context.error_msg = self.message_builder.get_error_message(error)

            # Error type handlers mapping
            handlers = {
                commands.NoPrivateMessage: (self._handle_no_private_message, True),
                commands.CommandNotFound: (self._handle_command_not_found, False),
                commands.MissingRequiredArgument: (self._handle_missing_argument, False),
                commands.CheckFailure: (self._handle_check_failure, True),
                commands.BadArgument: (self._handle_bad_argument, False),
                commands.CommandError: (self._handle_command_error, True),
                commands.CommandInvokeError: (self._handle_command_invoke_error, True),
                commands.CommandOnCooldown: (self._handle_command_on_cooldown, False),
                commands.TooManyArguments: (self._handle_too_many_arguments, False),
                discord.Forbidden: (self._handle_forbidden, True),
            }

            handler, should_log = handlers.get(type(error), (self._handle_unknown_error, True))
            await handler(context, should_log)

    @staticmethod
    async def _send_error_message(ctx: commands.Context, error_msg: str, should_log: bool) -> None:
        """Send an error message to user and optionally log it."""
        await bot_utils.send_error_msg(ctx, error_msg)
        if should_log:
            log_msg = f"({error_msg}) ({ctx.message.content}) ({ctx.message.author})"
            if ctx.guild is not None:
                log_msg += f"(Server[{ctx.guild.name}:{ctx.guild.id}])"
            log_msg += f"(Channel[{ctx.message.channel}:{ctx.message.channel.id}])"
            ctx.bot.log.error(log_msg)

    async def _handle_no_private_message(self, context: ErrorContext, should_log: bool) -> None:
        """Handle NoPrivateMessage error."""
        await self._send_error_message(context.ctx, context.error_msg, should_log)

    async def _handle_command_not_found(self, context: ErrorContext, should_log: bool) -> None:
        """Handle CommandNotFound error."""
        error_msg = self.message_builder.build_command_not_found(context)
        await self._send_error_message(context.ctx, error_msg, should_log)

    async def _handle_missing_argument(self, context: ErrorContext, should_log: bool) -> None:
        """Handle MissingRequiredArgument error."""
        error_msg = self.message_builder.build_missing_argument(context)
        await self._send_error_message(context.ctx, error_msg, should_log)

    async def _handle_check_failure(self, context: ErrorContext, should_log: bool) -> None:
        """Handle CheckFailure error."""
        error_msg = self.message_builder.build_check_failure(context)
        await self._send_error_message(context.ctx, error_msg, should_log)

    async def _handle_bad_argument(self, context: ErrorContext, should_log: bool) -> None:
        """Handle BadArgument error."""
        # Extract bad argument from message content
        if context.error_msg == "BadArgument_Gw2ConfigStatus":
            context.bad_argument = context.ctx.message.clean_content.split()[3]
        elif context.error_msg == "BadArgument_Gw2ConfigServer":
            bad_server_list = context.ctx.message.clean_content.split()[4:]
            context.bad_argument = " ".join(bad_server_list)
        else:
            context.bad_argument = context.ctx.message.clean_content.replace(context.command, "").strip()

        error_msg = self.message_builder.build_bad_argument(context)
        await self._send_error_message(context.ctx, error_msg, should_log)

    async def _handle_command_error(self, context: ErrorContext, should_log: bool) -> None:
        """Handle CommandError."""
        error_msg = f"CommandError: {context.error_msg}"
        await self._send_error_message(context.ctx, error_msg, should_log)

    async def _handle_command_invoke_error(self, context: ErrorContext, should_log: bool) -> None:
        """Handle CommandInvokeError."""
        error_msg = self.message_builder.build_command_invoke_error(context)
        await self._send_error_message(context.ctx, error_msg, should_log)

    async def _handle_command_on_cooldown(self, context: ErrorContext, should_log: bool) -> None:
        """Handle CommandOnCooldown error."""
        # Delete message for sensitive commands
        sensitive_commands = (
            "gw2 key add",
            "gw2 key remove",
            "gw2 key info",
            "gw2 key activate",
            "cc add",
            "cc edit",
            "customcom add",
            "customcom edit",
        )

        if any(cmd in context.ctx.message.content.lower() for cmd in sensitive_commands):
            await bot_utils.delete_message(context.ctx)

        error_msg = f"{context.error_msg}\nCommand: `{context.command}`"
        await self._send_error_message(context.ctx, error_msg, should_log)

    async def _handle_too_many_arguments(self, context: ErrorContext, should_log: bool) -> None:
        """Handle TooManyArguments error."""
        error_msg = f"{messages.COMMAND_ERROR}!\n {messages.HELP_COMMAND_MORE_INFO}: `{context.help_command}`"
        await self._send_error_message(context.ctx, error_msg, should_log)

    async def _handle_forbidden(self, context: ErrorContext, should_log: bool) -> None:
        """Handle Forbidden error."""
        error_msg = self.message_builder.build_forbidden_error(context)
        await self._send_error_message(context.ctx, error_msg, should_log)

    async def _handle_unknown_error(self, context: ErrorContext, should_log: bool) -> None:
        """Handle unknown error types."""
        await self._send_error_message(context.ctx, context.error_msg, should_log)


async def setup(bot: Bot) -> None:
    """Setup function to add the Errors cog to the bot."""
    await bot.add_cog(Errors(bot))
