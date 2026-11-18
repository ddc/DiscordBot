"""Bot message constants organized by domain."""


class Bot:
    MISSING_ENV_VAR = "BOT_TOKEN variable not found"
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

    @staticmethod
    def resumed(bot_user) -> str:
        return f"Bot {bot_user} resumed connection to Discord"


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
