# -*- coding: utf-8 -*-
import os
from pathlib import Path


API_VERSION = 2
API_URI = f"https://api.guildwars2.com/v{API_VERSION}"
###############################################################################
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
GW2_SETTINGS_FILENAME = os.path.join(BASE_DIR, "config", "gw2_settings.ini")
WIKI_URL = "https://wiki.guildwars2.com"
GW2_WIKI_ICON_URL = "https://wiki.guildwars.com/images/b/bf/Normal_gw2logo.jpg"
