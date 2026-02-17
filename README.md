<h1 align="center">
  <img src="https://raw.githubusercontent.com/ddc/DiscordBot/refs/heads/master/assets/DiscordBot-icon.svg" alt="DiscordBot" width="150">
  <br>
  DiscordBot
</h1>

<p align="center">
    <a href="https://www.paypal.com/ncp/payment/6G9Z78QHUD4RJ"><img src="https://img.shields.io/badge/Donate-PayPal-brightgreen.svg?style=plastic" alt="Donate"/></a>
    <a href="https://github.com/sponsors/ddc"><img src="https://img.shields.io/static/v1?style=plastic&label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=ff69b4" alt="Sponsor"/></a>
    <br>
    <a href="https://www.python.org/downloads"><img src="https://img.shields.io/badge/python-3.14-blue.svg?style=plastic" alt="Python"/></a>
    <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json?style=plastic" alt="uv"/></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json?style=plastic" alt="Ruff"/></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=plastic" alt="License: MIT"/></a>
    <br>
    <a href="https://github.com/ddc/DiscordBot/issues"><img src="https://img.shields.io/github/issues/ddc/DiscordBot?style=plastic" alt="issues"/></a>
    <a href="https://codecov.io/gh/ddc/DiscordBot"><img src="https://codecov.io/gh/ddc/DiscordBot/graph/badge.svg?token=E942EZII4Q&style=plastic" alt="codecov"/></a>
    <a href="https://sonarcloud.io/dashboard?id=ddc_DiscordBot"><img src="https://sonarcloud.io/api/project_badges/measure?project=ddc_DiscordBot&metric=alert_status&style=plastic" alt="Quality Gate Status"/></a>
    <a href="https://github.com/ddc/DiscordBot/actions/workflows/workflow.yml"><img src="https://github.com/ddc/DiscordBot/actions/workflows/workflow.yml/badge.svg?style=plastic" alt="CI/CD Pipeline"/></a>
</p>

<p align="center">A simple Discord bot with OpenAI support and server administration tools.</p>


## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Commands](#commands)
  - [OpenAI](#openai-commands)
  - [Admin/Mod](#adminmod-commands)
  - [Config](#config-commands)
  - [Custom Commands](#custom-commands)
  - [Misc](#misc-commands)
  - [Dice Rolls](#dice-rolls-commands)
  - [Bot Owner](#bot-owner-commands)
  - [GW2](#gw2-commands)
  - [GW2 Config](#gw2-config-commands)
  - [GW2 Key](#gw2-key-commands)
  - [GW2 WvW](#gw2-wvw-commands)
- [Development and Testing](#development-and-testing)
- [Acknowledgements](#acknowledgements)
- [Support](#support)
- [License](#license)


# Features
- OpenAI integration for AI-powered responses
- Guild Wars 2 API integration (accounts, WvW, sessions, wiki)
- Server administration and moderation tools
- Custom commands, profanity filtering, and text-to-speech
- PostgreSQL database with Alembic migrations
- Docker deployment with automatic database migrations


# Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- A [Discord Bot Token](https://discord.com/developers/applications)
- _(Optional)_ An [OpenAI API Key](https://platform.openai.com/api-keys) for AI commands
- _(Optional)_ A [Guild Wars 2 API Key](https://account.arena.net/applications) for GW2 commands


# Installation

### 1. Clone the repository
```shell
git clone https://github.com/ddc/DiscordBot.git
cd DiscordBot
```

### 2. Configure environment variables
```shell
cp .env.example .env
```

Edit the `.env` file and set the required values:
```ini
# Required
BOT_TOKEN=your_discord_bot_token

# Optional
OPENAI_API_KEY=your_openai_api_key

# Database (defaults work with the included docker-compose)
POSTGRESQL_HOST=discordbot_database
POSTGRESQL_PORT=5432
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=postgres
POSTGRESQL_DATABASE=discordbot
```

See [Configuration](#configuration) for all available options.

### 3. Start the bot
```shell
sudo systemctl enable docker
docker-compose up --build -d
```

This will:
1. Build the Docker image
2. Start the PostgreSQL database
3. Run database migrations automatically
4. Start the bot

### 4. Verify the bot is running
```shell
docker-compose logs -f discordbot
```

For the full installation guide, see the [Wiki](https://ddc.github.io/DiscordBot).


# Configuration

All configuration is done through environment variables in the `.env` file.

### Bot Settings
| Variable                  | Default           | Description                                                |
|:--------------------------|:------------------|:-----------------------------------------------------------|
| `BOT_TOKEN`               |                   | Discord bot token **(required)**                           |
| `BOT_PREFIX`              | `!`               | Command prefix                                             |
| `BOT_EMBED_COLOR`         | `green`           | Default embed color                                        |
| `BOT_EMBED_OWNER_COLOR`   | `dark_purple`     | Owner command embed color                                  |
| `BOT_ALLOWED_DM_COMMANDS` | `owner,about,gw2` | Commands allowed in DMs                                    |
| `BOT_BOT_REACTION_WORDS`  | `stupid,noob`     | Words that trigger bot reactions                           |
| `BOT_EXCLUSIVE_USERS`     |                   | Restrict bot to specific users (comma-separated IDs)       |
| `BOT_BG_ACTIVITY_TIMER`   | `0`               | Background activity rotation timer (seconds, 0 = disabled) |

### OpenAI Settings
| Variable           | Default       | Description         |
|:-------------------|:--------------|:--------------------|
| `OPENAI_API_KEY`   |               | OpenAI API key      |
| `BOT_OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |

### PostgreSQL Settings
| Variable              | Default               | Description       |
|:----------------------|:----------------------|:------------------|
| `POSTGRESQL_HOST`     | `discordbot_database` | Database host     |
| `POSTGRESQL_PORT`     | `5432`                | Database port     |
| `POSTGRESQL_USER`     | `postgres`            | Database user     |
| `POSTGRESQL_PASSWORD` | `postgres`            | Database password |
| `POSTGRESQL_DATABASE` | `discordbot`          | Database name     |
| `POSTGRESQL_SCHEMA`   | `public`              | Database schema   |

### Logging Settings
| Variable           | Default           | Description           |
|:-------------------|:------------------|:----------------------|
| `LOG_LEVEL`        | `INFO`            | Log level             |
| `LOG_TIMEZONE`     | `UTC`             | Log timezone          |
| `LOG_DIRECTORY`    | `/app/DiscordBot` | Log file directory    |
| `LOG_DAYS_TO_KEEP` | `30`              | Log retention in days |

See [.env.example](.env.example) for the complete list of configuration options including cooldowns, SSL, connection pooling, and retry settings.


# Commands

### OpenAI Commands
| Command        | Description                                      |
|:---------------|:-------------------------------------------------|
| `ai <message>` | Ask OpenAI for assistance, response as embed     |

### Admin/Mod Commands
| Command                    | Description                     |
|:---------------------------|:--------------------------------|
| `admin botgame <new game>` | Change game that bot is playing |

### Config Commands
| Command                                    | Description                                  |
|:-------------------------------------------|:---------------------------------------------|
| `admin config list`                        | List all bot configurations                  |
| `admin config joinmessage [on, off]`       | Toggle message when a user joins the server  |
| `admin config leavemessage [on, off]`      | Toggle message when a user leaves the server |
| `admin config servermessage [on, off]`     | Toggle message when a server gets updated    |
| `admin config membermessage [on, off]`     | Toggle message when someone updates profile  |
| `admin config blockinvisible [on, off]`    | Block messages from invisible members        |
| `admin config botreactions [on, off]`      | Toggle bot reactions to member words         |
| `admin config pfilter [on, off] <channel>` | Configure profanity filter per channel       |

### Custom Commands
| Command                               | Description                        |
|:--------------------------------------|:-----------------------------------|
| `admin cc add <command> <text>`       | Add a new custom command           |
| `admin cc edit <command> <text>`      | Edit an existing custom command    |
| `admin cc remove <command>`           | Remove a custom command            |
| `admin cc removeall`                  | Remove all custom commands         |
| `admin cc list`                       | List all custom commands           |

### Misc Commands
| Command             | Description                             |
|:--------------------|:----------------------------------------|
| `about`             | Display bot info                        |
| `echo <message>`    | Show your message again                 |
| `ping`              | Test latency                            |
| `pepe`              | Post a random Pepe image                |
| `tts <message>`     | Send text-to-speech as .mp3 to channel  |
| `serverinfo`        | Show server information                 |
| `userinfo <member>` | Show Discord user information           |
| `lmgtfy <search>`   | Create a LMGTFY link                    |
| `invites`           | List active invite links for the server |

### Dice Rolls Commands
| Command                  | Description                               |
|:-------------------------|:------------------------------------------|
| `roll`                   | Roll a die (defaults to 100)              |
| `roll <size>`            | Roll a die with specified size            |
| `roll results`           | Display all dice rolls from the server    |
| `roll reset`             | Delete all dice rolls (admin only)        |

### Bot Owner Commands
| Command                                  | Description                     |
|:-----------------------------------------|:--------------------------------|
| `owner servers`                          | Display all servers in database |
| `owner prefix <new prefix>`              | Change bot prefix for commands  |
| `owner botdescription <new description>` | Update bot description          |

### GW2 Commands
| Command             | Description                               |
|:--------------------|:------------------------------------------|
| `gw2 account`       | Display your GW2 account information      |
| `gw2 characters`    | Display your GW2 characters information   |
| `gw2 session`       | Display your last game session data       |
| `gw2 worlds na`     | List all NA worlds with WvW tier          |
| `gw2 worlds eu`     | List all EU worlds with WvW tier          |
| `gw2 wiki <search>` | Search the Guild Wars 2 wiki              |
| `gw2 info <search>` | Information about a given name/skill/rune |

### GW2 Config Commands
| Command                        | Description                           |
|:-------------------------------|:--------------------------------------|
| `gw2 config list`              | List all GW2 configurations           |
| `gw2 config session [on, off]` | Toggle recording of user sessions     |

### GW2 Key Commands
| Command                    | Description                   |
|:---------------------------|:------------------------------|
| `gw2 key add [api_key]`    | Add your first GW2 API key    |
| `gw2 key update [api_key]` | Update your existing API key  |
| `gw2 key remove`           | Remove your GW2 API key       |
| `gw2 key info`             | Show your API key information |

### GW2 WvW Commands
| Command                 | Description            |
|:------------------------|:-----------------------|
| `gw2 wvw info [world]`  | Info about a WvW world |
| `gw2 wvw match [world]` | WvW match scores       |
| `gw2 wvw kdr [world]`   | WvW kill/death ratios  |


# Development and Testing

Requires [UV](https://docs.astral.sh/uv/getting-started/installation/) to be installed.

### Setup
```shell
uv sync --all-extras --all-groups
```

### Running Tests
```shell
# Unit tests
poe test

# Integration tests (requires Docker for testcontainers)
poe test-integration

# All tests (unit + integration + hadolint + docker)
poe tests
```

### Other Tasks
```shell
# Run linter (ruff)
poe linter

# Update all dev dependencies
poe updatedev

# Run database migrations
poe migration

# Profile unit tests
poe profile

# Profile integration tests
poe profile-integration
```


# Acknowledgements
- [Discord Bot API](https://discord.com/developers/applications)
- [OpenAI API](https://openai.com/api)
- [Guild Wars 2 API](https://wiki.guildwars2.com/wiki/API:2)
- [PostgreSQL](https://www.postgresql.org)


# Support
If you find this project helpful, consider supporting development:

- [GitHub Sponsor](https://github.com/sponsors/ddc)
- [ko-fi](https://ko-fi.com/ddcsta)
- [PayPal](https://www.paypal.com/ncp/payment/6G9Z78QHUD4RJ)


# License
Released under the [MIT License](LICENSE)
