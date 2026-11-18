"""Tests for bot message constants."""

from src.bot.constants.messages import (
    Admin,
    Bot,
    BotUtils,
    CommandError,
    Config,
    CustomCommand,
    DiceRolls,
    GuildJoin,
    GuildUpdate,
    MemberJoin,
    MemberRemove,
    MemberUpdate,
    Messages,
    Misc,
    Owner,
    UserUpdate,
)


class TestBotClass:
    """Test cases for Bot message class."""

    def test_token_not_found(self):
        assert Bot.MISSING_ENV_VAR == "BOT_TOKEN variable not found"

    def test_terminated(self):
        assert Bot.TERMINATED == "Bot has been terminated."

    def test_stopped_ctrtc(self):
        assert Bot.STOPPED_CTRTC == "Bot stopped with Ctrl+C"

    def test_fatal_error_main(self):
        assert Bot.FATAL_ERROR_MAIN == "Fatal error in main()"

    def test_crashed(self):
        assert Bot.CRASHED == "Bot crashed"

    def test_closing(self):
        assert Bot.CLOSING == "Closing bot..."

    def test_login_failed(self):
        assert Bot.LOGIN_FAILED == "Bot login failed"

    def test_init_prefix_failed(self):
        assert Bot.INIT_PREFIX_FAILED == "Failed to get prefix from database, using default"

    def test_load_settings_failed(self):
        assert Bot.LOAD_SETTINGS_FAILED == "Failed to load settings"

    def test_load_cogs_failed(self):
        assert Bot.LOAD_COGS_FAILED == "Failed to load cogs"

    def test_loaded_all_cogs_success(self):
        assert Bot.LOADED_ALL_COGS_SUCCESS == "Successfully loaded all cogs"

    def test_online(self):
        result = Bot.online("TestBot#1234")
        assert "TestBot#1234" in result
        assert "ONLINE" in result
        assert "CONNECTED TO DISCORD" in result

    def test_starting(self):
        result = Bot.starting(5)
        assert "5" in result
        assert "secs" in result

    def test_disconnected(self):
        result = Bot.disconnected("TestBot#1234")
        assert "TestBot#1234" in result
        assert "disconnected" in result


class TestAdminClass:
    """Test cases for Admin message class."""

    def test_announce_playing(self):
        result = Admin.announce_playing("Test Game")
        assert "Test Game" in result
        assert "playing" in result

    def test_bg_task_warning(self):
        result = Admin.bg_task_warning(300)
        assert "300" in result
        assert "Background task" in result


class TestConfigClass:
    """Test cases for Config message class."""

    def test_join(self):
        assert "joins" in Config.JOIN

    def test_leave(self):
        assert "leaves" in Config.LEAVE

    def test_server(self):
        assert "updated" in Config.SERVER

    def test_member(self):
        assert "profile" in Config.MEMBER

    def test_block_invis_members(self):
        assert "invisible" in Config.BLOCK_INVIS_MEMBERS.lower()

    def test_bot_word_reactions(self):
        assert "reactions" in Config.BOT_WORD_REACTIONS.lower()

    def test_pfilter_channels(self):
        assert "profanity" in Config.PFILTER_CHANNELS.lower()

    def test_pfilter_function(self):
        result = Config.pfilter("ON", "#general")
        assert "ON" in result
        assert "#general" in result
        assert "Profanity Filter" in result

    def test_channel_id_instead_name(self):
        assert isinstance(Config.CHANNEL_ID_INSTEAD_NAME, str)

    def test_not_activated_error(self):
        assert "Profanity Filter" in Config.NOT_ACTIVATED_ERROR

    def test_missing_required_argument(self):
        assert "Missing" in Config.MISSING_REQUIRED_ARGUMENT

    def test_channel_id_not_found(self):
        assert "not found" in Config.CHANNEL_ID_NOT_FOUND

    def test_bot_missing_manage_messages(self):
        assert "permission" in Config.BOT_MISSING_MANAGE_MESSAGES.lower()

    def test_no_channels_listed(self):
        assert "No channels" in Config.NO_CHANNELS_LISTED


class TestCustomCommandClass:
    """Test cases for CustomCommand message class."""

    def test_already_standard_command(self):
        assert "standard command" in CustomCommand.ALREADY_A_STANDARD_COMMAND

    def test_length_error(self):
        assert "20 characters" in CustomCommand.LENGTH_ERROR

    def test_added(self):
        assert "added" in CustomCommand.ADDED

    def test_edited(self):
        assert "edited" in CustomCommand.EDITED

    def test_removed(self):
        assert "removed" in CustomCommand.REMOVED

    def test_all_removed(self):
        assert "removed" in CustomCommand.ALL_REMOVED

    def test_already_exists(self):
        assert "exists" in CustomCommand.ALREADY_EXISTS

    def test_no_commands_found(self):
        assert "no custom commands" in CustomCommand.NO_COMMANDS_FOUND.lower()

    def test_unable_remove(self):
        assert "Unable" in CustomCommand.UNABLE_REMOVE

    def test_commands_server(self):
        assert "Custom commands" in CustomCommand.COMMANDS_SERVER

    def test_get_configs_error(self):
        assert "Error" in CustomCommand.GET_CONFIGS_ERROR


