"""Tests for GW2 currency and achievement ID mappings."""

from src.gw2.constants.gw2_currencies import ACHIEVEMENT_MAPPING, WALLET_DISPLAY_NAMES, WALLET_MAPPING


class TestWalletMapping:
    """Test cases for WALLET_MAPPING constant."""

    def test_is_dict_of_int_to_str(self):
        assert isinstance(WALLET_MAPPING, dict)
        for key, value in WALLET_MAPPING.items():
            assert isinstance(key, int), f"Key {key} is not int"
            assert isinstance(value, str), f"Value {value} for key {key} is not str"

    def test_no_duplicate_values(self):
        values = list(WALLET_MAPPING.values())
        assert len(values) == len(set(values)), f"Duplicate values found: {[v for v in values if values.count(v) > 1]}"

    def test_all_keys_are_positive(self):
        for key in WALLET_MAPPING:
            assert key > 0, f"Key {key} is not positive"

    def test_all_values_are_snake_case(self):
        for value in WALLET_MAPPING.values():
            assert value == value.lower(), f"Value {value} is not lowercase"
            assert " " not in value, f"Value {value} contains spaces"

    def test_contains_gold(self):
        assert 1 in WALLET_MAPPING
        assert WALLET_MAPPING[1] == "gold"

    def test_contains_karma(self):
        assert 2 in WALLET_MAPPING
        assert WALLET_MAPPING[2] == "karma"

    def test_contains_gems(self):
        assert 4 in WALLET_MAPPING
        assert WALLET_MAPPING[4] == "gems"

    def test_contains_laurels(self):
        assert 3 in WALLET_MAPPING
        assert WALLET_MAPPING[3] == "laurels"

    def test_contains_spirit_shards(self):
        assert 23 in WALLET_MAPPING
        assert WALLET_MAPPING[23] == "spirit_shards"

    def test_contains_badges_of_honor(self):
        assert 15 in WALLET_MAPPING
        assert WALLET_MAPPING[15] == "badges_honor"

    def test_contains_fractal_relics(self):
        assert 7 in WALLET_MAPPING
        assert WALLET_MAPPING[7] == "fractal_relics"

    def test_contains_volatile_magic(self):
        assert 45 in WALLET_MAPPING
        assert WALLET_MAPPING[45] == "volatile_magic"

    def test_contains_unbound_magic(self):
        assert 32 in WALLET_MAPPING
        assert WALLET_MAPPING[32] == "unbound_magic"

    def test_contains_transmutation_charges(self):
        assert 18 in WALLET_MAPPING
        assert WALLET_MAPPING[18] == "transmutation_charges"

    def test_contains_wvw_tickets(self):
        assert 26 in WALLET_MAPPING
        assert WALLET_MAPPING[26] == "wvw_tickets"

    def test_contains_magnetite_shards(self):
        assert 28 in WALLET_MAPPING
        assert WALLET_MAPPING[28] == "magnetite_shards"

    def test_contains_research_notes(self):
        assert 61 in WALLET_MAPPING
        assert WALLET_MAPPING[61] == "research_notes"

    def test_contains_astral_acclaim(self):
        assert 63 in WALLET_MAPPING
        assert WALLET_MAPPING[63] == "astral_acclaim"

    def test_has_expected_count(self):
        assert len(WALLET_MAPPING) == 79


