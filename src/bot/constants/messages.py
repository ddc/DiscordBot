"""Bot message constants organized by domain."""


class Bot:
    TOKEN_NOT_FOUND = "BOT_TOKEN variable not found"
    TERMINATED = "Bot has been terminated."
    STOPPED_CTRTC = "Bot stopped with Ctrl+C"
    FATAL_ERROR_MAIN = "Fatal error in main()"
    CRASHED = "Bot crashed"
    CLOSING = "Closing bot..."
    LOGIN_FAILED = "Bot login failed"
    INIT_PREFIX_FAILED = "Failed to get prefix from database, using default"
    LOAD_SETTINGS_FAILED = "Failed to load settings"
    LOAD_COGS_FAILED = "Failed to load cogs"
    LOADED_ALL_COGS_SUCCESS = "Successfully loaded all cogs"

    @staticmethod
    def online(bot_user) -> str:
        return f"====> {bot_user} IS ONLINE AND CONNECTED TO DISCORD <===="

    @staticmethod
    def starting(seconds: int) -> str:
        return f"Starting Bot in {seconds} secs"

    @staticmethod
    def disconnected(bot_user) -> str:
        return f"Bot {bot_user} disconnected from Discord"


class Admin:
    @staticmethod
    def announce_playing(game: str) -> str:
        return f"I'm now playing: {game}"

    @staticmethod
    def bg_task_warning(seconds: int) -> str:
        return f"Background task running to update bot activity is ON\nActivity will change after {seconds} secs."


class Config:
    JOIN = "Display a message when someone joins the server"
    LEAVE = "Display a message when a member leaves the server"
    SERVER = "Display a message when server gets updated"
    MEMBER = "Display a message when someone changes profile"
    BLOCK_INVIS_MEMBERS = "Block messages from invisible members"
    BOT_WORD_REACTIONS = "Bot word reactions"
    PFILTER_CHANNELS = "Channels with profanity filter activated"
    CHANNEL_ID_INSTEAD_NAME = "Chnanel id should be used instead of its name!!!"
    NOT_ACTIVATED_ERROR = "Profanity Filter could not be activated.\n"
    MISSING_REQUIRED_ARGUMENT = "Missing required argument!!!"
    CHANNEL_ID_NOT_FOUND = "Channel id not found"
    BOT_MISSING_MANAGE_MESSAGES = 'Bot does not have permission to "Manage Messages"'
    NO_CHANNELS_LISTED = "No channels listed"

    @staticmethod
    def pfilter(status: str, channel: str) -> str:
        return f"Profanity Filter `{status}`\nChannel: `{channel}`"


class CustomCommand:
    ALREADY_A_STANDARD_COMMAND = "is already a standard command"
    LENGTH_ERROR = "Command names cannot exceed 20 characters.\nPlease try again with another name."
    ADDED = "Custom command successfully added"
    EDITED = "Custom command successfully edited"
    REMOVED = "Custom command successfully removed"
    ALL_REMOVED = "All custom commands from this server were successfully removed."
    ALREADY_EXISTS = "Command already exists"
    NO_COMMANDS_FOUND = "There are no custom commands in this server."
    UNABLE_REMOVE = "Unable to remove!!!"
    COMMANDS_SERVER = "Custom commands in this server"
    GET_CONFIGS_ERROR = "Error getting server configs"


class CommandError:
    MISSING_REQUIRED_ARGUMENT_HELP = "Missing required argument!!!\nFor more info on this command"
    NOT_FOUND = "Command not found"
    ERROR = "Command ERROR"
    RAISED_EXCEPTION = "Command raised an exception"
    NOT_ADMIN = "You are not an Admin to use this command"
    OWNERS_ONLY = "Only bot owners can use this command"
    PREFIXES_CHOICE = "Prefixes can only be one of"
    MORE_INFO = "For more info"
    UNKNOWN_OPTION = "Unknown option"
    HELP_MORE_INFO = "For more info on this command"
    NO_OPTION_FOUND = "No option found"
    NO_PERMISSION = "Bot does not have permission to execute this command"
    INVALID_MESSAGE = "Invalid message."
    INTERNAL_ERROR = "There was an internal error with command"
    CONTACT_ADMIN = "Please contact the server administrator"
    DM_CANNOT_EXECUTE = "Cannot execute action on a DM channel"
    PRIVILEGE_LOW = "Your Privilege is too low."
    DIRECT_MESSAGES_DISABLED = (
        "Direct messages are disabled in your configuration.\n"
        "To receive messages from Bots, enable **Direct messages** "
        "under **Settings > Content & Social > Social permissions**."
    )


