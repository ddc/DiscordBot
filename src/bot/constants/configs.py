# -*- coding: utf-8 -*-
import os
import ast


class Configs:
    def __init__(self):
        self.environ = dict(os.environ)

    @property
    def config_env(self):
        return self.environ.get("CONFIG_ENV", "dev")

    @property
    def debug(self):
        level = self.environ.get("DEBUG", "False")
        return ast.literal_eval(level)

    @property
    def default_prefix(self):
        return self.environ.get("DEFAULT_PREFIX", '!')

    @property
    def postgres_user(self):
        return self.environ.get("POSTGRES_USER", "postgres")

    @property
    def postgres_password(self):
        return self.environ.get("POSTGRES_PASSWORD", "postgres")

    @property
    def postgres_host(self):
        return self.environ.get("POSTGRES_HOST", "bot_database")

    @property
    def postgres_port(self):
        return int(self.environ.get("POSTGRES_PORT", 5432))

    @property
    def postgres_db(self):
        return self.environ.get("POSTGRES_DB", "discordbot")

    @property
    def bot_token(self):
        return self.environ.get("BOT_TOKEN", None)