class TestCommandErrorClass:
    """Test cases for CommandError message class."""

    def test_missing_required_argument_help(self):
        assert "Missing required argument" in CommandError.MISSING_REQUIRED_ARGUMENT_HELP

    def test_not_found(self):
        assert CommandError.NOT_FOUND == "Command not found"

    def test_error(self):
        assert CommandError.ERROR == "Command ERROR"

    def test_raised_exception(self):
        assert "exception" in CommandError.RAISED_EXCEPTION.lower()

    def test_not_admin(self):
        assert "Admin" in CommandError.NOT_ADMIN

    def test_owners_only(self):
        assert "owners" in CommandError.OWNERS_ONLY.lower()

    def test_prefixes_choice(self):
        assert "Prefixes" in CommandError.PREFIXES_CHOICE

    def test_more_info(self):
        assert CommandError.MORE_INFO == "For more info"

    def test_unknown_option(self):
        assert CommandError.UNKNOWN_OPTION == "Unknown option"

    def test_help_more_info(self):
        assert "more info" in CommandError.HELP_MORE_INFO.lower()

    def test_no_option_found(self):
        assert CommandError.NO_OPTION_FOUND == "No option found"

    def test_no_permission(self):
        assert "permission" in CommandError.NO_PERMISSION.lower()

    def test_invalid_message(self):
        assert CommandError.INVALID_MESSAGE == "Invalid message."

    def test_internal_error(self):
        assert "internal error" in CommandError.INTERNAL_ERROR.lower()

    def test_dm_cannot_execute(self):
        assert "DM" in CommandError.DM_CANNOT_EXECUTE

    def test_privilege_low(self):
        assert "Privilege" in CommandError.PRIVILEGE_LOW

    def test_direct_messages_disabled(self):
        assert "Direct messages" in CommandError.DIRECT_MESSAGES_DISABLED


class TestGuildJoinClass:
    """Test cases for GuildJoin message class."""

    def test_bot_message(self):
        result = GuildJoin.bot_message("MyBot", "!", "GW2")
        assert "MyBot" in result
        assert "!" in result
        assert "GW2" in result
        assert "help" in result


class TestGuildUpdateClass:
    """Test cases for GuildUpdate message class."""

    def test_new_server_settings(self):
        assert GuildUpdate.NEW_SERVER_SETTINGS == "New Server Settings"

    def test_new_server_icon(self):
        assert GuildUpdate.NEW_SERVER_ICON == "New Server Icon"

    def test_new_server_name(self):
        assert GuildUpdate.NEW_SERVER_NAME == "New Server Name"

    def test_previous_name(self):
        assert GuildUpdate.PREVIOUS_NAME == "Previous Name"

    def test_previous_server_owner(self):
        assert GuildUpdate.PREVIOUS_SERVER_OWNER == "Previous Server Owner"

    def test_new_server_owner(self):
        assert GuildUpdate.NEW_SERVER_OWNER == "New Server Owner"


class TestMemberJoinClass:
    """Test cases for MemberJoin message class."""

    def test_joined_the_server(self):
        assert MemberJoin.JOINED_THE_SERVER == "Joined the Server"


class TestMemberRemoveClass:
    """Test cases for MemberRemove message class."""

    def test_left_the_server(self):
        assert MemberRemove.LEFT_THE_SERVER == "Left the Server"


class TestMemberUpdateClass:
    """Test cases for MemberUpdate message class."""

    def test_profile_changes(self):
        assert MemberUpdate.PROFILE_CHANGES == "Profile Changes"

    def test_previous_nickname(self):
        assert MemberUpdate.PREVIOUS_NICKNAME == "Previous Nickname"

    def test_new_nickname(self):
        assert MemberUpdate.NEW_NICKNAME == "New Nickname"

    def test_previous_roles(self):
        assert MemberUpdate.PREVIOUS_ROLES == "Previous Roles"

    def test_new_roles(self):
        assert MemberUpdate.NEW_ROLES == "New Roles"


class TestMessagesClass:
    """Test cases for Messages (on_message events) class."""

    def test_bot_react_emojis(self):
        assert ":rage:" in Messages.BOT_REACT_EMOJIS

    def test_owner_dm_bot_message(self):
        assert "master" in Messages.OWNER_DM_BOT_MESSAGE.lower()

    def test_no_dm_messages(self):
        assert "direct messages" in Messages.NO_DM_MESSAGES.lower()

    def test_dm_command_not_allowed(self):
        assert "not allowed" in Messages.DM_COMMAND_NOT_ALLOWED.lower()

    def test_dm_commands_allow_list(self):
        assert "allowed" in Messages.DM_COMMANDS_ALLOW_LIST.lower()

    def test_message_censured(self):
        assert "censored" in Messages.MESSAGE_CENSURED.lower()

    def test_private_bot_message(self):
        assert "Private Bot" in Messages.PRIVATE_BOT_MESSAGE

    def test_blocked_invis(self):
        result = Messages.blocked_invis("Test Server")
        assert "Test Server" in result
        assert "Invisible" in result


