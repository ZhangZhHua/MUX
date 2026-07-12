# MUX Lab Log

> 物理学实验室协作平台 — 实验管理、值班日志、日程安排、团队协作，开箱即用。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 这是什么

MUX Lab Log 是一个面向**物理实验室**的 Web 协作系统。替代传统的纸质日志和分散的 Excel，把实验项目、每日值班记录、周日程、团队成员集中管理。

**典型场景：** 高能物理、凝聚态、光学等课题组，多人轮班操作实验设备，需要记录每日运行状态、异常事件、交接事项。

| 模块 | 做什么 |
|------|--------|
| 📊 实验管理 | 创建实验项目，标签分类，Markdown 文档，运行状态追踪 |
| 📋 值班日志 | 按日期分列 Kanban 看板，多人值班记录，附件上传，支持截图粘贴 |
| 📅 实验室日程 | 周视图日历，周期重复事件，参与人员，评论互动 |
| 👥 团队管理 | 多课题组，三级角色权限，成员档案，私人工作区 |
| 🗑️ 回收站 | 误删实验可恢复，管理员永久销毁 |
| 🌙 暗色模式 | Light / Dark / System 三模式，中英文界面 |
| ⏱️ 会话安全 | 可配超时自动登出，注册审批开关 |

## 部署

需要 **Docker**，无需安装数据库、无需配置 Python 环境。

```bash
git clone https://github.com/ZhangZhHua/MUX.git
cd MUX
./deploy.sh
```

打开 `http://localhost:18080`，注册第一个账号即为管理员。

### 部署到服务器

和在本地一样 — 把仓库 clone 到服务器，运行 `./deploy.sh`。如需域名访问，在 Nginx 里加一条反代：

```nginx
location / {
    proxy_pass http://127.0.0.1:18080;
    proxy_set_header Host $host;
    client_max_body_size 50M;
}
```

修改 `.env.prod` 中 `APP_PORT` 可自定义端口（如 `APP_PORT=80`）。

### 配置项

首次部署会自动生成 `.env.prod`，可修改：

| 变量 | 默认 | 说明 |
|------|------|------|
| `APP_PORT` | `18080` | 对外访问端口 |
| `DB_PASSWORD` | — | **必须修改** |
| `SECRET_KEY` | 自动生成 | JWT 签名密钥 |
| `DB_NAME` | `lab_logs` | 数据库名 |

## 技术栈

Vue 3 · FastAPI · PostgreSQL 15 · Docker · Nginx

## 角色权限

| 角色 | 权限 |
|------|------|
| `member` | 查看实验/日志/日程；编辑自己的日志；勾选实验步骤 |
| `team_admin` | 组内创建/删除实验；管理成员；发布公告；审批新用户 |
| `sys_admin` | 全部权限：建组、系统设置、永久删除、查看所有数据 |

## License

MIT
