#!/usr/bin/env bash

PROJECT_USERNAME=ddc
PROJECT_DIR=/opt/DiscordBot

pushd "$PROJECT_DIR" || exit

# update project
git fetch --all
git reset --hard origin/master

# change perms
sudo chown -R $PROJECT_USERNAME:$PROJECT_USERNAME "$PROJECT_DIR" && \
sudo chmod -R 0755 "$PROJECT_DIR"

popd || exit
