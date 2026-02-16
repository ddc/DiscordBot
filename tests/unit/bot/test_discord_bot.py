"""Tests for Bot class in src/bot/discord_bot.py."""

import sys
from unittest.mock import Mock

sys.modules["ddcDatabases"] = Mock()

import discord
import pytest
from src.bot.constants import messages
from src.bot.discord_bot import Bot
from unittest.mock import AsyncMock, MagicMock, patch


class TestBotInit:
    """Test cases for Bot.__init__."""

    @patch("src.bot.discord_bot.profanity")
    @patch("src.bot.discord_bot.get_gw2_settings")
    @patch("src.bot.discord_bot.get_bot_settings")
    @patch("src.bot.discord_bot.bot_utils")
    def _create_bot(self, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity, **overrides):
        """Helper to create a Bot instance with all patches applied."""
        mock_bot_utils.get_current_date_time.return_value = MagicMock()
        mock_bot_utils.get_color_settings.return_value = discord.Color.green()

        mock_bot_settings = MagicMock()
        mock_bot_settings.bg_activity_timer = 0
        mock_bot_settings.allowed_dm_commands = "owner, about"
        mock_bot_settings.bot_reaction_words = "stupid, retard"
        mock_bot_settings.embed_color = "green"
        mock_bot_settings.embed_owner_color = "dark_purple"
        mock_bot_settings.exclusive_users = ""
        mock_get_bot.return_value = mock_bot_settings

        mock_gw2_settings = MagicMock()
        mock_gw2_settings.embed_color = "green"
        mock_get_gw2.return_value = mock_gw2_settings

        kwargs = {
            "command_prefix": "!",
            "intents": discord.Intents.default(),
            "aiosession": MagicMock(),
            "db_session": MagicMock(),
            "log": MagicMock(),
        }
        kwargs.update(overrides)

        bot = Bot(**kwargs)
        return bot, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity

    def test_bot_init_stores_aiosession(self):
        """Verify aiosession is stored on the bot instance."""
        aiosession = MagicMock(name="aiosession")
        bot, *_ = self._create_bot(aiosession=aiosession)
        assert bot.aiosession is aiosession

    def test_bot_init_stores_db_session(self):
        """Verify db_session is stored on the bot instance."""
        db_session = MagicMock(name="db_session")
        bot, *_ = self._create_bot(db_session=db_session)
        assert bot.db_session is db_session

    def test_bot_init_stores_log(self):
        """Verify log is stored on the bot instance."""
        log = MagicMock(name="log")
        bot, *_ = self._create_bot(log=log)
        assert bot.log is log

    def test_bot_init_sets_start_time(self):
        """Verify start_time is set from bot_utils.get_current_date_time."""
        bot, mock_bot_utils, *_ = self._create_bot()
        mock_bot_utils.get_current_date_time.assert_called_once()
        assert bot.start_time is mock_bot_utils.get_current_date_time.return_value

    def test_bot_init_initializes_settings_dict(self):
        """Verify settings is a dict populated by _load_settings."""
        bot, *_ = self._create_bot()
        assert isinstance(bot.settings, dict)
        # _load_settings is called, so it should have 'bot' and 'gw2' keys
        assert "bot" in bot.settings
        assert "gw2" in bot.settings

    def test_bot_init_loads_profanity(self):
        """Verify profanity.load_censor_words was called and profanity is stored."""
        bot, _, _, _, mock_profanity = self._create_bot()
        mock_profanity.load_censor_words.assert_called_once()
        assert bot.profanity is mock_profanity

    @patch("src.bot.discord_bot.profanity")
    @patch("src.bot.discord_bot.get_gw2_settings")
    @patch("src.bot.discord_bot.get_bot_settings")
    @patch("src.bot.discord_bot.bot_utils")
    def test_bot_init_calls_load_settings(self, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity):
        """Verify _load_settings is called during __init__."""
        mock_bot_utils.get_current_date_time.return_value = MagicMock()
        mock_bot_utils.get_color_settings.return_value = discord.Color.green()

        mock_bot_settings = MagicMock()
        mock_get_bot.return_value = mock_bot_settings

        mock_gw2_settings = MagicMock()
        mock_get_gw2.return_value = mock_gw2_settings

        with patch.object(Bot, "_load_settings") as mock_load:
            bot = Bot(
                command_prefix="!",
                intents=discord.Intents.default(),
                aiosession=MagicMock(),
                db_session=MagicMock(),
                log=MagicMock(),
            )
            mock_load.assert_called_once()


