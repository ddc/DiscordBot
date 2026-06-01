#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pushd "$PROJECT_DIR" > /dev/null

docker compose down

popd > /dev/null
