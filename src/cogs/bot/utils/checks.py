#! /usr/bin/env python3
#|*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
#|*****************************************************
# # -*- coding: utf-8 -*-

from discord.ext import commands
from src.cogs.bot.utils import bot_utils as utils
################################################################################
################################################################################
############################################################################### 
class Checks():
    def __init__(self):
        pass
################################################################################
################################################################################
############################################################################### 
    def check_is_admin():
        def predicate(ctx):
            if utils.is_member_admin(ctx.message.author):
                return True
            else:
                raise commands.CheckFailure(message="not admin") 
        return commands.check(predicate)
################################################################################
################################################################################
################################################################################
    def check_is_bot_owner():
        def predicate(ctx):
            if utils.is_bot_owner(ctx, ctx.message.author):
                return True
            else:
                raise commands.CheckFailure(message="not owner") 
        return commands.check(predicate)
################################################################################
################################################################################ 
################################################################################ 
#     def check_is_music_user():
#         async def predicate(ctx):
#             musicUsersSql = MusicUsersSql(ctx.bot.log)
#             rs = await musicUsersSql.get_allowed_music_user(ctx.message.author)
#             adm = utils.is_member_admin(ctx.message.author)
#             if (len(rs)>0) or (adm == True):
#                 return True
#             else:
#                 raise commands.CheckFailure(message="not music user") 
#         return commands.check(predicate)
################################################################################
################################################################################ 
################################################################################ 
