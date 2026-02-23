#!/usr/bin/env bash
set -euo pipefail

PROJECT_USERNAME=ddc
PROJECT_DIR=/opt/DiscordBot

pushd "$PROJECT_DIR" > /dev/null

# update project
sudo git fetch --all
sudo git reset --hard origin/master

# change perms
sudo chown -R "$PROJECT_USERNAME":"$PROJECT_USERNAME" "$PROJECT_DIR"
sudo find "$PROJECT_DIR" -type d -exec chmod 755 {} +
sudo find "$PROJECT_DIR" -type f -exec chmod 644 {} +
sudo chmod 600 "$PROJECT_DIR/.env"
sudo chmod 755 "$PROJECT_DIR/utilities"/*.sh

# ensure logs dir is writable by container's botuser (uid 1000)
sudo chown 1000:1000 "$PROJECT_DIR/logs"

popd > /dev/null
