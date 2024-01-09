# -*- coding: utf-8 -*-
from src.gw2.constants import gw2_variables, gw2_messages
from src.gw2.tools.gw2_exceptions import (
    APIBadRequest, APIConnectionError, APIError, APIForbidden,
    APIInactiveError, APIInvalidKey, APIKeyError, APINotFound
)


class Gw2Api:
    def __init__(self, bot):
        self.bot = bot

    async def check_api_key(self, api_key):
        """checks if apy key is valid"""

        try:
            api_req_key_info = await self.call_api("tokeninfo", api_key)
        except (APIBadRequest, APIConnectionError, APIError, APIForbidden,
                APIInactiveError, APIInvalidKey, APIKeyError, APINotFound) as e:
            return e

        if "permissions" in api_req_key_info:
            api_req_key_info["permissions"] = sorted(api_req_key_info["permissions"])
        return api_req_key_info

    async def call_api(self, uri: str, key=None):
        """api languages can be ('en','es','de','fr','ko','zh')"""

        endpoint = f"{gw2_variables.API_URI}/{uri}"

        headers = {
            "User-Agent": self.bot.description,
            "Accept": "application/json",
            "lang": "en"
        }

        if key:
            headers.update({"Authorization": f"Bearer {key}"})

        async with self.bot.aiosession.get(endpoint, headers=headers) as response:
            if response.status != 200 and response.status != 206:
                try:
                    err = await response.json()
                    err_msg = err["text"]
                except:
                    err_msg = ""

                init_msg = f"{response.status})({endpoint.split('?')[0]}"

                if response.status == 400:
                    if err_msg == "invalid key":
                        raise APIInvalidKey(self.bot, f"({response.status}) {gw2_messages.INVALID_API_KEY}")
                    raise APIBadRequest(self.bot, f"({init_msg}) {gw2_messages.API_DOWN}")
                elif response.status == 404:
                    raise APINotFound(self.bot, f"({response.status})({endpoint.split('?')[0]}) {gw2_messages.API_NOT_FOUND}")
                elif response.status == 403:
                    if err_msg == "invalid key":
                        raise APIInvalidKey(self.bot, f"({response.status}) {gw2_messages.INVALID_API_KEY}")
                    raise APIForbidden(self.bot, f"({init_msg}) {gw2_messages.API_ACCESS_DENIED}")
                elif response.status == 429:
                    raise APIConnectionError(self.bot, f"({init_msg}) {gw2_messages.API_REQUEST_REACHED}")
                elif response.status == 502 or response.status == 504:
                    raise APIInactiveError(self.bot, f"({init_msg}) {gw2_messages.API_DOWN}")
                elif response.status == 503:
                    raise APIInactiveError(self.bot, f"({init_msg}) {err_msg}")
                else:
                    if len(err_msg) == 0:
                        err_msg = str(response.reason)
                    raise APIConnectionError(self.bot, f"{gw2_messages.API_ERROR} ({init_msg})({err_msg})")

            return await response.json()
