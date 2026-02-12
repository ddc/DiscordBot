"""Comprehensive tests for GW2 Worlds cog."""

import asyncio
import discord
import pytest
from src.gw2.cogs.worlds import GW2Worlds, _send_paginated_worlds_embed, setup, worlds, worlds_eu, worlds_na
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
        with patch('src.gw2.cogs.worlds.bot_utils.invoke_subcommand', new_callable=AsyncMock) as mock_invoke:
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
        ctx.bot.wait_for = AsyncMock()
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
        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
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

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
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

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[matches_data_na, matches_data_eu])
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
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

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[Exception("API timeout"), matches_data])
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
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

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[Exception("Error1"), Exception("Error2")])
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
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

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=Exception("Error"))
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    assert "..." in embed.footer.text

    @pytest.mark.asyncio
    async def test_worlds_na_calls_send_paginated(self, mock_ctx):
        """Test worlds_na calls _send_paginated_worlds_embed."""
        worlds_ids = [{"id": 1001, "name": "Anvil Rock", "population": "High"}]
        matches_data = {"id": "1-1"}

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    mock_send.assert_called_once_with(mock_ctx, mock_send.call_args[0][1])

    @pytest.mark.asyncio
    async def test_worlds_na_no_failed_worlds_no_footer(self, mock_ctx):
        """Test worlds_na does not add footer when no worlds fail."""
        worlds_ids = [{"id": 1001, "name": "Anvil Rock", "population": "High"}]
        matches_data = {"id": "1-2"}

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
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
        ctx.bot.wait_for = AsyncMock()
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
        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
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

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
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

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[matches_data_na, matches_data_eu])
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
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

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[Exception("API timeout"), matches_data])
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
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

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=Exception("Error"))
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
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

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=Exception("Error"))
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
                    await worlds_eu(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    assert "..." in embed.footer.text

    @pytest.mark.asyncio
    async def test_worlds_eu_tier_number_replaces_2_prefix(self, mock_ctx):
        """Test worlds_eu correctly replaces '2-' prefix for tier number."""
        worlds_ids = [{"id": 2002, "name": "Desolation", "population": "Full"}]
        matches_data = {"id": "2-4"}

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
                    await worlds_eu(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    assert "T4" in embed.fields[0].value


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
        ctx.bot.wait_for = AsyncMock()
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
        """Test that embed with >25 fields is paginated."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.bot.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)

        await _send_paginated_worlds_embed(mock_ctx, embed)
        # Should send the first page
        assert mock_ctx.send.called

    @pytest.mark.asyncio
    async def test_dm_channel_different_footer_text(self, mock_ctx):
        """Test that DM channel gets different footer text."""
        embed = self._make_embed_with_fields(30)
        mock_ctx.channel = MagicMock(spec=discord.DMChannel)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.bot.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)

        await _send_paginated_worlds_embed(mock_ctx, embed)
        sent_embed = mock_ctx.send.call_args[1]["embed"]
        assert "reactions won't disappear in DMs" in sent_embed.footer.text

    @pytest.mark.asyncio
    async def test_non_dm_channel_simple_footer(self, mock_ctx):
        """Test that non-DM channel gets simple page footer."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.id = 111
        mock_message.clear_reactions = AsyncMock()
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.bot.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)

        await _send_paginated_worlds_embed(mock_ctx, embed)
        sent_embed = mock_ctx.send.call_args[1]["embed"]
        assert "Page 1/2" in sent_embed.footer.text
        assert "reactions won't disappear" not in sent_embed.footer.text

    @pytest.mark.asyncio
    async def test_single_page_after_split_sends_without_reactions(self, mock_ctx):
        """Test that a single page after splitting sends without reactions."""
        # 25 fields exactly fits one page after split logic
        embed = self._make_embed_with_fields(25)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_ctx.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_pages_adds_reactions(self, mock_ctx):
        """Test that multiple pages adds left and right arrow reactions."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.id = 111
        mock_message.clear_reactions = AsyncMock()
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.bot.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)

        await _send_paginated_worlds_embed(mock_ctx, embed)
        # Check that both reactions were added
        calls = mock_message.add_reaction.call_args_list
        emojis = [call[0][0] for call in calls]
        assert "\u2b05\ufe0f" in emojis  # left arrow
        assert "\u27a1\ufe0f" in emojis  # right arrow

    @pytest.mark.asyncio
    async def test_reaction_add_fails_sends_first_page(self, mock_ctx):
        """Test that when reaction add fails, first page is sent without pagination."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "error"))
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)

        await _send_paginated_worlds_embed(mock_ctx, embed)
        # Should send twice: once for failed pagination, once for fallback
        assert mock_ctx.send.call_count == 2

    @pytest.mark.asyncio
    async def test_right_arrow_next_page(self, mock_ctx):
        """Test that right arrow reaction navigates to next page."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.edit = AsyncMock()
        mock_message.remove_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)

        # First call returns right arrow reaction, second call times out
        mock_reaction = MagicMock()
        mock_reaction.emoji = "\u27a1\ufe0f"
        mock_reaction.message = mock_message
        mock_user = MagicMock()
        mock_user.bot = False

        mock_ctx.bot.wait_for = AsyncMock(side_effect=[(mock_reaction, mock_user), asyncio.TimeoutError])

        await _send_paginated_worlds_embed(mock_ctx, embed)
        # Should have edited the message to show page 2
        mock_message.edit.assert_called_once()
        edited_embed = mock_message.edit.call_args[1]["embed"]
        assert "Page 2/2" in edited_embed.footer.text

    @pytest.mark.asyncio
    async def test_left_arrow_previous_page(self, mock_ctx):
        """Test that left arrow reaction navigates to previous page."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.edit = AsyncMock()
        mock_message.remove_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)

        # Navigate right first, then left
        mock_reaction_right = MagicMock()
        mock_reaction_right.emoji = "\u27a1\ufe0f"
        mock_reaction_right.message = mock_message

        mock_reaction_left = MagicMock()
        mock_reaction_left.emoji = "\u2b05\ufe0f"
        mock_reaction_left.message = mock_message

        mock_user = MagicMock()
        mock_user.bot = False

        mock_ctx.bot.wait_for = AsyncMock(
            side_effect=[
                (mock_reaction_right, mock_user),
                (mock_reaction_left, mock_user),
                asyncio.TimeoutError,
            ]
        )

        await _send_paginated_worlds_embed(mock_ctx, embed)
        # Should have edited the message twice (once right, once left)
        assert mock_message.edit.call_count == 2
        # Last edit should be back to page 1
        last_edited_embed = mock_message.edit.call_args_list[1][1]["embed"]
        assert "Page 1/2" in last_edited_embed.footer.text

    @pytest.mark.asyncio
    async def test_left_arrow_on_first_page_does_nothing(self, mock_ctx):
        """Test that left arrow on first page does not change page."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.edit = AsyncMock()
        mock_message.remove_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)

        mock_reaction_left = MagicMock()
        mock_reaction_left.emoji = "\u2b05\ufe0f"
        mock_reaction_left.message = mock_message

        mock_user = MagicMock()
        mock_user.bot = False

        mock_ctx.bot.wait_for = AsyncMock(side_effect=[(mock_reaction_left, mock_user), asyncio.TimeoutError])

        await _send_paginated_worlds_embed(mock_ctx, embed)
        # Should not edit message since already on first page
        mock_message.edit.assert_not_called()

    @pytest.mark.asyncio
    async def test_right_arrow_on_last_page_does_nothing(self, mock_ctx):
        """Test that right arrow on last page does not change page."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.edit = AsyncMock()
        mock_message.remove_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)

        mock_reaction_right = MagicMock()
        mock_reaction_right.emoji = "\u27a1\ufe0f"
        mock_reaction_right.message = mock_message

        mock_user = MagicMock()
        mock_user.bot = False

        # Go right twice (only first should work since only 2 pages)
        mock_ctx.bot.wait_for = AsyncMock(
            side_effect=[
                (mock_reaction_right, mock_user),
                (mock_reaction_right, mock_user),
                asyncio.TimeoutError,
            ]
        )

        await _send_paginated_worlds_embed(mock_ctx, embed)
        # Only one edit (the first right arrow)
        assert mock_message.edit.call_count == 1

    @pytest.mark.asyncio
    async def test_not_in_dm_removes_user_reaction(self, mock_ctx):
        """Test that in non-DM channel, user reaction is removed."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.edit = AsyncMock()
        mock_message.remove_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        # Non-DM channel (TextChannel)
        mock_ctx.channel = MagicMock(spec=discord.TextChannel)

        mock_reaction = MagicMock()
        mock_reaction.emoji = "\u27a1\ufe0f"
        mock_reaction.message = mock_message

        mock_user = MagicMock()
        mock_user.bot = False

        mock_ctx.bot.wait_for = AsyncMock(side_effect=[(mock_reaction, mock_user), asyncio.TimeoutError])

        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_message.remove_reaction.assert_called_once_with(mock_reaction.emoji, mock_user)

    @pytest.mark.asyncio
    async def test_in_dm_skips_reaction_removal(self, mock_ctx):
        """Test that in DM channel, user reaction is NOT removed."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.edit = AsyncMock()
        mock_message.remove_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.channel = MagicMock(spec=discord.DMChannel)

        mock_reaction = MagicMock()
        mock_reaction.emoji = "\u27a1\ufe0f"
        mock_reaction.message = mock_message

        mock_user = MagicMock()
        mock_user.bot = False

        mock_ctx.bot.wait_for = AsyncMock(side_effect=[(mock_reaction, mock_user), asyncio.TimeoutError])

        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_message.remove_reaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_timeout_error_silently_passes(self, mock_ctx):
        """Test that TimeoutError is handled silently."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.bot.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)

        # Should not raise
        await _send_paginated_worlds_embed(mock_ctx, embed)

    @pytest.mark.asyncio
    async def test_not_in_dm_after_timeout_clears_reactions(self, mock_ctx):
        """Test that reactions are cleared after timeout in non-DM channel."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.channel = MagicMock(spec=discord.TextChannel)
        mock_ctx.bot.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)

        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_message.clear_reactions.assert_called_once()

    @pytest.mark.asyncio
    async def test_in_dm_after_timeout_does_not_clear_reactions(self, mock_ctx):
        """Test that reactions are NOT cleared after timeout in DM channel."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.channel = MagicMock(spec=discord.DMChannel)
        mock_ctx.bot.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)

        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_message.clear_reactions.assert_not_called()

    @pytest.mark.asyncio
    async def test_forbidden_on_clear_reactions_silently_passes(self, mock_ctx):
        """Test that Forbidden error on clear_reactions is silently handled."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "Missing permissions"))
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.channel = MagicMock(spec=discord.TextChannel)
        mock_ctx.bot.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)

        # Should not raise
        await _send_paginated_worlds_embed(mock_ctx, embed)

    @pytest.mark.asyncio
    async def test_remove_reaction_forbidden_silently_passes(self, mock_ctx):
        """Test that Forbidden on remove_reaction is silently handled."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.edit = AsyncMock()
        mock_message.remove_reaction = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "Missing permissions"))
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.channel = MagicMock(spec=discord.TextChannel)

        mock_reaction = MagicMock()
        mock_reaction.emoji = "\u27a1\ufe0f"
        mock_reaction.message = mock_message

        mock_user = MagicMock()
        mock_user.bot = False

        mock_ctx.bot.wait_for = AsyncMock(side_effect=[(mock_reaction, mock_user), asyncio.TimeoutError])

        # Should not raise
        await _send_paginated_worlds_embed(mock_ctx, embed)

    @pytest.mark.asyncio
    async def test_embed_description_preserved_in_pages(self, mock_ctx):
        """Test that embed description is preserved in paginated pages."""
        embed = self._make_embed_with_fields(30, description="~~~~~ NA Servers ~~~~~")
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.bot.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)

        await _send_paginated_worlds_embed(mock_ctx, embed)
        sent_embed = mock_ctx.send.call_args[1]["embed"]
        assert sent_embed.description == "~~~~~ NA Servers ~~~~~"

    @pytest.mark.asyncio
    async def test_color_applied_to_all_pages(self, mock_ctx):
        """Test that color is applied to paginated pages."""
        embed = self._make_embed_with_fields(30)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.edit = AsyncMock()
        mock_message.remove_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)

        mock_reaction = MagicMock()
        mock_reaction.emoji = "\u27a1\ufe0f"
        mock_reaction.message = mock_message
        mock_user = MagicMock()
        mock_user.bot = False

        mock_ctx.bot.wait_for = AsyncMock(side_effect=[(mock_reaction, mock_user), asyncio.TimeoutError])

        await _send_paginated_worlds_embed(mock_ctx, embed)
        # First page
        first_page = mock_ctx.send.call_args[1]["embed"]
        assert first_page.color.value == 0x00FF00
        # Second page
        second_page = mock_message.edit.call_args[1]["embed"]
        assert second_page.color.value == 0x00FF00

    @pytest.mark.asyncio
    async def test_fields_split_correctly_across_pages(self, mock_ctx):
        """Test that fields are correctly distributed across pages."""
        embed = self._make_embed_with_fields(55)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.edit = AsyncMock()
        mock_message.remove_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)

        mock_reaction = MagicMock()
        mock_reaction.emoji = "\u27a1\ufe0f"
        mock_reaction.message = mock_message
        mock_user = MagicMock()
        mock_user.bot = False

        mock_ctx.bot.wait_for = AsyncMock(
            side_effect=[
                (mock_reaction, mock_user),
                (mock_reaction, mock_user),
                asyncio.TimeoutError,
            ]
        )

        await _send_paginated_worlds_embed(mock_ctx, embed)
        # First page should have 25 fields
        first_page = mock_ctx.send.call_args[1]["embed"]
        assert len(first_page.fields) == 25
        # Page 1/3
        assert "Page 1/3" in first_page.footer.text


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


class TestSendPaginatedWorldsEmbedEdgeCases:
    """Additional edge case tests for _send_paginated_worlds_embed (lines 154-155, 177)."""

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
        ctx.bot.wait_for = AsyncMock()
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
        """Test that when fields split into exactly one page, it sends without reactions (lines 153-155)."""
        # 26 fields -> split gives: page1=25, page2=1 -> 2 pages
        # But 25 fields -> split gives 1 page only since len<=25
        embed = self._make_embed_with_fields(25)
        await _send_paginated_worlds_embed(mock_ctx, embed)
        mock_ctx.send.assert_called_once()
        sent_embed = mock_ctx.send.call_args[1]["embed"]
        assert len(sent_embed.fields) == 25

    @pytest.mark.asyncio
    async def test_paginated_26_fields_creates_two_pages(self, mock_ctx):
        """Test pagination with 26 fields creates exactly 2 pages (lines 153-155)."""
        embed = self._make_embed_with_fields(26)
        mock_message = MagicMock()
        mock_message.add_reaction = AsyncMock()
        mock_message.clear_reactions = AsyncMock()
        mock_message.id = 111
        mock_ctx.send = AsyncMock(return_value=mock_message)
        mock_ctx.bot.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)

        await _send_paginated_worlds_embed(mock_ctx, embed)
        # Should send first page
        sent_embed = mock_ctx.send.call_args[1]["embed"]
        assert len(sent_embed.fields) == 25
        assert "Page 1/2" in sent_embed.footer.text

    @pytest.mark.asyncio
    async def test_worlds_na_exact_2001_boundary(self, mock_ctx):
        """Test worlds_na does not include world ID exactly at 2001 (line 177 equivalence)."""
        worlds_ids = [
            {"id": 2001, "name": "Boundary World", "population": "High"},
        ]
        # wid=2001 is NOT < 2001, so NA should NOT add it
        matches_data = {"id": "2-1"}

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
                    await worlds_na(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    # 2001 is NOT < 2001, so should not be added to NA embed
                    assert len(embed.fields) == 0

    @pytest.mark.asyncio
    async def test_worlds_eu_exact_2001_boundary(self, mock_ctx):
        """Test worlds_eu does not include world ID exactly at 2001 (line 177)."""
        worlds_ids = [
            {"id": 2001, "name": "Boundary World", "population": "High"},
        ]
        # wid=2001 is NOT > 2001, so EU should NOT add it
        matches_data = {"id": "2-1"}

        with patch('src.gw2.cogs.worlds.gw2_utils') as mock_utils:
            mock_utils.get_worlds_ids = AsyncMock(return_value=(True, worlds_ids))
            with patch('src.gw2.cogs.worlds.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=matches_data)
                with patch('src.gw2.cogs.worlds._send_paginated_worlds_embed', new_callable=AsyncMock) as mock_send:
                    await worlds_eu(mock_ctx)
                    embed = mock_send.call_args[0][1]
                    # 2001 is NOT > 2001, so should not be added to EU embed
                    assert len(embed.fields) == 0
