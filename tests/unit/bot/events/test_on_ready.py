"""Comprehensive tests for the OnReady event cog."""

# Mock problematic imports before importing the module
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.events.on_ready import OnReady, StartupInfoDisplay
from src.bot.constants import messages, variables


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.log = MagicMock()
    # Ensure log methods are not coroutines
    bot.log.error = MagicMock()
    bot.user = MagicMock()
    bot.user.id = 123456789
    bot.user.__str__ = MagicMock(return_value="TestBot#1234")
    bot.command_prefix = "!"
    # Ensure add_cog doesn't return a coroutine
    bot.add_cog = AsyncMock(return_value=None)
    return bot


@pytest.fixture
def on_ready_cog(mock_bot):
    """Create an OnReady cog instance."""
    return OnReady(mock_bot)


@pytest.fixture
def startup_info_display():
    """Create a StartupInfoDisplay instance."""
    return StartupInfoDisplay()


@pytest.fixture
def mock_bot_stats():
    """Create mock bot statistics."""
    return {'servers': 5, 'users': 150, 'channels': 45}


class TestStartupInfoDisplay:
    """Test cases for StartupInfoDisplay class."""

    @patch('builtins.print')
    def test_print_startup_banner(self, mock_print, startup_info_display):
        """Test printing startup banner."""
        test_version = "2.0.21"

        startup_info_display.print_startup_banner(test_version)

        # Should print 1 line with newlines: separator, version, separator
        assert mock_print.call_count == 1
        printed_text = mock_print.call_args[0][0]

        assert "=" * 20 in printed_text
        assert f"Discord Bot v{test_version}" in printed_text

    @patch('builtins.print')
    @patch('discord.__version__', '2.3.2')
    def test_print_version_info(self, mock_print, startup_info_display):
        """Test printing version information."""
        startup_info_display.print_version_info()

        # Should print 2 lines: Python version and Discord version
        assert mock_print.call_count == 2
        calls = [call[0][0] for call in mock_print.call_args_list]

        # Check Python version format
        python_version_str = f"Python v{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        assert calls[0] == python_version_str

        # Check Discord version
        assert calls[1] == "Discord API v2.3.2"

    @patch('builtins.print')
    def test_print_bot_info(self, mock_print, startup_info_display, mock_bot):
        """Test printing bot information."""
        startup_info_display.print_bot_info(mock_bot)

        # Should print 3 lines: separator, bot info, prefix
        assert mock_print.call_count == 3
        calls = [call[0][0] for call in mock_print.call_args_list]

        assert calls[0] == "--------------------"
        assert "TestBot#1234" in calls[1]
        assert "(id:123456789)" in calls[1]
        assert calls[2] == "Prefix: !"

    @patch('builtins.print')
    def test_print_bot_stats(self, mock_print, startup_info_display, mock_bot_stats):
        """Test printing bot statistics."""
        startup_info_display.print_bot_stats(mock_bot_stats)

        # Should print 3 lines: servers, users, channels
        assert mock_print.call_count == 3
        calls = [call[0][0] for call in mock_print.call_args_list]

        assert calls[0] == "Servers: 5"
        assert calls[1] == "Users: 150"
        assert calls[2] == "Channels: 45"

    @patch('builtins.print')
    @patch('src.bot.cogs.events.on_ready.bot_utils.get_current_date_time_str_long')
    def test_print_timestamp(self, mock_datetime, mock_print, startup_info_display):
        """Test printing timestamp."""
        mock_datetime.return_value = "2023-01-01 12:00:00"

        startup_info_display.print_timestamp()

        # Should print 2 lines: separator and timestamp
        assert mock_print.call_count == 2
        calls = [call[0][0] for call in mock_print.call_args_list]

        assert calls[0] == "--------------------"
        assert calls[1] == "2023-01-01 12:00:00"


