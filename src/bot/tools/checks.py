from typing import Any, Callable
from discord.ext import commands
from src.bot.tools import bot_utils


class Checks:
    """Collection of Discord command permission checks."""

    @staticmethod
    def check_is_admin() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Check if the command invoker is a server administrator.

        Returns:
            Command check decorator that raises CheckFailure if user is not admin

        Raises:
            commands.CheckFailure: When the user is not an administrator
        """

        def predicate(ctx: commands.Context) -> bool:
            if bot_utils.is_member_admin(ctx.message.author):
                return True
            raise commands.CheckFailure(message="User is not an administrator")

        return commands.check(predicate)

    @staticmethod
    def check_is_bot_owner() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Check if the command invoker is the bot owner.

        Returns:
            Command check decorator that raises CheckFailure if user is not owner

        Raises:
            commands.CheckFailure: When the user is not the bot owner
        """

        def predicate(ctx: commands.Context) -> bool:
            if bot_utils.is_bot_owner(ctx, ctx.message.author):
                return True
            raise commands.CheckFailure(message="User is not the bot owner")

        return commands.check(predicate)
