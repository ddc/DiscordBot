"""Comprehensive tests for the AI cog."""

import discord
import pytest
import sys
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules["ddcDatabases"] = Mock()

from src.bot.cogs.ai import AI
lazy from src.bot.cogs.ai import setup


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.db_session = MagicMock()
    bot.log = MagicMock()
    bot.user = MagicMock()
    bot.user.avatar = MagicMock()
    bot.user.avatar.url = "https://example.com/bot_avatar.png"
    return bot


@pytest.fixture
def ai_cog(mock_bot):
    """Create an AI cog instance."""
    with (
        patch("src.bot.cogs.ai.get_bot_settings") as mock_settings,
        patch("src.bot.cogs.ai.AsyncOpenAI"),
        patch("src.bot.cogs.ai.AsyncAnthropic"),
        patch("src.bot.cogs.ai.genai.Client"),
    ):
        mock_settings.return_value = MagicMock(
            openai_api_key="test-key",
            openai_model="gpt-3.5-turbo",
            anthropic_api_key="test-anthropic-key",
            anthropic_model="claude-test",
            gemini_api_key="test-gemini-key",
            gemini_model="gemini-test",
            default_ai_model="gpt",
        )
        return AI(mock_bot)


@pytest.fixture
def mock_ctx():
    """Create a mock context."""
    ctx = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    ctx.guild.name = "Test Server"

    author = MagicMock()
    author.id = 67890
    author.display_name = "TestUser"
    author.avatar = MagicMock()
    author.avatar.url = "https://example.com/avatar.png"

    ctx.author = author
    ctx.message = MagicMock()
    ctx.message.author = author
    ctx.message.channel = AsyncMock()
    ctx.prefix = "!"

    return ctx


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI Responses API response."""
    response = MagicMock()
    response.output_text = "This is a mock AI response from OpenAI."
    return response


@pytest.fixture
def mock_bot_settings():
    """Create mock bot settings."""
    settings = MagicMock()
    settings.openai_model = "gpt-3.5-turbo"
    return settings


class TestAI:
    """Test cases for AI cog."""

    def test_init(self, mock_bot):
        """Test AI cog initialization."""
        with patch("src.bot.cogs.ai.get_bot_settings") as mock_settings, patch("src.bot.cogs.ai.AsyncOpenAI"):
            mock_settings.return_value = MagicMock(openai_api_key="test-key", openai_model="gpt-3.5-turbo")
            cog = AI(mock_bot)
            assert cog.bot == mock_bot
            assert cog._openai_client is not None
            assert hasattr(cog, "_bot_settings")

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_ai_command_success(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings, mock_openai_response
    ):
        """Test successful AI command execution."""
        mock_get_settings.return_value = mock_bot_settings

        with patch.object(ai_cog, "_get_openai_response", return_value="AI response here"):
            await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text="What is Python?")

            mock_ctx.send.assert_called_once()
            mock_send_embed.assert_called_once()

            embed = mock_send_embed.call_args[0][1]
            assert embed.color == discord.Color.green()
            assert embed.description == "AI response here"
            assert embed.author.name == "TestUser"
            assert embed.author.icon_url == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_aiweb_command_success(self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings):
        """`aiweb` runs the shared flow with use_web=True (web search enabled)."""
        mock_get_settings.return_value = mock_bot_settings

        with patch.object(ai_cog, "_get_openai_response", return_value="web answer") as mock_get_response:
            await ai_cog.gptweb.callback(ai_cog, mock_ctx, msg_text="Latest news")

            mock_get_response.assert_awaited_once_with("Latest news", use_web=True)
            mock_ctx.send.assert_called_once()
            mock_send_embed.assert_called_once()
            embed = mock_send_embed.call_args[0][1]
            assert embed.description == "web answer"
            assert embed.color == discord.Color.green()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_ai_command_uses_plain_path(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """`ai` routes through _get_openai_response with use_web=False."""
        mock_get_settings.return_value = mock_bot_settings

        with patch.object(ai_cog, "_get_openai_response", return_value="plain answer") as mock_get_response:
            await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text="What is Python?")

            mock_get_response.assert_awaited_once_with("What is Python?", use_web=False)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_claude_command_routes_to_anthropic_plain(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """`claude` runs _get_claude_response with use_web=False."""
        mock_get_settings.return_value = mock_bot_settings
        with patch.object(ai_cog, "_get_claude_response", return_value="claude answer") as mock_get_response:
            await ai_cog.claude.callback(ai_cog, mock_ctx, msg_text="hi")
            mock_get_response.assert_awaited_once_with("hi", use_web=False)
            mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_claudeweb_command_routes_to_anthropic_web(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """`claudeweb` runs _get_claude_response with use_web=True."""
        mock_get_settings.return_value = mock_bot_settings
        with patch.object(ai_cog, "_get_claude_response", return_value="claude web answer") as mock_get_response:
            await ai_cog.claudeweb.callback(ai_cog, mock_ctx, msg_text="news")
            mock_get_response.assert_awaited_once_with("news", use_web=True)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_gemini_command_routes_to_gemini_plain(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """`gemini` runs _get_gemini_response with use_web=False."""
        mock_get_settings.return_value = mock_bot_settings
        with patch.object(ai_cog, "_get_gemini_response", return_value="gemini answer") as mock_get_response:
            await ai_cog.gemini.callback(ai_cog, mock_ctx, msg_text="hi")
            mock_get_response.assert_awaited_once_with("hi", use_web=False)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_geminiweb_command_routes_to_gemini_web(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """`geminiweb` runs _get_gemini_response with use_web=True."""
        mock_get_settings.return_value = mock_bot_settings
        with patch.object(ai_cog, "_get_gemini_response", return_value="gemini web answer") as mock_get_response:
            await ai_cog.geminiweb.callback(ai_cog, mock_ctx, msg_text="news")
            mock_get_response.assert_awaited_once_with("news", use_web=True)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_progress_delete_failure_is_tolerated(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """If progress_msg.delete() raises discord.HTTPException, _run_chat still posts the answer."""

        mock_get_settings.return_value = mock_bot_settings
        progress_msg = MagicMock()
        progress_msg.delete = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "boom"))
        mock_ctx.send = AsyncMock(return_value=progress_msg)

        with patch.object(ai_cog, "_get_openai_response", return_value="hi"):
            await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text="hi")

        mock_send_embed.assert_called_once()
        progress_msg.delete.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_footer_carries_active_provider_model(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """Embed footer reflects the active provider's model, not OpenAI's by default."""
        mock_get_settings.return_value = mock_bot_settings
        with patch.object(ai_cog, "_get_claude_response", return_value="claude says hi"):
            await ai_cog.claude.callback(ai_cog, mock_ctx, msg_text="hi")

        embed = mock_send_embed.call_args[0][1]
        assert "claude-test" in embed.footer.text

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_progress_message_text_differs_by_use_web(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """Web-enabled commands show 'searching the web' in the progress embed; plain ones don't."""
        mock_get_settings.return_value = mock_bot_settings

        with patch.object(ai_cog, "_get_openai_response", return_value="x"):
            await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text="hi")
            plain_embed = mock_ctx.send.call_args[1]["embed"]
            assert "searching the web" not in plain_embed.description.lower()

            mock_ctx.send.reset_mock()
            mock_send_embed.reset_mock()

            await ai_cog.gptweb.callback(ai_cog, mock_ctx, msg_text="hi")
            web_embed = mock_ctx.send.call_args[1]["embed"]
            assert "searching the web" in web_embed.description.lower()

    def test_is_transient_provider_error_status_code(self, ai_cog):
        """Detects transient HTTP errors via .status_code (Anthropic/OpenAI shape)."""
        for code in (429, 500, 502, 503, 504):
            e = MagicMock(spec=Exception)
            e.status_code = code
            assert ai_cog._is_transient_provider_error(e) is True

    def test_is_transient_provider_error_code_attr(self, ai_cog):
        """Detects transient HTTP errors via .code (google-genai shape)."""

        class GenaiLike(Exception):
            def __init__(self, code):
                self.code = code

        for code in (429, 503):
            assert ai_cog._is_transient_provider_error(GenaiLike(code)) is True

    def test_is_transient_provider_error_non_transient(self, ai_cog):
        """4xx (non-429) and bare exceptions are NOT transient."""
        for code in (400, 401, 403, 404):
            e = MagicMock(spec=Exception)
            e.status_code = code
            assert ai_cog._is_transient_provider_error(e) is False
        assert ai_cog._is_transient_provider_error(Exception("plain")) is False

    @pytest.mark.asyncio
    async def test_call_provider_with_retry_success_first_attempt_no_edit(self, ai_cog):
        """Happy path: factory succeeds first try, progress_msg is not touched."""
        progress = MagicMock()
        progress.edit = AsyncMock()
        factory = AsyncMock(return_value="ok")

        result = await ai_cog._call_provider_with_retry(factory, progress)

        assert result == "ok"
        factory.assert_awaited_once()
        progress.edit.assert_not_called()

    @pytest.mark.asyncio
    async def test_call_provider_with_retry_retries_on_transient(self, ai_cog):
        """503 once, then success — total one retry, progress edited to 'retrying'."""

        class Transient(Exception):
            status_code = 503

        factory = AsyncMock(side_effect=[Transient("overloaded"), "ok"])
        progress = MagicMock()
        progress.edit = AsyncMock()

        with patch("src.bot.cogs.ai.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await ai_cog._call_provider_with_retry(factory, progress, base_delay=0.01)

        assert result == "ok"
        assert factory.await_count == 2
        progress.edit.assert_awaited_once()
        edit_kwargs = progress.edit.call_args[1]
        assert "retrying" in edit_kwargs["embed"].description.lower()
        mock_sleep.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_call_provider_with_retry_does_not_retry_on_non_transient(self, ai_cog):
        """4xx (non-429) — raise immediately, no retry, no progress edit."""

        class HardFail(Exception):
            status_code = 400

        factory = AsyncMock(side_effect=HardFail("bad request"))
        progress = MagicMock()
        progress.edit = AsyncMock()

        with pytest.raises(HardFail):
            await ai_cog._call_provider_with_retry(factory, progress)

        factory.assert_awaited_once()
        progress.edit.assert_not_called()

    @pytest.mark.asyncio
    async def test_call_provider_with_retry_exhausts_then_raises(self, ai_cog):
        """All attempts transient — final raises, progress edited once."""

        class Transient(Exception):
            status_code = 503

        factory = AsyncMock(side_effect=Transient("overloaded"))
        progress = MagicMock()
        progress.edit = AsyncMock()

        with patch("src.bot.cogs.ai.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(Transient):
                await ai_cog._call_provider_with_retry(factory, progress, max_attempts=2)

        assert factory.await_count == 2
        progress.edit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_call_provider_with_retry_edit_failure_is_tolerated(self, ai_cog):
        """If editing the progress message fails, retry still happens silently."""

        class Transient(Exception):
            status_code = 503

        factory = AsyncMock(side_effect=[Transient("x"), "ok"])
        progress = MagicMock()
        progress.edit = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "no edit"))

        with patch("src.bot.cogs.ai.asyncio.sleep", new_callable=AsyncMock):
            result = await ai_cog._call_provider_with_retry(factory, progress, base_delay=0.01)

        assert result == "ok"
        assert factory.await_count == 2

    @pytest.mark.asyncio
    async def test_call_provider_with_retry_no_progress_msg(self, ai_cog):
        """progress_msg=None is allowed; retry still works, just no edit attempt."""

        class Transient(Exception):
            status_code = 503

        factory = AsyncMock(side_effect=[Transient("x"), "ok"])

        with patch("src.bot.cogs.ai.asyncio.sleep", new_callable=AsyncMock):
            result = await ai_cog._call_provider_with_retry(factory, None, base_delay=0.01)

        assert result == "ok"
        assert factory.await_count == 2

    @pytest.mark.asyncio
    async def test_dispatch_unknown_provider_raises(self, ai_cog):
        """_dispatch raises ValueError on unknown provider."""
        with pytest.raises(ValueError):
            await ai_cog._dispatch("notaprovider", "hi", False)

    @pytest.mark.asyncio
    async def test_get_claude_response_concatenates_text_blocks(self, ai_cog):
        """_get_claude_response joins text blocks and strips."""
        block_text = MagicMock(type="text", text="part one ")
        block_tool = MagicMock(type="tool_use", text="ignored")
        block_text2 = MagicMock(type="text", text="part two")
        mock_response = MagicMock(content=[block_text, block_tool, block_text2])
        ai_cog._anthropic_client = MagicMock()
        ai_cog._anthropic_client.messages.create = AsyncMock(return_value=mock_response)

        result = await ai_cog._get_claude_response("hi", use_web=False)

        assert result == "part one part two"
        call_args = ai_cog._anthropic_client.messages.create.call_args[1]
        assert call_args["model"] == "claude-test"
        assert call_args["system"] == ai_cog._instructions
        assert call_args["tools"] == []
        assert call_args["messages"] == [{"role": "user", "content": "hi"}]

    @pytest.mark.asyncio
    async def test_get_claude_response_web_enables_tool(self, ai_cog):
        """use_web=True enables the web_search server tool and uses web instructions."""
        block_text = MagicMock(type="text", text="ok")
        mock_response = MagicMock(content=[block_text])
        ai_cog._anthropic_client = MagicMock()
        ai_cog._anthropic_client.messages.create = AsyncMock(return_value=mock_response)

        await ai_cog._get_claude_response("hi", use_web=True)

        call_args = ai_cog._anthropic_client.messages.create.call_args[1]
        assert call_args["tools"] == [
            {"type": "web_search_20260318", "name": "web_search", "response_inclusion": "excluded"}
        ]
        assert call_args["system"] == ai_cog._instructions_web

    @pytest.mark.asyncio
    async def test_get_gemini_response_plain(self, ai_cog):
        """Plain Gemini call has no tools and uses plain instructions."""
        mock_response = MagicMock(text="gemini reply  ")
        ai_cog._gemini_client = MagicMock()
        ai_cog._gemini_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        result = await ai_cog._get_gemini_response("hi", use_web=False)

        assert result == "gemini reply"
        call_args = ai_cog._gemini_client.aio.models.generate_content.call_args[1]
        assert call_args["model"] == "gemini-test"
        assert call_args["contents"] == "hi"
        assert "tools" not in call_args["config"].model_dump(exclude_none=True) or call_args["config"].tools is None

    @pytest.mark.asyncio
    async def test_get_gemini_response_web_adds_google_search_tool(self, ai_cog):
        """use_web=True attaches a GoogleSearch tool in the config."""
        mock_response = MagicMock(text="ok")
        ai_cog._gemini_client = MagicMock()
        ai_cog._gemini_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        await ai_cog._get_gemini_response("hi", use_web=True)

        call_args = ai_cog._gemini_client.aio.models.generate_content.call_args[1]
        assert call_args["config"].tools is not None
        assert any(getattr(t, "google_search", None) is not None for t in call_args["config"].tools)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_ai_command_error(self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings):
        """Test AI command with OpenAI API error."""
        mock_get_settings.return_value = mock_bot_settings

        with patch.object(ai_cog, "_get_openai_response", side_effect=Exception("API Error")):
            await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text="What is Python?")

            mock_ctx.send.assert_called_once()
            mock_send_embed.assert_called_once()

            embed = mock_send_embed.call_args[0][1]
            assert embed.color == discord.Color.red()
            assert "Sorry, I encountered an error" in embed.description
            assert "API Error" in embed.description

            ai_cog.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    async def test_get_openai_response_success(
        self, mock_get_settings, ai_cog, mock_bot_settings, mock_openai_response
    ):
        """Test successful _get_openai_response method."""
        mock_get_settings.return_value = mock_bot_settings

        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        ai_cog._openai_client = mock_client

        result = await ai_cog._get_openai_response("What is Python?", use_web=False)

        assert result == "This is a mock AI response from OpenAI."

        mock_client.responses.create.assert_called_once()
        call_args = mock_client.responses.create.call_args

        assert call_args[1]["model"] == "gpt-3.5-turbo"
        assert call_args[1]["max_output_tokens"] is None
        assert call_args[1]["instructions"] == ai_cog._instructions
        assert call_args[1]["input"] == "What is Python?"
        assert call_args[1]["reasoning"]["effort"] == "xhigh"
        assert call_args[1]["tools"] == []

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    async def test_get_openai_response_web_success(
        self, mock_get_settings, ai_cog, mock_bot_settings, mock_openai_response
    ):
        """Web variant: uses web-grounded instructions and the web_search tool."""
        mock_get_settings.return_value = mock_bot_settings

        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        ai_cog._openai_client = mock_client

        result = await ai_cog._get_openai_response("What is Python?", use_web=True)

        assert result == "This is a mock AI response from OpenAI."
        call_args = mock_client.responses.create.call_args
        assert call_args[1]["instructions"] == ai_cog._instructions_web
        assert call_args[1]["tools"][0]["type"] == "web_search"
        assert call_args[1]["reasoning"]["effort"] == "xhigh"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    async def test_get_openai_response_with_leading_trailing_spaces(
        self, mock_get_settings, ai_cog, mock_bot_settings, mock_openai_response
    ):
        """Test _get_openai_response strips leading/trailing spaces."""
        mock_get_settings.return_value = mock_bot_settings
        mock_openai_response.output_text = "  Response with spaces  "

        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        ai_cog._openai_client = mock_client

        result = await ai_cog._get_openai_response("Test message", use_web=False)

        assert result == "Response with spaces"

    def test_create_ai_embeds_normal_length(self, ai_cog, mock_ctx):
        """Test _create_ai_embeds with normal length description."""
        description = "This is a normal length response."
        color = discord.Color.blue()

        embeds = ai_cog._create_ai_embeds(mock_ctx, description, color)

        assert len(embeds) == 1
        assert isinstance(embeds[0], discord.Embed)
        assert embeds[0].color == color
        assert embeds[0].description == description
        assert embeds[0].author.name == "TestUser"
        assert embeds[0].author.icon_url == "https://example.com/avatar.png"

    def test_create_ai_embeds_long_description(self, ai_cog, mock_ctx):
        """Test _create_ai_embeds with description exceeding 1000 characters paginates."""
        long_description = "a" * 2010
        color = discord.Color.green()

        embeds = ai_cog._create_ai_embeds(mock_ctx, long_description, color)

        assert len(embeds) == 3
        assert all(len(e.description) <= 1000 for e in embeds)
        assert "".join(e.description for e in embeds) == long_description
        assert "Page 1/3" in embeds[0].footer.text
        assert "Page 3/3" in embeds[2].footer.text

    def test_create_ai_embeds_exactly_1000_chars(self, ai_cog, mock_ctx):
        """Test _create_ai_embeds with exactly 1000 characters returns single page."""
        description = "a" * 1000
        color = discord.Color.red()

        embeds = ai_cog._create_ai_embeds(mock_ctx, description, color)

        assert len(embeds) == 1
        assert embeds[0].description == description
        assert len(embeds[0].description) == 1000

    def test_create_ai_embeds_no_author_avatar(self, ai_cog, mock_ctx):
        """Test _create_ai_embeds when author has no avatar."""
        mock_ctx.author.avatar = None
        description = "Test response"
        color = discord.Color.orange()

        embeds = ai_cog._create_ai_embeds(mock_ctx, description, color)

        assert embeds[0].author.name == "TestUser"
        assert embeds[0].author.icon_url is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("default_ai_model", "provider"),
        [("claude", "anthropic"), ("gpt", "openai"), ("gemini", "gemini")],
    )
    async def test_ai_command_uses_default_ai_model(self, ai_cog, mock_ctx, default_ai_model, provider):
        """`ai` routes to the provider chosen by BOT_DEFAULT_AI_MODEL, without web search."""
        ai_cog._bot_settings.default_ai_model = default_ai_model
        with patch.object(ai_cog, "_run_chat", new_callable=AsyncMock) as mock_run_chat:
            await ai_cog.ai.callback(ai_cog, mock_ctx, msg_text="What is Python?")
        mock_run_chat.assert_awaited_once_with(mock_ctx, "What is Python?", provider=provider, use_web=False)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("default_ai_model", "provider"),
        [("claude", "anthropic"), ("gpt", "openai"), ("gemini", "gemini")],
    )
    async def test_aiweb_command_uses_default_ai_model_with_web(self, ai_cog, mock_ctx, default_ai_model, provider):
        """`aiweb` routes to the BOT_DEFAULT_AI_MODEL provider with web search enabled."""
        ai_cog._bot_settings.default_ai_model = default_ai_model
        with patch.object(ai_cog, "_run_chat", new_callable=AsyncMock) as mock_run_chat:
            await ai_cog.aiweb.callback(ai_cog, mock_ctx, msg_text="Latest Python release?")
        mock_run_chat.assert_awaited_once_with(mock_ctx, "Latest Python release?", provider=provider, use_web=True)

    @pytest.mark.asyncio
    async def test_aiweb_and_claudeweb_commands_are_equivalent_when_default_is_claude(self, ai_cog, mock_ctx):
        ai_cog._bot_settings.default_ai_model = "claude"
        with patch.object(ai_cog, "_run_chat", new_callable=AsyncMock) as mock_run_chat:
            await ai_cog.aiweb.callback(ai_cog, mock_ctx, msg_text="hi")
            await ai_cog.claudeweb.callback(ai_cog, mock_ctx, msg_text="hi")
        aiweb_call, claudeweb_call = mock_run_chat.await_args_list
        assert aiweb_call == claudeweb_call

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.bot_utils.send_embed", new_callable=AsyncMock)
    @patch("src.bot.cogs.ai.bot_utils.send_with_retry", new_callable=AsyncMock)
    async def test_aiweb_end_to_end_uses_default_model_and_footer(
        self, mock_send_retry, mock_send_embed, ai_cog, mock_ctx
    ):
        """Through _run_chat: the web variant of the default provider is called and its model shows in the footer."""
        ai_cog._bot_settings.default_ai_model = "gemini"
        mock_send_retry.return_value = AsyncMock()
        with patch.object(ai_cog, "_get_gemini_response", new_callable=AsyncMock, return_value="answer") as mock_gemini:
            await ai_cog.aiweb.callback(ai_cog, mock_ctx, msg_text="news?")
        mock_gemini.assert_awaited_once_with("news?", use_web=True)
        embed = mock_send_embed.call_args[0][1]
        assert embed.description == "answer"
        assert embed.footer.text.startswith("gemini-test |")

    @pytest.mark.asyncio
    async def test_ai_and_claude_commands_are_equivalent_when_default_is_claude(self, ai_cog, mock_ctx):
        ai_cog._bot_settings.default_ai_model = "claude"
        with patch.object(ai_cog, "_run_chat", new_callable=AsyncMock) as mock_run_chat:
            await ai_cog.ai.callback(ai_cog, mock_ctx, msg_text="hi")
            await ai_cog.claude.callback(ai_cog, mock_ctx, msg_text="hi")
        ai_call, claude_call = mock_run_chat.await_args_list
        assert ai_call == claude_call

    @pytest.mark.parametrize("command_name", ["ai", "aiweb"])
    def test_default_model_commands_have_same_checks_as_other_ai_commands(self, ai_cog, command_name):
        command = getattr(ai_cog, command_name)
        assert command.checks and len(command.checks) == len(ai_cog.claude.checks)
        assert command._buckets._cooldown.rate == ai_cog.claude._buckets._cooldown.rate
        assert command._buckets._cooldown.per == ai_cog.claude._buckets._cooldown.per

    def test_create_ai_embeds_no_bot_avatar(self, ai_cog, mock_ctx):
        """Test _create_ai_embeds when bot has no avatar."""
        mock_ctx.bot.user.avatar = None
        description = "Test response"
        color = discord.Color.purple()

        embeds = ai_cog._create_ai_embeds(mock_ctx, description, color)

        assert embeds[0].footer.icon_url is None
        assert "UTC" in embeds[0].footer.text

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_ai_command_with_different_models(self, mock_send_embed, ai_cog, mock_ctx, mock_openai_response):
        """Test AI command with different OpenAI models."""
        ai_cog._bot_settings.openai_model = "gpt-4"

        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        ai_cog._openai_client = mock_client

        await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text="Test question")

        call_args = mock_client.responses.create.call_args
        assert call_args[1]["model"] == "gpt-4"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_ai_command_with_long_question(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """Test AI command with very long question."""
        mock_get_settings.return_value = mock_bot_settings
        long_question = "What is " + "very " * 1000 + "long question?"

        with patch.object(ai_cog, "_get_openai_response", return_value="Short answer"):
            await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text=long_question)

            mock_send_embed.assert_called_once()
            embed = mock_send_embed.call_args[0][1]
            assert embed.description == "Short answer"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_ai_command_with_special_characters(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """Test AI command with special characters in question."""
        mock_get_settings.return_value = mock_bot_settings
        special_question = "What is 2+2? 🤔 And émojis & spéciál chars?"

        with patch.object(ai_cog, "_get_openai_response", return_value="4! 😊"):
            await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text=special_question)

            mock_send_embed.assert_called_once()
            embed = mock_send_embed.call_args[0][1]
            assert embed.description == "4! 😊"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    async def test_get_openai_response_system_message_content(
        self, mock_get_settings, ai_cog, mock_bot_settings, mock_openai_response
    ):
        """Test that system message has correct content."""
        mock_get_settings.return_value = mock_bot_settings

        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        ai_cog._openai_client = mock_client

        await ai_cog._get_openai_response("Test message", use_web=False)

        call_args = mock_client.responses.create.call_args[1]
        assert call_args["instructions"] == ai_cog._instructions
        assert call_args["input"] == "Test message"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    async def test_get_openai_response_api_parameters(
        self, mock_get_settings, ai_cog, mock_bot_settings, mock_openai_response
    ):
        """Test that OpenAI API is called with correct parameters."""
        mock_get_settings.return_value = mock_bot_settings

        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        ai_cog._openai_client = mock_client

        await ai_cog._get_openai_response("Test message", use_web=False)

        call_args = mock_client.responses.create.call_args[1]
        assert call_args["max_output_tokens"] is None
        assert call_args["reasoning"]["effort"] == "xhigh"
        assert call_args["tools"] == []
        assert "temperature" not in call_args
        assert call_args["model"] == "gpt-3.5-turbo"

    @patch("src.bot.cogs.ai.bot_utils.get_current_date_time_str_long")
    def test_create_ai_embeds_footer(self, mock_get_datetime, ai_cog, mock_ctx):
        """Test that embed footer contains model, duration, and timestamp."""
        mock_get_datetime.return_value = "2023-01-01 12:00:00"

        embeds = ai_cog._create_ai_embeds(mock_ctx, "Test", discord.Color.blue(), elapsed=20.0)

        assert embeds[0].footer.text == "gpt-3.5-turbo | 20s | 2023-01-01 12:00:00 UTC"
        mock_get_datetime.assert_called_once()

    def test_format_duration_milliseconds(self, ai_cog):
        """Sub-second durations are shown in milliseconds."""
        assert ai_cog._format_duration(0.005) == "5ms"
        assert ai_cog._format_duration(0.5) == "500ms"

    def test_format_duration_seconds(self, ai_cog):
        """Durations of one second or more are shown in whole seconds."""
        assert ai_cog._format_duration(1.0) == "1s"
        assert ai_cog._format_duration(20.4) == "20s"
        assert ai_cog._format_duration(119.6) == "120s"

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""

        with patch("src.bot.cogs.ai.get_bot_settings") as mock_settings, patch("src.bot.cogs.ai.AsyncOpenAI"):
            mock_settings.return_value = MagicMock(openai_api_key="test-key", openai_model="gpt-3.5-turbo")
            await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, AI)
        assert added_cog.bot == mock_bot

    def test_ai_cog_inheritance(self, ai_cog):
        """Test that AI cog properly inherits from commands.Cog."""
        assert isinstance(ai_cog, commands.Cog)
        assert hasattr(ai_cog, "bot")

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_ai_command_error_logging(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """Test that errors are properly logged."""
        mock_get_settings.return_value = mock_bot_settings
        test_error = Exception("Test API Error")

        with patch.object(ai_cog, "_get_openai_response", side_effect=test_error):
            await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text="Test question")

            ai_cog.bot.log.error.assert_called_once()
            log_call = ai_cog.bot.log.error.call_args[0][0]
            assert "API error:" in log_call
            assert "Test API Error" in log_call

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    @patch("src.bot.cogs.ai.bot_utils.send_embed")
    async def test_ai_command_send_embed_parameters(
        self, mock_send_embed, mock_get_settings, ai_cog, mock_ctx, mock_bot_settings
    ):
        """Test that send_embed is called with correct parameters."""
        mock_get_settings.return_value = mock_bot_settings

        with patch.object(ai_cog, "_get_openai_response", return_value="Test response"):
            await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text="Test question")

            mock_send_embed.assert_called_once()
            call_args = mock_send_embed.call_args[0]
            assert call_args[0] == mock_ctx
            assert isinstance(call_args[1], discord.Embed)
            assert call_args[2] is False

    @pytest.mark.asyncio
    @patch("src.bot.cogs.ai.get_bot_settings")
    async def test_get_openai_response_empty_response(self, mock_get_settings, ai_cog, mock_bot_settings):
        """Test _get_openai_response with empty response from OpenAI."""
        mock_get_settings.return_value = mock_bot_settings

        mock_response = MagicMock()
        mock_response.output_text = "   "

        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_response)
        ai_cog._openai_client = mock_client

        result = await ai_cog._get_openai_response("Test message", use_web=False)

        assert result == ""

    def test_create_ai_embeds_edge_case_997_chars(self, ai_cog, mock_ctx):
        """Test _create_ai_embeds with exactly 997 characters returns single page."""
        description = "a" * 997
        color = discord.Color.teal()

        embeds = ai_cog._create_ai_embeds(mock_ctx, description, color)

        assert len(embeds) == 1
        assert embeds[0].description == description
        assert len(embeds[0].description) == 997

    def test_create_ai_embeds_edge_case_998_chars(self, ai_cog, mock_ctx):
        """Test _create_ai_embeds with 998 characters returns single page."""
        description = "a" * 998
        color = discord.Color.magenta()

        embeds = ai_cog._create_ai_embeds(mock_ctx, description, color)

        assert len(embeds) == 1
        assert embeds[0].description == description
        assert len(embeds[0].description) == 998

    def test_create_ai_embeds_splits_on_newline(self, ai_cog, mock_ctx):
        """Test _create_ai_embeds splits on newline boundary when possible."""
        first_part = "a" * 990
        second_part = "b" * 100
        description = first_part + "\n" + second_part
        color = discord.Color.green()

        embeds = ai_cog._create_ai_embeds(mock_ctx, description, color)

        assert len(embeds) == 2
        assert embeds[0].description == first_part
        assert embeds[1].description == second_part

    @pytest.mark.asyncio
    @patch("src.bot.tools.bot_utils.EmbedPagesDal")
    @patch("src.bot.cogs.ai.get_bot_settings")
    async def test_ai_command_pagination(self, mock_get_settings, mock_dal_class, ai_cog, mock_ctx, mock_bot_settings):
        """Test AI command uses pagination for long responses."""
        mock_get_settings.return_value = mock_bot_settings
        mock_dal = MagicMock()
        mock_dal.insert_embed_pages = AsyncMock()
        mock_dal_class.return_value = mock_dal
        long_response = "a" * 3000

        with patch.object(ai_cog, "_get_openai_response", return_value=long_response):
            await ai_cog.gpt.callback(ai_cog, mock_ctx, msg_text="Long question")

            assert mock_ctx.send.call_count == 2
            call_kwargs = mock_ctx.send.call_args[1]
            assert "embed" in call_kwargs
            assert "view" in call_kwargs


class TestLazyClients:
    """API clients (and their SDKs) are created on first use, once, with the configured keys."""

    @pytest.mark.parametrize(
        ("attr", "factory", "key_setting"),
        [
            ("_openai_client", "src.bot.cogs.ai.AsyncOpenAI", "openai_api_key"),
            ("_anthropic_client", "src.bot.cogs.ai.AsyncAnthropic", "anthropic_api_key"),
            ("_gemini_client", "src.bot.cogs.ai.genai.Client", "gemini_api_key"),
        ],
    )
    def test_client_created_on_first_use_only_once(self, mock_bot, attr, factory, key_setting):
        with patch("src.bot.cogs.ai.get_bot_settings") as mock_settings, patch(factory) as mock_factory:
            mock_settings.return_value = MagicMock(**{key_setting: "the-key"})
            cog = AI(mock_bot)
            mock_factory.assert_not_called()

            first = getattr(cog, attr)
            second = getattr(cog, attr)

        mock_factory.assert_called_once_with(api_key="the-key")
        assert first is second is mock_factory.return_value