class TestOnReady:
    """Test cases for OnReady cog."""

    def test_init(self, mock_bot):
        """Test OnReady cog initialization."""
        cog = OnReady(mock_bot)
        assert cog.bot == mock_bot
        assert isinstance(cog.info_display, StartupInfoDisplay)

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.events.on_ready import setup

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, OnReady)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_ready.bot_utils.get_bot_stats')
    async def test_on_ready_event_success(self, mock_get_bot_stats, mock_bot, mock_bot_stats):
        """Test on_ready event handler success."""
        mock_get_bot_stats.return_value = mock_bot_stats

        cog = OnReady(mock_bot)

        # Mock all the info display methods
        cog.info_display.print_startup_banner = MagicMock()
        cog.info_display.print_version_info = MagicMock()
        cog.info_display.print_bot_info = MagicMock()
        cog.info_display.print_bot_stats = MagicMock()
        cog.info_display.print_timestamp = MagicMock()

        # Call the listener method directly
        await cog.on_ready()

        # Verify all display methods were called
        cog.info_display.print_startup_banner.assert_called_once_with(variables.VERSION)
        cog.info_display.print_version_info.assert_called_once()
        cog.info_display.print_bot_info.assert_called_once_with(mock_bot)
        cog.info_display.print_bot_stats.assert_called_once_with(mock_bot_stats)
        cog.info_display.print_timestamp.assert_called_once()

        # Verify bot stats were retrieved
        mock_get_bot_stats.assert_called_once_with(mock_bot)

        # Verify log message
        mock_bot.log.info.assert_called_once_with(messages.bot_online(mock_bot.user))

    def test_on_ready_cog_inheritance(self, on_ready_cog):
        """Test that OnReady cog properly inherits from commands.Cog."""
        from discord.ext import commands

        assert isinstance(on_ready_cog, commands.Cog)
        assert hasattr(on_ready_cog, 'bot')

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_ready.bot_utils.get_bot_stats')
    async def test_on_ready_event_with_different_stats(self, mock_get_bot_stats, mock_bot):
        """Test on_ready event with different bot statistics."""
        different_stats = {'servers': 10, 'users': 500, 'channels': 120}
        mock_get_bot_stats.return_value = different_stats

        cog = OnReady(mock_bot)
        cog.info_display.print_bot_stats = MagicMock()

        # Call the listener method directly
        await cog.on_ready()

        # Verify stats were passed correctly
        cog.info_display.print_bot_stats.assert_called_once_with(different_stats)

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_ready.variables.VERSION', '3.0.0')
    @patch('src.bot.cogs.events.on_ready.bot_utils.get_bot_stats')
    async def test_on_ready_event_with_different_version(self, mock_get_bot_stats, mock_bot, mock_bot_stats):
        """Test on_ready event with different version."""
        mock_get_bot_stats.return_value = mock_bot_stats

        cog = OnReady(mock_bot)
        cog.info_display.print_startup_banner = MagicMock()

        # Call the listener method directly
        await cog.on_ready()

        # Verify version was passed correctly
        cog.info_display.print_startup_banner.assert_called_once_with('3.0.0')

    def test_startup_info_display_static_methods(self):
        """Test that all StartupInfoDisplay methods are static."""
        import inspect

        assert inspect.isfunction(StartupInfoDisplay.print_startup_banner)
        assert inspect.isfunction(StartupInfoDisplay.print_version_info)
        assert inspect.isfunction(StartupInfoDisplay.print_bot_info)
        assert inspect.isfunction(StartupInfoDisplay.print_bot_stats)
        assert inspect.isfunction(StartupInfoDisplay.print_timestamp)

    @patch('builtins.print')
    def test_startup_info_display_integration(self, mock_print, mock_bot, mock_bot_stats):
        """Test integration of all StartupInfoDisplay methods."""
        display = StartupInfoDisplay()

        # Call all methods in sequence
        display.print_startup_banner("2.0.21")
        display.print_version_info()
        display.print_bot_info(mock_bot)
        display.print_bot_stats(mock_bot_stats)
        display.print_timestamp()

        # Should have printed multiple lines
        assert mock_print.call_count >= 10  # At least 10 print calls

    @patch('builtins.print')
    def test_print_bot_stats_empty_stats(self, mock_print, startup_info_display):
        """Test printing bot statistics with empty stats."""
        empty_stats = {'servers': 0, 'users': 0, 'channels': 0}

        startup_info_display.print_bot_stats(empty_stats)

        calls = [call[0][0] for call in mock_print.call_args_list]
        assert calls[0] == "Servers: 0"
        assert calls[1] == "Users: 0"
        assert calls[2] == "Channels: 0"

    @patch('builtins.print')
    def test_print_bot_info_complex_bot_name(self, mock_print, startup_info_display):
        """Test printing bot info with complex bot name."""
        complex_bot = MagicMock()
        complex_bot.user = MagicMock()
        complex_bot.user.id = 987654321
        complex_bot.user.__str__ = MagicMock(return_value="Super Long Bot Name With Spaces#9999")
        complex_bot.command_prefix = "$$"

        startup_info_display.print_bot_info(complex_bot)

        calls = [call[0][0] for call in mock_print.call_args_list]
        assert "Super Long Bot Name With Spaces#9999" in calls[1]
        assert "(id:987654321)" in calls[1]
        assert calls[2] == "Prefix: $$"

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_ready.bot_utils.get_bot_stats')
    async def test_on_ready_event_bot_stats_error(self, mock_get_bot_stats, mock_bot):
        """Test on_ready event when bot stats retrieval fails."""
        # This test verifies the event still completes even if bot_stats fails
        mock_get_bot_stats.side_effect = Exception("Stats error")

        cog = OnReady(mock_bot)

        # Mock display methods
        cog.info_display.print_startup_banner = MagicMock()
        cog.info_display.print_version_info = MagicMock()
        cog.info_display.print_bot_info = MagicMock()
        cog.info_display.print_bot_stats = MagicMock()
        cog.info_display.print_timestamp = MagicMock()

        # Call the listener method directly
        # Should handle exception gracefully and not raise
        await cog.on_ready()

        # Startup banner should still have been called
        cog.info_display.print_startup_banner.assert_called_once()
        # Other display methods should also be called (except print_bot_stats)
        cog.info_display.print_version_info.assert_called_once()
        cog.info_display.print_bot_info.assert_called_once()
        cog.info_display.print_timestamp.assert_called_once()
        # print_bot_stats should not be called when stats fail
        cog.info_display.print_bot_stats.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.cogs.events.on_ready.messages.bot_online', return_value='Bot TestBot is now online!')
    @patch('src.bot.cogs.events.on_ready.bot_utils.get_bot_stats')
    async def test_on_ready_event_custom_message(self, mock_get_bot_stats, mock_bot_online, mock_bot, mock_bot_stats):
        """Test on_ready event with custom bot online message."""
        mock_get_bot_stats.return_value = mock_bot_stats

        cog = OnReady(mock_bot)

        # Call the listener method directly
        await cog.on_ready()

        # Verify custom log message format
        mock_bot_online.assert_called_once_with(mock_bot.user)
        mock_bot.log.info.assert_called_once_with('Bot TestBot is now online!')
