"""World Restructuring (WR) team constants for Guild Wars 2 WvW.

Since mid-2024, GW2 uses team-based matchmaking (World Restructuring) instead of
server-based WvW. Team IDs (11xxx for NA, 12xxx for EU) are not in the /v2/worlds
API, so names must be hardcoded.
"""

# NA teams: 11001-11012, EU teams: 12001-12015
WR_TEAM_NAMES: dict[int, str] = {
    # North America
    11001: "Team 1 (NA)",
    11002: "Team 2 (NA)",
    11003: "Team 3 (NA)",
    11004: "Team 4 (NA)",
    11005: "Team 5 (NA)",
    11006: "Team 6 (NA)",
    11007: "Team 7 (NA)",
    11008: "Team 8 (NA)",
    11009: "Team 9 (NA)",
    11010: "Team 10 (NA)",
    11011: "Team 11 (NA)",
    11012: "Team 12 (NA)",
    # Europe
    12001: "Team 1 (EU)",
    12002: "Team 2 (EU)",
    12003: "Team 3 (EU)",
    12004: "Team 4 (EU)",
    12005: "Team 5 (EU)",
    12006: "Team 6 (EU)",
    12007: "Team 7 (EU)",
    12008: "Team 8 (EU)",
    12009: "Team 9 (EU)",
    12010: "Team 10 (EU)",
    12011: "Team 11 (EU)",
    12012: "Team 12 (EU)",
    12013: "Team 13 (EU)",
    12014: "Team 14 (EU)",
    12015: "Team 15 (EU)",
}


def is_wr_team_id(world_id: int) -> bool:
    """Check if the given ID is a World Restructuring team ID (11xxx or 12xxx)."""
    return 11001 <= world_id <= 12999


def get_team_name(team_id: int) -> str | None:
    """Get the team name for a WR team ID, or None if not found."""
    return WR_TEAM_NAMES.get(team_id)
