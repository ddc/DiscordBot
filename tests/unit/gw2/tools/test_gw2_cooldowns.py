"""Tests for GW2 cooldowns module."""

import pytest
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


class TestGW2CoolDowns:
    """Test cases for GW2CoolDowns enum."""

    def test_cooldown_enum_values_exist(self):
        """Test that all expected cooldown values exist."""
        expected_cooldowns = ["Account", "ApiKeys", "Characters", "Config", "Daily", "Misc", "Session", "Worlds", "Wvw"]

        for cooldown_name in expected_cooldowns:
            assert hasattr(GW2CoolDowns, cooldown_name)
            cooldown = getattr(GW2CoolDowns, cooldown_name)
            assert isinstance(cooldown.value, tuple)
            assert isinstance(cooldown.value[0], int)
            assert cooldown.value[0] > 0  # All cooldowns should be positive

    def test_cooldown_str_representation(self):
        """Test that cooldowns can be converted to strings."""
        cooldown = GW2CoolDowns.Account
        str_value = str(cooldown)
        assert isinstance(str_value, str)
        assert str_value == str(cooldown.value[0])

    def test_cooldown_seconds_property(self):
        """Test that seconds property returns integer values."""
        for cooldown in GW2CoolDowns:
            seconds = cooldown.seconds
            assert isinstance(seconds, int)
            assert seconds > 0
            assert seconds == cooldown.value[0]

    def test_cooldown_attribute_error(self):
        """Test that accessing non-existent attributes raises appropriate error."""
        with pytest.raises(AttributeError):
            _ = GW2CoolDowns.NonExistentAttribute

    def test_cooldown_values_are_from_settings(self):
        """Test that cooldown values are properly loaded from GW2 settings."""
        from src.bot.constants import variables
        from src.gw2.tools.gw2_cooldowns import _gw2_settings

        # In non-debug mode, values should come from GW2 settings
        if not variables.DEBUG:
            assert GW2CoolDowns.Account.value[0] == _gw2_settings.account_cooldown
            assert GW2CoolDowns.ApiKeys.value[0] == _gw2_settings.api_keys_cooldown
            assert GW2CoolDowns.Characters.value[0] == _gw2_settings.characters_cooldown
            assert GW2CoolDowns.Config.value[0] == _gw2_settings.config_cooldown
            assert GW2CoolDowns.Daily.value[0] == _gw2_settings.daily_cooldown
            assert GW2CoolDowns.Misc.value[0] == _gw2_settings.misc_cooldown
            assert GW2CoolDowns.Session.value[0] == _gw2_settings.session_cooldown
            assert GW2CoolDowns.Worlds.value[0] == _gw2_settings.worlds_cooldown
            assert GW2CoolDowns.Wvw.value[0] == _gw2_settings.wvw_cooldown
        else:
            # In debug mode, all cooldowns should be 1 second
            assert GW2CoolDowns.Account.value[0] == 1
            assert GW2CoolDowns.ApiKeys.value[0] == 1
            assert GW2CoolDowns.Characters.value[0] == 1
            assert GW2CoolDowns.Config.value[0] == 1
            assert GW2CoolDowns.Daily.value[0] == 1
            assert GW2CoolDowns.Misc.value[0] == 1
            assert GW2CoolDowns.Session.value[0] == 1
            assert GW2CoolDowns.Worlds.value[0] == 1
            assert GW2CoolDowns.Wvw.value[0] == 1

    def test_all_cooldowns_have_reasonable_values(self):
        """Test that all cooldown values are within reasonable ranges."""
        for cooldown in GW2CoolDowns:
            # All cooldowns should be between 1 second and 1 day (86400 seconds)
            assert 1 <= cooldown.value[0] <= 86400

    def test_session_cooldown_is_longest(self):
        """Test that session cooldown is typically the longest (when not in debug mode)."""
        from src.bot.constants import variables

        if not variables.DEBUG:
            # Session cooldown should typically be the longest
            session_cooldown = GW2CoolDowns.Session.value[0]
            other_cooldowns = [
                GW2CoolDowns.Account.value[0],
                GW2CoolDowns.ApiKeys.value[0],
                GW2CoolDowns.Characters.value[0],
                GW2CoolDowns.Config.value[0],
                GW2CoolDowns.Daily.value[0],
                GW2CoolDowns.Misc.value[0],
                GW2CoolDowns.Worlds.value[0],
                GW2CoolDowns.Wvw.value[0],
            ]

            # Session should be >= all others (allows for equal values)
            for other_value in other_cooldowns:
                assert session_cooldown >= other_value

    def test_cooldown_enum_iteration(self):
        """Test that we can iterate over all cooldowns."""
        cooldown_names = set()
        for cooldown in GW2CoolDowns:
            cooldown_names.add(cooldown.name)
            assert isinstance(cooldown.value, tuple)
            assert isinstance(cooldown.value[0], int)

        # Should have all expected cooldowns
        expected_names = {"Account", "ApiKeys", "Characters", "Config", "Daily", "Misc", "Session", "Worlds", "Wvw"}
        assert cooldown_names == expected_names
