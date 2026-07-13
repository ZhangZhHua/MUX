# MUX Lab Log

> Physics lab collaboration platform — experiment management, shift logs, scheduling, team collaboration, ready to use.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

<details>
<summary><strong>🇨🇳 中文版 / Chinese Version</strong></summary>

<br>

# MUX Lab Log

> 物理学实验室协作平台 — 实验管理、值班日志、日程安排、团队协作，开箱即用。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 这是什么

MUX Lab Log 是一个面向**物理实验室**的 Web 协作系统。替代传统的纸质日志和分散的 Excel，把实验项目、每日值班记录、周日程、团队成员集中管理。

**典型场景：** 高能物理、凝聚态、光学等课题组，多人轮班操作实验设备，需要记录每日运行状态、异常事件、交接事项。

| 模块 | 做什么 |
|------|--------|
| 📊 实验管理 | 创建实验项目，标签分类，Markdown 文档，运行状态追踪 |
| 📋 值班日志 | 按日期分列看板，多人值班记录，附件上传，支持截图粘贴 |
| 📅 实验室日程 | 周视图日历，周期重复事件，参与人员，评论互动 |
| 👥 团队管理 | 多课题组，三级角色权限，成员档案，私人工作区 |
| 🗑️ 回收站 | 误删实验可恢复，管理员永久销毁 |
| 🌙 暗色模式 | Light / Dark / System 三模式，中英文界面 |
| ⏱️ 会话安全 | 可配超时自动登出，注册审批开关 |
| 💾 自动备份 | 每日 3:00 AM 自动备份，保留 7 天，可手动恢复 |

## 快速部署

需要 **Docker** 和 Node.js/npm。Node.js 只用于构建前端，不进入最终镜像。

```bash
git clone https://github.com/ZhangZhHua/MUX.git && cd MUX && ./deploy.sh
```

打开 `http://localhost:18080`，注册 → 第一个账号即为管理员。

服务器部署同样三条命令。需要域名的话用 Nginx 反代到 `127.0.0.1:18080`。端口可通过 `.env.prod` 中的 `APP_PORT` 修改。

## 技术栈

Vue 3 · FastAPI · PostgreSQL 15 · Docker · Nginx

## 角色权限

| 角色 | 权限 |
|------|------|
| `member` | 查看实验/日志/日程；编辑自己的日志 |
| `team_admin` | 组内创建/删除实验；管理成员；审批新用户 |
| `sys_admin` | 全部权限：建组、系统设置、永久删除、查看所有数据 |

## License

MIT · [ZhangZhHua](https://github.com/ZhangZhHua)

</details>

---

## What is MUX Lab Log?

MUX Lab Log is a **web-based collaboration system** designed for physics laboratories. It replaces paper logbooks and scattered spreadsheets, centralizing experiment projects, daily shift logs, weekly schedules, and team members in one place.

**Typical use case:** High-energy physics, condensed matter, optics, and other research groups where multiple people operate shared equipment in shifts and need to record daily status, anomalies, and handover notes.

| Module | What it does |
|--------|-------------|
| 📊 Experiments | Create experiment projects, tag-based categorization, Markdown documentation, status tracking |
| 📋 Shift Logs | Date-column Kanban board, multi-user shift records, file attachments, paste-from-clipboard images |
| 📅 Lab Events | Weekly calendar view, recurring events, participant lists, comments |
| 👥 Teams | Multiple research groups, three-tier role permissions, member profiles, private workspaces |
| 🗑️ Recycle Bin | Soft-delete experiments with admin restore or permanent purge |
| 🌙 Dark Mode | Light / Dark / System three-mode toggle, English & Chinese UI |
| ⏱️ Session Security | Configurable auto-logout timeout, registration approval toggle |
| 💾 Auto Backup | Daily 3:00 AM automated backup, 7-day retention, manual restore |

## Quick Deploy

**Prerequisites:** Docker and Node.js/npm (Node is only used to build the frontend; it does not go into the final image).

```bash
git clone https://github.com/ZhangZhHua/MUX.git && cd MUX && ./deploy.sh
```

Open `http://localhost:18080`, register — the first account becomes the system admin.

Server deployment uses the same three commands. For a custom domain, reverse-proxy to `127.0.0.1:18080` via Nginx. Change the port via `APP_PORT` in `.env.prod`.

## After Deployment

```bash
# Check running services
docker compose --env-file .env.prod ps

# View logs
docker compose --env-file .env.prod logs -f

# Manual database backup
docker compose --env-file .env.prod exec mux-db \
  sh -c 'PGPASSWORD="$DB_PASSWORD" pg_dumpall -U "$DB_USER"' > backups/manual.sql
```

## Tech Stack

**Frontend:** Vue 3 · Vite  
**Backend:** FastAPI (Python) · SQLAlchemy  
**Database:** PostgreSQL 15  
**Infra:** Docker · Nginx · Supervisor

## Roles & Permissions

| Role | Permissions |
|------|------------|
| `member` | View experiments/logs/events; edit own logs |
| `team_admin` | Create/delete experiments in group; manage members; approve new users |
| `sys_admin` | Full access: create groups, system settings, permanent delete, view all data |

## License

MIT © [ZhangZhHua](https://github.com/ZhangZhHua)
