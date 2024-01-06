# -*- coding: utf-8 -*-
import random
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.tools import bot_utils, chat_formatting
from src.bot.tools.checks import Checks
from src.bot.tools.cooldowns import CoolDowns
from src.database.dal.bot.dice_rolls_dal import DiceRollsDal


class DiceRolls(commands.Cog):
    """(Dice rolls commands)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.cooldown(1, CoolDowns.DiceRolls.value, BucketType.user)
    async def roll(self, ctx):
        """(Rolls random number [between 1 and user choice])
                roll (Defaults to 100)
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
                return await bot_utils.send_error_msg(ctx, msg)

        if dice_size > 1:
            msg = ""
            system_random = random.SystemRandom()
            roll = system_random.randint(1, dice_size)

            dice_rolls_dal = DiceRollsDal(self.bot.db_session, self.bot.log)
            rs_user = await dice_rolls_dal.get_user_roll_by_dice_size(server.id, author.id, dice_size)
            if not rs_user:
                user_highest_roll = 0
                await dice_rolls_dal.insert_user_roll(server.id, author.id, dice_size, roll)
            else:
                user_highest_roll = rs_user[0]["roll"]

            if roll > user_highest_roll:
                user_highest_roll = roll
                msg += ":star2: This is now your highest roll :star2:\n"
                await dice_rolls_dal.update_user_roll(server.id, author.id, dice_size, roll)

            server_highest_user = None
            server_highest_roll = 0
            rs_server_max_roll = await dice_rolls_dal.get_server_max_roll(ctx.guild.id, dice_size)
            if len(rs_server_max_roll) > 0:
                user = bot_utils.get_member_by_id(ctx.guild, rs_server_max_roll[0]["user_id"])
                if rs_server_max_roll[0]["max_roll"] is not None:
                    server_highest_roll = rs_server_max_roll[0]["max_roll"]
                if user is not None:
                    server_highest_user = user

            if roll > server_highest_roll:
                msg += ":crown: This is now the server highest roll :crown:\n"
                server_highest_roll = roll
                server_highest_user = author

            if server_highest_user is None or server_highest_user == author:
                msg += f":crown: You are the server winner with {user_highest_roll}\n"
            else:
                highest_roll_user_name = bot_utils.get_member_by_id(ctx.guild, server_highest_user.id)
                msg += f"`{highest_roll_user_name}` has the server highest roll with {server_highest_roll}\n"
                msg += f"Your highest roll is {user_highest_roll}\n"

            msg += f":game_die: {roll} :game_die:\n"
            color = discord.Color.red()
            embed = discord.Embed(description=msg, color=color)
            embed.set_author(name=author.display_name, icon_url=author.avatar.url)
            await bot_utils.send_embed(ctx, embed)
        else:
            await bot_utils.send_error_msg(ctx, "Dice size needs to be higher than 1")

    @roll.command(name="results")
    async def roll_results(self, ctx):
        """(Show all rolls from current server or user)
            roll results
            roll results <member#1234>
        """

        server = ctx.guild
        msg_lst = ctx.message.content.split()
        embed = discord.Embed()

        try:
            if len(msg_lst) == 3:
                dice_size = int(msg_lst[2])
            else:
                dice_size = 100
        except:
            msg = "Thats not a valid dice size.\nPlease try again."
            await bot_utils.send_error_msg(ctx, msg)
            return

        dice_rolls_sql = DiceRollsDal(self.bot.db_session, self.bot.log)
        rs_all_server_rolls = await dice_rolls_sql.get_all_server_rolls(server.id, dice_size)
        if not rs_all_server_rolls:
            msg = f"There are no dice rolls of the size {dice_size} in this server."
            await bot_utils.send_error_msg(ctx, msg)
            return

        member_lst = []
        rolls_lst = []
        for position, each_user in enumerate(rs_all_server_rolls, 1):
            member = bot_utils.get_member_by_id(ctx.guild, each_user["user_id"])
            member_lst.append(f"{position}) {member.display_name}")
            rolls_lst.append(str(each_user["roll"]))

        members = "\n".join(member_lst)
        rolls = "\n".join(rolls_lst)

        embed.set_author(name=f"{server.name} (Dice Size: {dice_size})", icon_url=server.icon.url)
        embed.add_field(name="Member", value=chat_formatting.inline(members))
        embed.add_field(name="Roll", value=chat_formatting.inline(rolls))
        embed.set_footer(text=f"To reset all rolls from this server type: {ctx.prefix}roll reset")
        await bot_utils.send_embed(ctx, embed)

    @roll.command(name="reset")
    @Checks.check_is_admin()
    async def roll_reset(self, ctx):
        """(Deletes all dice rolls from a server)
            roll reset
        """

        dice_rolls_sql = DiceRollsDal(self.bot.db_session, self.bot.log)
        await ctx.message.channel.typing()
        await dice_rolls_sql.delete_all_server_rolls(ctx.guild.id)
        await bot_utils.send_msg(ctx, "Rolls from all members in this server have been deleted.")


async def setup(bot):
    await bot.add_cog(DiceRolls(bot))
