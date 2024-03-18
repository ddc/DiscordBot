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
    def db_username(self):
        return self.environ.get("DB_USERNAME", "postgres")

    @property
    def db_password(self):
        return self.environ.get("DB_PASSWORD", "postgres")

    @property
    def db_host(self):
        return self.environ.get("DB_HOST", "bot_database")

    @property
    def db_port(self):
        return int(self.environ.get("DB_PORT", 5432))

    @property
    def db_database(self):
        return self.environ.get("DB_DATABASE", "discordbot")

    @property
    def bot_token(self):
        return self.environ.get("BOT_TOKEN", None)
