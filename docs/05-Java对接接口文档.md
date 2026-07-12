# Java 对接接口文档

## 一、基础约定

服务前缀：

```text
/internal/rag
```

所有 Java 内部接口都需要：

```http
Authorization: Bearer <Java Sa-Token JWT>
X-Request-Id: <trace id，可选但建议传>
Content-Type: application/json
```

统一响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

异常响应由 FastAPI 返回 HTTP 状态码，常见为：

- `401`：未登录、token 无效或过期。
- `403`：权限范围为空或无权访问。
- `404`：文档、任务、会话不存在。
- `429`：问答并发槽位已满，需要稍后重试。
- `415`：不支持的文件类型。
- `422`：请求字段校验失败。
- `503`：服务密钥未配置。

## 二、JWT 要求

Python 会用 `.env` 中的 `SA_TOKEN_JWT_SECRET` 解码 Java Sa-Token JWT。

payload 至少需要：

```json
{
  "loginId": "login:10001",
  "userId": "10001"
}
```

可选字段：

```json
{
  "tenantId": "tenant",
  "device": "default",
  "loginType": "login",
  "eff": 1710000000,
  "timeout": 7200
}
```

如果传了 `eff` 和 `timeout`，Python 会按 `eff + timeout + SA_TOKEN_CLOCK_SKEW_SECONDS` 判断是否过期。

## 三、公共对象

### user_context

```json
{
  "user_id": "10001",
  "dept_id": "200",
  "role_codes": ["common_user"],
  "data_scope": "dept"
}
```

### access_scope

```json
{
  "scope_mode": "dept",
  "allowed_dept_ids": ["200"],
  "allowed_knowledge_ids": ["default"],
  "allowed_attach_ids": [],
  "deny_attach_ids": []
}
```

`scope_mode` 可选：

- `dept`：部门范围，必须传 `allowed_dept_ids`。
- `all_public`：只查公共文档。
- `custom`：自定义范围，需传部门、知识库或附件 ID 中至少一个。
- `admin_all`：管理员全量范围。

## 四、健康检查

```http
GET /internal/rag/health
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

## 五、文档处理接口

### 1. 提交文档处理

```http
POST /internal/rag/documents/process
```

请求：

```json
{
  "attach_id": 123,
  "knowledge_id": "default",
  "doc_id": "java-doc-001",
  "publish_dept_id": "200",
  "owner_user_id": "10001",
  "visible_in_chat": true,
  "publish_scope": "dept",
  "allowed_dept_ids": ["200"],
  "allowed_user_ids": [],
  "file_name": "制度文件.pdf",
  "file_ext": ".pdf",
  "mime_type": "application/pdf",
  "file_size": 102400,
  "file_hash": "sha256-or-md5",
  "bucket": "rag-documents",
  "object_key": "documents/制度文件.pdf",
  "operator_id": "10001",
  "auto_process": true,
  "force": false
}
```

字段说明：

- `attach_id`：Java 附件 ID，Python 侧唯一关联 `documents.java_attach_id`。
- `knowledge_id`：知识库 ID，对应 `documents.knowledge_base`。
- `publish_scope`：`public`、`dept`、`private`、`custom`。
- `bucket`、`object_key`：Python worker 从 MinIO 读取文件的位置。
- `auto_process`：是否立即入队解析、切片和向量化。

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "attach_id": 123,
    "rag_doc_id": "uuid",
    "status": "uploaded",
    "jobs": [
      {
        "job_id": "uuid",
        "status": "pending"
      }
    ]
  }
}
```

### 2. 查询文档状态

```http
GET /internal/rag/documents/{attach_id}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "attach_id": 123,
    "rag_doc_id": "uuid",
    "status": "indexed",
    "file_name": "制度文件.pdf",
    "knowledge_base": "default",
    "error_message": null,
    "updated_at": "2026-07-10T10:00:00+00:00"
  }
}
```

### 3. 重新解析

```http
POST /internal/rag/documents/{attach_id}/reparse
```

请求：

```json
{
  "operator_id": "10001",
  "force": true
}
```

### 4. 重新切片

```http
POST /internal/rag/documents/{attach_id}/rechunk
```

