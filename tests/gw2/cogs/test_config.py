"""Comprehensive tests for GW2 config cog."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import discord
from discord.ext import commands

from src.gw2.cogs.config import GW2Config, config, config_list, config_session, GW2ConfigView


class TestGW2Config:
    """Test cases for the GW2Config cog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def gw2_config_cog(self, mock_bot):
        """Create a GW2Config cog instance."""
        return GW2Config(mock_bot)

    def test_gw2_config_initialization(self, mock_bot):
        """Test GW2Config cog initialization."""
        cog = GW2Config(mock_bot)
        assert cog.bot == mock_bot

    def test_gw2_config_inheritance(self, gw2_config_cog):
        """Test that GW2Config inherits from GuildWars2 properly."""
        from src.gw2.cogs.gw2 import GuildWars2
        assert isinstance(gw2_config_cog, GuildWars2)


class TestConfigGroupCommand:
    """Test cases for the config group command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.invoked_subcommand = None
        return ctx

    @pytest.mark.asyncio
    async def test_config_group_invokes_subcommand(self, mock_ctx):
        """Test that config group command calls invoke_subcommand."""
        with patch('src.gw2.cogs.config.bot_utils.invoke_subcommand') as mock_invoke:
            mock_invoke.return_value = None
            await config(mock_ctx)
            mock_invoke.assert_called_once_with(mock_ctx, "gw2 config")


class TestConfigListCommand:
    """Test cases for the config list command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.guild.icon = MagicMock()
        ctx.guild.icon.url = "https://example.com/icon.png"
        ctx.guild.name = "TestGuild"
        ctx.prefix = "!"
        ctx.author = MagicMock()
        ctx.author.id = 12345
        ctx.author.name = "TestUser"
        ctx.author.display_name = "TestUser"
        ctx.author.avatar = MagicMock()
        ctx.author.avatar.url = "https://example.com/avatar.png"
        ctx.author.send = AsyncMock()
        ctx.send = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_config_list_creates_embed_with_current_config_session_on(self, mock_ctx):
        """Test config_list creates embed with session ON."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=[{
                "session": True
            }])
            with patch('src.gw2.cogs.config.chat_formatting.green_text') as mock_green:
                mock_green.return_value = "```css\nON\n```"
                with patch('src.gw2.cogs.config.chat_formatting.red_text') as mock_red:
                    mock_red.return_value = "```diff\n-OFF\n```"
                    await config_list(mock_ctx)
                    mock_ctx.author.send.assert_called_once()
                    call_kwargs = mock_ctx.author.send.call_args[1]
                    embed = call_kwargs["embed"]
                    assert "TestGuild" in embed.author.name
                    # Session is ON, so green_text should be used for the field value
                    session_field = embed.fields[0]
                    assert "ON" in session_field.value

    @pytest.mark.asyncio
    async def test_config_list_creates_embed_with_current_config_session_off(self, mock_ctx):
        """Test config_list creates embed with session OFF."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=[{
                "session": False
            }])
            with patch('src.gw2.cogs.config.chat_formatting.green_text') as mock_green:
                mock_green.return_value = "```css\nON\n```"
                with patch('src.gw2.cogs.config.chat_formatting.red_text') as mock_red:
                    mock_red.return_value = "```diff\n-OFF\n```"
                    await config_list(mock_ctx)
                    mock_ctx.author.send.assert_called_once()
                    call_kwargs = mock_ctx.author.send.call_args[1]
                    embed = call_kwargs["embed"]
                    session_field = embed.fields[0]
                    assert "OFF" in session_field.value

    @pytest.mark.asyncio
    async def test_config_list_creates_interactive_view(self, mock_ctx):
        """Test config_list creates interactive view with buttons."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=[{
                "session": True
            }])
            with patch('src.gw2.cogs.config.chat_formatting.green_text', return_value="ON"):
                with patch('src.gw2.cogs.config.chat_formatting.red_text', return_value="OFF"):
                    await config_list(mock_ctx)
                    mock_ctx.author.send.assert_called_once()
                    call_kwargs = mock_ctx.author.send.call_args[1]
                    view = call_kwargs["view"]
                    assert isinstance(view, GW2ConfigView)

    @pytest.mark.asyncio
    async def test_config_list_sends_dm_and_notification_in_channel(self, mock_ctx):
        """Test config_list sends to DM and notification in channel."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=[{
                "session": True
            }])
            with patch('src.gw2.cogs.config.chat_formatting.green_text', return_value="ON"):
                with patch('src.gw2.cogs.config.chat_formatting.red_text', return_value="OFF"):
                    await config_list(mock_ctx)
                    # DM sent
                    mock_ctx.author.send.assert_called_once()
                    # Channel notification sent
                    mock_ctx.send.assert_called_once()
                    notification_kwargs = mock_ctx.send.call_args[1]
                    notification_embed = notification_kwargs["embed"]
                    assert "DM" in notification_embed.description or "DM" in notification_embed.description.upper()

    @pytest.mark.asyncio
    async def test_config_list_button_style_success_when_session_on(self, mock_ctx):
        """Test config_list sets button style to success when session is ON."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=[{
                "session": True
            }])
            with patch('src.gw2.cogs.config.chat_formatting.green_text', return_value="ON"):
                with patch('src.gw2.cogs.config.chat_formatting.red_text', return_value="OFF"):
                    await config_list(mock_ctx)
                    call_kwargs = mock_ctx.author.send.call_args[1]
                    view = call_kwargs["view"]
                    assert view.toggle_session.style == discord.ButtonStyle.success

    @pytest.mark.asyncio
    async def test_config_list_button_style_danger_when_session_off(self, mock_ctx):
        """Test config_list sets button style to danger when session is OFF."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=[{
                "session": False
            }])
            with patch('src.gw2.cogs.config.chat_formatting.green_text', return_value="ON"):
                with patch('src.gw2.cogs.config.chat_formatting.red_text', return_value="OFF"):
                    await config_list(mock_ctx)
                    call_kwargs = mock_ctx.author.send.call_args[1]
                    view = call_kwargs["view"]
                    assert view.toggle_session.style == discord.ButtonStyle.danger

    @pytest.mark.asyncio
    async def test_config_list_no_guild_icon(self, mock_ctx):
        """Test config_list when guild has no icon."""
        mock_ctx.guild.icon = None
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_gw2_server_configs = AsyncMock(return_value=[{
                "session": True
            }])
            with patch('src.gw2.cogs.config.chat_formatting.green_text', return_value="ON"):
                with patch('src.gw2.cogs.config.chat_formatting.red_text', return_value="OFF"):
                    await config_list(mock_ctx)
                    call_kwargs = mock_ctx.author.send.call_args[1]
                    embed = call_kwargs["embed"]
                    assert embed.thumbnail.url is None


