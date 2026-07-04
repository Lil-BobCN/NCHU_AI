#!/usr/bin/env bash
set -euo pipefail

if command -v docker >/dev/null 2>&1; then
  docker --version
else
  yum install -y docker docker-compose-plugin
  systemctl enable --now docker
fi

if docker compose version >/dev/null 2>&1; then
  docker compose version
else
  echo "Docker Compose v2 plugin is missing. Install it, then rerun deployment." >&2
  echo "On Alibaba Cloud Linux, try: yum install -y docker-compose-plugin" >&2
  exit 1
fi
