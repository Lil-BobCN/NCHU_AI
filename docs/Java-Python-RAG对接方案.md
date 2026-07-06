# AI 辅导员系统 Java-Python RAG 对接方案

版本：V1.0  
日期：2026-06-30  
适用对象：Java 后端、Python RAG 后端、前端、测试、项目负责人

## 1. 方案结论

系统采用“Java 业务后台 + Python RAG 内核”的架构。

核心原则：

1. 前端只访问 Java，不直接访问 Python。
2. Java 负责登录鉴权、用户、角色、部门、权限、页面、业务 CRUD、统计、审计。
3. Python 负责 RAG 相关能力，包括文档解析、切片、向量化、召回、重排、问答生成、引用来源、RAG 日志、评测。
4. Java 和 Python 可以共用同一个 PostgreSQL 实例，但必须明确表归属，不能两边随意混写同一张表。
5. Python 检索必须受 Java 传入的权限范围限制；没有权限范围时，Python 默认拒绝知识库检索。

一句话说明：

> Java 是业务入口和权限裁判，Python 是内部 RAG 引擎。Java 每次调用 Python 时，必须告诉 Python 当前用户允许检索哪些知识库和文档；Python 只能在这个范围内召回。

## 2. 系统边界

### 2.1 Java 负责范围

Java 负责所有面向用户和后台管理员的业务能力：

| 模块 | Java 职责 |
| --- | --- |
| 登录鉴权 | 登录、退出、Token 校验、Sa-Token 会话管理 |
| 用户权限 | 用户、角色、部门、菜单、按钮权限、数据权限 |
| 知识库管理 | 知识库新增、编辑、删除、启停、置顶、导入、导出 |
| 文档管理 | 文档上传入口、删除、批量删除、归类、权限配置、导出 |
| 片段管理 | 后台列表、筛选、查看、导出；数据主要由 Python 写入 |
| 问答会话 | 会话创建、重命名、删除、列表筛选、消息展示 |
| 反馈处理 | 回答有误、处理状态、异常会话筛选、处理记录 |
| 高频问题 | 高频问题统计、置顶、排序、展示、维护 |
| 统计看板 | 咨询量、访问量、问题类型、服务解决率等 |
| 审计日志 | 后台操作日志、用户行为日志、接口调用链路 |
| 前端页面 | 所有 Web 页面、路由、菜单、按钮、表格、导入导出 |

Java 不负责：

- 文档内容解析。
- 切片策略。
- 向量化。
- 召回排序。
- 大模型问答。
- RAG 技术链路细节。

### 2.2 Python 负责范围

Python 只负责 RAG 能力：

| 模块 | Python 职责 |
| --- | --- |
| 文档解析 | PDF、Word、Excel、图片、压缩包等解析 |
| 表格处理 | Markdown 表格识别、原文结构保留、表格片段元数据 |
| 切片 | 文档切片、父子块、页码、表格编号、章节路径 |
| 向量化 | chunk embedding、QA embedding、向量索引维护 |
| 召回 | 向量召回、关键词召回、QA 召回、混合召回 |
| 重排 | rerank、TopK 控制、结果去重 |
| 问答 | 问题改写、上下文组装、回答生成、闲聊拦截 |
| 引用来源 | 来源文档、页码、表格号、片段 ID，不暴露无权限内容 |
| RAG 日志 | retrieval trace、召回结果、最终上下文、耗时、模型信息 |
| 评测 | 评测集、评测任务、召回命中、答案质量 |

Python 不负责：

- 用户登录。
- Java Sa-Token 解析。
- 菜单权限。
- 后台页面。
- 用户、角色、部门 CRUD。
- 业务导出和审批流程。

## 3. 数据库归属

推荐使用同一个 PostgreSQL 实例，但按表划分归属。

建议：

- Java 业务表使用 Java 既有命名。
- Python RAG 内核表增加 `rag_` 前缀，或放在独立 schema，例如 `rag`。
- 所有表必须明确唯一写入方。

### 3.1 Java 主责表

