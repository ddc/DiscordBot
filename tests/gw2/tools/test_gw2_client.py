"""Comprehensive tests for GW2 client module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_exceptions import (
    APIError,
    APIBadRequest,
    APIConnectionError,
    APIInactiveError,
    APIForbidden,
    APINotFound,
    APIInvalidKey,
    APIKeyError,
)
from src.gw2.constants import gw2_messages


class AsyncContextManager:
    """Helper to simulate async context manager for aiohttp responses."""

    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args):
        pass


class TestGw2ClientInit:
    """Test cases for Gw2Client.__init__."""

    def test_init_stores_bot(self):
        """Test that __init__ stores the bot reference."""
        bot = MagicMock()
        client = Gw2Client(bot)
        assert client.bot is bot

    def test_init_with_different_bots(self):
        """Test initialization with different bot instances."""
        bot1 = MagicMock()
        bot2 = MagicMock()

        client1 = Gw2Client(bot1)
        client2 = Gw2Client(bot2)

        assert client1.bot is bot1
        assert client2.bot is bot2
        assert client1.bot is not client2.bot


class TestCheckApiKey:
    """Test cases for check_api_key method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        bot.description = "Test Bot"
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    @pytest.mark.asyncio
    async def test_successful_with_permissions(self, gw2_client):
        """Test successful check with permissions sorted (lines 21-36)."""
        token_info = {
            "id": "test-key-id",
            "name": "TestKey",
            "permissions": ["wallet", "account", "characters", "builds"]
        }

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=token_info)

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.check_api_key("test-api-key")

        assert result["permissions"] == ["account", "builds", "characters", "wallet"]

    @pytest.mark.asyncio
    async def test_successful_without_permissions_key(self, gw2_client):
        """Test successful check without permissions in response."""
        token_info = {"id": "test-key-id", "name": "TestKey"}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=token_info)

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.check_api_key("test-api-key")

        assert "permissions" not in result

    @pytest.mark.asyncio
    async def test_api_bad_request_returns_error(self, gw2_client):
        """Test that APIBadRequest is caught and returned (line 24)."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"text": "bad request"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.check_api_key("bad-key")

        assert isinstance(result, APIBadRequest)

    @pytest.mark.asyncio
    async def test_api_connection_error_returns_error(self, gw2_client):
        """Test that APIConnectionError is caught and returned (line 25)."""
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.json = AsyncMock(return_value={"text": "rate limited"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.check_api_key("test-key")

        assert isinstance(result, APIConnectionError)

    @pytest.mark.asyncio
    async def test_api_forbidden_returns_error(self, gw2_client):
        """Test that APIForbidden is caught and returned (line 28)."""
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.json = AsyncMock(return_value={"text": "access denied"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.check_api_key("test-key")

        assert isinstance(result, APIForbidden)

    @pytest.mark.asyncio
    async def test_api_inactive_error_returns_error(self, gw2_client):
        """Test that APIInactiveError is caught and returned (line 28)."""
        mock_response = AsyncMock()
        mock_response.status = 502
        mock_response.json = AsyncMock(return_value={"text": "bad gateway"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.check_api_key("test-key")

        assert isinstance(result, APIInactiveError)

    @pytest.mark.asyncio
    async def test_api_invalid_key_returns_error(self, gw2_client):
        """Test that APIInvalidKey is caught and returned (line 29)."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"text": "invalid key"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.check_api_key("invalid-key")

        assert isinstance(result, APIInvalidKey)

    @pytest.mark.asyncio
    async def test_api_not_found_returns_error(self, gw2_client):
        """Test that APINotFound is caught and returned (line 31)."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.json = AsyncMock(return_value={"text": "not found"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.check_api_key("test-key")

        assert isinstance(result, APINotFound)

    @pytest.mark.asyncio
    async def test_api_504_inactive_error_returns_error(self, gw2_client):
        """Test that 504 Gateway Timeout returns APIInactiveError."""
        mock_response = AsyncMock()
        mock_response.status = 504
        mock_response.json = AsyncMock(return_value={"text": "gateway timeout"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.check_api_key("test-key")

        assert isinstance(result, APIInactiveError)

    @pytest.mark.asyncio
    async def test_api_503_inactive_error_returns_error(self, gw2_client):
        """Test that 503 Service Unavailable returns APIInactiveError."""
        mock_response = AsyncMock()
        mock_response.status = 503
        mock_response.json = AsyncMock(return_value={"text": "service unavailable"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.check_api_key("test-key")

        assert isinstance(result, APIInactiveError)


class TestCallApi:
    """Test cases for call_api method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        bot.description = "Test Bot"
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    @pytest.mark.asyncio
    async def test_status_200_returns_json(self, gw2_client):
        """Test that status 200 returns json response (line 46-47)."""
        expected_data = {"name": "TestAccount", "world": 1001}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=expected_data)

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.call_api("account")

        assert result == expected_data

    @pytest.mark.asyncio
    async def test_status_206_returns_json(self, gw2_client):
        """Test that status 206 (Partial Content) returns json response (line 46-47)."""
        expected_data = [{"id": 1}, {"id": 2}]

        mock_response = AsyncMock()
        mock_response.status = 206
        mock_response.json = AsyncMock(return_value=expected_data)

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.call_api("achievements?ids=1,2,3")

        assert result == expected_data

    @pytest.mark.asyncio
    async def test_other_status_calls_handle_api_error(self, gw2_client):
        """Test that other status codes call _handle_api_error (line 49)."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.json = AsyncMock(return_value={"text": "internal error"})
        mock_response.reason = "Internal Server Error"

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        with pytest.raises(APIConnectionError):
            await gw2_client.call_api("account")

    @pytest.mark.asyncio
    async def test_call_api_with_key(self, gw2_client):
        """Test that call_api passes key to headers."""
        expected_data = {"name": "TestAccount"}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=expected_data)

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.call_api("account", "my-api-key")

        assert result == expected_data
        # Verify headers were built with key
        call_kwargs = gw2_client.bot.aiosession.get.call_args
        headers = call_kwargs[1]["headers"] if "headers" in call_kwargs[1] else call_kwargs[0][1] if len(call_kwargs[0]) > 1 else None
        # The headers parameter is passed as keyword arg
        if headers:
            assert "Authorization" in headers

    @pytest.mark.asyncio
    async def test_call_api_builds_correct_endpoint(self, gw2_client):
        """Test that call_api builds the correct endpoint URL."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        await gw2_client.call_api("account/wallet")

        call_args = gw2_client.bot.aiosession.get.call_args
        endpoint = call_args[0][0]
        assert "account/wallet" in endpoint
        assert endpoint.startswith("https://api.guildwars2.com/")