请求：

```json
{
  "operator_id": "10001",
  "chunk_config": {}
}
```

### 5. 删除 RAG 索引

```http
DELETE /internal/rag/documents/{attach_id}
```

请求：

```json
{
  "operator_id": "10001",
  "reason": "document_deleted"
}
```

说明：这里是 RAG 侧软删除和索引清理，不代表 Java 业务附件一定被物理删除。

## 六、任务接口

### 1. 分页查询任务

```http
GET /internal/rag/jobs?page=1&page_size=20&batch_id=&attach_id=&status=
```

支持参数：

- `batch_id`：批量重解析或重切片返回的批次 ID。
- `attach_id`：Java 附件 ID。
- `status`：`pending`、`running`、`succeeded`、`failed`、`skipped`、`canceled`。
- `page`：页码，最小 1。
- `page_size`：每页数量，最大 100。

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "job_id": "uuid",
        "rag_doc_id": "uuid",
        "job_type": "document_full_pipeline",
        "status": "pending",
        "batch_id": "BRP-20260712120000-xxxxxxxx",
        "batch_index": 1,
        "batch_label": "Batch reparse"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

### 2. 查询单个任务

```http
GET /internal/rag/jobs/{job_id}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "job_id": "uuid",
    "rag_doc_id": "uuid",
    "job_type": "document_full_pipeline",
    "status": "running",
    "progress": 70,
    "message": "processing",
    "error_message": null,
    "batch_id": "BRP-20260712120000-xxxxxxxx",
    "batch_index": 1,
    "batch_label": "Batch reparse",
    "result": {},
    "created_at": "2026-07-10T10:00:00+00:00",
    "updated_at": "2026-07-10T10:01:00+00:00"
  }
}
```

任务状态：

- `pending`
- `running`
- `succeeded`
- `failed`
- `skipped`
- `canceled`

## 七、会话接口

### 1. 创建会话

```http
POST /internal/rag/conversations
```

请求：

```json
{
  "title": "新会话",
  "created_by": "10001"
}
```

### 2. 会话列表

```http
GET /internal/rag/conversations?page=1&page_size=20&q=&feedback_only=false
```

支持参数：

- `page`
- `page_size`
- `q`
- `feedback_only`
- `created_by`

### 3. 会话消息

```http
GET /internal/rag/conversations/{conversation_id}/messages
```

### 4. 修改标题

```http
PATCH /internal/rag/conversations/{conversation_id}
```

请求：

```json
{
  "title": "新的标题"
}
```

### 5. 删除会话

```http
DELETE /internal/rag/conversations/{conversation_id}
```

## 八、问答接口

### 1. 非流式问答

```http
POST /internal/rag/chat
```

请求：

```json
{
  "session_id": "java-session-id",
  "message_id": "java-message-id",
  "question": "请问报销流程是什么？",
  "user_context": {
    "user_id": "10001",
    "dept_id": "200",
    "role_codes": ["common_user"],
    "data_scope": "dept"
  },
  "access_scope": {
    "scope_mode": "dept",
    "allowed_dept_ids": ["200"],
    "allowed_knowledge_ids": ["default"],
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

说明：

- `session_id` 可传 Java 会话 ID。若不是 UUID，Python 会稳定映射成 UUID。
- `question` 最大长度由 `CHAT_MAX_QUESTION_CHARS` 控制，默认 2000。
- `top_k` 最大 50。
- `rerank_top_k` 最大 20。
- 接口受聊天并发槽位保护。高峰期如果返回 `429`，Java 侧应提示稍后重试或做短暂退避重试。
- `access_scope` 会被 Python 转换为 SQL 条件并下推到文档、QA 和上下文扩展召回中。

响应 `data` 通常包含：

- `answer`
- `conversation_id`
- `user_message_id`
- `assistant_message_id`
- `citations`
- `suggested_questions`
- `retrieval_trace`

### 2. 流式问答

```http
POST /internal/rag/chat/stream
Accept: text/event-stream
```

请求体同非流式问答。

SSE 事件：

```text
event: message_start
data: {"conversation_id":"...","user_message_id":"...","assistant_message_id":"..."}

