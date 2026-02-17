"""Extra tests for the Config cog targeting uncovered lines.

Covers lines: 208, 405-466, 470-490, 496-559, 563, 573, 583, 593, 603, 613, 623-629.
"""

import discord
import pytest
import sys
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock, Mock, PropertyMock, patch

sys.modules["ddcDatabases"] = Mock()

from src.bot.cogs.admin.config import Config, ConfigView, _get_switch_status
from src.bot.constants import messages


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.db_session = MagicMock()
    bot.log = MagicMock()
    bot.log.info = MagicMock()
    bot.user = MagicMock()
    bot.command_prefix = ("!",)
    bot.remove_command = MagicMock(return_value=None)
    bot.add_cog = AsyncMock(return_value=None)
    bot.settings = {"bot": {"EmbedColor": 0x00FF00}}
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
    ctx.guild.id = 99999
    ctx.guild.name = "TestGuild"
    ctx.guild.icon = MagicMock()
    ctx.guild.icon.url = "https://example.com/icon.png"
    ctx.guild.me = MagicMock()
    ctx.guild.me.guild_permissions = MagicMock()
    ctx.guild.me.guild_permissions.administrator = True
    ctx.guild.me.guild_permissions.manage_messages = True
    ctx.guild.get_channel = MagicMock()
    ctx.guild.text_channels = []

    ctx.channel = MagicMock()
    ctx.channel.id = 11111
    ctx.channel.name = "test-channel"

    ctx.prefix = "!"

    ctx.author = MagicMock()
    ctx.author.id = 12345
    ctx.author.name = "TestUser"
    ctx.author.display_name = "TestUser"
    ctx.author.avatar = MagicMock()
    ctx.author.avatar.url = "https://example.com/avatar.png"
    ctx.author.send = AsyncMock()

    ctx.send = AsyncMock()
    ctx.message = MagicMock()
    ctx.message.channel = MagicMock()
    ctx.message.channel.typing = AsyncMock()
    ctx.message.author = ctx.author

    ctx.bot = mock_ctx_bot = MagicMock()
    ctx.bot.db_session = MagicMock()
    ctx.bot.log = MagicMock()
    ctx.bot.log.info = MagicMock()
    ctx.bot.settings = {"bot": {"EmbedColor": 0x00FF00}}

    return ctx


@pytest.fixture
def mock_text_channel():
    """Create a mock text channel."""
    channel = MagicMock()
    channel.id = 22222
    channel.name = "general"
    return channel


@pytest.fixture
def server_config():
    """Create a default server configuration dict."""
    return {
        "msg_on_join": True,
        "msg_on_leave": False,
        "msg_on_server_update": True,
        "msg_on_member_update": False,
        "block_invis_members": True,
        "bot_word_reactions": False,
    }


@pytest.fixture
def config_view(mock_ctx, server_config):
    """Create a ConfigView instance without requiring an event loop."""
    view = object.__new__(ConfigView)
    view.ctx = mock_ctx
    view.server_config = server_config
    view._updating = False
    view.message = None
    view._children = []
    view.__weights = {}
    # Create mock button attributes for restore_buttons
    view.toggle_join_messages = MagicMock()
    view.toggle_leave_messages = MagicMock()
    view.toggle_server_messages = MagicMock()
    view.toggle_member_messages = MagicMock()
    view.toggle_block_invisible = MagicMock()
    view.toggle_bot_reactions = MagicMock()
    return view


