#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.databases.databases import Databases


class Triggers:
    def __init__(self, bot):
        self.bot = bot
        self.database_in_use = self.bot.settings["DatabaseInUse"]

    ################################################################################
    async def create_triggers(self):
        if self.database_in_use.lower() == "sqlite":
            sql = """CREATE TRIGGER IF NOT EXISTS before_insert_bot_configs
                    BEFORE INSERT ON bot_configs
                    BEGIN
                        SELECT CASE
                            WHEN (SELECT count(*) FROM bot_configs)IS 1 THEN
                            RAISE(ABORT, 'CANNOT INSERT INTO BOT_CONFIGS TABLE ANYMORE.')
                        END;
                    END;
                CREATE TRIGGER IF NOT EXISTS before_update_author_id
                    BEFORE UPDATE OF author_id ON bot_configs
                    WHEN new.author_id <> '195615080665055232'
                    BEGIN
                        SELECT RAISE(ABORT, 'CANNOT CHANGE BOT AUTHOR ID.');
                    END;
                CREATE TRIGGER IF NOT EXISTS before_update_bot_url
                    BEFORE UPDATE OF url ON bot_configs
                    BEGIN
                        SELECT RAISE(ABORT, 'CANNOT CHANGE BOT URL.');
                    END;"""
        elif self.database_in_use.lower() == "postgres":
            sql = """DROP TRIGGER IF EXISTS before_insert_bot_configs ON bot_configs;
                DROP TRIGGER IF EXISTS before_update_author_id ON bot_configs;
                DROP TRIGGER IF EXISTS before_update_bot_url ON bot_configs;
                ------
                CREATE or REPLACE FUNCTION before_insert_bot_configs_func()
                    returns trigger language plpgsql as $$
                    begin
                        RAISE unique_violation USING MESSAGE = 'CANNOT INSERT INTO BOT_CONFIGS TABLE ANYMORE';
                        return null;
                    end $$;        
                
                CREATE TRIGGER before_insert_bot_configs
                    BEFORE INSERT ON bot_configs 
                    for each row execute procedure before_insert_bot_configs_func();
                ------
                CREATE or REPLACE FUNCTION before_update_author_id_func()
                        returns trigger language plpgsql as $$
                        begin
                                RAISE unique_violation USING MESSAGE = 'CANNOT CHANGE BOT AUTHOR ID.';
                                return null;
                        end $$; 
                
                CREATE TRIGGER before_update_author_id
                    BEFORE UPDATE ON bot_configs
                    FOR EACH ROW
                    WHEN (OLD.author_id IS DISTINCT FROM NEW.author_id)
                    EXECUTE PROCEDURE before_update_author_id_func();            
                ------            
                 CREATE or REPLACE FUNCTION before_update_bot_url_func()
                        returns trigger language plpgsql as $$
                        begin
                                RAISE unique_violation USING MESSAGE = 'CANNOT CHANGE BOT URL.';
                                return null;
                        end $$; 
                
                CREATE TRIGGER before_update_bot_url
                    BEFORE UPDATE ON bot_configs
                    FOR EACH ROW
                    WHEN (OLD.url IS DISTINCT FROM NEW.url)
                    EXECUTE PROCEDURE before_update_bot_url_func();"""

        databases = Databases(self.bot)
        await databases.execute(sql)
