#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pushd "$PROJECT_DIR" > /dev/null

docker compose down
docker images 'discordbot*' -a -q | xargs -r docker rmi -f

# ensure logs dir is writable by container's user (uid 65534, matches Dockerfile USER)
sudo chown -RH 65534:65534 "$PROJECT_DIR/logs"
sudo chmod 755 "$PROJECT_DIR/logs"

docker compose up -d --build --force-recreate

popd > /dev/null
