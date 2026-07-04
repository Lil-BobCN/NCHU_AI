# Java 后端调用 Python RAG 接口文档

版本：V1.2  
日期：2026-07-04  
适用项目：`rag_java`

> 如果 Java 需要按业务场景照着接，优先看 [Java对接调用流程详版.md](Java对接调用流程详版.md)。本文主要作为接口字段契约速查。

## 0. 2026-07-04 联调更新

本次按 Java 提供的《Python RAG 服务接口鉴权统一方案》完成以下调整：

- `/internal/rag/*` 鉴权统一改为 Java Sa-Token JWT：

```http
Authorization: Bearer <Java Sa-Token JWT>
```

- Python 不再要求 Java 传 `X-RAG-Service-Token`。旧 Service Token 函数保留在代码中，但 internal 路由已不再使用。
- Python 远程部署不再启动独立 PostgreSQL，`DATABASE_URL` 必须指向 Java 服务器现有 PostgreSQL。
- `POST /documents/process`、`/reparse`、`/rechunk` 返回的 `job_id` 已改为 `document_jobs.id`，Java 可以直接轮询 `/jobs/{job_id}`。
- 已补齐 Java 当前调用需要的文档状态与会话接口：

```text
GET    /internal/rag/documents/{attach_id}
POST   /internal/rag/conversations
GET    /internal/rag/conversations
GET    /internal/rag/conversations/{conversation_id}/messages
PATCH  /internal/rag/conversations/{conversation_id}
DELETE /internal/rag/conversations/{conversation_id}
```

下方历史章节中如仍出现 `X-RAG-Service-Token` 示例，以本节为准。

## 1. 总体说明

本项目是给 Java 后台调用的 Python RAG 内部服务。

调用链路：

```text
前端 -> Java 后台 -> Python RAG
```

Java 负责：

- 登录、鉴权、用户、角色、部门、菜单权限。
- 知识库、文档、会话、消息、反馈等业务 CRUD。
- 计算当前用户允许检索的部门、知识库、文档范围。
- 调用 Python RAG 内部接口，并把结果保存到 Java 业务表。

Python RAG 负责：

- 文档解析、切片、向量化。
- 向量召回、关键词召回、QA 召回、rerank。
- 多轮问题改写、答案生成、引用来源、RAG 日志。
- 按 Java 传入的权限范围过滤可召回文档。

Java 不应该直接调用原系统的管理接口。当前对 Java 稳定开放的接口前缀是：

```text
/internal/rag
```

### 1.1 当前远程部署信息

当前远程已部署一套独立 Python RAG internal 服务，没有覆盖服务器上已有旧 `rag-school` 服务。

| 项目 | 当前值 |
| --- | --- |
| 部署目录 | `/app/rag-java-internal` |
| 后端容器 | `rag_java2_backend` |
| Worker 容器 | `rag_java2_worker` |
| Java 同服务器调用地址 | `http://127.0.0.1:18020/internal/rag` |
| 外部机器调用地址 | `http://47.100.216.222:18020/internal/rag` |
| 服务 Token 存放位置 | `/app/rag-java-internal/.env` 的 `RAG_SERVICE_TOKEN` |
| 部署说明 | [部署运维文档.md](部署运维文档.md) |

注意：

- 当前服务器本机访问已验证通过。
- 如果 Java 不在同一台服务器，需要在阿里云安全组放行 TCP `18020`。
- 当前部署为轻量版，`OCR_ENABLED=false`，未启用 PaddleOCR；普通文本型 PDF、Word、Excel、TXT、Markdown 等能力保留，扫描件/图片 OCR 暂不保证。

## 2. 服务鉴权

所有 `/internal/rag/*` 接口都必须带内部服务 Token：

```http
X-RAG-Service-Token: <RAG_SERVICE_TOKEN>
X-Request-Id: <trace id，可选但建议传>
```

Python 配置项：

```env
RAG_SERVICE_TOKEN=双方约定的强随机字符串
```

如果未配置或仍为默认值 `change-me`，Python 会返回：

```json
{
  "detail": "RAG 服务 Token 未配置"
}
```

建议：

- 该 Token 只在 Java 后端和 Python RAG 服务之间使用。
- 不允许暴露到浏览器、前端代码、接口文档截图。
- 生产环境通过环境变量或容器 secret 注入。
- 当前远程部署的 Token 请从 `/app/rag-java-internal/.env` 读取，不要写死在前端或提交到代码仓库。

## 3. 通用响应格式

普通 JSON 接口统一返回：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

常见错误：

