from discord.ext import commands


class APIError(Exception):
    """Base exception for GW2 API errors."""

    def __init__(self, bot: commands.Bot, msg: str):
        super().__init__(msg)
        self.bot = bot
        self.message = msg
        # Log error when exception is created
        if hasattr(bot, 'log') and bot.log:
            bot.log.error(f"GW2 API Error: {msg}")


class APIBadRequest(APIError):
    """Raised when API returns 400 Bad Request."""

    pass


class APIConnectionError(APIError):
    """Raised when there are connection issues with the API."""

    pass


class APIInactiveError(APIError):
    """Raised when the API is inactive or down."""

    pass


class APIForbidden(APIError):
    """Raised when API returns 403 Forbidden."""

    pass


class APINotFound(APIError):
    """Raised when API returns 404 Not Found."""

    pass


class APIInvalidKey(APIError):
    """Raised when the API key is invalid."""

    pass


class APIKeyError(APIError):
    """Raised when there are general API key errors."""

    pass
