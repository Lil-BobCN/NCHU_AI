#!/usr/bin/env bash
set -euo pipefail

PUBLIC_HOST="${PUBLIC_HOST:-47.111.163.239}"
SKIP_IMAGE_LOAD="${SKIP_IMAGE_LOAD:-0}"
KEEP_EXISTING_DATA="${KEEP_EXISTING_DATA:-0}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_ROOT="${PACKAGE_ROOT}/source"
BACKUP_ROOT="${PACKAGE_ROOT}/backups"
IMAGE_TAR="${PACKAGE_ROOT}/images/school-agent-images.tar"
COMPOSE_FILE="${SOURCE_ROOT}/deploy/docker-compose.offline.yml"
POSTGRES_SQL="${BACKUP_ROOT}/postgres_rag.sql"
MINIO_TAR="${BACKUP_ROOT}/minio-data.tar"

require_file() {
  if [[ ! -f "$1" ]]; then
    echo "Missing file: $1" >&2
    exit 1
  fi
}

require_file "${COMPOSE_FILE}"
require_file "${POSTGRES_SQL}"
require_file "${MINIO_TAR}"

if [[ "${SKIP_IMAGE_LOAD}" != "1" ]]; then
  require_file "${IMAGE_TAR}"
  docker load -i "${IMAGE_TAR}"
fi

if [[ -f "${SOURCE_ROOT}/.env" ]]; then
  if grep -q '^MINIO_PUBLIC_BASE_URL=' "${SOURCE_ROOT}/.env"; then
    sed -i "s#^MINIO_PUBLIC_BASE_URL=.*#MINIO_PUBLIC_BASE_URL=http://${PUBLIC_HOST}:9002#" "${SOURCE_ROOT}/.env"
  else
    printf '\nMINIO_PUBLIC_BASE_URL=http://%s:9002\n' "${PUBLIC_HOST}" >> "${SOURCE_ROOT}/.env"
  fi
fi

docker compose -f "${COMPOSE_FILE}" down || true

if [[ "${KEEP_EXISTING_DATA}" != "1" ]]; then
  docker volume rm -f deploy_rag_postgres_data deploy_rag_minio_data >/dev/null 2>&1 || true
fi

docker volume create deploy_rag_postgres_data >/dev/null
docker volume create deploy_rag_minio_data >/dev/null

if [[ "${KEEP_EXISTING_DATA}" != "1" ]]; then
  docker run --rm \
    -v deploy_rag_minio_data:/data \
    -v "${BACKUP_ROOT}:/backup:ro" \
    busybox:1.36 \
    sh -c "tar -C /data -xf /backup/minio-data.tar"
fi

docker compose -f "${COMPOSE_FILE}" up -d postgres redis minio

for _ in $(seq 1 60); do
  if docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_isready -U rag -d rag >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_isready -U rag -d rag >/dev/null 2>&1; then
  echo "PostgreSQL did not become ready in time." >&2
  exit 1
fi

if [[ "${KEEP_EXISTING_DATA}" != "1" ]]; then
  docker compose -f "${COMPOSE_FILE}" exec -T postgres psql -U rag -d rag < "${POSTGRES_SQL}"
fi

docker compose -f "${COMPOSE_FILE}" up -d backend worker frontend

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:8010/api/v1/health" >/dev/null 2>&1; then
    echo "Backend health ok."
    break
  fi
  sleep 2
done

echo "Deployment restored."
echo "Frontend:  http://${PUBLIC_HOST}/"
echo "API base:  http://${PUBLIC_HOST}"
echo "Health:    http://${PUBLIC_HOST}/api/v1/health"
echo "Readiness: http://${PUBLIC_HOST}/api/v1/readiness"
echo "MinIO:    http://${PUBLIC_HOST}:9003"
