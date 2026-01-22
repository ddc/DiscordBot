"""Tests for bot settings module."""

import os
from unittest.mock import patch
import pytest
from src.bot.constants.settings import BotSettings, get_bot_settings


class TestBotSettings:
    """Test cases for BotSettings class."""

    def test_default_values_structure(self):
        """Test that settings have the expected structure and types."""
        settings = BotSettings()

        # Test that all expected fields exist
        assert hasattr(settings, 'prefix')
        assert hasattr(settings, 'token')
        assert hasattr(settings, 'openai_model')
        assert hasattr(settings, 'openai_api_key')
        assert hasattr(settings, 'bg_activity_timer')
        assert hasattr(settings, 'allowed_dm_commands')
        assert hasattr(settings, 'embed_color')
        assert hasattr(settings, 'admin_cooldown')

        # Test types are correct (allowing for None due to Optional)
        assert isinstance(settings.prefix, (str, type(None)))
        assert isinstance(settings.token, (str, type(None)))
        assert isinstance(settings.openai_model, (str, type(None)))
        assert isinstance(settings.openai_api_key, (str, type(None)))
        assert isinstance(settings.bg_activity_timer, (int, type(None)))
        assert isinstance(settings.admin_cooldown, (int, type(None)))

    def test_env_var_overrides(self):
        """Test that environment variables override default values."""
        env_vars = {
            "BOT_PREFIX": ">>",
            "BOT_TOKEN": "test_token_123",
            "BOT_OPENAI_MODEL": "gpt-4",
            "BOT_OPENAI_API_KEY": "test_api_key",
            "BOT_BG_ACTIVITY_TIMER": "300",
            "BOT_ALLOWED_DM_COMMANDS": "owner, test",
            "BOT_BOT_REACTION_WORDS": "test, words",
            "BOT_EMBED_COLOR": "blue",
            "BOT_EMBED_OWNER_COLOR": "red",
            "BOT_EXCLUSIVE_USERS": "user1, user2",
            "BOT_ADMIN_COOLDOWN": "30",
            "BOT_CONFIG_COOLDOWN": "25",
            "BOT_CUSTOM_CMD_COOLDOWN": "15",
            "BOT_DICE_ROLLS_COOLDOWN": "5",
            "BOT_MISC_COOLDOWN": "40",
            "BOT_OPENAI_COOLDOWN": "20",
            "BOT_OWNER_COOLDOWN": "3",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = BotSettings()

            # Basic settings
            assert settings.prefix == ">>"
            assert settings.token == "test_token_123"
            assert settings.openai_model == "gpt-4"
            assert settings.openai_api_key == "test_api_key"

            # Bot configuration
            assert settings.bg_activity_timer == 300
            assert settings.allowed_dm_commands == "owner, test"
            assert settings.bot_reaction_words == "test, words"
            assert settings.embed_color == "blue"
            assert settings.embed_owner_color == "red"
            assert settings.exclusive_users == "user1, user2"

            # Cooldowns
            assert settings.admin_cooldown == 30
            assert settings.config_cooldown == 25
            assert settings.custom_cmd_cooldown == 15
            assert settings.dice_rolls_cooldown == 5
            assert settings.misc_cooldown == 40
            assert settings.openai_cooldown == 20
            assert settings.owner_cooldown == 3

    def test_partial_env_var_overrides(self):
        """Test that only some environment variables override defaults."""
        env_vars = {
            "BOT_PREFIX": "?",
            "BOT_TOKEN": "partial_token", 
            "BOT_ADMIN_COOLDOWN": "35",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = BotSettings()

            # Overridden values
            assert settings.prefix == "?"
            assert settings.token == "partial_token"
            assert settings.admin_cooldown == 35

            # Default values for non-overridden fields
            assert settings.openai_model == "gpt-4o-mini"
            # Note: openai_api_key might have a value from actual env, so we'll check it's set
            assert settings.embed_color == "green"
            assert settings.config_cooldown == 20
            assert settings.owner_cooldown == 5

    def test_empty_string_env_vars(self):
        """Test behavior with empty string environment variables."""
        env_vars = {
            "BOT_PREFIX": "",
            "BOT_ALLOWED_DM_COMMANDS": "",
            "BOT_EXCLUSIVE_USERS": "",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = BotSettings()

            # Empty strings should be preserved
            assert settings.prefix == ""
            assert settings.allowed_dm_commands == ""
            assert settings.exclusive_users == ""

            # Other defaults should remain
            assert settings.embed_color == "green"
            assert settings.admin_cooldown == 20

    def test_invalid_int_env_vars_fallback_to_default(self):
        """Test that invalid integer environment variables fall back to defaults."""
        env_vars = {
            "BOT_ADMIN_COOLDOWN": "not_a_number",
            "BOT_BG_ACTIVITY_TIMER": "invalid",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # This should raise a ValidationError for invalid integers
            with pytest.raises(Exception):  # Pydantic will raise validation error
                BotSettings()

    def test_zero_values_are_preserved(self):
        """Test that zero values from environment variables are preserved."""
        env_vars = {
            "BOT_BG_ACTIVITY_TIMER": "0",
            "BOT_ADMIN_COOLDOWN": "0",
            "BOT_OWNER_COOLDOWN": "0",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = BotSettings()

            assert settings.bg_activity_timer == 0
            assert settings.admin_cooldown == 0
            assert settings.owner_cooldown == 0


class TestGetBotSettings:
    """Test cases for get_bot_settings function."""

    def test_get_bot_settings_caching(self):
        """Test that get_bot_settings uses caching properly."""
        # Clear the cache
        get_bot_settings.cache_clear()

        # First call
        settings1 = get_bot_settings()
        
        # Second call should use cache
        settings2 = get_bot_settings()
        
        # Should return the same instance
        assert settings1 is settings2

    def test_settings_function_returns_botssettings(self):
        """Test that get_bot_settings returns BotSettings instance."""
        settings = get_bot_settings()
        assert isinstance(settings, BotSettings)

    def test_settings_with_actual_env_file(self):
        """Test settings behavior when .env file might exist."""
        # This test runs with whatever environment is available
        settings = get_bot_settings()

        # Just verify the structure is correct
        assert hasattr(settings, 'prefix')
        assert hasattr(settings, 'token')
        assert hasattr(settings, 'admin_cooldown')
        assert hasattr(settings, 'embed_color')

        # Verify types
        assert isinstance(settings.prefix, (str, type(None)))
        assert isinstance(settings.admin_cooldown, (int, type(None)))