| 表名 | 主责方 | Python 是否写入 | 说明 |
| --- | --- | --- | --- |
| `knowledge_info` | Java | 不写 | 知识库基础信息、启停、排序、标签、权限配置 |
| `knowledge_attach` | Java | 只回写 RAG 状态字段 | 文档附件业务记录，Java 创建、删除、配置权限 |
| `knowledge_fragment` | Python 写，Java 读 | 写入方为 Python | 片段预览表，给 Java 后台展示，不存向量 |
| `qa_tag` | Java | 不写 | 问题分类标签 |
| `qa_hot_question` | Java | 可由 Python/定时任务提供统计数据 | 高频问题业务表 |
| `chat_session` | Java | 不直接写，除非双方另定 | 会话业务表 |
| `chat_message` | Java | 不直接写，除非双方另定 | 用户消息、AI 消息、展示用引用 |
| `qa_feedback` | Java | 可接收 Python 辅助字段 | 回答反馈和处理流程 |
| `sys_user` / `sys_role` / `sys_dept` | Java | 不写 | 用户、角色、部门 |

### 3.2 Python 主责表

| 表名 | 主责方 | Java 是否写入 | 说明 |
| --- | --- | --- | --- |
| `rag_documents` | Python | 不写 | RAG 文档映射，关联 `knowledge_attach.id` |
| `rag_document_jobs` | Python | 不写 | 解析、切片、向量化任务 |
| `rag_parse_results` | Python | 不写 | 解析原文、Markdown、解析元数据 |
| `rag_chunks` | Python | 不写 | 切片内容、页码、表格号、章节路径 |
| `rag_embeddings` | Python | 不写 | 向量数据和索引 |
| `rag_qa_pairs` | Python 或 Java 同步 | 通过接口同步 | 结构化 QA 数据 |
| `rag_qa_embeddings` | Python | 不写 | QA 向量 |
| `rag_retrieval_logs` | Python | 不写 | 召回日志、上下文、引用来源 |
| `rag_evaluation_*` | Python | 不写 | RAG 评测相关 |

`rag_documents` 需要保存 Java 传入的部门权限字段：

- `attach_id`
- `knowledge_id`
- `publish_dept_id`
- `visible_in_chat`
- `status`

这些字段不是由 Python 判定业务权限，而是用于检索时快速执行 Java 已定义的权限过滤规则。

### 3.3 特殊共享规则

#### `knowledge_attach`

Java 创建和维护业务字段：

- `id`
- `kid`
- `doc_id`
- `doc_name`
- `doc_type`
- `oss_id`
- 权限字段
- 删除状态
- 创建人
- 所属部门
- `publish_dept_id`，发布部门，用于问答检索部门权限过滤
- `visible_in_chat`，是否允许进入问答检索

Python 只允许回写 RAG 状态字段：

- `rag_doc_id`
- `vector_status`
- `parse_status`
- `quality_score`
- `error_message`
- `chunk_count`
- `updated_at`

建议状态枚举：

| 状态值 | 含义 |
| --- | --- |
| `0` | 未处理 |
| `1` | 已入队 |
| `2` | 解析中 |
| `3` | 切片中 |
| `4` | 向量化中 |
| `5` | 已入库 |
| `8` | 已禁用 |
| `9` | 处理失败 |
| `10` | 已删除 |

#### `knowledge_fragment`

Python 写入，Java 只读。

建议字段：

| 字段 | 说明 |
| --- | --- |
| `id` | 主键 |
| `kid` | 知识库 ID |
| `attach_id` | Java 附件 ID |
| `rag_doc_id` | Python RAG 文档 ID |
| `chunk_id` | Python chunk ID |
| `idx` | 片段序号 |
| `chunk_type` | text/table/qa/title |
| `content` | 片段预览内容 |
| `page_start` | 起始页 |
| `page_end` | 结束页 |
| `table_no` | 表格编号 |
| `section_path` | 章节路径 |
| `token_count` | token 数 |
| `is_active` | 是否有效 |

注意：`knowledge_fragment` 只用于后台展示，不参与向量检索。

## 4. 权限设计

权限问题是本方案的核心。

Python RAG 不应该自己判断业务权限，因为用户、角色、部门、菜单、数据范围都在 Java。正确做法是：

1. Java 校验用户登录。
2. Java 根据用户身份计算本次可访问范围。
3. Java 调 Python 时传入 `user_context` 和 `access_scope`。
4. Python 只在 `access_scope` 限定范围内召回。
5. 如果没有 `access_scope`，Python 拒绝知识库检索。

### 4.1 浏览器到 Java 的鉴权

```text
Browser -> Java
Authorization: Bearer <Java Sa-Token>
```

Java 负责：

- 校验登录态。
- 获取用户 ID。
- 获取部门 ID。
- 获取角色。
- 获取数据权限范围。
- 记录操作日志。

### 4.2 Java 到 Python 的鉴权

