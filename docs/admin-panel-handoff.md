# 管理端开发交接说明

版本: v0.2  
日期: 2026-06-01  
交接对象: 管理端开发  
开发基线: `main`  
状态: 会议前交接稿

## 1. 交接结论

| 项目 | 结论 |
| --- | --- |
| 使用分支 | `main` |
| 接入方式 | 管理端调用 FastAPI API |
| API Base URL | `http://localhost:8000/api/v1` |
| 正式业务 SQL | 暂无 |
| 当前业务数据 | in-memory Demo，服务重启后不作为正式业务数据保留 |
| 本地技术底座 | FastAPI、PostgreSQL、Redis、MinIO、Milvus |
| 第一版管理端范围 | 登录、统计、知识库 CRUD、审计日志 |
| 第一版不做 | 文档上传解析、向量索引、真实 SSO、真实学生数据、正式 PostgreSQL 业务表 |

当前可以先做 API 联调和页面开发。是否提前做 PostgreSQL 业务表、migration、seed SQL，需要会议确认后再进入。

## 2. 交接状态

| 项 | 状态 | 说明 |
| --- | --- | --- |
| 分支确认 | 已确认 | `main` |
| 本地运行说明 | 已提供 | 见第 3 节 |
| 登录方式 | 已提供 | Demo local login |
| token 传递方式 | 已提供 | `Authorization: Bearer <token>` |
| 管理端 API | 已提供 | 见第 6 节 |
| 字段字典 | 已提供 | 见第 7 节 |
| mock 数据 | 已提供 | 见第 8 节 |
| 正式业务 SQL | 未提供 | 当前阶段没有正式业务表 |
| 远程数据库 | 未提供 | 需要私有网络、凭据和安全边界确认 |
| 文档解析/RAG 入库 | 未实现 | 后续阶段单独确认 |

## 3. 本地启动

从仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

cd backend
docker compose -f docker-compose.phase1.yml up -d
```

健康检查：

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod http://localhost:8000/api/v1/readiness
```

本地服务：

| 服务 | 地址 | 用途 |
| --- | --- | --- |
| FastAPI | `http://localhost:8000` | 后端 API |
| PostgreSQL | `localhost:5432` | 技术底座，暂无正式业务表 |
| Redis | `localhost:6379` | 缓存/session/task state 基础 |
| MinIO | `localhost:9000` / `localhost:9001` | 原始文档对象存储基础 |
| Milvus | `localhost:19530` | 向量库基础 |

本地 PostgreSQL 默认连接信息：

```text
host: localhost
port: 5432
database: counselor_db
user: counselor
password: counselor_pass
```

不要把数据库账号密码写入前端代码。管理端前端应通过 API 访问数据。

## 4. 登录和鉴权

Demo 账号：

| 角色 | 账号 | 密码 |
| --- | --- | --- |
| 管理员 | `admin@example.edu` | `password` |
| 学生 | `student@example.edu` | `password` |
| 辅导员 | `counselor@example.edu` | `password` |

登录：

```http
POST /api/v1/auth/login
```

请求：

```json
{
  "username": "admin@example.edu",
  "password": "password"
}
```

返回：

```json
{
  "access_token": "phase1-<generated-token>",
  "token_type": "bearer",
  "provider": "local",
  "issued_at": "2026-06-01T00:00:00Z",
  "user": {
    "id": "admin-1",
    "displayName": "Demo Admin",
    "role": "admin",
    "demoAccount": true,
    "sessionState": "authenticated"
  }
}
```

后续请求头：

```http
Authorization: Bearer <access_token>
```

Demo 阶段 token 可先存 `sessionStorage` 或 `localStorage`。生产阶段的 SSO、session、httpOnly cookie 等策略另行确认。

## 5. 管理端第一版范围

| 页面 | 状态 | API |
| --- | --- | --- |
| 登录页 | 做 | `POST /auth/login` |
| 管理首页统计 | 做 | `GET /admin/stats` |
| 知识库列表 | 做 | `GET /admin/knowledge` |
| 新增知识 | 做 | `POST /admin/knowledge` |
| 编辑知识 | 做 | `PUT /admin/knowledge/{knowledge_id}` |
| 删除知识 | 做 | `DELETE /admin/knowledge/{knowledge_id}` |
| 审计日志 | 做 | `GET /admin/audit` |
| 会话只读查看 | 后续扩展 | 当前接口在 `/student/conversations` |
| 辅导员辅助 | 后续扩展 | `POST /counselor/assistance` |
| 文档上传解析 | 不做 | 后续 ingestion/RAG |
| 向量索引状态 | 不做 | 后续 Milvus/RAG |
| 用户管理 | 不做正式版 | 等 SSO 和权限策略 |

## 6. API Reference

