"""Comprehensive tests for GW2 Worlds cog."""

import discord
import pytest
from src.gw2.cogs.worlds import (
    EmbedPaginatorView,
    GW2Worlds,
    _send_paginated_worlds_embed,
    setup,
    worlds,
    worlds_eu,
    worlds_na,
)
from src.gw2.constants import gw2_messages
from unittest.mock import AsyncMock, MagicMock, patch


class TestGW2Worlds:
    """Test cases for the GW2Worlds cog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def gw2_worlds_cog(self, mock_bot):
        """Create a GW2Worlds cog instance."""
        return GW2Worlds(mock_bot)

    def test_gw2_worlds_initialization(self, mock_bot):
        """Test GW2Worlds cog initialization."""
        cog = GW2Worlds(mock_bot)
        assert cog.bot == mock_bot

    def test_gw2_worlds_inheritance(self, gw2_worlds_cog):
        """Test that GW2Worlds inherits from GuildWars2 properly."""
        from src.gw2.cogs.gw2 import GuildWars2

        assert isinstance(gw2_worlds_cog, GuildWars2)

    def test_gw2_worlds_docstring(self, gw2_worlds_cog):
        """Test that GW2Worlds has proper docstring."""
        assert GW2Worlds.__doc__ is not None
        assert "Guild Wars 2" in GW2Worlds.__doc__


class TestWorldsGroupCommand:
    """Test cases for the worlds group command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.prefix = "!"
        ctx.send = AsyncMock()
        ctx.invoked_subcommand = None
        return ctx

    @pytest.mark.asyncio
    async def test_worlds_calls_invoke_subcommand(self, mock_ctx):
        """Test that worlds group command calls invoke_subcommand."""
        with patch("src.gw2.cogs.worlds.bot_utils.invoke_subcommand", new_callable=AsyncMock) as mock_invoke:
            await worlds(mock_ctx)
            mock_invoke.assert_called_once_with(mock_ctx, "gw2 worlds")


