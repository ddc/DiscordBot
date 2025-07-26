# A Bot for Discord

[![Donate](https://img.shields.io/badge/Donate-PayPal-brightgreen.svg?style=plastic)](https://www.paypal.com/ncp/payment/6G9Z78QHUD4RJ)
[![license](https://img.shields.io/github/license/ddc/DiscordBot.svg?style=plastic)](https://github.com/ddc/DiscordBot/blob/master/LICENSE) 
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-yellow.svg?style=plastic)](https://www.postgresql.org)
[![python](https://img.shields.io/badge/python-3.13-lightgrey.svg?style=plastic)](https://www.python.org/downloads/release)
[![codecov](https://codecov.io/gh/ddc/DiscordBot/graph/badge.svg?token=K2SSZ142O1)](https://codecov.io/gh/ddc/DiscordBot)
[![Release](https://img.shields.io/github/release/ddc/DiscordBot.svg?style=plastic)](https://github.com/ddc/DiscordBot/releases/latest)
[![Build Status](https://img.shields.io/endpoint.svg?url=https://actions-badge.atrox.dev/ddc/DiscordBot/badge?ref=master&style=plastic&label=build&logo=none)](https://actions-badge.atrox.dev/ddc/DiscordBot/goto?ref=master)


<!--
### [Invitation Link](https://discordapp.com/api/oauth2/authorize?client_id=427992048088383518&permissions=8&scope=bot)
+ Use the link bellow to invite this bot into your server, or install your own using the install guide
    + [Invitation Link](https://discordapp.com/api/oauth2/authorize?client_id=427992048088383518&permissions=8&scope=bot)
-->

# [Install Guide - Wiki](https://ddc.github.io/DiscordBot)
+ Using Docker
    + git clone https://github.com/ddc/DiscordBot.git
      + BOT_TOKEN variable needs to be inside the .env file
    + sudo systemctl enable docker
    + docker-compose up --build -d

# Games Included
+ [Guild Wars 2](https://www.guildwars2.com)


# OpenAI Command
| Commands       | Description                                     |
|:---------------|:------------------------------------------------|
| ai <_message_> | Asks OpenAI, message will be on discord embeded |


# Admin/Mod Commands
| Commands                               | Description                         |
|:---------------------------------------|:------------------------------------|
| admin cc [add,edit,remove] <_command_> | Add, edit or remove custom commands |
| admin botgame <_new game_>             | Change game that bot is playing     |

# Config Commands
| Commands                                         | Description                                   |
|:-------------------------------------------------|:----------------------------------------------|
| admin config list                                | List all bot configurations                   |
| admin config servermessage   [on , off]          | Show message when a server gets updated       |
| admin config membermessage   [on , off]          | Show message when someone updates the profile |
| admin config joinmessage     [on , off]          | Show message when a user joins the server	    |
| admin config leavemessage    [on , off]          | Show message when a user leaves the server    |
| admin config blockinvisible  [on , off]          | Block messages from invisible members         |
| admin config botreactions    [on , off]          | Bot will react to member words                |
| admin config pfilter [on , off]	<_channel name_> | Profanity Filter (blocks swear words)         |

# Misc Commands
| Commands                 | Description                              |
|:-------------------------|:-----------------------------------------|
| about                    | Displays bot info                        |
| echo                     | Shows your msg again                     |
| ping                     | Test latency by receiving a ping message |
| roll                     | Rolls random number                      |
| pepe                     | Posts a random Pepe from imgur url       |
| tts <_message_>          | Send TTS as .mp3 to channel              |
| serverinfo               | Shows server's informations              |
| userinfo <_member#1234_> | Shows discord user informations          |
| lmgtfy <_link_>          | Creates a lmgtfy link	                   |
| invites                  | List active invites link for the server  |

# Bot Owner Commands
| Commands                                  | Description                     |
|:------------------------------------------|:--------------------------------|
| owner servers                             | Display all servers in database |
| owner prefix <_new prefix_>               | Change bot prefix for commands  |
| owner botdescription <_new description_>	 | Change bot description          |

# GW2 Commands
| Commands                                  | Description                                |
|:------------------------------------------|:-------------------------------------------|
| gw2 config list                           | List all gw2 configurations in the server  |
| gw2 config session [on , off]             | Bot should record users last sessions      |
| gw2 wvw [match, info, kdr] <_world name_> | Info about a wvw match                     |
| gw2 key [add , remove , info] <_api key_> | Add/Remove/Info - GW2 APIkey managing      |
| gw2 account                               | General information about your GW2 account |
| gw2 worlds [na, eu]                       | List all worlds by timezone                |
| gw2 wiki <_name to search_>               | Search the Guild wars 2 wiki               |
| gw2 info <_info to search_>               | Information about a given name/skill/rune  |



# Acknowledgements
+ [OpenAI API](https://openai.com/api)
+ [Guild Wars 2 API](https://wiki.guildwars2.com/wiki/API:2)
+ [Discord Bot Api](https://discordapp.com/developers/applications/me)
+ [PostgreSQL](https://www.postgresql.org)
+ [Git](https://git-scm.com/download)



# License
Released under the [MIT](LICENSE).



# Buy me a cup of coffee
+ [GitHub Sponsor](https://github.com/sponsors/ddc)
+ [ko-fi](https://ko-fi.com/ddcsta)
+ [Paypal](https://www.paypal.com/ncp/payment/6G9Z78QHUD4RJ)
