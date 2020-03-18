#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.databases.databases import Databases


class Gw2LastSessionSql:
    def __init__(self, bot):
        self.bot = bot

    ################################################################################
    async def get_user_last_session(self, discord_user_id: int):
        sql = f"SELECT * FROM gw2_sessions WHERE discord_user_id = {discord_user_id};"
        databases = Databases(self.bot)
        return await databases.select(sql)

    ################################################################################
    async def insert_last_session_start(self, user_stats: object):
        sql = f"""DELETE FROM gw2_sessions WHERE discord_user_id = {user_stats.discord_user_id};
        DELETE FROM gw2_chars_start WHERE discord_user_id = {user_stats.discord_user_id};
        DELETE FROM gw2_chars_end WHERE discord_user_id = {user_stats.discord_user_id};
        INSERT INTO gw2_sessions 
            (   discord_user_id
                ,acc_name
                ,start_date
                ,start_wvw_rank
                ,start_gold
                ,start_karma
                ,start_laurels
                ,start_badges_honor
                ,start_guild_commendations
                ,start_wvw_tickets
                ,start_proof_heroics
                ,start_test_heroics
                ,start_players
                ,start_yaks_scorted
                ,start_yaks
                ,start_camps
                ,start_castles
                ,start_towers
                ,start_keeps
            )VALUES(
                {user_stats.discord_user_id},
                '{user_stats.acc_name}',
                '{user_stats.date}',
                {user_stats.wvw_rank},
                {user_stats.gold},
                {user_stats.karma},
                {user_stats.laurels},
                {user_stats.badges_honor},
                {user_stats.guild_commendations},
                {user_stats.wvw_tickets},
                {user_stats.proof_heroics},
                {user_stats.test_heroics},
                {user_stats.players},
                {user_stats.yaks_scorted},
                {user_stats.yaks},
                {user_stats.camps},
                {user_stats.castles},
                {user_stats.towers},
                {user_stats.keeps});"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
    async def update_last_session_end(self, user_stats: object):
        sql = f"""UPDATE gw2_sessions SET
                    end_date =                  '{user_stats.date}',
                    end_wvw_rank =               {user_stats.wvw_rank},
                    end_gold =                   {user_stats.gold},
                    end_karma =                  {user_stats.karma},
                    end_laurels =                {user_stats.laurels},
                    end_badges_honor =           {user_stats.badges_honor},
                    end_guild_commendations =    {user_stats.guild_commendations},
                    end_wvw_tickets =            {user_stats.wvw_tickets},
                    end_proof_heroics =          {user_stats.proof_heroics},
                    end_test_heroics =           {user_stats.test_heroics},
                    end_players =                {user_stats.players},
                    end_yaks_scorted =           {user_stats.yaks_scorted},
                    end_yaks =                   {user_stats.yaks},
                    end_camps =                  {user_stats.camps},
                    end_castles =                {user_stats.castles},
                    end_towers =                 {user_stats.towers},
                    end_keeps =                  {user_stats.keeps}
                    WHERE discord_user_id =      {user_stats.discord_user_id};"""
        databases = Databases(self.bot)
        await databases.execute(sql)

    ################################################################################
