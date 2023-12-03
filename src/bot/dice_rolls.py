# -*- coding: utf-8 -*-
import random
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.utils import bot_utils, chat_formatting
from src.bot.utils.checks import Checks
from src.bot.utils.cooldowns import CoolDowns
from src.database.dal.bot.dice_rolls_dal import DiceRollsDal


class DiceRolls(commands.Cog):
    """(Dice rolls commands)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.cooldown(1, CoolDowns.DiceRolls.value, BucketType.user)
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


async def setup(bot):
    await bot.add_cog(DiceRolls(bot))
