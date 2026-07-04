# Java 对接 Python RAG 调用流程详版

版本：V1.1  
日期：2026-07-02  
适用对象：Java 后端开发、Python RAG 开发、联调测试

## 0. 2026-07-04 联调更新

- Python `/internal/rag/*` 鉴权已统一为 Java Sa-Token JWT：

```http
Authorization: Bearer <Java Sa-Token JWT>
```

- 旧 `X-RAG-Service-Token` 示例属于历史方案，当前联调不用再传。
- Python 远程部署使用 Java 现有 PostgreSQL，`DATABASE_URL` 指向同一个数据库实例。
- 文档处理接口返回的 `job_id` 已修复为 `document_jobs.id`，Java 可直接轮询 `/internal/rag/jobs/{job_id}`。
- 已补齐 Java 需要的文档状态和会话管理接口：`GET /documents/{attach_id}`、`POST/GET/PATCH/DELETE /conversations`、`GET /conversations/{id}/messages`。

## 1. 先看结论

Java 只需要记住一条主线：

```text
前端永远只调 Java
Java 负责业务、鉴权、权限计算、落库
Python 只负责 RAG 内核能力
```

用户问答时：

```text
Java 校验用户 -> Java 计算权限 -> Java 调 Python -> Python 先过滤可访问文档 -> Python 执行 RAG -> Java 保存结果
```

文档入库时：

```text
Java 上传文件 -> Java 写业务表 -> Java 调 Python 建索引 -> Python 解析/切片/向量化 -> Java 查询任务状态并更新业务状态
```

## 2. 服务地址和鉴权

Python RAG 内部接口前缀：

```text
/internal/rag
```

当前远程部署信息：

| 项目 | 当前值 |
| --- | --- |
| 部署目录 | `/app/rag-java-internal` |
| Java 同服务器调用地址 | `http://127.0.0.1:18020/internal/rag` |
| 外部机器调用地址 | `http://47.100.216.222:18020/internal/rag` |
| 服务 Token | 读取服务器 `/app/rag-java-internal/.env` 中的 `RAG_SERVICE_TOKEN` |
| 部署形态 | 轻量版，`OCR_ENABLED=false` |

如果 Java 服务和 Python RAG 在同一台服务器，推荐使用：

```text
RAG_BASE_URL=http://127.0.0.1:18020/internal/rag
```

如果 Java 服务在其他机器，需要先在阿里云安全组放行 TCP `18020`，再使用：

```text
RAG_BASE_URL=http://47.100.216.222:18020/internal/rag
```

所有内部接口都必须带：

```http
X-RAG-Service-Token: <双方约定的服务 Token>
X-Request-Id: <链路追踪 ID，建议传>
```

示例：

```http
POST http://127.0.0.1:18020/internal/rag/chat/stream
Content-Type: application/json
Accept: text/event-stream
X-RAG-Service-Token: xxxxxx
X-Request-Id: 20260701150000001
```

Java 注意：

- 不要把 `X-RAG-Service-Token` 返回给前端。
- 不要让前端直接访问 Python。
- 生产环境 Token 必须从配置中心、环境变量或 Secret 读取。
- 当前远程 Token 不写入本文档；Java 后端从服务器 `.env` 或配置中心读取。
- 当前部署为轻量版，不启用扫描件/图片 OCR；需要 OCR 时需后续部署完整镜像。

## 3. Java 和 Python 的职责边界

### 3.1 Java 负责

| 模块 | Java 职责 |
| --- | --- |
| 用户鉴权 | 登录、退出、Sa-Token 校验 |
| 用户权限 | 用户、角色、部门、数据范围 |
| 文档业务 | 知识库、附件、发布状态、部门权限、人员权限 |
| 会话业务 | 会话创建、重命名、删除、历史列表 |
| 消息业务 | 用户消息、AI 消息、反馈状态、展示字段 |
| 统计审计 | 操作日志、访问日志、业务统计 |
| 调用 Python | 传文件信息、权限范围、会话 ID、问题 |

### 3.2 Python 负责

| 模块 | Python 职责 |
| --- | --- |
| 文档解析 | PDF、Word、Excel、图片、压缩包等解析 |
| 切片 | 文本切片、表格切片、父子切片 |
| 向量化 | chunk embedding、QA embedding |
| 召回 | 向量召回、关键词召回、QA 召回 |
| 重排 | rerank、去重、上下文压缩 |
| 问答 | 多轮改写、答案生成、引用来源 |
| 权限执行 | 根据 Java 传入范围过滤可召回文档 |
| RAG 日志 | retrieval trace、召回结果、最终上下文 |