class GuildJoin:
    @staticmethod
    def bot_message(bot_name: str, prefix: str, games_included: str) -> str:
        return (
            f"Thanks for using *{bot_name}*\n"
            f"To learn more about this bot: `{prefix}about`\n"
            f"Games included so far: `{games_included}`\n\n"
            f"If you are an Admin and wish to list configurations: `{prefix}config list`\n"
            f"To get a list of commands: `{prefix}help`"
        )


class GuildUpdate:
    NEW_SERVER_SETTINGS = "New Server Settings"
    NEW_SERVER_ICON = "New Server Icon"
    NEW_SERVER_NAME = "New Server Name"
    PREVIOUS_NAME = "Previous Name"
    PREVIOUS_SERVER_OWNER = "Previous Server Owner"
    NEW_SERVER_OWNER = "New Server Owner"


class MemberJoin:
    JOINED_THE_SERVER = "Joined the Server"


class MemberRemove:
    LEFT_THE_SERVER = "Left the Server"


class MemberUpdate:
    PROFILE_CHANGES = "Profile Changes"
    PREVIOUS_NICKNAME = "Previous Nickname"
    NEW_NICKNAME = "New Nickname"
    PREVIOUS_ROLES = "Previous Roles"
    NEW_ROLES = "New Roles"


class Messages:
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

    @staticmethod
    def blocked_invis(guild_name: str) -> str:
        return (
            "You are Invisible (offline)\n"
            f'Server "{guild_name}" does not allow messages from invisible members.\n'
            "Please change your status if you want to send messages to this server."
        )


class UserUpdate:
    NEW_AVATAR = "New Avatar"
    NEW_NAME = "New Name"
    PREVIOUS_DISCRIMINATOR = "Previous Discriminator"
    NEW_DISCRIMINATOR = "New Discriminator"


class BotUtils:
    LOADING_EXTENSIONS = "Loading Bot Extensions..."
    LOADING_EXTENSION_FAILED = "ERROR: FAILED to load extension"
    DISABLED_DM = (
        "Direct messages are disabled in your configuration.\n"
        "To receive messages from Bots, enable **Direct messages** "
        "under **Settings > Content & Social > Social permissions**."
    )
    MESSAGE_REMOVED_FOR_PRIVACY = "Your message was removed for privacy."
    DELETE_MESSAGE_NO_PERMISSION = "Bot does not have permission to delete messages."
    SEND_MESSAGE_FAILED = "An error occurred while sending the response. Please try again later."


class DiceRolls:
    SIZE_NOT_VALID = "Thats not a valid dice size.\nPlease try again."
    MEMBER_HIGHEST_ROLL_ANNOUNCE = ":star2: This is now your highest roll :star2:"
    SERVER_HIGHEST_ROLL_ANNOUNCE = ":crown: This is now the server highest roll :crown:"
    MEMBER_SERVER_WINNER_ANNOUNCE = ":crown: You are the server winner with"
    MEMBER_HIGHEST_ROLL = "Your highest roll is now:"
    MEMBER_HAS_HIGHEST_ROLL = "has the server highest roll with"
    SIZE_HIGHER_ONE = "Dice size needs to be higher than 1"
    RESET_ALL = "Reset all rolls from this server"
    DELETED_ALL = "Rolls from all members in this server have been deleted."

    @staticmethod
    def no_size_rolls(dice_size) -> str:
        return f"There are no dice rolls of the size {dice_size} in this server."


class Misc:
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

    @staticmethod
    def dev_info(webpage_url: str, discordpy_url: str) -> str:
        return (
            f"Developed as an open source project and hosted on [GitHub]({webpage_url})\n"
            f"A python discord api wrapper: [discord.py]({discordpy_url})\n"
        )


class Owner:
    PREFIX_CHANGED = "Bot prefix has been changed to"
    DESCRIPTION_CHANGED = "Bot description changed to"


# ============================================================================
# Backward-compatible module-level aliases
# All existing code using `messages.FOO` continues to work unchanged.
# ============================================================================

# Bot
BOT_TOKEN_NOT_FOUND = Bot.TOKEN_NOT_FOUND
BOT_TERMINATED = Bot.TERMINATED
BOT_STOPPED_CTRTC = Bot.STOPPED_CTRTC
BOT_FATAL_ERROR_MAIN = Bot.FATAL_ERROR_MAIN
BOT_CRASHED = Bot.CRASHED
BOT_CLOSING = Bot.CLOSING
BOT_LOGIN_FAILED = Bot.LOGIN_FAILED
BOT_INIT_PREFIX_FAILED = Bot.INIT_PREFIX_FAILED
BOT_LOAD_SETTINGS_FAILED = Bot.LOAD_SETTINGS_FAILED
BOT_LOAD_COGS_FAILED = Bot.LOAD_COGS_FAILED
BOT_LOADED_ALL_COGS_SUCCESS = Bot.LOADED_ALL_COGS_SUCCESS
bot_online = Bot.online
bot_starting = Bot.starting
bot_disconnected = Bot.disconnected