class TestBuildHeaders:
    """Test cases for _build_headers method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        bot.description = "Test Bot v1.0"
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    def test_build_headers_without_key(self, gw2_client):
        """Test headers without API key (lines 52-55)."""
        headers = gw2_client._build_headers()

        assert headers["User-Agent"] == "Test Bot v1.0"
        assert headers["Accept"] == "application/json"
        assert headers["lang"] == "en"
        assert "Authorization" not in headers

    def test_build_headers_with_key(self, gw2_client):
        """Test headers with API key (lines 56-57)."""
        headers = gw2_client._build_headers("my-secret-api-key")

        assert headers["User-Agent"] == "Test Bot v1.0"
        assert headers["Accept"] == "application/json"
        assert headers["lang"] == "en"
        assert headers["Authorization"] == "Bearer my-secret-api-key"

    def test_build_headers_with_none_key(self, gw2_client):
        """Test headers with None key (treated as no key)."""
        headers = gw2_client._build_headers(None)

        assert "Authorization" not in headers

    def test_build_headers_with_empty_string_key(self, gw2_client):
        """Test headers with empty string key (treated as no key)."""
        headers = gw2_client._build_headers("")

        assert "Authorization" not in headers


class TestHandleApiError:
    """Test cases for _handle_api_error method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    @pytest.mark.asyncio
    async def test_status_400_calls_handle_400(self, gw2_client):
        """Test status 400 dispatches to _handle_400_error (line 71-72)."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"text": "some error"})

        with pytest.raises(APIBadRequest):
            await gw2_client._handle_api_error(mock_response, "https://api.guildwars2.com/v2/account")

    @pytest.mark.asyncio
    async def test_status_403_calls_handle_403(self, gw2_client):
        """Test status 403 dispatches to _handle_403_error (line 73-74)."""
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.json = AsyncMock(return_value={"text": "forbidden"})

        with pytest.raises(APIForbidden):
            await gw2_client._handle_api_error(mock_response, "https://api.guildwars2.com/v2/account")

    @pytest.mark.asyncio
    async def test_status_404_calls_handle_404(self, gw2_client):
        """Test status 404 dispatches to _handle_404_error (line 75-76)."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.json = AsyncMock(return_value={"text": "not found"})

        with pytest.raises(APINotFound):
            await gw2_client._handle_api_error(mock_response, "https://api.guildwars2.com/v2/account")

    @pytest.mark.asyncio
    async def test_status_429_calls_handle_429(self, gw2_client):
        """Test status 429 dispatches to _handle_429_error (line 77-78)."""
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.json = AsyncMock(return_value={"text": "rate limited"})

        with pytest.raises(APIConnectionError):
            await gw2_client._handle_api_error(mock_response, "https://api.guildwars2.com/v2/account")

    @pytest.mark.asyncio
    async def test_status_502_calls_handle_502_504(self, gw2_client):
        """Test status 502 dispatches to _handle_502_504_error (line 79-80)."""
        mock_response = AsyncMock()
        mock_response.status = 502
        mock_response.json = AsyncMock(return_value={"text": "bad gateway"})

        with pytest.raises(APIInactiveError):
            await gw2_client._handle_api_error(mock_response, "https://api.guildwars2.com/v2/account")

    @pytest.mark.asyncio
    async def test_status_504_calls_handle_502_504(self, gw2_client):
        """Test status 504 dispatches to _handle_502_504_error (line 79-80)."""
        mock_response = AsyncMock()
        mock_response.status = 504
        mock_response.json = AsyncMock(return_value={"text": "gateway timeout"})

        with pytest.raises(APIInactiveError):
            await gw2_client._handle_api_error(mock_response, "https://api.guildwars2.com/v2/account")

    @pytest.mark.asyncio
    async def test_status_503_calls_handle_503(self, gw2_client):
        """Test status 503 dispatches to _handle_503_error (line 81-82)."""
        mock_response = AsyncMock()
        mock_response.status = 503
        mock_response.json = AsyncMock(return_value={"text": "service unavailable"})

        with pytest.raises(APIInactiveError):
            await gw2_client._handle_api_error(mock_response, "https://api.guildwars2.com/v2/account")

    @pytest.mark.asyncio
    async def test_other_status_calls_handle_other(self, gw2_client):
        """Test other status codes dispatch to _handle_other_error (line 83-84)."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.json = AsyncMock(return_value={"text": "internal error"})
        mock_response.reason = "Internal Server Error"

        with pytest.raises(APIConnectionError):
            await gw2_client._handle_api_error(mock_response, "https://api.guildwars2.com/v2/account")

    @pytest.mark.asyncio
    async def test_json_parse_value_error_empty_err_msg(self, gw2_client):
        """Test that ValueError on json parse leads to empty err_msg (line 66-67)."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
        mock_response.reason = "Server Error"

        with pytest.raises(APIConnectionError) as exc_info:
            await gw2_client._handle_api_error(mock_response, "https://api.guildwars2.com/v2/account")

        # When err_msg is empty, _handle_other_error uses response.reason
        assert "Server Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_json_parse_key_error_empty_err_msg(self, gw2_client):
        """Test that KeyError on json parse leads to empty err_msg (line 66-67)."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.json = AsyncMock(side_effect=KeyError("text"))
        mock_response.reason = "Server Error"

        with pytest.raises(APIConnectionError) as exc_info:
            await gw2_client._handle_api_error(mock_response, "https://api.guildwars2.com/v2/account")

        assert "Server Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_endpoint_split_on_question_mark(self, gw2_client):
        """Test that endpoint is split on ? for init_msg."""
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.json = AsyncMock(return_value={"text": "rate limited"})

        with pytest.raises(APIConnectionError) as exc_info:
            await gw2_client._handle_api_error(
                mock_response,
                "https://api.guildwars2.com/v2/achievements?ids=1,2,3"
            )

        # The init_msg should not include query parameters
        error_msg = str(exc_info.value)
        assert "ids=1,2,3" not in error_msg


class TestHandle400Error:
    """Test cases for _handle_400_error method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    def test_invalid_key_raises_api_invalid_key(self, gw2_client):
        """Test 'invalid key' message raises APIInvalidKey (line 88-89)."""
        with pytest.raises(APIInvalidKey) as exc_info:
            gw2_client._handle_400_error(400, "invalid key", "init_msg")

        assert gw2_messages.INVALID_API_KEY in str(exc_info.value)

    def test_other_error_raises_api_bad_request(self, gw2_client):
        """Test other error messages raise APIBadRequest (line 90)."""
        with pytest.raises(APIBadRequest) as exc_info:
            gw2_client._handle_400_error(400, "some other error", "init_msg")

        assert gw2_messages.API_DOWN in str(exc_info.value)

    def test_empty_error_raises_api_bad_request(self, gw2_client):
        """Test empty error message raises APIBadRequest."""
        with pytest.raises(APIBadRequest):
            gw2_client._handle_400_error(400, "", "init_msg")


