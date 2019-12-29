# A Multifunction Bot for Discord

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg?style=plastic)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=38E66BHC4623Y)
[<img src="https://img.shields.io/github/license/ddc/DiscordBot.svg?style=plastic">](https://github.com/ddc/DiscordBot/blob/master/LICENSE) 
[![Python](https://img.shields.io/badge/python-3.7-blue.svg?style=plastic)](https://www.python.org/downloads/release)
[![GitHub release](https://img.shields.io/github/release/ddc/DiscordBot.svg?style=plastic)](https://github.com/ddc/DiscordBot/releases/latest)

Choice of PostgreSQL or SQLite3 as database.

### [Install guide - Wiki](https://ddc.github.io/DiscordBot)
+ Install [Python3.7](https://www.python.org/downloads/release)
+ Install [Git](https://git-scm.com/download/win)
+ Python modules can be installed using the script "install_reqs", running as root, this will also install Discord API or:
    + pip install -r requirements/requirements.txt

## Requirements
+ [Python3.7](https://www.python.org/downloads/release)
+ [Discord Bot Api](https://discordapp.com/developers/applications/me)
+ [Git](https://git-scm.com/download/win)
+ Python Modules:
    + [discord.py](https://pypi.org/project/discord)
    + [requests](https://pypi.python.org/pypi/requests)
    + [asyncpg](https://pypi.python.org/pypi/asyncpg/)
    + [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
    + [imgurpython](https://pypi.python.org/pypi/imgurpython)
    + [gitPython](https://pypi.python.org/pypi/gitPython)  
    
## Games Included
+ [Guild Wars 2](https://www.guildwars2.com)

## Admin Commands
| Command                                       | Description                                |
|:----------------------------------------------|:-------------------------------------------|
| invites										| List active invites link for the server	 |
| banlist										| List all members that have been banned	 |
| unban <_member#1234_>	  						| UnBan member from the channel				 |
| ban <_member#1234_> <_reason_>				| Ban member from the channel				 |
| kick <_member#1234_> <_reason_>				| Kick member from the channel				 |
| blacklist [add,remove] <_member#1234_>       	| Add or remove users from the blacklist	 |
| mute [add,remove] <_member#1234_> <_reason_>	| Mute or unmute an user					 |
| customcom [add,remove] <_command_>			| Add or remove Custom commands 			 |

## Config Commands
| Command                                       | Description                                |
|:----------------------------------------------|:-------------------------------------------|
| config list									| List all bot configurations				 |
| config bladmin         [on , off]				| Able to blacklist server's admins			 |
| config muteadmins		 [on , off]				| Able to mute server's admins			 	 |
| config servermessage   [on , off]				| Show message when a server gets updated	 |
| config membermessage   [on , off]				| Message when someone changes the profile 	 |
| config mentionpool     [on , off]				| Mention everyone when using pool command   |
| config anonymouspool   [on , off]				| Hide the author's name from the pool cmd   |
| config joinmessage     [on , off]				| Show message when a user joins the server	 |
| config leavemessage    [on , off]				| Show message when a user leaves the server |
| config blockinvisible  [on , off]				| Block messages from invisible members		 |
| config botreactions    [on , off]				| Bot will react to member words			 |
| config defaultchannel <_channel name_>		| Default text channel for bot messages		 |
| config pfilter [on , off]	<_channel name_>	| Profanity Filter (block swear/bad words)	 |

## GW2 Commands
| Command                                       | Description                                |
|:----------------------------------------------|:-------------------------------------------|
| gw2 account                        			| General information about your GW2 account |
| gw2 worlds	 								| List all worlds							 |
| gw2 wvwinfo	 								| Info about a world						 |
| gw2 lastsession	 							| Info about the gw2 player last game session|
| gw2 kdr <_worldname_>	 						| Info about a wvw kill/death ratings        |
| gw2 wiki <_name to search_>					| Search the Guild wars 2 wiki				 |
| gw2 info <_info to search_>					| Information about a given name/skill/rune	 |
| gw2 daily [pve, pvp, wvw, fractals]			| Show today's Dailies						 |
| gw2 key [add , remove , info] <_api key_>		| Add/Remove/Info - GW2 APIkey managing		 |
| gw2 [match, wvwinfo] <_world name_> 			| Info about a wvw match					 |
| gw2 config list								| List all gw2 configurations in the server  |
| gw2 config roletimer <_time secs_>			| Timer to check for api roles in seconds	 |
| gw2 config lastsession [on , off]				| Bot should record users last sessions	 	 |
| gw2 config apirole [on , off] <_server name_>	| Bot should add role that matches gw2 server|

## Misc Commands
| Command                                       | Description                                |
|:----------------------------------------------|:-------------------------------------------|
| about											| Display bot info							 |
| echo											| Show your msg again						 |
| ping											| Test latency by receiving a ping message	 |
| roll 											| Rolls random number					  	 |
| tts <_message_>				                | Send TTS as .mp3 to channel	             |
| serverinfo									| Shows server's informations				 |
| userinfo <_member#1234_>						| Shows discord user informations			 |
| lmgtfy <_link_>								| Creates a lmgtfy link						 |
| simplepool <_question_> <_emoji_>             | Create a simple yes,no pool                |
| pool <_Question;Choice1;Choice2_>				| Creates a numeric list of choices pool	 |

## Bot Owner Commands
| Command                                       | Description                                |
|:----------------------------------------------|:-------------------------------------------|
| owner executesql                              | Execute all sql files inside data/sql dir  |
| owner reload                                  | Command to reload all extensions           |
| owner servers									| Display all servers in database			 |
| owner prefix <_new prefix_>					| Change bot prefix for commands			 |
| owner reloadcog <_src.cogs.bot.name_>			| Command to reload a module				 |
| owner botdescription <_new description_>		| Change bot description					 |
| owner botgame <_new game_>					| Change game that bot is playing			 |

## Acknowledgements
+ [Guild Wars 2 API](https://wiki.guildwars2.com/wiki/API:2)
+ [PostgreSQL](https://www.postgresql.org)
+ [Discord Bot Api](https://discordapp.com/developers/applications/me)
+ [SQLite3](https://sqlite.org)
+ [Git](https://git-scm.com/download)

## License
Released under the [GNU GPL v3](LICENSE).

## Buy me a cup of coffee
This bot is open source and always will be, even if I don't get donations. That said, I know there are people out there that may still want to donate just to show their appreciation so this is for you guys. Thanks in advance!

[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=38E66BHC4623Y)
