# Java Internal RAG Service

这是给 Java 后台调用的 Python RAG 内部服务项目。

本项目只负责 RAG 能力：文档解析、切片、向量化、召回、重排、问答生成、引用来源和 RAG 日志。

本项目不负责：前端页面、用户登录、Sa-Token 鉴权、用户/角色/部门 CRUD、Java 后台业务 CRUD。

## 架构边界

```text
前端 -> Java 后台 -> Python RAG internal API
```

Java 负责登录鉴权、部门权限、文档业务记录、会话消息保存，并在调用 Python 时传入 `access_scope`。

Python 负责验证 Java Sa-Token JWT，并根据 Java 传来的范围过滤召回。

## 文档阅读顺序

Java 联调建议按这个顺序看：

1. [Java对接调用流程详版.md](docs/Java对接调用流程详版.md)：按业务场景说明 Java 怎么调用。
2. [Java后端调用接口文档.md](docs/Java后端调用接口文档.md)：接口字段、请求体、响应体契约。
3. [数据库表结构文档.md](docs/数据库表结构文档.md)：Python RAG 表结构和字段归属。
4. [Java-Python-RAG对接方案.md](docs/Java-Python-RAG对接方案.md)：整体架构方案。

## 内部接口

所有 `/internal/rag/*` 接口需要请求头：

```http
Authorization: Bearer <Java Sa-Token JWT>
X-Request-Id: <trace id>
```

接口前缀：`/internal/rag`

主要接口：

```text
GET    /internal/rag/health
GET    /internal/rag/documents/{attach_id}
POST   /internal/rag/documents/process
POST   /internal/rag/documents/{attach_id}/reparse
POST   /internal/rag/documents/{attach_id}/rechunk
DELETE /internal/rag/documents/{attach_id}
GET    /internal/rag/jobs/{job_id}
POST   /internal/rag/conversations
GET    /internal/rag/conversations
GET    /internal/rag/conversations/{conversation_id}/messages
PATCH  /internal/rag/conversations/{conversation_id}
DELETE /internal/rag/conversations/{conversation_id}
POST   /internal/rag/chat/stream
POST   /internal/rag/chat
```

## 部署数据库

远程部署不再启动独立 PostgreSQL。`deploy/docker-compose.remote.yml` 会从 `.env` 读取
`DATABASE_URL`，该地址应指向 Java 服务器现有 PostgreSQL 数据库。

Sa-Token JWT 验签密钥通过 `.env` 的 `SA_TOKEN_JWT_SECRET` 配置，必须与 Java 端
`sa-token.jwt-secret-key` 保持一致。

## 文档权限

Java 上传或发布文档时，需要传文档可见范围：

```text
publish_scope = public   所有人可看
publish_scope = dept     部门可看
publish_scope = private  归属人可看
publish_scope = custom   指定部门/指定人员可看
```

用户提问时，Java 计算当前用户可访问范围，传 `user_context` 和 `access_scope`。

Python 会先过滤可访问文档，再执行 RAG 召回，避免无权限文档进入模型上下文。