Java 调 Python 使用内部服务鉴权。

请求头：

```http
X-RAG-Service-Token: <内部服务密钥>
X-Request-Id: <链路追踪 ID>
Content-Type: application/json
```

Python 负责：

- 校验 `X-RAG-Service-Token`。
- 校验请求来源，建议配合 Nginx IP 白名单。
- 记录 `X-Request-Id`。
- 不接受浏览器直接调用。

不建议 Java 用 Python 管理员 JWT 模拟登录。短期可以兼容，长期应迁移为服务间 Token。

### 4.3 权限范围数据结构

Java 每次问答必须传：

```json
{
  "user_context": {
    "user_id": "10086",
    "dept_id": "finance",
    "role_codes": ["student_user"],
    "data_scope": "self"
  },
  "access_scope": {
    "scope_mode": "dept",
    "allowed_dept_ids": ["finance"],
    "allowed_knowledge_ids": ["kb_public", "kb_student"],
    "allowed_attach_ids": [101, 102, 103],
    "deny_attach_ids": []
  }
}
```

字段说明：

| 字段 | 是否必填 | 说明 |
| --- | --- | --- |
| `user_context.user_id` | 是 | 当前用户 ID |
| `user_context.dept_id` | 是 | 当前用户部门 |
| `user_context.role_codes` | 是 | 当前用户角色 |
| `access_scope.scope_mode` | 是 | 权限模式，建议支持 `dept`、`all_public`、`custom`、`admin_all` |
| `access_scope.allowed_dept_ids` | 部门权限场景必填 | 允许检索的发布部门范围 |
| `access_scope.allowed_knowledge_ids` | 是 | 允许检索的知识库范围 |
| `access_scope.allowed_attach_ids` | 可选 | 允许检索的具体文档 |
| `access_scope.deny_attach_ids` | 可选 | 强制排除文档 |

权限过滤原则：

- `scope_mode = dept` 时，以 `allowed_dept_ids` 过滤发布部门。
- 有 `allowed_attach_ids` 时，再叠加文档级权限过滤。
- 有 `allowed_knowledge_ids` 时，再叠加知识库级权限过滤。
- 普通用户不能传 `admin_all`；只有 Java 确认当前用户是系统管理员时才允许。
- 没有任何有效范围时，拒绝知识库检索。
- `deny_attach_ids` 永远优先排除。

### 4.4 部门权限模式

如果业务规则是“哪个部门发布的资料，只有该部门用户或管理员可以检索”，推荐使用 `scope_mode = dept`。

核心规则：

1. Java 在文档上传或发布时，将发布部门写入 `knowledge_attach.publish_dept_id` 或等价字段。
2. Java 在用户提问时，根据当前登录用户和角色计算 `allowed_dept_ids`。
3. Python 检索时按 `allowed_dept_ids` 过滤文档发布部门。
4. 系统管理员或校级管理员由 Java 传更大的部门范围，或传 `scope_mode = admin_all`。

示例：

```json
{
  "user_context": {
    "user_id": "20001",
    "dept_id": "finance",
    "role_codes": ["dept_counselor"],
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

如果当前用户是校级管理员，Java 可以传：

```json
{
  "access_scope": {
    "scope_mode": "admin_all",
    "allowed_dept_ids": [],
    "allowed_knowledge_ids": [],
    "allowed_attach_ids": [],
    "deny_attach_ids": []
  }
}
```

`admin_all` 不是前端可自行指定的权限，只能由 Java 后端在完成角色校验后传给 Python。

### 4.5 部门、用户、文档关系模型

部门权限需要拆成三类数据，且都由 Java 维护：

| 数据 | Java 维护位置 | 说明 |
| --- | --- | --- |
| 用户属于哪个部门 | `sys_user.dept_id` 或用户-部门关系表 | 用于判断当前用户归属部门 |
| 用户拥有哪些部门数据权限 | 角色、部门、数据权限配置 | 例如只能看本部门、可看多个部门、可看全校 |
| 文档绑定哪个发布部门 | `knowledge_attach.publish_dept_id` | 用于问答检索时过滤文档 |

推荐字段：

```text
sys_user
- user_id
- dept_id

sys_dept
- dept_id
- parent_id
- dept_name

knowledge_attach
- id
- kid
- doc_name
- publish_dept_id
- created_by
- visible_in_chat
- status
- rag_doc_id