class TestWorldsNACommand:
    """Test cases for the worlds_na command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.mention = "<@bot>"
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        ctx.author = ctx.message.author
        return ctx

    @pytest.mark.asyncio
    async def test_worlds_na_get_worlds_ids_returns_false(self, mock_ctx):
        """Test worlds_na returns None when get_worlds_ids returns False."""
        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(False, None))
            result = await worlds_na(mock_ctx)
            assert result is None
            mock_ctx.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_worlds_na_successful_with_na_worlds(self, mock_ctx):
        """Test worlds_na adds fields for NA worlds (wid < 2001)."""
        worlds_ids = [
            {"id": 1001, "name": "Anvil Rock", "population": "High"},
            {"id": 1002, "name": "Borlis Pass", "population": "Medium"},
        ]
        matches_data = {"id": "1-3"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    mock_send.assert_called_once()
                    embed = mock_send.call_args[0][1]
                    assert len(embed.fields) == 2
                    assert embed.fields[0].name == "Anvil Rock"
                    assert "T3" in embed.fields[0].value
                    assert "High" in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_worlds_na_skips_eu_worlds(self, mock_ctx):
        """Test worlds_na skips worlds with id > 2001 (EU worlds)."""
        worlds_ids = [
            {"id": 1001, "name": "Anvil Rock", "population": "High"},
            {"id": 2002, "name": "Desolation", "population": "Full"},
        ]
        matches_data_na = {"id": "1-2"}
        matches_data_eu = {"id": "2-1"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[matches_data_na, matches_data_eu])
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    # Only NA world should be added
                    assert len(embed.fields) == 1
                    assert embed.fields[0].name == "Anvil Rock"

    @pytest.mark.asyncio
    async def test_worlds_na_exception_on_world_logs_warning(self, mock_ctx):
        """Test worlds_na logs warning and continues when exception occurs."""
        worlds_ids = [
            {"id": 1001, "name": "Anvil Rock", "population": "High"},
            {"id": 1002, "name": "Borlis Pass", "population": "Medium"},
        ]
        matches_data = {"id": "1-3"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[Exception("API timeout"), matches_data])
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    mock_ctx.bot.log.warning.assert_called_once()
                    warning_msg = mock_ctx.bot.log.warning.call_args[0][0]
                    assert "Anvil Rock" in warning_msg
                    assert "1001" in warning_msg
                    # Second world should still be processed
                    embed = mock_send.call_args[0][1]
                    assert len(embed.fields) == 1
                    assert embed.fields[0].name == "Borlis Pass"

    @pytest.mark.asyncio
    async def test_worlds_na_failed_worlds_adds_footer(self, mock_ctx):
        """Test worlds_na adds footer when some worlds fail."""
        worlds_ids = [
            {"id": 1001, "name": "Anvil Rock", "population": "High"},
            {"id": 1002, "name": "Borlis Pass", "population": "Medium"},
        ]

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[Exception("Error1"), Exception("Error2")])
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    assert embed.footer is not None
                    assert "Failed to load" in embed.footer.text
                    assert "Anvil Rock" in embed.footer.text

    @pytest.mark.asyncio
    async def test_worlds_na_failed_worlds_footer_truncates_at_3(self, mock_ctx):
        """Test worlds_na footer truncates to 3 failed worlds with ellipsis."""
        worlds_ids = [
            {"id": 1001, "name": "World1", "population": "High"},
            {"id": 1002, "name": "World2", "population": "Medium"},
            {"id": 1003, "name": "World3", "population": "Low"},
            {"id": 1004, "name": "World4", "population": "VeryHigh"},
        ]

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=Exception("Error"))
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    assert "..." in embed.footer.text

    @pytest.mark.asyncio
    async def test_worlds_na_calls_send_paginated(self, mock_ctx):
        """Test worlds_na calls _send_paginated_worlds_embed."""
        worlds_ids = [{"id": 1001, "name": "Anvil Rock", "population": "High"}]
        matches_data = {"id": "1-1"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    mock_send.assert_called_once_with(mock_ctx, mock_send.call_args[0][1])

    @pytest.mark.asyncio
    async def test_worlds_na_no_failed_worlds_no_footer(self, mock_ctx):
        """Test worlds_na does not add footer when no worlds fail."""
        worlds_ids = [{"id": 1001, "name": "Anvil Rock", "population": "High"}]
        matches_data = {"id": "1-2"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    assert embed.footer.text is None


class TestWorldsEUCommand:
    """Test cases for the worlds_eu command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.mention = "<@bot>"
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        ctx.author = ctx.message.author
        return ctx

    @pytest.mark.asyncio
    async def test_worlds_eu_get_worlds_ids_returns_false(self, mock_ctx):
        """Test worlds_eu returns None when get_worlds_ids returns False."""
        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(False, None))
            result = await worlds_eu(mock_ctx)
            assert result is None
            mock_ctx.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_worlds_eu_successful_with_eu_worlds(self, mock_ctx):
        """Test worlds_eu adds fields for EU worlds (wid > 2001)."""
        worlds_ids = [
            {"id": 2002, "name": "Desolation", "population": "Full"},
            {"id": 2003, "name": "Gandara", "population": "VeryHigh"},
        ]
        matches_data = {"id": "2-1"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_eu(mock_ctx)
                    mock_send.assert_called_once()
                    embed = mock_send.call_args[0][1]
                    assert len(embed.fields) == 2
                    assert embed.fields[0].name == "Desolation"
                    assert "T1" in embed.fields[0].value
                    assert "Full" in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_worlds_eu_skips_na_worlds(self, mock_ctx):
        """Test worlds_eu skips worlds with id < 2001 (NA worlds)."""
        worlds_ids = [
            {"id": 1001, "name": "Anvil Rock", "population": "High"},
            {"id": 2002, "name": "Desolation", "population": "Full"},
        ]
        matches_data_na = {"id": "1-2"}
        matches_data_eu = {"id": "2-1"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[matches_data_na, matches_data_eu])
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_eu(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    # Only EU world should be added
                    assert len(embed.fields) == 1
                    assert embed.fields[0].name == "Desolation"

    @pytest.mark.asyncio
    async def test_worlds_eu_exception_on_world_logs_warning(self, mock_ctx):
        """Test worlds_eu logs warning and continues when exception occurs."""
        worlds_ids = [
            {"id": 2002, "name": "Desolation", "population": "Full"},
            {"id": 2003, "name": "Gandara", "population": "VeryHigh"},
        ]
        matches_data = {"id": "2-2"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[Exception("API timeout"), matches_data])
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_eu(mock_ctx)
                    mock_ctx.bot.log.warning.assert_called_once()
                    warning_msg = mock_ctx.bot.log.warning.call_args[0][0]
                    assert "Desolation" in warning_msg
                    assert "2002" in warning_msg
                    embed = mock_send.call_args[0][1]
                    assert len(embed.fields) == 1
                    assert embed.fields[0].name == "Gandara"

    @pytest.mark.asyncio
    async def test_worlds_eu_failed_worlds_adds_footer(self, mock_ctx):
        """Test worlds_eu adds footer when some worlds fail."""
        worlds_ids = [
            {"id": 2002, "name": "Desolation", "population": "Full"},
            {"id": 2003, "name": "Gandara", "population": "VeryHigh"},
        ]

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=Exception("Error"))
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_eu(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    assert embed.footer is not None
                    assert "Failed to load" in embed.footer.text
                    assert "Desolation" in embed.footer.text

    @pytest.mark.asyncio
    async def test_worlds_eu_failed_worlds_footer_truncates_at_3(self, mock_ctx):
        """Test worlds_eu footer truncates to 3 failed worlds with ellipsis."""
        worlds_ids = [
            {"id": 2002, "name": "World1", "population": "High"},
            {"id": 2003, "name": "World2", "population": "Medium"},
            {"id": 2004, "name": "World3", "population": "Low"},
            {"id": 2005, "name": "World4", "population": "VeryHigh"},
        ]

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=Exception("Error"))
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_eu(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    assert "..." in embed.footer.text

    @pytest.mark.asyncio
    async def test_worlds_eu_tier_number_replaces_2_prefix(self, mock_ctx):
        """Test worlds_eu correctly replaces '2-' prefix for tier number."""
        worlds_ids = [{"id": 2002, "name": "Desolation", "population": "Full"}]
        matches_data = {"id": "2-4"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_eu(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    assert "T4" in embed.fields[0].value


class TestEmbedPaginatorView:
    """Test cases for the EmbedPaginatorView class."""

    def _make_embed_pages(self, count):
        """Helper to create a list of embed pages."""
        pages = []
        for i in range(count):
            embed = discord.Embed(description=f"Page {i + 1}", color=0x00FF00)
            embed.set_footer(text=f"Page {i + 1}/{count}")
            pages.append(embed)
        return pages

    @pytest.mark.asyncio
    async def test_initial_state(self):
        """Test view starts on page 0 with correct button states."""
        pages = self._make_embed_pages(3)
        view = EmbedPaginatorView(pages, author_id=123)

        assert view.current_page == 0
        assert view.previous_button.disabled is True
        assert view.next_button.disabled is False
        assert view.page_indicator.label == "1/3"
        assert view.page_indicator.disabled is True

    @pytest.mark.asyncio
    async def test_update_buttons_middle_page(self):
        """Test buttons state on middle page: both enabled."""
        pages = self._make_embed_pages(3)
        view = EmbedPaginatorView(pages, author_id=1)
        view.current_page = 1
        view._update_buttons()

        assert view.previous_button.disabled is False
        assert view.next_button.disabled is False
        assert view.page_indicator.label == "2/3"

    @pytest.mark.asyncio
    async def test_update_buttons_last_page(self):
        """Test buttons state on last page: next disabled."""
        pages = self._make_embed_pages(3)
        view = EmbedPaginatorView(pages, author_id=1)
        view.current_page = 2
        view._update_buttons()

        assert view.previous_button.disabled is False
        assert view.next_button.disabled is True
        assert view.page_indicator.label == "3/3"

    @pytest.mark.asyncio
    async def test_next_button_advances_page(self):
        """Test clicking next button advances current_page and edits embed."""
        pages = self._make_embed_pages(3)
        view = EmbedPaginatorView(pages, author_id=42)
        interaction = MagicMock()
        interaction.user.id = 42
        interaction.response = AsyncMock()

        await view.next_button.callback(interaction)

        assert view.current_page == 1
        interaction.response.edit_message.assert_called_once()
        call_kwargs = interaction.response.edit_message.call_args[1]
        assert call_kwargs["embed"] is pages[1]

    @pytest.mark.asyncio
    async def test_previous_button_goes_back(self):
        """Test clicking previous button goes back a page."""
        pages = self._make_embed_pages(3)
        view = EmbedPaginatorView(pages, author_id=42)
        view.current_page = 2
        view._update_buttons()
        interaction = MagicMock()
        interaction.user.id = 42
        interaction.response = AsyncMock()

        await view.previous_button.callback(interaction)

        assert view.current_page == 1
        interaction.response.edit_message.assert_called_once()
        call_kwargs = interaction.response.edit_message.call_args[1]
        assert call_kwargs["embed"] is pages[1]

    @pytest.mark.asyncio
    async def test_next_button_rejects_non_author(self):
        """Test non-author clicking next gets ephemeral rejection."""
        pages = self._make_embed_pages(2)
        view = EmbedPaginatorView(pages, author_id=42)
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
        pages = self._make_embed_pages(2)
        view = EmbedPaginatorView(pages, author_id=42)
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
        pages = self._make_embed_pages(2)
        view = EmbedPaginatorView(pages, author_id=1)
        interaction = MagicMock()
        interaction.response = AsyncMock()

        await view.page_indicator.callback(interaction)

        interaction.response.defer.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_is_none(self):
        """Test view timeout is None (buttons never expire)."""
        pages = self._make_embed_pages(2)
        view = EmbedPaginatorView(pages, author_id=1)
        assert view.timeout is None

    @pytest.mark.asyncio
    async def test_pages_stored(self):
        """Test pages list is stored correctly."""
        pages = self._make_embed_pages(2)
        view = EmbedPaginatorView(pages, author_id=1)
        assert view.pages is pages

    @pytest.mark.asyncio
    async def test_author_id_stored(self):
        """Test author_id is stored correctly."""
        pages = self._make_embed_pages(2)
        view = EmbedPaginatorView(pages, author_id=12345)
        assert view.author_id == 12345


class TestSendPaginatedWorldsEmbed:
    """Test cases for the _send_paginated_worlds_embed function."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.mention = "<@bot>"
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        ctx.author = ctx.message.author
        return ctx

    def _make_embed_with_fields(self, num_fields, description="Test"):
        """Helper to create an embed with a given number of fields."""
        embed = discord.Embed(description=description)
        for i in range(num_fields):
            embed.add_field(name=f"World {i}", value=f"Value {i}")
        return embed

    @pytest.mark.asyncio
    async def test_sends_single_embed_when_25_or_fewer_fields(self, mock_ctx):
        """Test that embed with <=25 fields is sent as a single embed."""
        embed = self._make_embed_with_fields(20)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_ctx.send.assert_called_once()
        sent_embed = mock_ctx.send.call_args[1]["embed"]
        assert sent_embed.color.value == 0x00FF00
        assert len(sent_embed.fields) == 20

    @pytest.mark.asyncio
    async def test_sends_single_embed_exactly_25_fields(self, mock_ctx):
        """Test that embed with exactly 25 fields is sent without pagination."""
        embed = self._make_embed_with_fields(25)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_ctx.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_paginates_when_more_than_25_fields(self, mock_ctx):
        """Test that embed with >25 fields sends first page with view."""
        embed = self._make_embed_with_fields(30)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_ctx.send.assert_called_once()
        call_kwargs = mock_ctx.send.call_args[1]
        assert isinstance(call_kwargs["view"], EmbedPaginatorView)
        sent_embed = call_kwargs["embed"]
        assert len(sent_embed.fields) == 25

    @pytest.mark.asyncio
    async def test_paginated_footer_shows_page_numbers(self, mock_ctx):
        """Test that paginated embeds have correct page footer."""
        embed = self._make_embed_with_fields(30)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        call_kwargs = mock_ctx.send.call_args[1]
        sent_embed = call_kwargs["embed"]
        assert "Page 1/2" in sent_embed.footer.text

    @pytest.mark.asyncio
    async def test_paginated_view_has_second_page(self, mock_ctx):
        """Test that the view contains both pages with correct fields."""
        embed = self._make_embed_with_fields(30)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        call_kwargs = mock_ctx.send.call_args[1]
        view = call_kwargs["view"]
        assert len(view.pages) == 2
        assert len(view.pages[0].fields) == 25
        assert len(view.pages[1].fields) == 5
        assert "Page 2/2" in view.pages[1].footer.text

    @pytest.mark.asyncio
    async def test_single_page_after_split_sends_without_view(self, mock_ctx):
        """Test that a single page after splitting sends without view."""
        embed = self._make_embed_with_fields(25)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_ctx.send.assert_called_once()
        call_kwargs = mock_ctx.send.call_args[1]
        assert "view" not in call_kwargs

    @pytest.mark.asyncio
    async def test_embed_description_preserved_in_pages(self, mock_ctx):
        """Test that embed description is preserved in paginated pages."""
        embed = self._make_embed_with_fields(30, description=gw2_messages.NA_SERVERS_TITLE)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        call_kwargs = mock_ctx.send.call_args[1]
        sent_embed = call_kwargs["embed"]
        assert sent_embed.description == gw2_messages.NA_SERVERS_TITLE

    @pytest.mark.asyncio
    async def test_color_applied_to_all_pages(self, mock_ctx):
        """Test that color is applied to paginated pages."""
        embed = self._make_embed_with_fields(30)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        call_kwargs = mock_ctx.send.call_args[1]
        view = call_kwargs["view"]
        for page in view.pages:
            assert page.color.value == 0x00FF00

    @pytest.mark.asyncio
    async def test_fields_split_correctly_across_pages(self, mock_ctx):
        """Test that fields are correctly distributed across pages."""
        embed = self._make_embed_with_fields(55)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        call_kwargs = mock_ctx.send.call_args[1]
        view = call_kwargs["view"]
        assert len(view.pages) == 3
        assert len(view.pages[0].fields) == 25
        assert len(view.pages[1].fields) == 25
        assert len(view.pages[2].fields) == 5
        assert "Page 1/3" in view.pages[0].footer.text

    @pytest.mark.asyncio
    async def test_view_message_reference_is_set(self, mock_ctx):
        """Test that view.message is set to the sent message."""
        embed = self._make_embed_with_fields(30)
        mock_msg = AsyncMock()
        mock_ctx.send.return_value = mock_msg
        await _send_paginated_worlds_embed(mock_ctx, embed)
        call_kwargs = mock_ctx.send.call_args[1]
        view = call_kwargs["view"]
        assert view.message is mock_msg

    @pytest.mark.asyncio
    async def test_view_author_id_matches_ctx_author(self, mock_ctx):
        """Test that view.author_id matches ctx.author.id."""
        embed = self._make_embed_with_fields(30)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        call_kwargs = mock_ctx.send.call_args[1]
        view = call_kwargs["view"]
        assert view.author_id == 12345


class TestSendPaginatedWorldsEmbedEdgeCases:
    """Additional edge case tests for _send_paginated_worlds_embed."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.mention = "<@bot>"
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        ctx.author = ctx.message.author
        return ctx

    def _make_embed_with_fields(self, num_fields, description="Test"):
        """Helper to create an embed with a given number of fields."""
        embed = discord.Embed(description=description)
        for i in range(num_fields):
            embed.add_field(name=f"World {i}", value=f"Value {i}")
        return embed

    @pytest.mark.asyncio
    async def test_single_page_after_split_sends_directly(self, mock_ctx):
        """Test that when fields fit in one page, it sends without view."""
        embed = self._make_embed_with_fields(25)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_ctx.send.assert_called_once()
        sent_embed = mock_ctx.send.call_args[1]["embed"]
        assert len(sent_embed.fields) == 25

    @pytest.mark.asyncio
    async def test_paginated_26_fields_creates_two_pages(self, mock_ctx):
        """Test pagination with 26 fields creates exactly 2 pages."""
        embed = self._make_embed_with_fields(26)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        call_kwargs = mock_ctx.send.call_args[1]
        view = call_kwargs["view"]
        assert len(view.pages) == 2
        assert len(view.pages[0].fields) == 25
        assert len(view.pages[1].fields) == 1
        assert "Page 1/2" in view.pages[0].footer.text

    @pytest.mark.asyncio
    async def test_worlds_na_exact_2001_boundary(self, mock_ctx):
        """Test worlds_na does not include world ID exactly at 2001."""
        worlds_ids = [
            {"id": 2001, "name": "Boundary World", "population": "High"},
        ]
        # wid=2001 is NOT < 2001, so NA should NOT add it
        matches_data = {"id": "2-1"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    # 2001 is NOT < 2001, so should not be added to NA embed
                    assert len(embed.fields) == 0

    @pytest.mark.asyncio
    async def test_worlds_eu_exact_2001_boundary(self, mock_ctx):
        """Test worlds_eu does not include world ID exactly at 2001."""
        worlds_ids = [
            {"id": 2001, "name": "Boundary World", "population": "High"},
        ]
        # wid=2001 is NOT > 2001, so EU should NOT add it
        matches_data = {"id": "2-1"}

        with patch("src.gw2.cogs.worlds.gw2_utils") as mock_utils:
            mock_utils.send_progress_embed = AsyncMock(return_value=AsyncMock())
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch("src.gw2.cogs.worlds.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch("src.gw2.cogs.worlds._send_paginated_worlds_embed", new_callable=AsyncMock) as mock_send:
                    await worlds_eu(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    # 2001 is NOT > 2001, so should not be added to EU embed
                    assert len(embed.fields) == 0


class TestWorldsSetup:
    """Test cases for worlds cog setup."""

    @pytest.mark.asyncio
    async def test_setup_function_exists(self):
        """Test that setup function exists and is callable."""
        assert callable(setup)

    @pytest.mark.asyncio
    async def test_setup_removes_existing_gw2_command(self):
        """Test that setup removes existing gw2 command."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        await setup(mock_bot)
        mock_bot.remove_command.assert_called_once_with("gw2")

    @pytest.mark.asyncio
    async def test_setup_adds_cog(self):
        """Test that setup adds the GW2Worlds cog."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        await setup(mock_bot)
        mock_bot.add_cog.assert_called_once()
        cog_instance = mock_bot.add_cog.call_args[0][0]
        assert isinstance(cog_instance, GW2Worlds)
