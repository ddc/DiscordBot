"""Tests for __main__.py entry point."""

import sys
from unittest.mock import Mock

sys.modules["ddcDatabases"] = Mock()

import discord
import pytest
from src.__main__ import _create_bot_activity, _get_command_prefix, run_bot
from src.bot.constants import messages, variables
from unittest.mock import AsyncMock, MagicMock, patch
lazy from src import __main__ as main_module


class TestGetCommandPrefix:
    """Test cases for _get_command_prefix."""

    @pytest.mark.asyncio
    async def test_get_command_prefix_success(self):
        """Verify prefix from database is returned when available."""
        mock_db_session = MagicMock()
        mock_log = MagicMock()

        with patch("src.__main__.BotConfigsDal") as mock_dal_class:
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

        with patch("src.__main__.BotConfigsDal") as mock_dal_class:
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

        with patch("src.__main__.BotConfigsDal") as mock_dal_class:
            mock_dal_class.side_effect = RuntimeError("db connection failed")

            result = await _get_command_prefix(mock_db_session, mock_log)

            assert result == variables.PREFIX
            mock_log.warning.assert_called_once()
            warning_msg = mock_log.warning.call_args[0][0]
            assert messages.Bot.INIT_PREFIX_FAILED in warning_msg


class TestCreateBotActivity:
    """Test cases for _create_bot_activity."""

    @patch("src.__main__.get_bot_settings")
    def test_create_bot_activity_no_exclusive_users(self, mock_get_bot_settings):
        """Verify a Game activity is returned with a game from GAMES_INCLUDED when no exclusive users."""
        mock_settings = MagicMock()
        mock_settings.exclusive_users = ""
        mock_get_bot_settings.return_value = mock_settings

        with patch("src.__main__.random.SystemRandom") as mock_sys_random_class:
            mock_rng = MagicMock()
            mock_rng.choice.return_value = "Guild Wars 2"
            mock_sys_random_class.return_value = mock_rng

            result = _create_bot_activity("!")

            assert isinstance(result, discord.Game)
            assert "Guild Wars 2" in result.name
            assert "!help" in result.name
            mock_rng.choice.assert_called_once_with(variables.GAMES_INCLUDED)

    @patch("src.__main__.get_bot_settings")
    def test_create_bot_activity_exclusive_users(self, mock_get_bot_settings):
        """Verify 'PRIVATE BOT' activity is returned when exclusive_users is non-empty."""
        mock_settings = MagicMock()
        mock_settings.exclusive_users = "user1,user2"
        mock_get_bot_settings.return_value = mock_settings

        result = _create_bot_activity("!")

        assert isinstance(result, discord.Game)
        assert "PRIVATE BOT" in result.name
        assert "!help" in result.name

    @patch("src.__main__.get_bot_settings")
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

    @patch("src.__main__.main", new_callable=MagicMock)
    @patch("src.__main__.sys.exit")
    @patch("src.__main__.print")
    @patch("src.__main__.time.sleep")
    @patch("src.__main__.asyncio.run")
    def test_run_bot_keyboard_interrupt(self, mock_asyncio_run, mock_sleep, mock_print, mock_exit, mock_main):
        """Verify KeyboardInterrupt is caught and CTRLC message is printed."""
        mock_asyncio_run.side_effect = KeyboardInterrupt

        run_bot()

        mock_sleep.assert_called_once_with(variables.TIME_BEFORE_START)
        mock_asyncio_run.assert_called_once()
        calls = [call[0][0] for call in mock_print.call_args_list]
        assert any(messages.Bot.STOPPED_CTRTC == c for c in calls)
        mock_exit.assert_not_called()

    @patch("src.__main__.main", new_callable=MagicMock)
    @patch("src.__main__.sys.exit")
    @patch("src.__main__.print")
    @patch("src.__main__.time.sleep")
    @patch("src.__main__.asyncio.run")
    def test_run_bot_exception(self, mock_asyncio_run, mock_sleep, mock_print, mock_exit, mock_main):
        """Verify generic exceptions cause sys.exit(1)."""
        mock_asyncio_run.side_effect = RuntimeError("unexpected crash")

        run_bot()

        mock_sleep.assert_called_once_with(variables.TIME_BEFORE_START)
        mock_exit.assert_called_once_with(1)
        calls = [call[0][0] for call in mock_print.call_args_list]
        assert any(messages.Bot.CRASHED in c for c in calls)

    @patch("src.__main__.main", new_callable=MagicMock)
    @patch("src.__main__.sys.exit")
    @patch("src.__main__.print")
    @patch("src.__main__.time.sleep")
    @patch("src.__main__.asyncio.run")
    def test_run_bot_prints_starting_message(self, mock_asyncio_run, mock_sleep, mock_print, mock_exit, mock_main):
        """Verify run_bot prints the starting message and sleeps before running."""
        mock_asyncio_run.return_value = None

        run_bot()

        first_print = mock_print.call_args_list[0][0][0]
        expected_start_msg = messages.Bot.starting(variables.TIME_BEFORE_START)
        assert first_print == expected_start_msg
        mock_sleep.assert_called_once_with(variables.TIME_BEFORE_START)