rag_documents
- rag_doc_id
- attach_id
- knowledge_id
- publish_dept_id
- owner_user_id
- visible_in_chat
- status
```

如果一个用户只属于一个部门，Java 直接用 `sys_user.dept_id` 即可。

如果一个用户可能属于多个部门，Java 增加用户-部门关系表，例如：

```text
sys_user_dept
- user_id
- dept_id
```

Python 不需要直接查 `sys_user` 或判断用户是否属于某个部门。Python 只接收 Java 计算好的结果：

```json
{
  "user_context": {
    "user_id": "20001",
    "dept_id": "finance",
    "role_codes": ["dept_counselor"]
  },
  "access_scope": {
    "scope_mode": "dept",
    "allowed_dept_ids": ["finance"]
  }
}
```

也就是说：

```text
用户是不是某个部门的人：Java 判断
用户能看哪些部门资料：Java 判断
文档属于哪个部门：Java 写入 publish_dept_id
RAG 能不能召回该文档：Python 按 allowed_dept_ids 和 publish_dept_id 过滤
```

如果存在全校公开资料，可以额外增加 `publish_scope`：

```text
publish_scope = dept     只对发布部门可见
publish_scope = public   全校可见
publish_scope = private  仅创建人或指定人员可见
```

第一版如果没有全校公开和个人私有资料，可以先不加 `publish_scope`，只做 `publish_dept_id`。

### 4.6 Python 检索过滤要求

Python 的向量召回、关键词召回、QA 召回都必须在召回前过滤权限。

不能这样做：

```text
全库召回 -> 生成答案 -> 再过滤引用
```

必须这样做：

```text
权限过滤 -> 召回 -> 重排 -> 生成答案
```

示例逻辑：

```sql
WHERE (
    :scope_mode = 'admin_all'
    OR d.publish_dept_id = ANY(:allowed_dept_ids)
  )
  AND (
    :allowed_knowledge_ids_is_empty
    OR d.knowledge_id = ANY(:allowed_knowledge_ids)
  )
  AND (
    :allowed_attach_ids_is_empty
    OR d.attach_id = ANY(:allowed_attach_ids)
  )
  AND NOT (d.attach_id = ANY(:deny_attach_ids))
  AND d.status = 'indexed'
  AND c.is_active = true
```

如果用户没有某个文档权限，该文档从召回第一步就不会进入候选集。

### 4.7 大权限范围性能处理

如果用户可访问文档很多，不建议每次传几万个 `allowed_attach_ids`。

可以采用三种方式：

| 方式 | 适用场景 | 说明 |
| --- | --- | --- |
| 传 `allowed_knowledge_ids` | 多数场景 | 用户按知识库授权 |
| 传 `allowed_attach_ids` | 精细文档权限 | 文档数量较少 |
| Java 维护权限快照表 | 大规模精细权限 | Java 写权限表，Python 只读 join 过滤 |

权限快照表可选设计：

```text
rag_access_scope_snapshot
- scope_id
- user_id
- allowed_knowledge_ids
- allowed_attach_ids
- expires_at
- created_at
```

Java 生成 `scope_id`，Python 根据 `scope_id` 读取权限快照。该方案适合权限列表非常大时使用。

## 5. 接口规范

Python 提供内部接口，统一前缀：

```text
/internal/rag
```

所有接口必须带：

```http
X-RAG-Service-Token: <内部服务密钥>
X-Request-Id: <链路追踪 ID>
```

统一响应格式建议：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

错误响应：

```json
{
  "code": 403,
  "message": "access_scope 缺失，拒绝检索",
  "data": null
}
```

## 6. Python 需要提供的接口

### 6.1 健康检查

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
    "version": "1.0.0"
  }
}
```

### 6.2 文档处理

#### 6.2.1 发起文档处理

```http
POST /internal/rag/documents/process
```

Java 在完成文件上传和 `knowledge_attach` 写入后调用。

请求：

```json
{
  "attach_id": 101,
  "knowledge_id": "kb_student",
  "doc_id": "java-doc-001",
  "publish_dept_id": "finance",
  "visible_in_chat": true,
  "file_name": "学生事务指南.docx",
  "file_ext": "docx",
  "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "file_size": 123456,
  "file_hash": "sha256-value",
  "bucket": "ai-mentor",
  "object_key": "docs/2026/学生事务指南.docx",
  "operator_id": "1001",
  "auto_process": true,
  "force": false
}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "attach_id": 101,
    "rag_doc_id": "rag-doc-uuid",
    "job_id": "job-uuid",
    "status": "queued"
  }
}
```

