#!/usr/bin/env bash
set -euo pipefail

echo "🚀 MUX — Deploying two-container architecture"

if [ ! -f .env.prod ]; then
    cp .env.prod.example .env.prod

    new_key="$(openssl rand -hex 32)"
    new_db_password="$(openssl rand -hex 16)"
    sed -i.bak "s/change-me-to-a-random-32-byte-hex-string/${new_key}/" .env.prod
    sed -i.bak "s/your_secure_password_here/${new_db_password}/" .env.prod
    rm -f .env.prod.bak
    echo "✅ Created .env.prod with generated credentials"
fi

mkdir -p backups server/uploads

compose=(docker compose --env-file .env.prod)

if command -v npm >/dev/null 2>&1; then
    if [ ! -d client/node_modules ]; then
        echo "📥 Installing frontend dependencies..."
        npm --prefix client config set registry https://registry.npmmirror.com
        npm --prefix client ci
    fi
    echo "🧱 Building frontend static files..."
    npm --prefix client run build
elif [ ! -f client/dist/index.html ]; then
    echo "❌ Node.js/npm is required because client/dist is not present."
    exit 1
fi

# Building files on macOS can create new AppleDouble metadata. Clean it only
# after the frontend build and immediately before Docker reads the context.
find . -name '._*' -type f -not -path './.git/*' -delete 2>/dev/null || true

# Preserve a restorable host-side snapshot before replacing containers.
db_container="$("${compose[@]}" ps -q mux-db 2>/dev/null || true)"
if [ -n "$db_container" ] && docker inspect --format '{{.State.Running}}' "$db_container" 2>/dev/null | grep -q true; then
    timestamp="$(date +%Y-%m-%d_%H%M%S)"
    backup_file="backups/mux_pre_deploy_${timestamp}.sql"
    echo "💾 Backing up the existing database to ${backup_file}..."
    if docker exec "$db_container" sh -c \
        'PGPASSWORD="$POSTGRES_PASSWORD" pg_dumpall -U "$POSTGRES_USER"' >"$backup_file"; then
        chmod 600 "$backup_file"
    else
        rm -f "$backup_file"
        echo "❌ Database backup failed; deployment stopped without replacing containers."
        exit 1
    fi
fi

# Build completely before stopping the old frontend/backend/nginx containers.
echo "📦 Building mux-app..."
"${compose[@]}" build mux-app

echo "🔄 Starting mux-db and mux-app..."
"${compose[@]}" up -d --remove-orphans

port="$(sed -n 's/^APP_PORT=//p' .env.prod | tail -1)"
volume_name="$(sed -n 's/^DB_VOLUME_NAME=//p' .env.prod | tail -1)"
echo "✅ MUX is running at http://localhost:${port:-18080}"
echo "   Database volume: ${volume_name:-physics-lab-log_postgres_prod_data}"
echo "   Host backups:    ./backups"