def _async_cm(value):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=value)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


class TestMain:
    @pytest.fixture
    def env(self):
        """Patch every external dependency main() touches and expose the mocks."""

        bot = MagicMock()
        bot.start = AsyncMock()
        bot.close = AsyncMock()
        log = MagicMock()
        settings = MagicMock(token="TOKEN-123")
        patches = {
            "TimedRotatingLog": patch.object(main_module, "TimedRotatingLog", return_value=log),
            "get_bot_settings": patch.object(main_module, "get_bot_settings", return_value=settings),
            "ClientSession": patch.object(main_module, "ClientSession", return_value=_async_cm("http-session")),
            "PostgreSQL": patch.object(main_module, "PostgreSQL", return_value=_async_cm("db-session")),
            "Bot": patch.object(main_module, "Bot", return_value=_async_cm(bot)),
            "prefix": patch.object(main_module, "_get_command_prefix", new_callable=AsyncMock, return_value="!"),
            "activity": patch.object(main_module, "_create_bot_activity", return_value=discord.Game(name="x")),
            "bg_tasks": patch.object(main_module.bot_utils, "init_background_tasks"),
            "exit": patch.object(main_module.sys, "exit", side_effect=SystemExit(1)),
        }
        started = {name: p.start() for name, p in patches.items()}
        yield {"module": main_module, "bot": bot, "log": log, "settings": settings, **started}
        for p in patches.values():
            p.stop()

    @pytest.mark.asyncio
    async def test_missing_token_exits(self, env):
        env["settings"].token = None
        with pytest.raises(SystemExit):
            await env["module"].main()
        env["log"].error.assert_any_call(messages.Bot.MISSING_ENV_VAR)
        env["Bot"].assert_not_called()

    @pytest.mark.asyncio
    async def test_starts_and_closes_bot(self, env):
        await env["module"].main()

        kwargs = env["Bot"].call_args.kwargs
        assert kwargs["command_prefix"] == "!"
        assert kwargs["aiosession"] == "http-session"
        assert kwargs["db_session"] == "db-session"
        assert kwargs["owner_id"] == int(variables.AUTHOR_ID)
        env["bg_tasks"].assert_called_once_with(env["bot"])
        env["bot"].start.assert_awaited_once_with("TOKEN-123")
        env["bot"].close.assert_awaited_once()
        env["log"].info.assert_any_call(messages.Bot.CLOSING)

    @pytest.mark.asyncio
    async def test_login_failure_is_logged_not_raised(self, env):
        env["bot"].start.side_effect = discord.LoginFailure("bad token")
        await env["module"].main()

        logged = [c.args[0] for c in env["log"].error.call_args_list]
        assert any(m.startswith(messages.Bot.LOGIN_FAILED) and "bad token" in m for m in logged)
        env["bot"].close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_crash_is_logged_and_reraised(self, env):
        env["bot"].start.side_effect = RuntimeError("gateway exploded")
        with pytest.raises(RuntimeError, match="gateway exploded"):
            await env["module"].main()

        logged = [c.args[0] for c in env["log"].error.call_args_list]
        assert f"{messages.Bot.TERMINATED} | gateway exploded" in logged
        assert f"{messages.Bot.FATAL_ERROR_MAIN}: gateway exploded" in logged
        env["bot"].close.assert_awaited_once()