class TestLoadSettings:
    """Test cases for Bot._load_settings."""

    @patch("src.bot.discord_bot.profanity")
    @patch("src.bot.discord_bot.get_gw2_settings")
    @patch("src.bot.discord_bot.get_bot_settings")
    @patch("src.bot.discord_bot.bot_utils")
    def test_load_settings_populates_bot_settings(self, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity):
        """Verify _load_settings populates self.settings['bot'] and self.settings['gw2']."""
        mock_bot_utils.get_current_date_time.return_value = MagicMock()
        embed_color = discord.Color.green()
        owner_color = discord.Color.dark_purple()
        gw2_color = discord.Color.blue()
        mock_bot_utils.get_color_settings.side_effect = [embed_color, owner_color, gw2_color]

        mock_bot_settings = MagicMock()
        mock_bot_settings.bg_activity_timer = 300
        mock_bot_settings.allowed_dm_commands = "owner, about"
        mock_bot_settings.bot_reaction_words = "stupid, retard"
        mock_bot_settings.embed_color = "green"
        mock_bot_settings.embed_owner_color = "dark_purple"
        mock_bot_settings.exclusive_users = "user1"
        mock_get_bot.return_value = mock_bot_settings

        mock_gw2_settings = MagicMock()
        mock_gw2_settings.embed_color = "green"
        mock_get_gw2.return_value = mock_gw2_settings

        bot = Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            aiosession=MagicMock(),
            db_session=MagicMock(),
            log=MagicMock(),
        )

        assert bot.settings["bot"]["BGActivityTimer"] == 300
        assert bot.settings["bot"]["AllowedDMCommands"] == ["owner", "about"]
        assert bot.settings["bot"]["BotReactionWords"] == ["stupid", "retard"]
        assert bot.settings["bot"]["EmbedColor"] == embed_color
        assert bot.settings["bot"]["EmbedOwnerColor"] == owner_color
        assert bot.settings["bot"]["ExclusiveUsers"] == "user1"
        assert bot.settings["gw2"]["EmbedColor"] == gw2_color

    @patch("src.bot.discord_bot.profanity")
    @patch("src.bot.discord_bot.get_gw2_settings")
    @patch("src.bot.discord_bot.get_bot_settings")
    @patch("src.bot.discord_bot.bot_utils")
    def test_load_settings_error_raises(self, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity):
        """Verify exception propagates and log.error is called when _load_settings fails."""
        mock_bot_utils.get_current_date_time.return_value = MagicMock()
        mock_get_bot.side_effect = RuntimeError("settings load failure")

        log = MagicMock()

        with pytest.raises(RuntimeError, match="settings load failure"):
            Bot(
                command_prefix="!",
                intents=discord.Intents.default(),
                aiosession=MagicMock(),
                db_session=MagicMock(),
                log=log,
            )

        log.error.assert_called_once()
        error_msg = log.error.call_args[0][0]
        assert messages.BOT_LOAD_SETTINGS_FAILED in error_msg

    @patch("src.bot.discord_bot.profanity")
    @patch("src.bot.discord_bot.get_gw2_settings")
    @patch("src.bot.discord_bot.get_bot_settings")
    @patch("src.bot.discord_bot.bot_utils")
    def test_allowed_dm_commands_parsed_as_list(self, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity):
        """Verify comma-separated allowed_dm_commands string is parsed into a list."""
        mock_bot_utils.get_current_date_time.return_value = MagicMock()
        mock_bot_utils.get_color_settings.return_value = discord.Color.green()

        mock_bot_settings = MagicMock()
        mock_bot_settings.allowed_dm_commands = "owner, about, gw2"
        mock_bot_settings.bot_reaction_words = ""
        mock_get_bot.return_value = mock_bot_settings

        mock_gw2_settings = MagicMock()
        mock_get_gw2.return_value = mock_gw2_settings

        bot = Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            aiosession=MagicMock(),
            db_session=MagicMock(),
            log=MagicMock(),
        )

        result = bot.settings["bot"]["AllowedDMCommands"]
        assert isinstance(result, list)
        assert result == ["owner", "about", "gw2"]

    @patch("src.bot.discord_bot.profanity")
    @patch("src.bot.discord_bot.get_gw2_settings")
    @patch("src.bot.discord_bot.get_bot_settings")
    @patch("src.bot.discord_bot.bot_utils")
    def test_allowed_dm_commands_empty_returns_none(self, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity):
        """Verify empty allowed_dm_commands string returns None."""
        mock_bot_utils.get_current_date_time.return_value = MagicMock()
        mock_bot_utils.get_color_settings.return_value = discord.Color.green()

        mock_bot_settings = MagicMock()
        mock_bot_settings.allowed_dm_commands = ""
        mock_bot_settings.bot_reaction_words = ""
        mock_get_bot.return_value = mock_bot_settings

        mock_gw2_settings = MagicMock()
        mock_get_gw2.return_value = mock_gw2_settings

        bot = Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            aiosession=MagicMock(),
            db_session=MagicMock(),
            log=MagicMock(),
        )

        assert bot.settings["bot"]["AllowedDMCommands"] is None

    @patch("src.bot.discord_bot.profanity")
    @patch("src.bot.discord_bot.get_gw2_settings")
    @patch("src.bot.discord_bot.get_bot_settings")
    @patch("src.bot.discord_bot.bot_utils")
    def test_bot_reaction_words_parsed_as_list(self, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity):
        """Verify comma-separated bot_reaction_words string is parsed into a list."""
        mock_bot_utils.get_current_date_time.return_value = MagicMock()
        mock_bot_utils.get_color_settings.return_value = discord.Color.green()

        mock_bot_settings = MagicMock()
        mock_bot_settings.allowed_dm_commands = "owner"
        mock_bot_settings.bot_reaction_words = "stupid, retard, idiot"
        mock_get_bot.return_value = mock_bot_settings

        mock_gw2_settings = MagicMock()
        mock_get_gw2.return_value = mock_gw2_settings

        bot = Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            aiosession=MagicMock(),
            db_session=MagicMock(),
            log=MagicMock(),
        )

        result = bot.settings["bot"]["BotReactionWords"]
        assert isinstance(result, list)
        assert result == ["stupid", "retard", "idiot"]

    @patch("src.bot.discord_bot.profanity")
    @patch("src.bot.discord_bot.get_gw2_settings")
    @patch("src.bot.discord_bot.get_bot_settings")
    @patch("src.bot.discord_bot.bot_utils")
    def test_bot_reaction_words_empty_returns_empty_list(
        self, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity
    ):
        """Verify empty bot_reaction_words string returns empty list."""
        mock_bot_utils.get_current_date_time.return_value = MagicMock()
        mock_bot_utils.get_color_settings.return_value = discord.Color.green()

        mock_bot_settings = MagicMock()
        mock_bot_settings.allowed_dm_commands = "owner"
        mock_bot_settings.bot_reaction_words = ""
        mock_get_bot.return_value = mock_bot_settings

        mock_gw2_settings = MagicMock()
        mock_get_gw2.return_value = mock_gw2_settings

        bot = Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            aiosession=MagicMock(),
            db_session=MagicMock(),
            log=MagicMock(),
        )

        result = bot.settings["bot"]["BotReactionWords"]
        assert isinstance(result, list)
        assert result == []


