# Git 提交忽略记录

以下文件和目录因 `.gitignore` 规则被忽略，不会提交到远程仓库：

## 忽略的文件/目录列表

| 文件/目录 | 原因 |
|-----------|------|
| `.gitignore` 中的 `.*` 模式 | 隐藏文件（包括 ._, .vscode, .DS_Store 等） |
| `chat.txt` | 对话日志文件 |
| `walkthrough.log` | 运行日志文件 |
| `*.yml` | YML 配置文件（含 docker-compose.yml, docker-compose.prod.yml） |
| `.env` | 环境变量文件（含 .env.production, .env.prod） |
| `node_modules/` | 前端依赖 |
| `venv/` | Python 虚拟环境 |
| `__pycache__/`, `*.pyc` | Python 缓存文件 |
| `dist/` | 构建产物 |
| `server/uploads/` | 服务端上传文件 |
| 所有未暂存的修改文件 | 未被 git add 的文件不会推送 |

## 当前未暂存的修改（不会提交）

这些文件有修改但未被 git add：

- `client/index.html`
- `client/public/favicon.svg`
- `client/src/assets/main.css`
- `client/src/components/layout/Header.vue`
- `client/src/components/layout/Sidebar.vue`
- `client/src/router/index.js`
- `client/src/services/api.js`
- `client/src/views/Dashboard.vue`
- `client/src/views/Login.vue`
- `client/src/views/Register.vue`
- `server/config/database.py`
- `server/main.py`

## 新文件（不会提交）

需手动 git add 后才提交，否则仅存在于本地：

- `.dockerignore`, `client/.dockerignore`, `server/.dockerignore`
- `.env.prod.example`
- `DEPLOY.md`
- `client/.env.production`
- `client/Dockerfile`
- `client/nginx.conf`
- `client/src/components/common/MuxLogo.vue`
- `client/src/views/EventsTimeline.vue`
- `docker-compose.prod.yml`
- `nginx/`
- `server/models/event.py`
- `server/requirements.txt`
- `server/routers/event.py`
- `server/schemas/event.py`
- `test_docker_mirror.py`

## 注意

如果希望提交这些文件，请使用 `git add <file>` 将其纳入暂存区后重新提交。