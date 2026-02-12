import discord
import random
from discord.ext import commands
from src.bot.constants import messages
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils, chat_formatting
from src.bot.tools.checks import Checks
from src.bot.tools.cooldowns import CoolDowns
from src.database.dal.bot.dice_rolls_dal import DiceRollsDal


class DiceRolls(commands.Cog):
    """Discord cog for dice rolling commands with personal and server records."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.group()
    @commands.cooldown(1, CoolDowns.DiceRolls.value, commands.BucketType.user)
    async def roll(self, ctx: commands.Context) -> commands.Command | None:
        """Roll a die with specified size (defaults to 100).

        Usage:
            roll (default to 100)
            roll 500
            roll results
            roll reset
        """

        if ctx.invoked_subcommand:
            return ctx.invoked_subcommand

        await ctx.message.channel.typing()

        dice_size = self._parse_dice_size(ctx.subcommand_passed)
        if dice_size is None:
            return await bot_utils.send_error_msg(ctx, messages.DICE_SIZE_NOT_VALID)

        if dice_size <= 1:
            return await bot_utils.send_error_msg(ctx, messages.DICE_SIZE_HIGHER_ONE)

        roll_result = self._generate_roll(dice_size)

        dice_rolls_dal = DiceRollsDal(self.bot.db_session, self.bot.log)

        # Handle user roll record
        user_highest_roll = await self._handle_user_roll_record(
            dice_rolls_dal,
            ctx.guild.id,
            ctx.author.id,
            dice_size,
            roll_result,
        )

        # Handle server roll record
        server_record = await self._get_server_highest_roll(dice_rolls_dal, ctx.guild, dice_size)

        # Build result message
        message_parts = self._build_roll_message(roll_result, user_highest_roll, server_record, ctx.author)

        # Create and send embed
        embed = self._create_roll_embed(ctx.author, message_parts)
        await bot_utils.send_embed(ctx, embed)
        return None

    @roll.command(name="results")
    async def roll_results(self, ctx: commands.Context) -> None:
        """Display all dice rolls from the current server.

        Usage:
            roll results (defaults to dice size 100)
            roll results <dice_size>
        """
        dice_size = self._parse_results_dice_size(ctx.message.content)
        if dice_size is None:
            return await bot_utils.send_error_msg(ctx, messages.DICE_SIZE_NOT_VALID)

        dice_rolls_dal = DiceRollsDal(self.bot.db_session, self.bot.log)
        server_rolls = await dice_rolls_dal.get_all_server_rolls(ctx.guild.id, dice_size)

        if not server_rolls:
            return await bot_utils.send_error_msg(ctx, messages.NO_DICE_SIZE_ROLLS.format(dice_size))

        embed = self._create_results_embed(ctx, server_rolls, dice_size)
        await bot_utils.send_embed(ctx, embed)
        return None

    @roll.command(name="reset")
    @Checks.check_is_admin()
    async def roll_reset(self, ctx: commands.Context) -> None:
        """Delete all dice rolls from the server (admin only).

        Usage:
            roll reset
        """
        await ctx.message.channel.typing()

        dice_rolls_dal = DiceRollsDal(self.bot.db_session, self.bot.log)
        await dice_rolls_dal.delete_all_server_rolls(ctx.guild.id)
        await bot_utils.send_msg(ctx, messages.DELETED_ALL_ROLLS)

    @staticmethod
    def _parse_dice_size(subcommand_passed: str | None) -> int | None:
        """Parse dice size from subcommand input."""
        if subcommand_passed is None:
            return 100

        if subcommand_passed.isnumeric():
            return int(subcommand_passed)

        return None

    @staticmethod
    def _parse_results_dice_size(message_content: str) -> int | None:
        """Parse dice size from results command message."""
        try:
            msg_parts = message_content.split()
            if len(msg_parts) == 3:
                return int(msg_parts[2])
            return 100
        except ValueError, IndexError:
            return None

    @staticmethod
    def _generate_roll(dice_size: int) -> int:
        """Generate a cryptographically secure random roll."""
        system_random = random.SystemRandom()
        return system_random.randint(1, dice_size)

    @staticmethod
    async def _handle_user_roll_record(
        dice_rolls_dal: DiceRollsDal,
        server_id: int,
        user_id: int,
        dice_size: int,
        roll: int,
    ) -> int:
        """Handle user roll record creation/updating and return highest roll."""
        user_record = await dice_rolls_dal.get_user_roll_by_dice_size(server_id, user_id, dice_size)

        if not user_record:
            await dice_rolls_dal.insert_user_roll(server_id, user_id, dice_size, roll)
            return roll

        current_highest = user_record[0]["roll"]

        if roll > current_highest:
            await dice_rolls_dal.update_user_roll(server_id, user_id, dice_size, roll)
            return roll

        return current_highest

    @staticmethod
    async def _get_server_highest_roll(
        dice_rolls_dal: DiceRollsDal,
        guild: discord.Guild,
        dice_size: int,
    ) -> dict:
        """Get server the highest roll information."""
        server_max_rolls = await dice_rolls_dal.get_server_max_roll(guild.id, dice_size)

        if not server_max_rolls:
            return {"user": None, "roll": 0}

        max_roll_data = server_max_rolls[0]
        user = bot_utils.get_member_by_id(guild, max_roll_data["user_id"])

        return {"user": user, "roll": max_roll_data["max_roll"] or 0}

    @staticmethod
    def _build_roll_message(
        roll: int,
        user_highest: int,
        server_record: dict,
        author: discord.Member,
    ) -> list[str]:
        """Build message parts for roll result."""
        message_parts = []

        # Check if new server record
        if roll > server_record["roll"]:
            message_parts.append(messages.SERVER_HIGHEST_ROLL_ANOUNCE)
            server_record["roll"] = roll
            server_record["user"] = author

        # Check if new personal record (but not if user is server winner)
        is_server_winner = server_record["user"] == author
        if roll == user_highest and roll > 0 and not is_server_winner:
            message_parts.append(messages.MEMBER_HIGHEST_ROLL)

        # Add server record information
        if server_record["user"] is None or server_record["user"] == author:
            message_parts.append(f"{messages.MEMBER_SERVER_WINNER_ANOUNCE} {user_highest}")
        else:
            highest_user = server_record["user"]
            message_parts.extend(
                [
                    f"`{highest_user.display_name}` {messages.MEMBER_HAS_HIGHEST_ROLL} {server_record['roll']}",
                    f"{messages.MEMBER_HIGHEST_ROLL} {user_highest}",
                ]
            )

        message_parts.append(f":game_die: {roll} :game_die:")
        return message_parts

    @staticmethod
    def _create_roll_embed(author: discord.Member, message_parts: list[str]) -> discord.Embed:
        """Create embed for roll result."""
        description = "\n".join(message_parts)
        embed = discord.Embed(description=description, color=discord.Color.red())
        embed.set_author(name=author.display_name, icon_url=author.avatar.url)
        return embed

    @staticmethod
    def _create_results_embed(ctx: commands.Context, server_rolls: list[dict], dice_size: int) -> discord.Embed:
        """Create embed for results display."""
        member_list = []
        rolls_list = []

        for position, user_data in enumerate(server_rolls, 1):
            member = bot_utils.get_member_by_id(ctx.guild, user_data["user_id"])
            member_list.append(f"{position}) {member.display_name}")
            rolls_list.append(str(user_data["roll"]))

        members = "\n".join(member_list)
        rolls = "\n".join(rolls_list)

        embed = discord.Embed()
        embed.set_author(name=f"{ctx.guild.name} (Dice Size: {dice_size})", icon_url=ctx.guild.icon.url)
        embed.add_field(name="Member", value=chat_formatting.inline(members))
        embed.add_field(name="Roll", value=chat_formatting.inline(rolls))
        embed.set_footer(text=f"{messages.RESET_ALL_ROLLS}: {ctx.prefix}roll reset")

        return embed


async def setup(bot: Bot) -> None:
    """Setup function to add the DiceRolls cog to the bot."""
    await bot.add_cog(DiceRolls(bot))
