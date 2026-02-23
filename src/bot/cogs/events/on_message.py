import discord
from discord.ext import commands
from src.bot.constants import messages
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils, chat_formatting
from src.database.dal.bot.custom_commands_dal import CustomCommandsDal
from src.database.dal.bot.servers_dal import ServersDal


class MessageContext:
    """Container for message processing context."""

    def __init__(self, ctx: commands.Context, is_command: bool):
        self.ctx = ctx
        self.is_command = is_command
        self.is_dm = isinstance(ctx.channel, discord.DMChannel)
        self.server_configs = None


class MessageValidator:
    """Validates messages and checks various conditions."""

    @staticmethod
    def has_content(message: discord.Message) -> bool:
        """Check if the message has content."""
        return len(message.content) > 0

    @staticmethod
    def is_bot_message(author: discord.Member) -> bool:
        """Check if the message is from a bot."""
        return author.bot

    @staticmethod
    def is_command(ctx: commands.Context) -> bool:
        """Check if the message is a command."""
        return ctx.prefix is not None

    @staticmethod
    def is_member_invisible(ctx: commands.Context) -> bool:
        """Check if member status is offline/invisible."""
        return ctx.author.status == discord.Status.offline

    @staticmethod
    def has_double_prefix(message: discord.Message) -> bool:
        """Check if message has double prefix (should be ignored)."""
        if len(message.content) < 2:
            return False
        second_char = message.content[1:2]
        return not second_char.isalpha()


class ProfanityFilter:
    """Handles profanity filtering and censoring."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def check_and_censor(self, ctx: commands.Context) -> bool:
        """Check for profanity and censor if found. Returns True if censored."""
        user_msg = ctx.message.system_content

        if not self.bot.profanity.contains_profanity(user_msg):
            return False

        try:
            await self._censor_message(ctx, user_msg)
            return True
        except Exception as e:
            self._log_filter_error(ctx, user_msg, e)
            return True

    async def _censor_message(self, ctx: commands.Context, user_msg: str) -> None:
        """Censor the message and send replacement."""
        censored_text = self.bot.profanity.censor(user_msg, "#")
        await bot_utils.delete_message(ctx)
        await ctx.message.channel.send(censored_text)

        # Send censorship notification
        embed = discord.Embed(title="", color=discord.Color.red(), description=messages.MESSAGE_CENSURED)
        embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.display_avatar.url)

        try:
            await ctx.message.channel.send(embed=embed)
        except discord.HTTPException:
            await ctx.message.channel.send(f"{ctx.message.author.mention} {messages.MESSAGE_CENSURED}")

        self._log_censored_message(ctx, user_msg)

    def _log_censored_message(self, ctx: commands.Context, user_msg: str) -> None:
        """Log censored message details."""
        self.bot.log.info(
            f"(Server:{ctx.message.guild.name})"
            f"(Channel:{ctx.message.channel})"
            f"(Author:{ctx.message.author})"
            f"(Message:{user_msg})"
        )

    def _log_filter_error(self, ctx: commands.Context, user_msg: str, error: Exception) -> None:
        """Log profanity filter error."""
        error_msg = f"Profanity filter is ON\nbut {messages.BOT_MISSING_MANAGE_MESSAGES_PERMISSION}"
        self.bot.log.info(
            f"(Server:{ctx.message.guild.name})"
            f"(Channel:{ctx.message.channel})"
            f"(Author:{ctx.message.author})"
            f"(Message:{user_msg})"
            f"(Error:{error_msg} | {error})"
        )


class CustomReactionHandler:
    """Handles custom bot reactions to messages."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def check_and_react(self, message: discord.Message) -> bool:
        """Check for custom reactions and respond. Returns True if reacted."""
        msg_content = message.system_content.lower()
        reaction_words = self.bot.settings["bot"]["BotReactionWords"]
        reaction_words.append("🖕")

        has_reaction_word = any(word in msg_content.split() for word in reaction_words)
        has_bot_mention = self._has_bot_mention(message, msg_content)

        # Always react in DMs
        if isinstance(message.channel, discord.DMChannel):
            has_bot_mention = True

        if has_reaction_word and has_bot_mention:
            response = self._get_reaction_response(msg_content, reaction_words)
            await self._send_reaction_message(message, response)
            return True

        return False

    def _has_bot_mention(self, message: discord.Message, msg_content: str) -> bool:
        """Check if the message mentions the bot."""
        words = msg_content.split()
        return any(word == "bot" or word == self.bot.user.mention.lower() for word in words)

    @staticmethod
    def _get_reaction_response(msg_content: str, reaction_words: list) -> str:
        """Get appropriate reaction response based on message content."""
        # Check for specific reaction words and return appropriate responses
        for word in reaction_words:
            if word in msg_content:
                if word == "stupid":
                    return messages.BOT_REACT_STUPID
                elif word == "retard":
                    return messages.BOT_REACT_RETARD
                else:
                    # Generic response for other reaction words
                    return "fu ufk!!!"

        # Default fallback response
        return "fu ufk!!!"

    @staticmethod
    async def _send_reaction_message(message: discord.Message, response: str) -> None:
        """Send a reaction message."""
        await message.channel.typing()
        description = f"{messages.BOT_REACT_EMOJIS}\n{chat_formatting.inline(response)}"
        embed = discord.Embed(color=discord.Color.red(), description=description)
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        await message.channel.send(embed=embed)


