# MUX Lab Log System

> A collaborative research management platform for physics laboratories — experiments, shift logs, scheduling, and team coordination.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- **Experiment Management** — CRUD with tags, status tracking (running/paused/stopped), Markdown documentation
- **Daily Shift Logs** — Kanban-board logs grouped by date, multi-attachment support, clipboard image paste
- **Lab Events & Scheduling** — Weekly calendar, recurring events, participant tracking, comments
- **Team Management** — Research groups, role-based access (sys_admin / team_admin / member), member profiles
- **Private Workspaces** — Each user gets a personal `[Private]` group, invisible to others
- **Recycle Bin** — Soft-delete experiments; admins can restore or permanently destroy
- **Registration Approval** — Optional admin-approval workflow for new accounts
- **Dark Mode** — Light / Dark / System theme switching
- **i18n** — English / Chinese language support
- **Session Timeout** — Configurable idle detection with auto-logout

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3 (Composition API), Vue Router 5, Axios, Vite 8 |
| Backend | FastAPI, SQLAlchemy ORM, Pydantic v2 |
| Database | PostgreSQL 15 |
| Auth | JWT (python-jose) + bcrypt |
| Deployment | Docker Compose + Nginx reverse proxy |

## Quick Start (Production)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose v2+
- Git

### 1. Clone & configure

```bash
git clone https://github.com/ZhangZhHua/MUX.git
cd MUX

# Create production environment file
cp .env.prod.example .env.prod
# Edit .env.prod — change DB_PASSWORD and SECRET_KEY
```

### 2. Deploy

```bash
# One-command deploy (cleans macOS metadata, builds & starts all services)
find . -name "._*" -delete && docker compose -f docker-compose.prod.yml up -d --build
```

The app will be available at `http://localhost:18080` (configurable via `APP_PORT` in `.env.prod`).

### 3. First login

The first registered user automatically becomes **sys_admin**. Register at `/register`, then log in.

## Development Setup

### 1. Start PostgreSQL

```bash
docker compose up -d
```

### 2. Start backend

```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
# API docs: http://127.0.0.1:8000/docs
```

### 3. Start frontend

```bash
cd client
npm install
npm run dev
# App: http://localhost:5173
```

## Architecture

```
Browser (SPA) → Nginx :18080 → /api/*   → FastAPI :8000 → PostgreSQL :5432
                              → /*       → Vue SPA :80
```

```
client/   Vue 3 SPA (views, components, composables, router, i18n)
server/   FastAPI (routers, models, schemas, utils)
nginx/    Reverse proxy config
scripts/  Git helper scripts
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PORT` | `18080` | External HTTP port |
| `DB_USER` | `lab_user` | PostgreSQL user |
| `DB_PASSWORD` | — | PostgreSQL password |
| `DB_NAME` | `lab_logs` | Database name |
| `SECRET_KEY` | — | JWT signing key (use `openssl rand -hex 32`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime in minutes |

## Database Migrations

Run inside the backend container after schema changes:

```bash
docker exec mux_backend python migrate_event_group.py
docker exec mux_backend python migrate_soft_delete.py
docker exec mux_backend python migrate_private_groups.py
docker exec mux_backend python migrate_user_status.py
```

## Roles & Permissions

| Role | Capabilities |
|------|-------------|
| `member` | View experiments, logs, events; toggle step completion; edit own logs |
| `team_admin` | Create/delete experiments in their groups; manage group members; approve registrations |
| `sys_admin` | Full access; create groups; system settings; permanent delete; all approvals |

## License

MIT

## Author

[ZhangZhHua](https://github.com/ZhangZhHua)
