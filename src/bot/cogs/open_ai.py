import discord
from discord.ext import commands
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from src.bot.constants.settings import get_bot_settings
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils
from src.bot.tools.cooldowns import CoolDowns


class OpenAi(commands.Cog):
    """OpenAI-powered commands for AI assistance and text generation."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._openai_client: OpenAI | None = None

    @commands.command()
    @commands.cooldown(1, CoolDowns.OpenAI.value, commands.BucketType.user)
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
            description = f"Sorry, I encountered an error: {e}"

        embeds = self._create_ai_embeds(ctx, description, color)
        if len(embeds) == 1:
            await bot_utils.send_embed(ctx, embeds[0], False)
        else:
            view = bot_utils.EmbedPaginatorView(embeds, ctx.author.id)
            msg = await ctx.send(embed=embeds[0], view=view)
            view.message = msg

    @property
    def openai_client(self) -> OpenAI:
        """Get or create OpenAI client instance."""
        if self._openai_client is None:
            api_key = get_bot_settings().openai_api_key
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    async def _get_ai_response(self, message: str) -> str:
        """Get response from OpenAI API."""
        model = get_bot_settings().openai_model

        # Create properly typed messages for OpenAI API
        messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content="You are a helpful AI assistant. Provide clear, concise, and accurate responses.",
            ),
            ChatCompletionUserMessageParam(role="user", content=message),
        ]

        # Use the correct OpenAI API endpoint
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    @staticmethod
    def _create_ai_embeds(ctx: commands.Context, description: str, color: discord.Color) -> list[discord.Embed]:
        """Create formatted embed(s) for AI response, paginating if needed."""
        max_length = 2000
        chunks = []

        while description:
            if len(description) <= max_length:
                chunks.append(description)
                break
            split_index = description.rfind("\n", 0, max_length)
            if split_index == -1:
                split_index = description.rfind(" ", 0, max_length)
            if split_index == -1:
                split_index = max_length
            chunks.append(description[:split_index])
            description = description[split_index:].lstrip()

        pages = []
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(color=color, description=chunk)
            embed.set_author(
                name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None
            )
            footer_text = bot_utils.get_current_date_time_str_long() + " UTC"
            if len(chunks) > 1:
                footer_text = f"Page {i + 1}/{len(chunks)} | {footer_text}"
            embed.set_footer(
                icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None,
                text=footer_text,
            )
            pages.append(embed)

        return pages


async def setup(bot: Bot) -> None:
    """Setup function to add the OpenAi cog to the bot."""
    await bot.add_cog(OpenAi(bot))