class TestSetupHook:
    """Test cases for Bot.setup_hook."""

    @pytest.mark.asyncio
    @patch("src.bot.discord_bot.profanity")
    @patch("src.bot.discord_bot.get_gw2_settings")
    @patch("src.bot.discord_bot.get_bot_settings")
    @patch("src.bot.discord_bot.bot_utils")
    async def test_setup_hook_loads_cogs(self, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity):
        """Verify setup_hook calls bot_utils.load_cogs and logs success."""
        mock_bot_utils.get_current_date_time.return_value = MagicMock()
        mock_bot_utils.get_color_settings.return_value = discord.Color.green()
        mock_bot_utils.load_cogs = AsyncMock()

        mock_bot_settings = MagicMock()
        mock_get_bot.return_value = mock_bot_settings

        mock_gw2_settings = MagicMock()
        mock_get_gw2.return_value = mock_gw2_settings

        log = MagicMock()
        bot = Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            aiosession=MagicMock(),
            db_session=MagicMock(),
            log=log,
        )

        await bot.setup_hook()

        mock_bot_utils.load_cogs.assert_awaited_once_with(bot)
        log.info.assert_any_call(messages.BOT_LOADED_ALL_COGS_SUCCESS)

    @pytest.mark.asyncio
    @patch("src.bot.discord_bot.profanity")
    @patch("src.bot.discord_bot.get_gw2_settings")
    @patch("src.bot.discord_bot.get_bot_settings")
    @patch("src.bot.discord_bot.bot_utils")
    async def test_setup_hook_failure_logs_and_raises(self, mock_bot_utils, mock_get_bot, mock_get_gw2, mock_profanity):
        """Verify setup_hook logs error and re-raises when load_cogs fails."""
        mock_bot_utils.get_current_date_time.return_value = MagicMock()
        mock_bot_utils.get_color_settings.return_value = discord.Color.green()
        mock_bot_utils.load_cogs = AsyncMock(side_effect=RuntimeError("cog load boom"))

        mock_bot_settings = MagicMock()
        mock_get_bot.return_value = mock_bot_settings

        mock_gw2_settings = MagicMock()
        mock_get_gw2.return_value = mock_gw2_settings

        log = MagicMock()
        bot = Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            aiosession=MagicMock(),
            db_session=MagicMock(),
            log=log,
        )

        with pytest.raises(RuntimeError, match="cog load boom"):
            await bot.setup_hook()

        log.error.assert_called()
        error_msg = log.error.call_args[0][0]
        assert messages.BOT_LOAD_COGS_FAILED in error_msg