# Admin
bot_announce_playing = Admin.announce_playing
bg_task_warning = Admin.bg_task_warning

# Config
CONFIG_JOIN = Config.JOIN
CONFIG_LEAVE = Config.LEAVE
CONFIG_SERVER = Config.SERVER
CONFIG_MEMBER = Config.MEMBER
CONFIG_BLOCK_INVIS_MEMBERS = Config.BLOCK_INVIS_MEMBERS
CONFIG_BOT_WORD_REACTIONS = Config.BOT_WORD_REACTIONS
CONFIG_PFILTER_CHANNELS = Config.PFILTER_CHANNELS
config_pfilter = Config.pfilter
CONFIG_CHANNEL_ID_INSTEAD_NAME = Config.CHANNEL_ID_INSTEAD_NAME
CONFIG_NOT_ACTIVATED_ERROR = Config.NOT_ACTIVATED_ERROR
MISING_REUIRED_ARGUMENT = Config.MISSING_REQUIRED_ARGUMENT
CHANNEL_ID_NOT_FOUND = Config.CHANNEL_ID_NOT_FOUND
BOT_MISSING_MANAGE_MESSAGES_PERMISSION = Config.BOT_MISSING_MANAGE_MESSAGES
NO_CHANNELS_LISTED = Config.NO_CHANNELS_LISTED

# Custom Command
ALREADY_A_STANDARD_COMMAND = CustomCommand.ALREADY_A_STANDARD_COMMAND
COMMAND_LENGHT_ERROR = CustomCommand.LENGTH_ERROR
CUSTOM_COMMAND_ADDED = CustomCommand.ADDED
CUSTOM_COMMAND_EDITED = CustomCommand.EDITED
CUSTOM_COMMAND_REMOVED = CustomCommand.REMOVED
CUSTOM_COMMAND_ALL_REMOVED = CustomCommand.ALL_REMOVED
COMMAND_ALREADY_EXISTS = CustomCommand.ALREADY_EXISTS
NO_CUSTOM_COMMANDS_FOUND = CustomCommand.NO_COMMANDS_FOUND
CUSTOM_COMMAND_UNABLE_REMOVE = CustomCommand.UNABLE_REMOVE
CUSTOM_COMMANDS_SERVER = CustomCommand.COMMANDS_SERVER
GET_CONFIGS_ERROR = CustomCommand.GET_CONFIGS_ERROR

# Command Error
MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE = CommandError.MISSING_REQUIRED_ARGUMENT_HELP
COMMAND_NOT_FOUND = CommandError.NOT_FOUND
COMMAND_ERROR = CommandError.ERROR
COMMAND_RAISED_EXCEPTION = CommandError.RAISED_EXCEPTION
NOT_ADMIN_USE_COMMAND = CommandError.NOT_ADMIN
BOT_OWNERS_ONLY_COMMAND = CommandError.OWNERS_ONLY
PREFIXES_CHOICE = CommandError.PREFIXES_CHOICE
MORE_INFO = CommandError.MORE_INFO
UNKNOWN_OPTION = CommandError.UNKNOWN_OPTION
HELP_COMMAND_MORE_INFO = CommandError.HELP_MORE_INFO
NO_OPTION_FOUND = CommandError.NO_OPTION_FOUND
NO_PERMISSION_EXECUTE_COMMAND = CommandError.NO_PERMISSION
INVALID_MESSAGE = CommandError.INVALID_MESSAGE
COMMAND_INTERNAL_ERROR = CommandError.INTERNAL_ERROR
CONTACT_ADMIN = CommandError.CONTACT_ADMIN
DM_CANNOT_EXECUTE_COMMAND = CommandError.DM_CANNOT_EXECUTE
PRIVILEGE_LOW = CommandError.PRIVILEGE_LOW
DIRECT_MESSAGES_DISABLED = CommandError.DIRECT_MESSAGES_DISABLED

# Guild Join
guild_join_bot_message = GuildJoin.bot_message

# Guild Update
NEW_SERVER_SETTINGS = GuildUpdate.NEW_SERVER_SETTINGS
NEW_SERVER_ICON = GuildUpdate.NEW_SERVER_ICON
NEW_SERVER_NAME = GuildUpdate.NEW_SERVER_NAME
PREVIOUS_NAME = GuildUpdate.PREVIOUS_NAME
PREVIOUS_SERVER_OWNER = GuildUpdate.PREVIOUS_SERVER_OWNER
NEW_SERVER_OWNER = GuildUpdate.NEW_SERVER_OWNER

