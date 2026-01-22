"""Comprehensive tests for GW2 exceptions module."""

import pytest
from unittest.mock import MagicMock

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


class TestAPIError:
    """Test cases for the base APIError exception."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot with logging."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    @pytest.fixture
    def mock_bot_no_log(self):
        """Create a mock bot without logging."""
        bot = MagicMock()
        del bot.log  # Remove log attribute
        return bot

    def test_api_error_initialization(self, mock_bot):
        """Test APIError initialization with logging."""
        error_message = "Test API error"
        
        error = APIError(mock_bot, error_message)
        
        assert str(error) == error_message
        assert error.bot == mock_bot
        assert error.message == error_message
        mock_bot.log.error.assert_called_once_with("GW2 API Error: Test API error")

    def test_api_error_without_log(self, mock_bot_no_log):
        """Test APIError initialization without logging capability."""
        error_message = "Test API error without log"
        
        # Should not raise an exception even without log
        error = APIError(mock_bot_no_log, error_message)
        
        assert str(error) == error_message
        assert error.bot == mock_bot_no_log
        assert error.message == error_message

    def test_api_error_with_none_log(self):
        """Test APIError initialization with None log."""
        bot = MagicMock()
        bot.log = None
        error_message = "Test API error with None log"
        
        # Should not raise an exception with None log
        error = APIError(bot, error_message)
        
        assert str(error) == error_message
        assert error.bot == bot
        assert error.message == error_message

    def test_api_error_inheritance(self, mock_bot):
        """Test that APIError inherits from Exception properly."""
        error = APIError(mock_bot, "Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, APIError)

    def test_api_error_with_empty_message(self, mock_bot):
        """Test APIError with empty message."""
        error = APIError(mock_bot, "")
        
        assert str(error) == ""
        assert error.message == ""
        mock_bot.log.error.assert_called_once_with("GW2 API Error: ")

    def test_api_error_with_special_characters(self, mock_bot):
        """Test APIError with special characters in message."""
        error_message = "API error with special chars: éñ@#$%^&*()"
        
        error = APIError(mock_bot, error_message)
        
        assert str(error) == error_message
        assert error.message == error_message
        mock_bot.log.error.assert_called_once_with(f"GW2 API Error: {error_message}")


class TestAPIBadRequest:
    """Test cases for APIBadRequest exception."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    def test_api_bad_request_inheritance(self, mock_bot):
        """Test that APIBadRequest inherits from APIError."""
        error = APIBadRequest(mock_bot, "Bad request error")
        
        assert isinstance(error, APIError)
        assert isinstance(error, APIBadRequest)
        assert isinstance(error, Exception)

    def test_api_bad_request_initialization(self, mock_bot):
        """Test APIBadRequest initialization."""
        error_message = "400 Bad Request"
        
        error = APIBadRequest(mock_bot, error_message)
        
        assert str(error) == error_message
        assert error.bot == mock_bot
        assert error.message == error_message
        mock_bot.log.error.assert_called_once_with("GW2 API Error: 400 Bad Request")


class TestAPIConnectionError:
    """Test cases for APIConnectionError exception."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    def test_api_connection_error_inheritance(self, mock_bot):
        """Test that APIConnectionError inherits from APIError."""
        error = APIConnectionError(mock_bot, "Connection error")
        
        assert isinstance(error, APIError)
        assert isinstance(error, APIConnectionError)
        assert isinstance(error, Exception)

    def test_api_connection_error_initialization(self, mock_bot):
        """Test APIConnectionError initialization."""
        error_message = "Connection to API failed"
        
        error = APIConnectionError(mock_bot, error_message)
        
        assert str(error) == error_message
        assert error.bot == mock_bot
        assert error.message == error_message
        mock_bot.log.error.assert_called_once_with("GW2 API Error: Connection to API failed")


class TestAPIInactiveError:
    """Test cases for APIInactiveError exception."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    def test_api_inactive_error_inheritance(self, mock_bot):
        """Test that APIInactiveError inherits from APIError."""
        error = APIInactiveError(mock_bot, "API inactive")
        
        assert isinstance(error, APIError)
        assert isinstance(error, APIInactiveError)
        assert isinstance(error, Exception)

    def test_api_inactive_error_initialization(self, mock_bot):
        """Test APIInactiveError initialization."""
        error_message = "API is currently down"
        
        error = APIInactiveError(mock_bot, error_message)
        
        assert str(error) == error_message
        assert error.bot == mock_bot
        assert error.message == error_message
        mock_bot.log.error.assert_called_once_with("GW2 API Error: API is currently down")