class TestConfigPfilterChannelResolution:
    """Tests for config_pfilter channel resolution (around line 208)."""

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_pfilter_no_channel_specified_uses_current(
        self, mock_send_embed, mock_dal_class, config_cog, mock_ctx
    ):
        """When no channel is specified, uses current channel (line 208)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        from src.bot.cogs.admin.config import config_pfilter

        await config_pfilter(mock_ctx, subcommand_passed="on")

        mock_dal.insert_profanity_filter_channel.assert_called_once_with(99999, 11111, "test-channel", 12345)
        mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_pfilter_channel_found_by_numeric_id(
        self, mock_send_embed, mock_dal_class, config_cog, mock_ctx, mock_text_channel
    ):
        """When channel is found by numeric ID (line 215)."""
        mock_ctx.guild.get_channel.return_value = mock_text_channel
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        from src.bot.cogs.admin.config import config_pfilter

        await config_pfilter(mock_ctx, subcommand_passed="on 22222")

        mock_ctx.guild.get_channel.assert_called_once_with(22222)
        mock_dal.insert_profanity_filter_channel.assert_called_once_with(99999, 22222, "general", 12345)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_pfilter_channel_found_by_name(
        self, mock_send_embed, mock_dal_class, config_cog, mock_ctx, mock_text_channel
    ):
        """When channel is found by name after ID lookup fails (line 219)."""
        mock_ctx.guild.get_channel.return_value = None  # ID lookup fails
        mock_ctx.guild.text_channels = [mock_text_channel]

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        with patch("src.bot.cogs.admin.config.discord.utils.get", return_value=mock_text_channel):
            from src.bot.cogs.admin.config import config_pfilter

            await config_pfilter(mock_ctx, subcommand_passed="on general")

        mock_dal.insert_profanity_filter_channel.assert_called_once_with(99999, 22222, "general", 12345)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.bot_utils.send_error_msg", new_callable=AsyncMock)
    async def test_pfilter_channel_not_found_by_id_or_name(self, mock_send_error, config_cog, mock_ctx):
        """When channel is not found by ID or name, sends error (lines 221-224)."""
        mock_ctx.guild.get_channel.return_value = None

        with patch("src.bot.cogs.admin.config.discord.utils.get", return_value=None):
            from src.bot.cogs.admin.config import config_pfilter

            await config_pfilter(mock_ctx, subcommand_passed="on nonexistent")

        mock_send_error.assert_called_once()
        error_msg = mock_send_error.call_args[0][1]
        assert messages.CHANNEL_ID_NOT_FOUND in error_msg
        assert "nonexistent" in error_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.bot_utils.send_error_msg", new_callable=AsyncMock)
    async def test_pfilter_on_no_bot_permissions(self, mock_send_error, config_cog, mock_ctx):
        """When 'on' status with insufficient bot permissions, sends error (lines 231-233)."""
        mock_ctx.guild.me.guild_permissions.administrator = False
        mock_ctx.guild.me.guild_permissions.manage_messages = False

        from src.bot.cogs.admin.config import config_pfilter

        await config_pfilter(mock_ctx, subcommand_passed="on")

        mock_send_error.assert_called_once()
        error_msg = mock_send_error.call_args[0][1]
        assert messages.CONFIG_NOT_ACTIVATED_ERROR in error_msg
        assert messages.BOT_MISSING_MANAGE_MESSAGES_PERMISSION in error_msg

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_pfilter_off_deletes(self, mock_send_embed, mock_dal_class, config_cog, mock_ctx):
        """When 'off' status, deletes channel filter (lines 240-243)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        from src.bot.cogs.admin.config import config_pfilter

        await config_pfilter(mock_ctx, subcommand_passed="off")

        mock_dal.delete_profanity_filter_channel.assert_called_once_with(11111)
        embed = mock_send_embed.call_args[0][1]
        assert embed.color == discord.Color.red()

    @pytest.mark.asyncio
    async def test_pfilter_invalid_status_raises(self, config_cog, mock_ctx):
        """When invalid status, raises BadArgument (lines 244-245)."""
        with pytest.raises(commands.BadArgument):
            from src.bot.cogs.admin.config import config_pfilter

            await config_pfilter(mock_ctx, subcommand_passed="maybe")

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_pfilter_on_uppercase(self, mock_send_embed, mock_dal_class, config_cog, mock_ctx):
        """When 'ON' (uppercase) status, inserts channel filter (line 229)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        from src.bot.cogs.admin.config import config_pfilter

        await config_pfilter(mock_ctx, subcommand_passed="ON")

        mock_dal.insert_profanity_filter_channel.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    @patch("src.bot.cogs.admin.config.bot_utils.send_embed")
    async def test_pfilter_off_uppercase(self, mock_send_embed, mock_dal_class, config_cog, mock_ctx):
        """When 'OFF' (uppercase) status, deletes channel filter (line 240)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        from src.bot.cogs.admin.config import config_pfilter

        await config_pfilter(mock_ctx, subcommand_passed="OFF")

        mock_dal.delete_profanity_filter_channel.assert_called_once_with(11111)


