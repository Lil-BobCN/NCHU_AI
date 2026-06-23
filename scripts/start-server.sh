#!/usr/bin/env bash
set -euo pipefail

BUILD="${BUILD:-0}"
PUBLIC_HOST="${PUBLIC_HOST:-47.111.163.239}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_ROOT="${PACKAGE_ROOT}/source"

if [[ "${BUILD}" == "1" ]]; then
  docker compose -f "${SOURCE_ROOT}/deploy/docker-compose.yml" up -d --build
else
  docker compose -f "${SOURCE_ROOT}/deploy/docker-compose.offline.yml" up -d
fi

echo "Frontend:  http://${PUBLIC_HOST}/"
echo "API base:  http://${PUBLIC_HOST}"
echo "Health:    http://${PUBLIC_HOST}/api/v1/health"
echo "Readiness: http://${PUBLIC_HOST}/api/v1/readiness"
echo "Local backend: http://127.0.0.1:8010"
