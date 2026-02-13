from pathlib import Path


def discover_gw2_cogs() -> list[str]:
    """Discover GW2 cog file paths with gw2.py first for command group registration."""
    cogs_dir = Path(__file__).parent
    cogs = [str(cogs_dir / "gw2.py")]
    remaining = [str(p) for p in cogs_dir.glob("*.py") if p.name != "__init__.py"]
    cogs.extend(c for c in remaining if c not in cogs)
    return cogs