class TestConfigViewHandleUpdate:
    """Tests for ConfigView._handle_update (lines 396-466)."""

    @pytest.mark.asyncio
    async def test_handle_update_wrong_user_ephemeral(self, config_view, mock_ctx):
        """When interaction user is not the command invoker, sends ephemeral (lines 405-408)."""
        interaction = MagicMock()
        interaction.user = MagicMock()  # Different user
        interaction.user.__eq__ = lambda self, other: False
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        button = MagicMock()

        await config_view._handle_update(interaction, button, "msg_on_join", AsyncMock(), "Join Messages")

        interaction.response.send_message.assert_called_once_with(
            "Only the command invoker can use these buttons.", ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_handle_update_spam_clicking_wait_message(self, config_view, mock_ctx):
        """When _updating is True (spam clicking), sends wait message (lines 411-412)."""
        config_view._updating = True

        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        button = MagicMock()

        await config_view._handle_update(interaction, button, "msg_on_join", AsyncMock(), "Join Messages")

        interaction.response.send_message.assert_called_once()
        assert "Please wait" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    async def test_handle_update_successful(self, mock_dal_class, config_view, mock_ctx, server_config):
        """When update succeeds, updates config and edits message (lines 414-458)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        button = MagicMock()
        button.style = discord.ButtonStyle.danger

        update_method = AsyncMock()

        # Mock _create_updated_embed and _restore_buttons
        config_view._create_updated_embed = AsyncMock(return_value=discord.Embed())
        config_view._restore_buttons = AsyncMock()

        # Mock children property
        mock_child = MagicMock()
        mock_child.disabled = False
        mock_child.style = discord.ButtonStyle.success
        with patch.object(type(config_view), "children", new_callable=PropertyMock, return_value=[mock_child]):
            await config_view._handle_update(interaction, button, "msg_on_join", update_method, "Join Messages")

        interaction.response.defer.assert_called_once()
        # Verify config was toggled (was True, now should be False)
        assert server_config["msg_on_join"] is False
        update_method.assert_called_once()
        # Button style should reflect new status
        assert button.style == discord.ButtonStyle.danger
        # Should have been called at least twice: processing state + final update
        assert interaction.edit_original_response.call_count >= 2
        # _updating should be reset to False
        assert config_view._updating is False

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    async def test_handle_update_exception_error_message(self, mock_dal_class, config_view, mock_ctx, server_config):
        """When update raises exception, sends error message (lines 461-464)."""
        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        button = MagicMock()
        button.style = discord.ButtonStyle.success

        # Make the update method raise an exception
        update_method = AsyncMock(side_effect=Exception("Database error"))
        config_view._restore_buttons = AsyncMock()

        mock_child = MagicMock()
        mock_child.disabled = False
        mock_child.style = discord.ButtonStyle.success
        with patch.object(type(config_view), "children", new_callable=PropertyMock, return_value=[mock_child]):
            await config_view._handle_update(interaction, button, "msg_on_join", update_method, "Join Messages")

        # Should have error response
        last_call = interaction.edit_original_response.call_args_list[-1]
        assert "Error updating configuration" in last_call[1]["content"]
        # _updating should be reset to False in finally block
        assert config_view._updating is False

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    async def test_handle_update_toggles_from_false_to_true(self, mock_dal_class, config_view, mock_ctx, server_config):
        """When toggling from False to True, button becomes success style (lines 447-448)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        button = MagicMock()
        button.style = discord.ButtonStyle.danger

        update_method = AsyncMock()
        config_view._create_updated_embed = AsyncMock(return_value=discord.Embed())
        config_view._restore_buttons = AsyncMock()

        # Start with False value
        server_config["msg_on_leave"] = False

        mock_child = MagicMock()
        mock_child.disabled = False
        mock_child.style = discord.ButtonStyle.success
        with patch.object(type(config_view), "children", new_callable=PropertyMock, return_value=[mock_child]):
            await config_view._handle_update(interaction, button, "msg_on_leave", update_method, "Leave Messages")

        assert server_config["msg_on_leave"] is True
        assert button.style == discord.ButtonStyle.success

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ServersDal")
    async def test_handle_update_disables_buttons_during_processing(
        self, mock_dal_class, config_view, mock_ctx, server_config
    ):
        """Buttons are disabled during processing and re-enabled after (lines 416-420)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal

        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        button = MagicMock()
        button.style = discord.ButtonStyle.success

        update_method = AsyncMock()
        config_view._create_updated_embed = AsyncMock(return_value=discord.Embed())
        config_view._restore_buttons = AsyncMock()

        # Add mock children to view
        mock_child = MagicMock()
        mock_child.disabled = False
        mock_child.style = discord.ButtonStyle.success

        with patch.object(type(config_view), "children", new_callable=PropertyMock, return_value=[mock_child]):
            await config_view._handle_update(interaction, button, "msg_on_join", update_method, "Join Messages")

        # After completion, _updating should be False
        assert config_view._updating is False


class TestConfigViewRestoreButtons:
    """Tests for ConfigView._restore_buttons (lines 468-492)."""

    @pytest.mark.asyncio
    async def test_restore_buttons_sets_correct_styles(self, config_view, server_config):
        """Restores all button styles based on current config (lines 470-492)."""
        # Add mock children with disabled attribute
        mock_child1 = MagicMock()
        mock_child1.disabled = True
        mock_child2 = MagicMock()
        mock_child2.disabled = True
        config_view._children = [mock_child1, mock_child2]

        # Use property mock for children iteration
        with patch.object(
            type(config_view), "children", new_callable=PropertyMock, return_value=[mock_child1, mock_child2]
        ):
            await config_view._restore_buttons()

        # Check styles match config values
        # msg_on_join=True -> success
        assert config_view.toggle_join_messages.style == discord.ButtonStyle.success
        # msg_on_leave=False -> danger
        assert config_view.toggle_leave_messages.style == discord.ButtonStyle.danger
        # msg_on_server_update=True -> success
        assert config_view.toggle_server_messages.style == discord.ButtonStyle.success
        # msg_on_member_update=False -> danger
        assert config_view.toggle_member_messages.style == discord.ButtonStyle.danger
        # block_invis_members=True -> success
        assert config_view.toggle_block_invisible.style == discord.ButtonStyle.success
        # bot_word_reactions=False -> danger
        assert config_view.toggle_bot_reactions.style == discord.ButtonStyle.danger

    @pytest.mark.asyncio
    async def test_restore_buttons_enables_all_children(self, config_view, server_config):
        """All children are re-enabled (lines 470-472)."""
        mock_child1 = MagicMock()
        mock_child1.disabled = True
        mock_child2 = MagicMock()
        mock_child2.disabled = True

        with patch.object(
            type(config_view), "children", new_callable=PropertyMock, return_value=[mock_child1, mock_child2]
        ):
            await config_view._restore_buttons()

        assert mock_child1.disabled is False
        assert mock_child2.disabled is False


class TestConfigViewCreateUpdatedEmbed:
    """Tests for ConfigView._create_updated_embed (lines 494-559)."""

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    async def test_create_updated_embed_with_pfilter_channels(self, mock_dal_class, config_view, server_config):
        """Creates embed with profanity filter channels listed (lines 504-506)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_profanity_filter_channels.return_value = [
            {"channel_name": "general"},
            {"channel_name": "random"},
        ]

        embed = await config_view._create_updated_embed()

        assert isinstance(embed, discord.Embed)
        assert embed.author.name == "Configurations for TestGuild"
        assert len(embed.fields) == 7
        # Check profanity filter field has channel names
        pf_field = embed.fields[6]
        assert "general" in pf_field.value
        assert "random" in pf_field.value

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    async def test_create_updated_embed_without_pfilter_channels(self, mock_dal_class, config_view, server_config):
        """Creates embed without profanity filter channels (lines 507-508)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_profanity_filter_channels.return_value = []

        embed = await config_view._create_updated_embed()

        assert isinstance(embed, discord.Embed)
        pf_field = embed.fields[6]
        assert messages.NO_CHANNELS_LISTED in pf_field.value

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    async def test_create_updated_embed_status_indicators(self, mock_dal_class, config_view, server_config):
        """Status indicators match config (lines 510-512, 522-556)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_profanity_filter_channels.return_value = []

        embed = await config_view._create_updated_embed()

        # msg_on_join=True -> should have green ON text
        join_field = embed.fields[0]
        assert "ON" in join_field.value
        # msg_on_leave=False -> should have red OFF text
        leave_field = embed.fields[1]
        assert "OFF" in leave_field.value

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    async def test_create_updated_embed_no_guild_icon(self, mock_dal_class, mock_ctx, server_config):
        """Handles no guild icon gracefully (line 518)."""
        mock_ctx.guild.icon = None

        view = object.__new__(ConfigView)
        view.ctx = mock_ctx
        view.server_config = server_config
        view._updating = False
        view.message = None
        view._children = []

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_profanity_filter_channels.return_value = []

        embed = await view._create_updated_embed()

        assert embed.author.icon_url is None
        assert embed.thumbnail.url is None

    @pytest.mark.asyncio
    @patch("src.bot.cogs.admin.config.ProfanityFilterDal")
    async def test_create_updated_embed_footer(self, mock_dal_class, config_view, server_config):
        """Embed footer contains help info (line 558)."""
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_profanity_filter_channels.return_value = []

        embed = await config_view._create_updated_embed()

        assert messages.MORE_INFO in embed.footer.text
        assert "!help admin config" in embed.footer.text


class TestConfigViewButtonCallbacks:
    """Tests for button callbacks (lines 561-619).

    Since the buttons are decorated methods on the class, we use the class-level
    methods to invoke them, with _handle_update mocked to capture arguments.
    """

    def _get_real_config_view(self, mock_ctx, server_config):
        """Create a ConfigView with real button methods but no event loop dependency."""
        with patch.object(discord.ui.View, "__init__", lambda self, **kwargs: None):
            view = object.__new__(ConfigView)
            view.ctx = mock_ctx
            view.server_config = server_config
            view._updating = False
            view.message = None
            view._children = []
        return view

    @pytest.mark.asyncio
    async def test_toggle_join_messages_callback(self, mock_ctx, server_config):
        """Test toggle_join_messages button callback (lines 562-569, line 563)."""
        view = self._get_real_config_view(mock_ctx, server_config)
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        # Call the unbound method from ConfigView class
        await ConfigView.toggle_join_messages(view, interaction, button)

        view._handle_update.assert_called_once()
        call_args = view._handle_update.call_args
        assert call_args[0][0] == interaction
        assert call_args[0][1] == button
        assert call_args[0][2] == "msg_on_join"
        assert call_args[0][4] == "Join Messages"

    @pytest.mark.asyncio
    async def test_toggle_leave_messages_callback(self, mock_ctx, server_config):
        """Test toggle_leave_messages button callback (lines 571-579, line 573)."""
        view = self._get_real_config_view(mock_ctx, server_config)
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_leave_messages(view, interaction, button)

        view._handle_update.assert_called_once()
        call_args = view._handle_update.call_args
        assert call_args[0][2] == "msg_on_leave"
        assert call_args[0][4] == "Leave Messages"

    @pytest.mark.asyncio
    async def test_toggle_server_messages_callback(self, mock_ctx, server_config):
        """Test toggle_server_messages button callback (lines 581-589, line 583)."""
        view = self._get_real_config_view(mock_ctx, server_config)
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_server_messages(view, interaction, button)

        view._handle_update.assert_called_once()
        call_args = view._handle_update.call_args
        assert call_args[0][2] == "msg_on_server_update"
        assert call_args[0][4] == "Server Messages"

    @pytest.mark.asyncio
    async def test_toggle_member_messages_callback(self, mock_ctx, server_config):
        """Test toggle_member_messages button callback (lines 591-599, line 593)."""
        view = self._get_real_config_view(mock_ctx, server_config)
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_member_messages(view, interaction, button)

        view._handle_update.assert_called_once()
        call_args = view._handle_update.call_args
        assert call_args[0][2] == "msg_on_member_update"
        assert call_args[0][4] == "Member Messages"

    @pytest.mark.asyncio
    async def test_toggle_block_invisible_callback(self, mock_ctx, server_config):
        """Test toggle_block_invisible button callback (lines 601-609, line 603)."""
        view = self._get_real_config_view(mock_ctx, server_config)
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_block_invisible(view, interaction, button)

        view._handle_update.assert_called_once()
        call_args = view._handle_update.call_args
        assert call_args[0][2] == "block_invis_members"
        assert call_args[0][4] == "Block Invisible"

    @pytest.mark.asyncio
    async def test_toggle_bot_reactions_callback(self, mock_ctx, server_config):
        """Test toggle_bot_reactions button callback (lines 611-619, line 613)."""
        view = self._get_real_config_view(mock_ctx, server_config)
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_bot_reactions(view, interaction, button)

        view._handle_update.assert_called_once()
        call_args = view._handle_update.call_args
        assert call_args[0][2] == "bot_word_reactions"
        assert call_args[0][4] == "Bot Reactions"


class TestConfigViewOnTimeout:
    """Tests for ConfigView.on_timeout (lines 621-629)."""

    @pytest.mark.asyncio
    async def test_on_timeout_disables_buttons(self, config_view):
        """On timeout, all buttons are disabled (lines 623-624)."""
        mock_message = MagicMock()
        mock_message.edit = AsyncMock()
        config_view.message = mock_message

        # Add mock children
        mock_child1 = MagicMock()
        mock_child1.disabled = False
        mock_child2 = MagicMock()
        mock_child2.disabled = False

        with patch.object(
            type(config_view), "children", new_callable=PropertyMock, return_value=[mock_child1, mock_child2]
        ):
            await config_view.on_timeout()

        assert mock_child1.disabled is True
        assert mock_child2.disabled is True
        mock_message.edit.assert_called_once_with(view=config_view)

    @pytest.mark.asyncio
    async def test_on_timeout_message_not_found(self, config_view):
        """On timeout when message is deleted (NotFound), handles gracefully (lines 628-629)."""
        mock_message = MagicMock()
        mock_message.edit = AsyncMock(side_effect=discord.NotFound(MagicMock(), "Not found"))
        config_view.message = mock_message

        mock_child = MagicMock()
        mock_child.disabled = False

        with patch.object(type(config_view), "children", new_callable=PropertyMock, return_value=[mock_child]):
            # Should not raise
            await config_view.on_timeout()

        assert mock_child.disabled is True

    @pytest.mark.asyncio
    async def test_on_timeout_http_exception(self, config_view):
        """On timeout when HTTPException occurs, handles gracefully (lines 628-629)."""
        mock_message = MagicMock()
        mock_message.edit = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "HTTP error"))
        config_view.message = mock_message

        mock_child = MagicMock()
        mock_child.disabled = False

        with patch.object(type(config_view), "children", new_callable=PropertyMock, return_value=[mock_child]):
            # Should not raise
            await config_view.on_timeout()

        assert mock_child.disabled is True


