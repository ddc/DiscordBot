from discord.ext import commands
from src.bot.constants import messages
from src.bot.discord_bot import Bot


class OnResumed(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_resumed(self) -> None:
        """Called when the client has resumed a session after a disconnect"""
        try:
            self.bot.log.info(messages.bot_resumed(self.bot.user))
        except Exception as e:
            print(f"Bot resumed - logging failed: {e}")


async def setup(bot: Bot) -> None:
    await bot.add_cog(OnResumed(bot))
