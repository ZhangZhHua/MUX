# MUX Lab Log 架构文档

> 当前实现基线：2026-07-15。本文描述仓库中的实际运行架构、安全边界和部署流程，不包含特定个人电脑或网络环境的配置。

## 1. 系统定位

MUX Lab Log 是面向物理实验室的多课题组协作平台，核心能力包括：

- 实验项目、标签、状态、步骤、成员与公告管理；
- 每日值班日志、附件上传、预览和历史回溯；
- 实验室日程、重复事件、参与者、评论与附件；
- 多课题组、私人工作区、三级角色与注册审批；
- 组范围审计日志、系统设置、回收站和加密备份。

## 2. 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3、Composition API、Vue Router、Axios、Vite 8 |
| 后端 | FastAPI、Pydantic、SQLAlchemy、Gunicorn、Uvicorn Worker |
| 数据库 | PostgreSQL 15、Alembic |
| Web | Nginx 静态文件与 API 反向代理 |
| 任务调度 | 独立 APScheduler 进程 |
| 部署 | Docker Compose、非 root 应用镜像 |
| 认证 | 短期 JWT HttpOnly Cookie、CSRF Token、bcrypt |
| 文件存储 | 本地上传卷 + PostgreSQL 附件元数据 |

## 3. 运行拓扑

```mermaid
flowchart LR
    Browser[Browser / Vue SPA]

    subgraph AppContainer[mux-app · non-root UID 10001]
        Nginx[Nginx :8080]
        Gunicorn[Gunicorn :8000\nFastAPI workers]
        Static[Hashed SPA assets]
    end

    subgraph Services[Compose services]
        DB[(mux-db\nPostgreSQL 15)]
        Scheduler[mux-scheduler\nAPScheduler]
        Migrator[mux-migrator\none-shot Alembic]
    end

    Uploads[(uploads volume)]
    Backups[(encrypted backups)]

    Browser -->|HTTP(S)| Nginx
    Nginx --> Static
    Nginx -->|/api/*| Gunicorn
    Gunicorn -->|mux_app| DB
    Gunicorn --> Uploads
    Scheduler -->|mux_app settings| DB
    Scheduler -->|mux_backup pg_dump| DB
    Scheduler --> Backups
    Migrator -->|owner / migrator credential| DB
```

持久服务：

| 服务 | 职责 |
|------|------|
| `mux-db` | PostgreSQL；不映射宿主端口 |
| `mux-app` | Nginx + 多 Gunicorn worker；默认映射 `127.0.0.1:18080 → 8080` |
| `mux-scheduler` | 每日备份调度，不运行 Web 服务 |
| `mux-migrator` | `migration` profile 下的一次性 Alembic 迁移容器 |

应用健康检查同时验证 FastAPI `:8000` 和 Nginx `:8080`。生产环境应在可信 TLS 终止层之后运行，并启用 Secure Cookie。

## 4. 目录结构

```text
physics-lab-log/
├── client/
│   └── src/
│       ├── router/                 # 动态导入页面与服务端会话 guard
│       ├── services/api.js         # Cookie、CSRF、401 处理
│       ├── composables/            # toast、主题、i18n、PDF 导出
│       ├── features/pdf/           # 点击导出后按需加载的 PDF 功能
│       ├── components/             # 布局、通用组件、设置组件
│       └── views/                  # Dashboard、Experiment、Events 等页面
├── server/
│   ├── main.py                     # FastAPI、CORS、路由挂载
│   ├── config/                     # 数据库、scheduler worker
│   ├── models/                     # SQLAlchemy 模型、约束与索引
│   ├── schemas/                    # Pydantic 请求/响应校验
│   ├── routers/
│   │   ├── authorization.py        # 统一组/实验/日志授权依赖
│   │   ├── auth.py                 # 会话、用户、组、系统设置
│   │   ├── experiment.py
│   │   ├── daily_log.py
│   │   ├── event.py
│   │   └── backup.py
│   ├── utils/uploads.py            # UUID、签名、路径和哈希校验
│   └── migrations/                 # Alembic 版本化迁移
├── scripts/provision-db-roles.sh   # 最小权限角色配置
├── nginx/default.conf
├── docker-compose.yml
├── docker-entrypoint.sh
├── deploy.sh
└── .env.prod.example
```

## 5. 认证与会话

### 5.1 登录流程

1. `POST /api/auth/login` 校验账号状态和密码；
2. 服务端读取 `SystemSetting.session_timeout`，缺失时才使用环境默认值；
3. JWT、`access_token` Cookie 和 CSRF Cookie 使用相同有效期；
4. `access_token` 设置为 `HttpOnly + SameSite=Lax`，生产 HTTPS 下设置 `Secure`；
5. 前端只把显示所需的角色、姓名和 `user_id` 缓存在 `localStorage`，不保存访问令牌；
6. Axios 使用 `withCredentials`，修改状态的请求从可读 CSRF Cookie 附加 `X-CSRF-Token`。

