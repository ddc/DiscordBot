"""Comprehensive tests for CustomHelpCommand and HelpPaginatorView classes."""

import discord
import pytest
import sys
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock, Mock

sys.modules["ddcDatabases"] = Mock()

from src.bot.tools.custom_help import CustomHelpCommand, HelpPaginatorView


class TestHelpPaginatorView:
    """Test HelpPaginatorView pagination logic."""

    @pytest.mark.asyncio
    async def test_initial_state_first_page(self):
        """Test view starts on page 0 with previous disabled and next enabled."""
        view = HelpPaginatorView(["Page A", "Page B", "Page C"], author_id=123)

        assert view.current_page == 0
        assert view.previous_button.disabled is True
        assert view.next_button.disabled is False
        assert view.page_indicator.label == "1/3"
        assert view.page_indicator.disabled is True

    @pytest.mark.asyncio
    async def test_initial_state_two_pages(self):
        """Test view with two pages has correct initial state."""
        view = HelpPaginatorView(["Page A", "Page B"], author_id=456)

        assert view.current_page == 0
        assert view.previous_button.disabled is True
        assert view.next_button.disabled is False
        assert view.page_indicator.label == "1/2"

    @pytest.mark.asyncio
    async def test_format_page_first(self):
        """Test _format_page returns page header + content for first page."""
        view = HelpPaginatorView(["```\nContent A\n```", "```\nContent B\n```"], author_id=1)

        result = view._format_page()

        assert result == "**Page 1/2**\n```\nContent A\n```"

    @pytest.mark.asyncio
    async def test_format_page_second(self):
        """Test _format_page returns correct content after navigating."""
        view = HelpPaginatorView(["Page A", "Page B", "Page C"], author_id=1)
        view.current_page = 1
        view._update_buttons()

        result = view._format_page()

        assert result == "**Page 2/3**\nPage B"

    @pytest.mark.asyncio
    async def test_update_buttons_middle_page(self):
        """Test buttons state on middle page: both enabled."""
        view = HelpPaginatorView(["A", "B", "C"], author_id=1)
        view.current_page = 1
        view._update_buttons()

        assert view.previous_button.disabled is False
        assert view.next_button.disabled is False
        assert view.page_indicator.label == "2/3"

    @pytest.mark.asyncio
    async def test_update_buttons_last_page(self):
        """Test buttons state on last page: next disabled."""
        view = HelpPaginatorView(["A", "B", "C"], author_id=1)
        view.current_page = 2
        view._update_buttons()

        assert view.previous_button.disabled is False
        assert view.next_button.disabled is True
        assert view.page_indicator.label == "3/3"

    @pytest.mark.asyncio
    async def test_next_button_advances_page(self):
        """Test clicking next button advances current_page."""
        view = HelpPaginatorView(["A", "B", "C"], author_id=42)
        interaction = MagicMock()
        interaction.user.id = 42
        interaction.response = AsyncMock()

        await view.next_button.callback(interaction)

        assert view.current_page == 1
        interaction.response.edit_message.assert_called_once()
        call_kwargs = interaction.response.edit_message.call_args[1]
        assert "**Page 2/3**" in call_kwargs["content"]

    @pytest.mark.asyncio
    async def test_previous_button_goes_back(self):
        """Test clicking previous button goes back a page."""
        view = HelpPaginatorView(["A", "B", "C"], author_id=42)
        view.current_page = 2
        view._update_buttons()
        interaction = MagicMock()
        interaction.user.id = 42
        interaction.response = AsyncMock()

        await view.previous_button.callback(interaction)

        assert view.current_page == 1
        interaction.response.edit_message.assert_called_once()
        call_kwargs = interaction.response.edit_message.call_args[1]
        assert "**Page 2/3**" in call_kwargs["content"]

    @pytest.mark.asyncio
    async def test_next_button_rejects_non_author(self):
        """Test non-author clicking next gets ephemeral rejection."""
        view = HelpPaginatorView(["A", "B"], author_id=42)
        interaction = MagicMock()
        interaction.user.id = 999
        interaction.response = AsyncMock()

        await view.next_button.callback(interaction)

        assert view.current_page == 0  # unchanged
        interaction.response.send_message.assert_called_once_with(
            "Only the command invoker can use these buttons.", ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_previous_button_rejects_non_author(self):
        """Test non-author clicking previous gets ephemeral rejection."""
        view = HelpPaginatorView(["A", "B"], author_id=42)
        view.current_page = 1
        view._update_buttons()
        interaction = MagicMock()
        interaction.user.id = 999
        interaction.response = AsyncMock()

        await view.previous_button.callback(interaction)

        assert view.current_page == 1  # unchanged
        interaction.response.send_message.assert_called_once_with(
            "Only the command invoker can use these buttons.", ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_page_indicator_defers(self):
        """Test page indicator button just defers (non-interactive)."""
        view = HelpPaginatorView(["A", "B"], author_id=1)
        interaction = MagicMock()
        interaction.response = AsyncMock()

        await view.page_indicator.callback(interaction)

        interaction.response.defer.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_timeout_disables_all_buttons(self):
        """Test on_timeout disables all children and edits message."""
        view = HelpPaginatorView(["A", "B"], author_id=1)
        view.message = AsyncMock()

        await view.on_timeout()

        for item in view.children:
            assert item.disabled is True
        view.message.edit.assert_called_once_with(view=view)

    @pytest.mark.asyncio
    async def test_on_timeout_no_message(self):
        """Test on_timeout with no message reference does not raise."""
        view = HelpPaginatorView(["A", "B"], author_id=1)
        view.message = None

        await view.on_timeout()

        for item in view.children:
            assert item.disabled is True

    @pytest.mark.asyncio
    async def test_timeout_is_300(self):
        """Test view timeout is 300 seconds."""
        view = HelpPaginatorView(["A", "B"], author_id=1)
        assert view.timeout == 300

    @pytest.mark.asyncio
    async def test_author_id_stored(self):
        """Test author_id is stored correctly."""
        view = HelpPaginatorView(["A"], author_id=12345)
        assert view.author_id == 12345

    @pytest.mark.asyncio
    async def test_pages_stored(self):
        """Test pages list is stored correctly."""
        pages = ["Page 1", "Page 2"]
        view = HelpPaginatorView(pages, author_id=1)
        assert view.pages is pages


class TestCustomHelpCommandInit:
    """Test CustomHelpCommand initialization."""

    def test_init_default_options(self):
        """Test initialization with default options sets paginator."""
        cmd = CustomHelpCommand()

        assert cmd.paginator is not None
        assert isinstance(cmd.paginator, commands.Paginator)
        assert cmd.paginator.prefix == "```"
        assert cmd.paginator.suffix == "```"
        assert cmd.paginator.max_size == 2000

    def test_init_custom_paginator(self):
        """Test initialization with custom paginator preserves it."""
        custom_paginator = commands.Paginator(prefix="---", suffix="---", max_size=1000)
        cmd = CustomHelpCommand(paginator=custom_paginator)

        assert cmd.paginator is custom_paginator
        assert cmd.paginator.prefix == "---"
        assert cmd.paginator.suffix == "---"
        assert cmd.paginator.max_size == 1000

    def test_init_custom_options_passed_to_parent(self):
        """Test that other options are passed to the parent class."""
        cmd = CustomHelpCommand(no_category="Uncategorized", sort_commands=False)

        assert cmd.no_category == "Uncategorized"
        assert cmd.sort_commands is False

    def test_init_dm_help_option(self):
        """Test initialization with dm_help option."""
        cmd = CustomHelpCommand(dm_help=True)
        assert cmd.dm_help is True

        cmd2 = CustomHelpCommand(dm_help=False)
        assert cmd2.dm_help is False


class TestSendPages:
    """Test send_pages method."""

    @pytest.fixture
    def help_command(self):
        """Create a CustomHelpCommand instance with mocked context."""
        cmd = CustomHelpCommand()
        cmd.context = MagicMock()
        cmd.context.send = AsyncMock()
        cmd.context.author = MagicMock()
        cmd.context.author.send = AsyncMock()
        cmd.context.author.display_name = "TestUser"
        cmd.context.author.avatar = MagicMock()
        cmd.context.author.avatar.url = "https://example.com/avatar.png"
        return cmd

    @pytest.mark.asyncio
    async def test_send_pages_no_pages(self, help_command):
        """Test send_pages when paginator has no pages."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = []
        mock_destination = AsyncMock()
        help_command.get_destination = MagicMock(return_value=mock_destination)

        await help_command.send_pages()

        mock_destination.send.assert_called_once_with("No help available")

    @pytest.mark.asyncio
    async def test_send_pages_dm_help_true_not_in_dm(self, help_command):
        """Test send_pages with dm_help=True and not in DM channel."""
        help_command.dm_help = True
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["Page 1 content"]

        # Destination is NOT a DM channel
        mock_destination = MagicMock(spec=discord.TextChannel)
        help_command.get_destination = MagicMock(return_value=mock_destination)

        help_command._send_pages_to_dm = AsyncMock()

        await help_command.send_pages()

        # Should send pages to DM
        help_command._send_pages_to_dm.assert_called_once()

        # Should send notification embed to channel
        help_command.context.send.assert_called_once()
        call_kwargs = help_command.context.send.call_args[1]
        embed = call_kwargs["embed"]
        assert isinstance(embed, discord.Embed)
        assert embed.color == discord.Color.green()

    @pytest.mark.asyncio
    async def test_send_pages_dm_help_true_notification_embed_description(self, help_command):
        """Test that the notification embed has correct description."""
        help_command.dm_help = True
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["Page 1 content"]

        mock_destination = MagicMock(spec=discord.TextChannel)
        help_command.get_destination = MagicMock(return_value=mock_destination)
        help_command._send_pages_to_dm = AsyncMock()

        await help_command.send_pages()

        call_kwargs = help_command.context.send.call_args[1]
        embed = call_kwargs["embed"]
        assert "Response sent to your DM" in embed.description

    @pytest.mark.asyncio
    async def test_send_pages_dm_help_true_author_with_avatar(self, help_command):
        """Test notification embed uses author avatar when available."""
        help_command.dm_help = True
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["Page 1"]

        mock_destination = MagicMock(spec=discord.TextChannel)
        help_command.get_destination = MagicMock(return_value=mock_destination)
        help_command._send_pages_to_dm = AsyncMock()

        help_command.context.author.avatar = MagicMock()
        help_command.context.author.avatar.url = "https://cdn.example.com/avatar.png"

        await help_command.send_pages()

        call_kwargs = help_command.context.send.call_args[1]
        embed = call_kwargs["embed"]
        assert embed.author.name == "TestUser"
        assert embed.author.icon_url == "https://cdn.example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_send_pages_dm_help_true_author_no_avatar(self, help_command):
        """Test notification embed uses default avatar when no avatar set."""
        help_command.dm_help = True
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["Page 1"]

        mock_destination = MagicMock(spec=discord.TextChannel)
        help_command.get_destination = MagicMock(return_value=mock_destination)
        help_command._send_pages_to_dm = AsyncMock()

        # Simulate no avatar
        help_command.context.author.avatar = None
        help_command.context.author.default_avatar = MagicMock()
        help_command.context.author.default_avatar.url = "https://cdn.example.com/default.png"

        await help_command.send_pages()

        call_kwargs = help_command.context.send.call_args[1]
        embed = call_kwargs["embed"]
        assert embed.author.icon_url == "https://cdn.example.com/default.png"

    @pytest.mark.asyncio
    async def test_send_pages_dm_help_false(self, help_command):
        """Test send_pages with dm_help=False sends to destination."""
        help_command.dm_help = False
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["Page 1 content"]

        mock_destination = AsyncMock()
        help_command.get_destination = MagicMock(return_value=mock_destination)
        help_command._send_pages_to_destination = AsyncMock()

        await help_command.send_pages()

        help_command._send_pages_to_destination.assert_called_once_with(mock_destination)

    @pytest.mark.asyncio
    async def test_send_pages_in_dm_channel(self, help_command):
        """Test send_pages when already in a DM channel sends to destination."""
        help_command.dm_help = True
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["Page 1 content"]

        # Destination IS a DM channel (isinstance check returns True)
        mock_destination = MagicMock(spec=discord.DMChannel)
        help_command.get_destination = MagicMock(return_value=mock_destination)
        help_command._send_pages_to_destination = AsyncMock()

        await help_command.send_pages()

        # Should send to destination directly, not to DM separately
        help_command._send_pages_to_destination.assert_called_once_with(mock_destination)


class TestSendPagesToDm:
    """Test _send_pages_to_dm method."""

    @pytest.fixture
    def help_command(self):
        """Create a CustomHelpCommand instance with mocked context."""
        cmd = CustomHelpCommand()
        cmd.context = MagicMock()
        cmd.context.author = MagicMock()
        cmd.context.author.id = 42
        cmd.context.author.send = AsyncMock()
        return cmd

    @pytest.mark.asyncio
    async def test_send_pages_to_dm_single_page(self, help_command):
        """Test _send_pages_to_dm with a single page does not add view."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["```\nHelp content here\n```"]

        await help_command._send_pages_to_dm()

        help_command.context.author.send.assert_called_once_with("```\nHelp content here\n```")

    @pytest.mark.asyncio
    async def test_send_pages_to_dm_multiple_pages_sends_single_message(self, help_command):
        """Test _send_pages_to_dm with multiple pages sends one message with view."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["```\nPage 1 content\n```", "```\nPage 2 content\n```"]

        await help_command._send_pages_to_dm()

        # Should send exactly one message (not two)
        help_command.context.author.send.assert_called_once()
        call_kwargs = help_command.context.author.send.call_args[1]
        assert "**Page 1/2**" in call_kwargs["content"]
        assert isinstance(call_kwargs["view"], HelpPaginatorView)

    @pytest.mark.asyncio
    async def test_send_pages_to_dm_multiple_pages_view_has_correct_pages(self, help_command):
        """Test that the view receives all pages."""
        pages = ["Page A", "Page B", "Page C"]
        help_command.paginator = MagicMock()
        help_command.paginator.pages = pages

        await help_command._send_pages_to_dm()

        call_kwargs = help_command.context.author.send.call_args[1]
        view = call_kwargs["view"]
        assert view.pages is pages
        assert view.author_id == 42

    @pytest.mark.asyncio
    async def test_send_pages_to_dm_multiple_pages_sets_message_ref(self, help_command):
        """Test that view.message is set to the sent message."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["A", "B"]
        mock_msg = AsyncMock()
        help_command.context.author.send.return_value = mock_msg

        await help_command._send_pages_to_dm()

        call_kwargs = help_command.context.author.send.call_args[1]
        view = call_kwargs["view"]
        assert view.message is mock_msg


class TestSendPagesToDestination:
    """Test _send_pages_to_destination method."""

    @pytest.fixture
    def help_command(self):
        """Create a CustomHelpCommand instance."""
        cmd = CustomHelpCommand()
        cmd.context = MagicMock()
        cmd.context.author = MagicMock()
        cmd.context.author.id = 42
        return cmd

    @pytest.mark.asyncio
    async def test_send_pages_to_destination_single_page(self, help_command):
        """Test _send_pages_to_destination with a single page does not add view."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["```\nSingle page content\n```"]
        mock_destination = AsyncMock()

        await help_command._send_pages_to_destination(mock_destination)

        mock_destination.send.assert_called_once_with("```\nSingle page content\n```")

    @pytest.mark.asyncio
    async def test_send_pages_to_destination_multiple_pages_sends_single_message(self, help_command):
        """Test _send_pages_to_destination with multiple pages sends one message with view."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["```\nFirst page\n```", "```\nSecond page\n```"]
        mock_destination = AsyncMock()

        await help_command._send_pages_to_destination(mock_destination)

        # Should send exactly one message (not two)
        mock_destination.send.assert_called_once()
        call_kwargs = mock_destination.send.call_args[1]
        assert "**Page 1/2**" in call_kwargs["content"]
        assert isinstance(call_kwargs["view"], HelpPaginatorView)

    @pytest.mark.asyncio
    async def test_send_pages_to_destination_multiple_pages_view_has_correct_pages(self, help_command):
        """Test that the view receives all pages."""
        pages = ["Content A", "Content B", "Content C"]
        help_command.paginator = MagicMock()
        help_command.paginator.pages = pages
        mock_destination = AsyncMock()

        await help_command._send_pages_to_destination(mock_destination)

        call_kwargs = mock_destination.send.call_args[1]
        view = call_kwargs["view"]
        assert view.pages is pages
        assert view.author_id == 42

    @pytest.mark.asyncio
    async def test_send_pages_to_destination_multiple_pages_sets_message_ref(self, help_command):
        """Test that view.message is set to the sent message."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["A", "B"]
        mock_destination = AsyncMock()
        mock_msg = AsyncMock()
        mock_destination.send.return_value = mock_msg

        await help_command._send_pages_to_destination(mock_destination)

        call_kwargs = mock_destination.send.call_args[1]
        view = call_kwargs["view"]
        assert view.message is mock_msg

    @pytest.mark.asyncio
    async def test_send_pages_to_destination_sends_to_correct_destination(self, help_command):
        """Test that pages are sent to the correct destination object."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["Test content"]

        destination_a = AsyncMock()
        destination_b = AsyncMock()

        await help_command._send_pages_to_destination(destination_a)

        destination_a.send.assert_called_once()
        destination_b.send.assert_not_called()


class TestSendBotHelp:
    """Test send_bot_help method with subcommand pages."""

    @pytest.mark.asyncio
    async def test_send_bot_help_adds_subcommand_pages_for_groups(self):
        """Verify groups get separate pages listing their subcommands."""
        cmd = CustomHelpCommand()
        cmd.context = MagicMock()
        cmd.context.author = MagicMock()
        cmd.context.author.send = AsyncMock()
        cmd.dm_help = False

        # Create a mock bot with a group command that has subcommands
        bot = MagicMock()
        bot.description = ""
        cmd.context.bot = bot

        # Create a cog
        mock_cog = MagicMock()
        mock_cog.qualified_name = "Config"

        # Create subcommands
        sub1 = MagicMock(spec=commands.Command)
        sub1.name = "botgame"
        sub1.short_doc = "Change bot game."
        sub1.cog = mock_cog
        sub1.hidden = False
        sub1.checks = []
        sub1.enabled = True

        sub2 = MagicMock(spec=commands.Command)
        sub2.name = "config"
        sub2.short_doc = "Bot configuration."
        sub2.cog = mock_cog
        sub2.hidden = False
        sub2.checks = []
        sub2.enabled = True

        # Create a group command with subcommands
        group_cmd = MagicMock(spec=commands.Group)
        group_cmd.name = "admin"
        group_cmd.short_doc = "Admin commands."
        group_cmd.cog = mock_cog
        group_cmd.hidden = False
        group_cmd.checks = []
        group_cmd.enabled = True
        group_cmd.qualified_name = "admin"
        group_cmd.commands = [sub1, sub2]

        # Create a regular (non-group) command
        regular_cmd = MagicMock(spec=commands.Command)
        regular_cmd.name = "roll"
        regular_cmd.short_doc = "Roll a die."
        regular_cmd.cog = mock_cog
        regular_cmd.hidden = False
        regular_cmd.checks = []
        regular_cmd.enabled = True

        bot.commands = [group_cmd, regular_cmd]

        # Mock send_pages to capture paginator state
        sent_pages = []

        async def capture_send_pages():
            sent_pages.extend(cmd.paginator.pages)

        cmd.send_pages = capture_send_pages

        # Mock filter_commands to return commands as-is
        async def mock_filter(cmds, *, sort=True, key=None):
            return sorted(cmds, key=lambda c: c.name) if sort else list(cmds)

        cmd.filter_commands = mock_filter

        mapping = {mock_cog: [group_cmd, regular_cmd], None: []}
        await cmd.send_bot_help(mapping)

        # Should have at least 2 pages: overview + admin subcommands
        assert len(sent_pages) >= 2

        # First page should have the overview with command names
        assert "admin" in sent_pages[0]
        assert "roll" in sent_pages[0]

        # Second page should have the group subcommands
        subcommand_page = sent_pages[1]
        assert "admin subcommands:" in subcommand_page
        assert "botgame" in subcommand_page
        assert "config" in subcommand_page

    @pytest.mark.asyncio
    async def test_send_bot_help_no_subcommand_page_for_empty_groups(self):
        """Verify groups with no subcommands don't get extra pages."""
        cmd = CustomHelpCommand()
        cmd.context = MagicMock()
        cmd.context.author = MagicMock()
        cmd.context.author.send = AsyncMock()
        cmd.dm_help = False

        bot = MagicMock()
        bot.description = ""
        cmd.context.bot = bot

        mock_cog = MagicMock()
        mock_cog.qualified_name = "Config"

        # Group with no subcommands
        group_cmd = MagicMock(spec=commands.Group)
        group_cmd.name = "admin"
        group_cmd.short_doc = "Admin commands."
        group_cmd.cog = mock_cog
        group_cmd.hidden = False
        group_cmd.checks = []
        group_cmd.enabled = True
        group_cmd.qualified_name = "admin"
        group_cmd.commands = []

        bot.commands = [group_cmd]

        sent_pages = []

        async def capture_send_pages():
            sent_pages.extend(cmd.paginator.pages)

        cmd.send_pages = capture_send_pages

        async def mock_filter(cmds, *, sort=True, key=None):
            return sorted(cmds, key=lambda c: c.name) if sort else list(cmds)

        cmd.filter_commands = mock_filter

        mapping = {mock_cog: [group_cmd], None: []}
        await cmd.send_bot_help(mapping)

        # Should have only the overview page, no subcommand pages
        assert len(sent_pages) == 1

    @pytest.mark.asyncio
    async def test_send_bot_help_regular_commands_no_extra_pages(self):
        """Verify non-group commands don't generate extra pages."""
        cmd = CustomHelpCommand()
        cmd.context = MagicMock()
        cmd.context.author = MagicMock()
        cmd.context.author.send = AsyncMock()
        cmd.dm_help = False

        bot = MagicMock()
        bot.description = ""
        cmd.context.bot = bot

        mock_cog = MagicMock()
        mock_cog.qualified_name = "General"

        regular_cmd = MagicMock(spec=commands.Command)
        regular_cmd.name = "ping"
        regular_cmd.short_doc = "Pong!"
        regular_cmd.cog = mock_cog
        regular_cmd.hidden = False
        regular_cmd.checks = []
        regular_cmd.enabled = True

        bot.commands = [regular_cmd]

        sent_pages = []

        async def capture_send_pages():
            sent_pages.extend(cmd.paginator.pages)

        cmd.send_pages = capture_send_pages

        async def mock_filter(cmds, *, sort=True, key=None):
            return sorted(cmds, key=lambda c: c.name) if sort else list(cmds)

        cmd.filter_commands = mock_filter

        mapping = {mock_cog: [regular_cmd], None: []}
        await cmd.send_bot_help(mapping)

        # Only overview page
        assert len(sent_pages) == 1
        assert "ping" in sent_pages[0]
