#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.databases.databases import Databases


class InitialTablesSql:
    def __init__(self, bot):
        self.bot = bot
        self.database_in_use = self.bot.settings["DatabaseInUse"]

    ################################################################################
    async def create_initial_sqlite_bot_tables(self):
        databases = Databases(self.bot)
        primary_key_type = await databases.set_primary_key_type()

        sql = f"""
            CREATE TABLE IF NOT EXISTS users (
                discord_user_id   BIGINT  NOT NULL PRIMARY KEY UNIQUE,
                user_name         TEXT    NOT NULL,
                avatar_url        TEXT
               );
               
            CREATE TABLE IF NOT EXISTS servers (
                    discord_server_id    BIGINT  NOT NULL PRIMARY KEY UNIQUE,
                    server_owner_id      BIGINT  NOT NULL,
                    server_name          TEXT    NOT NULL,
                    region               TEXT    NOT NULL,
                    icon_url             TEXT
                   );
            
            CREATE TABLE IF NOT EXISTS profanity_filters (
                    channel_id          BIGINT    NOT NULL PRIMARY KEY UNIQUE,
                    discord_server_id   BIGINT    NOT NULL,
                    channel_name        TEXT      NOT NULL,
                    FOREIGN KEY(discord_server_id) REFERENCES servers(discord_server_id) ON DELETE CASCADE
               );
    
            CREATE TABLE IF NOT EXISTS blacklists (
                id                 {primary_key_type},
                discord_server_id  BIGINT   NOT NULL,
                discord_user_id    BIGINT   NOT NULL,
                discord_author_id  BIGINT,
                reason             TEXT,
                date               TEXT,
                FOREIGN KEY(discord_server_id) REFERENCES servers(discord_server_id) ON DELETE CASCADE,
                FOREIGN KEY(discord_user_id) REFERENCES users(discord_user_id) ON DELETE CASCADE,
                FOREIGN KEY(discord_author_id) REFERENCES users(discord_user_id) ON DELETE CASCADE
               );

            CREATE TABLE IF NOT EXISTS mutes (
                id                 {primary_key_type},
                discord_server_id  BIGINT   NOT NULL,
                discord_user_id    BIGINT   NOT NULL,
                discord_author_id  BIGINT,
                reason             TEXT,
                date               TEXT,
                FOREIGN KEY(discord_server_id) REFERENCES servers(discord_server_id) ON DELETE CASCADE,
                FOREIGN KEY(discord_user_id) REFERENCES users(discord_user_id) ON DELETE CASCADE,
                FOREIGN KEY(discord_author_id) REFERENCES users(discord_user_id) ON DELETE CASCADE
               );
                           
            CREATE TABLE IF NOT EXISTS server_configs (
                id                           {primary_key_type},
                discord_server_id            BIGINT   NOT NULL UNIQUE,
                msg_on_join                  CHAR(1)  NOT NULL DEFAULT 'Y',
                msg_on_leave                 CHAR(1)  NOT NULL DEFAULT 'Y',
                msg_on_server_update         CHAR(1)  NOT NULL DEFAULT 'Y',
                msg_on_member_update         CHAR(1)  NOT NULL DEFAULT 'Y',
                blacklist_admins             CHAR(1)  NOT NULL DEFAULT 'N',
                mute_admins                  CHAR(1)  NOT NULL DEFAULT 'N',
                block_invis_members          CHAR(1)  NOT NULL DEFAULT 'N',
                mention_everyone_pool_cmd    CHAR(1)  NOT NULL DEFAULT 'N',
                anonymous_pool               CHAR(1)  NOT NULL DEFAULT 'N',
                bot_word_reactions           CHAR(1)  NOT NULL DEFAULT 'Y',
                default_text_channel         TEXT,
                FOREIGN KEY(discord_server_id) REFERENCES servers(discord_server_id) ON DELETE CASCADE,
                CONSTRAINT check_msg_on_join_y_n CHECK (msg_on_join IN ('Y','N')),
                CONSTRAINT check_msg_on_leave_y_n CHECK (msg_on_leave IN ('Y','N')),
                CONSTRAINT check_msg_on_server_update_y_n CHECK (msg_on_server_update IN ('Y','N')),
                CONSTRAINT check_msg_on_member_update_y_n CHECK (msg_on_member_update IN ('Y','N')),
                CONSTRAINT check_blacklist_admins_y_n CHECK (blacklist_admins IN ('Y','N')),
                CONSTRAINT check_mute_admins_y_n CHECK (mute_admins IN ('Y','N')),
                CONSTRAINT check_block_invis_members_y_n CHECK (block_invis_members IN ('Y','N')),
                CONSTRAINT check_mention_everyone_pool_cmd_y_n CHECK (mention_everyone_pool_cmd IN ('Y','N')),
                CONSTRAINT check_anonymous_pool_y_n CHECK (anonymous_pool IN ('Y','N')),
                CONSTRAINT check_bot_word_reactions_y_n CHECK (bot_word_reactions IN ('Y','N'))
               );
    
            CREATE TABLE IF NOT EXISTS commands (
                id                 {primary_key_type},
                discord_server_id  BIGINT    NOT NULL,
                discord_author_id  BIGINT    NOT NULL,
                command_name       TEXT      NOT NULL,
                description        TEXT      NOT NULL,
                date               TEXT      NOT NULL,
                FOREIGN KEY(discord_server_id) REFERENCES servers(discord_server_id) ON DELETE CASCADE,
                FOREIGN KEY(discord_author_id) REFERENCES users(discord_user_id) ON DELETE CASCADE
               );
    
            CREATE TABLE IF NOT EXISTS bot_configs (
                id                   {primary_key_type},
                prefix               CHAR(1)  NOT NULL DEFAULT '?',
                author_id            BIGINT   NOT NULL,
                url                  TEXT     NOT NULL,
                description          TEXT     NOT NULL,
                FOREIGN KEY(author_id) REFERENCES users(discord_user_id) ON DELETE CASCADE,
                CONSTRAINT check_prefix CHECK (prefix IN ('!','$','%','^','&','?','>','<','.',';'))
               );
                     
            CREATE TABLE IF NOT EXISTS dice_rolls (
                id                   {primary_key_type},
                discord_server_id    BIGINT    NOT NULL,
                discord_user_id      BIGINT    NOT NULL,
                roll                 BIGINT    NOT NULL,
                dice_size            BIGINT    NOT NULL,
                FOREIGN KEY(discord_server_id) REFERENCES servers(discord_server_id) ON DELETE CASCADE,
                FOREIGN KEY(discord_user_id) REFERENCES users(discord_user_id) ON DELETE CASCADE
               );
               
            """
        await databases.execute(sql)