class TestAPIForbidden:
    """Test cases for APIForbidden exception."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    def test_api_forbidden_inheritance(self, mock_bot):
        """Test that APIForbidden inherits from APIError."""
        error = APIForbidden(mock_bot, "Forbidden access")
        
        assert isinstance(error, APIError)
        assert isinstance(error, APIForbidden)
        assert isinstance(error, Exception)

    def test_api_forbidden_initialization(self, mock_bot):
        """Test APIForbidden initialization."""
        error_message = "403 Forbidden - Insufficient permissions"
        
        error = APIForbidden(mock_bot, error_message)
        
        assert str(error) == error_message
        assert error.bot == mock_bot
        assert error.message == error_message
        mock_bot.log.error.assert_called_once_with("GW2 API Error: 403 Forbidden - Insufficient permissions")


class TestAPINotFound:
    """Test cases for APINotFound exception."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    def test_api_not_found_inheritance(self, mock_bot):
        """Test that APINotFound inherits from APIError."""
        error = APINotFound(mock_bot, "Not found")
        
        assert isinstance(error, APIError)
        assert isinstance(error, APINotFound)
        assert isinstance(error, Exception)

    def test_api_not_found_initialization(self, mock_bot):
        """Test APINotFound initialization."""
        error_message = "404 Not Found - Resource does not exist"
        
        error = APINotFound(mock_bot, error_message)
        
        assert str(error) == error_message
        assert error.bot == mock_bot
        assert error.message == error_message
        mock_bot.log.error.assert_called_once_with("GW2 API Error: 404 Not Found - Resource does not exist")


class TestAPIInvalidKey:
    """Test cases for APIInvalidKey exception."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    def test_api_invalid_key_inheritance(self, mock_bot):
        """Test that APIInvalidKey inherits from APIError."""
        error = APIInvalidKey(mock_bot, "Invalid API key")
        
        assert isinstance(error, APIError)
        assert isinstance(error, APIInvalidKey)
        assert isinstance(error, Exception)

    def test_api_invalid_key_initialization(self, mock_bot):
        """Test APIInvalidKey initialization."""
        error_message = "The provided API key is invalid"
        
        error = APIInvalidKey(mock_bot, error_message)
        
        assert str(error) == error_message
        assert error.bot == mock_bot
        assert error.message == error_message
        mock_bot.log.error.assert_called_once_with("GW2 API Error: The provided API key is invalid")


class TestAPIKeyError:
    """Test cases for APIKeyError exception."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    def test_api_key_error_inheritance(self, mock_bot):
        """Test that APIKeyError inherits from APIError."""
        error = APIKeyError(mock_bot, "API key error")
        
        assert isinstance(error, APIError)
        assert isinstance(error, APIKeyError)
        assert isinstance(error, Exception)

    def test_api_key_error_initialization(self, mock_bot):
        """Test APIKeyError initialization."""
        error_message = "General API key error occurred"
        
        error = APIKeyError(mock_bot, error_message)
        
        assert str(error) == error_message
        assert error.bot == mock_bot
        assert error.message == error_message
        mock_bot.log.error.assert_called_once_with("GW2 API Error: General API key error occurred")


