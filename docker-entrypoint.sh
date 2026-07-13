#!/bin/sh
set -eu

DB_HOST="${DB_HOST:-mux-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-mux_prod_admin}"
DB_PASSWORD="${DB_PASSWORD:-mux_lab_password_2026}"
DB_NAME="${DB_NAME:-mux_lab_logs}"

export DATABASE_URL="${DATABASE_URL:-postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}}"
export BACKUP_DIR="${BACKUP_DIR:-/backups}"

mkdir -p /app/uploads "$BACKUP_DIR" /var/log/supervisor

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

echo "[MUX] PostgreSQL is ready; starting FastAPI and Nginx."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/mux.conf
