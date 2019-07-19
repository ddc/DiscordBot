All Files with extension .sql inside this directory will run after bot has finishing booting
BEGIN TRANSACTION and COMMIT; already included
USE ONLY "UPDATE", "INSERT"

example:
file "script.sql" will have UPDATE script inside: 


UPDATE server_configs SET msg_on_join = 'N' WHERE discord_server_id = '341812870360858624';
