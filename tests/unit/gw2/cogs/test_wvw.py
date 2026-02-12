"""Comprehensive tests for GW2 WvW cog."""

import discord
import pytest
from src.gw2.cogs.wvw import (
    GW2WvW,
    _get_kdr_embed_values,
    _get_map_names_embed_values,
    _get_match_embed_values,
    setup,
)
from src.gw2.tools.gw2_exceptions import APIKeyError
from unittest.mock import AsyncMock, MagicMock, patch


class TestGW2WvW:
    """Test cases for the GW2WvW cog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def gw2_wvw_cog(self, mock_bot):
        """Create a GW2WvW cog instance."""
        return GW2WvW(mock_bot)

    def test_gw2_wvw_initialization(self, mock_bot):
        """Test GW2WvW cog initialization."""
        cog = GW2WvW(mock_bot)
        assert cog.bot == mock_bot

    def test_gw2_wvw_inheritance(self, gw2_wvw_cog):
        """Test that GW2WvW inherits from GuildWars2 properly."""
        from src.gw2.cogs.gw2 import GuildWars2

        assert isinstance(gw2_wvw_cog, GuildWars2)


class TestInfoCommand:
    """Test cases for the wvw info command."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.author.mention = "<@12345>"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def sample_matches_data(self):
        """Create sample WvW matches data."""
        return {
            "id": "1-3",
            "scores": {"red": 150000, "green": 120000, "blue": 100000},
            "victory_points": {"red": 50, "green": 40, "blue": 30},
            "all_worlds": {
                "red": [1001, 1002],
                "green": [1003, 1004],
                "blue": [1005, 1006],
            },
            "worlds": {"red": 1001, "green": 1003, "blue": 1005},
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
            "skirmishes": [
                {"scores": {"red": 500, "green": 400, "blue": 300}},
                {"scores": {"red": 600, "green": 500, "blue": 400}},
            ],
            "maps": [
                {
                    "objectives": [
                        {"owner": "Red", "points_tick": 5},
                        {"owner": "Green", "points_tick": 3},
                        {"owner": "Blue", "points_tick": 2},
                    ],
                    "kills": {"red": 1000, "green": 800, "blue": 600},
                    "deaths": {"red": 800, "green": 700, "blue": 500},
                },
                {
                    "objectives": [
                        {"owner": "Red", "points_tick": 4},
                        {"owner": "Green", "points_tick": 6},
                    ],
                    "kills": {"red": 1200, "green": 900, "blue": 700},
                    "deaths": {"red": 1000, "green": 800, "blue": 600},
                },
                {
                    "objectives": [
                        {"owner": "Blue", "points_tick": 7},
                        {"owner": "Red", "points_tick": 3},
                    ],
                    "kills": {"red": 1400, "green": 1100, "blue": 800},
                    "deaths": {"red": 1100, "green": 900, "blue": 700},
                },
                {
                    "objectives": [
                        {"owner": "Green", "points_tick": 5},
                        {"owner": "Blue", "points_tick": 4},
                    ],
                    "kills": {"red": 1500, "green": 1200, "blue": 900},
                    "deaths": {"red": 1200, "green": 1000, "blue": 800},
                },
            ],
        }

    @pytest.fixture
    def sample_worldinfo_data(self):
        """Create sample world info data."""
        return {
            "id": 1001,
            "name": "Anvil Rock",
            "population": "High",
        }

    @pytest.mark.asyncio
    async def test_info_no_world_no_api_key(self, mock_bot, mock_ctx):
        """Test info command with no world and no API key."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=None)

            with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                with patch('src.gw2.cogs.wvw.Gw2Client'):
                    await cog.info.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "You dont have an API key registered" in error_msg

    @pytest.mark.asyncio
    async def test_info_no_world_api_key_exists(self, mock_bot, mock_ctx, sample_matches_data, sample_worldinfo_data):
        """Test info command with no world but API key exists, uses account's world."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        api_key_data = [{"key": "test-api-key-12345"}]

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        {"world": 1001},  # account call
                        sample_matches_data,  # wvw/matches call
                        sample_worldinfo_data,  # worlds call
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    await cog.info.callback(cog, mock_ctx, world=None)
                    mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_info_no_world_api_key_error(self, mock_bot, mock_ctx):
        """Test info command with no world and APIKeyError."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        api_key_data = [{"key": "test-api-key-12345"}]

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=APIKeyError(mock_ctx.bot, "Invalid key"))

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.info.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "You dont have an API key registered" in error_msg

    @pytest.mark.asyncio
    async def test_info_no_world_generic_exception(self, mock_bot, mock_ctx):
        """Test info command with no world and generic exception."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        api_key_data = [{"key": "test-api-key-12345"}]

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                error = Exception("Something went wrong")
                mock_client_instance.call_api = AsyncMock(side_effect=error)

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.info.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once_with(mock_ctx, error)
                    mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_info_world_given_calls_get_world_id(
        self, mock_bot, mock_ctx, sample_matches_data, sample_worldinfo_data
    ):
        """Test info command with world given uses get_world_id."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_matches_data,
                        sample_worldinfo_data,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                    mock_get_wid.assert_called_once_with(mock_ctx.bot, "Anvil Rock")
                    mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_info_wid_is_none(self, mock_bot, mock_ctx):
        """Test info command when wid is None."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = None

            with patch('src.gw2.cogs.wvw.Gw2Client'):
                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.info.callback(cog, mock_ctx, world="InvalidWorld")

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "Invalid world name" in error_msg
                    assert "InvalidWorld" in error_msg

    @pytest.mark.asyncio
    async def test_info_api_call_fails(self, mock_bot, mock_ctx):
        """Test info command when API calls for matches/worldinfo fail."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                error = Exception("API failure")
                mock_client_instance.call_api = AsyncMock(side_effect=error)

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                    mock_error.assert_called_once_with(mock_ctx, error)
                    mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_info_world_color_not_found(self, mock_bot, mock_ctx, sample_worldinfo_data):
        """Test info command when world color is not found."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        matches_data = {
            "id": "1-3",
            "all_worlds": {
                "red": [2001, 2002],
                "green": [2003, 2004],
                "blue": [2005, 2006],
            },
        }

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001  # Not in any of the all_worlds lists

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        matches_data,
                        sample_worldinfo_data,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "Could not resolve world's color" in error_msg

    @pytest.mark.asyncio
    async def test_info_na_tier(self, mock_bot, mock_ctx, sample_matches_data, sample_worldinfo_data):
        """Test info command with NA tier (wid < 2001)."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001  # NA world

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_matches_data,
                        sample_worldinfo_data,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                    embed = mock_send.call_args[0][1]
                    assert "North America Tier" in embed.description

    @pytest.mark.asyncio
    async def test_info_eu_tier(self, mock_bot, mock_ctx, sample_worldinfo_data):
        """Test info command with EU tier (wid >= 2001)."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        eu_matches_data = {
            "id": "2-5",
            "scores": {"red": 150000, "green": 120000, "blue": 100000},
            "victory_points": {"red": 50, "green": 40, "blue": 30},
            "all_worlds": {
                "red": [2001, 2002],
                "green": [2003, 2004],
                "blue": [2005, 2006],
            },
            "worlds": {"red": 2001, "green": 2003, "blue": 2005},
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
            "skirmishes": [
                {"scores": {"red": 600, "green": 500, "blue": 400}},
            ],
            "maps": [
                {"objectives": [{"owner": "Red", "points_tick": 5}]},
            ],
        }

        eu_worldinfo = {
            "id": 2001,
            "name": "Desolation",
            "population": "Full",
        }

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 2001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        eu_matches_data,
                        eu_worldinfo,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    await cog.info.callback(cog, mock_ctx, world="Desolation")

                    embed = mock_send.call_args[0][1]
                    assert "Europe Tier" in embed.description

    @pytest.mark.asyncio
    async def test_info_red_world_color(self, mock_bot, mock_ctx, sample_matches_data, sample_worldinfo_data):
        """Test info command with red world color."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001  # In red all_worlds

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_matches_data,
                        sample_worldinfo_data,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                    embed = mock_send.call_args[0][1]
                    assert embed.color == discord.Color.red()

    @pytest.mark.asyncio
    async def test_info_green_world_color(self, mock_bot, mock_ctx, sample_matches_data, sample_worldinfo_data):
        """Test info command with green world color."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1003  # In green all_worlds

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_matches_data,
                        sample_worldinfo_data,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    await cog.info.callback(cog, mock_ctx, world="Some World")

                    embed = mock_send.call_args[0][1]
                    assert embed.color == discord.Color.green()

    @pytest.mark.asyncio
    async def test_info_blue_world_color(self, mock_bot, mock_ctx, sample_matches_data, sample_worldinfo_data):
        """Test info command with blue world color."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1005  # In blue all_worlds

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_matches_data,
                        sample_worldinfo_data,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    await cog.info.callback(cog, mock_ctx, world="Some World")

                    embed = mock_send.call_args[0][1]
                    assert embed.color == discord.Color.blue()

    @pytest.mark.asyncio
    async def test_info_population_veryhigh(self, mock_bot, mock_ctx, sample_matches_data):
        """Test info command with VeryHigh population is converted to 'Very high'."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        worldinfo_veryhigh = {
            "id": 1001,
            "name": "Anvil Rock",
            "population": "VeryHigh",
        }

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_matches_data,
                        worldinfo_veryhigh,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    with patch('src.gw2.cogs.wvw.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                        await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                        embed = mock_send.call_args[0][1]
                        # Check that the Population field has "Very high"
                        pop_field = next(f for f in embed.fields if f.name == "Population")
                        assert "Very high" in pop_field.value

    @pytest.mark.asyncio
    async def test_info_kills_zero_kd(self, mock_bot, mock_ctx, sample_worldinfo_data):
        """Test info command when kills=0, kd should be '0.0'."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        matches_zero_kills = {
            "id": "1-3",
            "scores": {"red": 150000, "green": 120000, "blue": 100000},
            "victory_points": {"red": 50, "green": 40, "blue": 30},
            "all_worlds": {
                "red": [1001, 1002],
                "green": [1003, 1004],
                "blue": [1005, 1006],
            },
            "kills": {"red": 0, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
            "skirmishes": [
                {"scores": {"red": 600, "green": 500, "blue": 400}},
            ],
            "maps": [
                {"objectives": [{"owner": "Red", "points_tick": 5}]},
            ],
        }

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        matches_zero_kills,
                        sample_worldinfo_data,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    with patch('src.gw2.cogs.wvw.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                        await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                        embed = mock_send.call_args[0][1]
                        kd_field = next(f for f in embed.fields if f.name == "K/D ratio")
                        assert "0.0" in kd_field.value

    @pytest.mark.asyncio
    async def test_info_deaths_zero_kd(self, mock_bot, mock_ctx, sample_worldinfo_data):
        """Test info command when deaths=0, kd should be '0.0'."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        matches_zero_deaths = {
            "id": "1-3",
            "scores": {"red": 150000, "green": 120000, "blue": 100000},
            "victory_points": {"red": 50, "green": 40, "blue": 30},
            "all_worlds": {
                "red": [1001, 1002],
                "green": [1003, 1004],
                "blue": [1005, 1006],
            },
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 0, "green": 3500, "blue": 2500},
            "skirmishes": [
                {"scores": {"red": 600, "green": 500, "blue": 400}},
            ],
            "maps": [
                {"objectives": [{"owner": "Red", "points_tick": 5}]},
            ],
        }

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        matches_zero_deaths,
                        sample_worldinfo_data,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    with patch('src.gw2.cogs.wvw.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                        await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                        embed = mock_send.call_args[0][1]
                        kd_field = next(f for f in embed.fields if f.name == "K/D ratio")
                        assert "0.0" in kd_field.value

    @pytest.mark.asyncio
    async def test_info_normal_kd_calculation(self, mock_bot, mock_ctx, sample_matches_data, sample_worldinfo_data):
        """Test info command with normal kd calculation."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001  # red world

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_matches_data,
                        sample_worldinfo_data,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    with patch('src.gw2.cogs.wvw.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                        await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                        embed = mock_send.call_args[0][1]
                        kd_field = next(f for f in embed.fields if f.name == "K/D ratio")
                        expected_kd = round(5000 / 4000, 3)
                        assert str(expected_kd) in kd_field.value

    @pytest.mark.asyncio
    async def test_info_successful_embed_sent(self, mock_bot, mock_ctx, sample_matches_data, sample_worldinfo_data):
        """Test info command sends successful embed with all fields."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_matches_data,
                        sample_worldinfo_data,
                    ]
                )

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    with patch('src.gw2.cogs.wvw.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                        await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                        mock_send.assert_called_once()
                        embed = mock_send.call_args[0][1]
                        assert embed.title == "Anvil Rock"
                        field_names = [f.name for f in embed.fields]
                        assert "Score" in field_names
                        assert "Points per tick" in field_names
                        assert "Victory Points" in field_names
                        assert "Skirmish" in field_names
                        assert "Kills" in field_names
                        assert "Deaths" in field_names
                        assert "K/D ratio" in field_names
                        assert "Population" in field_names


class TestMatchCommand:
    """Test cases for the wvw match command."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.author.mention = "<@12345>"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def sample_matches_data(self):
        """Create sample WvW matches data."""
        return {
            "id": "1-3",
            "scores": {"red": 150000, "green": 120000, "blue": 100000},
            "victory_points": {"red": 50, "green": 40, "blue": 30},
            "all_worlds": {
                "red": [1001, 1002],
                "green": [1003, 1004],
                "blue": [1005, 1006],
            },
            "worlds": {"red": 1001, "green": 1003, "blue": 1005},
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
            "skirmishes": [
                {"scores": {"red": 600, "green": 500, "blue": 400}},
            ],
            "maps": [
                {
                    "objectives": [
                        {"owner": "Red", "points_tick": 5, "yaks_delivered": 10},
                        {"owner": "Green", "points_tick": 3},
                        {"owner": "Blue", "points_tick": 2, "yaks_delivered": 5},
                    ],
                    "kills": {"red": 1000, "green": 800, "blue": 600},
                    "deaths": {"red": 800, "green": 700, "blue": 500},
                },
                {
                    "objectives": [
                        {"owner": "Red", "points_tick": 4, "yaks_delivered": 8},
                    ],
                    "kills": {"red": 1200, "green": 900, "blue": 700},
                    "deaths": {"red": 1000, "green": 800, "blue": 600},
                },
                {
                    "objectives": [
                        {"owner": "Blue", "points_tick": 7},
                    ],
                    "kills": {"red": 1400, "green": 1100, "blue": 800},
                    "deaths": {"red": 1100, "green": 900, "blue": 700},
                },
                {
                    "objectives": [
                        {"owner": "Green", "points_tick": 5, "yaks_delivered": 12},
                    ],
                    "kills": {"red": 1500, "green": 1200, "blue": 900},
                    "deaths": {"red": 1200, "green": 1000, "blue": 800},
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_match_no_world_no_api_key(self, mock_bot, mock_ctx):
        """Test match command with no world and no API key shows help message."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=None)

            with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                with patch('src.gw2.cogs.wvw.Gw2Client'):
                    await cog.match.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "Missing World Name" in error_msg

    @pytest.mark.asyncio
    async def test_match_no_world_api_key_error(self, mock_bot, mock_ctx):
        """Test match command with no world and APIKeyError."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        api_key_data = [{"key": "test-api-key-12345"}]

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=APIKeyError(mock_ctx.bot, "Invalid key"))

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.match.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "You dont have an API key registered" in error_msg

    @pytest.mark.asyncio
    async def test_match_no_world_generic_exception(self, mock_bot, mock_ctx):
        """Test match command with no world and generic exception."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        api_key_data = [{"key": "test-api-key-12345"}]

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                error = Exception("Something went wrong")
                mock_client_instance.call_api = AsyncMock(side_effect=error)

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.match.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once_with(mock_ctx, error)
                    mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_match_world_given_uses_get_world_id(self, mock_bot, mock_ctx, sample_matches_data):
        """Test match command with world given uses get_world_id."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=sample_matches_data)

                with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
                    mock_pop.return_value = ["World1 (High)", "World2 (Medium)"]

                    with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                        await cog.match.callback(cog, mock_ctx, world="Anvil Rock")

                        mock_get_wid.assert_called_once_with(mock_ctx.bot, "Anvil Rock")

    @pytest.mark.asyncio
    async def test_match_wid_none(self, mock_bot, mock_ctx):
        """Test match command when wid is None."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = None

            with patch('src.gw2.cogs.wvw.Gw2Client'):
                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.match.callback(cog, mock_ctx, world="InvalidWorld")

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "Invalid world name" in error_msg
                    assert "InvalidWorld" in error_msg

    @pytest.mark.asyncio
    async def test_match_na_tier(self, mock_bot, mock_ctx, sample_matches_data):
        """Test match command with NA tier."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=sample_matches_data)

                with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
                    mock_pop.return_value = ["World1 (High)"]

                    with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                        await cog.match.callback(cog, mock_ctx, world="Anvil Rock")

                        embed = mock_send.call_args[0][1]
                        assert "North America Tier" in embed.description

    @pytest.mark.asyncio
    async def test_match_eu_tier(self, mock_bot, mock_ctx):
        """Test match command with EU tier."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        eu_matches = {
            "id": "2-5",
            "scores": {"red": 150000, "green": 120000, "blue": 100000},
            "victory_points": {"red": 50, "green": 40, "blue": 30},
            "all_worlds": {
                "red": [2001, 2002],
                "green": [2003, 2004],
                "blue": [2005, 2006],
            },
            "worlds": {"red": 2001, "green": 2003, "blue": 2005},
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
            "skirmishes": [
                {"scores": {"red": 600, "green": 500, "blue": 400}},
            ],
            "maps": [
                {
                    "objectives": [{"owner": "Red", "points_tick": 5}],
                    "kills": {"red": 1000, "green": 800, "blue": 600},
                    "deaths": {"red": 800, "green": 700, "blue": 500},
                },
                {
                    "objectives": [{"owner": "Green", "points_tick": 3}],
                    "kills": {"red": 1200, "green": 900, "blue": 700},
                    "deaths": {"red": 1000, "green": 800, "blue": 600},
                },
                {
                    "objectives": [{"owner": "Blue", "points_tick": 7}],
                    "kills": {"red": 1400, "green": 1100, "blue": 800},
                    "deaths": {"red": 1100, "green": 900, "blue": 700},
                },
                {
                    "objectives": [{"owner": "Green", "points_tick": 5}],
                    "kills": {"red": 1500, "green": 1200, "blue": 900},
                    "deaths": {"red": 1200, "green": 1000, "blue": 800},
                },
            ],
        }

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 2001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=eu_matches)

                with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
                    mock_pop.return_value = ["World1 (High)"]

                    with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                        await cog.match.callback(cog, mock_ctx, world="Desolation")

                        embed = mock_send.call_args[0][1]
                        assert "Europe Tier" in embed.description

    @pytest.mark.asyncio
    async def test_match_exception_during_fetch(self, mock_bot, mock_ctx):
        """Test match command when exception during matches fetch."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                error = Exception("API Error")
                mock_client_instance.call_api = AsyncMock(side_effect=error)

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.match.callback(cog, mock_ctx, world="Anvil Rock")

                    mock_error.assert_called_once_with(mock_ctx, error)
                    mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_match_successful_embed(self, mock_bot, mock_ctx, sample_matches_data):
        """Test match command sends successful embed with green/blue/red values."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=sample_matches_data)

                with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
                    mock_pop.return_value = ["World1 (High)", "World2 (Medium)"]

                    with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                        await cog.match.callback(cog, mock_ctx, world="Anvil Rock")

                        mock_send.assert_called_once()
                        embed = mock_send.call_args[0][1]
                        assert embed.title == "WvW Score"
                        field_names = [f.name for f in embed.fields]
                        assert "Green" in field_names
                        assert "Blue" in field_names
                        assert "Red" in field_names