class TestUserUpdateClass:
    """Test cases for UserUpdate message class."""

    def test_new_avatar(self):
        assert UserUpdate.NEW_AVATAR == "New Avatar"

    def test_new_name(self):
        assert UserUpdate.NEW_NAME == "New Name"

    def test_previous_discriminator(self):
        assert UserUpdate.PREVIOUS_DISCRIMINATOR == "Previous Discriminator"

    def test_new_discriminator(self):
        assert UserUpdate.NEW_DISCRIMINATOR == "New Discriminator"


class TestBotUtilsClass:
    """Test cases for BotUtils message class."""

    def test_loading_extensions(self):
        assert "Loading" in BotUtils.LOADING_EXTENSIONS

    def test_loading_extension_failed(self):
        assert "FAILED" in BotUtils.LOADING_EXTENSION_FAILED

    def test_disabled_dm(self):
        assert "Direct messages" in BotUtils.DISABLED_DM

    def test_message_removed_for_privacy(self):
        assert "privacy" in BotUtils.MESSAGE_REMOVED_FOR_PRIVACY.lower()

    def test_delete_message_no_permission(self):
        assert "permission" in BotUtils.DELETE_MESSAGE_NO_PERMISSION.lower()


class TestDiceRollsClass:
    """Test cases for DiceRolls message class."""

    def test_size_not_valid(self):
        assert "valid" in DiceRolls.SIZE_NOT_VALID.lower()

    def test_member_highest_roll_announce(self):
        assert "highest roll" in DiceRolls.MEMBER_HIGHEST_ROLL_ANNOUNCE.lower()

    def test_server_highest_roll_announce(self):
        assert "server highest" in DiceRolls.SERVER_HIGHEST_ROLL_ANNOUNCE.lower()

    def test_member_server_winner_announce(self):
        assert "winner" in DiceRolls.MEMBER_SERVER_WINNER_ANNOUNCE.lower()

    def test_member_highest_roll(self):
        assert "highest roll" in DiceRolls.MEMBER_HIGHEST_ROLL.lower()

    def test_member_has_highest_roll(self):
        assert "highest roll" in DiceRolls.MEMBER_HAS_HIGHEST_ROLL.lower()

    def test_size_higher_one(self):
        assert "higher than 1" in DiceRolls.SIZE_HIGHER_ONE

    def test_reset_all(self):
        assert "Reset" in DiceRolls.RESET_ALL

    def test_deleted_all(self):
        assert "deleted" in DiceRolls.DELETED_ALL.lower()

    def test_no_size_rolls(self):
        result = DiceRolls.no_size_rolls(20)
        assert "20" in result
        assert "no dice rolls" in result.lower()


class TestMiscClass:
    """Test cases for Misc message class."""

    def test_pepe_download_error(self):
        assert "pepe" in Misc.PEPE_DOWNLOAD_ERROR.lower()

    def test_invite_title(self):
        assert Misc.INVITE_TITLE == "Invite Links"

    def test_unlimited_invites(self):
        assert Misc.UNLIMITED_INVITES == "Unlimited Invites"

    def test_temporary_invites(self):
        assert Misc.TEMPORARY_INVITES == "Temporary Invites"

    def test_revoked_invites(self):
        assert Misc.REVOKED_INVITES == "Revoked Invites"

    def test_no_invites(self):
        assert "No current invites" in Misc.NO_INVITES

    def test_do_not_disturb(self):
        assert Misc.DO_NOT_DISTURB == "Do Not Disturb"

    def test_joined_discord_on(self):
        assert Misc.JOINED_DISCORD_ON == "Joined Discord on"

    def test_joined_this_server_on(self):
        assert Misc.JOINED_THIS_SERVER_ON == "Joined this server on"

    def test_list_command_categories(self):
        assert "categories" in Misc.LIST_COMMAND_CATEGORIES.lower()

    def test_dev_info(self):
        result = Misc.dev_info("https://github.com/test", "https://discordpy.readthedocs.io")
        assert "https://github.com/test" in result
        assert "https://discordpy.readthedocs.io" in result
        assert "discord.py" in result


class TestOwnerClass:
    """Test cases for Owner message class."""

    def test_prefix_changed(self):
        assert "prefix" in Owner.PREFIX_CHANGED.lower()

    def test_description_changed(self):
        assert "description" in Owner.DESCRIPTION_CHANGED.lower()