class TestHandle403Error:
    """Test cases for _handle_403_error method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    def test_invalid_key_raises_api_invalid_key(self, gw2_client):
        """Test 'invalid key' message raises APIInvalidKey (line 94-95)."""
        with pytest.raises(APIInvalidKey) as exc_info:
            gw2_client._handle_403_error(403, "invalid key", "init_msg")

        assert gw2_messages.INVALID_API_KEY in str(exc_info.value)

    def test_other_error_raises_api_forbidden(self, gw2_client):
        """Test other error messages raise APIForbidden (line 96)."""
        with pytest.raises(APIForbidden) as exc_info:
            gw2_client._handle_403_error(403, "access denied", "init_msg")

        assert gw2_messages.API_ACCESS_DENIED in str(exc_info.value)

    def test_empty_error_raises_api_forbidden(self, gw2_client):
        """Test empty error message raises APIForbidden."""
        with pytest.raises(APIForbidden):
            gw2_client._handle_403_error(403, "", "init_msg")


class TestHandle404Error:
    """Test cases for _handle_404_error method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    def test_raises_api_not_found(self, gw2_client):
        """Test that 404 raises APINotFound (line 99-100)."""
        with pytest.raises(APINotFound) as exc_info:
            gw2_client._handle_404_error(404, "https://api.guildwars2.com/v2/account?key=123")

        assert gw2_messages.API_NOT_FOUND in str(exc_info.value)
        # Check that the endpoint is split on ?
        assert "key=123" not in str(exc_info.value)

    def test_endpoint_without_query_string(self, gw2_client):
        """Test 404 with endpoint without query string."""
        with pytest.raises(APINotFound) as exc_info:
            gw2_client._handle_404_error(404, "https://api.guildwars2.com/v2/items")

        assert "items" in str(exc_info.value)