class TestKdrCommand:
    """Test cases for the wvw kdr command."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.author.mention = "<@12345>"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def sample_matches_data(self):
        """Create sample WvW matches data for kdr."""
        return {
            "id": "1-3",
            "scores": {"red": 150000, "green": 120000, "blue": 100000},
            "victory_points": {"red": 50, "green": 40, "blue": 30},
            "all_worlds": {
                "red": [1001, 1002],
                "green": [1003, 1004],
                "blue": [1005, 1006],
            },
            "worlds": {"red": 1001, "green": 1003, "blue": 1005},
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
            "skirmishes": [
                {"scores": {"red": 600, "green": 500, "blue": 400}},
            ],
            "maps": [
                {
                    "objectives": [{"owner": "Red", "points_tick": 5}],
                    "kills": {"red": 1000, "green": 800, "blue": 600},
                    "deaths": {"red": 800, "green": 700, "blue": 500},
                },
                {
                    "objectives": [{"owner": "Green", "points_tick": 3}],
                    "kills": {"red": 1200, "green": 900, "blue": 700},
                    "deaths": {"red": 1000, "green": 800, "blue": 600},
                },
                {
                    "objectives": [{"owner": "Blue", "points_tick": 7}],
                    "kills": {"red": 1400, "green": 1100, "blue": 800},
                    "deaths": {"red": 1100, "green": 900, "blue": 700},
                },
                {
                    "objectives": [{"owner": "Green", "points_tick": 5}],
                    "kills": {"red": 1500, "green": 1200, "blue": 900},
                    "deaths": {"red": 1200, "green": 1000, "blue": 800},
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_kdr_no_world_no_api_key(self, mock_bot, mock_ctx):
        """Test kdr command with no world and no API key shows error message."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=None)

            with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                with patch('src.gw2.cogs.wvw.Gw2Client'):
                    await cog.kdr.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "Invalid world name" in error_msg

    @pytest.mark.asyncio
    async def test_kdr_no_world_api_key_error(self, mock_bot, mock_ctx):
        """Test kdr command with no world and APIKeyError."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        api_key_data = [{"key": "test-api-key-12345"}]

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=APIKeyError(mock_ctx.bot, "Invalid key"))

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.kdr.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "You dont have an API key registered" in error_msg

    @pytest.mark.asyncio
    async def test_kdr_no_world_generic_exception(self, mock_bot, mock_ctx):
        """Test kdr command with no world and generic exception."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        api_key_data = [{"key": "test-api-key-12345"}]

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                error = Exception("Something went wrong")
                mock_client_instance.call_api = AsyncMock(side_effect=error)

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.kdr.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once_with(mock_ctx, error)
                    mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_kdr_world_given(self, mock_bot, mock_ctx, sample_matches_data):
        """Test kdr command with world given uses get_world_id."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=sample_matches_data)

                with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
                    mock_pop.return_value = ["World1 (High)"]

                    with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                        await cog.kdr.callback(cog, mock_ctx, world="Anvil Rock")

                        mock_get_wid.assert_called_once_with(mock_ctx.bot, "Anvil Rock")

    @pytest.mark.asyncio
    async def test_kdr_wid_none(self, mock_bot, mock_ctx):
        """Test kdr command when wid is None."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = None

            with patch('src.gw2.cogs.wvw.Gw2Client'):
                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.kdr.callback(cog, mock_ctx, world="InvalidWorld")

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "Invalid world name" in error_msg
                    assert "InvalidWorld" in error_msg

    @pytest.mark.asyncio
    async def test_kdr_na_tier_title(self, mock_bot, mock_ctx, sample_matches_data):
        """Test kdr command with NA tier title."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=sample_matches_data)

                with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
                    mock_pop.return_value = ["World1 (High)"]

                    with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                        await cog.kdr.callback(cog, mock_ctx, world="Anvil Rock")

                        embed = mock_send.call_args[0][1]
                        assert "North America Tier" in embed.description

    @pytest.mark.asyncio
    async def test_kdr_eu_tier_title(self, mock_bot, mock_ctx):
        """Test kdr command with EU tier title."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        eu_matches = {
            "id": "2-5",
            "scores": {"red": 150000, "green": 120000, "blue": 100000},
            "victory_points": {"red": 50, "green": 40, "blue": 30},
            "all_worlds": {
                "red": [2001, 2002],
                "green": [2003, 2004],
                "blue": [2005, 2006],
            },
            "worlds": {"red": 2001, "green": 2003, "blue": 2005},
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
            "skirmishes": [
                {"scores": {"red": 600, "green": 500, "blue": 400}},
            ],
            "maps": [
                {
                    "objectives": [{"owner": "Red", "points_tick": 5}],
                    "kills": {"red": 1000, "green": 800, "blue": 600},
                    "deaths": {"red": 800, "green": 700, "blue": 500},
                },
                {
                    "objectives": [{"owner": "Green", "points_tick": 3}],
                    "kills": {"red": 1200, "green": 900, "blue": 700},
                    "deaths": {"red": 1000, "green": 800, "blue": 600},
                },
                {
                    "objectives": [{"owner": "Blue", "points_tick": 7}],
                    "kills": {"red": 1400, "green": 1100, "blue": 800},
                    "deaths": {"red": 1100, "green": 900, "blue": 700},
                },
                {
                    "objectives": [{"owner": "Green", "points_tick": 5}],
                    "kills": {"red": 1500, "green": 1200, "blue": 900},
                    "deaths": {"red": 1200, "green": 1000, "blue": 800},
                },
            ],
        }

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 2001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=eu_matches)

                with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
                    mock_pop.return_value = ["World1 (High)"]

                    with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                        await cog.kdr.callback(cog, mock_ctx, world="Desolation")

                        embed = mock_send.call_args[0][1]
                        assert "Europe" in embed.description
                        assert "Tier" in embed.description

    @pytest.mark.asyncio
    async def test_kdr_exception_during_fetch(self, mock_bot, mock_ctx):
        """Test kdr command when exception during matches fetch."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                error = Exception("API Error")
                mock_client_instance.call_api = AsyncMock(side_effect=error)

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    await cog.kdr.callback(cog, mock_ctx, world="Anvil Rock")

                    mock_error.assert_called_once_with(mock_ctx, error)
                    mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_kdr_successful_embed(self, mock_bot, mock_ctx, sample_matches_data):
        """Test kdr command sends successful embed."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(return_value=sample_matches_data)

                with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
                    mock_pop.return_value = ["World1 (High)"]

                    with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                        await cog.kdr.callback(cog, mock_ctx, world="Anvil Rock")

                        mock_send.assert_called_once()
                        embed = mock_send.call_args[0][1]
                        assert embed.title == "WvW Kills/Death Ratings"
                        field_names = [f.name for f in embed.fields]
                        assert "Green" in field_names
                        assert "Blue" in field_names
                        assert "Red" in field_names


