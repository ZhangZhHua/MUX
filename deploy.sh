#!/usr/bin/env bash
set -e

echo "=== MUX Lab Log — Production Deploy ==="

# 1. Create .env.prod from template if missing
if [ ! -f .env.prod ]; then
  echo "→ Creating .env.prod from template..."
  cp .env.prod.example .env.prod
  # Generate random secret key if the template has the placeholder
  if grep -q "yoursecurerandomsecretkey" .env.prod; then
    NEW_KEY=$(openssl rand -hex 32)
    sed -i.bak "s/yoursecurerandomsecretkeyforjwttokenencoding2026prod/$NEW_KEY/" .env.prod
    rm -f .env.prod.bak
    echo "  ✅ Generated new SECRET_KEY"
  fi
  echo "  ⚠️  Edit .env.prod to change DB_PASSWORD"
fi

# 2. Clean macOS metadata & deploy
echo "→ Building & starting containers..."
find . -name "._*" -delete 2>/dev/null
docker compose -f docker-compose.prod.yml up -d --build

# 3. Run migrations
echo "→ Running database migrations..."
sleep 3
docker exec mux_backend python migrate_event_group.py 2>/dev/null || true
docker exec mux_backend python migrate_soft_delete.py 2>/dev/null || true
docker exec mux_backend python migrate_private_groups.py 2>/dev/null || true
docker exec mux_backend python migrate_user_status.py 2>/dev/null || true

# 4. Restart gateway
docker restart mux_gateway 2>/dev/null || true

PORT=$(grep APP_PORT .env.prod 2>/dev/null | cut -d= -f2 || echo "18080")
echo ""
echo "========================================="
echo "  ✅ MUX Lab Log is running!"
echo "  🌐 http://localhost:${PORT:-18080}"
echo "  📝 First user to register becomes admin"
echo "========================================="