event: retrieval_start
data: {"query":"..."}

event: retrieval_done
data: {"recall_count":10,"rerank_count":5,"citation_count":3}

event: delta
data: {"content":"回答片段"}

event: citations
data: {"citations":[...]}

event: suggested_questions
data: {"questions":[...]}

event: message_end
data: {"message_id":"...","latency_ms":1234}
```

### 3. 撤回一轮问答

```http
POST /internal/rag/chat/retract
```

请求：

```json
{
  "session_id": "java-session-id",
  "conversation_id": null,
  "user_message_id": "uuid",
  "assistant_message_id": "uuid"
}
```

`session_id` 和 `conversation_id` 至少传一个。

## 九、Java 联调建议

推荐联调顺序：

1. `/internal/rag/health`：确认 JWT 可验证。
2. `/internal/rag/documents/process`：提交一个小 PDF 或 txt。
3. `/internal/rag/jobs/{job_id}`：轮询直到 `succeeded`。
4. `/internal/rag/documents/{attach_id}`：确认 `status=indexed`。
5. `/internal/rag/chat`：用同部门用户提问，确认能返回引用。
6. 换无权限用户提问，确认不会召回该文档。
7. `/internal/rag/chat/stream`：确认前端 SSE 解析。
8. 删除 Java 附件后调用 `DELETE /internal/rag/documents/{attach_id}`。

## 十、新增批量与反馈接口

### 1. 知识库列表

```http
GET /internal/rag/knowledge-bases
```

返回 `items`，每项包含 `id`、`code`、`name`、`value`、`source` 等字段。Python 会优先读取共库中的 `public.knowledge_info`，不可用时回退到 RAG 文档表中已有的知识库值。

### 2. 批量文档操作

```http
POST /internal/rag/documents/batch/reparse
POST /internal/rag/documents/batch/rechunk
POST /internal/rag/documents/batch/knowledge-base
POST /internal/rag/documents/batch/delete
```

批量重解析和重切片请求：

```json
{
  "attach_ids": [1001, 1002]
}
```

批量调整知识库请求：

```json
{
  "attach_ids": [1001, 1002],
  "knowledge_id": "default"
}
```

重解析和重切片响应会返回 `batch.batch_id` 以及每个附件对应的 `job_id`，Java 可以用任务列表接口分页查询同批次任务：

```http
GET /internal/rag/jobs?batch_id=BRP-20260712120000-xxxxxxxx&page=1&page_size=20
GET /internal/rag/jobs?attach_id=1001
GET /internal/rag/jobs?status=failed
```

批量删除会软删除 RAG 侧索引并返回删除数量；不代表 Java 业务附件被物理删除。

### 3. 回答反馈

```http
POST /internal/rag/feedback/answers
POST /internal/rag/feedback/answers/{feedback_id}/cancel
```

提交反馈请求：

```json
{
  "assistant_message_id": "uuid",
  "error_type": "answer_wrong",
  "description": "答案不准确"
}
```

`error_type` 支持：`answer_wrong`、`citation_wrong`、`off_topic`、`incomplete`、`other`。接口会校验当前 Sa-Token 用户是否可访问该会话，并同步更新 retrieval log 的回答质量信息。

## 十一、本轮接口冒烟结果

本轮基于 `app.openapi()` 做了全量路由冒烟，覆盖 76 个 HTTP 操作，未出现 500。新增 Java 对接接口在未带鉴权时均返回 `401`，说明路由和 Sa-Token 鉴权链路已命中：

- `GET /internal/rag/knowledge-bases`
- `POST /internal/rag/documents/batch/reparse`
- `POST /internal/rag/documents/batch/rechunk`
- `POST /internal/rag/documents/batch/knowledge-base`
- `POST /internal/rag/documents/batch/delete`
- `GET /internal/rag/jobs?batch_id=BRP-smoke`
- `POST /internal/rag/feedback/answers`
- `POST /internal/rag/feedback/answers/{feedback_id}/cancel`

真实业务闭环仍需在联调环境带有效 Sa-Token JWT、PostgreSQL、Redis、MinIO 和模型 Key 验证文档入库、批量任务执行、问答检索和反馈取消。