### 5.2 会话检查

`get_current_user()` 在更新 `last_active_at` 之前计算空闲时长。超过系统会话超时立即返回 401，不会被“先刷新后检查”绕过。Vue Router 对受保护页面调用 `/api/auth/me`，不依赖本地布尔值判断登录状态；全局 Axios 拦截器收到 401 后清理显示缓存并回到登录页。

Bearer Token 仍作为迁移期 API 客户端兼容方式保留；Cookie 认证的非 GET/HEAD/OPTIONS 请求必须通过 CSRF 校验。

## 6. 服务端授权模型

前端角色仅用于控制界面展示，不能作为授权依据。真正权限由服务端统一依赖执行：

| 依赖 | 保证 |
|------|------|
| `require_group_member` | 用户属于目标组，或为 `sys_admin` |
| `require_group_admin` | 目标组可访问，且角色为组管理员或系统管理员 |
| `require_experiment_access` | 在同一 SQL 查询中同时约束实验 ID、删除状态和可访问组 |
| `require_experiment_admin` | 实验可访问，并具备所属组管理权限 |
| `require_daily_log_access` | 日志、实验和组成员关系在同一查询链中校验 |

设计原则：

- 不允许“先按资源 ID 查询，再由调用者选择性判断组权限”；
- 普通用户只能看到自己所属课题组的数据；
- 无权访问的实验/日志通常返回 404，避免泄露资源是否存在；
- 创建事件、日志、公告和附件绑定时同时校验目标组或实验；
- 组成员同步、实验成员同步和管理操作要求对应管理员权限；
- `sys_admin` 是显式全局管理角色，不通过伪造 group ID 获得权限。

## 7. API 模块

所有业务 API 均挂载在 `/api` 下。

| 模块 | 路径 | 主要职责 |
|------|------|----------|
| Auth | `/api/auth/*` | 登录、登出、资料、角色、组成员、审批、系统设置、会话状态 |
| Experiments | `/api/experiments/*` | 实验、标签、回收站、成员、公告、步骤、通知和活动日志 |
| Daily Logs | `/api/experiments/{id}/logs` | 日志 CRUD、附件认领和附件访问 |
| Events | `/api/events/*` | 日程、重复事件、参与者、评论、标签和附件 |
| Backup | `/api/backup/*` | 管理员触发/查看备份、更新备份设置；Web 恢复禁用 |

实验状态在数据库、Pydantic 和前端统一为：

```text
running | paused | completed | archived
```

非法状态（例如旧的 `stopped`）在 Pydantic 层返回 422，不进入数据库。

## 8. 附件安全模型

上传流程由 `server/utils/uploads.py` 统一实现：

1. 最多读取 50 MiB + 1 byte，拒绝空文件和超限文件；
2. 根据真实文件头识别 PDF、PNG、JPEG、GIF、BMP、WebP 和 Office Open XML；
3. 客户端原始文件名只保存为元数据；
4. 服务端生成 UUID 存储名，避免同名覆盖；
5. `Path.resolve()` 确认最终路径位于上传根目录内；
6. 计算 SHA-256，并写入 `attachments` 表；
7. 记录 owner、group、daily_log、媒体类型、大小和创建时间；
8. 日志或事件认领附件时再次校验上传者、组和关联状态。

下载端点只按 `storage_name` 查询附件元数据，再执行 owner/组授权。原始文件名仅用于下载响应。前端通过认证 fetch 获取文件并创建临时 Blob URL，JWT 不进入 query string、浏览器历史或访问日志。

旧版 `daily_logs.attachments` 与事件附件 JSON 暂时保留用于响应兼容；Alembic 回填迁移已为历史文件创建规范化附件元数据。新访问控制以 `attachments` 表为准。

## 9. Markdown 与浏览器安全

- 实验描述使用经过审计的 Markdown 解析器，关闭原始 HTML；
- 不再将用户输入自行拼接为任意 HTML 后交给 `v-html`；
- Nginx 设置 `X-Frame-Options`、`X-Content-Type-Options`、Referrer Policy 和 CSP；
- `/assets/` 中带哈希的构建文件使用一年期 `immutable` 缓存；
- 生产 CORS 来源由 `CORS_ORIGINS` 明确配置，并允许凭据 Cookie。

## 10. 数据库权限与完整性

### 10.1 角色分离

| 数据库身份 | 使用位置 | 权限边界 |
|------------|----------|----------|
| owner / migrator | `mux-db` 初始化和一次性 `mux-migrator` | DDL 与迁移；不注入日常 Web/scheduler |
| `mux_app` | Web 与 scheduler 设置查询 | 表 CRUD、序列使用；无建库、建角色、复制和超级用户权限 |
| `mux_backup` | `pg_dump` | 应用数据库只读；无 DDL、恢复或集群级权限 |

