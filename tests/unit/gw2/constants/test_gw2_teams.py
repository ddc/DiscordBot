"""Tests for GW2 World Restructuring team constants."""

from src.gw2.constants.gw2_teams import WR_TEAM_NAMES, get_team_name, is_wr_team_id


class TestIsWrTeamId:
    """Test cases for is_wr_team_id function."""

    def test_na_team_id(self):
        assert is_wr_team_id(11001) is True

    def test_na_team_id_last(self):
        assert is_wr_team_id(11012) is True

    def test_eu_team_id(self):
        assert is_wr_team_id(12001) is True

    def test_eu_team_id_last(self):
        assert is_wr_team_id(12015) is True

    def test_legacy_na_world_id(self):
        assert is_wr_team_id(1001) is False

    def test_legacy_eu_world_id(self):
        assert is_wr_team_id(2001) is False

    def test_zero(self):
        assert is_wr_team_id(0) is False

    def test_boundary_below(self):
        assert is_wr_team_id(11000) is False

    def test_boundary_above(self):
        assert is_wr_team_id(13000) is False

    def test_mid_range_gap(self):
        """ID between NA and EU ranges is still considered WR."""
        assert is_wr_team_id(11500) is True


class TestGetTeamName:
    """Test cases for get_team_name function."""

    def test_na_team(self):
        assert get_team_name(11001) == "Team 1 (NA)"

    def test_eu_team(self):
        assert get_team_name(12001) == "Team 1 (EU)"

    def test_last_na_team(self):
        assert get_team_name(11012) == "Team 12 (NA)"

    def test_last_eu_team(self):
        assert get_team_name(12015) == "Team 15 (EU)"

    def test_unknown_team_id(self):
        assert get_team_name(99999) is None

    def test_legacy_world_id(self):
        assert get_team_name(1001) is None

    def test_zero(self):
        assert get_team_name(0) is None


class TestWrTeamNames:
    """Test cases for WR_TEAM_NAMES dict."""

    def test_has_12_na_teams(self):
        na_teams = {k: v for k, v in WR_TEAM_NAMES.items() if 11001 <= k <= 11999}
        assert len(na_teams) == 12

    def test_has_15_eu_teams(self):
        eu_teams = {k: v for k, v in WR_TEAM_NAMES.items() if 12001 <= k <= 12999}
        assert len(eu_teams) == 15

    def test_total_teams(self):
        assert len(WR_TEAM_NAMES) == 27

    def test_all_na_names_contain_na(self):
        for team_id in range(11001, 11013):
            assert "(NA)" in WR_TEAM_NAMES[team_id]

    def test_all_eu_names_contain_eu(self):
        for team_id in range(12001, 12016):
            assert "(EU)" in WR_TEAM_NAMES[team_id]
