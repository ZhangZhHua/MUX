#!/bin/sh
set -eu

DB_HOST="${DB_HOST:-mux-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:?DB_NAME is required}"
if [ "${APP_ROLE:-app}" != "migrator" ]; then
    DB_USER="${APP_DB_USER:?APP_DB_USER is required}"
    DB_PASSWORD="${APP_DB_PASSWORD:?APP_DB_PASSWORD is required}"
else
    DB_USER="${DB_USER:?DB_USER is required}"
    DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD is required}"
fi

export DATABASE_URL="${DATABASE_URL:-postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}}"
if [ -n "${BACKUP_DB_USER:-}" ]; then
    export BACKUP_DATABASE_URL="postgresql://${BACKUP_DB_USER}:${BACKUP_DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
fi
export BACKUP_DIR="${BACKUP_DIR:-/backups}"

# Directories are provisioned and owned by the non-root image user at build
# time. Host-mounted backup volumes must be writable by uid 10001.

echo "[MUX] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
attempt=0
until PGPASSWORD="$DB_PASSWORD" pg_isready \
    --host "$DB_HOST" \
    --port "$DB_PORT" \
    --username "$DB_USER" \
    --dbname "$DB_NAME" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 60 ]; then
        echo "[MUX] PostgreSQL did not become ready in time."
        exit 1
    fi
    sleep 2
done

if [ "${APP_ROLE:-app}" = "scheduler" ]; then
    exec python -m config.scheduler_worker
fi

if [ "${APP_ROLE:-app}" = "migrator" ]; then
    alembic upgrade head
    exit 0
fi

echo "[MUX] Starting FastAPI and Nginx."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/mux.conf