class TestExceptionHierarchy:
    """Test cases for exception hierarchy and relationships."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    def test_all_exceptions_inherit_from_api_error(self, mock_bot):
        """Test that all specific exceptions inherit from APIError."""
        # Ensure log.error is a regular MagicMock, not AsyncMock
        mock_bot.log.error = MagicMock()
        
        exception_classes = [
            APIBadRequest,
            APIConnectionError,
            APIInactiveError,
            APIForbidden,
            APINotFound,
            APIInvalidKey,
            APIKeyError
        ]
        
        for exception_class in exception_classes:
            error = exception_class(mock_bot, "Test error")
            assert isinstance(error, APIError)
            assert isinstance(error, Exception)

    def test_exception_catching_hierarchy(self, mock_bot):
        """Test that exceptions can be caught by their parent classes."""
        # Ensure log.error is a regular MagicMock, not AsyncMock
        mock_bot.log.error = MagicMock()
        
        error = APIBadRequest(mock_bot, "Bad request")
        
        # Should be catchable as APIError
        try:
            raise error
        except APIError as e:
            assert isinstance(e, APIBadRequest)
            assert isinstance(e, APIError)
        
        # Should be catchable as Exception
        try:
            raise error
        except Exception as e:
            assert isinstance(e, APIBadRequest)
            assert isinstance(e, APIError)

    def test_exception_differentiation(self, mock_bot):
        """Test that different exception types can be differentiated."""
        bad_request = APIBadRequest(mock_bot, "Bad request")
        forbidden = APIForbidden(mock_bot, "Forbidden")
        not_found = APINotFound(mock_bot, "Not found")
        
        assert type(bad_request) != type(forbidden)
        assert type(forbidden) != type(not_found)
        assert type(bad_request) != type(not_found)
        
        assert isinstance(bad_request, APIBadRequest)
        assert not isinstance(bad_request, APIForbidden)
        assert not isinstance(bad_request, APINotFound)


class TestExceptionHandling:
    """Test cases for exception handling scenarios."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.log = MagicMock()
        return bot

    def test_exception_can_be_raised_and_caught(self, mock_bot):
        """Test that exceptions can be properly raised and caught."""
        error_message = "Test exception handling"
        
        with pytest.raises(APIError) as exc_info:
            raise APIError(mock_bot, error_message)
        
        assert str(exc_info.value) == error_message
        assert exc_info.value.bot == mock_bot
        assert exc_info.value.message == error_message

    def test_specific_exception_catching(self, mock_bot):
        """Test catching specific exception types."""
        with pytest.raises(APIBadRequest) as exc_info:
            raise APIBadRequest(mock_bot, "Specific bad request")
        
        assert isinstance(exc_info.value, APIBadRequest)
        assert isinstance(exc_info.value, APIError)

    def test_exception_args_property(self, mock_bot):
        """Test that exception args are properly set."""
        error_message = "Test args property"
        error = APIError(mock_bot, error_message)
        
        assert error.args == (error_message,)
        assert error.args[0] == error_message

    def test_multiple_exceptions_same_bot(self, mock_bot):
        """Test multiple exceptions with the same bot instance."""
        # Ensure log.error is a regular MagicMock, not AsyncMock
        mock_bot.log.error = MagicMock()
        
        error1 = APIError(mock_bot, "First error")
        error2 = APIBadRequest(mock_bot, "Second error")
        error3 = APIForbidden(mock_bot, "Third error")
        
        assert error1.bot == error2.bot == error3.bot == mock_bot
        assert mock_bot.log.error.call_count == 3

    def test_exception_with_long_message(self, mock_bot):
        """Test exception with very long error message."""
        long_message = "This is a very long error message " * 50
        
        error = APIError(mock_bot, long_message)
        
        assert str(error) == long_message
        assert error.message == long_message
        mock_bot.log.error.assert_called_once_with(f"GW2 API Error: {long_message}")

    def test_exception_message_formatting(self, mock_bot):
        """Test that exception messages are properly formatted in logs."""
        error_message = "API call failed with status 500"
        
        _ = APIInactiveError(mock_bot, error_message)
        
        expected_log_message = f"GW2 API Error: {error_message}"
        mock_bot.log.error.assert_called_once_with(expected_log_message)