### 6.1 Auth

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/login` | 无 | Demo 登录 |
| `GET` | `/api/v1/auth/me` | Bearer token | 当前用户信息 |
| `POST` | `/api/v1/auth/sso/callback` | 无 | SSO 边界，当前返回未实现 |

常见错误：

| 状态码 | 场景 |
| --- | --- |
| `401` | 用户名或密码错误；缺少/无效 token |
| `501` | SSO 当前阶段未启用 |

### 6.2 Admin

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/admin/knowledge` | admin | 知识库列表 |
| `POST` | `/api/v1/admin/knowledge` | admin | 新增知识 |
| `PUT` | `/api/v1/admin/knowledge/{knowledge_id}` | admin | 替换知识 |
| `DELETE` | `/api/v1/admin/knowledge/{knowledge_id}` | admin | 删除知识 |
| `GET` | `/api/v1/admin/audit` | admin | 审计事件 |
| `GET` | `/api/v1/admin/stats` | admin | 基础统计 |

常见错误：

| 状态码 | 场景 |
| --- | --- |
| `401` | 未登录或 token 无效 |
| `403` | 当前用户不是 admin |
| `404` | 知识条目不存在 |

### 6.3 Knowledge 请求体

`POST /admin/knowledge` 和 `PUT /admin/knowledge/{knowledge_id}` 使用同一结构：

```json
{
  "title": "校园心理咨询预约说明",
  "content": "学生可通过学校心理咨询中心预约系统进行预约。该条目仅用于 Demo 联调。",
  "category": "services",
  "tags": ["心理咨询", "预约", "Demo"],
  "status": "published"
}
```

字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `title` | string | 是 | 标题 |
| `content` | string | 是 | 内容 |
| `category` | string | 否 | 分类，默认 `general` |
| `tags` | string[] | 否 | 标签 |
| `status` | string | 否 | `draft` 或 `published` |

返回：

```json
{
  "id": "knowledge-<id>",
  "title": "校园心理咨询预约说明",
  "content": "学生可通过学校心理咨询中心预约系统进行预约。该条目仅用于 Demo 联调。",
  "category": "services",
  "tags": ["心理咨询", "预约", "Demo"],
  "status": "published",
  "updated_by": "admin-1",
  "created_at": "2026-06-01T00:00:00Z",
  "updated_at": "2026-06-01T00:00:00Z"
}
```

### 6.4 Stats 返回

```json
{
  "users": 3,
  "knowledge_items": 2,
  "published_knowledge_items": 2,
  "conversations": 0,
  "messages": 0,
  "audit_events": 1
}
```

### 6.5 Audit 返回

```json
{
  "id": "audit-<id>",
  "actorId": "admin-1",
  "actorRole": "admin",
  "action": "knowledge.create",
  "targetType": "knowledge",
  "targetId": "knowledge-<id>",
  "result": "success",
  "eventTags": ["demo", "role:admin", "result:success", "resource:knowledge"],
  "counterKey": "knowledge.write.count",
  "createdAt": "2026-06-01T00:00:00Z"
}
```

审计事件只记录结构化标签和计数键，不记录完整对话正文、用户输入原文、模型输出全文或敏感内容。

## 7. 字段字典

### 7.1 User

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 用户 ID |
| `displayName` | string | 展示名 |
| `role` | string | `student`、`counselor`、`admin` |
| `demoAccount` | boolean | 是否 Demo 账号 |
| `sessionState` | string | 会话状态 |

### 7.2 Knowledge

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 知识条目 ID |
| `title` | string | 标题 |
| `content` | string | 内容 |
| `category` | string | 分类 |
| `tags` | string[] | 标签 |
| `status` | string | `draft` 或 `published` |
| `updated_by` | string | 最近更新人 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### 7.3 AuditEvent

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 审计事件 ID |
| `actorId` | string | 操作人 ID |
| `actorRole` | string | 操作人角色 |
| `action` | string | 操作类型 |
| `targetType` | string | 目标类型 |
| `targetId` | string | 目标 ID |
| `result` | string | `success`、`failure`、`denied` |
| `eventTags` | string[] | 结构化标签 |
| `counterKey` | string | 统计计数键 |
| `createdAt` | datetime | 事件时间 |

## 8. 快速联调

登录并保存 token：

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/auth/login `
  -ContentType "application/json" `
  -Body '{"username":"admin@example.edu","password":"password"}'

$headers = @{ Authorization = "Bearer $($login.access_token)" }
```

读取当前用户：

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8000/api/v1/auth/me -Headers $headers
```

读取统计：

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8000/api/v1/admin/stats -Headers $headers
```

读取知识库：

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8000/api/v1/admin/knowledge -Headers $headers
```

新增知识：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/admin/knowledge `
  -Headers $headers `
  -ContentType "application/json" `
  -Body '{"title":"校园心理咨询预约说明","content":"学生可通过学校心理咨询中心预约系统进行预约。该条目仅用于 Demo 联调。","category":"services","tags":["心理咨询","预约","Demo"],"status":"published"}'
```

