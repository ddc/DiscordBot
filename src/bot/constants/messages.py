#################################
# BOT
#################################
BOT_TOKEN_NOT_FOUND = "BOT_TOKEN variable not found"
BOT_TERMINATED = "Bot has been terminated."
BOT_STOPPED_CTRTC = "Bot stopped with Ctrl+C"
BOT_FATAL_ERROR_MAIN = "Fatal error in main()"
BOT_CRASHED = "Bot crashed"
BOT_CLOSING = "Closing bot..."
BOT_LOGIN_FAILED = "Bot login failed"
BOT_INIT_PREFIX_FAILED = "Failed to get prefix from database, using default"
BOT_LOAD_SETTINGS_FAILED = "Failed to load settings"
BOT_LOAD_COGS_FAILED = "Failed to load cogs"
BOT_LOADED_ALL_COGS_SUCCESS = "Successfully loaded all cogs"


def bot_online(bot_user) -> str:
    return f"====> {bot_user} IS ONLINE AND CONNECTED TO DISCORD <===="


def bot_starting(seconds: int) -> str:
    return f"Starting Bot in {seconds} secs"


def bot_disconnected(bot_user) -> str:
    return f"Bot {bot_user} disconnected from Discord"


#################################
# EVENT ADMIN
#################################


def bot_announce_playing(game: str) -> str:
    return f"I'm now playing: {game}"


def bg_task_warning(seconds: int) -> str:
    return f"Background task running to update bot activity is ON\nActivity will change after {seconds} secs."


#################################
# EVENT CONFIG
#################################
CONFIG_JOIN = "Display a message when someone joins the server"
CONFIG_LEAVE = "Display a message when a member leaves the server"
CONFIG_SERVER = "Display a message when server gets updated"
CONFIG_MEMBER = "Display a message when someone changes profile"
CONFIG_BLOCK_INVIS_MEMBERS = "Block messages from invisible members"
CONFIG_BOT_WORD_REACTIONS = "Bot word reactions"
CONFIG_PFILTER_CHANNELS = "Channels with profanity filter activated"


def config_pfilter(status: str, channel: str) -> str:
    return f"Profanity Filter `{status}`\nChannel: `{channel}`"


CONFIG_CHANNEL_ID_INSTEAD_NAME = "Chnanel id should be used instead of its name!!!"
CONFIG_NOT_ACTIVATED_ERROR = "Profanity Filter could not be activated.\n"
MISING_REUIRED_ARGUMENT = "Missing required argument!!!"
CHANNEL_ID_NOT_FOUND = "Channel id not found"
BOT_MISSING_MANAGE_MESSAGES_PERMISSION = "Bot does not have permission to \"Manage Messages\""
NO_CHANNELS_LISTED = "No channels listed"
#################################
# EVENT CUSTOM COMMAND
#################################
ALREADY_A_STANDARD_COMMAND = "is already a standard command"
COMMAND_LENGHT_ERROR = "Command names cannot exceed 20 characters.\nPlease try again with another name."
CUSTOM_COMMAND_ADDED = "Custom command successfully added"
CUSTOM_COMMAND_EDITED = "Custom command successfully edited"
CUSTOM_COMMAND_REMOVED = "Custom command successfully removed"
CUSTOM_COMMAND_ALL_REMOVED = "All custom commands from this server were successfully removed."
COMMAND_ALREADY_EXISTS = "Command already exists"
NO_CUSTOM_COMMANDS_FOUND = "There are no custom commands in this server."
CUSTOM_COMMAND_UNABLE_REMOVE = "Unable to remove!!!"
CUSTOM_COMMANDS_SERVER = "Custom commands in this server"
GET_CONFIGS_ERROR = "Error getting server configs"
#################################
# EVENT ON COMMAND ERROR
#################################
MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE = "Missing required argument!!!\nFor more info on this command"
COMMAND_NOT_FOUND = "Command not found"
COMMAND_ERROR = "Command ERROR"
COMMAND_RAISED_EXCEPTION = "Command raised an exception"
NOT_ADMIN_USE_COMMAND = "You are not an Admin to use this command"
BOT_OWNERS_ONLY_COMMAND = "Only bot owners can use this command"
PREFIXES_CHOICE = "Prefixes can only be one of"
MORE_INFO = "For more info"
UNKNOWN_OPTION = "Unknown option"
HELP_COMMAND_MORE_INFO = "For more info on this command"
NO_OPTION_FOUND = "No option found"
NO_PERMISSION_EXECUTE_COMMAND = "Bot does not have permission to execute this command"
INVALID_MESSAGE = "Invalid message."
COMMAND_INTERNAL_ERROR = "There was an internal error with command"
DM_CANNOT_EXECUTE_COMMAND = "Cannot execute action on a DM channel"
PRIVILEGE_LOW = "Your Privilege is too low."
DIRECT_MESSAGES_DISABLED = (
    "Direct messages are disable in your configuration.\n"
    "If you want to receive messages from Bots, "
    "you need to enable this option under Privacy & Safety:"
    "\"Allow direct messages from server members.\""
)
#################################
# EVENT ON GUILD JOIN
#################################