class TestGetMapNamesEmbedValues:
    """Test cases for the _get_map_names_embed_values function."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        return ctx

    @pytest.fixture
    def sample_matches(self):
        """Create sample matches data."""
        return {
            "all_worlds": {
                "green": [1003, 1004, 1005],
                "blue": [1006, 1007],
                "red": [1001, 1002],
            },
            "worlds": {
                "green": 1003,
                "blue": 1006,
                "red": 1001,
            },
        }

    @pytest.mark.asyncio
    async def test_get_map_names_green(self, mock_ctx, sample_matches):
        """Test _get_map_names_embed_values for green color."""
        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
            mock_pop.return_value = ["World1 (High)", "World2 (Medium)", "World3 (Low)"]

            result = await _get_map_names_embed_values(mock_ctx, "green", sample_matches)

            assert "World1 (High)" in result
            assert "World2 (Medium)" in result
            assert "World3 (Low)" in result
            # Verify the primary server is first in the list
            mock_pop.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_map_names_primary_server_first(self, mock_ctx, sample_matches):
        """Test that primary server ID is first in the list."""
        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
            mock_pop.return_value = ["World1 (High)"]

            await _get_map_names_embed_values(mock_ctx, "green", sample_matches)

            call_args = mock_pop.call_args[0]
            ids_str = call_args[1]
            # Primary server (1003) should be first
            assert ids_str.startswith("1003")

    @pytest.mark.asyncio
    async def test_get_map_names_no_duplicates(self, mock_ctx):
        """Test that primary server is not duplicated if already in all_worlds."""
        matches = {
            "all_worlds": {"red": [1001, 1002]},
            "worlds": {"red": 1001},
        }

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_name_population', new_callable=AsyncMock) as mock_pop:
            mock_pop.return_value = ["World1 (High)", "World2 (Medium)"]

            await _get_map_names_embed_values(mock_ctx, "red", matches)

            call_args = mock_pop.call_args[0]
            ids_str = call_args[1]
            # 1001 should appear only once
            assert ids_str.count("1001") == 1


class TestGetKdrEmbedValues:
    """Test cases for the _get_kdr_embed_values function."""

    @pytest.mark.asyncio
    async def test_kdr_normal_calculation(self):
        """Test _get_kdr_embed_values with normal kills and deaths."""
        matches = {
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
        }

        result = await _get_kdr_embed_values("red", matches)

        expected_kd = round(5000 / 4000, 3)
        assert f"Kills: `{format(5000, ',d')}`" in result
        assert f"Deaths: `{format(4000, ',d')}`" in result
        assert f"Activity: `{format(9000, ',d')}`" in result
        assert f"K/D: `{expected_kd}`" in result

    @pytest.mark.asyncio
    async def test_kdr_kills_zero(self):
        """Test _get_kdr_embed_values when kills=0."""
        matches = {
            "kills": {"red": 0, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
        }

        result = await _get_kdr_embed_values("red", matches)

        assert "K/D: `0.0`" in result
        assert "Activity: `4,000`" in result

    @pytest.mark.asyncio
    async def test_kdr_deaths_zero(self):
        """Test _get_kdr_embed_values when deaths=0."""
        matches = {
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 0, "green": 3500, "blue": 2500},
        }

        result = await _get_kdr_embed_values("red", matches)

        assert "K/D: `0.0`" in result

    @pytest.mark.asyncio
    async def test_kdr_green_color(self):
        """Test _get_kdr_embed_values with green color."""
        matches = {
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
        }

        result = await _get_kdr_embed_values("green", matches)

        expected_kd = round(4000 / 3500, 3)
        assert f"K/D: `{expected_kd}`" in result
        assert f"Kills: `{format(4000, ',d')}`" in result

    @pytest.mark.asyncio
    async def test_kdr_both_zero(self):
        """Test _get_kdr_embed_values when both kills and deaths are 0."""
        matches = {
            "kills": {"red": 0},
            "deaths": {"red": 0},
        }

        result = await _get_kdr_embed_values("red", matches)

        assert "K/D: `0.0`" in result
        assert "Activity: `0`" in result


class TestGetMatchEmbedValues:
    """Test cases for the _get_match_embed_values function."""

    @pytest.fixture
    def sample_matches(self):
        """Create sample matches data for match embed values."""
        return {
            "scores": {"red": 150000, "green": 120000, "blue": 100000},
            "victory_points": {"red": 50, "green": 40, "blue": 30},
            "kills": {"red": 5000, "green": 4000, "blue": 3000},
            "deaths": {"red": 4000, "green": 3500, "blue": 2500},
            "skirmishes": [
                {"scores": {"red": 500, "green": 400, "blue": 300}},
                {"scores": {"red": 600, "green": 500, "blue": 400}},
            ],
            "maps": [
                {
                    "objectives": [
                        {"owner": "Red", "points_tick": 5, "yaks_delivered": 10},
                        {"owner": "Green", "points_tick": 3},
                        {"owner": "Blue", "points_tick": 2, "yaks_delivered": 5},
                    ],
                    "kills": {"red": 1000, "green": 800, "blue": 600},
                    "deaths": {"red": 800, "green": 700, "blue": 500},
                },
                {
                    "objectives": [
                        {"owner": "Red", "points_tick": 4, "yaks_delivered": 8},
                        {"owner": "Green", "points_tick": 6},
                    ],
                    "kills": {"red": 1200, "green": 900, "blue": 700},
                    "deaths": {"red": 1000, "green": 800, "blue": 600},
                },
                {
                    "objectives": [
                        {"owner": "Blue", "points_tick": 7},
                        {"owner": "Red", "points_tick": 3, "yaks_delivered": 6},
                    ],
                    "kills": {"red": 1400, "green": 1100, "blue": 800},
                    "deaths": {"red": 1100, "green": 900, "blue": 700},
                },
                {
                    "objectives": [
                        {"owner": "Green", "points_tick": 5, "yaks_delivered": 12},
                        {"owner": "Blue", "points_tick": 4},
                    ],
                    "kills": {"red": 1500, "green": 1200, "blue": 900},
                    "deaths": {"red": 1200, "green": 1000, "blue": 800},
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_match_embed_values_normal(self, sample_matches):
        """Test _get_match_embed_values with normal data."""
        result = await _get_match_embed_values("red", sample_matches)

        assert "Score: `150,000`" in result
        assert "Victory Pts: `50`" in result
        assert "PPT:" in result
        assert "Skirmish:" in result
        assert "Kills:" in result
        assert "Deaths:" in result
        assert "K/D:" in result
        assert "K/D EBG:" in result
        assert "K/D Green:" in result
        assert "K/D Blue:" in result
        assert "K/D Red:" in result
        assert "%PPT~:" in result
        assert "%PPK~:" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_kd_zero_kills(self):
        """Test _get_match_embed_values when kills=0."""
        matches = {
            "scores": {"red": 100000},
            "victory_points": {"red": 50},
            "kills": {"red": 0},
            "deaths": {"red": 4000},
            "skirmishes": [{"scores": {"red": 600}}],
            "maps": [
                {"objectives": [], "kills": {"red": 0}, "deaths": {"red": 800}},
                {"objectives": [], "kills": {"red": 0}, "deaths": {"red": 1000}},
                {"objectives": [], "kills": {"red": 0}, "deaths": {"red": 900}},
                {"objectives": [], "kills": {"red": 0}, "deaths": {"red": 1200}},
            ],
        }

        result = await _get_match_embed_values("red", matches)
        assert "K/D: `0.0`" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_kd_zero_deaths(self):
        """Test _get_match_embed_values when deaths=0."""
        matches = {
            "scores": {"red": 100000},
            "victory_points": {"red": 50},
            "kills": {"red": 5000},
            "deaths": {"red": 0},
            "skirmishes": [{"scores": {"red": 600}}],
            "maps": [
                {"objectives": [], "kills": {"red": 1000}, "deaths": {"red": 0}},
                {"objectives": [], "kills": {"red": 1200}, "deaths": {"red": 0}},
                {"objectives": [], "kills": {"red": 1400}, "deaths": {"red": 0}},
                {"objectives": [], "kills": {"red": 1500}, "deaths": {"red": 0}},
            ],
        }

        result = await _get_match_embed_values("red", matches)
        assert "K/D: `0.0`" in result
        assert "K/D EBG: `0.0`" in result
        assert "K/D Green: `0.0`" in result
        assert "K/D Blue: `0.0`" in result
        assert "K/D Red: `0.0`" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_score_zero(self):
        """Test _get_match_embed_values when score=0, pppt and pppk should be '0.0'."""
        matches = {
            "scores": {"red": 0},
            "victory_points": {"red": 50},
            "kills": {"red": 0},
            "deaths": {"red": 0},
            "skirmishes": [{"scores": {"red": 600}}],
            "maps": [
                {"objectives": [], "kills": {"red": 0}, "deaths": {"red": 0}},
                {"objectives": [], "kills": {"red": 0}, "deaths": {"red": 0}},
                {"objectives": [], "kills": {"red": 0}, "deaths": {"red": 0}},
                {"objectives": [], "kills": {"red": 0}, "deaths": {"red": 0}},
            ],
        }

        result = await _get_match_embed_values("red", matches)
        assert "%PPT~: `0.0`" in result
        assert "%PPK~: `0.0`" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_normal_pppt_pppk(self, sample_matches):
        """Test _get_match_embed_values with normal pppt/pppk calculations."""
        result = await _get_match_embed_values("red", sample_matches)

        score = 150000
        kills = 5000
        ppt_points = int(score - (2 * kills))
        expected_pppt = round((ppt_points * 100) / score, 3)
        expected_pppk = round((2 * kills * 100) / score, 3)

        assert f"%PPT~: `{expected_pppt}`" in result
        assert f"%PPK~: `{expected_pppk}`" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_yaks_delivered_present(self, sample_matches):
        """Test _get_match_embed_values with yaks_delivered present."""
        result = await _get_match_embed_values("red", sample_matches)

        # Red owns objectives with yaks_delivered: 10, 8, 6 = 24
        assert "Yaks Dlv:" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_yaks_delivered_absent(self):
        """Test _get_match_embed_values with no yaks_delivered in objectives."""
        matches = {
            "scores": {"red": 100000},
            "victory_points": {"red": 50},
            "kills": {"red": 5000},
            "deaths": {"red": 4000},
            "skirmishes": [{"scores": {"red": 600}}],
            "maps": [
                {"objectives": [{"owner": "Red", "points_tick": 5}], "kills": {"red": 1000}, "deaths": {"red": 800}},
                {"objectives": [{"owner": "Red", "points_tick": 4}], "kills": {"red": 1200}, "deaths": {"red": 1000}},
                {"objectives": [{"owner": "Blue", "points_tick": 7}], "kills": {"red": 1400}, "deaths": {"red": 1100}},
                {"objectives": [{"owner": "Green", "points_tick": 5}], "kills": {"red": 1500}, "deaths": {"red": 1200}},
            ],
        }

        result = await _get_match_embed_values("red", matches)
        # yaks_delivered should be 0 since no objectives have the key
        assert "Yaks Dlv: `0`" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_per_map_kd_blue(self):
        """Test _get_match_embed_values per-map KD for blue (map index 0)."""
        matches = {
            "scores": {"red": 100000},
            "victory_points": {"red": 50},
            "kills": {"red": 5000},
            "deaths": {"red": 4000},
            "skirmishes": [{"scores": {"red": 600}}],
            "maps": [
                {"objectives": [], "kills": {"red": 1000}, "deaths": {"red": 500}},  # blue map
                {"objectives": [], "kills": {"red": 1200}, "deaths": {"red": 1000}},  # ebg
                {"objectives": [], "kills": {"red": 1400}, "deaths": {"red": 700}},  # green
                {"objectives": [], "kills": {"red": 1500}, "deaths": {"red": 1200}},  # red
            ],
        }

        result = await _get_match_embed_values("red", matches)
        expected_kd_blue = round(1000 / 500, 3)
        assert f"K/D Blue: `{expected_kd_blue}`" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_per_map_kd_ebg(self):
        """Test _get_match_embed_values per-map KD for EBG (map index 1)."""
        matches = {
            "scores": {"green": 120000},
            "victory_points": {"green": 40},
            "kills": {"green": 4000},
            "deaths": {"green": 3500},
            "skirmishes": [{"scores": {"green": 500}}],
            "maps": [
                {"objectives": [], "kills": {"green": 800}, "deaths": {"green": 700}},
                {"objectives": [], "kills": {"green": 900}, "deaths": {"green": 600}},  # ebg
                {"objectives": [], "kills": {"green": 1100}, "deaths": {"green": 900}},
                {"objectives": [], "kills": {"green": 1200}, "deaths": {"green": 1000}},
            ],
        }

        result = await _get_match_embed_values("green", matches)
        expected_kd_ebg = round(900 / 600, 3)
        assert f"K/D EBG: `{expected_kd_ebg}`" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_per_map_kd_green(self):
        """Test _get_match_embed_values per-map KD for green (map index 2)."""
        matches = {
            "scores": {"blue": 100000},
            "victory_points": {"blue": 30},
            "kills": {"blue": 3000},
            "deaths": {"blue": 2500},
            "skirmishes": [{"scores": {"blue": 400}}],
            "maps": [
                {"objectives": [], "kills": {"blue": 600}, "deaths": {"blue": 500}},
                {"objectives": [], "kills": {"blue": 700}, "deaths": {"blue": 600}},
                {"objectives": [], "kills": {"blue": 800}, "deaths": {"blue": 400}},  # green
                {"objectives": [], "kills": {"blue": 900}, "deaths": {"blue": 800}},
            ],
        }

        result = await _get_match_embed_values("blue", matches)
        expected_kd_green = round(800 / 400, 3)
        assert f"K/D Green: `{expected_kd_green}`" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_per_map_kd_red(self):
        """Test _get_match_embed_values per-map KD for red (map index 3)."""
        matches = {
            "scores": {"blue": 100000},
            "victory_points": {"blue": 30},
            "kills": {"blue": 3000},
            "deaths": {"blue": 2500},
            "skirmishes": [{"scores": {"blue": 400}}],
            "maps": [
                {"objectives": [], "kills": {"blue": 600}, "deaths": {"blue": 500}},
                {"objectives": [], "kills": {"blue": 700}, "deaths": {"blue": 600}},
                {"objectives": [], "kills": {"blue": 800}, "deaths": {"blue": 700}},
                {"objectives": [], "kills": {"blue": 900}, "deaths": {"blue": 300}},  # red
            ],
        }

        result = await _get_match_embed_values("blue", matches)
        expected_kd_red = round(900 / 300, 3)
        assert f"K/D Red: `{expected_kd_red}`" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_skirmish_uses_last(self, sample_matches):
        """Test _get_match_embed_values uses the last skirmish."""
        result = await _get_match_embed_values("red", sample_matches)

        # Last skirmish is index 1, score for red is 600
        assert "Skirmish: `600`" in result

    @pytest.mark.asyncio
    async def test_match_embed_values_activity(self, sample_matches):
        """Test _get_match_embed_values calculates activity correctly."""
        result = await _get_match_embed_values("red", sample_matches)

        # Activity = kills + deaths = 5000 + 4000 = 9000
        assert "Activity: `9,000`" in result


class TestWvWSetup:
    """Test cases for WvW cog setup."""

    @pytest.mark.asyncio
    async def test_setup_function_exists(self):
        """Test that setup function exists and is callable."""
        assert callable(setup)

    @pytest.mark.asyncio
    async def test_setup_removes_gw2_command(self):
        """Test that setup removes existing gw2 command."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        await setup(mock_bot)

        mock_bot.remove_command.assert_called_once_with("gw2")

    @pytest.mark.asyncio
    async def test_setup_adds_cog(self):
        """Test that setup adds the GW2WvW cog."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()
        cog_instance = mock_bot.add_cog.call_args[0][0]
        assert isinstance(cog_instance, GW2WvW)


class TestWvWSubcommand:
    """Test cases for the wvw group subcommand (line 27)."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.message = MagicMock()
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.invoked_subcommand = None
        ctx.command = MagicMock()
        ctx.send = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_wvw_group_calls_invoke_subcommand(self, mock_bot, mock_ctx):
        """Test that wvw group command calls invoke_subcommand (line 27)."""
        cog = GW2WvW(mock_bot)

        with patch('src.gw2.cogs.wvw.bot_utils.invoke_subcommand', new_callable=AsyncMock) as mock_invoke:
            await cog.wvw.callback(cog, mock_ctx)
            mock_invoke.assert_called_once_with(mock_ctx, "gw2 wvw")


