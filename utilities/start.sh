#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=/opt/DiscordBot
pushd "$PROJECT_DIR" > /dev/null

docker compose down
docker images 'discordbot*' -a -q | xargs -r docker rmi -f

# ensure logs dir is writable by container's botuser (uid 1000)
sudo chown 1000:1000 "$PROJECT_DIR/logs"
sudo chmod 755 "$PROJECT_DIR/logs"

docker compose up -d --build --force-recreate

popd > /dev/null