Python 处理内容：

1. 创建或更新 `rag_documents`。
2. 创建 `rag_document_jobs`。
3. 从 MinIO 读取文件。
4. 异步执行解析、切片、向量化。
5. 回写 `knowledge_attach` 状态。
6. 写入 `knowledge_fragment` 片段预览。

#### 6.2.2 重新解析

```http
POST /internal/rag/documents/{attach_id}/reparse
```

请求：

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
    "job_id": "job-uuid",
    "status": "queued"
  }
}
```

#### 6.2.3 重新切片和向量化

```http
POST /internal/rag/documents/{attach_id}/rechunk
```

请求：

```json
{
  "operator_id": "1001",
  "chunk_config": {
    "chunk_size": 800,
    "chunk_overlap": 120
  }
}
```

响应同重新解析。

#### 6.2.4 删除 RAG 索引

```http
DELETE /internal/rag/documents/{attach_id}
```

Java 删除或禁用文档后调用。

请求：

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
    "status": "deleted"
  }
}
```

Python 处理内容：

1. 将 `rag_documents` 标记删除或禁用。
2. 将相关 `rag_chunks` 置为 inactive。
3. 删除或禁用向量。
4. 清理 `knowledge_fragment`。
5. 回写 `knowledge_attach.vector_status = 10`。

#### 6.2.5 查询任务状态

```http
GET /internal/rag/jobs/{job_id}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "job_id": "job-uuid",
    "attach_id": 101,
    "job_type": "parse_chunk_embed",
    "status": "running",
    "progress": 65,
    "message": "向量化中",
    "error_message": null,
    "created_at": "2026-06-30 10:00:00",
    "updated_at": "2026-06-30 10:00:30"
  }
}
```

### 6.3 问答接口

#### 6.3.1 流式问答

```http
POST /internal/rag/chat/stream
```

用于前端需要打字机效果的场景。Java 调 Python，Java 再把 SSE 转发给前端。

请求：

```json
{
  "session_id": "java-session-001",
  "message_id": "java-user-message-001",
  "question": "票据报销需要哪些材料？",
  "user_context": {
    "user_id": "10086",
    "dept_id": "finance",
    "role_codes": ["student_user"],
    "data_scope": "self"
  },
  "access_scope": {
    "allowed_knowledge_ids": ["kb_public", "kb_student"],
    "allowed_attach_ids": [101, 102, 103],
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

SSE 事件：

```text
event: message_start
data: {"assistant_message_id":"rag-msg-001"}

event: delta
data: {"text":"票据报销需要准备"}

event: citations
data: [{"document_name":"学生事务指南.docx","attach_id":101,"page":3,"table_no":"表格 4"}]

event: message_end
data: {"answer":"完整答案","retrieval_log_id":"log-uuid","latency_ms":3200}
```

Java 处理要求：

1. Java 创建用户消息。
2. Java 调 Python SSE。
3. Java 将 Python SSE 转发给前端。
4. Java 在 `message_end` 后保存 AI 消息。
5. Java 保存引用来源和 `retrieval_log_id`。

Python 处理要求：

1. 校验服务 Token。
2. 校验 `access_scope`。
3. 闲聊类问题直接返回固定引导话术，可跳过检索。
4. 业务问题只在权限范围内召回。
5. 生成答案。
6. 返回精简后的引用来源。
7. 写入 `rag_retrieval_logs`。

#### 6.3.2 非流式问答

```http
POST /internal/rag/chat
```

请求同流式问答。

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "answer": "票据报销需要准备发票、报销单、审批材料等。",
    "citations": [
      {
        "attach_id": 101,
        "document_name": "学生事务指南.docx",
        "page_start": 3,
        "page_end": 3,
        "table_no": "表格 4",
        "chunk_id": "chunk-uuid"
      }
    ],
    "suggested_questions": [],
    "retrieval_log_id": "log-uuid",
    "latency_ms": 3200
  }
}
```

### 6.4 检索调试接口

```http
POST /internal/rag/retrieval/search
```

仅供后台调试，不建议普通用户使用。

请求：

```json
{
  "query": "票据报销",
  "user_context": {
    "user_id": "10086",
    "dept_id": "finance",
    "role_codes": ["dept_counselor"]
  },
  "access_scope": {
    "allowed_knowledge_ids": ["kb_public"],
    "allowed_attach_ids": [101, 102]
  },
  "options": {
    "top_k": 10,
    "score_threshold": 0.3
  }
}
```

