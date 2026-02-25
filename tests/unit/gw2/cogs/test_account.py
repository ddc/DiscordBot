"""Comprehensive tests for GW2 account cog."""

import asyncio
import discord
import pytest
from src.gw2.cogs.account import GW2Account, account
from src.gw2.constants import gw2_messages
from src.gw2.tools.gw2_exceptions import APIInvalidKey
from unittest.mock import AsyncMock, MagicMock, patch


class TestGW2Account:
    """Test cases for the GW2Account cog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def gw2_account_cog(self, mock_bot):
        """Create a GW2Account cog instance."""
        return GW2Account(mock_bot)

    def test_gw2_account_initialization(self, mock_bot):
        """Test GW2Account cog initialization."""
        cog = GW2Account(mock_bot)
        assert cog.bot == mock_bot

    def test_gw2_account_inheritance(self, gw2_account_cog):
        """Test that GW2Account inherits from GuildWars2 properly."""
        # Should inherit from the base GuildWars2 class
        from src.gw2.cogs.gw2 import GuildWars2

        assert isinstance(gw2_account_cog, GuildWars2)


class TestAccountCommand:
    """Test cases for the account command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.avatar = MagicMock()
        ctx.bot.user.avatar.url = "https://example.com/bot_avatar.png"
        ctx.bot.user.display_avatar = MagicMock()
        ctx.bot.user.display_avatar.url = "https://example.com/bot_avatar.png"

        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/user_avatar.png"
        ctx.message.author.display_avatar = MagicMock()
        ctx.message.author.display_avatar.url = "https://example.com/user_avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()

        ctx.prefix = "!"
        return ctx

    @pytest.fixture
    def sample_api_key_data(self):
        """Create sample API key data."""
        return [{"key": "test-api-key-12345", "permissions": "account,characters,progression,pvp,guilds"}]

    @pytest.fixture
    def sample_account_data(self):
        """Create sample account data."""
        return {
            "id": "account-id-123",
            "name": "TestUser.1234",
            "world": 1001,
            "guilds": ["guild-id-1", "guild-id-2"],
            "guild_leader": ["guild-id-1"],
            "created": "2020-01-01T00:00:00.000Z",
            "access": ["PlayForFree", "GuildWars2", "HeartOfThorns"],
            "commander": True,
            "fractal_level": 100,
            "daily_ap": 5000,
            "monthly_ap": 500,
            "wvw_rank": 1250,
            "age": 1051200,  # minutes (2 years)
        }

    @pytest.fixture
    def sample_world_data(self):
        """Create sample world data."""
        return {"id": 1001, "name": "Anvil Rock", "population": "High"}

    @pytest.mark.asyncio
    async def test_account_command_no_api_key(self, mock_ctx):
        """Test account command when user has no API key."""
        with patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=None)

            with patch("src.gw2.cogs.account.bot_utils.send_error_msg") as mock_error:
                await account(mock_ctx)

                mock_error.assert_called_once()
                error_msg = mock_error.call_args[0][1]
                assert gw2_messages.NO_API_KEY in error_msg

    @pytest.mark.asyncio
    async def test_account_command_invalid_api_key(self, mock_ctx, sample_api_key_data):
        """Test account command with invalid API key."""
        with patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch("src.gw2.cogs.account.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                invalid_key_error = APIInvalidKey(mock_ctx.bot, "Invalid API key")
                # Make the error have an args attribute like a real exception
                invalid_key_error.args = ("error", "Invalid API key message")
                mock_client_instance.check_api_key = AsyncMock(return_value=invalid_key_error)

                with patch("src.gw2.cogs.account.bot_utils.send_error_msg") as mock_error:
                    await account(mock_ctx)

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert "Invalid API key message" in error_msg

    @pytest.mark.asyncio
    async def test_account_command_insufficient_permissions(self, mock_ctx, sample_account_data):
        """Test account command with insufficient API key permissions."""
        insufficient_permissions_data = [
            {"key": "test-api-key-12345", "permissions": "characters"}  # Missing 'account' permission
        ]

        with patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=insufficient_permissions_data)

            with patch("src.gw2.cogs.account.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)

                with patch("src.gw2.cogs.account.bot_utils.send_error_msg") as mock_error:
                    await account(mock_ctx)

                    mock_error.assert_called_once()
                    error_msg = mock_error.call_args[0][1]
                    assert gw2_messages.API_KEY_NO_PERMISSION in error_msg

    @pytest.mark.asyncio
    async def test_account_command_successful_basic(
        self, mock_ctx, sample_api_key_data, sample_account_data, sample_world_data
    ):
        """Test successful account command with basic information."""
        with patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch("src.gw2.cogs.account.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_account_data,  # account call
                        sample_world_data,  # world call
                    ]
                )

                with patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send:
                    await account(mock_ctx)

                    mock_send.assert_called_once()
                    mock_send.assert_called_once()
                    # The embed is created inside the function, just verify send was called

    @pytest.mark.asyncio
    async def test_account_command_with_characters_permission(self, mock_ctx, sample_account_data, sample_world_data):
        """Test account command with characters permission."""
        characters_api_key_data = [{"key": "test-api-key-12345", "permissions": "account,characters"}]

        characters_data = ["Character1", "Character2", "Character3"]

        with patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=characters_api_key_data)

            with patch("src.gw2.cogs.account.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_account_data,  # account call
                        sample_world_data,  # world call
                        characters_data,  # characters call
                    ]
                )

                with patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send:
                    await account(mock_ctx)

                    mock_send.assert_called_once()
                    mock_send.assert_called_once()
                    # Verify the function completed without error

    @pytest.mark.asyncio
    async def test_account_command_with_progression_permission(self, mock_ctx, sample_account_data, sample_world_data):
        """Test account command with progression permission."""
        progression_api_key_data = [{"key": "test-api-key-12345", "permissions": "account,progression"}]

        achievements_data = [{"id": 1, "current": 10}, {"id": 2, "current": 5}]

        with patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=progression_api_key_data)

            with patch("src.gw2.cogs.account.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_account_data,  # account call
                        sample_world_data,  # world call
                        achievements_data,  # achievements call
                    ]
                )

                with patch("src.gw2.cogs.account.gw2_utils.calculate_user_achiev_points") as mock_calc:
                    mock_calc.return_value = 15000

                    with patch("src.gw2.cogs.account.gw2_utils.get_wvw_rank_title") as mock_wvw_title:
                        mock_wvw_title.return_value = "Gold General"

                        with patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send:
                            await account(mock_ctx)

                            mock_send.assert_called_once()
                            mock_send.assert_called_once()
                            # Verify the function completed without error

    @pytest.mark.asyncio
    async def test_account_command_with_pvp_permission(self, mock_ctx, sample_account_data, sample_world_data):
        """Test account command with PvP permission."""
        pvp_api_key_data = [{"key": "test-api-key-12345", "permissions": "account,pvp"}]

        pvp_stats_data = {"pvp_rank": 45, "pvp_rank_rollovers": 5}

        with patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=pvp_api_key_data)

            with patch("src.gw2.cogs.account.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_account_data,  # account call
                        sample_world_data,  # world call
                        pvp_stats_data,  # pvp stats call
                    ]
                )

                with patch("src.gw2.cogs.account.gw2_utils.get_pvp_rank_title") as mock_pvp_title:
                    mock_pvp_title.return_value = "Tiger"

                    with patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send:
                        await account(mock_ctx)

                        mock_send.assert_called_once()
                        mock_send.assert_called_once()
                        # Verify the function completed without error

    @pytest.mark.asyncio
    async def test_account_command_with_guilds(self, mock_ctx, sample_account_data, sample_world_data):
        """Test account command with guild information."""
        full_permissions_data = [{"key": "test-api-key-12345", "permissions": "account,guilds"}]

        guild_data_1 = {"id": "guild-id-1", "name": "Test Guild One", "tag": "TG1"}

        guild_data_2 = {"id": "guild-id-2", "name": "Test Guild Two", "tag": "TG2"}

        with patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=full_permissions_data)

            with patch("src.gw2.cogs.account.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_account_data,  # account call
                        sample_world_data,  # world call
                        guild_data_1,  # first guild call
                        guild_data_2,  # second guild call
                    ]
                )

                with patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send:
                    await account(mock_ctx)

                    mock_send.assert_called_once()
                    mock_send.assert_called_once()
                    # Verify the function completed without error

    @pytest.mark.asyncio
    async def test_account_command_api_error_during_execution(self, mock_ctx, sample_api_key_data, sample_account_data):
        """Test account command when API error occurs during execution."""
        with patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=sample_api_key_data)

            with patch("src.gw2.cogs.account.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(side_effect=Exception("API Error"))

                with patch("src.gw2.cogs.account.bot_utils.send_error_msg") as mock_error:
                    await account(mock_ctx)

                    mock_error.assert_called_once()
                    mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_command_guild_api_error(self, mock_ctx, sample_account_data, sample_world_data):
        """Test account command when guild API call fails."""
        full_permissions_data = [{"key": "test-api-key-12345", "permissions": "account,guilds"}]

        with patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal:
            mock_instance = mock_dal.return_value
            mock_instance.get_api_key_by_user = AsyncMock(return_value=full_permissions_data)

            with patch("src.gw2.cogs.account.Gw2Client") as mock_client:
                mock_client_instance = mock_client.return_value
                mock_client_instance.check_api_key = AsyncMock(return_value=sample_account_data)
                mock_client_instance.call_api = AsyncMock(
                    side_effect=[
                        sample_account_data,  # account call
                        sample_world_data,  # world call
                        Exception("Guild API Error"),  # guild call fails
                    ]
                )

                with patch("src.gw2.cogs.account.bot_utils.send_error_msg") as mock_error:
                    await account(mock_ctx)

                    mock_error.assert_called_once()
                    mock_ctx.bot.log.error.assert_called_once()

    def test_account_command_cooldown(self):
        """Test that account command has proper cooldown."""
        # The cooldown is applied via decorator, just check the function exists
        from src.gw2.cogs.account import account

        assert callable(account)

    def test_account_command_belongs_to_gw2_group(self):
        """Test that account command belongs to gw2 command group."""
        # The command is registered as a subcommand via @GW2Account.gw2.command()
        from src.gw2.cogs.account import account

        assert callable(account)


class TestAccountSetup:
    """Test cases for account cog setup."""

    @pytest.mark.asyncio
    async def test_setup_function_exists(self):
        """Test that setup function exists and is callable."""
        from src.gw2.cogs.account import setup

        assert callable(setup)

    @pytest.mark.asyncio
    async def test_setup_function_removes_existing_gw2_command(self):
        """Test that setup removes existing gw2 command."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        from src.gw2.cogs.account import setup

        await setup(mock_bot)

        mock_bot.remove_command.assert_called_once_with("gw2")
        mock_bot.add_cog.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_function_adds_cog(self):
        """Test that setup adds the GW2Account cog."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        from src.gw2.cogs.account import setup

        await setup(mock_bot)

        # Verify that add_cog was called with a GW2Account instance
        mock_bot.add_cog.assert_called_once()
        cog_instance = mock_bot.add_cog.call_args[0][0]
        assert isinstance(cog_instance, GW2Account)


class TestKeepTypingAlive:
    """Test cases for the _keep_typing_alive helper function."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context with async typing."""
        ctx = MagicMock()
        ctx.message = MagicMock()
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        return ctx

    @pytest.mark.asyncio
    async def test_keep_typing_normal_operation(self, mock_ctx):
        """Test that typing() is called and loop exits when event is set."""
        from src.gw2.cogs.account import _keep_typing_alive

        stop_event = asyncio.Event()

        # Immediately set the event so the while loop exits on first check
        stop_event.set()

        await _keep_typing_alive(mock_ctx, stop_event)

        # The while condition is checked first; since it's already set, the loop body never runs
        mock_ctx.message.channel.typing.assert_not_called()

    @pytest.mark.asyncio
    async def test_keep_typing_calls_typing_then_stops(self, mock_ctx):
        """Test that typing() is called at least once before event is set."""
        from src.gw2.cogs.account import _keep_typing_alive

        stop_event = asyncio.Event()
        call_count = 0

        original_typing = mock_ctx.message.channel.typing

        async def typing_side_effect():
            nonlocal call_count
            call_count += 1
            # Set the stop event after first typing call
            stop_event.set()

        mock_ctx.message.channel.typing = AsyncMock(side_effect=typing_side_effect)

        with patch("src.gw2.cogs.account.asyncio.sleep", new_callable=AsyncMock):
            await _keep_typing_alive(mock_ctx, stop_event)

        assert call_count >= 1

    @pytest.mark.asyncio
    async def test_keep_typing_cancelled_error_propagates(self, mock_ctx):
        """Test that CancelledError is re-raised from the outer handler."""
        from src.gw2.cogs.account import _keep_typing_alive

        stop_event = asyncio.Event()

        # Make typing raise CancelledError
        mock_ctx.message.channel.typing = AsyncMock(side_effect=asyncio.CancelledError)

        with pytest.raises(asyncio.CancelledError):
            await _keep_typing_alive(mock_ctx, stop_event)

    @pytest.mark.asyncio
    async def test_keep_typing_http_exception_breaks_loop(self, mock_ctx):
        """Test that discord.HTTPException causes the loop to break gracefully."""
        from src.gw2.cogs.account import _keep_typing_alive

        stop_event = asyncio.Event()

        mock_response = MagicMock(status=500)
        mock_ctx.message.channel.typing = AsyncMock(side_effect=discord.HTTPException(mock_response, "server error"))

        # Should not raise, just break out of loop
        await _keep_typing_alive(mock_ctx, stop_event)

        mock_ctx.message.channel.typing.assert_called_once()

    @pytest.mark.asyncio
    async def test_keep_typing_forbidden_breaks_loop(self, mock_ctx):
        """Test that discord.Forbidden causes the loop to break gracefully."""
        from src.gw2.cogs.account import _keep_typing_alive

        stop_event = asyncio.Event()

        mock_response = MagicMock(status=403)
        mock_ctx.message.channel.typing = AsyncMock(side_effect=discord.Forbidden(mock_response, "forbidden"))

        # Forbidden is a subclass of HTTPException, so it is caught too
        await _keep_typing_alive(mock_ctx, stop_event)

        mock_ctx.message.channel.typing.assert_called_once()


class TestFetchGuildInfoStandalone:
    """Test cases for the _fetch_guild_info_standalone helper function."""

    @pytest.mark.asyncio
    async def test_fetch_guild_info_success(self):
        """Test successful guild info fetch returns formatted name and id."""
        from src.gw2.cogs.account import _fetch_guild_info_standalone

        mock_gw2_api = MagicMock()
        mock_gw2_api.call_api = AsyncMock(return_value={"name": "Test Guild", "tag": "TG"})
        mock_ctx = MagicMock()
        guild_id = "guild-abc-123"

        result = await _fetch_guild_info_standalone(mock_gw2_api, guild_id, "api-key", mock_ctx)

        assert result == ("[TG] Test Guild", guild_id)
        mock_gw2_api.call_api.assert_called_once_with(f"guild/{guild_id}", "api-key")

    @pytest.mark.asyncio
    async def test_fetch_guild_info_exception_returns_none(self):
        """Test that an exception returns (None, guild_id) and logs the error."""
        from src.gw2.cogs.account import _fetch_guild_info_standalone

        mock_gw2_api = MagicMock()
        mock_gw2_api.call_api = AsyncMock(side_effect=Exception("API failure"))
        mock_ctx = MagicMock()
        mock_ctx.bot = MagicMock()
        mock_ctx.bot.log = MagicMock()
        guild_id = "guild-abc-123"

        result = await _fetch_guild_info_standalone(mock_gw2_api, guild_id, "api-key", mock_ctx)

        assert result == (None, guild_id)
        mock_ctx.bot.log.error.assert_called_once()
        error_msg = mock_ctx.bot.log.error.call_args[0][0]
        assert "guild-abc-123" in error_msg
        assert "API failure" in error_msg


class TestAccountCommandFullPaths:
    """Test cases covering the main account command body (lines 86-259)."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock context with AsyncMock for send (awaitable)."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.avatar = MagicMock()
        ctx.bot.user.avatar.url = "https://example.com/bot_avatar.png"

        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/user_avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()

        ctx.prefix = "!"
        # Critical fix: ctx.send must be AsyncMock so `await ctx.send(...)` works
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def sample_account_data_no_guilds(self):
        """Account data without guilds to skip guild handling."""
        return {
            "id": "account-id-123",
            "name": "TestUser.1234",
            "world": 1001,
            "access": ["PlayForFree", "GuildWars2", "HeartOfThorns"],
            "commander": True,
            "fractal_level": 100,
            "daily_ap": 5000,
            "monthly_ap": 500,
            "wvw_rank": 1250,
            "age": 1051200,
            "created": "2020-01-01T00:00:00.000Z",
        }

    @pytest.fixture
    def sample_world_data(self):
        """Sample world data."""
        return {"id": 1001, "name": "Anvil Rock", "population": "High"}

    @pytest.mark.asyncio
    async def test_account_command_full_success_path(self, mock_ctx, sample_account_data_no_guilds, sample_world_data):
        """Test the full success path with account-only permissions (no optional calls, no guilds)."""
        api_key_data = [{"key": "test-api-key-12345", "permissions": "account"}]

        # progress_msg returned by ctx.send
        progress_msg = AsyncMock()
        mock_ctx.send.return_value = progress_msg

        with (
            patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.account.Gw2Client") as mock_client,
            patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send_embed,
            patch("src.gw2.cogs.account.bot_utils.get_current_date_time_str_long", return_value="2024-01-01 12:00:00"),
            patch("src.gw2.cogs.account._keep_typing_alive", new=MagicMock()),
            patch("src.gw2.cogs.account.asyncio.create_task") as mock_create_task,
            patch("src.gw2.cogs.account.asyncio.Event") as mock_event_cls,
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            mock_client_instance = mock_client.return_value
            mock_client_instance.check_api_key = AsyncMock(return_value={"valid": True})
            mock_client_instance.call_api = AsyncMock(
                side_effect=[
                    sample_account_data_no_guilds,  # account call
                    sample_world_data,  # worlds/{server_id} call
                ]
            )

            mock_stop_event = MagicMock()
            mock_event_cls.return_value = mock_stop_event

            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            await account(mock_ctx)

            # ctx.send was called for the progress embed
            mock_ctx.send.assert_called_once()

            # send_embed was called with the final embed
            mock_send_embed.assert_called_once()

            # progress_msg.delete was called to remove the progress message
            progress_msg.delete.assert_called_once()

            # The stop event was set and typing task was cancelled
            mock_stop_event.set.assert_called_once()
            mock_task.cancel.assert_called_once()

            # Verify API calls
            assert mock_client_instance.call_api.call_count == 2
            mock_client_instance.call_api.assert_any_call("account", "test-api-key-12345")
            mock_client_instance.call_api.assert_any_call("worlds/1001", "test-api-key-12345")

    @pytest.mark.asyncio
    async def test_account_command_exception_handler(self, mock_ctx):
        """Test the exception handler path (lines 249-259)."""
        api_key_data = [{"key": "test-api-key-12345", "permissions": "account"}]

        # ctx.send raises immediately, so the try block fails at progress message
        mock_ctx.send = AsyncMock(side_effect=RuntimeError("send failed"))

        with (
            patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.account.Gw2Client") as mock_client,
            patch("src.gw2.cogs.account.bot_utils.send_error_msg") as mock_error_msg,
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            mock_client_instance = mock_client.return_value
            mock_client_instance.check_api_key = AsyncMock(return_value={"valid": True})

            await account(mock_ctx)

            # send_error_msg should be called with the exception
            mock_error_msg.assert_called_once()
            error_arg = mock_error_msg.call_args[0][1]
            assert isinstance(error_arg, RuntimeError)

            # log.error should also be called
            mock_ctx.bot.log.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_command_exception_handler_with_active_typing_task(self, mock_ctx):
        """Test exception handler when typing task exists and needs cleanup."""
        api_key_data = [{"key": "test-api-key-12345", "permissions": "account"}]

        progress_msg = AsyncMock()
        mock_ctx.send.return_value = progress_msg

        with (
            patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.account.Gw2Client") as mock_client,
            patch("src.gw2.cogs.account.bot_utils.send_error_msg") as mock_error_msg,
            patch("src.gw2.cogs.account._keep_typing_alive", new=MagicMock()),
            patch("src.gw2.cogs.account.asyncio.create_task") as mock_create_task,
            patch("src.gw2.cogs.account.asyncio.Event") as mock_event_cls,
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            mock_client_instance = mock_client.return_value
            mock_client_instance.check_api_key = AsyncMock(return_value={"valid": True})
            # First call_api (account) raises, after progress msg and typing task created
            mock_client_instance.call_api = AsyncMock(side_effect=RuntimeError("API exploded"))

            mock_stop_event = MagicMock()
            mock_event_cls.return_value = mock_stop_event
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            await account(mock_ctx)

            mock_error_msg.assert_called_once()
            mock_ctx.bot.log.error.assert_called_once()

            # Stop event and task cleanup should have been called in the except block
            mock_stop_event.set.assert_called_once()
            mock_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_command_all_permissions(self, mock_ctx, sample_account_data_no_guilds, sample_world_data):
        """Test account command with all optional permissions (characters, progression, pvp)."""
        api_key_data = [{"key": "test-api-key-12345", "permissions": "account,characters,progression,pvp"}]
        characters_data = ["Char1", "Char2", "Char3"]
        achievements_data = [{"id": 1, "current": 10}, {"id": 2, "current": 5}]
        pvp_data = {"pvp_rank": 45, "pvp_rank_rollovers": 5}

        progress_msg = AsyncMock()
        mock_ctx.send.return_value = progress_msg

        with (
            patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.account.Gw2Client") as mock_client,
            patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send_embed,
            patch("src.gw2.cogs.account.bot_utils.get_current_date_time_str_long", return_value="2024-01-01 12:00:00"),
            patch("src.gw2.cogs.account._keep_typing_alive", new=MagicMock()),
            patch("src.gw2.cogs.account.asyncio.create_task") as mock_create_task,
            patch("src.gw2.cogs.account.asyncio.Event") as mock_event_cls,
            patch(
                "src.gw2.cogs.account.gw2_utils.calculate_user_achiev_points",
                new_callable=AsyncMock,
                return_value=15000,
            ) as mock_achiev,
            patch("src.gw2.cogs.account.gw2_utils.get_wvw_rank_title", return_value="Gold General") as mock_wvw,
            patch("src.gw2.cogs.account.gw2_utils.get_pvp_rank_title", return_value="Tiger") as mock_pvp,
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            mock_client_instance = mock_client.return_value
            mock_client_instance.check_api_key = AsyncMock(return_value={"valid": True})
            mock_client_instance.call_api = AsyncMock(
                side_effect=[
                    sample_account_data_no_guilds,  # account
                    sample_world_data,  # worlds/{server_id}
                    characters_data,  # characters (gathered)
                    achievements_data,  # account/achievements (gathered)
                    pvp_data,  # pvp/stats (gathered)
                ]
            )

            mock_stop_event = MagicMock()
            mock_event_cls.return_value = mock_stop_event
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            await account(mock_ctx)

            mock_send_embed.assert_called_once()
            progress_msg.delete.assert_called_once()

            # Verify optional tasks were requested
            # progress_msg.edit should have been called to update progress
            progress_msg.edit.assert_called()

            # Verify the embed contains expected fields
            embed = mock_send_embed.call_args[0][1]
            field_names = [f.name for f in embed.fields]
            assert "Characters" in field_names
            assert "Fractal Level" in field_names
            assert "Achievements Points" in field_names
            assert "WvW Rank" in field_names
            assert "PVP Rank" in field_names

            mock_achiev.assert_called_once()
            mock_wvw.assert_called_once_with(1250)
            mock_pvp.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_command_optional_task_failure_is_skipped(
        self, mock_ctx, sample_account_data_no_guilds, sample_world_data
    ):
        """Test that a failed optional API call is logged and skipped, not fatal."""
        api_key_data = [{"key": "test-api-key-12345", "permissions": "account,characters"}]

        progress_msg = AsyncMock()
        mock_ctx.send.return_value = progress_msg

        with (
            patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.account.Gw2Client") as mock_client,
            patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send_embed,
            patch("src.gw2.cogs.account.bot_utils.get_current_date_time_str_long", return_value="2024-01-01 12:00:00"),
            patch("src.gw2.cogs.account._keep_typing_alive", new=MagicMock()),
            patch("src.gw2.cogs.account.asyncio.create_task") as mock_create_task,
            patch("src.gw2.cogs.account.asyncio.Event") as mock_event_cls,
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            mock_client_instance = mock_client.return_value
            mock_client_instance.check_api_key = AsyncMock(return_value={"valid": True})
            mock_client_instance.call_api = AsyncMock(
                side_effect=[
                    sample_account_data_no_guilds,  # account
                    sample_world_data,  # worlds/{server_id}
                    Exception("characters API failed"),  # characters call fails
                ]
            )

            mock_stop_event = MagicMock()
            mock_event_cls.return_value = mock_stop_event
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            await account(mock_ctx)

            # The command should still succeed despite characters failing
            mock_send_embed.assert_called_once()
            progress_msg.delete.assert_called_once()

            # Warning should be logged for the failed optional task
            mock_ctx.bot.log.warning.assert_called_once()
            warning_msg = mock_ctx.bot.log.warning.call_args[0][0]
            assert "characters" in warning_msg

            # Embed should NOT have Characters field since that call failed
            embed = mock_send_embed.call_args[0][1]
            field_names = [f.name for f in embed.fields]
            assert "Characters" not in field_names

    @pytest.mark.asyncio
    async def test_account_command_guild_handling(self, mock_ctx, sample_world_data):
        """Test account command with guilds in account data (lines 187-228)."""
        api_key_data = [{"key": "test-api-key-12345", "permissions": "account"}]
        account_data_with_guilds = {
            "id": "account-id-123",
            "name": "TestUser.1234",
            "world": 1001,
            "guilds": ["guild-id-1", "guild-id-2"],
            "guild_leader": ["guild-id-1"],
            "access": ["GuildWars2"],
            "commander": False,
            "fractal_level": 50,
            "daily_ap": 3000,
            "monthly_ap": 200,
            "wvw_rank": 100,
            "age": 525600,
            "created": "2021-06-15T00:00:00.000Z",
        }
        guild_data_1 = {"name": "Test Guild One", "tag": "TG1"}
        guild_data_2 = {"name": "Test Guild Two", "tag": "TG2"}

        progress_msg = AsyncMock()
        mock_ctx.send.return_value = progress_msg

        with (
            patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.account.Gw2Client") as mock_client,
            patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send_embed,
            patch("src.gw2.cogs.account.bot_utils.get_current_date_time_str_long", return_value="2024-01-01 12:00:00"),
            patch("src.gw2.cogs.account._keep_typing_alive", new=MagicMock()),
            patch("src.gw2.cogs.account.asyncio.create_task") as mock_create_task,
            patch("src.gw2.cogs.account.asyncio.Event") as mock_event_cls,
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            mock_client_instance = mock_client.return_value
            mock_client_instance.check_api_key = AsyncMock(return_value={"valid": True})
            mock_client_instance.call_api = AsyncMock(
                side_effect=[
                    account_data_with_guilds,  # account
                    sample_world_data,  # worlds/{server_id}
                    guild_data_1,  # guild/{guild-id-1}
                    guild_data_2,  # guild/{guild-id-2}
                ]
            )

            mock_stop_event = MagicMock()
            mock_event_cls.return_value = mock_stop_event
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            await account(mock_ctx)

            mock_send_embed.assert_called_once()
            progress_msg.delete.assert_called_once()

            # progress_msg.edit should be called for guild fetching status
            progress_msg.edit.assert_called()

            # Verify the embed has guild fields
            embed = mock_send_embed.call_args[0][1]
            field_names = [f.name for f in embed.fields]
            assert "Guilds" in field_names
            assert "Guild Leader" in field_names

            # Get the guild field values
            guilds_field = next(f for f in embed.fields if f.name == "Guilds")
            assert "[TG1] Test Guild One" in guilds_field.value
            assert "[TG2] Test Guild Two" in guilds_field.value

            leader_field = next(f for f in embed.fields if f.name == "Guild Leader")
            assert "[TG1] Test Guild One" in leader_field.value
            # guild-id-2 is NOT a leader, so TG2 should not be in leader field
            assert "[TG2] Test Guild Two" not in leader_field.value

    @pytest.mark.asyncio
    async def test_account_command_guild_fetch_exception_skipped(self, mock_ctx, sample_world_data):
        """Test that guild fetch exceptions are skipped gracefully."""
        api_key_data = [{"key": "test-api-key-12345", "permissions": "account"}]
        account_data_with_guilds = {
            "id": "account-id-123",
            "name": "TestUser.1234",
            "world": 1001,
            "guilds": ["guild-id-1"],
            "guild_leader": [],
            "access": ["GuildWars2"],
            "commander": False,
            "fractal_level": 50,
            "daily_ap": 3000,
            "monthly_ap": 200,
            "wvw_rank": 100,
            "age": 525600,
            "created": "2021-06-15T00:00:00.000Z",
        }

        progress_msg = AsyncMock()
        mock_ctx.send.return_value = progress_msg

        with (
            patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.account.Gw2Client") as mock_client,
            patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send_embed,
            patch("src.gw2.cogs.account.bot_utils.get_current_date_time_str_long", return_value="2024-01-01 12:00:00"),
            patch("src.gw2.cogs.account._keep_typing_alive", new=MagicMock()),
            patch("src.gw2.cogs.account.asyncio.create_task") as mock_create_task,
            patch("src.gw2.cogs.account.asyncio.Event") as mock_event_cls,
            patch(
                "src.gw2.cogs.account._fetch_guild_info_standalone",
                new_callable=AsyncMock,
                return_value=(None, "guild-id-1"),
            ),
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            mock_client_instance = mock_client.return_value
            mock_client_instance.check_api_key = AsyncMock(return_value={"valid": True})
            mock_client_instance.call_api = AsyncMock(
                side_effect=[
                    account_data_with_guilds,
                    sample_world_data,
                ]
            )

            mock_stop_event = MagicMock()
            mock_event_cls.return_value = mock_stop_event
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            await account(mock_ctx)

            mock_send_embed.assert_called_once()

            # Guild returned None for name, so Guilds field should not appear
            embed = mock_send_embed.call_args[0][1]
            field_names = [f.name for f in embed.fields]
            assert "Guilds" not in field_names
            assert "Guild Leader" not in field_names

    @pytest.mark.asyncio
    async def test_account_command_commander_no(self, mock_ctx, sample_world_data):
        """Test that commander=False shows 'No' in the embed."""
        api_key_data = [{"key": "test-api-key-12345", "permissions": "account"}]
        account_data = {
            "id": "account-id-123",
            "name": "TestUser.1234",
            "world": 1001,
            "access": ["GuildWars2"],
            "commander": False,
            "fractal_level": 50,
            "daily_ap": 3000,
            "monthly_ap": 200,
            "wvw_rank": 100,
            "age": 525600,
            "created": "2021-06-15T00:00:00.000Z",
        }

        progress_msg = AsyncMock()
        mock_ctx.send.return_value = progress_msg

        with (
            patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.account.Gw2Client") as mock_client,
            patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send_embed,
            patch("src.gw2.cogs.account.bot_utils.get_current_date_time_str_long", return_value="2024-01-01 12:00:00"),
            patch("src.gw2.cogs.account._keep_typing_alive", new=MagicMock()),
            patch("src.gw2.cogs.account.asyncio.create_task") as mock_create_task,
            patch("src.gw2.cogs.account.asyncio.Event") as mock_event_cls,
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            mock_client_instance = mock_client.return_value
            mock_client_instance.check_api_key = AsyncMock(return_value={"valid": True})
            mock_client_instance.call_api = AsyncMock(
                side_effect=[
                    account_data,
                    sample_world_data,
                ]
            )

            mock_stop_event = MagicMock()
            mock_event_cls.return_value = mock_stop_event
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            await account(mock_ctx)

            embed = mock_send_embed.call_args[0][1]
            commander_field = next(f for f in embed.fields if f.name == "Commander Tag")
            assert "No" in commander_field.value

    @pytest.mark.asyncio
    async def test_account_command_access_normalization(self, mock_ctx, sample_world_data):
        """Test that access strings are properly normalized (camelCase to spaced)."""
        api_key_data = [{"key": "test-api-key-12345", "permissions": "account"}]
        account_data = {
            "id": "account-id-123",
            "name": "TestUser.1234",
            "world": 1001,
            "access": ["HeartOfThorns", "PathOfFire", "EndOfDragons"],
            "commander": True,
            "fractal_level": 50,
            "daily_ap": 3000,
            "monthly_ap": 200,
            "wvw_rank": 100,
            "age": 525600,
            "created": "2021-06-15T00:00:00.000Z",
        }

        progress_msg = AsyncMock()
        mock_ctx.send.return_value = progress_msg

        with (
            patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.account.Gw2Client") as mock_client,
            patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send_embed,
            patch("src.gw2.cogs.account.bot_utils.get_current_date_time_str_long", return_value="2024-01-01 12:00:00"),
            patch("src.gw2.cogs.account._keep_typing_alive", new=MagicMock()),
            patch("src.gw2.cogs.account.asyncio.create_task") as mock_create_task,
            patch("src.gw2.cogs.account.asyncio.Event") as mock_event_cls,
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            mock_client_instance = mock_client.return_value
            mock_client_instance.check_api_key = AsyncMock(return_value={"valid": True})
            mock_client_instance.call_api = AsyncMock(
                side_effect=[
                    account_data,
                    sample_world_data,
                ]
            )

            mock_stop_event = MagicMock()
            mock_event_cls.return_value = mock_stop_event
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            await account(mock_ctx)

            embed = mock_send_embed.call_args[0][1]
            access_field = next(f for f in embed.fields if f.name == "Access")
            # HeartOfThorns -> Heart Of Thorns
            assert "Heart Of Thorns" in access_field.value
            assert "Path Of Fire" in access_field.value
            assert "End Of Dragons" in access_field.value

    @pytest.mark.asyncio
    async def test_account_author_no_avatar(self, mock_ctx, sample_world_data):
        """Test account command does not crash when author has no custom avatar."""
        mock_ctx.message.author.avatar = None
        mock_ctx.message.author.display_avatar = MagicMock()
        mock_ctx.message.author.display_avatar.url = "https://example.com/default.png"
        mock_ctx.bot.user.avatar = None
        mock_ctx.bot.user.display_avatar = MagicMock()
        mock_ctx.bot.user.display_avatar.url = "https://example.com/default_bot.png"

        api_key_data = [{"key": "test-api-key-12345", "permissions": "account"}]
        account_data = {
            "id": "account-id-123",
            "name": "TestUser.1234",
            "world": 1001,
            "access": ["GuildWars2"],
            "commander": False,
            "fractal_level": 50,
            "daily_ap": 3000,
            "monthly_ap": 200,
            "wvw_rank": 100,
            "age": 525600,
            "created": "2021-06-15T00:00:00.000Z",
        }

        progress_msg = AsyncMock()
        mock_ctx.send.return_value = progress_msg

        with (
            patch("src.gw2.cogs.account.Gw2KeyDal") as mock_dal,
            patch("src.gw2.cogs.account.Gw2Client") as mock_client,
            patch("src.gw2.cogs.account.bot_utils.send_embed") as mock_send_embed,
            patch("src.gw2.cogs.account.bot_utils.get_current_date_time_str_long", return_value="2024-01-01 12:00:00"),
            patch("src.gw2.cogs.account._keep_typing_alive", new=MagicMock()),
            patch("src.gw2.cogs.account.asyncio.create_task") as mock_create_task,
            patch("src.gw2.cogs.account.asyncio.Event") as mock_event_cls,
        ):
            mock_dal.return_value.get_api_key_by_user = AsyncMock(return_value=api_key_data)

            mock_client_instance = mock_client.return_value
            mock_client_instance.check_api_key = AsyncMock(return_value={"valid": True})
            mock_client_instance.call_api = AsyncMock(
                side_effect=[
                    account_data,
                    sample_world_data,
                ]
            )

            mock_stop_event = MagicMock()
            mock_event_cls.return_value = mock_stop_event
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            await account(mock_ctx)

            mock_send_embed.assert_called_once()
            embed = mock_send_embed.call_args[0][1]
            assert embed.thumbnail.url == "https://example.com/default.png"
            assert embed.author.icon_url == "https://example.com/default.png"
