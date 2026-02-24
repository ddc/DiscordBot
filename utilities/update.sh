#!/usr/bin/env bash
set -euo pipefail

PROJECT_USERNAME=ddc
PROJECT_DIR=/opt/DiscordBot

pushd "$PROJECT_DIR" > /dev/null

# stop containers
./utilities/stop.sh

# update project
sudo git fetch --all
sudo git reset --hard origin/master

# change perms
sudo chown -R "$PROJECT_USERNAME":"$PROJECT_USERNAME" "$PROJECT_DIR"
sudo find "$PROJECT_DIR" -type d -exec chmod 755 {} +
sudo find "$PROJECT_DIR" -type f -exec chmod 644 {} +
sudo chmod 600 "$PROJECT_DIR/.env"
sudo chmod 755 "$PROJECT_DIR/utilities"/*.sh

# start containers
./utilities/start.sh

popd > /dev/null
