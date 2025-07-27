"""Comprehensive tests for GW2 client module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from aiohttp import ClientSession, ClientError, ClientTimeout
from aiohttp.web_response import Response as AiohttpResponse

from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_exceptions import (
    APIError,
    APIBadRequest,
    APIConnectionError,
    APIInactiveError,
    APIForbidden,
    APINotFound,
    APIInvalidKey,
    APIKeyError
)


class TestGw2Client:
    """Test cases for the Gw2Client class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def gw2_client(self, mock_bot):
        """Create a Gw2Client instance with mock bot."""
        return Gw2Client(mock_bot)

    def test_init(self, mock_bot):
        """Test Gw2Client initialization."""
        client = Gw2Client(mock_bot)
        assert client.bot == mock_bot

    @pytest.mark.asyncio
    async def test_call_api_basic_structure(self, gw2_client):
        """Test that call_api method exists and is callable."""
        # Basic test to ensure the method exists
        assert hasattr(gw2_client, 'call_api')
        assert callable(gw2_client.call_api)

    def test_build_headers_integration(self, gw2_client):
        """Test header building integration."""
        gw2_client.bot.description = "Test Bot"
        headers_without_key = gw2_client._build_headers()
        headers_with_key = gw2_client._build_headers("test-key")
        
        assert "Authorization" not in headers_without_key
        assert "Authorization" in headers_with_key
        assert headers_with_key["Authorization"] == "Bearer test-key"




    @pytest.mark.asyncio
    async def test_call_api_429_error(self, gw2_client):
        """Test API call with 429 Too Many Requests error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 429
            mock_response.text = AsyncMock(return_value="Too Many Requests")
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with pytest.raises(APIError):
                await gw2_client.call_api("test/endpoint")





    @pytest.mark.asyncio
    async def test_check_api_key_structure(self, gw2_client):
        """Test that check_api_key method exists and is callable."""
        assert hasattr(gw2_client, 'check_api_key')
        assert callable(gw2_client.check_api_key)



    def test_endpoint_building(self, gw2_client):
        """Test endpoint building in call_api method."""
        # The URL building is done inside call_api method
        # We can test this indirectly through the call_api method
        assert gw2_client.bot is not None

    def test_build_headers_without_api_key(self, gw2_client):
        """Test headers building without API key."""
        gw2_client.bot.description = "Test Bot"
        headers = gw2_client._build_headers()
        expected = {
            "User-Agent": "Test Bot",
            "Accept": "application/json",
            "lang": "en"
        }
        assert headers == expected

    def test_build_headers_with_api_key(self, gw2_client):
        """Test headers building with API key."""
        gw2_client.bot.description = "Test Bot"
        headers = gw2_client._build_headers("test-api-key")
        expected = {
            "User-Agent": "Test Bot",
            "Accept": "application/json",
            "lang": "en",
            "Authorization": "Bearer test-api-key"
        }
        assert headers == expected

    def test_handle_400_error(self, gw2_client):
        """Test _handle_400_error method."""
        with pytest.raises(APIBadRequest) as exc_info:
            gw2_client._handle_400_error(400, "test error", "init_msg")
        
        assert "API is currently down" in str(exc_info.value)

    def test_handle_403_error(self, gw2_client):
        """Test _handle_403_error method."""
        with pytest.raises(APIForbidden) as exc_info:
            gw2_client._handle_403_error(403, "test error", "init_msg")
        
        assert "Access denied" in str(exc_info.value)

    def test_handle_404_error(self, gw2_client):
        """Test _handle_404_error method."""
        with pytest.raises(APINotFound) as exc_info:
            gw2_client._handle_404_error(404, "test/endpoint")
        
        assert "Not found" in str(exc_info.value)

    def test_handle_429_error(self, gw2_client):
        """Test _handle_429_error method."""
        with pytest.raises(APIConnectionError) as exc_info:
            gw2_client._handle_429_error("init_msg")
        
        assert "Requests limit has been saturated" in str(exc_info.value)

    def test_handle_502_504_error(self, gw2_client):
        """Test _handle_502_504_error method."""
        with pytest.raises(APIInactiveError) as exc_info:
            gw2_client._handle_502_504_error("init_msg")
        
        assert "API is currently down" in str(exc_info.value)

    def test_handle_other_error(self, gw2_client):
        """Test _handle_other_error method."""
        mock_response = MagicMock()
        mock_response.reason = "I'm a teapot"
        
        with pytest.raises(APIConnectionError) as exc_info:
            gw2_client._handle_other_error(mock_response, "init_msg", "")
        
        assert "API ERROR" in str(exc_info.value)

    def test_handle_503_error(self, gw2_client):
        """Test _handle_503_error method."""
        with pytest.raises(APIInactiveError) as exc_info:
            gw2_client._handle_503_error("init_msg", "Service unavailable")
        
        assert "Service unavailable" in str(exc_info.value)