### 6.5 反馈同步接口

```http
POST /internal/rag/feedback/sync
```

Java 在用户点击“回答有误”或后台处理反馈时调用。

请求：

```json
{
  "feedback_id": "fb-001",
  "session_id": "java-session-001",
  "user_message_id": "java-user-message-001",
  "assistant_message_id": "java-assistant-message-001",
  "retrieval_log_id": "log-uuid",
  "error_type": "wrong_answer",
  "description": "答案不准确",
  "status": "open",
  "operator_id": "1001"
}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "feedback_id": "fb-001",
    "synced": true
  }
}
```

### 6.6 统计接口

如果 Java 统计直接查自己的业务表即可，不一定需要调用 Python。涉及 RAG 技术质量的统计可由 Python 提供。

```http
GET /internal/rag/statistics/quality
GET /internal/rag/statistics/retrieval
GET /internal/rag/statistics/documents
```

建议 Java 优先维护业务统计：

- 咨询量。
- 用户数。
- 反馈数。
- 问题类型。
- 高频问题。

Python 提供技术统计：

- 平均召回耗时。
- 平均生成耗时。
- 向量召回命中率。
- 无答案率。
- 文档解析成功率。

## 7. Java 需要提供或实现的能力

### 7.1 Java 需要传给 Python 的内容

每次文档处理，Java 必须传：

- `attach_id`
- `knowledge_id`
- `doc_id`
- `file_name`
- `file_ext`
- `file_size`
- `file_hash`
- `bucket`
- `object_key`
- `operator_id`

每次问答，Java 必须传：

- `session_id`
- `message_id`
- `question`
- `user_context`
- `access_scope`
- `options`

### 7.2 Java 需要保存的数据

Java 保存业务展示数据：

- 会话。
- 用户消息。
- AI 消息。
- 引用来源。
- 反馈状态。
- 异常会话标记。
- 文档状态。
- 操作日志。

Python 返回的答案和引用来源由 Java 落库，方便后台统一查询、导出和权限过滤。

### 7.3 Java 权限计算

Java 在问答前需要计算：

```text
当前用户能访问哪些知识库？
当前用户能访问哪些文档？
哪些文档必须禁止访问？
当前用户是否能使用问答能力？
```

计算结果通过 `access_scope` 传给 Python。

### 7.4 Java SSE 转发

Java 可继续使用当前 `RagChatServiceImpl` 思路：

```text
前端请求 Java SSE 接口
Java 调 Python /internal/rag/chat/stream
Java 逐行转发 Python SSE
Java 在结束时保存 AI 消息
```

Nginx 需要关闭 SSE 缓冲：

```text
X-Accel-Buffering: no
Cache-Control: no-cache
```

## 8. 主要业务流程

### 8.1 知识库新增

```text
1. 管理员在 Java 后台新增知识库
2. Java 校验权限
3. Java 写 knowledge_info
4. Python 无需处理
```

### 8.2 知识库删除或禁用

```text
1. 管理员删除/禁用知识库
2. Java 校验权限
3. Java 更新 knowledge_info 状态
4. Java 查询该知识库下所有 attach_id
5. Java 批量调用 Python 删除或禁用 RAG 索引
6. Python 禁用对应 rag_documents/chunks/embeddings
7. Python 清理 knowledge_fragment
```

### 8.3 文档上传

```text
1. 用户在 Java 页面上传文档
2. Java 校验用户是否有该知识库上传权限
3. Java 上传文件到 MinIO
4. Java 写 knowledge_attach，状态为未处理或已入队
5. Java 调 Python /internal/rag/documents/process
6. Python 返回 job_id 和 rag_doc_id
7. Java 页面显示处理中
8. Python 异步解析、切片、向量化
9. Python 回写 knowledge_attach 状态
10. Python 写 knowledge_fragment
11. Java 轮询 job 或查表刷新状态
```

### 8.4 文档删除

```text
1. 用户在 Java 页面删除文档
2. Java 校验权限
3. Java 将 knowledge_attach 标记删除
4. Java 调 Python DELETE /internal/rag/documents/{attach_id}
5. Python 禁用 RAG 文档、切片和向量
6. Python 清理 knowledge_fragment
7. Java 记录操作日志
```

### 8.5 文档重新解析

```text
1. 用户在 Java 页面点击重新解析
2. Java 校验权限
3. Java 调 Python /internal/rag/documents/{attach_id}/reparse
4. Python 创建任务
5. Python 重新解析、切片、向量化
6. Python 更新状态和片段
7. Java 展示最新状态
```

