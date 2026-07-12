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

sleep 5
echo ""
echo "  MUX Lab Log is running"
echo "  First to register becomes admin"

PORT=$(grep APP_PORT .env.prod 2>/dev/null | cut -d= -f2 | tr -d ' ' || echo "18080")
echo "  http://localhost:${PORT:-18080}"
