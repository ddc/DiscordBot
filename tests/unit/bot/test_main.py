"""Tests for __main__.py entry point."""

import sys
from unittest.mock import Mock

sys.modules['ddcDatabases'] = Mock()

import discord
import pytest
from src.__main__ import _create_bot_activity, _get_command_prefix, run_bot
from src.bot.constants import messages, variables
from unittest.mock import AsyncMock, MagicMock, patch


class TestGetCommandPrefix:
    """Test cases for _get_command_prefix."""

    @pytest.mark.asyncio
    async def test_get_command_prefix_success(self):
        """Verify prefix from database is returned when available."""
        mock_db_session = MagicMock()
        mock_log = MagicMock()

        with patch('src.__main__.BotConfigsDal') as mock_dal_class:
            mock_dal = AsyncMock()
            mock_dal.get_bot_prefix.return_value = "!!"
            mock_dal_class.return_value = mock_dal

            result = await _get_command_prefix(mock_db_session, mock_log)

            assert result == "!!"
            mock_dal_class.assert_called_once_with(mock_db_session, mock_log)
            mock_dal.get_bot_prefix.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_command_prefix_none_returns_default(self):
        """Verify default PREFIX is returned when database returns None."""
        mock_db_session = MagicMock()
        mock_log = MagicMock()

        with patch('src.__main__.BotConfigsDal') as mock_dal_class:
            mock_dal = AsyncMock()
            mock_dal.get_bot_prefix.return_value = None
            mock_dal_class.return_value = mock_dal

            result = await _get_command_prefix(mock_db_session, mock_log)

            assert result == variables.PREFIX

    @pytest.mark.asyncio
    async def test_get_command_prefix_exception_returns_default(self):
        """Verify default PREFIX is returned on exception and warning is logged."""
        mock_db_session = MagicMock()
        mock_log = MagicMock()

        with patch('src.__main__.BotConfigsDal') as mock_dal_class:
            mock_dal_class.side_effect = RuntimeError("db connection failed")

            result = await _get_command_prefix(mock_db_session, mock_log)

            assert result == variables.PREFIX
            mock_log.warning.assert_called_once()
            warning_msg = mock_log.warning.call_args[0][0]
            assert messages.BOT_INIT_PREFIX_FAILED in warning_msg


class TestCreateBotActivity:
    """Test cases for _create_bot_activity."""

    @patch('src.__main__.get_bot_settings')
    def test_create_bot_activity_no_exclusive_users(self, mock_get_bot_settings):
        """Verify a Game activity is returned with a game from GAMES_INCLUDED when no exclusive users."""
        mock_settings = MagicMock()
        mock_settings.exclusive_users = ""
        mock_get_bot_settings.return_value = mock_settings

        with patch('src.__main__.random.SystemRandom') as mock_sys_random_class:
            mock_rng = MagicMock()
            mock_rng.choice.return_value = "Guild Wars 2"
            mock_sys_random_class.return_value = mock_rng

            result = _create_bot_activity("!")

            assert isinstance(result, discord.Game)
            assert "Guild Wars 2" in result.name
            assert "!help" in result.name
            mock_rng.choice.assert_called_once_with(variables.GAMES_INCLUDED)

    @patch('src.__main__.get_bot_settings')
    def test_create_bot_activity_exclusive_users(self, mock_get_bot_settings):
        """Verify 'PRIVATE BOT' activity is returned when exclusive_users is non-empty."""
        mock_settings = MagicMock()
        mock_settings.exclusive_users = "user1,user2"
        mock_get_bot_settings.return_value = mock_settings

        result = _create_bot_activity("!")

        assert isinstance(result, discord.Game)
        assert "PRIVATE BOT" in result.name
        assert "!help" in result.name

    @patch('src.__main__.get_bot_settings')
    def test_create_bot_activity_custom_prefix(self, mock_get_bot_settings):
        """Verify the activity includes the custom prefix in the help command."""
        mock_settings = MagicMock()
        mock_settings.exclusive_users = "user1"
        mock_get_bot_settings.return_value = mock_settings

        result = _create_bot_activity("$")

        assert isinstance(result, discord.Game)
        assert "$help" in result.name


class TestRunBot:
    """Test cases for run_bot."""

    @patch('src.__main__.main', new_callable=MagicMock)
    @patch('src.__main__.sys.exit')
    @patch('src.__main__.print')
    @patch('src.__main__.time.sleep')
    @patch('src.__main__.asyncio.run')
    def test_run_bot_keyboard_interrupt(self, mock_asyncio_run, mock_sleep, mock_print, mock_exit, mock_main):
        """Verify KeyboardInterrupt is caught and CTRLC message is printed."""
        mock_asyncio_run.side_effect = KeyboardInterrupt

        run_bot()

        mock_sleep.assert_called_once_with(variables.TIME_BEFORE_START)
        mock_asyncio_run.assert_called_once()
        # First print call is the starting message, second is the CTRLC message
        calls = [call[0][0] for call in mock_print.call_args_list]
        assert any(messages.BOT_STOPPED_CTRTC == c for c in calls)
        mock_exit.assert_not_called()

    @patch('src.__main__.main', new_callable=MagicMock)
    @patch('src.__main__.sys.exit')
    @patch('src.__main__.print')
    @patch('src.__main__.time.sleep')
    @patch('src.__main__.asyncio.run')
    def test_run_bot_exception(self, mock_asyncio_run, mock_sleep, mock_print, mock_exit, mock_main):
        """Verify generic exceptions cause sys.exit(1)."""
        mock_asyncio_run.side_effect = RuntimeError("unexpected crash")

        run_bot()

        mock_sleep.assert_called_once_with(variables.TIME_BEFORE_START)
        mock_exit.assert_called_once_with(1)
        # Verify the crash message was printed
        calls = [call[0][0] for call in mock_print.call_args_list]
        assert any(messages.BOT_CRASHED in c for c in calls)

    @patch('src.__main__.main', new_callable=MagicMock)
    @patch('src.__main__.sys.exit')
    @patch('src.__main__.print')
    @patch('src.__main__.time.sleep')
    @patch('src.__main__.asyncio.run')
    def test_run_bot_prints_starting_message(self, mock_asyncio_run, mock_sleep, mock_print, mock_exit, mock_main):
        """Verify run_bot prints the starting message and sleeps before running."""
        mock_asyncio_run.return_value = None

        run_bot()

        # First print should be the starting message
        first_print = mock_print.call_args_list[0][0][0]
        expected_start_msg = messages.bot_starting(variables.TIME_BEFORE_START)
        assert first_print == expected_start_msg
        mock_sleep.assert_called_once_with(variables.TIME_BEFORE_START)
