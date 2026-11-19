"""Comprehensive tests for the Config cog."""

import discord
import pytest
import sys
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules["ddcDatabases"] = Mock()

from src.bot.cogs.admin.config import Config, _get_switch_status
from src.bot.constants import messages
lazy from src.bot.cogs.admin.admin import Admin
lazy from src.bot.cogs.admin.config import (
    config,
    config_block_invis_members,
    config_bot_word_reactions,
    config_join_message,
    config_leave_message,
    config_list,
    config_member_message,
    config_pfilter,
    config_server_message,
    setup,
)


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.db_session = MagicMock()
    bot.log = MagicMock()
    bot.user = MagicMock()
    bot.command_prefix = ("!",)
    bot.remove_command = MagicMock(return_value=None)
    bot.add_cog = AsyncMock(return_value=None)
    return bot


@pytest.fixture
def config_cog(mock_bot):
    """Create a Config cog instance."""
    return Config(mock_bot)


@pytest.fixture
def mock_ctx():
    """Create a mock context."""
    ctx = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    ctx.guild.name = "Test Server"
    ctx.guild.icon = MagicMock()
    ctx.guild.icon.url = "https://example.com/icon.png"
    ctx.guild.text_channels = []
    ctx.guild.me = MagicMock()
    ctx.guild.me.guild_permissions = MagicMock()
    ctx.guild.me.guild_permissions.administrator = True
    ctx.guild.me.guild_permissions.manage_messages = True
    ctx.guild.get_channel = MagicMock()

    author = MagicMock()
    author.id = 67890
    author.display_name = "TestUser"
    author.send = AsyncMock()
    author.avatar = MagicMock()
    author.avatar.url = "https://example.com/avatar.png"

    ctx.author = author
    ctx.message = MagicMock()
    ctx.message.channel = AsyncMock()
    ctx.send = AsyncMock()
    ctx.prefix = "!"

    return ctx


@pytest.fixture
def mock_text_channel():
    """Create a mock text channel."""
    channel = MagicMock()
    channel.id = 98765
    channel.name = "test-channel"
    return channel


