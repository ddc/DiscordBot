from __future__ import annotations

import asyncio
import discord
import random
from src.bot.constants.variables import GAMES_INCLUDED
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.bot.discord_bot import Bot


class BackGroundTasks:
    """Manages bot background tasks for dynamic presence updates."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.random = random.SystemRandom()

    async def change_presence_task(self, interval_seconds: int) -> None:
        """Background task to periodically change bot presence.

        Args:
            interval_seconds: Time in seconds between presence changes
        """
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            try:
                game_name = self.random.choice(GAMES_INCLUDED)
                prefix = (
                    self.bot.command_prefix if isinstance(self.bot.command_prefix, str) else self.bot.command_prefix[0]
                )
                activity_description = f"{game_name} | {prefix}help"

                self.bot.log.info(f"Background task ({interval_seconds}s) - Changing activity: {game_name}")

                activity = discord.Game(name=activity_description)
                status = discord.Status.online
                await self.bot.change_presence(status=status, activity=activity)

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                self.bot.log.error(f"Error in background presence task: {e}")
                await asyncio.sleep(interval_seconds)
