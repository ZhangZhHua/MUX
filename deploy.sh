#!/usr/bin/env bash
set -e

if [ ! -f .env.prod ]; then
  cp .env.prod.example .env.prod
  if grep -q "yoursecurerandomsecretkey" .env.prod; then
    NEW_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i.bak "s/yoursecurerandomsecretkeyforjwttokenencoding2026prod/$NEW_KEY/" .env.prod
    rm -f .env.prod.bak
  fi
  echo "Created .env.prod — edit DB_PASSWORD before deploying"
fi

find . -name "._*" -delete 2>/dev/null
docker compose --env-file .env.prod up -d --build

# Get the project name (defaults to directory name)
PROJ=$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
BACKEND="${PROJ}-mux-backend-1"
GATEWAY="${PROJ}-mux-nginx-1"

sleep 3
for script in migrate_event_group.py migrate_soft_delete.py migrate_private_groups.py migrate_user_status.py; do
  docker exec "$BACKEND" python $script 2>/dev/null || true
done
docker restart "$GATEWAY" 2>/dev/null || true

PORT=$(grep APP_PORT .env.prod 2>/dev/null | cut -d= -f2 | tr -d ' ' || echo "18080")
echo ""
echo "  MUX Lab Log running → http://localhost:${PORT:-18080}"
echo "  First to register becomes admin"
