# MUX Lab Log System

> Collaborative research management for physics laboratories — experiments, shift logs, scheduling, and team coordination.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Prerequisites

- **Docker** ≥ 20.10 & **Docker Compose** ≥ v2
- Linux / macOS / Windows (WSL2)
- 2 GB free RAM, 5 GB disk space

## Quick Deploy

```bash
git clone https://github.com/ZhangZhHua/MUX.git && cd MUX && ./deploy.sh
```

Open `http://localhost:18080`, register — the first account becomes **admin**.

## Server Deployment

Same as above — run `./deploy.sh` on your server. Then:

### Option A: Reverse proxy (recommended)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
```

### Option B: Direct port exposure

Set `APP_PORT=80` in `.env.prod` before running `./deploy.sh`, then access via `http://your-server-ip`.

### Firewall

```bash
# If using firewall
sudo ufw allow 18080/tcp    # or 80/tcp
```

## Configuration

Edit `.env.prod` (auto-generated on first `./deploy.sh`)：

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PORT` | `18080` | External HTTP port |
| `DB_USER` | `lab_user` | PostgreSQL user |
| `DB_PASSWORD` | — | PostgreSQL password **(change this!)** |
| `DB_NAME` | `lab_logs` | Database name |
| `SECRET_KEY` | auto-generated | JWT signing key |

## Features

- **Experiments** — CRUD with tags, status (running/paused/stopped), Markdown docs
- **Daily Shift Logs** — Kanban by date, multi-attachment, clipboard image paste (Ctrl+V)
- **Lab Events** — Weekly calendar, recurring events, participant tracking, comments
- **Team Management** — Research groups, role-based access, member profiles
- **Private Workspaces** — Each user gets a `[Private]` group invisible to others
- **Recycle Bin** — Soft-delete experiments; admins restore or permanently destroy
- **Registration Approval** — Optional admin-approval workflow for new accounts
- **Dark Mode** — Light / Dark / System theme, English / Chinese i18n
- **Session Timeout** — Configurable idle detection with auto-logout

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vue Router 5, Axios, Vite 8 |
| Backend | FastAPI, SQLAlchemy ORM, Pydantic v2 |
| Database | PostgreSQL 15 |
| Auth | JWT + bcrypt |
| Deploy | Docker Compose + Nginx |

## Roles

| Role | Capabilities |
|------|-------------|
| `member` | View experiments/logs/events; edit own logs; toggle step completion |
| `team_admin` | Create/delete experiments in their groups; manage members; approve registrations |
| `sys_admin` | Full access; create groups; system settings; permanent delete; all approvals |

## License

MIT