class TestWalletDisplayNames:
    """Test cases for WALLET_DISPLAY_NAMES constant."""

    def test_is_dict_of_str_to_str(self):
        assert isinstance(WALLET_DISPLAY_NAMES, dict)
        for key, value in WALLET_DISPLAY_NAMES.items():
            assert isinstance(key, str), f"Key {key} is not str"
            assert isinstance(value, str), f"Value {value} for key {key} is not str"

    def test_all_keys_are_snake_case(self):
        for key in WALLET_DISPLAY_NAMES:
            assert key == key.lower(), f"Key {key} is not lowercase"
            assert " " not in key, f"Key {key} contains spaces"

    def test_all_values_are_nonempty(self):
        for key, value in WALLET_DISPLAY_NAMES.items():
            assert len(value) > 0, f"Display name for {key} is empty"

    def test_gold_display_name(self):
        assert WALLET_DISPLAY_NAMES["gold"] == "Gold"

    def test_karma_display_name(self):
        assert WALLET_DISPLAY_NAMES["karma"] == "Karma"

    def test_gems_display_name(self):
        assert WALLET_DISPLAY_NAMES["gems"] == "Gems"

    def test_wvw_tickets_display_name(self):
        assert WALLET_DISPLAY_NAMES["wvw_tickets"] == "WvW Skirmish Tickets"

    def test_research_notes_display_name(self):
        assert WALLET_DISPLAY_NAMES["research_notes"] == "Research Notes"

    def test_badges_honor_display_name(self):
        assert WALLET_DISPLAY_NAMES["badges_honor"] == "Badges of Honor"

    def test_has_expected_count(self):
        assert len(WALLET_DISPLAY_NAMES) == 79


class TestWalletMappingAndDisplayNamesConsistency:
    """Test that WALLET_MAPPING and WALLET_DISPLAY_NAMES are consistent."""

    def test_every_mapping_value_has_display_name(self):
        for api_id, stat_name in WALLET_MAPPING.items():
            assert stat_name in WALLET_DISPLAY_NAMES, (
                f"WALLET_MAPPING value '{stat_name}' (API ID {api_id}) has no display name"
            )

    def test_every_display_name_key_has_mapping(self):
        mapping_values = set(WALLET_MAPPING.values())
        for stat_name in WALLET_DISPLAY_NAMES:
            assert stat_name in mapping_values, (
                f"WALLET_DISPLAY_NAMES key '{stat_name}' is not in WALLET_MAPPING values"
            )

    def test_same_count(self):
        assert len(WALLET_MAPPING) == len(WALLET_DISPLAY_NAMES)


class TestAchievementMapping:
    """Test cases for ACHIEVEMENT_MAPPING constant."""

    def test_is_dict_of_int_to_str(self):
        assert isinstance(ACHIEVEMENT_MAPPING, dict)
        for key, value in ACHIEVEMENT_MAPPING.items():
            assert isinstance(key, int), f"Key {key} is not int"
            assert isinstance(value, str), f"Value {value} for key {key} is not str"

    def test_no_duplicate_values(self):
        values = list(ACHIEVEMENT_MAPPING.values())
        assert len(values) == len(set(values))

    def test_all_keys_are_positive(self):
        for key in ACHIEVEMENT_MAPPING:
            assert key > 0

    def test_contains_players_killed(self):
        assert 283 in ACHIEVEMENT_MAPPING
        assert ACHIEVEMENT_MAPPING[283] == "players"

    def test_contains_yaks_scorted(self):
        assert 285 in ACHIEVEMENT_MAPPING
        assert ACHIEVEMENT_MAPPING[285] == "yaks_scorted"

    def test_contains_yaks_killed(self):
        assert 288 in ACHIEVEMENT_MAPPING
        assert ACHIEVEMENT_MAPPING[288] == "yaks"

    def test_contains_camps(self):
        assert 291 in ACHIEVEMENT_MAPPING
        assert ACHIEVEMENT_MAPPING[291] == "camps"

    def test_contains_castles(self):
        assert 294 in ACHIEVEMENT_MAPPING
        assert ACHIEVEMENT_MAPPING[294] == "castles"

    def test_contains_towers(self):
        assert 297 in ACHIEVEMENT_MAPPING
        assert ACHIEVEMENT_MAPPING[297] == "towers"

    def test_contains_keeps(self):
        assert 300 in ACHIEVEMENT_MAPPING
        assert ACHIEVEMENT_MAPPING[300] == "keeps"

    def test_has_expected_count(self):
        assert len(ACHIEVEMENT_MAPPING) == 7

    def test_all_values_are_snake_case(self):
        for value in ACHIEVEMENT_MAPPING.values():
            assert value == value.lower()
            assert " " not in value
