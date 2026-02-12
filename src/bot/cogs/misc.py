import discord
import random
import sys
from discord.ext import commands
from gtts import gTTS
from io import BytesIO
from src.bot.constants import messages, variables
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils, chat_formatting
from src.bot.tools.cooldowns import CoolDowns
from src.bot.tools.pepe import pepedatabase


class Misc(commands.Cog):
    """Miscellaneous bot commands for entertainment and server utilities."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._random = random.SystemRandom()

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, commands.BucketType.user)
    async def pepe(self, ctx: commands.Context) -> None:
        """Post a random Pepe image from the database.

        Usage:
            pepe
        """
        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        pepe_url = self._random.choice(pepedatabase)
        await ctx.send(pepe_url)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, commands.BucketType.user)
    async def tts(self, ctx: commands.Context, *, tts_text: str) -> None:
        """Generate and send text-to-speech audio file.

        Converts mentions and custom emojis to readable text format.

        Usage:
            tts Hello everyone!
            tts <@!123456789> check this out <:custom_emoji:123456789>
        """
        await ctx.message.channel.typing()

        display_filename = f"{ctx.author.display_name}.mp3"
        processed_text = self._process_tts_text(ctx, tts_text)

        if not processed_text:
            return await bot_utils.send_error_msg(ctx, messages.INVALID_MESSAGE)

        mp3_buffer = BytesIO()
        try:
            tts = gTTS(text=processed_text, lang="en", slow=False, timeout=10)
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)

            await ctx.send(file=discord.File(mp3_buffer, display_filename))
        except AssertionError:
            await bot_utils.send_error_msg(ctx, messages.INVALID_MESSAGE)
        finally:
            mp3_buffer.close()

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, commands.BucketType.user)
    async def echo(self, ctx: commands.Context, *, msg: str) -> None:
        """Echo a message back to the channel.

        Usage:
            echo Hello world!
        """
        await ctx.message.channel.typing()
        await bot_utils.send_msg(ctx, msg)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, commands.BucketType.user)
    async def ping(self, ctx: commands.Context) -> None:
        """Test bot latency and response time.

        Usage:
            ping
        """
        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        latency_ms = int(self.bot.ws.latency * 1000)
        color = discord.Color.green() if latency_ms <= 200 else discord.Color.red()

        embed = discord.Embed(description=f"Ping: {latency_ms} ms", color=color)
        await bot_utils.send_embed(ctx, embed)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, commands.BucketType.user)
    async def lmgtfy(self, ctx: commands.Context, *, user_msg: str) -> None:
        """Create a 'Let Me Google That For You' link.

        Usage:
            lmgtfy how to code in python
        """
        await ctx.message.channel.typing()
        search_terms = user_msg.replace(" ", "+")
        lmgtfy_url = f"{variables.LMGTFY_URL}/?q={search_terms}"
        await bot_utils.send_msg(ctx, lmgtfy_url)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, commands.BucketType.user)
    async def invites(self, ctx: commands.Context) -> None:
        """List all active invite links for the current server.

        Usage:
            invites
        """
        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        server = ctx.guild
        active_invites = await server.invites()

        invite_categories = self._categorize_invites(active_invites)

        if not any(invite_categories.values()):
            return await bot_utils.send_msg(ctx, chat_formatting.inline(messages.NO_INVITES))

        embed = discord.Embed(title=messages.INVITE_TITLE)
        embed.set_thumbnail(url=server.icon.url)

        self._add_invite_fields(embed, invite_categories)
        await bot_utils.send_embed(ctx, embed)
        return None

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, commands.BucketType.user)
    async def serverinfo(self, ctx: commands.Context) -> None:
        """Display comprehensive information about the current server.

        Usage:
            serverinfo
        """
        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        server = ctx.guild

        # Calculate member statistics
        stats = self._calculate_server_stats(server)

        # Format creation date
        now = bot_utils.get_current_date_time()
        created_str = bot_utils.convert_datetime_to_str_long(server.created_at)
        days_ago = (now - server.created_at).days
        created_at = f"Created {created_str}. That's over {days_ago} days ago!"

        embed = discord.Embed(description=created_at)
        self._add_server_info_fields(embed, server, stats)

        embed.set_footer(text=f"Server ID: {server.id} | {created_str}")

        if server.icon and server.icon.url:
            embed.set_author(name=server.name, url=server.icon.url)
            embed.set_thumbnail(url=server.icon.url)
        else:
            embed.set_author(name=server.name)

        await bot_utils.send_embed(ctx, embed)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, commands.BucketType.user)
    async def userinfo(self, ctx: commands.Context, *, member_str: str | None = None) -> None:
        """Display detailed information about a user.

        Usage:
            userinfo (shows your info)
            userinfo @username
            userinfo username
        """
        await ctx.message.channel.typing()

        # Determine target user
        user = None
        if member_str:
            user = bot_utils.get_object_member_by_str(ctx, member_str)

        if not user:
            user = ctx.author

        user_info = self._get_user_info(ctx.guild, user)
        activity_description = self._get_activity_description(user)

        embed = discord.Embed(description=activity_description, color=user.color)
        self._add_user_info_fields(embed, user_info)

        display_name = f"{user} ~ {user.nick}" if user.nick else str(user)

        if user.avatar and user.avatar.url:
            embed.set_author(name=display_name, url=user.avatar.url)
            embed.set_thumbnail(url=user.avatar.url)
        else:
            embed.set_author(name=display_name)

        await bot_utils.send_embed(ctx, embed)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, commands.BucketType.user)
    async def about(self, ctx: commands.Context) -> None:
        """Display comprehensive information about the bot.

        Usage:
            about
        """
        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()

        bot_avatar = self.bot.user.avatar.url if self.bot.user.avatar else None
        author = self.bot.get_user(self.bot.owner_id)
        python_version = f"Python {'.'.join(map(str, sys.version_info[:3]))}"
        games_included = self._get_games_included(variables.GAMES_INCLUDED)
        dev_info_msg = messages.DEV_INFO_MSG.format(variables.BOT_WEBPAGE_URL, variables.DISCORDPY_URL)

        bot_stats = bot_utils.get_bot_stats(self.bot)

        embed = discord.Embed(description=str(self.bot.description))
        embed.set_author(
            name=f"{self.bot.user.name} v{variables.VERSION}",
            icon_url=bot_avatar,
            url=variables.BOT_WEBPAGE_URL,
        )
        embed.set_thumbnail(url=bot_avatar)

        if author and author.avatar:
            embed.set_footer(icon_url=author.avatar.url, text=f"Developed by {author} | {python_version}")

        self._add_about_fields(embed, dev_info_msg, bot_stats, games_included, ctx.prefix)
        await bot_utils.send_embed(ctx, embed)

    def _process_tts_text(self, ctx: commands.Context, text: str) -> str:
        """Process TTS text to convert mentions and emojis to readable format."""
        if not self._has_special_tokens(text):
            return text

        processed_parts = []
        for word in text.split():
            processed_word = self._process_word(ctx, word)
            processed_parts.append(processed_word)

        return " ".join(processed_parts)

    @staticmethod
    def _has_special_tokens(text: str) -> bool:
        """Check if text contains mentions or custom emojis."""
        return "<@!" in text or "<:" in text

    def _process_word(self, ctx: commands.Context, word: str) -> str:
        """Process a single word for mentions and emojis."""
        if self._is_user_mention(word):
            return self._process_user_mention(ctx, word)
        elif self._is_custom_emoji(word):
            return self._process_custom_emoji(word)
        else:
            return word

    @staticmethod
    def _is_user_mention(word: str) -> bool:
        """Check if word is a user mention."""
        return word.startswith("<@!") and word.endswith(">")

    @staticmethod
    def _is_custom_emoji(word: str) -> bool:
        """Check if word is a custom emoji."""
        return word.startswith("<:") and word.endswith(">") and ":" in word

    @staticmethod
    def _process_user_mention(ctx: commands.Context, word: str) -> str:
        """Process user mention to readable format."""
        try:
            member_id = word.strip("<@!>")
            member = ctx.guild.get_member(int(member_id))
            return f"@{member.display_name}" if member else word
        except ValueError:
            return word

    @staticmethod
    def _process_custom_emoji(word: str) -> str:
        """Process custom emoji to readable format."""
        try:
            emoji_parts = word.split(":")
            if len(emoji_parts) >= 3 and len(emoji_parts[2].rstrip(">")) >= 18:
                return emoji_parts[1]
            return word
        except IndexError, ValueError:
            return word

    @staticmethod
    def _categorize_invites(invites: list) -> dict[str, list[str]]:
        """Categorize server invites by type."""
        categories = {"revoked": [], "unlimited": [], "limited": []}

        for invite in invites:
            if invite.revoked:
                categories["revoked"].append(f"~~{invite.code}: `{invite.channel}` created by `{invite.inviter}`~~")
            elif invite.max_age == 0:
                categories["unlimited"].append(
                    f"[`{invite.code}`]({invite.url}): `{invite.channel}` created by `{invite.inviter}`"
                )
            else:
                categories["limited"].append(
                    f"[`{invite.code}`]({invite.url}): `{invite.channel}` created by `{invite.inviter}`"
                )

        return categories

    @staticmethod
    def _add_invite_fields(embed: discord.Embed, categories: dict[str, list[str]]) -> None:
        """Add invite category fields to embed."""
        if categories["unlimited"]:
            embed.add_field(
                name=f"{messages.UNLIMITED_INVITES} ({len(categories['unlimited'])})",
                value="\n".join(categories["unlimited"][:5]),
            )
        if categories["limited"]:
            embed.add_field(
                name=f"{messages.TEMPORARY_INVITES} ({len(categories['limited'])})",
                value="\n".join(categories["limited"]),
            )
        if categories["revoked"]:
            embed.add_field(
                name=f"{messages.REVOKED_INVITES} ({len(categories['revoked'])})",
                value="\n".join(categories["revoked"]),
            )

    @staticmethod
    def _calculate_server_stats(server: discord.Guild) -> dict[str, int]:
        """Calculate various server statistics."""
        online_count = sum(
            1 for member in server.members if member.status in (discord.Status.online, discord.Status.idle)
        )

        user_count = sum(1 for member in server.members if not member.bot)
        bot_count = sum(1 for member in server.members if member.bot)

        return {
            "online": online_count,
            "users": user_count,
            "bots": bot_count,
            "text_channels": len(server.text_channels),
            "voice_channels": len(server.voice_channels),
        }

    @staticmethod
    def _add_server_info_fields(embed: discord.Embed, server: discord.Guild, stats: dict[str, int]) -> None:
        """Add server information fields to embed."""
        embed.add_field(name="Users", value=str(stats["users"]))
        embed.add_field(name="Online", value=str(stats["online"]))
        embed.add_field(name="Offline", value=str(stats["users"] - stats["online"]))
        embed.add_field(name="Bots", value=str(stats["bots"]))
        embed.add_field(name="Text Channels", value=str(stats["text_channels"]))
        embed.add_field(name="Voice Channels", value=str(stats["voice_channels"]))
        embed.add_field(name="Roles", value=str(len(server.roles)))
        embed.add_field(name="Owner", value=str(server.owner))
        embed.add_field(name="Emojis", value=str(len(server.emojis)))

    @staticmethod
    def _get_user_info(guild: discord.Guild, user: discord.Member) -> dict:
        """Get comprehensive user information."""
        now = bot_utils.get_current_date_time()
        joined_at = user.joined_at

        since_created = (now - user.created_at).days
        since_joined = (now - joined_at).days

        user_joined = joined_at.strftime("%d %b %Y %H:%M")
        user_created = user.created_at.strftime("%d %b %Y %H:%M")

        member_number = sorted(guild.members, key=lambda m: m.joined_at).index(user) + 1

        roles_list = sorted([role.name for role in user.roles if role.name != "@everyone"])
        roles_str = ", ".join(roles_list) if roles_list else "None"

        return {
            "created_on": f"{user_created}\n({since_created} days ago)",
            "joined_on": f"{user_joined}\n({since_joined} days ago)",
            "member_number": member_number,
            "roles": roles_str,
            "user_id": user.id,
        }

    @staticmethod
    def _get_activity_description(user: discord.Member) -> str:
        """Get user activity description."""
        if user.activity:
            match user.activity.type:
                case discord.ActivityType.playing:
                    return f"Playing {user.activity.name}"
                case discord.ActivityType.streaming:
                    return f"Streaming: [{user.activity.name}]({user.activity.details})"
                case _:
                    return str(user.status)
        elif user.status == discord.Status.dnd:
            return messages.DO_NOT_DISTURB
        else:
            return str(user.status)

    @staticmethod
    def _add_user_info_fields(embed: discord.Embed, user_info: dict) -> None:
        """Add user information fields to embed."""
        embed.add_field(name=messages.JOINED_DISCORD_ON, value=user_info["created_on"])
        embed.add_field(name=messages.JOINED_THIS_SERVER_ON, value=user_info["joined_on"])
        embed.add_field(name="Roles", value=user_info["roles"], inline=False)
        embed.set_footer(
            text=f"Member #{user_info['member_number']} | "
            f"User ID: {user_info['user_id']} | "
            f"{bot_utils.get_current_date_time_str_long()}"
        )

    @staticmethod
    def _add_about_fields(
        embed: discord.Embed,
        dev_info: str,
        stats: dict,
        games: str | None,
        prefix: str,
    ) -> None:
        """Add about information fields to embed."""
        embed.add_field(name="Development Info", value=dev_info, inline=False)
        embed.add_field(name="Servers", value=stats["servers"])
        embed.add_field(name="Users", value=stats["users"])
        embed.add_field(name="Channels", value=stats["channels"])

        if games:
            embed.add_field(name="Games Included", value=games, inline=False)

        embed.add_field(name="Download", value=f"[Version {variables.VERSION}]({variables.BOT_WEBPAGE_URL})")
        embed.add_field(name="Donations", value=f"[Paypal]({variables.PAYPAL_URL})")
        embed.add_field(name="Help", value=f"{messages.LIST_COMMAND_CATEGORIES}: `{prefix}help`", inline=False)

    @staticmethod
    def _get_games_included(games_tuple: tuple[str, ...]) -> str | None:
        """Format games included string from tuple."""
        if not games_tuple:
            return None

        if len(games_tuple) == 1:
            return games_tuple[0]
        else:
            return " ".join(f"({game})" for game in games_tuple)

    # @commands.command()
    # async def test(self, ctx):
    #     """(test)"""
    #
    #     msg = "test"
    #     color = discord.Color.red()
    #     embed = discord.Embed(color=color, description=msg)
    #     embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
    #     embed.set_footer(icon_url=ctx.bot.user.avatar.url, text=f"{bot_utils.get_current_date_time_str_long()} UTC")
    #     await bot_utils.send_embed(ctx, embed, True)


async def setup(bot: Bot) -> None:
    """Setup function to add the Misc cog to the bot."""
    await bot.add_cog(Misc(bot))
