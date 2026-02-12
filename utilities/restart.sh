#!/usr/bin/env bash

PROJECT_DIR=/opt/DiscordBot
pushd "$PROJECT_DIR" || exit

docker compose down
docker rmi "$(docker images 'discordbot*' -a -q)" -f
docker compose up -d --build --force-recreate

popd || exit