def guild_join_bot_message(bot_name: str, prefix: str, games_included: str) -> str:
    return (
        f"Thanks for using *{bot_name}*\n"
        f"To learn more about this bot: `{prefix}about`\n"
        f"Games included so far: `{games_included}`\n\n"
        f"If you are an Admin and wish to list configurations: `{prefix}config list`\n"
        f"To get a list of commands: `{prefix}help`"
    )


#################################
# EVENT ON GUILD UPDATE
#################################
NEW_SERVER_SETTINGS = "New Server Settings"
NEW_SERVER_ICON = "New Server Icon"
NEW_SERVER_NAME = "New Server Name"
PREVIOUS_NAME = "Previous Name"
PREVIOUS_SERVER_OWNER = "Previous Server Owner"
NEW_SERVER_OWNER = "New Server Owner"
#################################
# EVENT ON MEMBER JOIN
#################################
JOINED_THE_SERVER = "Joined the Server"
#################################
# EVENT ON MEMBER REMOVE
#################################
LEFT_THE_SERVER = "Left the Server"
#################################
# EVENT ON MEMBER UPDATE
#################################
PROFILE_CHANGES = "Profile Changes"
PREVIOUS_NICKNAME = "Previous Nickname"
NEW_NICKNAME = "New Nickname"
PREVIOUS_ROLES = "Previous Roles"
NEW_ROLES = "New Roles"
#################################
# EVENT ON MESSAGES
#################################
BOT_REACT_EMOJIS = ":rage: :middle_finger:"
OWNER_DM_BOT_MESSAGE = "Hello master.\nWhat can i do for you?"
NO_DM_MESSAGES = "Hello, I don't accept direct messages."
DM_COMMAND_NOT_ALLOWED = "Commands are not allowed in direct messages."
DM_COMMANDS_ALLOW_LIST = "Commands allowed in direct messages"
BOT_REACT_STUPID = "I'm not stupid, fu ufk!!!"
BOT_REACT_RETARD = "I'm not retard, fu ufk!!!"
MESSAGE_CENSURED = "Your message was censored.\nPlease don't say offensive words in this channel."
PRIVATE_BOT_MESSAGE = (
    "This is a Private Bot.\n"
    "You are not allowed to execute any commands.\n"
    "Only a few users are allowed to use it.\n"
    "Please don't insist. Thank You!!!"
)


def blocked_invis_message(guild_name: str) -> str:
    return (
        "You are Invisible (offline)\n"
        f"Server \"{guild_name}\" does not allow messages from invisible members.\n"
        "Please change your status if you want to send messages to this server."
    )


#################################
# EVENT ON USER UPDATE
#################################
NEW_AVATAR = "New Avatar"
NEW_NAME = "New Name"
PREVIOUS_DISCRIMINATOR = "Previous Discriminator"
NEW_DISCRIMINATOR = "New Discriminator"
#################################
# BOT UTILS
#################################
LOADING_EXTENSIONS = "Loading Bot Extensions..."
LOADING_EXTENSION_FAILED = "ERROR: FAILED to load extension"
DISABLED_DM = (
    "Direct messages are disable in your configuration.\n"
    "If you want to receive messages from Bots, "
    "you need to enable this option under Privacy & Safety:\n"
    "\"Allow direct messages from server members.\"\n"
)
MESSAGE_REMOVED_FOR_PRIVACY = "Your message was removed for privacy."
DELETE_MESSAGE_NO_PERMISSION = "Bot does not have permission to delete messages."
#################################
# DICE ROLLS
#################################
DICE_SIZE_NOT_VALID = "Thats not a valid dice size.\nPlease try again."
MEMBER_HIGHEST_ROLL_ANOUNCE = ":star2: This is now your highest roll :star2:"
SERVER_HIGHEST_ROLL_ANOUNCE = ":crown: This is now the server highest roll :crown:"
MEMBER_SERVER_WINNER_ANOUNCE = ":crown: You are the server winner with"
MEMBER_HIGHEST_ROLL = "Your highest roll is now:"
MEMBER_HAS_HIGHEST_ROLL = "has the server highest roll with"
DICE_SIZE_HIGHER_ONE = "Dice size needs to be higher than 1"
RESET_ALL_ROLLS = "Reset all rolls from this server"
DELETED_ALL_ROLLS = "Rolls from all members in this server have been deleted."


def no_dice_size_rolls(dice_size) -> str:
    return f"There are no dice rolls of the size {dice_size} in this server."


#################################
# MISC
#################################
PEPE_DOWNLOAD_ERROR = "Could not download pepe file..."
INVITE_TITLE = "Invite Links"
UNLIMITED_INVITES = "Unlimited Invites"
TEMPORARY_INVITES = "Temporary Invites"
REVOKED_INVITES = "Revoked Invites"
NO_INVITES = "No current invites on any channel."
DO_NOT_DISTURB = "Do Not Disturb"
JOINED_DISCORD_ON = "Joined Discord on"
JOINED_THIS_SERVER_ON = "Joined this server on"
LIST_COMMAND_CATEGORIES = "For a list of command categories"


def dev_info_msg(webpage_url: str, discordpy_url: str) -> str:
    return (
        f"Developed as an open source project and hosted on [GitHub]({webpage_url})\n"
        f"A python discord api wrapper: [discord.py]({discordpy_url})\n"
    )


#################################
# OWNER
#################################
BOT_PREFIX_CHANGED = "Bot prefix has been changed to"
BOT_DESCRIPTION_CHANGED = "Bot description changed to"
