#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

import discord
import asyncio
import random
from src.cogs.bot.utils import constants
from src.cogs.gw2.utils import gw2_utils as Gw2Utils


class BgTasks:
    """(BackGround Tasks)"""

    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def bgtask_change_presence(self, task_timer: int):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            game = str(random.choice(constants.GAMES_INCLUDED))
            bot_game_desc = f"{game} | {self.bot.command_prefix[0]}help"
            self.bot.log.info(f"(Background task {task_timer}s)(Change activity: {game})")
            await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name=bot_game_desc))
            await asyncio.sleep(int(task_timer))

    ################################################################################
    async def bgtask_check_gw2_roles(self, server: discord.Guild, role: discord.Guild.roles, task_timer: int):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.bot.log.info(f"(Background task {task_timer}s)(Gw2 roles)({server}:{server.id})(Role:{role})")
            await Gw2Utils.check_gw2_roles(self, server)
            await asyncio.sleep(int(task_timer))
