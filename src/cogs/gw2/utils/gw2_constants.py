#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
GW2_SETTINGS_FILENAME = os.path.join(BASE_DIR, "config", "gw2_settings.ini")
WIKI_URL = "https://wiki.guildwars2.com"
GW2_WIKI_ICON_URL = "https://wiki.guildwars.com/images/b/bf/Normal_gw2logo.jpg"
GW2_SETTINGS_URL_FILE = "https://raw.githubusercontent.com/ddc/DiscordBot/master/config/gw2_settings.ini"