# Member Join
JOINED_THE_SERVER = MemberJoin.JOINED_THE_SERVER

# Member Remove
LEFT_THE_SERVER = MemberRemove.LEFT_THE_SERVER

# Member Update
PROFILE_CHANGES = MemberUpdate.PROFILE_CHANGES
PREVIOUS_NICKNAME = MemberUpdate.PREVIOUS_NICKNAME
NEW_NICKNAME = MemberUpdate.NEW_NICKNAME
PREVIOUS_ROLES = MemberUpdate.PREVIOUS_ROLES
NEW_ROLES = MemberUpdate.NEW_ROLES

# Messages
BOT_REACT_EMOJIS = Messages.BOT_REACT_EMOJIS
OWNER_DM_BOT_MESSAGE = Messages.OWNER_DM_BOT_MESSAGE
NO_DM_MESSAGES = Messages.NO_DM_MESSAGES
DM_COMMAND_NOT_ALLOWED = Messages.DM_COMMAND_NOT_ALLOWED
DM_COMMANDS_ALLOW_LIST = Messages.DM_COMMANDS_ALLOW_LIST
BOT_REACT_STUPID = Messages.BOT_REACT_STUPID
BOT_REACT_RETARD = Messages.BOT_REACT_RETARD
MESSAGE_CENSURED = Messages.MESSAGE_CENSURED
PRIVATE_BOT_MESSAGE = Messages.PRIVATE_BOT_MESSAGE
blocked_invis_message = Messages.blocked_invis

# User Update
NEW_AVATAR = UserUpdate.NEW_AVATAR
NEW_NAME = UserUpdate.NEW_NAME
PREVIOUS_DISCRIMINATOR = UserUpdate.PREVIOUS_DISCRIMINATOR
NEW_DISCRIMINATOR = UserUpdate.NEW_DISCRIMINATOR

# Bot Utils
LOADING_EXTENSIONS = BotUtils.LOADING_EXTENSIONS
LOADING_EXTENSION_FAILED = BotUtils.LOADING_EXTENSION_FAILED
DISABLED_DM = BotUtils.DISABLED_DM
MESSAGE_REMOVED_FOR_PRIVACY = BotUtils.MESSAGE_REMOVED_FOR_PRIVACY
DELETE_MESSAGE_NO_PERMISSION = BotUtils.DELETE_MESSAGE_NO_PERMISSION
SEND_MESSAGE_FAILED = BotUtils.SEND_MESSAGE_FAILED

# Dice Rolls
DICE_SIZE_NOT_VALID = DiceRolls.SIZE_NOT_VALID
MEMBER_HIGHEST_ROLL_ANOUNCE = DiceRolls.MEMBER_HIGHEST_ROLL_ANNOUNCE
SERVER_HIGHEST_ROLL_ANOUNCE = DiceRolls.SERVER_HIGHEST_ROLL_ANNOUNCE
MEMBER_SERVER_WINNER_ANOUNCE = DiceRolls.MEMBER_SERVER_WINNER_ANNOUNCE
MEMBER_HIGHEST_ROLL = DiceRolls.MEMBER_HIGHEST_ROLL
MEMBER_HAS_HIGHEST_ROLL = DiceRolls.MEMBER_HAS_HIGHEST_ROLL
DICE_SIZE_HIGHER_ONE = DiceRolls.SIZE_HIGHER_ONE
RESET_ALL_ROLLS = DiceRolls.RESET_ALL
DELETED_ALL_ROLLS = DiceRolls.DELETED_ALL
no_dice_size_rolls = DiceRolls.no_size_rolls

# Misc
PEPE_DOWNLOAD_ERROR = Misc.PEPE_DOWNLOAD_ERROR
INVITE_TITLE = Misc.INVITE_TITLE
UNLIMITED_INVITES = Misc.UNLIMITED_INVITES
TEMPORARY_INVITES = Misc.TEMPORARY_INVITES
REVOKED_INVITES = Misc.REVOKED_INVITES
NO_INVITES = Misc.NO_INVITES
DO_NOT_DISTURB = Misc.DO_NOT_DISTURB
JOINED_DISCORD_ON = Misc.JOINED_DISCORD_ON
JOINED_THIS_SERVER_ON = Misc.JOINED_THIS_SERVER_ON
LIST_COMMAND_CATEGORIES = Misc.LIST_COMMAND_CATEGORIES
dev_info_msg = Misc.dev_info

# Owner
BOT_PREFIX_CHANGED = Owner.PREFIX_CHANGED
BOT_DESCRIPTION_CHANGED = Owner.DESCRIPTION_CHANGED
