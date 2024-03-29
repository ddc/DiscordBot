# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.database.dal.bot.custom_commands_dal import CustomCommandsDal
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.tools import bot_utils, chat_formatting
from src.bot.constants import messages


class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_message(message):
            if len(message.content) == 0:
                return

            ctx = await bot.get_context(message)

            if ctx.author.bot:
                await bot.process_commands(message)
                return

            if isinstance(ctx.channel, discord.DMChannel):
                await self.execute_private_msg(ctx)
            else:
                await self.execute_server_msg(ctx)

    async def execute_private_msg(self, ctx):
        is_command = True if ctx.prefix is not None else False
        if not is_command:
            custom_messages = await self._check_custom_messages(ctx.message)
            if custom_messages:
                return

            if bot_utils.is_bot_owner(ctx, ctx.message.author):
                msg = messages.OWNER_DM_BOT_MESSAGE
                embed = discord.Embed(color=discord.Color.green(), description=f"{chat_formatting.inline(msg)}")
                await ctx.message.author.send(embed=embed)

                cmd = self.bot.get_command("owner")
                await ctx.author.send(chat_formatting.box(cmd.help))
            else:
                msg = messages.NO_DM_MESSAGES
                embed = discord.Embed(color=discord.Color.red(), description=f"{chat_formatting.error_inline(msg)}")
                await ctx.message.author.send(embed=embed)
        else:
            if not await self._check_exclusive_users(ctx):
                return

            allowed_dm_commands = self.bot.settings["bot"]["AllowedDMCommands"]
            msg = messages.DM_COMMAND_NOT_ALLOWED
            if allowed_dm_commands is not None:
                user_cmd = ctx.message.content.split(" ", 1)[0][1:]

                if user_cmd in allowed_dm_commands:
                    return await self.bot.process_commands(ctx.message)

                str_allowed_dm_commands = "\n".join(allowed_dm_commands)
                embed = discord.Embed(color=discord.Color.red(), description=f"{chat_formatting.error_inline(msg)}")
                embed.add_field(name=f"{messages.DM_COMMANDS_ALLOW_LIST}:",
                                value=f"{chat_formatting.inline(str_allowed_dm_commands)}",
                                inline=False)

                await ctx.message.author.send(embed=embed)
            else:
                embed = discord.Embed(color=discord.Color.red(), description=f"{chat_formatting.error_inline(msg)}")
                await ctx.message.author.send(embed=embed)

    async def execute_server_msg(self, ctx):
        is_command = True if ctx.prefix is not None else False

        servers_dal = ServersDal(self.bot.db_session, self.bot.log)
        configs = await servers_dal.get_server(
            ctx.message.guild.id,
            ctx.message.channel.id
        )
        if not configs:
            self.bot.log.warning(messages.GET_CONFIGS_ERROR)
            if is_command:
                await self.bot.process_commands(ctx.message)
            return

        # block messages/commands from invisible members
        if configs["block_invis_members"]:
            is_member_invis = self._check_member_invisible(ctx)
            if is_member_invis:
                await bot_utils.delete_message(ctx)
                msg = messages.BLOCKED_INVIS_MESSAGE.format(ctx.guild.name)
                embed = discord.Embed(title="", color=discord.Color.red(), description=chat_formatting.error_inline(msg))
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
                try:
                    await ctx.message.author.send(embed=embed)
                except discord.HTTPException:
                    try:
                        await ctx.send(embed=embed)
                    except discord.HTTPException:
                        await ctx.send(f"{ctx.message.author.mention} {msg}")
                return

        if not is_command:
            # remove bad words on current channel
            if configs["profanity_filter"]:
                bad_word = await self._check_censured_words(ctx)
                if bad_word:
                    return

            # check for bot reactions
            if configs["bot_word_reactions"]:
                custom_messages = await self._check_custom_messages(ctx.message)
                if custom_messages:
                    return
        else:
            ignore_prefixes_characteres = await self._check_prefixes_characteres(ctx.message)
            if ignore_prefixes_characteres:
                return

            if not (await self._check_exclusive_users(ctx)):
                return

            # execute custom commands
            commands_dal = CustomCommandsDal(self.bot.db_session, self.bot.log)
            rs_command = await commands_dal.get_command(ctx.author.guild.id, str(ctx.invoked_with))
            if rs_command:
                await ctx.message.channel.typing()
                await ctx.message.channel.send(rs_command["description"])
                return

            await self.bot.process_commands(ctx.message)

    @staticmethod
    def _check_member_invisible(ctx):
        if ctx.author.status.name == "offline":
            return True
        return False

    @staticmethod
    async def _send_custom_message(message, send_msg: str):
        await message.channel.typing()
        desc = f"{messages.BOT_REACT_EMOJIS}\n{chat_formatting.inline(send_msg)}"
        embed = discord.Embed(color=discord.Color.red(), description=desc)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        await message.channel.send(embed=embed)

    @staticmethod
    async def _check_prefixes_characteres(message):
        # ignore 2 sequence of prefixes
        second_char = message.content[1:2]
        if not second_char.isalpha():
            return True

    async def _check_exclusive_users(self, ctx):
        exclusive_users_id = self.bot.settings["bot"]["ExclusiveUsers"]
        user_found = False

        if exclusive_users_id is not None:
            if isinstance(exclusive_users_id, tuple):
                for ids in exclusive_users_id:
                    if ctx.message.author.id == ids:
                        user_found = True
            else:
                if ctx.message.author.id == exclusive_users_id:
                    user_found = True

        if user_found is False and exclusive_users_id is not None:
            await bot_utils.send_error_msg(ctx, messages.PRIVATE_BOT_MESSAGE, True)
            return False

        return True

    async def _check_custom_messages(self, message):
        msg = message.system_content.lower()
        cwords = self.bot.settings["bot"]["BotReactionWords"]
        cwords.append("🖕")
        config_word_found = False
        bot_word_found_in_message = False

        # always react on DM messages
        if isinstance(message.channel, discord.DMChannel):
            bot_word_found_in_message = True

        for m in msg.split():
            if m in cwords:
                config_word_found = True
            if str(m).lower() == "bot" or str(m).lower() == self.bot.user.mention:
                bot_word_found_in_message = True

        if config_word_found is True and bot_word_found_in_message is True:
            bot_msg = "fu ufk!!!"
            if "stupid" in msg.lower():
                bot_msg = messages.BOT_REACT_STUPID
            elif "retard" in msg.lower():
                bot_msg = messages.BOT_REACT_RETARD
            await self._send_custom_message(message, bot_msg)
            return True
        return False

    async def _check_censured_words(self, ctx):
        user_msg = ctx.message.system_content
        if self.bot.profanity.contains_profanity(user_msg):
            censored_text = self.bot.profanity.censor(user_msg, "#")
            self.bot.log.info(f"(Server:{ctx.message.guild.name})"
                              f"(Channel:{ctx.message.channel})"
                              f"(Author:{ctx.message.author})"
                              f"(Message:{user_msg})")

            try:
                await bot_utils.delete_message(ctx)
                await ctx.message.channel.send(censored_text)
                msg = messages.MESSAGE_CENSURED
                embed = discord.Embed(title="", color=discord.Color.red(), description=msg)
                embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
                try:
                    await ctx.message.channel.send(embed=embed)
                except discord.HTTPException:
                    await ctx.message.channel.send(f"{ctx.message.author.mention} {msg}")
                return True
            except Exception as e:
                msg = f"Profanity filter is ON\nbut {messages.BOT_MISSING_MANAGE_MESSAGES_PERMISSION}"
                self.bot.log.info(f"(Server:{ctx.message.guild.name})"
                                  f"(Channel:{ctx.message.channel})"
                                  f"(Author:{ctx.message.author})"
                                  f"(Message:{user_msg})"
                                  f"(Error:{msg} | {str(e)})")
                return True

        return False


async def setup(bot):
    await bot.add_cog(OnMessage(bot))
