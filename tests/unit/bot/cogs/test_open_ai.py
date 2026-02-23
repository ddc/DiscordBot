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
    """Create a mock OpenAI response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = "This is a mock AI response from OpenAI."
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
        cog = OpenAi(mock_bot)
        assert cog.bot == mock_bot
        assert cog._openai_client is None

    def test_openai_client_property_creates_client(self, openai_cog):
        """Test that openai_client property creates client on first access."""
        with patch("src.bot.cogs.open_ai.OpenAI") as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            client = openai_cog.openai_client

            assert client == mock_client
            assert openai_cog._openai_client == mock_client
            mock_openai_class.assert_called_once()

    def test_openai_client_property_returns_existing_client(self, openai_cog):
        """Test that openai_client property returns existing client."""
        mock_client = MagicMock()
        openai_cog._openai_client = mock_client

        client = openai_cog.openai_client

        assert client == mock_client

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

            mock_ctx.message.channel.typing.assert_called_once()
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

            mock_ctx.message.channel.typing.assert_called_once()
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
        mock_client.chat.completions.create.return_value = mock_openai_response
        openai_cog._openai_client = mock_client

        result = await openai_cog._get_ai_response("What is Python?")

        assert result == "This is a mock AI response from OpenAI."

        # Verify OpenAI API call
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args

        assert call_args[1]["model"] == "gpt-3.5-turbo"
        assert call_args[1]["max_completion_tokens"] == 1000
        assert call_args[1]["temperature"] == pytest.approx(0.7)

        # Verify message types and content
        messages = call_args[1]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "What is Python?"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    async def test_get_ai_response_with_leading_trailing_spaces(
        self, mock_get_settings, openai_cog, mock_bot_settings, mock_openai_response
    ):
        """Test _get_ai_response strips leading/trailing spaces."""
        mock_get_settings.return_value = mock_bot_settings
        mock_openai_response.choices[0].message.content = "  Response with spaces  "

        # Mock the client instance directly
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        openai_cog._openai_client = mock_client

        result = await openai_cog._get_ai_response("Test message")

        assert result == "Response with spaces"

    def test_create_ai_embed_normal_length(self, openai_cog, mock_ctx):
        """Test _create_ai_embed with normal length description."""
        description = "This is a normal length response."
        color = discord.Color.blue()

        embed = openai_cog._create_ai_embed(mock_ctx, description, color)

        assert isinstance(embed, discord.Embed)
        assert embed.color == color
        assert embed.description == description
        assert embed.author.name == "TestUser"
        assert embed.author.icon_url == "https://example.com/avatar.png"

    def test_create_ai_embed_long_description(self, openai_cog, mock_ctx):
        """Test _create_ai_embed with description exceeding 2000 characters."""
        long_description = "a" * 2010  # Exceeds 2000-character limit
        color = discord.Color.green()

        embed = openai_cog._create_ai_embed(mock_ctx, long_description, color)

        assert len(embed.description) <= 2000
        assert embed.description.endswith("...")
        assert embed.description.startswith("a" * 1997)

    def test_create_ai_embed_exactly_2000_chars(self, openai_cog, mock_ctx):
        """Test _create_ai_embed with exactly 2000 characters."""
        description = "a" * 2000
        color = discord.Color.red()

        embed = openai_cog._create_ai_embed(mock_ctx, description, color)

        assert embed.description == description
        assert len(embed.description) == 2000

    def test_create_ai_embed_no_author_avatar(self, openai_cog, mock_ctx):
        """Test _create_ai_embed when author has no avatar."""
        mock_ctx.author.avatar = None
        description = "Test response"
        color = discord.Color.orange()

        embed = openai_cog._create_ai_embed(mock_ctx, description, color)

        assert embed.author.name == "TestUser"
        assert embed.author.icon_url is None

    def test_create_ai_embed_no_bot_avatar(self, openai_cog, mock_ctx):
        """Test _create_ai_embed when bot has no avatar."""
        mock_ctx.bot.user.avatar = None
        description = "Test response"
        color = discord.Color.purple()

        embed = openai_cog._create_ai_embed(mock_ctx, description, color)

        assert embed.footer.icon_url is None
        assert "UTC" in embed.footer.text

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    @patch("src.bot.cogs.open_ai.bot_utils.send_embed")
    async def test_ai_command_with_different_models(
        self, mock_send_embed, mock_get_settings, openai_cog, mock_ctx, mock_openai_response
    ):
        """Test AI command with different OpenAI models."""
        # Test with GPT-4
        mock_settings = MagicMock()
        mock_settings.openai_model = "gpt-4"
        mock_get_settings.return_value = mock_settings

        # Mock the client instance directly
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        openai_cog._openai_client = mock_client

        await openai_cog.ai.callback(openai_cog, mock_ctx, msg_text="Test question")

        # Verify correct model was used
        call_args = mock_client.chat.completions.create.call_args
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
        mock_client.chat.completions.create.return_value = mock_openai_response
        openai_cog._openai_client = mock_client

        await openai_cog._get_ai_response("Test message")

        messages = mock_client.chat.completions.create.call_args[1]["messages"]
        system_message = messages[0]
        expected_content = "You are a helpful AI assistant. Provide clear, concise, and accurate responses."
        assert system_message["content"] == expected_content

    @pytest.mark.asyncio
    @patch("src.bot.cogs.open_ai.get_bot_settings")
    async def test_get_ai_response_api_parameters(
        self, mock_get_settings, openai_cog, mock_bot_settings, mock_openai_response
    ):
        """Test that OpenAI API is called with correct parameters."""
        mock_get_settings.return_value = mock_bot_settings

        # Mock the client instance directly
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        openai_cog._openai_client = mock_client

        await openai_cog._get_ai_response("Test message")

        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["max_completion_tokens"] == 1000
        assert call_args["temperature"] == pytest.approx(0.7)
        assert call_args["model"] == "gpt-3.5-turbo"

    @patch("src.bot.cogs.open_ai.bot_utils.get_current_date_time_str_long")
    def test_create_ai_embed_footer(self, mock_get_datetime, openai_cog, mock_ctx):
        """Test that embed footer contains correct timestamp."""
        mock_get_datetime.return_value = "2023-01-01 12:00:00"

        embed = openai_cog._create_ai_embed(mock_ctx, "Test", discord.Color.blue())

        assert embed.footer.text == "2023-01-01 12:00:00 UTC"
        mock_get_datetime.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.open_ai import setup

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

        # Mock empty response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "   "  # Only whitespace

        # Mock the client instance directly
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        openai_cog._openai_client = mock_client

        result = await openai_cog._get_ai_response("Test message")

        assert result == ""  # Should strip to empty string

    def test_create_ai_embed_edge_case_1997_chars(self, openai_cog, mock_ctx):
        """Test _create_ai_embed with exactly 1997 characters (edge case)."""
        description = "a" * 1997
        color = discord.Color.teal()

        embed = openai_cog._create_ai_embed(mock_ctx, description, color)

        # Should not be truncated
        assert embed.description == description
        assert len(embed.description) == 1997

    def test_create_ai_embed_edge_case_1998_chars(self, openai_cog, mock_ctx):
        """Test _create_ai_embed with 1998 characters (should NOT be truncated)."""
        description = "a" * 1998
        color = discord.Color.magenta()

        embed = openai_cog._create_ai_embed(mock_ctx, description, color)

        # Should NOT be truncated since 1998 <= 2000
        assert embed.description == description
        assert len(embed.description) == 1998