`scripts/provision-db-roles.sh` 每次部署幂等创建/收紧运行时角色，并配置现有表和 owner 新建对象的默认权限。已验证 `mux_app` 与 `mux_backup` 的 `SUPERUSER / CREATEDB / CREATEROLE / REPLICATION` 均为 false，应用角色执行 `CREATE ROLE` 会被 PostgreSQL 拒绝。

### 10.2 迁移

应用启动时不再执行 `Base.metadata.create_all()`。`deploy.sh` 在启动 Web 前运行：

```bash
docker compose --env-file .env.prod --profile migration run --rm mux-migrator
```

当前 Alembic 链包含：

- `20260715_initial_schema`：接管新库和既有未版本化数据库的安全基线；
- `20260715_backfill_attach`：为历史日志、事件和头像文件回填附件元数据。

### 10.3 约束与索引

数据库 CHECK 约束覆盖用户角色、用户状态、实验状态和事件日期范围。主要访问索引包括：

```text
experiments(group_id, is_deleted, updated_at)
daily_logs(experiment_id, created_at)
daily_logs(author_id)
lab_events(group_id, start_date)
activity_logs(group_id, created_at)
notices(group_id, type, created_at)
group_users(group_id, user_id)
```

## 11. 备份与恢复边界

- scheduler 是独立容器，不在 Gunicorn worker 内运行；
- 每天 03:00 读取 `auto_backup`，关闭时不执行；
- `backup_retention_days` 实际控制清理范围，限制为 1–3650 天；
- 使用 `mux_backup` 对单个应用数据库执行 `pg_dump --no-owner --no-privileges`；
- 明文 SQL 只存在于临时文件，随后通过 AES-256-CBC + PBKDF2 加密；
- `BACKUP_ENCRYPTION_KEY` 缺失或仍为占位值时备份失败；
- Web 恢复端点固定返回 409，不向 Web 容器提供 owner/恢复权限；
- 恢复必须进入维护窗口，由 owner 身份离线执行和验证。

当前 `./backups` 仍是宿主机挂载目录。加密降低静态泄露风险，但独立异地存储和自动恢复演练仍属于运维层后续工作。

## 12. 前端加载与查询性能

- 所有 Vue 页面路由使用动态导入；
- `pdfmake`、字体注册、图片加载与 PDF 构建仅在点击导出后加载；
- PDF 大包与主应用 chunk 分离；
- Nginx 对哈希静态资源设置一年期 immutable 缓存；
- 实验、日志和事件列表支持分页参数；
- 关系集合使用 `selectinload`，减少列表场景 N+1 查询。

`ExperimentDetail.vue` 和 `EventsTimeline.vue` 仍然较大，继续拆分为功能组件与 composable 是维护性工作，不应被视为已完成。

## 13. 部署流程

`./deploy.sh` 的顺序是：

1. 从模板生成或补齐强随机密钥；
2. 构建 Vue 静态文件；
3. 清理 macOS AppleDouble 构建元数据；
4. 对现有数据库创建部署前加密快照；
5. 构建非 root `mux-app` 镜像；
6. 启动并等待 PostgreSQL 健康；
7. 配置最小权限数据库角色；
8. 运行一次性 Alembic migrator；
9. 启动/重建 `mux-app` 与 `mux-scheduler`。

`.env.prod.example` 不提供可工作的生产密码。关键环境变量：

```text
DB_USER / DB_PASSWORD             owner，仅数据库和 migrator
APP_DB_USER / APP_DB_PASSWORD     日常 CRUD
BACKUP_DB_USER / BACKUP_DB_PASSWORD
SECRET_KEY
BACKUP_ENCRYPTION_KEY
APP_BIND_ADDRESS / APP_PORT
COOKIE_SECURE / CORS_ORIGINS
GUNICORN_WORKERS
```

本地 HTTP 开发可使用 `COOKIE_SECURE=false` 且仅绑定 loopback；非本机绑定时部署脚本要求启用 Secure Cookie。生产必须配套可信 HTTPS 终止。

## 14. 开发启动

生产 Compose 负责完整应用栈。需要单独调试前后端时：

```bash
# 数据库与现有服务
docker compose --env-file .env.prod up -d

# 前端开发服务器
npm --prefix client run dev

# 后端依赖和启动方式按 server/requirements.txt 配置
cd server
uvicorn main:app --reload
```

前端开发地址默认 `http://localhost:5173`，FastAPI 默认 `http://127.0.0.1:8000`。开发环境需提供可用 `DATABASE_URL` 与匹配的 CORS 来源。

## 15. 当前已知边界

- `attachments` 表已成为安全访问依据，但旧 JSON 附件字段尚未完全移除；
- 上传内容采用有限 magic-byte 识别，Office Open XML 尚未深入校验 ZIP 内部结构；
- 备份保存在宿主挂载目录，尚未自动复制到独立存储；
- 数据库恢复是明确的离线运维流程，尚未提供原子切换或自动恢复演练；
- 超大 Vue 页面仍需继续组件化；
- CSP 为兼容现有页面仍包含 `unsafe-inline` 与 `unsafe-eval`，后续应配合前端重构收紧。
