"""Integration tests that validate GW2 API currency and achievement ID mappings.

These tests connect to the public GW2 API (no authentication required) to verify
that our hardcoded ID mappings still exist in the live API.
"""

import json
import pytest
import urllib.request
from src.gw2.constants.gw2_currencies import ACHIEVEMENT_MAPPING, WALLET_MAPPING

GW2_API_BASE = "https://api.guildwars2.com/v2"
REQUEST_TIMEOUT = 60


def _fetch_json(url: str) -> dict | list:
    """Fetch JSON from a URL using only stdlib."""
    req = urllib.request.Request(url, headers={"User-Agent": "DiscordBot-Tests/1.0"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


@pytest.mark.gw2_api
class TestWalletCurrencyIdsExist:
    """Validate that all WALLET_MAPPING IDs exist in the live GW2 API."""

    @pytest.fixture(scope="class")
    def api_currencies_by_id(self):
        """Fetch currency data for all our mapped IDs from the GW2 API."""
        ids = ",".join(str(k) for k in sorted(WALLET_MAPPING.keys()))
        return {c["id"]: c for c in _fetch_json(f"{GW2_API_BASE}/currencies?ids={ids}")}

    def test_all_wallet_ids_exist_in_api(self, api_currencies_by_id):
        missing = set(WALLET_MAPPING.keys()) - set(api_currencies_by_id.keys())
        assert not missing, f"WALLET_MAPPING contains IDs not found in GW2 API: {missing}"

    def test_all_currencies_have_name_field(self, api_currencies_by_id):
        for cid, data in api_currencies_by_id.items():
            assert "name" in data, f"Currency {cid} has no name field"


@pytest.mark.gw2_api
class TestWalletCurrencyNamesMatch:
    """Validate that our currency names roughly match the API names."""

    @pytest.fixture(scope="class")
    def api_currencies(self):
        """Fetch full currency data from the GW2 API."""
        ids = ",".join(str(k) for k in sorted(WALLET_MAPPING.keys()))
        return {c["id"]: c["name"] for c in _fetch_json(f"{GW2_API_BASE}/currencies?ids={ids}")}

    def test_gold_maps_to_coin(self, api_currencies):
        assert api_currencies[1] == "Coin"

    def test_karma_maps_to_karma(self, api_currencies):
        assert api_currencies[2] == "Karma"

    def test_gems_maps_to_gem(self, api_currencies):
        assert api_currencies[4] == "Gem"

    def test_laurels_maps_to_laurel(self, api_currencies):
        assert api_currencies[3] == "Laurel"

    def test_spirit_shards_maps_correctly(self, api_currencies):
        assert api_currencies[23] == "Spirit Shard"

    def test_badges_of_honor_maps_correctly(self, api_currencies):
        assert api_currencies[15] == "Badge of Honor"

    def test_all_ids_have_api_data(self, api_currencies):
        missing = set(WALLET_MAPPING.keys()) - set(api_currencies.keys())
        assert not missing, f"Could not fetch API data for currency IDs: {missing}"


@pytest.mark.gw2_api
class TestAchievementIdsExist:
    """Validate that all ACHIEVEMENT_MAPPING IDs exist in the live GW2 API."""

    @pytest.fixture(scope="class")
    def api_achievements(self):
        """Fetch achievement data for our mapped IDs from the GW2 API."""
        ids = ",".join(str(k) for k in sorted(ACHIEVEMENT_MAPPING.keys()))
        return {a["id"]: a for a in _fetch_json(f"{GW2_API_BASE}/achievements?ids={ids}")}

    def test_all_achievement_ids_exist(self, api_achievements):
        missing = set(ACHIEVEMENT_MAPPING.keys()) - set(api_achievements.keys())
        assert not missing, f"ACHIEVEMENT_MAPPING contains IDs not found in GW2 API: {missing}"

    def test_all_achievements_have_tiers(self, api_achievements):
        """All WvW achievements should have progression tiers."""
        for ach_id, ach in api_achievements.items():
            assert "tiers" in ach, f"Achievement {ach_id} ({ach['name']}) has no tiers"
            assert len(ach["tiers"]) > 0, f"Achievement {ach_id} ({ach['name']}) has empty tiers"

    def test_all_achievements_are_permanent(self, api_achievements):
        """All WvW stat achievements should be permanent (not daily/weekly)."""
        for ach_id, ach in api_achievements.items():
            flags = ach.get("flags", [])
            assert "Permanent" in flags, f"Achievement {ach_id} ({ach['name']}) is not permanent"

    def test_players_killed_achievement_requirement(self, api_achievements):
        ach = api_achievements[283]
        assert "player" in ach.get("requirement", "").lower()

    def test_yaks_killed_achievement_requirement(self, api_achievements):
        ach = api_achievements[288]
        req = ach.get("requirement", "").lower()
        assert "yak" in req or "caravan" in req or "dolyak" in req

    def test_camps_captured_achievement_requirement(self, api_achievements):
        ach = api_achievements[291]
        assert "camp" in ach.get("requirement", "").lower()


@pytest.mark.gw2_api
class TestWorldsEndpoint:
    """Validate that the worlds endpoint is accessible and returns data."""

    def test_can_fetch_world_details(self):
        """Test that we can fetch details for a specific world."""
        worlds = _fetch_json(f"{GW2_API_BASE}/worlds?ids=1001")
        assert len(worlds) == 1
        assert worlds[0]["id"] == 1001
        assert "name" in worlds[0]