class TestConfig:
    """Test cases for Config cog."""

    def test_init(self, mock_bot):
        """Test Config cog initialization."""
        cog = Config(mock_bot)
        assert cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.bot_utils.invoke_subcommand")
    async def test_config_group_command(self, mock_invoke, config_cog, mock_ctx):
        """Test config group command."""
        mock_invoke.return_value = "mock_command"

        result = await config(mock_ctx)

        mock_invoke.assert_called_once_with(mock_ctx, "admin config")
        assert result == "mock_command"

    def test_get_switch_status_on_lowercase(self):
        """Test _get_switch_status with 'on' input."""
        status, color = _get_switch_status("on")
        assert status is True
        assert color == discord.Color.green()

    def test_get_switch_status_on_uppercase(self):
        """Test _get_switch_status with 'ON' input."""
        status, color = _get_switch_status("ON")
        assert status is True
        assert color == discord.Color.green()

    def test_get_switch_status_off_lowercase(self):
        """Test _get_switch_status with 'off' input."""
        status, color = _get_switch_status("off")
        assert status is False
        assert color == discord.Color.red()

    def test_get_switch_status_off_uppercase(self):
        """Test _get_switch_status with 'OFF' input."""
        status, color = _get_switch_status("OFF")
        assert status is False
        assert color == discord.Color.red()

    def test_get_switch_status_invalid(self):
        """Test _get_switch_status with invalid input."""
        with pytest.raises(commands.BadArgument):
            _get_switch_status("invalid")

    def test_get_switch_status_mixed_case(self):
        """Test _get_switch_status with mixed case input."""
        status, color = _get_switch_status("On")
        assert status is True
        assert color == discord.Color.green()

        status, color = _get_switch_status("Off")
        assert status is False
        assert color == discord.Color.red()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_join_message_on(self, mock_send_embed, mock_dal_class, config_cog, mock_ctx):
        """Test enabling join messages."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_join_message(mock_ctx, status="on")

        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.update_msg_on_join.assert_called_once_with(12345, True, 67890)
        mock_send_embed.assert_called_once()

        embed = mock_send_embed.call_args[0][1]
        assert embed.color == discord.Color.green()
        assert "ON" in embed.description

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_join_message_off(self, mock_send_embed, mock_dal_class, config_cog, mock_ctx):
        """Test disabling join messages."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_join_message(mock_ctx, status="off")

        mock_dal.update_msg_on_join.assert_called_once_with(12345, False, 67890)

        embed = mock_send_embed.call_args[0][1]
        assert embed.color == discord.Color.red()
        assert "OFF" in embed.description

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_leave_message_on(self, mock_send_embed, mock_dal_class, config_cog, mock_ctx):
        """Test enabling leave messages."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_leave_message(mock_ctx, status="on")

        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.update_msg_on_leave.assert_called_once_with(12345, True, 67890)
        mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_server_message_on(self, mock_send_embed, mock_dal_class, config_cog, mock_ctx):
        """Test enabling server messages."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_server_message(mock_ctx, status="on")

        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.update_msg_on_server_update.assert_called_once_with(12345, True, 67890)
        mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_member_message_on(self, mock_send_embed, mock_dal_class, config_cog, mock_ctx):
        """Test enabling member messages."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_member_message(mock_ctx, status="on")

        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.update_msg_on_member_update.assert_called_once_with(12345, True, 67890)
        mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_block_invis_members_on(self, mock_send_embed, mock_dal_class, config_cog, mock_ctx):
        """Test enabling blocking invisible members."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_block_invis_members(mock_ctx, status="on")

        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.update_block_invis_members.assert_called_once_with(12345, True, 67890)
        mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_bot_word_reactions_on(self, mock_send_embed, mock_dal_class, config_cog, mock_ctx):
        """Test enabling bot word reactions."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_bot_word_reactions(mock_ctx, status="on")

        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.update_bot_word_reactions.assert_called_once_with(12345, True, 67890)
        mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_pfilter_on_success(
        self, mock_send_embed, mock_dal_class, config_cog, mock_ctx, mock_text_channel
    ):
        """Test enabling profanity filter successfully."""
        mock_ctx.guild.text_channels = [mock_text_channel]
        mock_ctx.guild.get_channel.return_value = mock_text_channel

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_pfilter(mock_ctx, subcommand_passed="on 98765")

        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.insert_profanity_filter_channel.assert_called_once_with(12345, 98765, "test-channel", 67890)
        mock_send_embed.assert_called_once()

        embed = mock_send_embed.call_args[0][1]
        assert embed.color == discord.Color.green()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_pfilter_off_success(
        self, mock_send_embed, mock_dal_class, config_cog, mock_ctx, mock_text_channel
    ):
        """Test disabling profanity filter successfully."""
        mock_ctx.guild.text_channels = [mock_text_channel]
        mock_ctx.guild.get_channel.return_value = mock_text_channel

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_pfilter(mock_ctx, subcommand_passed="off 98765")

        mock_dal.delete_profanity_filter_channel.assert_called_once_with(98765)

        embed = mock_send_embed.call_args[0][1]
        assert embed.color == discord.Color.red()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.bot_utils.send_error_msg", new_callable=AsyncMock)
    async def test_config_pfilter_missing_arguments(self, mock_send_error, config_cog, mock_ctx):
        """Test profanity filter with missing arguments."""

        await config_pfilter(mock_ctx, subcommand_passed="")

        mock_send_error.assert_called_once()
        error_msg = mock_send_error.call_args[0][1]
        assert messages.Config.MISSING_REQUIRED_ARGUMENT in error_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.bot_utils.send_error_msg", new_callable=AsyncMock)
    async def test_config_pfilter_invalid_channel_id(self, mock_send_error, config_cog, mock_ctx):
        """Test profanity filter with invalid channel ID."""

        await config_pfilter(mock_ctx, subcommand_passed="on invalid_id")

        mock_send_error.assert_called_once()
        error_msg = mock_send_error.call_args[0][1]
        assert messages.Config.CHANNEL_ID_NOT_FOUND in error_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.bot_utils.send_error_msg", new_callable=AsyncMock)
    async def test_config_pfilter_channel_not_found(self, mock_send_error, config_cog, mock_ctx):
        """Test profanity filter with non-existent channel."""
        mock_ctx.guild.text_channels = []
        mock_ctx.guild.get_channel.return_value = None

        await config_pfilter(mock_ctx, subcommand_passed="on 98765")

        mock_send_error.assert_called_once()
        error_msg = mock_send_error.call_args[0][1]
        assert messages.Config.CHANNEL_ID_NOT_FOUND in error_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.bot_utils.send_error_msg")
    async def test_config_pfilter_no_permissions(self, mock_send_error, config_cog, mock_ctx, mock_text_channel):
        """Test profanity filter without bot permissions."""
        mock_ctx.guild.text_channels = [mock_text_channel]
        mock_ctx.guild.get_channel.return_value = mock_text_channel
        mock_ctx.guild.me.guild_permissions.administrator = False
        mock_ctx.guild.me.guild_permissions.manage_messages = False

        await config_pfilter(mock_ctx, subcommand_passed="on 98765")

        mock_send_error.assert_called_once()
        error_msg = mock_send_error.call_args[0][1]
        assert messages.Config.NOT_ACTIVATED_ERROR in error_msg
        assert messages.Config.BOT_MISSING_MANAGE_MESSAGES in error_msg

    @pytest.mark.asyncio
    async def test_config_pfilter_invalid_status(self, config_cog, mock_ctx, mock_text_channel):
        """Test profanity filter with invalid status."""
        mock_ctx.guild.text_channels = [mock_text_channel]
        mock_ctx.guild.get_channel.return_value = mock_text_channel

        with pytest.raises(commands.BadArgument):
            from src.bot.cogs.admin.config import config_pfilter

            await config_pfilter(mock_ctx, subcommand_passed="invalid 98765")

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    @patch("src.bot.cogs.admin.config.chat_formatting.green_text")
    @patch("src.bot.cogs.admin.config.chat_formatting.red_text")
    async def test_config_list_success(
        self,
        mock_red_text,
        mock_green_text,
        mock_send_embed,
        mock_pf_dal_class,
        mock_servers_dal_class,
        config_cog,
        mock_ctx,
    ):
        """Test listing all configurations."""
        mock_servers_dal = AsyncMock()
        mock_servers_dal_class.return_value = mock_servers_dal
        mock_servers_dal.get_server.return_value = {
            "msg_on_join": True,
            "msg_on_leave": False,
            "msg_on_server_update": True,
            "msg_on_member_update": False,
            "block_invis_members": True,
            "bot_word_reactions": False,
        }

        mock_pf_dal = AsyncMock()
        mock_pf_dal_class.return_value = mock_pf_dal
        mock_pf_dal.get_all_server_profanity_filter_channels.return_value = [
            {"channel_name": "general"},
            {"channel_name": "random"},
        ]

        mock_green_text.return_value = "GREEN_ON"
        mock_red_text.return_value = "RED_OFF"

        await config_list(mock_ctx)

        mock_ctx.message.channel.typing.assert_called_once()
        mock_ctx.author.send.assert_called_once()
        mock_ctx.send.assert_called_once()

        dm_call_args = mock_ctx.author.send.call_args
        embed = dm_call_args[1]["embed"]
        assert embed.author.name == "Configurations for Test Server"
        assert len(embed.fields) == 7

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    async def test_config_list_no_profanity_channels(
        self, mock_pf_dal_class, mock_servers_dal_class, config_cog, mock_ctx
    ):
        """Test listing configurations with no profanity filter channels."""
        mock_servers_dal = AsyncMock()
        mock_servers_dal_class.return_value = mock_servers_dal
        mock_servers_dal.get_server.return_value = {
            "msg_on_join": False,
            "msg_on_leave": False,
            "msg_on_server_update": False,
            "msg_on_member_update": False,
            "block_invis_members": False,
            "bot_word_reactions": False,
        }

        mock_pf_dal = AsyncMock()
        mock_pf_dal_class.return_value = mock_pf_dal
        mock_pf_dal.get_all_server_profanity_filter_channels.return_value = []

        await config_list(mock_ctx)

        mock_ctx.author.send.assert_called_once()
        mock_ctx.send.assert_called_once()

        dm_call_args = mock_ctx.author.send.call_args
        embed = dm_call_args[1]["embed"]

        pf_field = next(field for field in embed.fields if "pfilter" in field.name.lower())
        assert messages.Config.NO_CHANNELS_LISTED in pf_field.value

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    async def test_config_list_no_guild_icon(self, mock_servers_dal_class, config_cog, mock_ctx):
        """Test listing configurations when guild has no icon."""
        mock_ctx.guild.icon = None

        mock_servers_dal = AsyncMock()
        mock_servers_dal_class.return_value = mock_servers_dal
        mock_servers_dal.get_server.return_value = {
            "msg_on_join": False,
            "msg_on_leave": False,
            "msg_on_server_update": False,
            "msg_on_member_update": False,
            "block_invis_members": False,
            "bot_word_reactions": False,
        }

        with patch("src.bot.cogs.admin.config.ProfanityFilterDal") as mock_pf_dal_class:
            mock_pf_dal = AsyncMock()
            mock_pf_dal_class.return_value = mock_pf_dal
            mock_pf_dal.get_all_server_profanity_filter_channels.return_value = []

            from src.bot.cogs.admin.config import config_list

            await config_list(mock_ctx)

            dm_call_args = mock_ctx.author.send.call_args
            embed = dm_call_args[1]["embed"]
            assert embed.author.icon_url is None
            assert embed.thumbnail.url is None

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""

        await setup(mock_bot)

        mock_bot.remove_command.assert_called_once_with("admin")
        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, Config)
        assert added_cog.bot == mock_bot

    def test_config_cog_inheritance(self, config_cog):
        """Test that Config cog properly inherits from Admin."""

        assert isinstance(config_cog, Admin)
        assert hasattr(config_cog, "bot")

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_error_msg")
    async def test_config_pfilter_channel_get_returns_none(
        self, mock_send_error, mock_dal_class, config_cog, mock_ctx, mock_text_channel
    ):
        """Test profanity filter when get_channel returns None."""
        mock_ctx.guild.text_channels = [mock_text_channel]
        mock_ctx.guild.get_channel.return_value = None

        await config_pfilter(mock_ctx, subcommand_passed="on 98765")

        mock_send_error.assert_called_once()
        error_msg = mock_send_error.call_args[0][1]
        assert messages.Config.CHANNEL_ID_NOT_FOUND in error_msg
        assert "98765" in error_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_pfilter_admin_permission_only(
        self, mock_send_embed, mock_dal_class, config_cog, mock_ctx, mock_text_channel
    ):
        """Test profanity filter with admin permission but no manage messages."""
        mock_ctx.guild.text_channels = [mock_text_channel]
        mock_ctx.guild.get_channel.return_value = mock_text_channel
        mock_ctx.guild.me.guild_permissions.administrator = True
        mock_ctx.guild.me.guild_permissions.manage_messages = False

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_pfilter(mock_ctx, subcommand_passed="on 98765")

        mock_dal.insert_profanity_filter_channel.assert_called_once()
        mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_config_pfilter_manage_messages_permission_only(
        self, mock_send_embed, mock_dal_class, config_cog, mock_ctx, mock_text_channel
    ):
        """Test profanity filter with manage messages permission but no admin."""
        mock_ctx.guild.text_channels = [mock_text_channel]
        mock_ctx.guild.get_channel.return_value = mock_text_channel
        mock_ctx.guild.me.guild_permissions.administrator = False
        mock_ctx.guild.me.guild_permissions.manage_messages = True

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        await config_pfilter(mock_ctx, subcommand_passed="on 98765")

        mock_dal.insert_profanity_filter_channel.assert_called_once()
        mock_send_embed.assert_called_once()
