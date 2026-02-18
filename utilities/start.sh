#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=/opt/DiscordBot
pushd "$PROJECT_DIR" > /dev/null

docker compose down
docker images 'discordbot*' -a -q | xargs -r docker rmi -f
docker compose up -d --build --force-recreate

popd > /dev/null
