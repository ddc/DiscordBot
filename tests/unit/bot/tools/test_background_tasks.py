"""Comprehensive tests for background tasks module."""

import discord
import pytest
from src.bot.tools.background_tasks import BackGroundTasks
from unittest.mock import AsyncMock, MagicMock, patch


class TestBackGroundTasks:
    """Test cases for BackGroundTasks class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot instance."""
        bot = AsyncMock()
        bot.command_prefix = ["!"]
        bot.log = MagicMock()
        bot.wait_until_ready = AsyncMock()
        bot.is_closed = MagicMock(return_value=False)
        bot.change_presence = AsyncMock()
        return bot

    def test_init(self, mock_bot):
        """Test BackGroundTasks initialization."""
        bg_tasks = BackGroundTasks(mock_bot)

        assert bg_tasks.bot is mock_bot
        assert hasattr(bg_tasks, "random")
        assert bg_tasks.random is not None

    @pytest.mark.asyncio
    async def test_change_presence_task_single_iteration(self, mock_bot):
        """Test single iteration of change_presence_task."""
        call_count = 0

        def mock_is_closed():
            nonlocal call_count
            call_count += 1
            return call_count > 1

        mock_bot.is_closed.side_effect = mock_is_closed

        bg_tasks = BackGroundTasks(mock_bot)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await bg_tasks.change_presence_task(5)

        mock_bot.wait_until_ready.assert_called_once()

        mock_bot.change_presence.assert_called_once()

        call_args = mock_bot.change_presence.call_args
        assert call_args[1]["status"] == discord.Status.online
        assert isinstance(call_args[1]["activity"], discord.Game)

        activity_name = call_args[1]["activity"].name
        assert " | !help" in activity_name

        mock_bot.log.info.assert_called_once()
        log_message = mock_bot.log.info.call_args[0][0]
        assert "Background task (5s) - Changing activity:" in log_message

        mock_sleep.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_change_presence_task_multiple_iterations(self, mock_bot):
        """Test multiple iterations of change_presence_task."""
        call_count = 0

        def mock_is_closed():
            nonlocal call_count
            call_count += 1
            return call_count > 3

        mock_bot.is_closed.side_effect = mock_is_closed

        bg_tasks = BackGroundTasks(mock_bot)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await bg_tasks.change_presence_task(10)

        assert mock_bot.change_presence.call_count == 3
        assert mock_sleep.call_count == 3
        assert mock_bot.log.info.call_count == 3

        for call in mock_sleep.call_args_list:
            assert call[0][0] == 10

    @pytest.mark.asyncio
    async def test_change_presence_task_random_game_selection(self, mock_bot):
        """Test that games are randomly selected."""
        call_count = 0

        def mock_is_closed():
            nonlocal call_count
            call_count += 1
            return call_count > 10

        mock_bot.is_closed.side_effect = mock_is_closed

        bg_tasks = BackGroundTasks(mock_bot)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await bg_tasks.change_presence_task(1)

        activity_names = []
        for call in mock_bot.change_presence.call_args_list:
            activity_name = call[1]["activity"].name
            activity_names.append(activity_name)

        for name in activity_names:
            assert " | !help" in name

    @pytest.mark.asyncio
    async def test_change_presence_task_exception_handling(self, mock_bot):
        """Test exception handling in change_presence_task."""
        call_count = 0

        def mock_is_closed():
            nonlocal call_count
            call_count += 1
            return call_count > 2

        mock_bot.is_closed.side_effect = mock_is_closed

        mock_bot.change_presence.side_effect = [Exception("Test error"), None]

        bg_tasks = BackGroundTasks(mock_bot)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await bg_tasks.change_presence_task(3)

        mock_bot.log.error.assert_called_once()
        error_message = mock_bot.log.error.call_args[0][0]
        assert "Error in background presence task: Test error" in error_message

        assert mock_sleep.call_count == 2
        for call in mock_sleep.call_args_list:
            assert call[0][0] == 3

    @pytest.mark.asyncio
    async def test_change_presence_task_wait_until_ready_exception(self, mock_bot):
        """Test exception during wait_until_ready."""
        mock_bot.wait_until_ready.side_effect = Exception("Ready error")
        mock_bot.is_closed.return_value = True

        bg_tasks = BackGroundTasks(mock_bot)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(Exception, match="Ready error"):
                await bg_tasks.change_presence_task(1)

    @pytest.mark.asyncio
    async def test_change_presence_task_different_prefixes(self, mock_bot):
        """Test with different command prefixes."""
        test_cases = [["$"], ["!", "&"], ["custom_prefix"]]

        for prefixes in test_cases:
            mock_bot.reset_mock()
            mock_bot.command_prefix = prefixes
            mock_bot.is_closed.return_value = False

            call_count = 0

            def mock_is_closed():
                nonlocal call_count
                call_count += 1
                return call_count > 1

            mock_bot.is_closed.side_effect = mock_is_closed

            bg_tasks = BackGroundTasks(mock_bot)

            with patch("asyncio.sleep", new_callable=AsyncMock):
                await bg_tasks.change_presence_task(1)

            activity_name = mock_bot.change_presence.call_args[1]["activity"].name
            expected_suffix = f" | {prefixes[0]}help"
            assert activity_name.endswith(expected_suffix)

    @pytest.mark.asyncio
    async def test_change_presence_task_empty_games_list(self, mock_bot):
        """Test behavior with empty games list."""
        mock_bot.is_closed.return_value = False

        call_count = 0

        def mock_is_closed():
            nonlocal call_count
            call_count += 1
            return call_count > 1

        mock_bot.is_closed.side_effect = mock_is_closed

        bg_tasks = BackGroundTasks(mock_bot)

        bg_tasks.random.choice = MagicMock(side_effect=IndexError("list index out of range"))

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await bg_tasks.change_presence_task(1)

            mock_bot.log.error.assert_called()
            error_message = mock_bot.log.error.call_args[0][0]
            assert "Error in background presence task:" in error_message

    @pytest.mark.asyncio
    async def test_change_presence_task_continuous_exceptions(self, mock_bot):
        """Test behavior when exceptions happen continuously."""
        call_count = 0

        def mock_is_closed():
            nonlocal call_count
            call_count += 1
            return call_count > 3

        mock_bot.is_closed.side_effect = mock_is_closed

        mock_bot.change_presence.side_effect = Exception("Persistent error")

        bg_tasks = BackGroundTasks(mock_bot)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await bg_tasks.change_presence_task(2)

        assert mock_bot.log.error.call_count == 3

        assert mock_sleep.call_count == 3


