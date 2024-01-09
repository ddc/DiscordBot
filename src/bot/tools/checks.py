# -*- coding: utf-8 -*-
from discord.ext import commands
from src.bot.tools import bot_utils


class Checks:
    @staticmethod
    def check_is_admin():
        def wrapper(*args, **kwargs):
            ctx = args[0]
            if bot_utils.is_member_admin(ctx.message.author):
                return True
            else:
                raise commands.CheckFailure(message="not admin")
        return commands.check(wrapper)

    @staticmethod
    def check_is_bot_owner():
        def wrapper(*args, **kwargs):
            ctx = args[0]
            if bot_utils.is_bot_owner(ctx, ctx.message.author):
                return True
            else:
                raise commands.CheckFailure(message="not owner")
        return commands.check(wrapper)
