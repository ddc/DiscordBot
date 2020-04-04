#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import os
import datetime as dt
import discord
import random
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from .utils import bot_utils as BotUtils
from .utils import constants
from .utils import chat_formatting as Formatting
from .utils.checks import Checks
from src.sql.bot.server_configs_sql import ServerConfigsSql
from src.sql.bot.dice_rolls_sql import DiceRollsSql
from src.cogs.bot.utils.cooldowns import CoolDowns
from gtts import gTTS
from io import BytesIO
from data.pepe import pepedatabase
import aiohttp


class Misc(commands.Cog):
    """(Bot misc commands)"""

    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    # @commands.command()
    # #@commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    # async def test(self, ctx):
    #     """(test)"""

    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def pepe(self, ctx):
        """Posts a random Pepe from imgur

        Example:
        pepe
        """

        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.trigger_typing()
        pepe_url = f"{random.choice(pepedatabase)[:-1]}.jpg"
        async with aiohttp.ClientSession() as session:
            async with session.get(pepe_url) as resp:
                if resp.status != 200:
                    return await BotUtils.send_error_msg(self, ctx, "Could not download pepe file...")
                data = BytesIO(await resp.read())
                data.seek(0)
                name = pepe_url.split("/")[3]
                await ctx.send(file=discord.File(data, name))
                data.close()

    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def tts(self, ctx, *, tts_text: str):
        """(Send TTS as .mp3 to current channel)

        Example:
        tts Hello everyone!
        """

        await ctx.message.channel.trigger_typing()
        display_filename = f"{BotUtils.get_member_name_by_id(self, ctx, ctx.message.author.id)}.mp3"
        new_tts_msg = None
        # new_msg = None

        if "<@!" in tts_text:
            mentions = tts_text.split(' ')
            new_tts_msg = []
            # new_msg = []
            for msg in mentions:
                if "<@!" in msg:
                    member_id = msg.strip(' ').strip('<@!').strip('>')
                    member = ctx.guild.get_member(int(member_id))
                    new_tts_msg.append(f"@{member.display_name}")
                    # new_msg.append(f"{member.mention}")
                else:
                    new_tts_msg.append(msg)
                    # new_msg.append(msg)

            new_tts_msg = ' '.join(new_tts_msg)
            # new_msg = ' '.join(new_msg)

        if new_tts_msg is None:
            new_tts_msg = tts_text
        # if new_msg is None:
        #    new_msg = tts_text

        mp3_fp = BytesIO()
        tts = gTTS(text=new_tts_msg)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        # await ctx.send(new_msg)
        await ctx.send(file=discord.File(mp3_fp, display_filename))
        mp3_fp.close()

    ################################################################################
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

        if ctx.invoked_subcommand is None:
            await ctx.message.channel.trigger_typing()
            author = ctx.message.author

            if ctx.subcommand_passed is None:
                dice_size = 100
            else:
                if ctx.subcommand_passed.isnumeric():
                    dice_size = int(ctx.subcommand_passed)
                else:
                    raise commands.CommandNotFound(message="CommandNotFound")

            if dice_size > 1:
                serverHighestRoll = 0
                userBestRoll = 0
                roll = random.randint(1, dice_size)
                serverHighestUser = ""

                diceRollsSql = DiceRollsSql(self.bot)
                rsUser = await diceRollsSql.get_user_dice_rolls(author, dice_size)
                rsServerMaxRoll = await diceRollsSql.get_server_max_dice_roll(ctx.guild.id, dice_size)

                if len(rsServerMaxRoll) > 0:
                    if rsServerMaxRoll[0]["max_roll"] is not None:
                        serverHighestRoll = rsServerMaxRoll[0]["max_roll"]
                    if rsServerMaxRoll[0]["username"] is not None:
                        serverHighestUser = rsServerMaxRoll[0]["username"]

                if len(rsUser) == 0:
                    await diceRollsSql.insert_user_dice_roll(author, dice_size, str(roll))
                else:
                    userBestRoll = rsUser[0]["roll"]

                if roll > serverHighestRoll:
                    await ctx.send(":crown: This is now the server highest roll :crown:")
                    serverHighestRoll = roll

                if roll > userBestRoll:
                    await ctx.send(":star2: This is now your highest roll :star2:")
                    await diceRollsSql.update_user_dice_roll(author, dice_size, str(roll))
                    userBestRoll = roll

                if userBestRoll == 0:
                    userBestRoll = roll

                if serverHighestUser == str(author):
                    await ctx.send(Formatting.inline(f"You are the server winner: {userBestRoll}"))
                else:
                    await ctx.send(Formatting.inline(f"Server highest roll: {serverHighestRoll}"))
                    await ctx.send(Formatting.inline(f"Your highest roll: {userBestRoll}"))

                await ctx.send(f"{author.mention} :game_die: {roll} :game_die:")
            else:
                await BotUtils.send_error_msg(self, ctx, "Dice size needs to be higher than 1")

            return

        ctx.invoked_subcommand

    ################################################################################
    @roll.command(name="results")
    async def roll_results(self, ctx):
        """(Show all rolls from current server or user)

        Example:
        roll results
        roll results <member#1234>
        """

        member_str = None
        dice_size = None
        server = ctx.guild
        msg_size = len(ctx.message.content)
        color = self.bot.settings["EmbedColor"]
        embed = discord.Embed(color=color)
        embed.set_footer(text=f"To reset all rolls from this server type: {ctx.prefix}roll reset")

        if "roll results" in ctx.message.content and msg_size == 13:
            arg = "100"
        elif "roll results " in ctx.message.content:
            arg = str(ctx.message.content.replace(f"{ctx.prefix}roll results ", ""))

        if arg.isnumeric():
            dice_size = arg
        elif len(arg) > 0:
            member_str = arg.strip(' ')

        diceRollsSql = DiceRollsSql(self.bot)
        if member_str is not None:
            # get object member from string
            member = BotUtils.get_object_member_by_str(self, ctx, member_str)
            if member is None:
                await BotUtils.send_error_msg(self, ctx, f"Member `{member_str}` not found\n" \
                                                         f"Use `{ctx.prefix}roll results member#1234`")
                return

            if dice_size is None:
                rs = await diceRollsSql.get_all_user_dice_rolls(server.id, member.id)
                if len(rs) == 0:
                    await BotUtils.send_error_msg(self, ctx,
                                                  f"There are no dice rolls from {member_str} in this server.")
                    return

                rolls_lst = []
                dice_size_lst = []
                position = 1
                for key, value in rs.items():
                    rolls_lst.append(str(value["roll"]))
                    dice_size_lst.append(str(value["dice_size"]))
                    position += 1

                dice_sizes = '\n'.join(dice_size_lst)
                rolls = '\n'.join(rolls_lst)

                embed.set_author(name=f"{ctx.guild.name} ({member_str})", icon_url=f"{ctx.guild.icon_url}")
                embed.add_field(name="Dice Size", value=Formatting.inline(dice_sizes), inline=True)
                embed.add_field(name="Roll", value=Formatting.inline(rolls), inline=True)
                await BotUtils.send_embed(self, ctx, embed, False)
        else:
            rs = await diceRollsSql.get_all_server_dice_rolls(server.id, dice_size)
            if len(rs) == 0:
                await BotUtils.send_error_msg(self, ctx,
                                              f"There are no dice rolls of the size {dice_size} in this server.")
                return

            member_lst = []
            rolls_lst = []
            position = 1
            for key, value in rs.items():
                member_name = BotUtils.get_member_name_by_id(self, ctx, value["discord_user_id"])
                member_lst.append(f"{position}) {member_name}")
                rolls_lst.append(str(value["roll"]))
                position += 1

            members = '\n'.join(member_lst)
            rolls = '\n'.join(rolls_lst)

            embed.set_author(name=f"{ctx.guild.name} (Dice Size: {dice_size})", icon_url=f"{ctx.guild.icon_url}")
            embed.add_field(name="Member", value=Formatting.inline(members), inline=True)
            embed.add_field(name="Roll", value=Formatting.inline(rolls), inline=True)
            await BotUtils.send_embed(self, ctx, embed, False)

    ################################################################################
    @roll.command(name="reset")
    @Checks.check_is_admin()
    async def roll_reset(self, ctx):
        """(Deletes all dice rolls from a server)

        Example:
        roll reset
        """

        diceRollsSql = DiceRollsSql(self.bot)
        color = self.bot.settings["EmbedColor"]
        await ctx.message.channel.trigger_typing()
        await diceRollsSql.delete_all_server_dice_rolls(ctx.guild.id)
        await BotUtils.send_msg(self, ctx, color, "Dice rolls from all members in this server have been deleted.")

    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def pool(self, ctx, *, questions: str):
        """(Creates a numeric list of choices pool)

        - Choices are going to be separated by semicolon (;)
        - First sentence before the first semicolon will be the question
        - All emojis found with the choices are going to stay at the message
        - Need at least two choices
        - No more than 10 choices allowed

        Example:
        pool Question?; First choice; Second choice; Third choice
        """

        await ctx.message.channel.trigger_typing()
        await BotUtils.delete_last_channel_message(self, ctx)

        new_question_list = []
        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(ctx.guild.id)
        if rs[0]["mention_everyone_pool_cmd"] == 'Y':
            mention_everyone = True
        else:
            mention_everyone = False

        if rs[0]["anonymous_pool"] == 'Y':
            anonymous_pool = True
        else:
            anonymous_pool = False

        counter = 0
        for question in questions.split(";"):
            if str(question) != "":
                if counter == 0:
                    new_question_list.append(str(question))
                else:
                    new_question_list.append(f"{counter}) {question}")
                counter += 1

        new_question = '\n'.join(new_question_list)
        color = BotUtils.get_random_color()
        embed = discord.Embed(color=color, description=Formatting.orange_text(new_question))
        list_size = len(new_question_list)

        if list_size == 2:
            msg = "Command \"pool\" need at least two choices!!!\n" \
                  "Choices are separated by semicolon (;)\n" \
                  "The first sentence is always the question\n" \
                  f"For a simple line pool, use the command: {ctx.prefix}simplepool" \
                  f"For more info: {ctx.prefix}help pool"
            await BotUtils.send_error_msg(self, ctx, msg)
            return

        if list_size > 11:
            msg = "Cannot exceed more than 10 choices.\n" \
                  f"command: {ctx.prefix}pool"
            await BotUtils.send_error_msg(self, ctx, msg)
            return

        if anonymous_pool is False:
            author_name = BotUtils.get_member_name_by_id(self, ctx, ctx.message.author.id)
            embed.set_author(name=author_name, icon_url=ctx.message.author.avatar_url)

        try:
            msg = await ctx.send(embed=embed)
        except discord.Forbidden:
            msg = await ctx.send(new_question)

        for x in range(1, list_size):
            if x == 10:
                await msg.add_reaction("\U0001F51F")
            else:
                await msg.add_reaction(f"{x}\u20e3")

        if (mention_everyone):
            m = await ctx.send("@everyone")
            m.mention_everyone = True
        ################################################################################

    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def simplepool(self, ctx, *, question: str):
        """(Create a simple yes,no,emojis pool)

        - All emojis found in the question are going to be converted to reactions
        - Need at least two emojis
        - If no emojis are found, "Thumbs Up" and "Thums Down" are going to be the only reactions

        Example:
        simplepool <question goes here> <:emoji: :emoji:>

        simplepool Question? :robot: :heart:
        simplepool Question?
        """

        await ctx.message.channel.trigger_typing()
        await BotUtils.delete_last_channel_message(self, ctx)

        server = ctx.message.guild
        question_list = []
        reactions_list = []

        serverConfigsSql = ServerConfigsSql(self.bot)
        rs = await serverConfigsSql.get_server_configs(server.id)
        if rs[0]["mention_everyone_pool_cmd"] == 'Y':
            mention_everyone = True
        else:
            mention_everyone = False

        if rs[0]["anonymous_pool"] == 'Y':
            anonymous_pool = True
        else:
            anonymous_pool = False

        for word in question.split():
            is_server_emoji = False
            is_discord_emoji = False
            is_question = True
            temp_emoji = None

            if len(word.encode('utf-8')) > len(word):
                is_discord_emoji = True
                is_question = False
                temp_emoji = str(word)

            if is_discord_emoji is False:
                if len(server.emojis) > 0:
                    for emoji in server.emojis:
                        sename_str = f"<:{emoji.name}:{emoji.id}>"
                        if str(word) == str(sename_str):
                            is_server_emoji = True
                            is_question = False
                            temp_emoji = emoji

            if is_question is True:
                question_list.append(str(word))
            elif is_server_emoji is True or is_discord_emoji is True:
                emoji_already_in_list = False
                if len(reactions_list) > 0:
                    for rl in reactions_list:
                        if str(word) == str(rl):
                            emoji_already_in_list = True

                if emoji_already_in_list is False:
                    reactions_list.append(temp_emoji)

        new_question = ' '.join(question_list)
        if len(new_question) == 0:
            msg = f"Please ask at least one question!!!\n Command: {ctx.prefix}simplepool"
            await BotUtils.send_error_msg(self, ctx, msg)
            return

        color = BotUtils.get_random_color()
        embed = discord.Embed(color=color, description=Formatting.orange_text(new_question))

        if anonymous_pool is False:
            author_name = BotUtils.get_member_name_by_id(self, ctx, ctx.message.author.id)
            embed.set_author(name=author_name, icon_url=ctx.message.author.avatar_url)

        try:
            msg = await ctx.send(embed=embed)
        except discord.Forbidden:
            msg = await ctx.send(new_question)

        if len(reactions_list) == 0:
            await msg.add_reaction("\U0001F44D")
            await msg.add_reaction("\U0001F44E")
        elif len(reactions_list) == 1:
            msg = f"Please use more than one emoji!!!\n Command: {ctx.prefix}pool"
            await BotUtils.send_error_msg(self, ctx, msg)
            return
        elif len(reactions_list) > 1:
            for reaction in reactions_list:
                await msg.add_reaction(reaction)

        if (mention_everyone):
            m = await ctx.send("@everyone")
            m.mention_everyone = True

    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def echo(self, ctx, *, msg: str):
        """(Show your msg again)

        Example:
        echo <msg>
        """

        color = self.bot.settings["EmbedColor"]
        await ctx.message.channel.trigger_typing()
        await BotUtils.send_msg(self, ctx, color, msg)

    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def ping(self, ctx):
        """(Test latency)

        Example:
        ping
        """

        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.trigger_typing()
        msgtime = ctx.message.created_at.now()
        await (await self.bot.ws.ping())
        now = dt.datetime.now()
        ping = now - msgtime
        p = int(ping.microseconds / 1000.0)
        color = discord.Color.green()
        if p >= 200:
            color = discord.Color.red()
        pong = discord.Embed(description=f"Ping: {p} ms", color=color)
        await ctx.send(embed=pong)

    #         p=int(self.bot.latency * 1000)
    #         color = discord.Color.green()
    #         if p > 200:
    #             color = discord.Color.red()
    #         embed=discord.Embed(title=None, description=f"Ping: {p} ms", color=color)
    #         await ctx.send(embed=embed)
    #
    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def lmgtfy(self, ctx, *, search_terms: str):
        """(Creates a lmgtfy link)

        Let me Google that for You

        Example:
        lmgtfy <link>
        """

        await ctx.message.channel.trigger_typing()
        search_terms = Formatting.escape_mass_mentions(search_terms.replace(" ", "+"))
        await ctx.send(f"https://lmgtfy.com/?q={search_terms}")

    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.AdminCooldown.value, BucketType.user)
    async def invites(self, ctx):
        """(List active invites link for the current server)

        Example:
        invites
        """

        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.trigger_typing()
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
        embed.set_thumbnail(url=server.icon_url)

        if unlimited_invites:
            embed.add_field(name=f'Unlimited Invites ({len(unlimited_invites)})',
                            value='\n'.join(unlimited_invites[:5]))
        if limited_invites:
            embed.add_field(name=f'Temporary Invites ({len(limited_invites)})', value='\n'.join(limited_invites))
        if revoked_invites:
            embed.add_field(name=f'Revoked Invites ({len(revoked_invites)})', value='\n'.join(revoked_invites))
        if len(unlimited_invites) > 0 or len(limited_invites) > 0 or len(revoked_invites) > 0:
            await BotUtils.send_embed(self, ctx, embed, False)
        else:
            await BotUtils.send_msg(self, ctx, color, Formatting.inline("No current invites on any channel."))

    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def serverinfo(self, ctx):
        """(Shows server's informations)

        Example:
        serverinfo
        """

        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.trigger_typing()
        now = dt.datetime.now()
        server = ctx.guild
        online = len([m.status for m in server.members
                      if m.status == discord.Status.online
                      or m.status == discord.Status.idle])

        # total_users = len([x.bot for x in server.members if x.bot is False])
        # total_bots = len([x.bot for x in server.members if x.bot is True])
        total_users = 0
        total_bots = 0
        for x in server.members:
            if not x.bot:
                total_users += 1
            else:
                total_bots += 1

        text_channels = len(server.text_channels)
        voice_channels = len(server.voice_channels)
        flag = BotUtils.get_region_flag(str(server.region))
        created = BotUtils.convert_date_time_toStr(server.created_at)
        passed = (now - server.created_at).days
        created_at = (f"Since {created}. That's over {passed} days ago!")

        color = self.bot.settings["EmbedColor"]
        data = discord.Embed(description=created_at, color=color)
        data.add_field(name="Users", value=f"{online}/{total_users}")
        data.add_field(name="Bots", value=str(total_bots))
        data.add_field(name="Text Channels", value=text_channels)
        data.add_field(name="Voice Channels", value=voice_channels)
        data.add_field(name="Roles", value=len(server.roles))
        data.add_field(name="Voice Region", value=f"{flag} {server.region}")
        data.add_field(name="Owner", value=str(server.owner))
        data.add_field(name='Emojis', value=len(server.emojis))
        data.set_footer(text=f"Server ID: {server.id} | {now.strftime('%c')}")

        if server.icon_url:
            data.set_author(name=server.name, url=server.icon_url)
            data.set_thumbnail(url=server.icon_url)
        else:
            data.set_author(name=server.name)

        await BotUtils.send_embed(self, ctx, data, False)

    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def userinfo(self, ctx, *, member_str: str):
        """(Shows users's informations)

        Example:
        userinfo user#1234
        """

        await ctx.message.channel.trigger_typing()
        now = dt.datetime.now()
        author = ctx.message.author
        server = ctx.guild

        if not member_str[-4:].isnumeric():
            msg = "Please use full member name with tag number: member#1234"
            await BotUtils.send_error_msg(self, ctx, msg)
            return

        # get object member from string
        member = BotUtils.get_object_member_by_str(self, ctx, member_str)
        if member is None:
            user = author
        else:
            user = member

        joined_at = user.joined_at
        since_created = (now - user.created_at).days
        since_joined = (now - joined_at).days
        user_joined = joined_at.strftime("%d %b %Y %H:%M")
        user_created = user.created_at.strftime("%d %b %Y %H:%M")
        member_number = sorted(server.members, key=lambda m: m.joined_at).index(user) + 1

        created_on = f"{user_created}\n({since_created} days ago)"
        joined_on = f"{user_joined}\n({since_joined} days ago)"

        if user.status.name == "dnd":
            status = "Do Not Disturb"
        else:
            status = user.status.name

        game = f"{status}"
        if user.activity is None:
            pass
        elif user.activity.type == discord.ActivityType.playing:
            game = f"Playing {user.activity.name}"
        elif user.activity.type == discord.ActivityType.streaming:
            game = f"Streaming: [{user.activity.name}]({user.activity.details})"
        else:
            pass

        roles_str = ""
        roles_lst = sorted([x.name for x in user.roles if x.name != "@everyone"])
        if roles_lst:
            if len(roles_lst) == 1:
                roles_str = str(roles_lst[0])
            else:
                for role in roles_lst:
                    roles_str += f"({role}) "
        else:
            roles_str = "None"

        data = discord.Embed(description=game, color=user.color)
        data.add_field(name="Joined Discord on", value=created_on)
        data.add_field(name="Joined this server on", value=joined_on)
        data.add_field(name="Roles", value=roles_str, inline=False)
        data.set_footer(text=f"Member #{member_number} | User ID:{user.id} | {now.strftime('%c')}")

        name = str(user)
        name = " ~ ".join((name, user.nick)) if user.nick else name

        if user.avatar_url:
            data.set_author(name=name, url=user.avatar_url)
            data.set_thumbnail(url=user.avatar_url)
        else:
            data.set_author(name=name)

        await BotUtils.send_embed(self, ctx, data, False)

    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def about(self, ctx):
        """(Information about this bot)

        Example:
        about
        """
        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        await ctx.message.channel.trigger_typing()
        version = constants.VERSION
        bot_webpage_url = self.bot.settings['bot_webpage_url']
        bot_avatar = self.bot.user.avatar_url
        # python_version_url = "[Python {}.{}.{}]({})".format(*os.sys.version_info[:3], constants.PYTHON_URL)
        # python_version_fixed_url = f"[Python 3.7.3]({constants.PYTHON_URL})"
        python_version = "Python {}.{}.{}".format(*os.sys.version_info[:3])
        author = self.bot.get_user(self.bot.settings['author_id'])
        author_icon_url = author.avatar_url
        db_in_use = self.bot.settings["full_db_name"].split()[0]

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

        dev_info_msg = f"Developed as an open source project and hosted on [GitHub]({bot_webpage_url})\n" \
                       f"A python discord api wrapper: [discord.py]({constants.DISCORDPY_URL})\n" \
                       f"Version control: [Git]({constants.GIT_URL})\n"""

        if db_in_use.lower() == "postgresql":
            dev_info_msg += f"Database: [PostgreSQL]({constants.POSTGRESQL_URL})"
        elif db_in_use.lower() == "sqlite":
            dev_info_msg += f"Database: [SQLite3]({constants.SQLITE3_URL})"

        bot_stats = BotUtils.get_bot_stats(self.bot)
        servers = bot_stats["servers"]
        users = bot_stats["users"]
        # channels = bot_stats["channels"]

        color = self.bot.settings["EmbedColor"]
        embed = discord.Embed(description=str(self.bot.description), color=color)
        embed.set_author(name=f"{self.bot.user.name} v{constants.VERSION}", icon_url=bot_avatar, url=bot_webpage_url)
        embed.set_thumbnail(url=bot_avatar)
        embed.set_footer(text=f"Developed by {str(author)} | {python_version}", icon_url=author_icon_url)

        embed.add_field(name="Development Info", value=dev_info_msg, inline=False)
        embed.add_field(name="Servers", value=f"{servers}", inline=True)
        embed.add_field(name="Users", value=f"{users}", inline=True)
        # embed.add_field(name="Channels", value=f"{channels}", inline=True)
        if apis_included is not None:
            embed.add_field(name="APIs Included", value=apis_included, inline=False)
        if games_included is not None:
            embed.add_field(name="Games Included", value=games_included, inline=False)
        embed.add_field(name="Download", value=f"[Version {version}]({bot_webpage_url})", inline=True)
        embed.add_field(name="Donations", value=f"[Paypal]({constants.PAYPAL_URL})", inline=True)
        embed.add_field(name="Help", value=(f"For a list of command categories, type `{ctx.prefix}help`"), inline=False)

        await BotUtils.send_embed(self, ctx, embed, False)

    ################################################################################
    @commands.command()
    @commands.cooldown(1, CoolDowns.MiscCooldown.value, BucketType.user)
    async def lp(self, ctx):
        """(Useful information to learn python)

        Example:
        lp
        """
        if ctx.subcommand_passed is not None:
            raise commands.BadArgument(message="BadArgument")

        python_version = "{}.{}".format(*os.sys.version_info[:2])
        field_value = "1) [For complete beginners to programming](https://automatetheboringstuff.com/)\n" \
                      "2) [For people who know programming already](https://learnxinyminutes.com/docs/python3/)\n" \
                      f"3) [Official tutorial {python_version}](https://docs.python.org/{python_version}/tutorial/)\n" \
                      "4) [Useful book](http://python.swaroopch.com/)\n" \
                      "5) [Exercises for beginners](http://www.codeabbey.com/)"

        await ctx.message.channel.trigger_typing()
        color = self.bot.settings["EmbedColor"]
        embed = discord.Embed(color=color)
        embed.add_field(name="Useful information to learn python", value=field_value, inline=True)
        await BotUtils.send_embed(self, ctx, embed, False)


################################################################################
def setup(bot):
    bot.add_cog(Misc(bot))