读取审计：

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8000/api/v1/admin/audit -Headers $headers
```

## 9. 数据和存储边界

当前没有正式业务 SQL dump。

原因：

| 项 | 说明 |
| --- | --- |
| PostgreSQL | 当前用于技术 Phase 1 底座和 smoke gate |
| 业务数据 | 当前在 in-memory Demo store |
| 正式 schema | Phase 6 再确认 |
| 持久化审计 | Phase 6 再确认 |
| RAG/vector/source citation | Phase 7 再确认 |

推荐接入路径：

```text
管理端 UI -> FastAPI API -> 后端权限校验 -> 当前 in-memory Demo / 未来 PostgreSQL
```

不推荐：

```text
管理端前端 -> 直接连接 PostgreSQL
```

如需远程共享数据库或远程共享 API 地址，需要先确认：

- 私有网络访问方式；
- 凭据发放方式；
- 默认密码替换；
- CORS 和来源白名单；
- 是否允许外部机器访问本地服务；
- 是否需要审计远程访问。

## 10. 文档解析和 RAG 后续链路

当前没有完整的文档解析和 RAG 入库。

后续目标链路：

```text
1. 管理端上传文档
2. 原始文件存 MinIO
3. PostgreSQL 存文档元数据、上传人、状态、时间
4. 后端解析文档生成 chunks
5. embedding 服务生成向量
6. Milvus 存 chunk embedding
7. PostgreSQL 记录 document/chunk/vector 关联
8. 问答时检索 Milvus，再回查文档来源
9. 管理端展示上传状态、解析状态、索引状态、失败原因
```

这条链路需要单独确认数据表、任务队列、失败重试、审计策略和真实资料边界。

## 11. 待会议确认

| 问题 | 为什么要确认 |
| --- | --- |
| 管理端是否是当前正式任务 | 决定是否提前投入后端持久化 |
| 管理端只做前端还是也做后台服务 | 决定交接 API 还是交接数据库 |
| 是否批准 PostgreSQL 业务 schema | 决定是否进入 Phase 6 |
| 是否需要 seed SQL | 决定是否提供临时 mock 表 |
| 真实知识库资料由谁提供 | 决定 RAG 入库排期 |
| 文档解析、清洗、入库由谁负责 | 决定后续任务 owner |
| SSO 是否进入当前阶段 | 决定是否继续使用 Demo login |
| 第一版是否只做登录、统计、知识库、审计 | 防止管理端范围失控 |

## 12. 接收方验收清单

管理端开发者拿到本文档后，应能确认：

| 检查项 | 通过标准 |
| --- | --- |
| 分支 | 知道使用 `main` |
| 启动 | 能启动后端和本地依赖 |
| 登录 | 能用 Demo 管理员账号拿到 token |
| 鉴权 | 知道后续请求如何带 bearer token |
| 知识库 | 能完成列表、新增、编辑、删除的页面设计和接口联调 |
| 统计 | 能读取管理端首页统计 |
| 审计 | 能读取操作日志 |
| 数据边界 | 知道当前没有正式业务 SQL |
| 范围边界 | 知道文档解析、RAG、SSO、正式 DB 不在第一版 |
| 待确认事项 | 知道会议要拍板哪些问题 |

## 13. 给管理端开发者的说明

```text
现在以 main 分支为准。

当前后端有本地 Docker 技术底座，包括 FastAPI、PostgreSQL、Redis、MinIO、Milvus，但业务数据还没有正式落 PostgreSQL。目前业务接口是 in-memory Demo，所以没有正式业务 SQL 可以导出。

管理端第一版先按 FastAPI API 和 mock 数据开发，范围是登录、管理首页统计、知识库管理、审计日志。文档上传解析、向量索引、真实 SSO、真实学生数据和正式 PostgreSQL 业务表暂时不在第一版范围内。

如果会议确认管理端必须基于数据库持久化开发，再补 PostgreSQL schema、migration 和 seed SQL。
```

## 14. 资料位置

| 内容 | 路径 |
| --- | --- |
| 后端入口 | `backend/app/main.py` |
| API 路由 | `backend/app/api/v1/` |
| 业务 schema | `backend/app/schemas/business.py` |
| 当前 in-memory store | `backend/app/services/business.py` |
| Docker 启动 | `backend/docker-compose.phase1.yml` |
| 环境变量模板 | `backend/.env.example` |
| 数据契约决策 | `.omx/decisions/SDAR-0006-product-data-contract-boundary.md` |
| 项目状态 | `PROJECT_STATE.md` |
| 项目启动说明 | `README.md` |

## 15. 参考模板结构

本交接文档采用了以下公开模板的结构思路：

- 项目交接模板常见字段：状态、范围、交付物、风险、约束、待办和接收方清单。
- 开发者文档结构：把 setup guide、API reference、concept/boundary 分开，避免混在一篇长叙述里。
- API 文档结构：每个接口说明 method、path、auth、request、response、error 和示例。

参考来源：

- Smartsheet: https://www.smartsheet.com/content/project-handover-templates
- CodeDashboard: https://www.codedashboard.dev/templates/software-handover-document
- Document360: https://document360.com/blog/developer-documentation-templates/
- Cavaro: https://www.cavaro.io/templates/api-specification-document