| HTTP 状态 | 场景 |
| --- | --- |
| 401 | `X-RAG-Service-Token` 缺失或错误 |
| 403 | 权限范围为空、当前用户无可检索资料 |
| 404 | 文档或任务不存在 |
| 415 | 不支持的文档类型 |
| 422 | 请求参数格式错误 |
| 503 | Python 未配置 `RAG_SERVICE_TOKEN` |

## 4. 权限模型

Python 不解析 Java 的 Sa-Token，也不判断用户属于哪个部门。

正确流程是：

```text
Java 校验登录用户
Java 查询用户、角色、部门、数据权限
Java 计算本次允许检索范围 access_scope
Java 调 Python RAG
Python 只在 access_scope 内召回文档
```

### 4.1 文档发布时的权限字段

Java 调文档处理接口时，需要传：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `attach_id` | 是 | Java 附件 ID，Python 用它和 RAG 文档绑定 |
| `knowledge_id` | 是 | Java 知识库 ID |
| `publish_dept_id` | 建议必填 | 文档发布部门 ID，用于部门权限过滤 |
| `owner_user_id` | 否 | 创建人或归属人 ID |
| `visible_in_chat` | 否 | 是否允许进入问答检索，默认 `true` |
| `publish_scope` | 是 | 文档可见范围：`public`、`dept`、`private`、`custom` |
| `allowed_dept_ids` | 视场景 | `custom` 场景允许访问的部门 ID |
| `allowed_user_ids` | 视场景 | `custom` 场景允许访问的用户 ID |

### 4.2 问答时的权限字段

Java 每次问答都需要传 `user_context` 和 `access_scope`。

示例：

```json
{
  "user_context": {
    "user_id": "1001",
    "dept_id": "finance",
    "role_codes": ["dept_admin"],
    "data_scope": "dept"
  },
  "access_scope": {
    "scope_mode": "dept",
    "allowed_dept_ids": ["finance"],
    "allowed_knowledge_ids": [],
    "allowed_attach_ids": [],
    "deny_attach_ids": []
  }
}
```

### 4.3 `scope_mode` 说明

| 值 | 当前含义 | 使用建议 |
| --- | --- | --- |
| `dept` | 按 `allowed_dept_ids` 过滤 `documents.publish_dept_id` | 普通部门用户推荐使用 |
| `custom` | 可同时按部门、知识库、文档 ID 过滤 | 精细权限时使用 |
| `admin_all` | 不按部门过滤，只叠加知识库/文档黑白名单 | 只能由 Java 确认管理员后传 |
| `all_public` | 只检索 `publish_scope=public` 的公开资料 | 公开资料入口使用 |

重要：

- 普通用户不要传 `admin_all`。
- 如果使用 `dept`，`allowed_dept_ids` 不能为空。
- 如果使用 `custom`，`allowed_dept_ids`、`allowed_knowledge_ids`、`allowed_attach_ids` 至少一个不能为空。
- Python 检索前会把可访问文档查出来，并只把这些文档 ID 传给原 RAG 召回逻辑。

文档可见范围规则：

| `publish_scope` | Python 判断规则 |
| --- | --- |
| `public` | 所有人可检索 |
| `dept` | 当前用户的 `allowed_dept_ids` 命中文档 `publish_dept_id` 或文档 `allowed_dept_ids` |
| `private` | 当前 `user_id` 等于文档 `owner_user_id` |
| `custom` | 命中 `owner_user_id`、`allowed_user_ids`、`allowed_dept_ids` 或 Java 明确传入的 `allowed_attach_ids` |

## 5. 多轮对话机制

多轮上下文由 `session_id` 控制。

```text
Java session_id -> Python conversation_id -> 读取历史消息 -> 多轮改写/回答
```

规则：

- 同一条对话的每次提问，Java 必须传同一个 `session_id`。
- 新建对话时，Java 生成新的 `session_id`。
- 切换历史对话时，Java 传对应历史会话的 `session_id`。
- 不同用户、不同会话不能复用同一个 `session_id`。
- 如果不传 `session_id`，Python 会按新会话处理，多轮效果会丢失。

推荐：

```text
session_id = Java chat_session.id
```

如果 Java 的 `session_id` 不是 UUID，Python 会用 UUID5 稳定转换成内部 UUID。

## 6. 接口清单

| 方法 | 地址 | 说明 |
| --- | --- | --- |
| GET | `/internal/rag/health` | RAG 服务健康检查 |
| POST | `/internal/rag/documents/process` | 创建或更新 RAG 文档，并可自动解析切片向量化 |
| POST | `/internal/rag/documents/{attach_id}/reparse` | 重新解析文档 |
| POST | `/internal/rag/documents/{attach_id}/rechunk` | 重新切片并向量化 |
| DELETE | `/internal/rag/documents/{attach_id}` | 删除 RAG 索引和相关数据 |
| GET | `/internal/rag/jobs/{job_id}` | 查询后台任务状态 |
| POST | `/internal/rag/chat/stream` | 流式问答，Java 转发 SSE 给前端 |
| POST | `/internal/rag/chat` | 非流式问答 |