class TestInfoDefaultColor:
    """Test cases for the default color branch (lines 89-90)."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
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
        return ctx

    @pytest.mark.asyncio
    async def test_info_unknown_world_color_uses_default(self, mock_bot, mock_ctx):
        """Test info command uses discord.Color.default() for unexpected worldcolor (lines 89-90)."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        sample_worldinfo = {"id": 1001, "name": "Anvil Rock", "population": "High"}

        # Create matches where the world is in a color key that is NOT red/green/blue
        matches_data = {
            "id": "1-3",
            "scores": {"yellow": 150000},
            "victory_points": {"yellow": 50},
            "all_worlds": {
                "yellow": [1001, 1002],
            },
            "kills": {"yellow": 5000},
            "deaths": {"yellow": 4000},
            "skirmishes": [{"scores": {"yellow": 600}}],
            "maps": [{"objectives": [{"owner": "Yellow", "points_tick": 5}]}],
        }

        with patch('src.gw2.cogs.wvw.gw2_utils.get_world_id', new_callable=AsyncMock) as mock_get_wid:
            mock_get_wid.return_value = 1001

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=[matches_data, sample_worldinfo])

                with patch('src.gw2.cogs.wvw.bot_utils.send_embed') as mock_send:
                    with patch('src.gw2.cogs.wvw.chat_formatting.inline', side_effect=lambda x: f"`{x}`"):
                        await cog.info.callback(cog, mock_ctx, world="Anvil Rock")

                        embed = mock_send.call_args[0][1]
                        assert embed.color == discord.Color.default()