## 4. 核心字段说明

### 4.1 文档权限字段

Java 发布或同步文档给 Python 时，需要传这些权限字段。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `publish_scope` | string | 是 | 文档可见范围 |
| `publish_dept_id` | string | 部门文档必填 | 发布部门 ID |
| `owner_user_id` | string | 私有文档必填 | 文档归属人 ID |
| `allowed_dept_ids` | string[] | 自定义部门权限时填 | 指定可访问部门 |
| `allowed_user_ids` | string[] | 自定义人员权限时填 | 指定可访问人员 |
| `visible_in_chat` | boolean | 否 | 是否允许进入问答检索 |

`publish_scope` 可选值：

| 值 | 含义 | 典型场景 |
| --- | --- | --- |
| `public` | 所有人可看 | 全校公开政策、公开办事指南 |
| `dept` | 发布部门可看 | 某部门内部资料 |
| `private` | 归属人可看 | 个人私有资料 |
| `custom` | 指定部门/人员可看 | 多部门共享、指定老师可看 |

### 4.2 用户上下文字段

用户提问时，Java 必须传：

```json
{
  "user_context": {
    "user_id": "1001",
    "dept_id": "finance",
    "role_codes": ["student"],
    "data_scope": "dept"
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 当前登录用户 ID |
| `dept_id` | string | 否 | 当前主部门 ID |
| `role_codes` | string[] | 否 | 当前用户角色编码 |
| `data_scope` | string | 否 | Java 数据权限说明，例如 `self`、`dept`、`all` |

Python 不用这些字段判断 Java 角色，只用 `user_id` 匹配私有/指定人员文档，用 `access_scope` 过滤文档范围。

### 4.3 检索权限字段

用户提问时，Java 必须传：

```json
{
  "access_scope": {
    "scope_mode": "dept",
    "allowed_dept_ids": ["finance"],
    "allowed_knowledge_ids": [],
    "allowed_attach_ids": [],
    "deny_attach_ids": []
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `scope_mode` | string | 是 | 本次检索权限模式 |
| `allowed_dept_ids` | string[] | 普通用户建议必填 | 当前用户允许访问的部门范围 |
| `allowed_knowledge_ids` | string[] | 否 | 限制只能查这些知识库 |
| `allowed_attach_ids` | number[] | 否 | 限制或明确授权的 Java 附件 ID |
| `deny_attach_ids` | number[] | 否 | 强制排除的附件 ID |

`scope_mode` 可选值：

| 值 | 作用 | 谁能用 |
| --- | --- | --- |
| `dept` | 公开文档 + 用户部门范围内文档 + 用户本人可见文档 | 普通用户默认 |
| `all_public` | 只查公开文档 | 公开入口或游客入口 |
| `custom` | 自定义部门、知识库、文档范围 | 精细授权场景 |
| `admin_all` | 管理员查全部可检索文档 | Java 确认管理员后才可传 |

## 5. 权限过滤到底怎么生效

用户问问题时，Python 不会直接召回。

Python 会先筛文档：

```text
基础条件：
deleted_at IS NULL
visible_in_chat = true
status = indexed
```

然后按权限过滤。

普通部门用户：

```text
scope_mode = dept

可检索文档 =
public 公开文档
+ publish_scope=dept 且 publish_dept_id 命中 allowed_dept_ids
+ publish_scope=dept 且 allowed_dept_ids 与用户 allowed_dept_ids 有交集
+ publish_scope=private 且 owner_user_id = 当前 user_id
+ publish_scope=custom 且 allowed_user_ids 包含当前 user_id
+ publish_scope=custom 且 allowed_dept_ids 与用户 allowed_dept_ids 有交集
- deny_attach_ids
```

公开入口：

```text
scope_mode = all_public

可检索文档 =
publish_scope = public
```

管理员：

```text
scope_mode = admin_all

可检索文档 =
所有 indexed 且 visible_in_chat=true 的文档
再叠加 allowed_knowledge_ids / allowed_attach_ids / deny_attach_ids
```

重要：

```text
权限过滤发生在 RAG 召回之前。
不是先召回再过滤答案。
```

所以无权限文档不会进入向量召回候选，也不会被模型看到。

## 6. 调用流程一：健康检查

### 6.1 使用场景

Java 启动时、定时巡检时、联调前确认 Python RAG 服务可用。

### 6.2 请求

```http
GET /internal/rag/health
X-RAG-Service-Token: <token>
```

### 6.3 响应

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

### 6.4 Java 处理

- 成功：说明服务和 Token 正常。
- 401：Token 错误。
- 503：Python 没配置 `RAG_SERVICE_TOKEN`。

当前远程可用验证：

```bash
python3 /app/rag-java-internal/deploy/remote_health_check.py
curl http://127.0.0.1:18020/api/v1/readiness
```

`/api/v1/readiness` 成功时会返回 `api/postgres/redis/minio` 全部 `ok`。

## 7. 调用流程二：发布公开文档

### 7.1 场景

这类文档所有用户都能问到，例如全校公开政策、办事指南。

### 7.2 Java 处理步骤

```text
1. Java 校验管理员权限。
2. Java 上传文件到 MinIO。
3. Java 写 knowledge_attach 业务表。
4. Java 设置 publish_scope=public。
5. Java 调 Python /documents/process。
6. Java 保存 Python 返回的 rag_doc_id 和 job_id。
7. Java 轮询任务状态，更新业务表 RAG 状态。
```

当前部署注意：

```text
当前 /documents/process 返回的 jobs[0].job_id 是 Redis 队列任务 ID。
当前 /internal/rag/jobs/{job_id} 查询的是数据库 document_jobs.id。
两者暂未打通，Java 直接用返回的 job_id 轮询可能得到 404。
```

建议 Java 联调前先让 Python 侧修复任务 ID 契约：

```text
1. /documents/process 入队前创建数据库 document_jobs。
2. 接口返回 document_jobs.id。
3. Redis task payload 携带同一个 job_id。
4. worker 更新同一条 document_jobs。
```

在修复前，可以先验证健康检查、文档元数据创建、权限字段同步和问答接口；文档进度轮询暂不作为最小闭环阻塞项。

### 7.3 请求示例

```http
POST /internal/rag/documents/process
Content-Type: application/json
X-RAG-Service-Token: <token>
```

```json
{
  "attach_id": 10001,
  "knowledge_id": "kb_public",
  "doc_id": "doc-10001",
  "publish_scope": "public",
  "publish_dept_id": null,
  "owner_user_id": "admin-1",
  "allowed_dept_ids": [],
  "allowed_user_ids": [],
  "visible_in_chat": true,
  "file_name": "学生办事指南.pdf",
  "file_ext": ".pdf",
  "mime_type": "application/pdf",
  "file_size": 1048576,
  "file_hash": "sha256:xxxx",
  "bucket": "rag-documents",
  "object_key": "knowledge/2026/07/01/学生办事指南.pdf",
  "operator_id": "admin-1",
  "auto_process": true,
  "force": false
}
```

### 7.4 字段重点

| 字段 | 公开文档怎么传 |
| --- | --- |
| `publish_scope` | `public` |
| `publish_dept_id` | 可以为空 |
| `allowed_dept_ids` | 空数组 |
| `allowed_user_ids` | 空数组 |
| `visible_in_chat` | `true` |

## 8. 调用流程三：发布部门文档

### 8.1 场景

这类文档只有某个部门或部门数据范围内用户能查。

### 8.2 请求示例

```json
{
  "attach_id": 10002,
  "knowledge_id": "kb_finance",
  "doc_id": "doc-10002",
  "publish_scope": "dept",
  "publish_dept_id": "finance",
  "owner_user_id": "2001",
  "allowed_dept_ids": [],
  "allowed_user_ids": [],
  "visible_in_chat": true,
  "file_name": "财务报销制度.docx",
  "file_ext": ".docx",
  "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "file_size": 35000,
  "file_hash": "sha256:yyyy",
  "bucket": "rag-documents",
  "object_key": "knowledge/finance/财务报销制度.docx",
  "operator_id": "2001",
  "auto_process": true,
  "force": false
}
```

### 8.3 Java 需要保证

- `publish_dept_id` 是 Java 部门表里的真实部门 ID。
- 用户提问时，Java 计算出的 `allowed_dept_ids` 要能包含该部门 ID，用户才查得到。
- 如果部门有上下级权限，例如校级管理员能看多个部门，Java 应把这些部门都放进 `allowed_dept_ids`。

## 9. 调用流程四：发布指定部门/指定人员文档

### 9.1 多部门共享

```json
{
  "attach_id": 10003,
  "knowledge_id": "kb_shared",
  "doc_id": "doc-10003",
  "publish_scope": "custom",
  "publish_dept_id": "student_affairs",
  "owner_user_id": "3001",
  "allowed_dept_ids": ["student_affairs", "finance"],
  "allowed_user_ids": [],
  "visible_in_chat": true,
  "file_name": "奖助学金联合办理说明.docx",
  "file_ext": ".docx",
  "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "file_size": 42000,
  "file_hash": "sha256:zzzz",
  "bucket": "rag-documents",
  "object_key": "knowledge/shared/奖助学金联合办理说明.docx",
  "operator_id": "3001",
  "auto_process": true,
  "force": false
}
```

### 9.2 指定人员可看

```json
{
  "attach_id": 10004,
  "knowledge_id": "kb_teacher",
  "doc_id": "doc-10004",
  "publish_scope": "custom",
  "publish_dept_id": "student_affairs",
  "owner_user_id": "3001",
  "allowed_dept_ids": [],
  "allowed_user_ids": ["teacher-1001", "teacher-1002"],
  "visible_in_chat": true,
  "file_name": "辅导员内部问答口径.docx",
  "file_ext": ".docx",
  "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "file_size": 28000,
  "file_hash": "sha256:aaaa",
  "bucket": "rag-documents",
  "object_key": "knowledge/teacher/辅导员内部问答口径.docx",
  "operator_id": "3001",
  "auto_process": true,
  "force": false
}
```

### 9.3 仅个人可看

```json
{
  "attach_id": 10005,
  "knowledge_id": "kb_private",
  "doc_id": "doc-10005",
  "publish_scope": "private",
  "publish_dept_id": null,
  "owner_user_id": "teacher-1001",
  "allowed_dept_ids": [],
  "allowed_user_ids": [],
  "visible_in_chat": true,
  "file_name": "个人工作备忘.docx",
  "file_ext": ".docx",
  "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "file_size": 12000,
  "file_hash": "sha256:bbbb",
  "bucket": "rag-documents",
  "object_key": "knowledge/private/个人工作备忘.docx",
  "operator_id": "teacher-1001",
  "auto_process": true,
  "force": false
}
```

## 10. 调用流程五：只修改文档权限

### 10.1 场景

文件内容没有变化，只是 Java 后台把文档从“部门可见”改成“公开可见”，或修改指定人员。

### 10.2 调用方式

继续调用：

```http
POST /internal/rag/documents/process
```

但是：

```json
"auto_process": false
```

### 10.3 请求示例

```json
{
  "attach_id": 10002,
  "knowledge_id": "kb_finance",
  "doc_id": "doc-10002",
  "publish_scope": "public",
  "publish_dept_id": "finance",
  "owner_user_id": "2001",
  "allowed_dept_ids": [],
  "allowed_user_ids": [],
  "visible_in_chat": true,
  "file_name": "财务报销制度.docx",
  "file_ext": ".docx",
  "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "file_size": 35000,
  "file_hash": "sha256:yyyy",
  "bucket": "rag-documents",
  "object_key": "knowledge/finance/财务报销制度.docx",
  "operator_id": "2001",
  "auto_process": false,
  "force": false
}
```

### 10.4 Python 行为

- 如果文件哈希、object key、文件名、大小都没变，只更新权限元数据。
- 已经 `indexed` 的文档会保持 `indexed`。
- 不会重新解析、切片、向量化。

### 10.5 Java 注意

如果文件内容变了，不能只改权限。应该：

```text
auto_process = true
```

让 Python 重新解析切片向量化。

## 11. 调用流程六：禁用问答检索

### 11.1 场景

文档还在 Java 后台可见，但暂时不允许被问答召回。

### 11.2 做法

调用 `/documents/process`，保持文件信息不变，传：

```json
{
  "visible_in_chat": false,
  "auto_process": false
}
```

Python 检索基础条件包含：

```text
visible_in_chat = true
```

所以该文档不会再被召回。

## 12. 调用流程七：删除文档索引

### 12.1 场景

Java 删除文档、禁用文档、撤回发布时调用。

### 12.2 请求

```http
DELETE /internal/rag/documents/{attach_id}
Content-Type: application/json
X-RAG-Service-Token: <token>
```

```json
{
  "operator_id": "admin-1",
  "reason": "document_deleted"
}
```

### 12.3 响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "attach_id": 10002,
    "rag_doc_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "status": "deleted"
  }
}
```

### 12.4 Java 处理

- Java 先改自己的业务状态。
- 再调用 Python 删除 RAG 索引。
- 如果 Python 删除失败，Java 需要记录异常，避免“业务已删但 RAG 仍可召回”。

## 13. 调用流程八：重新解析 / 重新切片

### 13.1 重新解析

适用于文件解析质量不好、解析器升级、原文件重新上传。

```http
POST /internal/rag/documents/{attach_id}/reparse
```

```json
{
  "operator_id": "admin-1",
  "force": true
}
```

### 13.2 重新切片

适用于切片策略调整，但解析原文不变。

```http
POST /internal/rag/documents/{attach_id}/rechunk
```

```json
{
  "operator_id": "admin-1",
  "chunk_config": {}
}
```

当前说明：

- `chunk_config` 是保留字段。
- 当前实际切片参数仍来自 Python 环境配置。

## 14. 调用流程九：查询任务状态

### 14.1 请求

```http
GET /internal/rag/jobs/{job_id}
X-RAG-Service-Token: <token>
```

### 14.2 响应

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

### 14.3 Java 状态映射建议

| Python 状态 | Java 建议状态 |
| --- | --- |
| `pending` | 待处理 |
| `running` | 处理中 |
| `succeeded` | 已入库 |
| `failed` | 处理失败 |
| `skipped` | 已跳过 |

Java 可以：

- 前台轮询。
- 后台定时任务轮询。
- 后续如果需要，也可以增加 Python 回调 Java 的接口。

当前实现特别注意：

- `/internal/rag/jobs/{job_id}` 只认数据库 `document_jobs.id`。
- `/documents/process`、`/reparse`、`/rechunk` 当前返回的是 Redis task id。
- 该契约需要在 Java 正式文档处理联调前修复，否则 Java 轮询会不稳定。

## 15. 调用流程十：普通用户发起问答

### 15.1 Java 处理步骤

```text
1. 前端把问题发给 Java。
2. Java 校验用户登录。
3. Java 获取 user_id、dept_id、role_codes。
4. Java 查询用户数据权限，算出 allowed_dept_ids。
5. Java 创建或读取 chat_session。
6. Java 保存用户消息 chat_message。
7. Java 组装请求，调用 Python /chat/stream。
8. Java 转发 Python SSE 给前端。
9. Java 在 message_end 后保存 AI 消息、引用来源、推荐追问、RAG 日志 ID。
```

### 15.2 请求示例

```http
POST /internal/rag/chat/stream
Content-Type: application/json
Accept: text/event-stream
X-RAG-Service-Token: <token>
```

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

### 15.3 字段解释

| 字段 | Java 怎么传 |
| --- | --- |
| `session_id` | Java 会话表主键，控制多轮上下文 |
| `message_id` | Java 用户消息 ID，方便链路追踪 |
| `question` | 用户原始问题 |
| `user_context.user_id` | 当前登录用户 ID |
| `user_context.dept_id` | 当前主部门 |
| `access_scope.scope_mode` | 普通用户建议 `dept` |
| `access_scope.allowed_dept_ids` | Java 根据用户数据权限算出的部门列表 |
| `options.enable_rewrite` | 建议 `true`，用于多轮追问改写 |

### 15.4 Python 会召回哪些文档

假设用户：

```json
{
  "user_id": "1001",
  "allowed_dept_ids": ["finance"]
}
```

Python 可召回：

```text
public 文档
finance 部门文档
allowed_dept_ids 包含 finance 的 custom 文档
owner_user_id = 1001 的 private/custom 文档
allowed_user_ids 包含 1001 的 custom 文档
```

Python 不会召回：

```text
其他部门 dept 文档
其他人员 private 文档
visible_in_chat=false 的文档
status 不是 indexed 的文档
deleted_at 不为空的文档
deny_attach_ids 里的文档
```

## 16. 调用流程十一：公开入口问答

如果存在未登录或公共入口，只允许查公开资料：

```json
{
  "session_id": "public-session-001",
  "question": "学校办事指南有哪些？",
  "user_context": {
    "user_id": "anonymous",
    "dept_id": null,
    "role_codes": [],
    "data_scope": "public"
  },
  "access_scope": {
    "scope_mode": "all_public",
    "allowed_dept_ids": [],
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

Python 只会查：

```text
publish_scope = public
```

## 17. 调用流程十二：管理员问答

管理员需要查全部资料时：

```json
{
  "session_id": "admin-session-001",
  "question": "统计一下财务和学工相关办事指南有哪些？",
  "user_context": {
    "user_id": "admin-1",
    "dept_id": "school",
    "role_codes": ["system_admin"],
    "data_scope": "all"
  },
  "access_scope": {
    "scope_mode": "admin_all",
    "allowed_dept_ids": [],
    "allowed_knowledge_ids": [],
    "allowed_attach_ids": [],
    "deny_attach_ids": []
  },
  "options": {
    "top_k": 12,
    "rerank_top_k": 6,
    "enable_rewrite": true,
    "enable_suggested_questions": true
  }
}
```

Java 注意：

- 只有 Java 确认用户是管理员后，才允许传 `admin_all`。
- 前端不能直接传 `scope_mode` 给 Python。
- 普通用户不能通过篡改参数获得 `admin_all`。

## 18. 调用流程十三：指定知识库或指定文档问答

### 18.1 限定知识库

```json
{
  "access_scope": {
    "scope_mode": "dept",
    "allowed_dept_ids": ["finance"],
    "allowed_knowledge_ids": ["kb_finance"],
    "allowed_attach_ids": [],
    "deny_attach_ids": []
  }
}
```

含义：

```text
在用户本来有权限的文档里，再限定 knowledge_id = kb_finance
```

### 18.2 限定具体文档

普通模式下传 `allowed_attach_ids`，表示把最终范围缩小到这些附件：

```json
{
  "access_scope": {
    "scope_mode": "dept",
    "allowed_dept_ids": ["finance"],
    "allowed_knowledge_ids": [],
    "allowed_attach_ids": [10001, 10002],
    "deny_attach_ids": []
  }
}
```

适用场景：

- 前端在某个文档详情页里提问。
- 后台调试只看某几篇文档。

### 18.3 精细授权文档

如果 Java 已经算出“这几篇文档明确授权给当前用户”，可用 `custom`：

```json
{
  "access_scope": {
    "scope_mode": "custom",
    "allowed_dept_ids": [],
    "allowed_knowledge_ids": [],
    "allowed_attach_ids": [10003, 10004],
    "deny_attach_ids": []
  }
}
```

## 19. SSE 事件说明

Python `/chat/stream` 返回 SSE。

Java 需要解析并转发给前端。

常见事件：

| 事件 | 含义 | Java 怎么处理 |
| --- | --- | --- |
| `message_start` | 消息开始，返回 Python 会话和消息 ID | 记录链路字段 |
| `retrieval_start` | 开始检索 | 可转发给前端展示状态 |
| `retrieval_done` | 检索完成 | 可记录召回数量 |
| `delta` | 答案增量文本 | 转发给前端打字机 |
| `message_end` | 答案结束 | 保存完整 AI 消息、引用、推荐问题 |
| `error` | 出错 | 保存错误状态并通知前端 |

示例：

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

Java 最少要保存：

```text
session_id
user_message_id
assistant_message_id
answer
citations
retrieval_log_id
model_name
latency_ms
```

## 20. 非流式问答

如果后台任务或测试工具不需要打字机，可以调用：

```http
POST /internal/rag/chat
```

请求体和 `/chat/stream` 一样。

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

## 21. 多轮对话怎么控制

多轮靠 `session_id` 控制。

```text
同一个 session_id -> 同一场对话 -> Python 读取历史上下文
新的 session_id -> 新对话 -> 不带旧历史
```

Java 必须保证：

| 场景 | Java 传什么 |
| --- | --- |
| 新建对话 | 新生成 `chat_session.id` |
| 继续追问 | 继续传同一个 `chat_session.id` |
| 切换历史会话 | 传对应历史会话 ID |
| 删除会话 | Java 业务删除，后续不再传该 ID |

示例：

第一问：

```json
{
  "session_id": "chat-001",
  "question": "奖学金申请条件是什么？"
}
```

追问：

```json
{
  "session_id": "chat-001",
  "question": "那需要准备哪些材料？"
}
```

Python 会结合上一轮“奖学金申请条件”的上下文，把追问理解成“奖学金申请需要准备哪些材料”。

## 22. Java 落库建议

### 22.1 文档业务表建议字段

Java `knowledge_attach` 建议保存：

| 字段 | 说明 |
| --- | --- |
| `id` | Java 附件 ID |
| `kid` | 知识库 ID |
| `doc_id` | 文档业务 ID |
| `doc_name` | 文档名 |
| `oss_bucket` | 文件 bucket |
| `oss_object_key` | 文件 object key |
| `file_hash` | 文件 hash |
| `publish_scope` | `public/dept/private/custom` |
| `publish_dept_id` | 发布部门 |
| `owner_user_id` | 归属人 |
| `allowed_dept_ids` | 指定部门 |
| `allowed_user_ids` | 指定人员 |
| `visible_in_chat` | 是否允许问答检索 |
| `rag_doc_id` | Python RAG 文档 ID |
| `rag_status` | RAG 状态 |
| `rag_error_message` | RAG 错误 |
| `rag_quality_score` | 解析质量 |

### 22.2 会话表建议字段

Java `chat_session` 建议保存：

| 字段 | 说明 |
| --- | --- |
| `id` | Java 会话 ID，同时传给 Python 的 `session_id` |
| `user_id` | 用户 ID |
| `title` | 会话标题 |
| `has_error_feedback` | 是否有回答有误 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### 22.3 消息表建议字段

Java `chat_message` 建议保存：

| 字段 | 说明 |
| --- | --- |
| `id` | Java 消息 ID |
| `session_id` | Java 会话 ID |
| `role` | `user/assistant` |
| `content` | 消息内容 |
| `citations` | 引用来源 JSON |
| `retrieval_log_id` | Python 检索日志 ID |
| `python_conversation_id` | Python 内部会话 ID |
| `python_message_id` | Python 内部消息 ID |
| `model_name` | 模型 |
| `latency_ms` | 耗时 |

## 23. 错误处理建议

| HTTP 状态 | 场景 | Java 处理 |
| --- | --- | --- |
| 401 | Token 错误 | 告警，检查服务配置 |
| 403 | 当前用户无可检索资料 | 返回“当前暂无可检索资料” |
| 404 | 文档或任务不存在 | 检查 Java attach_id/job_id 是否正确 |
| 415 | 不支持文件类型 | 上传时提示用户 |
| 422 | 参数错误 | Java 打日志并修请求体 |
| 503 | Python Token 未配置 | 运维处理 |
| 500 | Python 内部错误 | Java 记录失败，提示稍后重试 |

## 24. 联调检查清单

Java 联调前逐项确认：

- `X-RAG-Service-Token` 配置一致。
- Java 如果和 Python 在同服务器，优先使用 `http://127.0.0.1:18020/internal/rag`。
- Java 如果在外部服务器，确认阿里云安全组已放行 TCP `18020`。
- Java 上传文件后，Python 容器能访问相同 MinIO bucket/object key。
- Java 文档表有 `publish_scope`、`publish_dept_id`、`owner_user_id`、`allowed_dept_ids`、`allowed_user_ids`。
- 普通用户问答传 `scope_mode=dept`。
- 管理员问答才传 `scope_mode=admin_all`。
- 公开入口才传 `scope_mode=all_public`。
- 同一会话追问时 `session_id` 保持不变。
- 权限变更但文件不变时，传 `auto_process=false`。
- 文件内容变更时，传 `auto_process=true`。
- 删除/禁用文档时，调用 `DELETE /internal/rag/documents/{attach_id}` 或 `visible_in_chat=false`。
- 当前远程部署 `OCR_ENABLED=false`，不要用扫描件 PDF 或纯图片文档做第一轮联调样例。
- 文档处理任务轮询前，先修复 `job_id` 契约，或临时绕过任务进度轮询。

## 25. 最小 Java 调用顺序

最小闭环：

```text
1. GET /internal/rag/health
2. POST /internal/rag/documents/process
3. POST /internal/rag/chat/stream
4. DELETE /internal/rag/documents/{attach_id}
```

完成这 4 个接口，Java 和 Python 的主链路就能先跑通。

补充：

```text
GET /internal/rag/jobs/{job_id}
```

建议在修复当前 `job_id` 契约后再纳入正式文档处理闭环验收。