class TestConfigSessionCommand:
    """Test cases for the config session command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.message = MagicMock()
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.message.channel.guild = MagicMock()
        ctx.message.channel.guild.id = 99999
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.prefix = "!"
        ctx.author = MagicMock()
        ctx.author.id = 12345
        ctx.send = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_config_session_on_activates(self, mock_ctx):
        """Test config session 'on' activates session with green color."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.update_gw2_session_config = AsyncMock()
            with patch('src.gw2.cogs.config.bot_utils.send_embed') as mock_send:
                await config_session(mock_ctx, "on")
                mock_instance.update_gw2_session_config.assert_called_once_with(
                    99999, True, 12345
                )
                mock_send.assert_called_once()
                embed = mock_send.call_args[0][1]
                assert embed.color == discord.Color.green()
                assert "ACTIVATED" in embed.description

    @pytest.mark.asyncio
    async def test_config_session_ON_uppercase_activates(self, mock_ctx):
        """Test config session 'ON' (uppercase) activates session with green color."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.update_gw2_session_config = AsyncMock()
            with patch('src.gw2.cogs.config.bot_utils.send_embed') as mock_send:
                await config_session(mock_ctx, "ON")
                mock_instance.update_gw2_session_config.assert_called_once_with(
                    99999, True, 12345
                )
                mock_send.assert_called_once()
                embed = mock_send.call_args[0][1]
                assert embed.color == discord.Color.green()

    @pytest.mark.asyncio
    async def test_config_session_off_deactivates(self, mock_ctx):
        """Test config session 'off' deactivates session with red color."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.update_gw2_session_config = AsyncMock()
            with patch('src.gw2.cogs.config.bot_utils.send_embed') as mock_send:
                await config_session(mock_ctx, "off")
                mock_instance.update_gw2_session_config.assert_called_once_with(
                    99999, False, 12345
                )
                mock_send.assert_called_once()
                embed = mock_send.call_args[0][1]
                assert embed.color == discord.Color.red()
                assert "DEACTIVATED" in embed.description

    @pytest.mark.asyncio
    async def test_config_session_OFF_uppercase_deactivates(self, mock_ctx):
        """Test config session 'OFF' (uppercase) deactivates session with red color."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.update_gw2_session_config = AsyncMock()
            with patch('src.gw2.cogs.config.bot_utils.send_embed') as mock_send:
                await config_session(mock_ctx, "OFF")
                mock_instance.update_gw2_session_config.assert_called_once_with(
                    99999, False, 12345
                )
                mock_send.assert_called_once()
                embed = mock_send.call_args[0][1]
                assert embed.color == discord.Color.red()

    @pytest.mark.asyncio
    async def test_config_session_invalid_argument_raises_bad_argument(self, mock_ctx):
        """Test config session with invalid argument raises BadArgument."""
        with pytest.raises(commands.BadArgument):
            await config_session(mock_ctx, "invalid")

    @pytest.mark.asyncio
    async def test_config_session_invalid_mixed_case_raises_bad_argument(self, mock_ctx):
        """Test config session with mixed case invalid argument raises BadArgument."""
        with pytest.raises(commands.BadArgument):
            await config_session(mock_ctx, "On")

    @pytest.mark.asyncio
    async def test_config_session_triggers_typing_indicator(self, mock_ctx):
        """Test that config session triggers typing indicator."""
        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.update_gw2_session_config = AsyncMock()
            with patch('src.gw2.cogs.config.bot_utils.send_embed'):
                await config_session(mock_ctx, "on")
                mock_ctx.message.channel.typing.assert_called_once()


class TestGW2ConfigView:
    """Test cases for the GW2ConfigView class."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.guild.icon = MagicMock()
        ctx.guild.icon.url = "https://example.com/icon.png"
        ctx.guild.name = "TestGuild"
        ctx.prefix = "!"
        ctx.author = MagicMock()
        ctx.author.id = 12345
        ctx.author.name = "TestUser"
        ctx.author.display_name = "TestUser"
        return ctx

    @pytest.fixture
    def server_config(self):
        """Create a sample server config."""
        return {"session": True}

    @pytest.fixture
    def config_view(self, mock_ctx, server_config):
        """Create a GW2ConfigView instance."""
        with patch('discord.ui.view.View.__init__', return_value=None):
            view = GW2ConfigView(mock_ctx, server_config)
            # Manually set up what View.__init__ would set
            view._children = []
            view._View__timeout = 300
            # Create a mock toggle_session button
            view.toggle_session = MagicMock()
            view.toggle_session.style = discord.ButtonStyle.secondary
            view.toggle_session.disabled = False
            view.toggle_session.callback = AsyncMock()
            # Add it to children
            view._children.append(view.toggle_session)
            view.message = MagicMock()
            view.message.edit = AsyncMock()
            return view

    @pytest.mark.asyncio
    async def test_config_view_initialization(self, mock_ctx, server_config):
        """Test GW2ConfigView initialization."""
        with patch('discord.ui.view.View.__init__', return_value=None):
            view = GW2ConfigView(mock_ctx, server_config)
            assert view.ctx == mock_ctx
            assert view.server_config == server_config
            assert view._updating is False
            assert view.message is None

    @pytest.mark.asyncio
    async def test_handle_update_wrong_user_ephemeral_message(self, config_view, mock_ctx):
        """Test _handle_update sends ephemeral message when wrong user interacts."""
        interaction = MagicMock()
        # Create a different user that is != ctx.author
        different_user = MagicMock()
        different_user.id = 99999
        interaction.user = different_user
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        button = MagicMock()

        await config_view._handle_update(interaction, button, "session", "Session Tracking")

        interaction.response.send_message.assert_called_once_with(
            "Only the command invoker can use these buttons.", ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_handle_update_spam_clicking_wait_message(self, config_view, mock_ctx):
        """Test _handle_update sends wait message when spam clicking."""
        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        config_view._updating = True
        button = MagicMock()

        await config_view._handle_update(interaction, button, "session", "Session Tracking")

        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "Please wait" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_handle_update_successful_update(self, config_view, mock_ctx, server_config):
        """Test _handle_update performs successful configuration update."""
        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        button = MagicMock()

        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.update_gw2_session_config = AsyncMock()
            with patch('src.gw2.cogs.config.chat_formatting.green_text', return_value="ON"):
                with patch('src.gw2.cogs.config.chat_formatting.red_text', return_value="OFF"):
                    await config_view._handle_update(
                        interaction, button, "session", "Session Tracking"
                    )

                    # Verify defer was called
                    interaction.response.defer.assert_called_once()
                    # Verify database update
                    mock_instance.update_gw2_session_config.assert_called_once_with(
                        99999, False, 12345  # Toggle from True to False
                    )
                    # Verify config was toggled
                    assert config_view.server_config["session"] is False
                    # Verify _updating was reset
                    assert config_view._updating is False
                    # Verify success message was sent
                    assert interaction.edit_original_response.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_update_discord_http_error(self, config_view, mock_ctx):
        """Test _handle_update handles Discord HTTP error."""
        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        button = MagicMock()

        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_response = MagicMock()
            mock_response.status = 500
            mock_instance.update_gw2_session_config = AsyncMock(
                side_effect=discord.HTTPException(mock_response, "Server error")
            )
            await config_view._handle_update(
                interaction, button, "session", "Session Tracking"
            )

            # Verify error message was sent
            last_call = interaction.edit_original_response.call_args
            assert "Discord error" in last_call[1]["content"]
            # Verify _updating was reset
            assert config_view._updating is False

    @pytest.mark.asyncio
    async def test_handle_update_other_exception(self, config_view, mock_ctx):
        """Test _handle_update handles other exceptions."""
        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        button = MagicMock()

        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.update_gw2_session_config = AsyncMock(
                side_effect=Exception("Database connection error")
            )
            await config_view._handle_update(
                interaction, button, "session", "Session Tracking"
            )

            # Verify error was logged
            mock_ctx.bot.log.error.assert_called()
            # Verify error message was sent
            last_call = interaction.edit_original_response.call_args
            assert "Error updating configuration" in last_call[1]["content"]
            # Verify _updating was reset
            assert config_view._updating is False

    @pytest.mark.asyncio
    async def test_handle_update_exception_with_edit_failure(self, config_view, mock_ctx):
        """Test _handle_update handles exception when edit_original_response also fails."""
        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        # First call for processing state works, second call raises
        interaction.edit_original_response = AsyncMock(
            side_effect=[None, Exception("Edit failed")]
        )

        button = MagicMock()

        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.update_gw2_session_config = AsyncMock(
                side_effect=Exception("DB error")
            )
            # Should not raise - the inner exception is caught
            await config_view._handle_update(
                interaction, button, "session", "Session Tracking"
            )
            # Verify _updating was reset even with double failure
            assert config_view._updating is False

    @pytest.mark.asyncio
    async def test_restore_buttons(self, config_view):
        """Test _restore_buttons restores button states."""
        # Disable all buttons first
        for item in config_view.children:
            if hasattr(item, 'disabled'):
                item.disabled = True

        config_view.server_config["session"] = True
        await config_view._restore_buttons()

        # Check buttons are re-enabled
        for item in config_view.children:
            if hasattr(item, 'disabled'):
                assert item.disabled is False

        # Check toggle_session style is success (session is True)
        assert config_view.toggle_session.style == discord.ButtonStyle.success

    @pytest.mark.asyncio
    async def test_restore_buttons_session_off(self, config_view):
        """Test _restore_buttons with session OFF sets danger style."""
        config_view.server_config["session"] = False
        await config_view._restore_buttons()

        assert config_view.toggle_session.style == discord.ButtonStyle.danger

    @pytest.mark.asyncio
    async def test_create_updated_embed(self, config_view):
        """Test _create_updated_embed creates proper embed."""
        config_view.server_config["session"] = True
        with patch('src.gw2.cogs.config.chat_formatting.green_text') as mock_green:
            mock_green.return_value = "```css\nON\n```"
            with patch('src.gw2.cogs.config.chat_formatting.red_text') as mock_red:
                mock_red.return_value = "```diff\n-OFF\n```"
                embed = await config_view._create_updated_embed()
                assert embed.color.value == 0x00FF00
                assert "TestGuild" in embed.author.name
                assert len(embed.fields) == 1
                assert "ON" in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_create_updated_embed_session_off(self, config_view):
        """Test _create_updated_embed with session OFF."""
        config_view.server_config["session"] = False
        with patch('src.gw2.cogs.config.chat_formatting.green_text') as mock_green:
            mock_green.return_value = "```css\nON\n```"
            with patch('src.gw2.cogs.config.chat_formatting.red_text') as mock_red:
                mock_red.return_value = "```diff\n-OFF\n```"
                embed = await config_view._create_updated_embed()
                assert "OFF" in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_create_updated_embed_no_guild_icon(self, config_view, mock_ctx):
        """Test _create_updated_embed when guild has no icon."""
        mock_ctx.guild.icon = None
        config_view.server_config["session"] = True
        with patch('src.gw2.cogs.config.chat_formatting.green_text', return_value="ON"):
            with patch('src.gw2.cogs.config.chat_formatting.red_text', return_value="OFF"):
                embed = await config_view._create_updated_embed()
                assert embed.thumbnail.url is None

    @pytest.mark.asyncio
    async def test_toggle_session_button_callback(self, mock_ctx, server_config):
        """Test toggle_session button callback calls _handle_update with correct args."""
        with patch('discord.ui.view.View.__init__', return_value=None):
            view = GW2ConfigView(mock_ctx, server_config)
            view._children = []
            view._View__timeout = 300

        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        button = MagicMock()

        with patch.object(view, '_handle_update', new_callable=AsyncMock) as mock_handle:
            # Call the actual toggle_session function directly (it's a decorated method)
            await GW2ConfigView.toggle_session(view, interaction, button)
            mock_handle.assert_called_once_with(
                interaction,
                button,
                "session",
                "Session Tracking",
            )

    @pytest.mark.asyncio
    async def test_on_timeout_disables_buttons(self, config_view):
        """Test on_timeout disables all buttons."""
        await config_view.on_timeout()

        for item in config_view.children:
            assert item.disabled is True

        config_view.message.edit.assert_called_once_with(view=config_view)

    @pytest.mark.asyncio
    async def test_on_timeout_message_not_found(self, config_view):
        """Test on_timeout handles discord.NotFound gracefully."""
        mock_response = MagicMock()
        mock_response.status = 404
        config_view.message.edit = AsyncMock(
            side_effect=discord.NotFound(mock_response, "Not found")
        )

        # Should not raise
        await config_view.on_timeout()

        for item in config_view.children:
            assert item.disabled is True

    @pytest.mark.asyncio
    async def test_on_timeout_http_exception(self, config_view):
        """Test on_timeout handles discord.HTTPException gracefully."""
        mock_response = MagicMock()
        mock_response.status = 500
        config_view.message.edit = AsyncMock(
            side_effect=discord.HTTPException(mock_response, "Server error")
        )

        # Should not raise
        await config_view.on_timeout()

        for item in config_view.children:
            assert item.disabled is True

    @pytest.mark.asyncio
    async def test_on_timeout_message_is_none(self, config_view):
        """Test on_timeout when message is None."""
        config_view.message = None

        # Should raise AttributeError but it is caught by discord.NotFound/HTTPException handler
        # Actually the code tries self.message.edit which would raise AttributeError
        # Let's verify it raises as the code doesn't handle None message
        with pytest.raises(AttributeError):
            await config_view.on_timeout()

    @pytest.mark.asyncio
    async def test_handle_update_disables_all_buttons_during_processing(self, config_view, mock_ctx):
        """Test that _handle_update disables all buttons during processing."""
        interaction = MagicMock()
        interaction.user = mock_ctx.author
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        button = MagicMock()
        buttons_disabled_during_processing = []

        original_edit = interaction.edit_original_response

        async def capture_disabled_state(*args, **kwargs):
            # Capture button states when edit is first called (processing state)
            if not buttons_disabled_during_processing:
                for item in config_view.children:
                    if hasattr(item, 'disabled'):
                        buttons_disabled_during_processing.append(item.disabled)

        interaction.edit_original_response = AsyncMock(side_effect=capture_disabled_state)

        with patch('src.gw2.cogs.config.Gw2ConfigsDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.update_gw2_session_config = AsyncMock()
            with patch('src.gw2.cogs.config.chat_formatting.green_text', return_value="ON"):
                with patch('src.gw2.cogs.config.chat_formatting.red_text', return_value="OFF"):
                    await config_view._handle_update(
                        interaction, button, "session", "Session Tracking"
                    )

        # Verify all buttons were disabled during processing
        for disabled_state in buttons_disabled_during_processing:
            assert disabled_state is True


class TestConfigSetup:
    """Test cases for config cog setup."""

    @pytest.mark.asyncio
    async def test_setup_function_exists(self):
        """Test that setup function exists and is callable."""
        from src.gw2.cogs.config import setup
        assert callable(setup)

    @pytest.mark.asyncio
    async def test_setup_removes_existing_gw2_command(self):
        """Test that setup removes existing gw2 command."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        from src.gw2.cogs.config import setup
        await setup(mock_bot)

        mock_bot.remove_command.assert_called_once_with("gw2")

    @pytest.mark.asyncio
    async def test_setup_adds_gw2_config_cog(self):
        """Test that setup adds the GW2Config cog."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        from src.gw2.cogs.config import setup
        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        cog_instance = mock_bot.add_cog.call_args[0][0]
        assert isinstance(cog_instance, GW2Config)
