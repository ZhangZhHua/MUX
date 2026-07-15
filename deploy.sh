#!/usr/bin/env bash
set -euo pipefail

echo "🚀 MUX — Deploying two-container architecture"

if [ ! -f .env.prod ]; then
    cp .env.prod.example .env.prod

    new_key="$(openssl rand -hex 32)"
    new_db_password="$(openssl rand -hex 16)"
    new_app_db_password="$(openssl rand -hex 24)"
    new_backup_db_password="$(openssl rand -hex 24)"
    new_backup_key="$(openssl rand -hex 32)"
    sed -i.bak "s/change-me-to-a-random-32-byte-hex-string/${new_key}/" .env.prod
    sed -i.bak "s/your_secure_password_here/${new_db_password}/" .env.prod
    sed -i.bak "s/change-me-to-a-random-app-db-password/${new_app_db_password}/" .env.prod
    sed -i.bak "s/change-me-to-a-random-backup-db-password/${new_backup_db_password}/" .env.prod
    sed -i.bak "s/change-me-to-a-random-backup-encryption-key/${new_backup_key}/" .env.prod
    rm -f .env.prod.bak
    echo "✅ Created .env.prod with generated credentials"
fi

ensure_env() {
    local key="$1"
    local value="$2"
    if ! grep -q "^${key}=" .env.prod; then
        printf '\n%s=%s\n' "$key" "$value" >> .env.prod
    fi
}

ensure_env BACKUP_ENCRYPTION_KEY "$(openssl rand -hex 32)"
ensure_env APP_DB_USER mux_app
ensure_env APP_DB_PASSWORD "$(openssl rand -hex 24)"
ensure_env BACKUP_DB_USER mux_backup
ensure_env BACKUP_DB_PASSWORD "$(openssl rand -hex 24)"

cookie_secure="$(sed -n 's/^COOKIE_SECURE=//p' .env.prod | tail -1)"
app_bind_address="$(sed -n 's/^APP_BIND_ADDRESS=//p' .env.prod | tail -1)"
if [ "${cookie_secure:-false}" != "true" ] && [ "${app_bind_address:-127.0.0.1}" != "127.0.0.1" ] && [ "${app_bind_address:-127.0.0.1}" != "localhost" ]; then
    echo "❌ Remote deployments require TLS: set COOKIE_SECURE=true before binding outside localhost."
    exit 1
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
    backup_file="backups/mux_pre_deploy_${timestamp}.sql.enc"
    echo "💾 Backing up the existing database to ${backup_file}..."
    backup_key="$(sed -n 's/^BACKUP_ENCRYPTION_KEY=//p' .env.prod | tail -1)"
    if docker exec "$db_container" sh -c \
        'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges' \
        | openssl enc -aes-256-cbc -pbkdf2 -salt -pass "pass:${backup_key}" -out "$backup_file"; then
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

echo "🔄 Starting mux-db..."
"${compose[@]}" up -d mux-db

db_container="$("${compose[@]}" ps -q mux-db)"
for _ in $(seq 1 60); do
    if docker inspect --format '{{.State.Health.Status}}' "$db_container" 2>/dev/null | grep -q healthy; then
        break
    fi
    sleep 2
done
if ! docker inspect --format '{{.State.Health.Status}}' "$db_container" 2>/dev/null | grep -q healthy; then
    echo "❌ mux-db did not become healthy in time."
    exit 1
fi

db_name="$(sed -n 's/^DB_NAME=//p' .env.prod | tail -1)"
db_owner="$(sed -n 's/^DB_USER=//p' .env.prod | tail -1)"
app_db_password="$(sed -n 's/^APP_DB_PASSWORD=//p' .env.prod | tail -1)"
backup_db_password="$(sed -n 's/^BACKUP_DB_PASSWORD=//p' .env.prod | tail -1)"
echo "🔐 Provisioning least-privilege database roles..."
bash scripts/provision-db-roles.sh "$db_container" "$db_name" "$db_owner" "$app_db_password" "$backup_db_password"

echo "🗃️ Applying schema migrations with the isolated migrator..."
"${compose[@]}" --profile migration run --rm mux-migrator

echo "🔄 Starting mux-app and mux-scheduler..."
"${compose[@]}" up -d --remove-orphans

port="$(sed -n 's/^APP_PORT=//p' .env.prod | tail -1)"
volume_name="$(sed -n 's/^DB_VOLUME_NAME=//p' .env.prod | tail -1)"
echo "✅ MUX is running at http://localhost:${port:-18080}"
echo "   Database volume: ${volume_name:-physics-lab-log_postgres_prod_data}"
echo "   Host backups:    ./backups"
