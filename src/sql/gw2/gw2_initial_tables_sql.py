#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.databases.databases import Databases


class Gw2InitialTablesSql:
    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def create_gw2_sqlite_tables(self):
        databases = Databases(self.bot)
        primary_key_type = await databases.set_primary_key_type()

        sql = f"""CREATE TABLE IF NOT EXISTS gw2_keys (
                id                  {primary_key_type},
                discord_server_id   BIGINT  NOT NULL,
                discord_user_id     BIGINT  NOT NULL,
                gw2_acc_name        TEXT    NOT NULL,
                server_name         TEXT    NOT NULL,
                key_name            TEXT,
                permissions         TEXT    NOT NULL,
                key                 TEXT    NOT NULL,
                FOREIGN KEY(discord_user_id) REFERENCES users(discord_user_id) ON DELETE CASCADE,
                FOREIGN KEY(discord_server_id) REFERENCES servers(discord_server_id) ON DELETE CASCADE
                );

            CREATE TABLE IF NOT EXISTS gw2_sessions (
                discord_user_id                 BIGINT  NOT NULL PRIMARY KEY UNIQUE,
                acc_name                        TEXT    NOT NULL,
                start_date                      TEXT    NOT NULL,
                end_date                        TEXT,
                start_wvw_rank                  BIGINT  NOT NULL,
                end_wvw_rank                    BIGINT,
                start_gold                      BIGINT  NOT NULL,
                end_gold                        BIGINT,
                start_karma                     BIGINT  NOT NULL,
                end_karma                       BIGINT,
                start_laurels                   BIGINT  NOT NULL,
                end_laurels                     BIGINT,
                start_badges_honor              BIGINT  NOT NULL,
                end_badges_honor                BIGINT,
                start_guild_commendations       BIGINT  NOT NULL,
                end_guild_commendations         BIGINT,
                start_wvw_tickets               BIGINT  NOT NULL,
                end_wvw_tickets                 BIGINT,            
                start_proof_heroics             BIGINT  NOT NULL,
                end_proof_heroics               BIGINT,
                start_test_heroics              BIGINT  NOT NULL,
                end_test_heroics                BIGINT,            
                start_players                   BIGINT  NOT NULL,
                end_players                     BIGINT,
                start_yaks_scorted              BIGINT  NOT NULL,
                end_yaks_scorted                BIGINT,
                start_yaks                      BIGINT  NOT NULL,
                end_yaks                        BIGINT,
                start_camps                     BIGINT  NOT NULL,
                end_camps                       BIGINT,
                start_castles                   BIGINT  NOT NULL,
                end_castles                     BIGINT,
                start_towers                    BIGINT  NOT NULL,
                end_towers                      BIGINT,
                start_keeps                     BIGINT  NOT NULL,
                end_keeps                       BIGINT,
                FOREIGN KEY(discord_user_id) REFERENCES users(discord_user_id) ON DELETE CASCADE
                );

            CREATE TABLE IF NOT EXISTS gw2_chars_start (
                id                  {primary_key_type},
                discord_user_id     BIGINT   NOT NULL,
                name                TEXT     NOT NULL UNIQUE,
                profession          TEXT     NOT NULL,
                deaths              BIGINT   NOT NULL,
                FOREIGN KEY(discord_user_id) REFERENCES users(discord_user_id) ON DELETE CASCADE
                );

            CREATE TABLE IF NOT EXISTS gw2_chars_end (
                id                  {primary_key_type},
                discord_user_id     BIGINT   NOT NULL,
                name                TEXT     NOT NULL UNIQUE,
                profession          TEXT     NOT NULL,
                deaths              BIGINT   NOT NULL,
                FOREIGN KEY(discord_user_id) REFERENCES users(discord_user_id) ON DELETE CASCADE
                );
                
            CREATE TABLE IF NOT EXISTS gw2_configs (
                discord_server_id       BIGINT   NOT NULL PRIMARY KEY UNIQUE,
                last_session            CHAR(1)  NOT NULL DEFAULT 'N',
                role_timer              BIGINT   NOT NULL,
                CONSTRAINT last_session_y_n CHECK (last_session IN ('Y', 'N')),
                FOREIGN KEY(discord_server_id) REFERENCES servers(discord_server_id) ON DELETE CASCADE
                );

            CREATE TABLE IF NOT EXISTS gw2_roles (
                id                      {primary_key_type},
                discord_server_id       BIGINT   NOT NULL,
                role_name               TEXT     NOT NULL,
                FOREIGN KEY(discord_server_id) REFERENCES servers(discord_server_id) ON DELETE CASCADE
                );
             
                """

        await databases.execute(sql)