class ExclusiveUsersChecker:
    """Utility class for checking exclusive users permissions."""

    @staticmethod
    async def check_exclusive_users(bot: Bot, ctx: commands.Context) -> bool:
        """Check if user is in the exclusive users list."""
        exclusive_users = bot.settings["bot"]["ExclusiveUsers"]

        if exclusive_users is None or exclusive_users == "":
            return True

        user_id = ctx.message.author.id
        is_allowed = (
            user_id in exclusive_users if isinstance(exclusive_users, (list, tuple)) else user_id == exclusive_users
        )

        if not is_allowed:
            await bot_utils.send_error_msg(ctx, messages.PRIVATE_BOT_MESSAGE, True)

        return is_allowed


class DMMessageHandler:
    """Handles direct message processing."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.reaction_handler = CustomReactionHandler(bot)

    async def process(self, ctx: commands.Context, is_command: bool) -> None:
        """Process DM message."""
        if not is_command:
            await self._handle_dm_non_command(ctx)
        else:
            await self._handle_dm_command(ctx)

    async def _handle_dm_non_command(self, ctx: commands.Context) -> None:
        """Handle non-command DM messages."""
        # Check for custom reactions first
        if await self.reaction_handler.check_and_react(ctx.message):
            return

        if bot_utils.is_bot_owner(ctx, ctx.message.author):
            await self._send_owner_help(ctx)
        else:
            await self._send_dm_not_allowed(ctx)

    async def _handle_dm_command(self, ctx: commands.Context) -> None:
        """Handle command in DM."""
        if not await ExclusiveUsersChecker.check_exclusive_users(self.bot, ctx):
            return

        allowed_commands = self.bot.settings["bot"]["AllowedDMCommands"]

        if allowed_commands is None:
            await self._send_no_dm_commands_allowed(ctx)
            return

        user_command = ctx.message.content.split(" ", 1)[0][1:]

        if user_command in allowed_commands:
            await self.bot.process_commands(ctx.message)
        else:
            await self._send_command_not_allowed(ctx, allowed_commands)

    async def _send_owner_help(self, ctx: commands.Context) -> None:
        """Send help message to bot owner."""
        embed = discord.Embed(
            color=discord.Color.green(),
            description=chat_formatting.inline(messages.OWNER_DM_BOT_MESSAGE),
        )
        await ctx.message.author.send(embed=embed)

        owner_command = self.bot.get_command("owner")
        await ctx.author.send(chat_formatting.box(owner_command.help))

    async def _send_dm_not_allowed(self, ctx: commands.Context) -> None:
        """Send DM not allowed message."""
        embed = discord.Embed(
            color=discord.Color.red(),
            description=chat_formatting.error_inline(messages.NO_DM_MESSAGES),
        )
        await ctx.message.author.send(embed=embed)

    async def _send_no_dm_commands_allowed(self, ctx: commands.Context) -> None:
        """Send no DM commands allowed message."""
        embed = discord.Embed(
            color=discord.Color.red(),
            description=chat_formatting.error_inline(messages.DM_COMMAND_NOT_ALLOWED),
        )
        await ctx.message.author.send(embed=embed)

    async def _send_command_not_allowed(self, ctx: commands.Context, allowed_commands: list) -> None:
        """Send command not allowed message with allowed commands list."""
        embed = discord.Embed(
            color=discord.Color.red(),
            description=chat_formatting.error_inline(messages.DM_COMMAND_NOT_ALLOWED),
        )
        embed.add_field(
            name=f"{messages.DM_COMMANDS_ALLOW_LIST}:",
            value=chat_formatting.inline("\n".join(allowed_commands)),
            inline=False,
        )
        await ctx.message.author.send(embed=embed)


class ServerMessageHandler:
    """Handles server message processing."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.profanity_filter = ProfanityFilter(bot)
        self.reaction_handler = CustomReactionHandler(bot)

    async def process(self, ctx: commands.Context, is_command: bool) -> None:
        """Process server message."""
        # Get server configuration
        servers_dal = ServersDal(self.bot.db_session, self.bot.log)
        configs = await servers_dal.get_server(ctx.message.guild.id, ctx.message.channel.id)

        if not configs:
            self.bot.log.warning(messages.GET_CONFIGS_ERROR)
            if is_command:
                await self.bot.process_commands(ctx.message)
            return

        # Check invisible member blocking
        if configs["block_invis_members"] and MessageValidator.is_member_invisible(ctx):
            await self._handle_invisible_member(ctx)
            return

        if not is_command:
            await self._handle_server_non_command(ctx, configs)
        else:
            await self._handle_server_command(ctx)

    async def _handle_invisible_member(self, ctx: commands.Context) -> None:
        """Handle message from invisible member."""
        await bot_utils.delete_message(ctx)

        message_text = messages.blocked_invis_message(ctx.guild.name)
        embed = discord.Embed(
            title="",
            color=discord.Color.red(),
            description=chat_formatting.error_inline(message_text),
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

        # Try to send DM, fall back to channel, then mention
        try:
            await ctx.message.author.send(embed=embed)
        except discord.HTTPException:
            try:
                await ctx.send(embed=embed)
            except discord.HTTPException:
                await ctx.send(f"{ctx.message.author.mention} {message_text}")

    async def _handle_server_non_command(self, ctx: commands.Context, configs: dict) -> None:
        """Handle non-command server messages."""
        # Check profanity filter
        if configs["profanity_filter"]:
            if await self.profanity_filter.check_and_censor(ctx):
                return

        # Check bot reactions
        if configs["bot_word_reactions"]:
            await self.reaction_handler.check_and_react(ctx.message)

    async def _handle_server_command(self, ctx: commands.Context) -> None:
        """Handle command in server."""
        # Check for double prefix (ignore)
        if MessageValidator.has_double_prefix(ctx.message):
            return

        # Check exclusive users
        if not await ExclusiveUsersChecker.check_exclusive_users(self.bot, ctx):
            return

        # Check for custom commands
        if await self._try_custom_command(ctx):
            return

        # Process regular bot commands
        await self.bot.process_commands(ctx.message)

    async def _try_custom_command(self, ctx: commands.Context) -> bool:
        """Try to execute custom command. Returns True if executed."""
        commands_dal = CustomCommandsDal(self.bot.db_session, self.bot.log)
        command_data = await commands_dal.get_command(ctx.guild.id, str(ctx.invoked_with))

        if command_data:
            await ctx.message.channel.typing()
            await ctx.message.channel.send(command_data["description"])
            return True

        return False


class OnMessage(commands.Cog):
    """Main message event handler with improved architecture."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.dm_handler = DMMessageHandler(bot)
        self.server_handler = ServerMessageHandler(bot)

        @self.bot.event
        async def on_message(message: discord.Message) -> None:
            """Handle incoming messages."""
            # Validate message
            if not MessageValidator.has_content(message):
                return

            ctx = await bot.get_context(message)

            # Handle bot messages
            if MessageValidator.is_bot_message(ctx.author):
                await bot.process_commands(message)
                return

            # Determine if this is a command
            is_command = MessageValidator.is_command(ctx)

            # Route to appropriate handler
            if isinstance(ctx.channel, discord.DMChannel):
                await self.dm_handler.process(ctx, is_command)
            else:
                await self.server_handler.process(ctx, is_command)


async def setup(bot: Bot) -> None:
    """Setup function to add the OnMessage cog to the bot."""
    await bot.add_cog(OnMessage(bot))