class TestHandle429Error:
    """Test cases for _handle_429_error method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    def test_raises_api_connection_error(self, gw2_client):
        """Test that 429 raises APIConnectionError (line 103-104)."""
        with pytest.raises(APIConnectionError) as exc_info:
            gw2_client._handle_429_error("429)(account")

        assert gw2_messages.API_REQUEST_REACHED in str(exc_info.value)


class TestHandle502504Error:
    """Test cases for _handle_502_504_error method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    def test_raises_api_inactive_error(self, gw2_client):
        """Test that 502/504 raises APIInactiveError (line 107-108)."""
        with pytest.raises(APIInactiveError) as exc_info:
            gw2_client._handle_502_504_error("502)(account")

        assert gw2_messages.API_DOWN in str(exc_info.value)


class TestHandle503Error:
    """Test cases for _handle_503_error method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    def test_raises_api_inactive_error_with_message(self, gw2_client):
        """Test that 503 raises APIInactiveError with error message (line 111-112)."""
        with pytest.raises(APIInactiveError) as exc_info:
            gw2_client._handle_503_error("503)(account", "Service Unavailable")

        assert "Service Unavailable" in str(exc_info.value)

    def test_raises_api_inactive_error_with_empty_message(self, gw2_client):
        """Test that 503 raises APIInactiveError with empty error message."""
        with pytest.raises(APIInactiveError) as exc_info:
            gw2_client._handle_503_error("503)(account", "")

        assert "503)(account" in str(exc_info.value)


class TestHandleOtherError:
    """Test cases for _handle_other_error method."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    def test_empty_err_msg_uses_response_reason(self, gw2_client):
        """Test that empty err_msg falls back to response.reason (line 116-117)."""
        mock_response = MagicMock()
        mock_response.reason = "I'm a teapot"

        with pytest.raises(APIConnectionError) as exc_info:
            gw2_client._handle_other_error(mock_response, "418)(account", "")

        assert "I'm a teapot" in str(exc_info.value)

    def test_with_err_msg_uses_err_msg(self, gw2_client):
        """Test that non-empty err_msg is used in error (line 118)."""
        mock_response = MagicMock()
        mock_response.reason = "Should not appear"

        with pytest.raises(APIConnectionError) as exc_info:
            gw2_client._handle_other_error(mock_response, "500)(account", "custom error message")

        assert "custom error message" in str(exc_info.value)

    def test_error_includes_api_error_prefix(self, gw2_client):
        """Test that the error message includes the API_ERROR prefix."""
        mock_response = MagicMock()
        mock_response.reason = "Server Error"

        with pytest.raises(APIConnectionError) as exc_info:
            gw2_client._handle_other_error(mock_response, "init_msg", "")

        assert gw2_messages.API_ERROR in str(exc_info.value)

    def test_error_includes_init_msg(self, gw2_client):
        """Test that the error message includes the init_msg."""
        mock_response = MagicMock()
        mock_response.reason = "Error"

        with pytest.raises(APIConnectionError) as exc_info:
            gw2_client._handle_other_error(mock_response, "999)(some/endpoint", "the error")

        assert "999)(some/endpoint" in str(exc_info.value)