### 8.6 文档权限变化

文档权限变化由 Java 负责。

```text
1. 管理员调整文档或知识库权限
2. Java 更新权限配置、发布部门或 visible_in_chat
3. 如发布部门或可见性字段变化，Java 通知 Python 同步 rag_documents 元数据
4. Python 不需要重建向量
5. 后续问答时 Java 传新的 access_scope
6. Python 按新的 access_scope 过滤召回
```

如果采用权限快照表：

```text
1. Java 更新权限配置
2. Java 刷新权限快照
3. Python 问答时读取最新快照
```

### 8.7 新建对话

```text
1. 用户点击新建对话
2. Java 创建 chat_session
3. Java 不传旧 session 上下文给 Python
4. Python 只基于当前 session_id 处理后续问题
```

要求：

- 新会话必须隔离历史上下文。
- Python 不允许使用全局历史记忆。
- 闲聊类问题直接返回固定引导话术，跳过知识库检索。

### 8.8 用户提问

```text
1. 用户输入问题
2. 前端请求 Java
3. Java 校验登录态
4. Java 计算 access_scope
5. Java 保存用户消息
6. Java 调 Python /internal/rag/chat/stream
7. Python 校验服务 Token
8. Python 校验 access_scope
9. Python 判断是否闲聊
10. 如果是业务问题，Python 在权限范围内召回
11. Python 重排、组装上下文、生成答案
12. Python 返回答案流和引用来源
13. Java 保存 AI 消息
14. 前端展示答案
```

### 8.9 回答有误反馈

```text
1. 用户点击回答有误
2. Java 写 qa_feedback
3. Java 标记该会话为异常反馈会话
4. Java 调 Python /internal/rag/feedback/sync
5. Python 关联 retrieval_log，保留问题快照、答案快照、引用快照
6. 后台人员在 Java 处理反馈
7. 如需更新知识库，由 Java 修改业务数据并触发 Python 重建相关索引
```

## 9. Python 改造清单

Python 侧需要做：

1. 新增 `/internal/rag/*` 路由。
2. 新增服务间鉴权依赖，校验 `X-RAG-Service-Token`。
3. 文档模型增加 Java 映射字段：`attach_id`、`knowledge_id`、`doc_id`、`oss_id`。
4. 文档处理接口支持从 Java 提供的 MinIO bucket/object_key 读取文件。
5. 文档处理完成后回写 `knowledge_attach`。
6. 文档处理完成后写入 `knowledge_fragment`。
7. 问答接口支持 `user_context` 和 `access_scope`。
8. 所有召回方法强制加权限过滤。
9. 没有权限范围时拒绝检索。
10. 支持 SSE 给 Java 转发。
11. 保留现有 RAG 能力，逐步下线 Python 前端和本地管理员鉴权。

当前工程中需要重点改造的位置：

- `backend/app/api/v1/chat.py`
- `backend/app/api/v1/documents.py`
- `backend/app/services/chat_service.py`
- `backend/app/services/retrieval_service.py`
- `backend/app/services/document_pipeline.py`
- `backend/app/db/models.py`

## 10. Java 改造清单

Java 侧需要做：

1. 前端所有 RAG 相关页面都走 Java 接口。
2. `RagApiClient` 改为调用 `/internal/rag/*`。
3. Java 调 Python 时改用 `X-RAG-Service-Token`。
4. 文档上传后传 MinIO 信息给 Python。
5. Java 保存 `rag_doc_id`、`job_id`、处理状态。
6. Java 实现权限范围计算，生成 `access_scope`。
7. Java 问答接口负责创建 session 和 message。
8. Java SSE 转发 Python SSE。
9. Java 保存 AI 答案、引用来源、反馈状态。
10. Java 后台列表读取 Java 业务表，不直接读 Python 向量表。

## 11. 安全要求

1. Python internal 接口不能暴露给公网浏览器。
2. Nginx 建议限制 `/internal/rag/*` 只允许 Java 服务访问。
3. Java 到 Python 必须带服务 Token。
4. 服务 Token 需要可轮换。
5. 所有请求带 `X-Request-Id`。
6. Python 日志不能打印完整 Token。
7. Python 返回引用来源时不返回无权限文档内容。
8. Python 不允许在缺少权限范围时默认查全库。

## 12. 性能要求