class TestGetSwitchStatus:
    """Tests for _get_switch_status function (lines 365-383)."""

    def test_on_returns_true_green(self):
        """'on' returns (True, green) (lines 378-379)."""
        status, color = _get_switch_status("on")
        assert status is True
        assert color == discord.Color.green()

    def test_off_returns_false_red(self):
        """'off' returns (False, red) (lines 380-381)."""
        status, color = _get_switch_status("off")
        assert status is False
        assert color == discord.Color.red()

    def test_invalid_raises_bad_argument(self):
        """Invalid input raises BadArgument (lines 382-383)."""
        with pytest.raises(commands.BadArgument):
            _get_switch_status("invalid")

    def test_on_mixed_case(self):
        """Mixed case 'On' works (case insensitive via .lower())."""
        status, color = _get_switch_status("On")
        assert status is True
        assert color == discord.Color.green()

    def test_off_mixed_case(self):
        """Mixed case 'oFf' works (case insensitive via .lower())."""
        status, color = _get_switch_status("oFf")
        assert status is False
        assert color == discord.Color.red()

    def test_on_uppercase(self):
        """'ON' returns (True, green)."""
        status, color = _get_switch_status("ON")
        assert status is True
        assert color == discord.Color.green()

    def test_off_uppercase(self):
        """'OFF' returns (False, red)."""
        status, color = _get_switch_status("OFF")
        assert status is False
        assert color == discord.Color.red()

    def test_empty_string_raises(self):
        """Empty string raises BadArgument."""
        with pytest.raises(commands.BadArgument):
            _get_switch_status("")

    def test_numeric_raises(self):
        """Numeric input raises BadArgument."""
        with pytest.raises(commands.BadArgument):
            _get_switch_status("123")