当前尚未作为 `/internal/rag/*` 稳定接口开放：

| 接口 | 当前状态 |
| --- | --- |
| `/internal/rag/retrieval/search` | 文档设计中有说明，当前部署未开放 |
| `/internal/rag/feedback/sync` | 文档设计中有说明，当前部署未开放 |
| `/internal/rag/statistics/*` | 文档设计中有说明，当前部署未开放 |

## 7. 健康检查

```http
GET /internal/rag/health
X-RAG-Service-Token: <token>
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "status": "ok",
    "name": "Java Internal RAG Service"
  }
}
```

当前远程验证命令：

```bash
python3 /app/rag-java-internal/deploy/remote_health_check.py
```

Readiness 检查：

```http
GET http://127.0.0.1:18020/api/v1/readiness
```

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "api": "ok",
    "postgres": "ok",
    "redis": "ok",
    "minio": "ok"
  }
}
```

## 8. 文档处理

### 8.1 创建或更新 RAG 文档

Java 在完成文件上传和附件业务记录保存后调用。

```http
POST /internal/rag/documents/process
Content-Type: application/json
X-RAG-Service-Token: <token>
```

请求体：

```json
{
  "attach_id": 101,
  "knowledge_id": "kb_student",
  "doc_id": "java-doc-001",
  "publish_dept_id": "finance",
  "owner_user_id": "1001",
  "visible_in_chat": true,
  "publish_scope": "dept",
  "allowed_dept_ids": [],
  "allowed_user_ids": [],
  "file_name": "高校学生问题清单及归口部门.docx",
  "file_ext": ".docx",
  "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "file_size": 31245,
  "file_hash": "sha256-or-md5",
  "bucket": "rag-documents",
  "object_key": "java/2026/07/01/xxx.docx",
  "operator_id": "1001",
  "auto_process": true,
  "force": false
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `attach_id` | number | 是 | Java 附件 ID，唯一 |
| `knowledge_id` | string | 是 | Java 知识库 ID，写入 `documents.knowledge_base` |
| `doc_id` | string | 否 | Java 文档业务 ID |
| `publish_dept_id` | string | 建议必填 | 发布部门 |
| `owner_user_id` | string | 否 | 文档归属人 |
| `visible_in_chat` | boolean | 否 | 是否进入问答检索 |
| `publish_scope` | string | 否 | 可见范围，默认 `dept`；可选 `public`、`dept`、`private`、`custom` |
| `allowed_dept_ids` | string[] | 否 | 自定义可访问部门 |
| `allowed_user_ids` | string[] | 否 | 自定义可访问人员 |
| `file_name` | string | 是 | 原始文件名 |
| `file_ext` | string | 否 | 文件扩展名，不传则从文件名推断 |
| `mime_type` | string | 否 | 文件 MIME |
| `file_size` | number | 是 | 文件大小，单位字节 |
| `file_hash` | string | 是 | 文件哈希 |
| `bucket` | string | 是 | MinIO bucket |
| `object_key` | string | 是 | MinIO object key |
| `operator_id` | string | 否 | 操作人 |
| `auto_process` | boolean | 否 | 是否自动入队解析、切片、向量化，默认 `true` |
| `force` | boolean | 否 | 当前代码保留字段，暂未实际使用 |

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "attach_id": 101,
    "rag_doc_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "status": "uploaded",
    "jobs": [
      {
        "job_id": "8d58904f-2f35-45f5-b301-777777777777",
        "status": "queued"
      }
    ]
  }
}
```

处理说明：

- 如果 `attach_id` 已存在，Python 会更新该 RAG 文档记录。
- 如果 `auto_process=true`，Python 会创建后台任务执行完整流水线。
- 完整流水线包括解析、切片、embedding、索引入库。
- Java 后台应保存 `rag_doc_id` 和任务 ID，便于后续查询。

当前部署注意：

- 当前代码中 `/documents/process`、`/reparse`、`/rechunk` 返回的 `job_id` 是 Redis 队列任务 ID。
- `/internal/rag/jobs/{job_id}` 当前查询的是数据库 `document_jobs.id`。
- 因此 Java 联调前建议先修复该契约，否则 Java 用返回的 `job_id` 直接轮询可能得到 `404 任务不存在`。
- 建议修复方向：入队前先创建数据库 `document_jobs` 记录，接口返回数据库 job id，Redis task payload 携带同一个 job id，worker 更新同一条 job。
- 在修复前，Java 可以先完成健康检查、文档元数据同步和问答接口联通；文档处理进度轮询不要作为验收阻塞项。

### 8.2 重新解析

```http
POST /internal/rag/documents/{attach_id}/reparse
```

请求体：

```json
{
  "operator_id": "1001",
  "force": true
}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "attach_id": 101,
    "rag_doc_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "job_id": "8d58904f-2f35-45f5-b301-777777777777",
    "status": "queued"
  }
}
```

### 8.3 重新切片

```http
POST /internal/rag/documents/{attach_id}/rechunk
```

请求体：

```json
{
  "operator_id": "1001",
  "chunk_config": {}
}
```

说明：

- 当前 `chunk_config` 是保留字段。
- 当前代码仍使用 Python 环境变量中的切片配置。

### 8.4 删除 RAG 索引

```http
DELETE /internal/rag/documents/{attach_id}
```

请求体：

```json
{
  "operator_id": "1001",
  "reason": "document_deleted"
}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "attach_id": 101,
    "rag_doc_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "status": "deleted"
  }
}
```

说明：

- Java 删除、禁用、取消发布文档后，应调用该接口。
- Python 会软删除 RAG 文档，并清理召回相关数据。
- 这样可以避免已删除文档继续被召回。

## 9. 任务查询

```http
GET /internal/rag/jobs/{job_id}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "job_id": "8d58904f-2f35-45f5-b301-777777777777",
    "rag_doc_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "job_type": "document_full_pipeline",
    "status": "running",
    "progress": 60,
    "message": "已向量化 10/20",
    "error_message": null,
    "result": {}
  }
}
```

任务状态：

| 状态 | 说明 |
| --- | --- |
| `pending` | 已创建，待执行 |
| `running` | 执行中 |
| `succeeded` | 成功 |
| `failed` | 失败 |
| `skipped` | 跳过 |

## 10. 流式问答

前端如果需要打字机效果，推荐：

```text
前端请求 Java SSE -> Java 调 Python SSE -> Java 转发给前端
```

```http
POST /internal/rag/chat/stream
Content-Type: application/json
Accept: text/event-stream
X-RAG-Service-Token: <token>
```

请求体：

```json
{
  "session_id": "java-chat-session-001",
  "message_id": "java-user-message-001",
  "question": "票据管理与报销类归口哪个部门？",
  "user_context": {
    "user_id": "1001",
    "dept_id": "finance",
    "role_codes": ["student"],
    "data_scope": "dept"
  },
  "access_scope": {
    "scope_mode": "dept",
    "allowed_dept_ids": ["finance"],
    "allowed_knowledge_ids": [],
    "allowed_attach_ids": [],
    "deny_attach_ids": []
  },
  "options": {
    "top_k": 8,
    "rerank_top_k": 5,
    "enable_rewrite": true,
    "enable_suggested_questions": true
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `session_id` | string | 强烈建议 | Java 会话 ID，控制多轮上下文 |
| `message_id` | string | 否 | Java 用户消息 ID，当前为透传保留字段 |
| `question` | string | 是 | 用户问题 |
| `user_context.user_id` | string | 是 | 当前用户 ID |
| `user_context.dept_id` | string | 否 | 当前用户部门 |
| `access_scope` | object | 是 | Java 计算后的检索权限范围 |
| `options.top_k` | number | 否 | 每路召回数量，默认 8，最大 50 |
| `options.rerank_top_k` | number | 否 | 最终上下文数量，默认 5，最大 20 |
| `options.enable_rewrite` | boolean | 否 | 是否启用多轮问题改写 |
| `options.enable_suggested_questions` | boolean | 否 | 是否生成推荐追问 |

SSE 事件示例：

```text
event: message_start
data: {"conversation_id":"...","user_message_id":"...","assistant_message_id":"...","history_count":2}

event: retrieval_start
data: {"query":"票据管理与报销类归口哪个部门？","uses_history":false}

event: retrieval_done
data: {"recall_count":15,"rerank_count":5,"citation_count":2}

event: delta
data: {"text":"票据管理与报销类一般归口..."}

event: message_end
data: {"answer":"...","citations":[...],"suggested_questions":[...]}
```

Java 处理要求：

1. Java 先保存用户消息。
2. Java 调 Python SSE。
3. Java 将 `delta` 转发给前端。
4. Java 在 `message_end` 后保存 AI 完整答案、引用来源、推荐问题。
5. Java 保存 Python 返回的 `conversation_id`、`assistant_message_id`、`retrieval_log_id` 等调试字段。

## 11. 非流式问答

```http
POST /internal/rag/chat
```

请求体同流式问答。

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "answer": "票据管理与报销类问题一般归口资金结算科/会计核算科。",
    "citations": [
      {
        "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
        "document_title": "高校学生问题清单及归口部门.docx",
        "document_name": "高校学生问题清单及归口部门.docx",
        "chunk_id": "d50fb469-05a8-4ad0-a53d-222222222222",
        "page_start": null,
        "page_end": null,
        "section_path": "表格 4",
        "url": "http://..."
      }
    ],
    "suggested_questions": []
  }
}
```

说明：

- 非流式接口内部复用同一套 RAG 逻辑。
- 如果前端需要实时打字机效果，优先使用流式接口。

## 12. Java 推荐接入流程

### 12.1 文档发布流程

```text
Java 上传文件到 MinIO
Java 写入 knowledge_attach
Java 计算/写入 publish_dept_id、knowledge_id、visible_in_chat
Java 调 POST /internal/rag/documents/process
Python 入队解析、切片、向量化
Java 轮询 GET /internal/rag/jobs/{job_id}
Java 更新 knowledge_attach 的 RAG 状态字段
```

### 12.2 文档删除流程

```text
Java 校验管理员权限
Java 软删或禁用 knowledge_attach
Java 调 DELETE /internal/rag/documents/{attach_id}
Python 删除该文档的 RAG 索引数据
Java 更新业务状态
```

### 12.3 用户问答流程

```text
前端发问题给 Java
Java 校验登录态
Java 创建或读取 chat_session
Java 保存用户消息
Java 根据用户、角色、部门计算 access_scope
Java 调 POST /internal/rag/chat/stream
Python 根据 access_scope 找可检索文档
Python 执行原 RAG 召回、rerank、多轮改写、答案生成
Java 转发 SSE 给前端
Java 保存 AI 消息、引用来源、retrieval trace
```

## 13. 当前已实现和待完善点

### 已实现

- 内部服务 Token 鉴权。
- Java 附件 ID 和 Python RAG 文档绑定。
- 文档处理、重新解析、重新切片、删除索引。
- 按部门、知识库、文档 ID 过滤可召回文档。
- 多轮会话由 `session_id` 隔离。
- 原 RAG 召回、rerank、问答、多轮问题改写逻辑完整保留。
- 当前远程轻量版服务已部署并通过 `/internal/rag/health`、`/api/v1/readiness` 验证。

### 联调前建议完善

| 项目 | 说明 | 建议 |
| --- | --- | --- |
| `job_id` 契约 | 当前接口返回 Redis task id，但 `/jobs/{job_id}` 查询数据库 job id | Java 文档处理联调前优先修复 |
| Java 权限字段 | 已支持 `publish_scope`、`allowed_dept_ids`、`allowed_user_ids` | Java 上传/发布文档时必须正确传值 |
| `force` 字段 | 文档处理接口保留字段，当前未实际控制覆盖逻辑 | 如 Java 有强制重建需求，补充实现 |
| `chunk_config` 字段 | 重新切片接口保留字段，当前未覆盖环境配置 | 如需按文档自定义切片，补充实现 |
| Java 消息 ID | `message_id` 当前未写入 Python 消息表 | 如需精确对账，建议增加 `java_message_id` 字段 |
| 表名前缀 | 当前表名沿用原项目，如 `documents` | 与 Java 共库时建议独立 schema 或统一 `rag_` 前缀 |
| 状态回写 | Python 目前只返回任务状态，不主动回写 Java 表 | Java 可轮询任务，也可后续增加回调接口 |
| OCR 能力 | 当前远程部署 `OCR_ENABLED=false` | 扫描件/图片 OCR 需后续完整镜像部署 |

## 14. Java 最小调用示例

```bash
curl -X POST "http://127.0.0.1:18020/internal/rag/chat" \
  -H "Content-Type: application/json" \
  -H "X-RAG-Service-Token: ${RAG_SERVICE_TOKEN}" \
  -d '{
    "session_id": "chat-10001",
    "question": "票据管理与报销类归口哪个部门？",
    "user_context": {
      "user_id": "1001",
      "dept_id": "finance",
      "role_codes": ["student"]
    },
    "access_scope": {
      "scope_mode": "dept",
      "allowed_dept_ids": ["finance"],
      "allowed_knowledge_ids": [],
      "allowed_attach_ids": [],
      "deny_attach_ids": []
    },
    "options": {
      "top_k": 8,
      "rerank_top_k": 5,
      "enable_rewrite": true
    }
  }'
```
