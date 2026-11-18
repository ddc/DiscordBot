"""Guild Wars 2 message constants organized by domain."""


class Gw2:
    FULL_NAME = "Guild Wars 2"


class CommandError:
    SERVER_NOT_FOUND = "Guild Wars 2 server not found"
    SERVER_MORE_INFO = "For more info on gw2 server names"


class Api:
    INVALID_KEY = "This API Key is INVALID or no longer exists in gw2 api database"
    ERROR = "GW2 API ERROR"
    DOWN = "GW2 API is currently down. Try again later."
    NOT_FOUND = "GW2 API Not found."
    REQUEST_LIMIT_REACHED = "GW2 API Requests limit has been saturated. Try again later."
    ACCESS_DENIED = "Access denied with your GW2 API key."


class Utils:
    KEY_MESSAGE_REMOVED = "Your message with your API Key was removed for privacy."
    KEY_MESSAGE_REMOVED_DENIED = "Bot does not have permission to delete the message with your API key.\nMissing bot permission: `Manage Messages`"


class Key:
    NO_API_KEY = "You dont have an API key registered.\n"
    INVALID_KEY_HELP = "This API Key is INVALID or no longer exists in gw2 api database.\n"
    NO_ACCOUNT_PERMISSION = (
        "Your API key doesnt have permission to access your gw2 account.\nPlease add one key with account permission."
    )
    ALREADY_IN_USE = "That API key is already in use by someone else."
    REMOVED_SUCCESSFULLY = "Your GW2 API Key has been deleted successfully."

    @staticmethod
    def add_info_help(prefix: str) -> str:
        return f"To add or replace an API key send a DM with: `{prefix}gw2 key add <api_key>`\n"

    @staticmethod
    def more_info_help(prefix: str) -> str:
        return f"To get info about your api key: `{prefix}gw2 key info`"

    @staticmethod
    def replaced_successfully(old: str, new: str, server: str) -> str:
        return f"Your API key `{old}` was **replaced** with your new key: `{new}`\nServer: `{server}`\n"

    @staticmethod
    def added_successfully(key_name: str, server_name: str) -> str:
        return (
            "Your key was verified and was **added** to your discord account.\n"
            f"Key: `{key_name}`\nServer: `{server_name}`\n"
        )


class Config:
    TITLE = "Guild Wars 2 configurations for"
    USER_SESSION_TITLE = "GW2 Users Session"
    SESSION_ACTIVATED = "Last session `ACTIVATED`\nBot will now record Gw2 users last sessions."
    SESSION_DEACTIVATED = "Last session `DEACTIVATED`\nBot will `NOT` record Gw2 users last sessions."

    @staticmethod
    def more_info(prefix: str) -> str:
        return f"For more info: {prefix}help gw2 config"


class Daily:
    NO_OBJECTIVES = "No Wizard's Vault objectives found."
    META_PROGRESS = "Meta progress"
    CLAIMED = "claimed"

    @staticmethod
    def title(period: str) -> str:
        return f"Wizard's Vault {period.title()} Objectives"


class Misc:
    LONG_SEARCH = "Search too long"
    WIKI_SEARCH_RESULTS = "Wiki Search Results"
    NO_RESULTS = "No results!"
    CLICK_HERE = "Click here"
    CLICK_ON_LINK = "Click on link above for more info !!!"

    @staticmethod
    def wiki_search_title(count: int, keyword: str) -> str:
        return f"Displaying **{count}** closest titles that matches **{keyword}**"


class Session:
    TITLE = "GW2 Last Session"
    MISSING_PERMISSIONS_TITLE = "To use this command your API key needs to have the following permissions"
    ADD_RIGHT_API_KEY_PERMISSIONS = (
        "Please add another API key with permissions that are MISSING if you want to use this command."
    )
    BOT_STILL_UPDATING = "Bot still updating your stats!"
    END_PROCESSING = (
        "Your session is still being processed.\n"
        "The bot waits a few minutes after you stop playing to ensure accurate data from the GW2 API.\n"
        "Please try again shortly."
    )
    USER_STILL_PLAYING = "You are playing Guild Wars 2 at the moment.\nYour stats may NOT be accurate."
    WAITING_TIME = "Waiting time"
    ACCOUNT_NAME = "Account Name"
    SERVER = "Server"
    PLAY_TIME = "Play time"
    TIMES_YOU_DIED = "Times you died"
    WVW_RANKS = "WvW ranks"
    YAKS_KILLED = "Yaks killed"
    YAKS_ESCORTED = "Yaks escorted"
    PLAYERS_KILLED = "Players killed"
    KEEPS_CAPTURED = "Keeps captured"
    TOWERS_CAPTURED = "Towers captured"
    CAMPS_CAPTURED = "Camps captured"
    SMC_CAPTURED = "SMC captured"
    IN_PROGRESS = (
        "Your Guild Wars 2 session is still in progress.\nSession stats will be available after you stop playing."
    )
    SAVE_ERROR = (
        "There was a problem trying to record your last finished session.\n"
        "Please, do not close discord when the game is running."
    )
    API_DOWN_DM = (
        "The GW2 API was unreachable while recording your session.\n"
        "Your session data may be incomplete. Please try again later."
    )
    NO_SESSION_FOUND = (
        "No records were found in your name.\n"
        "You are probably trying to execute this command without playing the game.\n"
        "Make sure your status is NOT set to invisible in discord.\n"
        'Make sure "Display current running game as a status message" is ON.\n'
        "Make sure to start discord on your Desktop FIRST before starting Guild Wars 2."
    )

    @staticmethod
    def not_active(prefix: str) -> str:
        return f"Last session is not active on this server.\nTo activate use: `{prefix}gw2 config session on`"


class Worlds:
    NA_SERVERS_TITLE = "~~~~~ NA Servers ~~~~~"
    EU_SERVERS_TITLE = "~~~~~ EU Servers ~~~~~"


class Wvw:
    INVALID_WORLD_NAME = "Invalid world name"
    MISSING_WORLD_NAME = "Missing World Name"
    WORLD_COLOR_ERROR = "Could not resolve world's color"
    KDR_TITLE = "WvW Kills/Death Ratings"
    NA_TIER_TITLE = "North America Tier"
    EU_TIER_TITLE = "Europe Tier"

    @staticmethod
    def match_world_name_help(prefix: str) -> str:
        return f"Use `{prefix}gw2 wvw match <world_name>`\nOr register an API key on your account.\n"
