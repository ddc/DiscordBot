import asyncio
from src.gw2.constants import gw2_messages, gw2_variables
from src.gw2.constants.gw2_settings import get_gw2_settings
from src.gw2.tools.gw2_exceptions import (
    APIBadRequest,
    APIConnectionError,
    APIError,
    APIForbidden,
    APIInactiveError,
    APIInvalidKey,
    APINotFound,
)

_gw2_settings = get_gw2_settings()
_RETRYABLE_STATUSES = (502, 503, 504)


class Gw2Client:
    def __init__(self, bot):
        self.bot = bot

    async def check_api_key(self, api_key):
        """checks if apy key is valid"""

        try:
            api_req_key_info = await self.call_api("tokeninfo", api_key)
        except APIError as e:
            return e

        if "permissions" in api_req_key_info:
            api_req_key_info["permissions"] = sorted(api_req_key_info["permissions"])
        return api_req_key_info

    async def call_api(self, uri: str, key=None):
        """api languages can be ('en','es','de','fr','ko','zh')"""

        endpoint = f"{gw2_variables.API_URI}/{uri}"
        headers = self._build_headers(key)
        max_attempts = _gw2_settings.api_retry_max_attempts
        retry_delay = _gw2_settings.api_retry_delay

        for attempt in range(1, max_attempts + 1):
            try:
                async with self.bot.aiosession.get(endpoint, headers=headers) as response:
                    if response.status in (200, 206):
                        return await response.json()

                    if response.status not in _RETRYABLE_STATUSES or attempt == max_attempts:
                        await self._handle_api_error(response, endpoint)
                        return None

                    self.bot.log.warning(
                        f"GW2 API returned {response.status} for {endpoint.split('?')[0]}, "
                        f"retrying ({attempt}/{max_attempts})..."
                    )
            except APIError:
                raise
            except Exception:
                if attempt == max_attempts:
                    raise
                self.bot.log.warning(
                    f"GW2 API connection error for {endpoint.split('?')[0]}, retrying ({attempt}/{max_attempts})..."
                )

            await asyncio.sleep(retry_delay)

        return None

    def _build_headers(self, key=None):
        """Build HTTP headers for API request."""
        headers = {"User-Agent": self.bot.description, "Accept": "application/json", "lang": "en"}

        if key:
            headers.update({"Authorization": f"Bearer {key}"})

        return headers

    async def _handle_api_error(self, response, endpoint):
        """Handle API error responses by raising appropriate exceptions."""
        try:
            err = await response.json()
            err_msg = err.get("text", "")
        except Exception:
            err_msg = ""

        init_msg = f"{response.status})({endpoint.split('?')[0]}"

        match response.status:
            case 400:
                self._handle_400_error(response.status, err_msg, init_msg)
            case 403:
                self._handle_403_error(response.status, err_msg, init_msg)
            case 404:
                self._handle_404_error(response.status, endpoint)
            case 429:
                self._handle_429_error(init_msg)
            case 502 | 504:
                self._handle_502_504_error(init_msg)
            case 503:
                self._handle_503_error(init_msg, err_msg)
            case _:
                self._handle_other_error(response, init_msg, err_msg)

    def _handle_400_error(self, status, err_msg, init_msg):
        """Handle 400 Bad Request errors."""
        if err_msg == "invalid key":
            raise APIInvalidKey(self.bot, f"({status}) {gw2_messages.INVALID_API_KEY}")
        raise APIBadRequest(self.bot, f"({init_msg}) {gw2_messages.API_DOWN}")

    def _handle_403_error(self, status, err_msg, init_msg):
        """Handle 403 Forbidden errors."""
        if err_msg == "invalid key":
            raise APIInvalidKey(self.bot, f"({status}) {gw2_messages.INVALID_API_KEY}")
        raise APIForbidden(self.bot, f"({init_msg}) {gw2_messages.API_ACCESS_DENIED}")

    def _handle_404_error(self, status, endpoint):
        """Handle 404 Not Found errors."""
        raise APINotFound(self.bot, f"({status})({endpoint.split('?')[0]}) {gw2_messages.API_NOT_FOUND}")

    def _handle_429_error(self, init_msg):
        """Handle 429 Too Many Requests errors."""
        raise APIConnectionError(self.bot, f"({init_msg}) {gw2_messages.API_REQUEST_REACHED}")

    def _handle_502_504_error(self, init_msg):
        """Handle 502 Bad Gateway and 504 Gateway Timeout errors."""
        raise APIInactiveError(self.bot, f"({init_msg}) {gw2_messages.API_DOWN}")

    def _handle_503_error(self, init_msg, err_msg):
        """Handle 503 Service Unavailable errors."""
        raise APIInactiveError(self.bot, f"({init_msg}) {err_msg}")

    def _handle_other_error(self, response, init_msg, err_msg):
        """Handle other HTTP error statuses."""
        if not err_msg:
            err_msg = str(response.reason)
        raise APIConnectionError(self.bot, f"{gw2_messages.API_ERROR} ({init_msg})({err_msg})")