class TestMatchAPIKeyError:
    """Test cases for match command APIKeyError handler (line 159-161)."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
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
        return ctx

    @pytest.mark.asyncio
    async def test_match_api_key_error_on_account_call(self, mock_bot, mock_ctx):
        """Test match command sends NO_API_KEY error when APIKeyError is raised during account call (line 159-161)."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        api_key_data = [{"key": "test-api-key"}]

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                # Raise APIKeyError on the account call (results = await gw2_api.call_api("account", api_key))
                mock_client_instance.call_api = AsyncMock(side_effect=APIKeyError(mock_ctx.bot, "Invalid key"))

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    result = await cog.match.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once()
                    from src.gw2.constants import gw2_messages

                    assert mock_error.call_args[0][1] == gw2_messages.NO_API_KEY


class TestKdrAPIKeyError:
    """Test cases for kdr command APIKeyError handler (line 227-229)."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
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
        return ctx

    @pytest.mark.asyncio
    async def test_kdr_api_key_error_on_account_call(self, mock_bot, mock_ctx):
        """Test kdr command sends NO_API_KEY error when APIKeyError is raised during account call (line 227-229)."""
        cog = GW2WvW(mock_bot)
        cog.bot = mock_ctx.bot

        api_key_data = [{"key": "test-api-key"}]

        with patch('src.gw2.cogs.wvw.Gw2KeyDal') as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            with patch('src.gw2.cogs.wvw.Gw2Client') as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.call_api = AsyncMock(side_effect=APIKeyError(mock_ctx.bot, "Invalid key"))

                with patch('src.gw2.cogs.wvw.bot_utils.send_error_msg') as mock_error:
                    result = await cog.kdr.callback(cog, mock_ctx, world=None)

                    mock_error.assert_called_once()
                    from src.gw2.constants import gw2_messages

                    assert mock_error.call_args[0][1] == gw2_messages.NO_API_KEY
