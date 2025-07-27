import os
from pathlib import Path
from typing import Final


# Base directory
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent.parent

# API configuration
API_VERSION: Final[int] = 2
API_URI: Final[str] = f"https://api.guildwars2.com/v{API_VERSION}"

# Configuration file paths
GW2_SETTINGS_FILENAME: Final[str] = os.path.join(BASE_DIR, "config", "gw2_settings.ini")

# Wiki and external URLs
WIKI_URL: Final[str] = "https://wiki.guildwars2.com"
GW2_WIKI_ICON_URL: Final[str] = "https://wiki.guildwars.com/images/b/bf/Normal_gw2logo.jpg"