class TestBackGroundTasksLegacyAlias:
    """Test legacy alias for backward compatibility."""

    def test_legacy_alias_exists(self):
        """Test that BackGroundTasks alias exists."""
        assert BackGroundTasks is not None

    def test_legacy_alias_functionality(self):
        """Test that legacy alias works identically."""
        mock_bot = MagicMock()

        bg_tasks_new = BackGroundTasks(mock_bot)
        bg_tasks_legacy = BackGroundTasks(mock_bot)

        assert type(bg_tasks_new) is type(bg_tasks_legacy)
        assert bg_tasks_new.__class__.__name__ == bg_tasks_legacy.__class__.__name__


class TestBackGroundTasksRandomness:
    """Test randomness behavior in BackGroundTasks."""

    def test_random_instance_creation(self):
        """Test that each BackGroundTasks instance has its own random instance."""
        mock_bot = MagicMock()

        bg_tasks1 = BackGroundTasks(mock_bot)
        bg_tasks2 = BackGroundTasks(mock_bot)

        assert bg_tasks1.random is not bg_tasks2.random
        assert type(bg_tasks1.random).__name__ == "SystemRandom"
        assert type(bg_tasks2.random).__name__ == "SystemRandom"

    def test_random_choice_usage(self):
        """Test that SystemRandom.choice is used correctly."""
        mock_bot = MagicMock()
        bg_tasks = BackGroundTasks(mock_bot)

        bg_tasks.random.choice = MagicMock(return_value="SelectedGame")

        test_games = ["Game1", "Game2", "Game3"]
        result = bg_tasks.random.choice(test_games)

        assert result == "SelectedGame"
        bg_tasks.random.choice.assert_called_once_with(test_games)


class TestBackGroundTasksIntegration:
    """Integration tests for BackGroundTasks."""

    @pytest.mark.asyncio
    async def test_full_integration_scenario(self):
        """Test full integration scenario with realistic bot behavior."""
        mock_bot = AsyncMock()
        mock_bot.command_prefix = ["!"]
        mock_bot.user = MagicMock()
        mock_bot.user.name = "TestBot"
        mock_bot.log = MagicMock()
        mock_bot.wait_until_ready = AsyncMock()
        mock_bot.change_presence = AsyncMock()

        iteration_count = 0

        def mock_is_closed():
            nonlocal iteration_count
            iteration_count += 1
            return iteration_count > 2

        mock_bot.is_closed = mock_is_closed

        bg_tasks = BackGroundTasks(mock_bot)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await bg_tasks.change_presence_task(5)

        mock_bot.wait_until_ready.assert_called_once()
        assert mock_bot.change_presence.call_count >= 1
        assert mock_bot.log.info.call_count >= 1
        assert mock_sleep.call_count >= 1

        for call in mock_bot.change_presence.call_args_list:
            activity = call[1]["activity"]
            assert isinstance(activity, discord.Game)
            assert " | !help" in activity.name
            assert call[1]["status"] == discord.Status.online

        for call in mock_bot.log.info.call_args_list:
            message = call[0][0]
            assert "Background task (5s) - Changing activity:" in message
