"""Tests for GW2 settings module."""

import os
import pytest
from src.gw2.constants.gw2_settings import Gw2Settings, get_gw2_settings
from unittest.mock import patch


class TestGw2Settings:
    """Test cases for Gw2Settings class."""

    def test_default_values_without_env_vars(self):
        """Test that default values are used when no environment variables are set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Gw2Settings()

            # GW2 configuration
            assert settings.embed_color == "green"
            assert settings.api_version == 2

            # GW2 cooldowns
            assert settings.account_cooldown == 20
            assert settings.api_keys_cooldown == 20
            assert settings.characters_cooldown == 20
            assert settings.config_cooldown == 20
            assert settings.daily_cooldown == 20
            assert settings.misc_cooldown == 20
            assert settings.session_cooldown == 60
            assert settings.worlds_cooldown == 20
            assert settings.wvw_cooldown == 20

    def test_env_var_overrides(self):
        """Test that environment variables override default values."""
        env_vars = {
            "GW2_EMBED_COLOR": "blue",
            "GW2_API_VERSION": "3",
            "GW2_ACCOUNT_COOLDOWN": "30",
            "GW2_API_KEYS_COOLDOWN": "25",
            "GW2_CHARACTERS_COOLDOWN": "15",
            "GW2_CONFIG_COOLDOWN": "35",
            "GW2_DAILY_COOLDOWN": "40",
            "GW2_MISC_COOLDOWN": "50",
            "GW2_SESSION_COOLDOWN": "120",
            "GW2_WORLDS_COOLDOWN": "10",
            "GW2_WVW_COOLDOWN": "45",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Gw2Settings()

            # GW2 configuration
            assert settings.embed_color == "blue"
            assert settings.api_version == 3

            # GW2 cooldowns
            assert settings.account_cooldown == 30
            assert settings.api_keys_cooldown == 25
            assert settings.characters_cooldown == 15
            assert settings.config_cooldown == 35
            assert settings.daily_cooldown == 40
            assert settings.misc_cooldown == 50
            assert settings.session_cooldown == 120
            assert settings.worlds_cooldown == 10
            assert settings.wvw_cooldown == 45

    def test_partial_env_var_overrides(self):
        """Test that only some environment variables override defaults."""
        env_vars = {
            "GW2_EMBED_COLOR": "red",
            "GW2_API_VERSION": "1",
            "GW2_SESSION_COOLDOWN": "90",
            "GW2_WVW_COOLDOWN": "30",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Gw2Settings()

            # Overridden values
            assert settings.embed_color == "red"
            assert settings.api_version == 1
            assert settings.session_cooldown == 90
            assert settings.wvw_cooldown == 30

            # Default values for non-overridden fields
            assert settings.account_cooldown == 20
            assert settings.api_keys_cooldown == 20
            assert settings.characters_cooldown == 20
            assert settings.config_cooldown == 20
            assert settings.daily_cooldown == 20
            assert settings.misc_cooldown == 20
            assert settings.worlds_cooldown == 20

    def test_empty_string_env_vars(self):
        """Test behavior with empty string environment variables."""
        env_vars = {"GW2_EMBED_COLOR": ""}

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Gw2Settings()

            # Empty string should be preserved
            assert settings.embed_color == ""

            # Other defaults should remain
            assert settings.account_cooldown == 20
            assert settings.session_cooldown == 60

    def test_invalid_int_env_vars_fallback_to_default(self):
        """Test that invalid integer environment variables fall back to defaults."""
        env_vars = {
            "GW2_ACCOUNT_COOLDOWN": "not_a_number",
            "GW2_SESSION_COOLDOWN": "invalid_int",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # This should raise a ValidationError for invalid integers
            with pytest.raises(ValueError):  # Pydantic will raise validation error
                Gw2Settings()

    def test_zero_values_are_preserved(self):
        """Test that zero values from environment variables are preserved."""
        env_vars = {
            "GW2_ACCOUNT_COOLDOWN": "0",
            "GW2_SESSION_COOLDOWN": "0",
            "GW2_WVW_COOLDOWN": "0",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Gw2Settings()

            assert settings.account_cooldown == 0
            assert settings.session_cooldown == 0
            assert settings.wvw_cooldown == 0

    def test_negative_values_are_preserved(self):
        """Test that negative values from environment variables are preserved."""
        env_vars = {
            "GW2_ACCOUNT_COOLDOWN": "-1",
            "GW2_SESSION_COOLDOWN": "-5",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Gw2Settings()

            assert settings.account_cooldown == -1
            assert settings.session_cooldown == -5

    def test_large_values_are_preserved(self):
        """Test that large values from environment variables are preserved."""
        env_vars = {
            "GW2_SESSION_COOLDOWN": "3600",
            "GW2_ACCOUNT_COOLDOWN": "86400",
        }  # 1 hour  # 1 day

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Gw2Settings()

            assert settings.session_cooldown == 3600
            assert settings.account_cooldown == 86400

    def test_session_end_delay_below_180_clamped(self):
        """Test that api_session_end_delay below 180 is clamped to 180."""
        env_vars = {"GW2_API_SESSION_END_DELAY": "60"}
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Gw2Settings()
            assert settings.api_session_end_delay == 180.0

    def test_session_end_delay_at_180_preserved(self):
        """Test that api_session_end_delay at exactly 180 is preserved."""
        env_vars = {"GW2_API_SESSION_END_DELAY": "180"}
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Gw2Settings()
            assert settings.api_session_end_delay == 180.0

    def test_session_end_delay_above_180_preserved(self):
        """Test that api_session_end_delay above 180 is preserved."""
        env_vars = {"GW2_API_SESSION_END_DELAY": "300"}
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Gw2Settings()
            assert settings.api_session_end_delay == 300.0

    def test_all_cooldown_fields_exist(self):
        """Test that all expected cooldown fields exist with correct types."""
        settings = Gw2Settings()

        cooldown_fields = [
            "account_cooldown",
            "api_keys_cooldown",
            "characters_cooldown",
            "config_cooldown",
            "daily_cooldown",
            "misc_cooldown",
            "session_cooldown",
            "worlds_cooldown",
            "wvw_cooldown",
        ]

        for field in cooldown_fields:
            assert hasattr(settings, field)
            value = getattr(settings, field)
            assert isinstance(value, (int, type(None)))


class TestGetGw2Settings:
    """Test cases for get_gw2_settings function."""

    def test_get_gw2_settings_caching(self):
        """Test that get_gw2_settings uses caching properly."""
        # Clear the cache
        get_gw2_settings.cache_clear()

        # First call
        settings1 = get_gw2_settings()

        # Second call should use cache
        settings2 = get_gw2_settings()

        # Should return the same instance
        assert settings1 is settings2

    def test_settings_instance_type(self):
        """Test that get_gw2_settings returns Gw2Settings instance."""
        settings = get_gw2_settings()
        assert isinstance(settings, Gw2Settings)

    def test_settings_with_actual_env_file(self):
        """Test settings behavior when .env file might exist."""
        # This test runs with whatever environment is available
        settings = get_gw2_settings()

        # Just verify the structure is correct
        assert hasattr(settings, "embed_color")
        assert hasattr(settings, "api_version")
        assert hasattr(settings, "account_cooldown")
        assert hasattr(settings, "session_cooldown")

        # Verify types
        assert isinstance(settings.embed_color, (str, type(None)))
        assert isinstance(settings.api_version, (int, type(None)))
        assert isinstance(settings.account_cooldown, (int, type(None)))
        assert isinstance(settings.session_cooldown, (int, type(None)))

    def test_gw2_vs_bot_prefix_isolation(self):
        """Test that GW2 settings only respond to GW2_ prefixed env vars."""
        env_vars = {
            "BOT_EMBED_COLOR": "bot_color",  # Should not affect GW2 settings
            "GW2_EMBED_COLOR": "gw2_color",  # Should affect GW2 settings
            "BOT_COOLDOWN": "100",  # Should not affect GW2 settings
            "GW2_SESSION_COOLDOWN": "200",  # Should affect GW2 settings
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Gw2Settings()

            # Should use GW2_ prefixed values
            assert settings.embed_color == "gw2_color"
            assert settings.session_cooldown == 200

            # Should use defaults for non-GW2 prefixed values
            assert settings.account_cooldown == 20  # Default, not affected by BOT_COOLDOWN

    def test_api_version_affects_api_uri(self):
        """Test that changing API version affects the constructed API URI."""
        from src.gw2.constants import gw2_variables

        # Test that API_URI contains the version from settings
        expected_version = get_gw2_settings().api_version
        expected_uri = f"https://api.guildwars2.com/v{expected_version}"
        assert gw2_variables.API_URI == expected_uri
