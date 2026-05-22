"""Comprehensive tests for the OpenAi cog."""

import discord
import pytest

# Mock problematic imports before importing the module
import sys
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules["ddcDatabases"] = Mock()

from src.bot.cogs.open_ai import OpenAi


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
def openai_cog(mock_bot):
    """Create an OpenAi cog instance."""
    with patch("src.bot.cogs.open_ai.get_bot_settings") as mock_settings, patch("src.bot.cogs.open_ai.AsyncOpenAI"):
        mock_settings.return_value = MagicMock(openai_api_key="test-key", openai_model="gpt-3.5-turbo")
        return OpenAi(mock_bot)


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


class TestOpenAi:
    """Test cases for OpenAi cog."""

    def test_init(self, mock_bot):
        """Test OpenAi cog initialization."""
        with patch("src.bot.cogs.open_ai.get_bot_settings") as mock_settings, patch("src.bot.cogs.open_ai.AsyncOpenAI"):
            mock_settings.return_value = MagicMock(openai_api_key="test-key", openai_model="gpt-3.5-turbo")
            cog = OpenAi(mock_bot)
            assert cog.bot == mock_bot
            assert cog._openai_client is not None
            assert hasattr(cog, "_bot_settings")

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    @patch("src.bot.cogs.open_ai.bot_utils.send_embed")
    async def test_ai_command_success(
        self, mock_send_embed, mock_get_settings, openai_cog, mock_ctx, mock_bot_settings, mock_openai_response
    ):
        """Test successful AI command execution."""
        mock_get_settings.return_value = mock_bot_settings

        with patch.object(openai_cog, "_get_ai_response", return_value="AI response here"):
            await openai_cog.ai.callback(openai_cog, mock_ctx, msg_text="What is Python?")

            mock_ctx.send.assert_called_once()  # progress message was sent
            mock_send_embed.assert_called_once()

            # Check embed properties
            embed = mock_send_embed.call_args[0][1]
            assert embed.color == discord.Color.green()
            assert embed.description == "AI response here"
            assert embed.author.name == "TestUser"
            assert embed.author.icon_url == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    @patch("src.bot.cogs.open_ai.bot_utils.send_embed")
    async def test_ai_command_error(self, mock_send_embed, mock_get_settings, openai_cog, mock_ctx, mock_bot_settings):
        """Test AI command with OpenAI API error."""
        mock_get_settings.return_value = mock_bot_settings

        with patch.object(openai_cog, "_get_ai_response", side_effect=Exception("API Error")):
            await openai_cog.ai.callback(openai_cog, mock_ctx, msg_text="What is Python?")

            mock_ctx.send.assert_called_once()  # progress message was sent
            mock_send_embed.assert_called_once()

            # Check error embed properties
            embed = mock_send_embed.call_args[0][1]
            assert embed.color == discord.Color.red()
            assert "Sorry, I encountered an error" in embed.description
            assert "API Error" in embed.description

            # Verify error was logged
            openai_cog.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    async def test_get_ai_response_success(
        self, mock_get_settings, openai_cog, mock_bot_settings, mock_openai_response
    ):
        """Test successful _get_ai_response method."""
        mock_get_settings.return_value = mock_bot_settings

        # Mock the client instance directly
        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        openai_cog._openai_client = mock_client

        result = await openai_cog._get_ai_response("What is Python?")

        assert result == "This is a mock AI response from OpenAI."

        # Verify OpenAI API call
        mock_client.responses.create.assert_called_once()
        call_args = mock_client.responses.create.call_args

        assert call_args[1]["model"] == "gpt-3.5-turbo"
        assert call_args[1]["max_output_tokens"] is None
        assert call_args[1]["instructions"] == openai_cog._instructions
        assert call_args[1]["input"] == "What is Python?"
        # Reasoning effort and web search are enabled
        assert call_args[1]["reasoning"]["effort"] == "xhigh"
        assert call_args[1]["tools"][0]["type"] == "web_search"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    async def test_get_ai_response_with_leading_trailing_spaces(
        self, mock_get_settings, openai_cog, mock_bot_settings, mock_openai_response
    ):
        """Test _get_ai_response strips leading/trailing spaces."""
        mock_get_settings.return_value = mock_bot_settings
        mock_openai_response.output_text = "  Response with spaces  "

        # Mock the client instance directly
        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        openai_cog._openai_client = mock_client

        result = await openai_cog._get_ai_response("Test message")

        assert result == "Response with spaces"

    def test_create_ai_embeds_normal_length(self, openai_cog, mock_ctx):
        """Test _create_ai_embeds with normal length description."""
        description = "This is a normal length response."
        color = discord.Color.blue()

        embeds = openai_cog._create_ai_embeds(mock_ctx, description, color)

        assert len(embeds) == 1
        assert isinstance(embeds[0], discord.Embed)
        assert embeds[0].color == color
        assert embeds[0].description == description
        assert embeds[0].author.name == "TestUser"
        assert embeds[0].author.icon_url == "https://example.com/avatar.png"

    def test_create_ai_embeds_long_description(self, openai_cog, mock_ctx):
        """Test _create_ai_embeds with description exceeding 2000 characters paginates."""
        long_description = "a" * 2010  # Exceeds 2000-character limit
        color = discord.Color.green()

        embeds = openai_cog._create_ai_embeds(mock_ctx, long_description, color)

        assert len(embeds) == 2
        assert len(embeds[0].description) <= 2000
        assert len(embeds[1].description) <= 2000
        assert embeds[0].description + embeds[1].description == long_description
        assert "Page 1/2" in embeds[0].footer.text
        assert "Page 2/2" in embeds[1].footer.text

    def test_create_ai_embeds_exactly_2000_chars(self, openai_cog, mock_ctx):
        """Test _create_ai_embeds with exactly 2000 characters returns single page."""
        description = "a" * 2000
        color = discord.Color.red()

        embeds = openai_cog._create_ai_embeds(mock_ctx, description, color)

        assert len(embeds) == 1
        assert embeds[0].description == description
        assert len(embeds[0].description) == 2000

    def test_create_ai_embeds_no_author_avatar(self, openai_cog, mock_ctx):
        """Test _create_ai_embeds when author has no avatar."""
        mock_ctx.author.avatar = None
        description = "Test response"
        color = discord.Color.orange()

        embeds = openai_cog._create_ai_embeds(mock_ctx, description, color)

        assert embeds[0].author.name == "TestUser"
        assert embeds[0].author.icon_url is None

    def test_create_ai_embeds_no_bot_avatar(self, openai_cog, mock_ctx):
        """Test _create_ai_embeds when bot has no avatar."""
        mock_ctx.bot.user.avatar = None
        description = "Test response"
        color = discord.Color.purple()

        embeds = openai_cog._create_ai_embeds(mock_ctx, description, color)

        assert embeds[0].footer.icon_url is None
        assert "UTC" in embeds[0].footer.text

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.bot_utils.send_embed")
    async def test_ai_command_with_different_models(self, mock_send_embed, openai_cog, mock_ctx, mock_openai_response):
        """Test AI command with different OpenAI models."""
        # Test with GPT-4 - set model directly on the cog's stored settings
        openai_cog._bot_settings.openai_model = "gpt-4"

        # Mock the client instance directly
        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        openai_cog._openai_client = mock_client

        await openai_cog.ai.callback(openai_cog, mock_ctx, msg_text="Test question")

        # Verify correct model was used
        call_args = mock_client.responses.create.call_args
        assert call_args[1]["model"] == "gpt-4"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    @patch("src.bot.cogs.open_ai.bot_utils.send_embed")
    async def test_ai_command_with_long_question(
        self, mock_send_embed, mock_get_settings, openai_cog, mock_ctx, mock_bot_settings
    ):
        """Test AI command with very long question."""
        mock_get_settings.return_value = mock_bot_settings
        long_question = "What is " + "very " * 1000 + "long question?"

        with patch.object(openai_cog, "_get_ai_response", return_value="Short answer"):
            await openai_cog.ai.callback(openai_cog, mock_ctx, msg_text=long_question)

            mock_send_embed.assert_called_once()
            embed = mock_send_embed.call_args[0][1]
            assert embed.description == "Short answer"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    @patch("src.bot.cogs.open_ai.bot_utils.send_embed")
    async def test_ai_command_with_special_characters(
        self, mock_send_embed, mock_get_settings, openai_cog, mock_ctx, mock_bot_settings
    ):
        """Test AI command with special characters in question."""
        mock_get_settings.return_value = mock_bot_settings
        special_question = "What is 2+2? 🤔 And émojis & spéciál chars?"

        with patch.object(openai_cog, "_get_ai_response", return_value="4! 😊"):
            await openai_cog.ai.callback(openai_cog, mock_ctx, msg_text=special_question)

            mock_send_embed.assert_called_once()
            embed = mock_send_embed.call_args[0][1]
            assert embed.description == "4! 😊"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    async def test_get_ai_response_system_message_content(
        self, mock_get_settings, openai_cog, mock_bot_settings, mock_openai_response
    ):
        """Test that system message has correct content."""
        mock_get_settings.return_value = mock_bot_settings

        # Mock the client instance directly
        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        openai_cog._openai_client = mock_client

        await openai_cog._get_ai_response("Test message")

        call_args = mock_client.responses.create.call_args[1]
        assert call_args["instructions"] == openai_cog._instructions
        assert call_args["input"] == "Test message"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    async def test_get_ai_response_api_parameters(
        self, mock_get_settings, openai_cog, mock_bot_settings, mock_openai_response
    ):
        """Test that OpenAI API is called with correct parameters."""
        mock_get_settings.return_value = mock_bot_settings

        # Mock the client instance directly
        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_openai_response)
        openai_cog._openai_client = mock_client

        await openai_cog._get_ai_response("Test message")

        call_args = mock_client.responses.create.call_args[1]
        assert call_args["max_output_tokens"] is None
        assert call_args["reasoning"]["effort"] == "xhigh"
        assert call_args["tools"][0]["type"] == "web_search"
        assert "temperature" not in call_args
        assert call_args["model"] == "gpt-3.5-turbo"

    @patch("src.bot.cogs.open_ai.bot_utils.get_current_date_time_str_long")
    def test_create_ai_embeds_footer(self, mock_get_datetime, openai_cog, mock_ctx):
        """Test that embed footer contains model, duration, and timestamp."""
        mock_get_datetime.return_value = "2023-01-01 12:00:00"

        embeds = openai_cog._create_ai_embeds(mock_ctx, "Test", discord.Color.blue(), elapsed=20.0)

        assert embeds[0].footer.text == "gpt-3.5-turbo | 20s | 2023-01-01 12:00:00 UTC"
        mock_get_datetime.assert_called_once()

    def test_format_duration_milliseconds(self, openai_cog):
        """Sub-second durations are shown in milliseconds."""
        assert openai_cog._format_duration(0.005) == "5ms"
        assert openai_cog._format_duration(0.5) == "500ms"

    def test_format_duration_seconds(self, openai_cog):
        """Durations of one second or more are shown in whole seconds."""
        assert openai_cog._format_duration(1.0) == "1s"
        assert openai_cog._format_duration(20.4) == "20s"
        assert openai_cog._format_duration(119.6) == "120s"

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.open_ai import setup

        with patch("src.bot.cogs.open_ai.get_bot_settings") as mock_settings, patch("src.bot.cogs.open_ai.AsyncOpenAI"):
            mock_settings.return_value = MagicMock(openai_api_key="test-key", openai_model="gpt-3.5-turbo")
            await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OpenAi)
        assert added_cog.bot == mock_bot

    def test_openai_cog_inheritance(self, openai_cog):
        """Test that OpenAi cog properly inherits from commands.Cog."""
        assert isinstance(openai_cog, commands.Cog)
        assert hasattr(openai_cog, "bot")

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    @patch("src.bot.cogs.open_ai.bot_utils.send_embed")
    async def test_ai_command_error_logging(
        self, mock_send_embed, mock_get_settings, openai_cog, mock_ctx, mock_bot_settings
    ):
        """Test that errors are properly logged."""
        mock_get_settings.return_value = mock_bot_settings
        test_error = Exception("Test API Error")

        with patch.object(openai_cog, "_get_ai_response", side_effect=test_error):
            await openai_cog.ai.callback(openai_cog, mock_ctx, msg_text="Test question")

            # Verify error was logged with correct message
            openai_cog.bot.log.error.assert_called_once()
            log_call = openai_cog.bot.log.error.call_args[0][0]
            assert "OpenAI API error:" in log_call
            assert "Test API Error" in log_call

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    @patch("src.bot.cogs.open_ai.bot_utils.send_embed")
    async def test_ai_command_send_embed_parameters(
        self, mock_send_embed, mock_get_settings, openai_cog, mock_ctx, mock_bot_settings
    ):
        """Test that send_embed is called with correct parameters."""
        mock_get_settings.return_value = mock_bot_settings

        with patch.object(openai_cog, "_get_ai_response", return_value="Test response"):
            await openai_cog.ai.callback(openai_cog, mock_ctx, msg_text="Test question")

            # Verify send_embed was called with ctx, embed, and False
            mock_send_embed.assert_called_once()
            call_args = mock_send_embed.call_args[0]
            assert call_args[0] == mock_ctx  # ctx
            assert isinstance(call_args[1], discord.Embed)  # embed
            assert call_args[2] is False  # dm parameter

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    async def test_get_ai_response_empty_response(self, mock_get_settings, openai_cog, mock_bot_settings):
        """Test _get_ai_response with empty response from OpenAI."""
        mock_get_settings.return_value = mock_bot_settings

        # Mock empty response (whitespace only)
        mock_response = MagicMock()
        mock_response.output_text = "   "

        # Mock the client instance directly
        mock_client = MagicMock()
        mock_client.responses.create = AsyncMock(return_value=mock_response)
        openai_cog._openai_client = mock_client

        result = await openai_cog._get_ai_response("Test message")

        assert result == ""  # Should strip to empty string

    def test_create_ai_embeds_edge_case_1997_chars(self, openai_cog, mock_ctx):
        """Test _create_ai_embeds with exactly 1997 characters returns single page."""
        description = "a" * 1997
        color = discord.Color.teal()

        embeds = openai_cog._create_ai_embeds(mock_ctx, description, color)

        assert len(embeds) == 1
        assert embeds[0].description == description
        assert len(embeds[0].description) == 1997

    def test_create_ai_embeds_edge_case_1998_chars(self, openai_cog, mock_ctx):
        """Test _create_ai_embeds with 1998 characters returns single page."""
        description = "a" * 1998
        color = discord.Color.magenta()

        embeds = openai_cog._create_ai_embeds(mock_ctx, description, color)

        assert len(embeds) == 1
        assert embeds[0].description == description
        assert len(embeds[0].description) == 1998

    def test_create_ai_embeds_splits_on_newline(self, openai_cog, mock_ctx):
        """Test _create_ai_embeds splits on newline boundary when possible."""
        # Create text with a newline near the 2000 char boundary
        first_part = "a" * 1990
        second_part = "b" * 100
        description = first_part + "\n" + second_part
        color = discord.Color.green()

        embeds = openai_cog._create_ai_embeds(mock_ctx, description, color)

        assert len(embeds) == 2
        assert embeds[0].description == first_part
        assert embeds[1].description == second_part

    @pytest.mark.asyncio
    @patch("src.database.dal.bot.embed_pages_dal.EmbedPagesDal")
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    async def test_ai_command_pagination(
        self, mock_get_settings, mock_dal_class, openai_cog, mock_ctx, mock_bot_settings
    ):
        """Test AI command uses pagination for long responses."""
        mock_get_settings.return_value = mock_bot_settings
        mock_dal = MagicMock()
        mock_dal.insert_embed_pages = AsyncMock()
        mock_dal_class.return_value = mock_dal
        long_response = "a" * 3000

        with patch.object(openai_cog, "_get_ai_response", return_value=long_response):
            await openai_cog.ai.callback(openai_cog, mock_ctx, msg_text="Long question")

            # ctx.send called twice: progress message, then the paginated first page
            assert mock_ctx.send.call_count == 2
            call_kwargs = mock_ctx.send.call_args[1]  # last call == paginated send
            assert "embed" in call_kwargs
            assert "view" in call_kwargs
