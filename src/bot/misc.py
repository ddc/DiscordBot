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
from src.bot.utils.checks import Checks
from src.bot.utils.cooldowns import CoolDowns
from src.database.dal.bot.dice_rolls_dal import DiceRollsDal


class Misc(commands.Cog):
    """(Bot misc commands)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def test(self, ctx):
        """(test)"""

        await ctx.message.channel.typing()
        msg = "test"
        embed = discord.Embed(color=discord.Color.red(), description=msg)
        embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
        await bot_utils.send_embed(self, ctx, embed)

    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def pepe(self, ctx):
        """Posts a random Pepe from imgur

        Example:
        pepe
        """

        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        pepe_url = f"{random.choice(pepedatabase)[:-1]}.jpg"
        async with aiohttp.ClientSession() as session:
            async with session.get(pepe_url) as resp:
                if resp.status != 200:
                    return await bot_utils.send_error_msg(self, ctx, "Could not download pepe file...")
                data = BytesIO(await resp.read())
                data.seek(0)
                name = pepe_url.split("/")[3]
                await ctx.send(file=discord.File(data, name))
                data.close()

    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def tts(self, ctx, *, tts_text: str):
        """(Send TTS as .mp3 to current channel)

        Example:
        tts Hello everyone!
        """

        await ctx.message.channel.typing()
        display_filename = f"{bot_utils.get_member_name_by_id(self, ctx, ctx.message.author.id)}.mp3"
        new_tts_msg = []

        if "<@!" in tts_text or "<:" in tts_text:
            msg_text = tts_text.split(' ')
            for msg in msg_text:
                if "<@!" == msg[0:3]:
                    member_id = msg.strip(' ').strip('<@!').strip('>')
                    member = ctx.guild.get_member(int(member_id))
                    new_tts_msg.append(f"@{member.display_name}")
                elif "<:" == msg[0:2] and ">" == msg[-1]:
                    emoji_id = msg.split(":")[2].strip('>')
                    if len(emoji_id) >= 18:
                        emoji_name = msg.split(":")[1]
                        new_tts_msg.append(emoji_name)
                elif len(msg) > 0:
                    new_tts_msg.append(msg)

            new_tts_msg = ' '.join(new_tts_msg)

        if len(new_tts_msg) == 0:
            new_tts_msg = tts_text

        try:
            mp3_fp = BytesIO()
            tts = gTTS(text=new_tts_msg, lang='en')
            tts.write_to_fp(mp3_fp)
        except AssertionError as e:
            err_msg = "No text to send to TTS API"
            raise commands.CommandInvokeError(err_msg)

        mp3_fp.seek(0)
        await ctx.send(file=discord.File(mp3_fp, display_filename))
        mp3_fp.close()

    @commands.group()
    @commands.cooldown(1, CoolDowns.RollDiceCooldown.value, BucketType.user)
    async def roll(self, ctx):
        """(Rolls random number [between 1 and user choice])

        Defaults to 100.

        Example:
        roll
        roll 500
        roll results
        roll results user#1234
        roll reset
        """

        if ctx.invoked_subcommand:
            return ctx.invoked_subcommand

        await ctx.message.channel.typing()
        server = ctx.guild
        author = ctx.message.author

        if ctx.subcommand_passed is None:
            dice_size = 100
        else:
            if ctx.subcommand_passed.isnumeric():
                dice_size = int(ctx.subcommand_passed)
            else:
                msg = "Thats not a valid dice size.\nPlease try again."
                embed = discord.Embed(title="", color=discord.Color.red(), description=msg)
                embed.set_author(name=author.display_name, icon_url=author.avatar.url)
                await bot_utils.send_embed(self, ctx, embed)
                return

        if dice_size > 1:
            server_highest_roll = 0
            user_best_roll = 0
            roll = random.randint(1, dice_size)
            server_highest_user = None

            dice_rolls_dal = DiceRollsDal(self.bot.db_session, self.bot.log)
            rs_user = await dice_rolls_dal.get_user_rolls_by_dice_size(server.id, author.id, dice_size)
            rs_server_max_roll = await dice_rolls_dal.get_server_max_roll(ctx.guild.id, dice_size)

            if len(rs_server_max_roll) > 0:
                user = bot_utils.get_member_by_id(ctx.guild, rs_server_max_roll[0]["user_id"])
                if rs_server_max_roll[0]["max_roll"] is not None:
                    server_highest_roll = rs_server_max_roll[0]["max_roll"]
                if user is not None:
                    server_highest_user = user

            if len(rs_user) == 0:
                await dice_rolls_dal.insert_user_roll(server.id, author.id, dice_size, roll)
            else:
                user_best_roll = rs_user[0]["roll"]

            if roll > server_highest_roll:
                await ctx.send(":crown: This is now the server highest roll :crown:")
                server_highest_roll = roll

            if roll > user_best_roll:
                await ctx.send(":star2: This is now your highest roll :star2:")
                await dice_rolls_dal.update_user_roll(server.id, author.id, dice_size, roll)
                user_best_roll = roll

            if user_best_roll == 0:
                user_best_roll = roll

            if server_highest_user is None or server_highest_user == author:
                await ctx.send(chat_formatting.inline(f"You are the server winner with {user_best_roll}"))
            else:
                await ctx.send(chat_formatting.inline(f"{server_highest_user} has the server highest roll with "
                                                      f"{server_highest_roll}"))
                await ctx.send(chat_formatting.inline(f"Your highest roll is {user_best_roll}"))

            await ctx.send(f"{author.mention} :game_die: {roll} :game_die:")
        else:
            await bot_utils.send_error_msg(self, ctx, "Dice size needs to be higher than 1")

    @roll.command(name="results")
    async def roll_results(self, ctx):
        """(Show all rolls from current server or user)

        Example:
        roll results
        roll results <member#1234>
        """

        dice_size = 100
        server = ctx.guild
        author = ctx.message.author
        msg_lst = ctx.message.content.split()
        color = self.bot.settings["EmbedColor"]
        embed = discord.Embed(color=color)

        try:
            if len(msg_lst) == 3:
                dice_size = int(msg_lst[2])
            else:
                raise ValueError
        except ValueError:
            msg = "Thats not a valid dice size.\nPlease try again."
            embed = discord.Embed(title="", color=discord.Color.red(), description=msg)
            embed.set_author(name=author.display_name, icon_url=author.avatar.url)
            await bot_utils.send_embed(self, ctx, embed)
            return

        dice_rolls_sql = DiceRollsDal(self.bot.db_session, self.bot.log)
        rs_all_server_rolls = await dice_rolls_sql.get_all_server_rolls(server.id, dice_size)
        if len(rs_all_server_rolls) == 0:
            await bot_utils.send_error_msg(
                self, ctx,
                f"There are no dice rolls of the size {dice_size} in this server."
            )
            return

        member_lst = []
        rolls_lst = []
        for position, each_user in enumerate(rs_all_server_rolls, 1):
            member_name = bot_utils.get_member_name_by_id(self, ctx, each_user["user_id"])
            member_lst.append(f"{position}) {member_name}")
            rolls_lst.append(str(each_user["roll"]))

        members = '\n'.join(member_lst)
        rolls = '\n'.join(rolls_lst)

        embed.set_author(name=f"{server.name} (Dice Size: {dice_size})", icon_url=server.icon.url)
        embed.add_field(name="Member", value=chat_formatting.inline(members), inline=True)
        embed.add_field(name="Roll", value=chat_formatting.inline(rolls), inline=True)
        embed.set_footer(text=f"To reset all rolls from this server type: {ctx.prefix}roll reset")
        await bot_utils.send_embed(self, ctx, embed)

    @roll.command(name="reset")
    @Checks.check_is_admin()
    async def roll_reset(self, ctx):
        """(Deletes all dice rolls from a server)

        Example:
        roll reset
        """

        dice_rolls_sql = DiceRollsDal(self.bot.db_session, self.bot.log)
        color = self.bot.settings["EmbedColor"]
        await ctx.message.channel.typing()
        await dice_rolls_sql.delete_all_server_rolls(ctx.guild.id)
        await bot_utils.send_msg(self, ctx, color, "Rolls from all members in this server have been deleted.")

    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def echo(self, ctx, *, msg: str):
        """(Show your msg again)

        Example:
        echo <msg>
        """

        color = self.bot.settings["EmbedColor"]
        await ctx.message.channel.typing()
        await bot_utils.send_msg(self, ctx, color, msg)

    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def ping(self, ctx):
        """(Test latency)

        Example:
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
        await bot_utils.send_embed(self, ctx, embed)

    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def lmgtfy(self, ctx, *, user_msg: str):
        """(Creates a lmgtfy link)

        Let me Google that for You

        Example:
        lmgtfy <link>
        """

        await ctx.message.channel.typing()
        search_terms = chat_formatting.escape_mass_mentions(user_msg.replace(" ", "+"))
        msg = f"https://lmgtfy.com/?q={search_terms}"
        color = self.bot.settings["EmbedColor"]
        await ctx.message.channel.typing()
        await bot_utils.send_msg(self, ctx, color, msg)

    @commands.command()
    @commands.cooldown(1, CoolDowns.AdminCooldown.value, BucketType.user)
    async def invites(self, ctx):
        """(List active invites link for the current server)

        Example:
        invites
        """

        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        server = ctx.guild
        active_invites = await server.invites()

        revoked_invites = ['~~{0.code}: `{0.channel}` created by `{0.inviter}`~~ '.format(x) for x in active_invites if
                           x.revoked]
        unlimited_invites = ['[`{0.code}`]({0.url}): `{0.channel}` created by `{0.inviter}`'.format(x) for x in
                             active_invites if x.max_age == 0 and x not in revoked_invites]
        limited_invites = ['[`{0.code}`]({0.url}): `{0.channel}` created by `{0.inviter}`'.format(x) for x in
                           active_invites if x.max_age != 0 and x not in revoked_invites]

        color = self.bot.settings["EmbedColor"]
        embed = discord.Embed(title='Invite Links', color=color)
        embed.set_thumbnail(url=server.icon.url)

        if unlimited_invites:
            embed.add_field(name=f'Unlimited Invites ({len(unlimited_invites)})',
                            value='\n'.join(unlimited_invites[:5]))
        if limited_invites:
            embed.add_field(name=f'Temporary Invites ({len(limited_invites)})', value='\n'.join(limited_invites))
        if revoked_invites:
            embed.add_field(name=f'Revoked Invites ({len(revoked_invites)})', value='\n'.join(revoked_invites))
        if len(unlimited_invites) > 0 or len(limited_invites) > 0 or len(revoked_invites) > 0:
            await bot_utils.send_embed(self, ctx, embed)
        else:
            await bot_utils.send_msg(self, ctx, color, chat_formatting.inline("No current invites on any channel."))

    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def serverinfo(self, ctx):
        """(Shows server's information)

        Example:
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

        color = self.bot.settings["EmbedColor"]
        data = discord.Embed(description=created_at, color=color)
        data.add_field(name="Users", value=f"{total_users}")
        data.add_field(name="Online", value=f"{online}")
        data.add_field(name="Offline", value=f"{total_users - online}")
        data.add_field(name="Bots", value=str(total_bots))
        data.add_field(name="Text Channels", value=text_channels)
        data.add_field(name="Voice Channels", value=voice_channels)
        data.add_field(name="Roles", value=len(server.roles))
        data.add_field(name="Owner", value=str(server.owner))
        data.add_field(name='Emojis', value=len(server.emojis))
        data.set_footer(text=f"Server ID: {server.id} | {now.strftime('%c')}")

        if server.icon.url:
            data.set_author(name=server.name, url=server.icon.url)
            data.set_thumbnail(url=server.icon.url)
        else:
            data.set_author(name=server.name)

        await bot_utils.send_embed(self, ctx, data)

    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def userinfo(self, ctx, *, member_str: str = None):
        """(Shows users's information)

        Example:
        userinfo
        userinfo user#1234
        """

        await ctx.message.channel.typing()
        author = ctx.message.author
        server = ctx.guild

        user = None
        if member_str:
            user = bot_utils.get_object_member_by_str(self, ctx, member_str)

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

        data = discord.Embed(description=description, color=user.color)
        data.add_field(name="Joined Discord on", value=created_on)
        data.add_field(name="Joined this server on", value=joined_on)
        data.add_field(name="Roles", value=roles_str.replace("@", ""), inline=False)
        data.set_footer(text=f"Member #{member_number} | User ID:{user.id} | {now.strftime('%c')}")

        name = str(user)
        name = " ~ ".join((name, user.nick)) if user.nick else name

        if user.avatar.url:
            data.set_author(name=name, url=user.avatar.url)
            data.set_thumbnail(url=user.avatar.url)
        else:
            data.set_author(name=name)

        await bot_utils.send_embed(self, ctx, data)

    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def about(self, ctx):
        """(Information about this bot)

        Example:
        about
        """
        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.typing()
        bot_webpage_url = constants.BOT_WEBPAGE_URL
        bot_avatar = self.bot.user.avatar.url
        author = self.bot.get_user(self.bot.owner_id)
        python_version = "Python {}.{}.{}".format(*sys.version_info[:3])

        games_included = None
        if constants.GAMES_INCLUDED is not None:
            if len(constants.GAMES_INCLUDED) == 1:
                games_included = f"{constants.GAMES_INCLUDED[0]}"
            elif len(constants.GAMES_INCLUDED) > 1:
                games_included = ""
                for games in constants.GAMES_INCLUDED:
                    games_included += f"({games}) "

        apis_included = None
        if constants.APIS_INCLUDED is not None:
            if len(constants.APIS_INCLUDED) == 1:
                apis_included = f"{constants.APIS_INCLUDED[0]}"
            elif len(constants.APIS_INCLUDED) > 1:
                apis_included = ""
                for apis in constants.APIS_INCLUDED:
                    apis_included += f"({apis}) "

        dev_info_msg = (f"Developed as an open source project and hosted on [GitHub]({bot_webpage_url})\n"
                        f"A python discord api wrapper: [discord.py]({constants.DISCORDPY_URL})\n""")

        bot_stats = bot_utils.get_bot_stats(self.bot)
        servers = bot_stats["servers"]
        users = bot_stats["users"]
        # channels = bot_stats["channels"]

        color = self.bot.settings["EmbedColor"]
        embed = discord.Embed(description=str(self.bot.description), color=color)
        embed.set_author(name=f"{self.bot.user.name} v{constants.VERSION}", icon_url=bot_avatar, url=bot_webpage_url)
        embed.set_thumbnail(url=bot_avatar)
        embed.set_footer(text=f"Developed by {str(author)} | {python_version}", icon_url=author.avatar.url)

        embed.add_field(name="Development Info", value=dev_info_msg, inline=False)
        embed.add_field(name="Servers", value=f"{servers}", inline=True)
        embed.add_field(name="Users", value=f"{users}", inline=True)
        # embed.add_field(name="Channels", value=f"{channels}", inline=True)
        if apis_included is not None:
            embed.add_field(name="APIs Included", value=apis_included, inline=False)
        if games_included is not None:
            embed.add_field(name="Games Included", value=games_included, inline=False)
        embed.add_field(name="Download", value=f"[Version {constants.VERSION}]({bot_webpage_url})", inline=True)
        embed.add_field(name="Donations", value=f"[Paypal]({constants.PAYPAL_URL})", inline=True)
        embed.add_field(name="Help", value=f"For a list of command categories, type `{ctx.prefix}help`", inline=False)

        await bot_utils.send_embed(self, ctx, embed)


async def setup(bot):
    await bot.add_cog(Misc(bot))