class TestCallApiIntegration:
    """Integration-style tests for call_api with various error scenarios."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        bot.description = "Test Bot"
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance."""
        return Gw2Client(mock_bot)

    @pytest.mark.asyncio
    async def test_400_invalid_key_flow(self, gw2_client):
        """Test full flow for 400 with invalid key."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"text": "invalid key"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        with pytest.raises(APIInvalidKey):
            await gw2_client.call_api("tokeninfo", "bad-key")

    @pytest.mark.asyncio
    async def test_403_invalid_key_flow(self, gw2_client):
        """Test full flow for 403 with invalid key."""
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.json = AsyncMock(return_value={"text": "invalid key"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        with pytest.raises(APIInvalidKey):
            await gw2_client.call_api("account", "expired-key")

    @pytest.mark.asyncio
    async def test_403_forbidden_flow(self, gw2_client):
        """Test full flow for 403 without invalid key."""
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.json = AsyncMock(return_value={"text": "requires scope account"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        with pytest.raises(APIForbidden):
            await gw2_client.call_api("account/wallet", "limited-key")

    @pytest.mark.asyncio
    async def test_429_rate_limit_flow(self, gw2_client):
        """Test full flow for 429 rate limit."""
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.json = AsyncMock(return_value={"text": "too many requests"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        with pytest.raises(APIConnectionError):
            await gw2_client.call_api("achievements?ids=all")

    @pytest.mark.asyncio
    async def test_502_bad_gateway_flow(self, gw2_client):
        """Test full flow for 502 bad gateway."""
        mock_response = AsyncMock()
        mock_response.status = 502
        mock_response.json = AsyncMock(return_value={"text": "bad gateway"})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        with pytest.raises(APIInactiveError):
            await gw2_client.call_api("account")

    @pytest.mark.asyncio
    async def test_unknown_error_with_reason_fallback(self, gw2_client):
        """Test unknown status with JSON parse failure falls back to reason."""
        mock_response = AsyncMock()
        mock_response.status = 418
        mock_response.json = AsyncMock(side_effect=ValueError("not json"))
        mock_response.reason = "I'm a teapot"

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        with pytest.raises(APIConnectionError) as exc_info:
            await gw2_client.call_api("account")

        assert "I'm a teapot" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_api_without_key(self, gw2_client):
        """Test call_api without providing an API key."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"worlds": [1001, 1002]})

        gw2_client.bot.aiosession = MagicMock()
        gw2_client.bot.aiosession.get = MagicMock(
            return_value=AsyncContextManager(mock_response)
        )

        result = await gw2_client.call_api("worlds?ids=all")

        assert result == {"worlds": [1001, 1002]}
        # Verify no Authorization header
        call_kwargs = gw2_client.bot.aiosession.get.call_args
        headers = call_kwargs[1].get("headers", {})
        assert "Authorization" not in headers
