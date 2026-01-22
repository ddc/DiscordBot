"""Comprehensive tests for CustomHelpCommand class."""

import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import discord
import pytest
from discord.ext import commands

sys.modules['ddcDatabases'] = Mock()

from src.bot.tools.custom_help import CustomHelpCommand


class TestCustomHelpCommandInit:
    """Test CustomHelpCommand initialization."""

    def test_init_default_options(self):
        """Test initialization with default options sets paginator."""
        cmd = CustomHelpCommand()

        assert cmd.paginator is not None
        assert isinstance(cmd.paginator, commands.Paginator)
        assert cmd.paginator.prefix == '```'
        assert cmd.paginator.suffix == '```'
        assert cmd.paginator.max_size == 2000

    def test_init_custom_paginator(self):
        """Test initialization with custom paginator preserves it."""
        custom_paginator = commands.Paginator(prefix='---', suffix='---', max_size=1000)
        cmd = CustomHelpCommand(paginator=custom_paginator)

        assert cmd.paginator is custom_paginator
        assert cmd.paginator.prefix == '---'
        assert cmd.paginator.suffix == '---'
        assert cmd.paginator.max_size == 1000

    def test_init_custom_options_passed_to_parent(self):
        """Test that other options are passed to the parent class."""
        cmd = CustomHelpCommand(no_category='Uncategorized', sort_commands=False)

        assert cmd.no_category == 'Uncategorized'
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
        embed = call_kwargs['embed']
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
        embed = call_kwargs['embed']
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
        embed = call_kwargs['embed']
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
        embed = call_kwargs['embed']
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
        cmd.context.author.send = AsyncMock()
        return cmd

    @pytest.mark.asyncio
    async def test_send_pages_to_dm_single_page(self, help_command):
        """Test _send_pages_to_dm with a single page does not add page header."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["```\nHelp content here\n```"]

        await help_command._send_pages_to_dm()

        help_command.context.author.send.assert_called_once_with("```\nHelp content here\n```")

    @pytest.mark.asyncio
    async def test_send_pages_to_dm_multiple_pages(self, help_command):
        """Test _send_pages_to_dm with multiple pages adds page headers."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["```\nPage 1 content\n```", "```\nPage 2 content\n```"]

        await help_command._send_pages_to_dm()

        assert help_command.context.author.send.call_count == 2

        first_call_content = help_command.context.author.send.call_args_list[0][0][0]
        assert first_call_content == "**Page 1/2**\n```\nPage 1 content\n```"

        second_call_content = help_command.context.author.send.call_args_list[1][0][0]
        assert second_call_content == "**Page 2/2**\n```\nPage 2 content\n```"

    @pytest.mark.asyncio
    async def test_send_pages_to_dm_three_pages(self, help_command):
        """Test _send_pages_to_dm with three pages for complete pagination."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["Page A", "Page B", "Page C"]

        await help_command._send_pages_to_dm()

        assert help_command.context.author.send.call_count == 3

        expected_contents = [
            "**Page 1/3**\nPage A",
            "**Page 2/3**\nPage B",
            "**Page 3/3**\nPage C",
        ]

        for i, expected in enumerate(expected_contents):
            actual = help_command.context.author.send.call_args_list[i][0][0]
            assert actual == expected


class TestSendPagesToDestination:
    """Test _send_pages_to_destination method."""

    @pytest.fixture
    def help_command(self):
        """Create a CustomHelpCommand instance."""
        cmd = CustomHelpCommand()
        cmd.context = MagicMock()
        return cmd

    @pytest.mark.asyncio
    async def test_send_pages_to_destination_single_page(self, help_command):
        """Test _send_pages_to_destination with a single page does not add page header."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["```\nSingle page content\n```"]
        mock_destination = AsyncMock()

        await help_command._send_pages_to_destination(mock_destination)

        mock_destination.send.assert_called_once_with("```\nSingle page content\n```")

    @pytest.mark.asyncio
    async def test_send_pages_to_destination_multiple_pages(self, help_command):
        """Test _send_pages_to_destination with multiple pages adds page headers."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["```\nFirst page\n```", "```\nSecond page\n```"]
        mock_destination = AsyncMock()

        await help_command._send_pages_to_destination(mock_destination)

        assert mock_destination.send.call_count == 2

        first_call_content = mock_destination.send.call_args_list[0][0][0]
        assert first_call_content == "**Page 1/2**\n```\nFirst page\n```"

        second_call_content = mock_destination.send.call_args_list[1][0][0]
        assert second_call_content == "**Page 2/2**\n```\nSecond page\n```"

    @pytest.mark.asyncio
    async def test_send_pages_to_destination_three_pages(self, help_command):
        """Test _send_pages_to_destination with three pages for complete pagination."""
        help_command.paginator = MagicMock()
        help_command.paginator.pages = ["Content A", "Content B", "Content C"]
        mock_destination = AsyncMock()

        await help_command._send_pages_to_destination(mock_destination)

        assert mock_destination.send.call_count == 3

        expected_contents = [
            "**Page 1/3**\nContent A",
            "**Page 2/3**\nContent B",
            "**Page 3/3**\nContent C",
        ]

        for i, expected in enumerate(expected_contents):
            actual = mock_destination.send.call_args_list[i][0][0]
            assert actual == expected

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
