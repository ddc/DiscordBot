# -*- coding: utf-8 -*-
import asyncio
import random
import discord
from src.bot.utils.constants import GAMES_INCLUDED


class BackGroundTasks:
    """(BackGround Tasks)"""
    def __init__(self, bot):
        self.bot = bot

    async def bgtask_change_presence(self, task_timer: int):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            game = str(random.choice(GAMES_INCLUDED))
            bot_game_desc = f"{game} | {self.bot.command_prefix[0]}help"
            self.bot.log.info(f"(Background task {task_timer}s)(Change activity: {game})")
            await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name=bot_game_desc))
            await asyncio.sleep(int(task_timer))
