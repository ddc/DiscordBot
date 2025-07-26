"""OpenAI integration for Discord bot commands."""

import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from src.bot.constants.settings import get_bot_settings
from src.bot.tools import bot_utils
from src.bot.tools.cooldowns import CoolDowns




class OpenAi(commands.Cog):
    """OpenAI-powered commands for AI assistance and text generation."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._openai_client: OpenAI | None = None

    @commands.command()
    @commands.cooldown(1, CoolDowns.OpenAI.value, BucketType.user)
    async def ai(self, ctx: commands.Context, *, msg_text: str) -> None:
        """Ask OpenAI for assistance with any question or task.

        Usage:
            ai What is Python?
            ai Write a haiku about programming
            ai Explain quantum computing in simple terms
        """
        await ctx.message.channel.typing()

        try:
            response_text = await self._get_ai_response(msg_text)
            color = discord.Color.green()
            description = response_text
        except Exception as e:
            self.bot.log.error(f"OpenAI API error: {e}")
            color = discord.Color.red()
            description = f"Sorry, I encountered an error: {str(e)}"

        embed = self._create_ai_embed(ctx, description, color)
        await bot_utils.send_embed(ctx, embed, False)

    @property
    def openai_client(self) -> OpenAI:
        """Get or create OpenAI client instance."""
        if self._openai_client is None:
            self._openai_client = OpenAI()
        return self._openai_client

    async def _get_ai_response(self, message: str) -> str:
        """Get response from OpenAI API."""
        model = get_bot_settings().openai_model

        # Create properly typed messages for OpenAI API
        messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content="You are a helpful AI assistant. Provide clear, concise, and accurate responses."
            ),
            ChatCompletionUserMessageParam(role="user", content=message),
        ]

        # Use the correct OpenAI API endpoint
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    @staticmethod
    def _create_ai_embed(ctx: commands.Context, description: str, color: discord.Color) -> discord.Embed:
        """Create formatted embed for AI response."""
        # Truncate long responses to fit Discord limits
        if len(description) > 2000:
            description = description[:1997] + "..."

        embed = discord.Embed(color=color, description=description)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.set_footer(
            icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None,
            text=f"{bot_utils.get_current_date_time_str_long()} UTC",
        )

        return embed


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the OpenAi cog to the bot."""
    await bot.add_cog(OpenAi(bot))
