# MUX Lab Log

物理学实验室协作平台 — 实验管理、值班日志、日程安排、团队协作。

## 部署

需要 **Docker**。

```bash
git clone https://github.com/ZhangZhHua/MUX.git && cd MUX && ./deploy.sh
```

访问 `http://localhost:18080`，注册 → 第一个账号即管理员。

---

### 部署到服务器

```bash
git clone https://github.com/ZhangZhHua/MUX.git && cd MUX
# 编辑 .env.prod：改 DB_PASSWORD，设 APP_PORT=80
./deploy.sh
```

如需域名，Nginx 反代到 `127.0.0.1:18080` 即可。

### 配置

`.env.prod` 首次运行自动生成，可修改：

| 变量 | 默认 | 说明 |
|------|------|------|
| `APP_PORT` | `18080` | 对外端口 |
| `DB_PASSWORD` | — | **必须修改** |
| `SECRET_KEY` | 自动生成 | JWT 密钥 |

## 功能

实验管理 · 值班日志看板 · 周日程 · 团队管理 · 私人工作区 · 回收站 · 暗色模式 · 中英文 · 会话超时

## 技术栈

Vue 3 + FastAPI + PostgreSQL 15 + Docker

## 角色

| 角色 | 权限 |
|------|------|
| `member` | 查看实验/日志/日程，编辑自己的日志 |
| `team_admin` | 管理组内实验和成员，审批注册 |
| `sys_admin` | 全部权限：建组、系统设置、永久删除 |
