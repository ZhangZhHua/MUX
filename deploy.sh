#!/usr/bin/env bash
set -e

# Create .env.prod if missing
if [ ! -f .env.prod ]; then
  cp .env.prod.example .env.prod
  if grep -q "yoursecurerandomsecretkey" .env.prod; then
    NEW_KEY=$(openssl rand -hex 32)
    sed -i.bak "s/yoursecurerandomsecretkeyforjwttokenencoding2026prod/$NEW_KEY/" .env.prod
    rm -f .env.prod.bak
  fi
  echo "✅ Created .env.prod — edit DB_PASSWORD before deploying"
fi

find . -name "._*" -delete 2>/dev/null
docker compose up -d --build

sleep 3
docker exec mux_backend python migrate_event_group.py 2>/dev/null || true
docker exec mux_backend python migrate_soft_delete.py 2>/dev/null || true
docker exec mux_backend python migrate_private_groups.py 2>/dev/null || true
docker exec mux_backend python migrate_user_status.py 2>/dev/null || true
docker restart mux_gateway 2>/dev/null || true

PORT=$(grep APP_PORT .env.prod 2>/dev/null | cut -d= -f2 || echo "18080")
echo ""
echo "  ✅  MUX Lab Log is running → http://localhost:${PORT:-18080}"
echo "  📝  First to register becomes admin"
