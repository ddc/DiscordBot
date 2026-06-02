import asyncio
import discord
import time
from anthropic import AsyncAnthropic
from collections.abc import Awaitable, Callable
from discord.ext import commands
from google import genai
from google.genai import types as genai_types
from openai import AsyncOpenAI
from openai.types.responses import WebSearchToolParam
from openai.types.shared import ReasoningEffort
from openai.types.shared_params import Reasoning
from src.bot.constants.settings import BotSettings, get_bot_settings
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils
from src.bot.tools.cooldowns import CoolDowns


class OpenAi(commands.Cog):
    """LLM chat commands (OpenAI / Anthropic Claude / Google Gemini) with optional web search."""

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self._bot_settings: BotSettings = get_bot_settings()
        self._openai_client: AsyncOpenAI = AsyncOpenAI(api_key=self._bot_settings.openai_api_key)
        self._anthropic_client: AsyncAnthropic = AsyncAnthropic(api_key=self._bot_settings.anthropic_api_key)
        self._gemini_client: genai.Client = genai.Client(api_key=self._bot_settings.gemini_api_key)
        self._effort: ReasoningEffort = "xhigh"
        self._instructions: str = "You are a helpful AI assistant."
        self._instructions_web: str = (
            "You are a helpful AI assistant. When answering factual questions, use web search and base your "
            "answer only on information directly supported by the sources. Do not invent or extrapolate specific "
            "numbers, statistics, or breakdowns that the sources do not explicitly state. Cite the source URL(s)."
        )

    # ─────────────────────────── Commands ───────────────────────────

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, CoolDowns.OpenAI.value, commands.BucketType.user)
    async def gpt(self, ctx: commands.Context, *, msg_text: str) -> None:
        """Ask OpenAI's GPT model for a direct answer (no web search)."""
        await self._run_chat(ctx, msg_text, provider="openai", use_web=False)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, CoolDowns.OpenAI.value, commands.BucketType.user)
    async def gptweb(self, ctx: commands.Context, *, msg_text: str) -> None:
        """Ask OpenAI's GPT model with web search enabled — for current/factual info."""
        await self._run_chat(ctx, msg_text, provider="openai", use_web=True)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, CoolDowns.OpenAI.value, commands.BucketType.user)
    async def claude(self, ctx: commands.Context, *, msg_text: str) -> None:
        """Ask Anthropic's Claude model for a direct answer (no web search)."""
        await self._run_chat(ctx, msg_text, provider="anthropic", use_web=False)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, CoolDowns.OpenAI.value, commands.BucketType.user)
    async def claudeweb(self, ctx: commands.Context, *, msg_text: str) -> None:
        """Ask Anthropic's Claude model with web search enabled — for current/factual info."""
        await self._run_chat(ctx, msg_text, provider="anthropic", use_web=True)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, CoolDowns.OpenAI.value, commands.BucketType.user)
    async def gemini(self, ctx: commands.Context, *, msg_text: str) -> None:
        """Ask Google's Gemini model for a direct answer (no web search)."""
        await self._run_chat(ctx, msg_text, provider="gemini", use_web=False)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, CoolDowns.OpenAI.value, commands.BucketType.user)
    async def geminiweb(self, ctx: commands.Context, *, msg_text: str) -> None:
        """Ask Google's Gemini model with Google Search grounding enabled."""
        await self._run_chat(ctx, msg_text, provider="gemini", use_web=True)

    # ─────────────────────────── Shared flow ───────────────────────────

    async def _run_chat(self, ctx: commands.Context, msg_text: str, provider: str, use_web: bool) -> None:
        """Send progress message, dispatch to provider, time, post answer."""
        progress_text = (
            "Please wait, I'm thinking and searching the web for an accurate answer..."
            if use_web
            else "Please wait, I'm thinking..."
        )
        progress_embed = discord.Embed(
            description=f"🔄 **{progress_text}** (this may take a moment)",
            color=discord.Color.blurple(),
        )
        progress_embed.set_author(name=ctx.author.display_name, icon_url=getattr(ctx.author.avatar, "url", None))
        progress_msg = await bot_utils.send_with_retry(ctx, ctx.send, embed=progress_embed)

        start = time.monotonic()
        try:
            response_text = await self._call_provider_with_retry(
                lambda: self._dispatch(provider, msg_text, use_web),
                progress_msg,
            )
            color = discord.Color.green()
            description = response_text
        except Exception as e:
            self.bot.log.error(f"{provider} API error: {e}")
            color = discord.Color.red()
            description = f"Sorry, I encountered an error: {e}"
        elapsed = time.monotonic() - start

        try:
            await progress_msg.delete()
        except discord.HTTPException:
            pass

        model = self._model_for(provider)
        embeds = self._create_ai_embeds(ctx, description, color, elapsed, model)
        if len(embeds) == 1:
            await bot_utils.send_embed(ctx, embeds[0], False)
        else:
            view = bot_utils.EmbedPaginatorView(embeds, ctx.author.id)
            await view.send_and_save(ctx)

    async def _dispatch(self, provider: str, message: str, use_web: bool) -> str:
        if provider == "openai":
            return await self._get_openai_response(message, use_web=use_web)
        if provider == "anthropic":
            return await self._get_claude_response(message, use_web=use_web)
        if provider == "gemini":
            return await self._get_gemini_response(message, use_web=use_web)
        raise ValueError(f"Unknown provider: {provider}")

    def _model_for(self, provider: str) -> str:
        return {
            "openai": self._bot_settings.openai_model,
            "anthropic": self._bot_settings.anthropic_model,
            "gemini": self._bot_settings.gemini_model,
        }[provider]

    # ─────────────────────────── Retry-on-transient ───────────────────────────

    _TRANSIENT_STATUSES = frozenset({429, 500, 502, 503, 504})

    @staticmethod
    def _is_transient_provider_error(e: BaseException) -> bool:
        """True for retry-worthy HTTP errors from any of the three LLM SDKs.

        Anthropic and OpenAI expose `.status_code` on their `APIStatusError` types;
        google-genai uses `.code` on `ClientError`/`ServerError`. We duck-type
        across both attribute names to avoid SDK-specific isinstance checks.
        """
        s = getattr(e, "status_code", None)
        if isinstance(s, int) and s in OpenAi._TRANSIENT_STATUSES:
            return True
        c = getattr(e, "code", None)
        if isinstance(c, int) and c in OpenAi._TRANSIENT_STATUSES:
            return True
        return False

    async def _call_provider_with_retry(
        self,
        coro_factory: Callable[[], Awaitable[str]],
        progress_msg: discord.Message | None,
        *,
        max_attempts: int = 2,
        base_delay: float = 2.0,
    ) -> str:
        """Run `coro_factory()` with one retry on transient provider errors.

        On the first transient failure, edits `progress_msg` to a "retrying"
        embed and sleeps `base_delay` seconds, then tries again. Non-transient
        errors and the final-attempt failure propagate.
        """
        notified = False
        for attempt in range(1, max_attempts + 1):
            try:
                return await coro_factory()
            except Exception as e:
                if not self._is_transient_provider_error(e) or attempt >= max_attempts:
                    raise
                self.bot.log.warning(
                    f"Transient provider error, retrying in {base_delay:.1f}s "
                    f"(attempt {attempt}/{max_attempts - 1}): {e}"
                )
                if not notified and progress_msg is not None:
                    try:
                        retry_embed = discord.Embed(
                            description="🔄 **Provider hiccup — retrying...** (this may take a moment)",
                            color=discord.Color.orange(),
                        )
                        await progress_msg.edit(embed=retry_embed)
                        notified = True
                    except discord.HTTPException:
                        pass
                await asyncio.sleep(base_delay)
        # Unreachable: the loop above either returns or raises.
        raise RuntimeError("retry loop exited without returning")  # pragma: no cover

    # ─────────────────────────── Provider calls ───────────────────────────

    async def _get_openai_response(self, message: str, use_web: bool) -> str:
        """Call OpenAI's Responses API with optional web_search tool."""
        instructions = self._instructions_web if use_web else self._instructions
        tools: list[WebSearchToolParam] = [WebSearchToolParam(type="web_search")] if use_web else []
        response = await self._openai_client.responses.create(
            instructions=instructions,
            model=self._bot_settings.openai_model,
            reasoning=Reasoning(effort=self._effort),
            tools=tools,
            max_output_tokens=None,
            input=message,
        )
        content = response.output_text
        return content.strip() if content else ""

    async def _get_claude_response(self, message: str, use_web: bool) -> str:
        """Call Anthropic Messages API with optional web_search server tool."""
        instructions = self._instructions_web if use_web else self._instructions
        tools = [{"type": "web_search_20250305", "name": "web_search"}] if use_web else []
        response = await self._anthropic_client.messages.create(
            model=self._bot_settings.anthropic_model,
            max_tokens=4096,
            system=instructions,
            messages=[{"role": "user", "content": message}],
            tools=tools,
        )
        # Concatenate all text blocks (web search may interleave tool-use blocks).
        text_parts = [
            getattr(block, "text", "") for block in response.content if getattr(block, "type", None) == "text"
        ]
        content = "".join(text_parts).strip()
        return content

    async def _get_gemini_response(self, message: str, use_web: bool) -> str:
        """Call Google Gemini with optional Google Search grounding."""
        instructions = self._instructions_web if use_web else self._instructions
        config_kwargs: dict = {"system_instruction": instructions}
        if use_web:
            config_kwargs["tools"] = [genai_types.Tool(google_search=genai_types.GoogleSearch())]
        config = genai_types.GenerateContentConfig(**config_kwargs)
        response = await self._gemini_client.aio.models.generate_content(
            model=self._bot_settings.gemini_model,
            contents=message,
            config=config,
        )
        content = response.text or ""
        return content.strip()

    # ─────────────────────────── Embed formatting ───────────────────────────

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format an elapsed duration as e.g. '5ms' (sub-second) or '20s'."""
        if seconds < 1:
            return f"{round(seconds * 1000)}ms"
        return f"{round(seconds)}s"

    def _create_ai_embeds(
        self,
        ctx: commands.Context,
        description: str,
        color: discord.Color,
        elapsed: float = 0.0,
        model: str | None = None,
    ) -> list[discord.Embed]:
        """Create formatted embed(s) for an AI response, paginating if needed."""
        if model is None:
            model = self._bot_settings.openai_model
        duration = self._format_duration(elapsed)
        max_length = 2000
        chunks: list[str] = []

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
                name=ctx.author.display_name,
                icon_url=getattr(ctx.author.avatar, "url", None),
            )
            footer_text = f"{model} | {duration} | {bot_utils.get_current_date_time_str_long()} UTC"
            if len(chunks) > 1:
                footer_text = f"Page {i + 1}/{len(chunks)} | {footer_text}"
            embed.set_footer(
                icon_url=ctx.bot.user.avatar.url if ctx.bot.user and ctx.bot.user.avatar else None,
                text=footer_text,
            )
            pages.append(embed)

        return pages


async def setup(bot: Bot) -> None:
    """Setup function to add the OpenAi cog to the bot."""
    await bot.add_cog(OpenAi(bot))
