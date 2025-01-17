#!/usr/bin/env bash

docker rmi $(docker images 'discordbot*' -a -q) -f
docker compose up -d --build --force-recreate
