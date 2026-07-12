#!/usr/bin/env bash
set -e

if [ ! -f .env.prod ]; then
  cp .env.prod.example .env.prod

  # Auto-generate secrets
  NEW_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
  NEW_DB_PW=$(openssl rand -hex 16 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(16))")

  if grep -q "yoursecurerandomsecretkey" .env.prod; then
    sed -i.bak "s/yoursecurerandomsecretkeyforjwttokenencoding2026prod/$NEW_KEY/" .env.prod
    rm -f .env.prod.bak
  fi
  if grep -q "lab_password_2026" .env.prod; then
    sed -i.bak "s/lab_password_2026/$NEW_DB_PW/" .env.prod
    rm -f .env.prod.bak
  fi

  echo "✅ .env.prod created — DB_PASSWORD and SECRET_KEY auto-generated"
fi

find . -name "._*" -delete 2>/dev/null
docker compose --env-file .env.prod up -d --build

sleep 5
PORT=$(grep APP_PORT .env.prod 2>/dev/null | cut -d= -f2 | tr -d ' ' || echo "18080")
echo ""
echo "  ✅  MUX Lab Log is running → http://localhost:${PORT:-18080}"
echo "  📝  First to register becomes admin"
