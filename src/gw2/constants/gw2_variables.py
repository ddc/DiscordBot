from pathlib import Path
from src.gw2.constants.gw2_settings import get_gw2_settings
from typing import Final

# Base directory
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent.parent

# API configuration
_gw2_settings = get_gw2_settings()
API_URI: Final[str] = f"https://api.guildwars2.com/v{_gw2_settings.api_version}"

# Wiki and external URLs
WIKI_URL: Final[str] = "https://wiki.guildwars2.com"
GW2_WIKI_ICON_URL: Final[str] = "https://wiki.guildwars.com/images/b/bf/Normal_gw2logo.jpg"
GW2TP_ITEM_URL: Final[str] = "https://www.gw2tp.com/item"
GW2BLTC_ITEM_URL: Final[str] = "https://www.gw2bltc.com/en/item"

# GW2 API endpoints (relative to API_URI)
API_ACCOUNT: Final[str] = "account"
API_ACCOUNT_ACHIEVEMENTS: Final[str] = "account/achievements"
API_ACCOUNT_WALLET: Final[str] = "account/wallet"
API_ACCOUNT_WIZARDSVAULT: Final[str] = "account/wizardsvault"
API_ACHIEVEMENTS: Final[str] = "achievements"
API_CHARACTERS: Final[str] = "characters"
API_GUILD: Final[str] = "guild"
API_PVP_STATS: Final[str] = "pvp/stats"
API_TOKENINFO: Final[str] = "tokeninfo"
API_WORLDS: Final[str] = "worlds"
API_WVW_MATCHES: Final[str] = "wvw/matches"
