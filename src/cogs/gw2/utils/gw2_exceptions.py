#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-


class APIError(Exception):
    def __init__(self, bot, msg):
        self.bot = bot
        self.bot.log.error(f"{msg}")


class APIBadRequest(APIError):
    pass


class APIConnectionError(APIError):
    pass


class APIInactiveError(APIError):
    pass


class APIForbidden(APIError):
    pass


class APINotFound(APIError):
    pass


class APIInvalidKey(APIError):
    pass


class APIKeyError(APIError):
    pass