1. 文档解析、切片、向量化必须异步。
2. Java 上传文档后只等待 Python 返回 `job_id`，不等待完整解析完成。
3. 问答使用 SSE 流式返回，减少用户等待感。
4. 权限过滤必须发生在召回前。
5. Java 后台片段列表读 `knowledge_fragment`，不读 `rag_chunks` 大表。
6. Java 不直接查询 `rag_embeddings`。
7. 大权限范围用户优先传 `allowed_knowledge_ids`，避免传超长文档 ID 列表。
8. 统计看板使用聚合表或定时任务，避免实时扫日志大表。

## 13. 验收标准

### 13.1 文档流程验收

- Java 上传文档后，Python 能收到处理请求。
- Python 能从 MinIO 读取文件。
- Python 能完成解析、切片、向量化。
- Java 页面能看到处理状态。
- Java 页面能看到片段预览。
- 删除文档后，Python 不再召回该文档。
- 重新解析后，引用来源和片段内容更新。

### 13.2 权限流程验收

- 用户只能召回自己有权限的知识库。
- 用户不能召回无权限文档。
- Java 不传 `access_scope` 时，Python 拒绝知识库检索。
- 调整权限后，无需重建向量即可生效。
- 新建会话不会继承旧会话上下文。

### 13.3 问答流程验收

- 前端只请求 Java。
- Java 能正常转发 Python SSE。
- Java 能保存用户消息和 AI 消息。
- Python 返回引用来源只包含文档名、页码、表格号等精简信息。
- 回答有误后，Java 历史会话能标记异常反馈。

## 14. 推荐实施阶段

### 第一阶段：接口打通

目标：Java 能调 Python 完成最小闭环。

任务：

1. Python 新增 internal 鉴权。
2. Python 提供文档处理接口。
3. Python 提供问答接口。
4. Java 上传文档后调用 Python。
5. Java 问答接口调用 Python。

### 第二阶段：权限闭环

目标：所有检索都受 Java 权限控制。

任务：

1. Java 计算 `access_scope`。
2. Python 检索前强制过滤。
3. 缺失权限范围时拒绝检索。
4. 测试无权限文档不可召回。

### 第三阶段：数据同步

目标：后台管理页面可用。

任务：

1. Python 回写 `knowledge_attach` 状态。
2. Python 写 `knowledge_fragment`。
3. Java 展示处理进度、质量分、片段列表。
4. Java 反馈和异常会话接入。

### 第四阶段：下线重复能力

目标：Java 成为唯一前端和业务入口。

任务：

1. Python 前端不再对用户开放。
2. Python 本地管理员鉴权仅保留内部调试或废弃。
3. Java 统一提供文档、会话、反馈、统计页面。

## 15. 需要双方确认的问题

1. PostgreSQL schema 怎么划分：Java 表和 Python 表是否使用不同 schema。
2. `knowledge_attach` 最终字段是否允许 Python 回写 RAG 状态。
3. `knowledge_fragment` 是否由 Python 直接写 Java 表。
4. 文件存储是否统一使用 MinIO，Java 是否能提供 bucket/object_key。
5. Java 问答是否必须 SSE 流式。
6. 权限粒度是知识库级、文档级，还是两者都有。
7. 大规模文档权限是否需要权限快照表。
8. RAG 日志是否只放 Python 表，还是 Java 也需要同步摘要。
9. 反馈处理后是否需要自动触发知识库重建。
10. 服务间 Token 和 Nginx 白名单由谁配置。

## 16. 给 Java 的简短对接说明

Java 只需要记住以下规则：

1. 所有前端请求先进入 Java。
2. Java 负责用户鉴权和权限计算。
3. 上传文档后，Java 把 MinIO 文件信息和 `attach_id` 发给 Python。
4. 问答时，Java 必须把 `user_context` 和 `access_scope` 发给 Python。
5. Python 返回答案、引用来源和 RAG 日志 ID。
6. Java 保存会话、消息、反馈、统计。
7. Java 不直接操作 Python 的向量表。
8. Java 删除或禁用文档时，必须通知 Python 禁用 RAG 索引。

## 17. 给 Python 的简短实现说明

Python 只需要记住以下规则：

1. 只提供内部 RAG 接口给 Java。
2. 不处理浏览器登录态。
3. 不解析 Java Sa-Token。
4. 所有 internal 接口校验服务 Token。
5. 文档处理从 MinIO 读取文件。
6. 所有召回都必须带权限过滤。
7. 没有权限范围就拒绝检索。
8. 处理结果同步给 Java 业务表。
