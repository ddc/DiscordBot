import asyncio
import random
from typing import TYPE_CHECKING
import discord
from src.bot.constants.variables import GAMES_INCLUDED


if TYPE_CHECKING:
    from discord.ext import commands


class BackgroundTasks:
    """Manages bot background tasks for dynamic presence updates."""

    def __init__(self, bot: "commands.Bot") -> None:
        self.bot = bot
        self._random = random.SystemRandom()

    async def change_presence_task(self, interval_seconds: int) -> None:
        """Background task to periodically change bot presence.

        Args:
            interval_seconds: Time in seconds between presence changes
        """
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            try:
                game_name = self._random.choice(GAMES_INCLUDED)
                activity_description = f"{game_name} | {self.bot.command_prefix[0]}help"

                self.bot.log.info(f"Background task ({interval_seconds}s) - Changing activity: {game_name}")

                activity = discord.Game(name=activity_description)
                await self.bot.change_presence(status=discord.Status.online, activity=activity)

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                self.bot.log.error(f"Error in background presence task: {e}")
                await asyncio.sleep(interval_seconds)  # Continue despite errors


# Legacy alias for backward compatibility
BackGroundTasks = BackgroundTasks
