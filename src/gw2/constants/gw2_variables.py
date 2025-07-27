from pathlib import Path
from typing import Final
from src.gw2.constants.gw2_settings import get_gw2_settings


# Base directory
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent.parent

# API configuration
_gw2_settings = get_gw2_settings()
API_URI: Final[str] = f"https://api.guildwars2.com/v{_gw2_settings.api_version}"

# Wiki and external URLs
WIKI_URL: Final[str] = "https://wiki.guildwars2.com"
GW2_WIKI_ICON_URL: Final[str] = "https://wiki.guildwars.com/images/b/bf/Normal_gw2logo.jpg"
