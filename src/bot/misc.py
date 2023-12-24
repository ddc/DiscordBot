# -*- coding: utf-8 -*-
import random
import sys
from io import BytesIO
import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from gtts import gTTS
from data.pepe import pepedatabase
from src.bot.utils import bot_utils, chat_formatting, constants
from src.bot.utils.cooldowns import CoolDowns


class Misc(commands.Cog):
    """(Misc commands)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, BucketType.user)
    async def pepe(self, ctx):
        """Posts a random Pepe from imgur
            pepe
        """

        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        pepe_url = f"{random.choice(pepedatabase)[:-1]}.jpg"
        async with aiohttp.ClientSession() as session:
            async with session.get(pepe_url) as resp:
                if resp.status != 200:
                    return await bot_utils.send_error_msg(ctx, "Could not download pepe file...")
                data = BytesIO(await resp.read())
                data.seek(0)
                name = pepe_url.split("/")[3]
                await ctx.send(file=discord.File(data, name))
                data.close()

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, BucketType.user)
    async def tts(self, ctx, *, tts_text: str):
        """(Send TTS to current channel)
            tts Hello everyone!
        """

        await ctx.message.channel.typing()
        display_filename = f"{bot_utils.get_member_by_id(ctx.guild, ctx.message.author.id)}.mp3"
        new_tts_msg = []

        if "<@!" in tts_text or "<:" in tts_text:
            msg_text = tts_text.split(" ")
            for msg in msg_text:
                if "<@!" == msg[0:3]:
                    member_id = msg.strip(" ").strip("<@!").strip(">")
                    member = ctx.guild.get_member(int(member_id))
                    new_tts_msg.append(f"@{member.display_name}")
                elif "<:" == msg[0:2] and ">" == msg[-1]:
                    emoji_id = msg.split(":")[2].strip(">")
                    if len(emoji_id) >= 18:
                        emoji_name = msg.split(":")[1]
                        new_tts_msg.append(emoji_name)
                elif len(msg) > 0:
                    new_tts_msg.append(msg)

            new_tts_msg = " ".join(new_tts_msg)

        if len(new_tts_msg) == 0:
            new_tts_msg = tts_text

        try:
            mp3_fp = BytesIO()
            tts = gTTS(text=new_tts_msg, lang="en")
            tts.write_to_fp(mp3_fp)
        except AssertionError as e:
            err_msg = "No text to send to TTS API"
            raise commands.CommandInvokeError(err_msg)

        mp3_fp.seek(0)
        await ctx.send(file=discord.File(mp3_fp, display_filename))
        mp3_fp.close()

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, BucketType.user)
    async def echo(self, ctx, *, msg: str):
        """(Show your msg again)
            echo <msg>
        """

        await ctx.message.channel.typing()
        await bot_utils.send_msg(ctx, msg)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, BucketType.user)
    async def ping(self, ctx):
        """(Test latency)
            ping
        """

        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        p = int(self.bot.ws.latency * 1000)
        color = discord.Color.green()
        if p > 200:
            color = discord.Color.red()
        embed = discord.Embed(title=None, description=f"Ping: {p} ms", color=color)
        await bot_utils.send_embed(ctx, embed)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, BucketType.user)
    async def lmgtfy(self, ctx, *, user_msg: str):
        """(Creates a lmgtfy link)
            Let me Google that for You
                lmgtfy <link>
        """

        await ctx.message.channel.typing()
        search_terms = chat_formatting.escape_mass_mentions(user_msg.replace(" ", "+"))
        msg = f"https://lmgtfy.com/?q={search_terms}"
        await ctx.message.channel.typing()
        await bot_utils.send_msg(ctx, msg)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, BucketType.user)
    async def invites(self, ctx):
        """(List active invites link for the current server)
            invites
        """

        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        server = ctx.guild
        active_invites = await server.invites()

        revoked_invites = ["~~{0.code}: `{0.channel}` created by `{0.inviter}`~~ ".format(x) for x in active_invites if
                           x.revoked]
        unlimited_invites = ["[`{0.code}`]({0.url}): `{0.channel}` created by `{0.inviter}`".format(x) for x in
                             active_invites if x.max_age == 0 and x not in revoked_invites]
        limited_invites = ["[`{0.code}`]({0.url}): `{0.channel}` created by `{0.inviter}`".format(x) for x in
                           active_invites if x.max_age != 0 and x not in revoked_invites]

        embed = discord.Embed(title="Invite Links")
        embed.set_thumbnail(url=server.icon.url)

        if unlimited_invites:
            embed.add_field(name=f"Unlimited Invites ({len(unlimited_invites)})",
                            value="\n".join(unlimited_invites[:5]))
        if limited_invites:
            embed.add_field(name=f"Temporary Invites ({len(limited_invites)})", value="\n".join(limited_invites))
        if revoked_invites:
            embed.add_field(name=f"Revoked Invites ({len(revoked_invites)})", value="\n".join(revoked_invites))
        if len(unlimited_invites) > 0 or len(limited_invites) > 0 or len(revoked_invites) > 0:
            await bot_utils.send_embed(ctx, embed)
        else:
            await bot_utils.send_msg(ctx, chat_formatting.inline("No current invites on any channel."))

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, BucketType.user)
    async def serverinfo(self, ctx):
        """(Shows server's information)
            serverinfo
        """

        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        server = ctx.guild
        online = len([m.status for m in server.members
                      if m.status == discord.Status.online
                      or m.status == discord.Status.idle])

        total_users = len([x.bot for x in server.members if x.bot is False])
        total_bots = len([x.bot for x in server.members if x.bot is True])
        text_channels = len(server.text_channels)
        voice_channels = len(server.voice_channels)

        now = bot_utils.get_current_date_time()
        created = bot_utils.convert_datetime_to_str(server.created_at)
        passed = (now - server.created_at).days
        created_at = f"Since {created[:-7]}. That's over {passed} days ago!"

        embed = discord.Embed(description=created_at)
        embed.add_field(name="Users", value=f"{total_users}")
        embed.add_field(name="Online", value=f"{online}")
        embed.add_field(name="Offline", value=f"{total_users - online}")
        embed.add_field(name="Bots", value=str(total_bots))
        embed.add_field(name="Text Channels", value=text_channels)
        embed.add_field(name="Voice Channels", value=voice_channels)
        embed.add_field(name="Roles", value=len(server.roles))
        embed.add_field(name="Owner", value=str(server.owner))
        embed.add_field(name="Emojis", value=len(server.emojis))
        embed.set_footer(text=f"Server ID: {server.id} | {created}")

        if server.icon.url:
            embed.set_author(name=server.name, url=server.icon.url)
            embed.set_thumbnail(url=server.icon.url)
        else:
            embed.set_author(name=server.name)

        await bot_utils.send_embed(ctx, embed)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, BucketType.user)
    async def userinfo(self, ctx, *, member_str: str = None):
        """(Shows users's information)
            userinfo
            userinfo user#1234
        """

        await ctx.message.channel.typing()
        author = ctx.message.author
        server = ctx.guild

        user = None
        if member_str:
            user = bot_utils.get_object_member_by_str(ctx, member_str)

        if not user:
            user = author

        now = bot_utils.get_current_date_time()
        joined_at = user.joined_at
        since_created = (now - user.created_at).days
        since_joined = (now - joined_at).days
        user_joined = joined_at.strftime("%d %b %Y %H:%M")
        user_created = user.created_at.strftime("%d %b %Y %H:%M")
        member_number = sorted(server.members, key=lambda m: m.joined_at).index(user) + 1

        created_on = f"{user_created}\n({since_created} days ago)"
        joined_on = f"{user_joined}\n({since_joined} days ago)"

        if user.activity:
            match user.activity.type:
                case discord.ActivityType.playing:
                    description = f"Playing {user.activity.name}"
                case discord.ActivityType.streaming:
                    description = f"Streaming: [{user.activity.name}]({user.activity.details})"
                case _:
                    description = user.status.name
        elif user.status.name == "dnd":
            description = "Do Not Disturb"
        else:
            description = user.status.name

        roles_lst = sorted([x.name for x in user.roles])
        roles_str = ",".join(roles_lst) if roles_lst else None

        embed = discord.Embed(description=description, color=user.color)
        embed.add_field(name="Joined Discord on", value=created_on)
        embed.add_field(name="Joined this server on", value=joined_on)
        embed.add_field(name="Roles", value=roles_str.replace("@", ""), inline=False)
        embed.set_footer(text=f"Member #{member_number} | User ID:{user.id} | {bot_utils.get_current_date_time_str()}")

        name = str(user)
        name = " ~ ".join((name, user.nick)) if user.nick else name

        if user.avatar.url:
            embed.set_author(name=name, url=user.avatar.url)
            embed.set_thumbnail(url=user.avatar.url)
        else:
            embed.set_author(name=name)

        await bot_utils.send_embed(ctx, embed)

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, BucketType.user)
    async def about(self, ctx):
        """(Information about this bot)
            about
        """
        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        bot_webpage_url = constants.BOT_WEBPAGE_URL
        bot_avatar = self.bot.user.avatar.url
        author = self.bot.get_user(self.bot.owner_id)
        python_version = "Python {}.{}.{}".format(*sys.version_info[:3])

        apis_included = self._get_apis_included(constants.APIS_INCLUDED)
        games_included = self._get_apis_included(constants.GAMES_INCLUDED)

        dev_info_msg = (f"Developed as an open source project and hosted on [GitHub]({bot_webpage_url})\n"
                        f"A python discord api wrapper: [discord.py]({constants.DISCORDPY_URL})\n""")

        bot_stats = bot_utils.get_bot_stats(self.bot)
        servers = bot_stats["servers"]
        users = bot_stats["users"]
        channels = bot_stats["channels"]

        embed = discord.Embed(description=str(self.bot.description))
        embed.set_author(name=f"{self.bot.user.name} v{constants.VERSION}", icon_url=bot_avatar, url=bot_webpage_url)
        embed.set_thumbnail(url=bot_avatar)
        embed.set_footer(icon_url=author.avatar.url, text=f"Developed by {str(author)} | {python_version}")

        embed.add_field(name="Development Info", value=dev_info_msg, inline=False)
        embed.add_field(name="Servers", value=f"{servers}")
        embed.add_field(name="Users", value=f"{users}")
        embed.add_field(name="Channels", value=f"{channels}")
        if apis_included is not None:
            embed.add_field(name="APIs Included", value=apis_included, inline=False)
        if games_included is not None:
            embed.add_field(name="Games Included", value=games_included, inline=False)
        embed.add_field(name="Download", value=f"[Version {constants.VERSION}]({bot_webpage_url})")
        embed.add_field(name="Donations", value=f"[Paypal]({constants.PAYPAL_URL})")
        embed.add_field(name="Help", value=f"For a list of command categories, type `{ctx.prefix}help`", inline=False)
        await bot_utils.send_embed(ctx, embed)

    @staticmethod
    def _get_apis_included(apis_const: tuple):
        result = None
        if apis_const is not None:
            if len(apis_const) == 1:
                result = f"{apis_const[0]}"
            elif len(apis_const) > 1:
                result = ""
                for apis in apis_const:
                    result += f"({apis}) "
        return result

    @commands.command()
    @commands.cooldown(1, CoolDowns.Misc.value, BucketType.user)
    async def test(self, ctx):
        """(test)"""

        msg = "test"
        color = discord.Color.red()
        embed = discord.Embed(color=color, description=msg)
        embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
        embed.set_footer(icon_url=ctx.bot.user.avatar.url, text=f"{bot_utils.get_current_date_time_str()} UTC")
        await bot_utils.send_embed(ctx, embed, True)


async def setup(bot):
    await bot.add_cog(Misc(bot))