class TestConfigViewButtonUpdateMethodLambdas:
    """Tests for the lambda update methods passed by button callbacks (lines 567, 577, 587, 597, 607, 617)."""

    def _get_real_config_view(self, mock_ctx, server_config):
        """Create a ConfigView with real button methods but no event loop dependency."""
        with patch.object(discord.ui.View, "__init__", lambda self, **kwargs: None):
            view = object.__new__(ConfigView)
            view.ctx = mock_ctx
            view.server_config = server_config
            view._updating = False
            view.message = None
            view._children = []
        return view

    @pytest.mark.asyncio
    async def test_join_messages_lambda_calls_correct_dal_method(self, mock_ctx, server_config):
        """The join messages lambda calls dal.update_msg_on_join."""
        view = self._get_real_config_view(mock_ctx, server_config)
        mock_dal = AsyncMock()
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_join_messages(view, interaction, button)

        # Extract the lambda from the call
        call_args = view._handle_update.call_args
        update_lambda = call_args[0][3]

        # Call the lambda and verify it calls the correct DAL method
        await update_lambda(mock_dal, 99999, True, 12345)
        mock_dal.update_msg_on_join.assert_called_once_with(99999, True, 12345)

    @pytest.mark.asyncio
    async def test_leave_messages_lambda_calls_correct_dal_method(self, mock_ctx, server_config):
        """The leave messages lambda calls dal.update_msg_on_leave."""
        view = self._get_real_config_view(mock_ctx, server_config)
        mock_dal = AsyncMock()
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_leave_messages(view, interaction, button)

        call_args = view._handle_update.call_args
        update_lambda = call_args[0][3]

        await update_lambda(mock_dal, 99999, False, 12345)
        mock_dal.update_msg_on_leave.assert_called_once_with(99999, False, 12345)

    @pytest.mark.asyncio
    async def test_server_messages_lambda_calls_correct_dal_method(self, mock_ctx, server_config):
        """The server messages lambda calls dal.update_msg_on_server_update."""
        view = self._get_real_config_view(mock_ctx, server_config)
        mock_dal = AsyncMock()
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_server_messages(view, interaction, button)

        call_args = view._handle_update.call_args
        update_lambda = call_args[0][3]

        await update_lambda(mock_dal, 99999, True, 12345)
        mock_dal.update_msg_on_server_update.assert_called_once_with(99999, True, 12345)

    @pytest.mark.asyncio
    async def test_member_messages_lambda_calls_correct_dal_method(self, mock_ctx, server_config):
        """The member messages lambda calls dal.update_msg_on_member_update."""
        view = self._get_real_config_view(mock_ctx, server_config)
        mock_dal = AsyncMock()
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_member_messages(view, interaction, button)

        call_args = view._handle_update.call_args
        update_lambda = call_args[0][3]

        await update_lambda(mock_dal, 99999, False, 12345)
        mock_dal.update_msg_on_member_update.assert_called_once_with(99999, False, 12345)

    @pytest.mark.asyncio
    async def test_block_invisible_lambda_calls_correct_dal_method(self, mock_ctx, server_config):
        """The block invisible lambda calls dal.update_block_invis_members."""
        view = self._get_real_config_view(mock_ctx, server_config)
        mock_dal = AsyncMock()
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_block_invisible(view, interaction, button)

        call_args = view._handle_update.call_args
        update_lambda = call_args[0][3]

        await update_lambda(mock_dal, 99999, True, 12345)
        mock_dal.update_block_invis_members.assert_called_once_with(99999, True, 12345)

    @pytest.mark.asyncio
    async def test_bot_reactions_lambda_calls_correct_dal_method(self, mock_ctx, server_config):
        """The bot reactions lambda calls dal.update_bot_word_reactions."""
        view = self._get_real_config_view(mock_ctx, server_config)
        mock_dal = AsyncMock()
        view._handle_update = AsyncMock()

        interaction = MagicMock()
        button = MagicMock()

        await ConfigView.toggle_bot_reactions(view, interaction, button)

        call_args = view._handle_update.call_args
        update_lambda = call_args[0][3]

        await update_lambda(mock_dal, 99999, False, 12345)
        mock_dal.update_bot_word_reactions.assert_called_once_with(99999, False, 12345)
