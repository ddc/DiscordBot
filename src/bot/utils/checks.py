# -*- coding: utf-8 -*-
from discord.ext import commands
from src.bot.utils import bot_utils


class Checks:
    def __init__(self):
        pass

    def check_is_admin():
        def predicate(ctx):
            if bot_utils.is_member_admin(ctx.message.author):
                return True
            else:
                raise commands.CheckFailure(message="not admin")
        return commands.check(predicate)

    def check_is_bot_owner():
        def predicate(ctx):
            if bot_utils.is_bot_owner(ctx, ctx.message.author):
                return True
            else:
                raise commands.CheckFailure(message="not owner")
        return commands.check(predicate)