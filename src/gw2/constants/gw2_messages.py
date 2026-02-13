#################################
# EVENT ON COMMAND ERROR
#################################
GW2_SERVER_NOT_FOUND = "Guild Wars 2 server not found"
GW2_SERVER_MORE_INFO = "For more info on gw2 server names"
#################################
# GW2 API
#################################
INVALID_API_KEY = "This API Key is INVALID or no longer exists in gw2 api database"
API_ERROR = "GW2 API ERROR"
API_DOWN = "GW2 API is currently down. Try again later."
API_NOT_FOUND = "GW2 API Not found."
API_REQUEST_REACHED = "GW2 API Requests limit has been saturated. Try again later."
API_ACCESS_DENIED = "Access denied with your GW2 API key."
#################################
# GW2 UTILS
#################################
API_KEY_MESSAGE_REMOVED = "Your message with your API Key was removed for privacy."
API_KEY_MESSAGE_REMOVED_DENIED = (
    "Bot does not have permission to delete the message with your API key.\n"
    "Missing bot permission: `Manage Messages`"
)
#################################
# GW2 ACCOUNT/CHARACTERS
#################################
NO_API_KEY = "You dont have an API key registered.\n"
INVALID_API_KEY_HELP_MESSAGE = "This API Key is INVALID or no longer exists in gw2 api database.\n"


def key_add_info_help(prefix: str) -> str:
    return f"To add or replace an API key send a DM with: `{prefix}gw2 key add <api_key>`\n"


def key_more_info_help(prefix: str) -> str:
    return f"To get info about your api key: `{prefix}gw2 key info`"


API_KEY_NO_PERMISSION = (
    "Your API key doesnt have permission to access your gw2 account.\n" "Please add one key with account permission."
)
#################################
# GW2 CONFIG
#################################
CONFIG_TITLE = "Guild Wars 2 configurations for"


def config_more_info(prefix: str) -> str:
    return f"For more info: {prefix}help gw2 config"


USER_SESSION_TITLE = "GW2 Users Session"
SESSION_ACTIVATED = "Last session `ACTIVATED`\nBot will now record Gw2 users last sessions."
SESSION_DEACTIVATED = "Last session `DEACTIVATED`\nBot will `NOT` record Gw2 users last sessions."
#################################
# GW2 KEY
#################################
KEY_ALREADY_IN_USE = "That API key is already in use by someone else."
KEY_REMOVED_SUCCESSFULLY = "Your GW2 API Key has been deleted successfully."


def key_replaced_successfully(old: str, new: str, server: str) -> str:
    return f"Your API key `{old}` was **replaced** with your new key: `{new}`\nServer: `{server}`\n"


def key_added_successfully(key_name: str, server_name: str) -> str:
    return f"Your key was verified and was **added** to your discord account.\nKey: `{key_name}`\nServer: `{server_name}`\n"


#################################
# GW2 MISC
#################################
LONG_SEARCH = "Search too long"
WIKI_SEARCH_RESULTS = "Wiki Search Results"
NO_RESULTS = "No results!"
CLICK_HERE = "Click here"


def displaying_wiki_search_title(count: int, keyword: str) -> str:
    return f"Displaying **{count}** closest titles that matches **{keyword}**"


CLICK_ON_LINK = "Click on link above for more info !!!"
#################################
# GW2 SESSIONS
#################################
SESSION_TITLE = "GW2 Last Session"


def session_not_active(prefix: str) -> str:
    return f"Last session is not active on this server.\nTo activate use: `{prefix}gw2 config session on`"


SESSION_MISSING_PERMISSIONS_TITLE = "To use this command your API key needs to have the following permissions"
ADD_RIGHT_API_KEY_PERMISSIONS = (
    "Please add another API key with permissions that are MISSING if you want to use this command."
)
SESSION_BOT_STILL_UPDATING = "Bot still updating your stats!"
SESSION_USER_STILL_PLAYING = "You are playing Guild Wars 2 at the moment.\nYour stats may NOT be accurate."
WAITING_TIME = "Waiting time"
ACCOUNT_NAME = "Account Name"
SERVER = "Server"
TOTAL_PLAYED_TIME = "Total played time"
GAINED_GOLD = "Gained gold"
LOST_GOLD = "Lost gold"
TIMES_YOU_DIED = "Times you died"
GAINED_KARMA = "Gained karma"
LOST_KARMA = "Lost karma"
GAINED_LAURElS = "Gained laurels"
LOST_LAURElS = "Lost laurels"
GAINED_WVW_RANKS = "Gained wvw ranks"
YAKS_KILLED = "Yaks killed"
YAKS_SCORTED = "Yaks scorted"
PLAYERS_KILLED = "Players killed"
KEEPS_CAPTURED = "Keeps captured"
TOWERS_CAPTURED = "Towers captured"
CAMPS_CAPTURED = "Camps captured"
SMC_CAPTURED = "SMC captured"
GAINED_WVW_TICKETS = "Gained wvw tickets"
LOST_WVW_TICKETS = "Lost wvw tickets"
GAINED_PROOF_HEROICS = "Gained proof heroics"
LOST_PROOF_HEROICS = "Lost proof heroics"
GAINED_BADGES_HONOR = "Gained badges of honor"
LOST_BADGES_HONOR = "Lost badges of honor"
GAINED_GUILD_COMMENDATIONS = "Gained guild commendations"
LOST_GUILD_COMMENDATIONS = "Lost guild commendations"
SESSION_SAVE_ERROR = (
    "There was a problem trying to record your last finished session.\n"
    "Please, do not close discord when the game is running."
)
USER_NO_SESSION_FOUND = (
    "No records were found in your name.\n"
    "You are probably trying to execute this command without playing the game.\n"
    "Make sure your status is NOT set to invisible in discord.\n"
    "Make sure \"Display current running game as a status message\" is ON.\n"
    "Make sure to start discord on your Desktop FIRST before starting Guild Wars 2."
)
#################################
# GW2 WORLDS
#################################
NA_SERVERS_TITLE = "~~~~~ NA Servers ~~~~~"
EU_SERVERS_TITLE = "~~~~~ EU Servers ~~~~~"
#################################
# GW2 WVW
#################################
INVALID_WORLD_NAME = "Invalid world name"
MISSING_WORLD_NAME = "Missing World Name"
WORLD_COLOR_ERROR = "Could not resolve world's color"


def match_world_name_help(prefix: str) -> str:
    return f"Use `{prefix}gw2 match <world_name>`\nOr register an API key on your account.\n"


WVW_KDR_TITLE = "WvW Kills/Death Ratings"
NA_TIER_TITLE = "North America Tier"
EU_TIER_TITLE = "Europe Tier"
