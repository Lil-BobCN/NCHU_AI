# 学校 RAG 智能问答系统 - API 接口文档

> 当前版本按现有 FastAPI 代码整理。  
> 后端默认地址：`http://127.0.0.1:8010`  
> API 前缀：`/api/v1`  
> OpenAPI 地址：`http://127.0.0.1:8010/openapi.json`  
> Swagger UI：`http://127.0.0.1:8010/docs`

---

## 1. 通用约定

### 1.1 Base URL

```text
http://127.0.0.1:8010
```

除根路径外，业务接口统一以 `/api/v1` 开头，例如：

```text
http://127.0.0.1:8010/api/v1/documents
```

### 1.2 鉴权

除以下接口外，其他接口都需要管理员 JWT：

- `GET /`
- `GET /api/v1/health`
- `POST /api/v1/auth/login`

鉴权头：

```http
Authorization: Bearer <access_token>
```

调用案例中默认使用：

```bash
BASE="http://127.0.0.1:8010"
TOKEN="<登录接口返回的 access_token>"
```

Windows PowerShell 下建议显式使用 `curl.exe`，避免和 `Invoke-WebRequest` 别名冲突。

### 1.3 成功响应格式

代码中通过 `ok()` 统一返回成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

### 1.4 错误响应格式

当前错误主要由 FastAPI `HTTPException` 和参数校验产生，不会统一包成 `code/message/data`。

业务错误示例：

```json
{
  "detail": "未登录"
}
```

参数校验错误示例：

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "question"],
      "msg": "Field required"
    }
  ]
}
```

常见 HTTP 状态：

| 状态码 | 场景 |
| --- | --- |
| 401 | 未登录、token 无效、账号密码错误 |
| 404 | 文档、任务、会话、QA、评测批次不存在 |
| 413 | 上传文件超过 `MAX_UPLOAD_SIZE_MB` |
| 415 | 不支持的上传文件类型 |
| 422 | 请求体或参数校验失败 |

### 1.5 分页

分页接口通常支持：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | ---: | --- |
| `page` | integer | 1 | 页码，从 1 开始 |
| `page_size` | integer | 20 | 每页数量 |

当前代码未统一限制 `page_size` 最大值，前端或调用方应自行控制。

分页响应：

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

### 1.6 文件类型与状态

上传接口当前允许以下扩展名：

```text
.pdf .doc .docx .xls .xlsx .xlsm .txt .md
.jpg .jpeg .png .bmp .tif .tiff .zip .rar
```

文档状态常见值：

| 状态 | 说明 |
| --- | --- |
| `uploaded` | 已上传，可能尚未处理 |
| `parsed` | 已解析；`.doc/.zip/.rar` 等可能到此为止，不切片 |
| `chunked` | 已切片 |
| `indexed` | 已完成向量化，可参与检索 |
| `failed` | 处理失败 |
| `deleted` | 已逻辑删除 |

任务状态常见值：

```text
pending running succeeded failed canceled
```

---

## 2. 根路径与健康检查

### 2.1 根路径

```http
GET /
```

是否鉴权：否。

用途：确认 FastAPI 应用本身已启动，不检查数据库、Redis、MinIO。

调用案例：

```bash
curl -s "$BASE/"
```

响应示例：

```json
{
  "name": "学校 RAG 智能问答系统",
  "status": "ok"
}
```

### 2.2 健康检查

```http
GET /api/v1/health
```

是否鉴权：否。

用途：检查 API、PostgreSQL、Redis、MinIO 连接状态。

调用案例：

```bash
curl -s "$BASE/api/v1/health"
```

响应示例：

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

如果依赖异常，对应字段会变成 `error: ...`。

---

## 3. 管理员认证

### 3.1 登录

```http
POST /api/v1/auth/login
```

是否鉴权：否。

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `username` | string | 是 | 管理员账号 |
| `password` | string | 是 | 管理员密码 |

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400,
    "admin": {
      "id": "6d99f9bb-7f1d-4e68-8f22-a3f8f1a0a111",
      "username": "admin",
      "display_name": "管理员"
    }
  }
}
```

失败示例：

```json
{
  "detail": "账号或密码错误"
}
```

### 3.2 获取当前管理员

```http
GET /api/v1/auth/me
```

是否鉴权：是。

调用案例：

```bash
curl -s "$BASE/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "6d99f9bb-7f1d-4e68-8f22-a3f8f1a0a111",
    "username": "admin",
    "display_name": "管理员"
  }
}
```

---

## 4. 文档管理

### 4.1 上传文档

```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data
```

是否鉴权：是。

表单字段：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `file` | file | 是 | 无 | 上传文件 |
| `title` | string | 否 | 文件名 | 文档标题 |
| `source_url` | string | 否 | null | 外部来源 URL |
| `auto_process` | boolean | 否 | true | 是否上传后自动解析、切片、向量化 |

实际行为：

- 校验扩展名和大小。
- 上传原始文件到 MinIO。
- 写入 `documents`。
- `preview_url` 和 `download_url` 当前都使用 MinIO 下载 URL。
- `auto_process=true` 时添加后台处理任务，但响应中的 `jobs` 只有 `{job_type,status}`，不包含任务 ID。

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_contract.pdf" \
  -F "title=示例合同" \
  -F "source_url=https://example.com/source/sample_contract.pdf" \
  -F "auto_process=true"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "document": {
      "id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
      "title": "示例合同",
      "file_name": "sample_contract.pdf",
      "file_ext": ".pdf",
      "file_size": 348216,
      "status": "uploaded",
      "source_url": "https://example.com/source/sample_contract.pdf",
      "preview_url": "http://localhost:9002/rag-documents/...",
      "download_url": "http://localhost:9002/rag-documents/...",
      "parse_quality_score": 0,
      "error_message": null,
      "created_at": "2026-06-07T13:30:00.000000+00:00",
      "updated_at": "2026-06-07T13:30:00.000000+00:00"
    },
    "jobs": [
      {
        "job_type": "parse",
        "status": "pending"
      }
    ]
  }
}
```

### 4.2 文档列表

```http
GET /api/v1/documents
```

是否鉴权：是。

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | ---: | --- |
| `keyword` | string | null | 按标题或文件名模糊搜索 |
| `status` | string | null | 按文档状态过滤 |
| `page` | integer | 1 | 页码 |
| `page_size` | integer | 20 | 每页数量 |

调用案例：

```bash
curl -s "$BASE/api/v1/documents?keyword=合同&status=indexed&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
        "title": "示例合同",
        "file_name": "sample_contract.pdf",
        "file_ext": ".pdf",
        "file_size": 348216,
        "status": "indexed",
        "source_url": null,
        "preview_url": "http://localhost:9002/rag-documents/...",
        "download_url": "http://localhost:9002/rag-documents/...",
        "parse_quality_score": 95,
        "error_message": null,
        "created_at": "2026-06-07T13:30:00.000000+00:00",
        "updated_at": "2026-06-07T13:31:00.000000+00:00"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 1
  }
}
```

### 4.3 文档详情

```http
GET /api/v1/documents/{document_id}
```

是否鉴权：是。

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `document_id` | string | 文档 ID |

调用案例：

```bash
curl -s "$BASE/api/v1/documents/0f8b7a1d-0b1d-4a79-b0db-611b11ef0001" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "title": "示例合同",
    "file_name": "sample_contract.pdf",
    "file_ext": ".pdf",
    "file_size": 348216,
    "status": "indexed",
    "source_url": null,
    "preview_url": "http://localhost:9002/rag-documents/...",
    "download_url": "http://localhost:9002/rag-documents/...",
    "parse_quality_score": 95,
    "error_message": null,
    "created_at": "2026-06-07T13:30:00.000000+00:00",
    "updated_at": "2026-06-07T13:31:00.000000+00:00",
    "stats": {
      "chunk_count": 6
    },
    "latest_jobs": [
      {
        "id": "1bb6223d-5f94-4ab8-a313-111111111111",
        "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
        "job_type": "embed",
        "status": "succeeded",
        "progress": 100,
        "message": "向量化完成",
        "error_message": null,
        "created_at": "2026-06-07T13:30:20.000000+00:00"
      }
    ]
  }
}
```

### 4.4 删除文档

```http
DELETE /api/v1/documents/{document_id}
```

是否鉴权：是。

实际行为：逻辑删除，设置 `status=deleted` 和 `deleted_at`。

调用案例：

```bash
curl -s -X DELETE "$BASE/api/v1/documents/0f8b7a1d-0b1d-4a79-b0db-611b11ef0001" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "status": "deleted"
  }
}
```

### 4.5 重新解析

```http
POST /api/v1/documents/{document_id}/reparse
```

是否鉴权：是。

请求体：无。

实际行为：从 MinIO 读取原始文件，后台重新执行完整流水线：解析、切片、向量化。

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/documents/0f8b7a1d-0b1d-4a79-b0db-611b11ef0001/reparse" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "status": "pending"
  }
}
```

### 4.6 重新切片

```http
POST /api/v1/documents/{document_id}/rechunk
```

是否鉴权：是。

请求体：无。

实际行为：基于已有解析结果重新切片，并继续执行向量化。

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/documents/0f8b7a1d-0b1d-4a79-b0db-611b11ef0001/rechunk" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "status": "pending"
  }
}
```

### 4.7 重新向量化

```http
POST /api/v1/documents/{document_id}/reembed
```

是否鉴权：是。

请求体：无。

实际行为：删除该文档已有 `chunk_embeddings`，然后重新向量化当前 active chunks。

前置条件：

- 文档必须已经有解析结果。
- 文档必须已经有 active chunk。
- 如果没有解析结果或没有可向量化切片，后台任务会失败，文档状态会变为 `failed`，错误信息会写入 `error_message` 和最新任务的 `error_message`。

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/documents/0f8b7a1d-0b1d-4a79-b0db-611b11ef0001/reembed" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "status": "pending"
  }
}
```

### 4.8 转换旧版 Office 文档

```http
POST /api/v1/documents/{document_id}/convert-office
```

是否鉴权：是。

请求体：无。

实际行为：仅支持 `.doc` 和 `.xls`。后台读取原文件，转换为 `.docx` 或 `.xlsx` 后创建新的子文档，并继续执行解析、切片、向量化。任务结果会写入 `document_jobs.result`，包含 `converted_document_id`、`converted_file_name`、`converted_preview_url` 等字段。

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "job_type": "convert_office",
    "status": "pending"
  }
}
```

### 4.9 解压导入压缩包

```http
POST /api/v1/documents/{document_id}/extract-archive
```

是否鉴权：是。

请求体：无。

实际行为：仅支持 `.zip` 和 `.rar`。后台按安全策略提取可导入的内部文件，为每个内部文件创建新文档并继续入库。任务结果会写入 `document_jobs.result`，包含 `imported_documents`、`imported_document_ids`、`skipped` 等字段。

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "job_type": "extract_import",
    "status": "pending"
  }
}
```

### 4.10 从文档生成 QA

```http
POST /api/v1/documents/{document_id}/qa-pairs/generate
```

是否鉴权：是。

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | ---: | --- |
| `count` | integer | 10 | 目标生成数量 |
| `auto_enable` | boolean | true | 生成后是否直接启用 |

请求体：无。

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/documents/0f8b7a1d-0b1d-4a79-b0db-611b11ef0001/qa-pairs/generate?count=5&auto_enable=true" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "job_type": "qa_generate",
    "status": "pending"
  }
}
```

### 4.11 获取解析结果

```http
GET /api/v1/documents/{document_id}/parse-result
```

是否鉴权：是。

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `format` | string | `markdown` | `markdown` 返回 `content_md`，其他值返回 `content_text` |

调用案例：

```bash
curl -s "$BASE/api/v1/documents/0f8b7a1d-0b1d-4a79-b0db-611b11ef0001/parse-result?format=markdown" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "format": "markdown",
    "content": "## 第1页\n\n合同正文...",
    "quality_score": 95,
    "parse_meta": {
      "parser": "pymupdf",
      "page_count": 4,
      "ocr_enabled": true
    }
  }
}
```

### 4.12 获取文档切片

```http
GET /api/v1/documents/{document_id}/chunks
```

是否鉴权：是。

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | ---: | --- |
| `page` | integer | 1 | 页码 |
| `page_size` | integer | 20 | 每页数量 |
| `keyword` | string | null | 按 chunk 内容模糊搜索 |

调用案例：

```bash
curl -s "$BASE/api/v1/documents/0f8b7a1d-0b1d-4a79-b0db-611b11ef0001/chunks?page=1&page_size=5&keyword=付款" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": "d50fb469-05a8-4ad0-a53d-222222222222",
        "chunk_no": 1,
        "chunk_type": "text",
        "content": "付款方式为...",
        "char_count": 512,
        "token_count": 512,
        "page_start": 2,
        "page_end": 2,
        "section_path": "付款条款",
        "metadata": {
          "source": "pdf"
        },
        "is_active": true
      }
    ],
    "page": 1,
    "page_size": 5,
    "total": 1
  }
}
```

---

## 5. 任务管理

### 5.1 获取任务详情

```http
GET /api/v1/jobs/{job_id}
```

是否鉴权：是。

实际行为：优先读取 Redis 的 `job:{job_id}:progress`，缓存不存在时读取 PostgreSQL。

调用案例：

```bash
curl -s "$BASE/api/v1/jobs/1bb6223d-5f94-4ab8-a313-111111111111" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "1bb6223d-5f94-4ab8-a313-111111111111",
    "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "job_type": "embed",
    "status": "running",
    "progress": 65,
    "message": "已向量化 30/46",
    "error_message": null
  }
}
```

### 5.2 获取文档任务列表

```http
GET /api/v1/documents/{document_id}/jobs
```

是否鉴权：是。

调用案例：

```bash
curl -s "$BASE/api/v1/documents/0f8b7a1d-0b1d-4a79-b0db-611b11ef0001/jobs" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "id": "1bb6223d-5f94-4ab8-a313-111111111111",
      "job_type": "parse",
      "status": "succeeded",
      "progress": 100,
      "message": "解析完成",
      "error_message": null,
      "created_at": "2026-06-07T13:30:00.000000+00:00"
    }
  ]
}
```

---

## 6. QA 问答对管理

### 6.1 QA 列表

```http
GET /api/v1/qa-pairs
```

是否鉴权：是。

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | ---: | --- |
| `keyword` | string | null | 搜索问题或答案 |
| `status` | string | null | 按状态过滤，常用 `enabled` 或 `disabled` |
| `document_id` | string | null | 按来源文档过滤 |
| `page` | integer | 1 | 页码 |
| `page_size` | integer | 20 | 每页数量 |

调用案例：

```bash
curl -s "$BASE/api/v1/qa-pairs?keyword=报名&status=enabled&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": "8e95d856-fc53-43f3-82fe-333333333333",
        "question": "辅修学士学位报名方式是什么？",
        "answer": "资料中说明报名需要...",
        "status": "enabled",
        "source_document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
        "source_chunk_ids": [],
        "source_url": "http://localhost:9002/rag-documents/...",
        "tags": ["报名"],
        "version": 1,
        "updated_at": "2026-06-07T13:35:00.000000+00:00"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 1
  }
}
```

### 6.2 新增 QA

```http
POST /api/v1/qa-pairs
```

是否鉴权：是。

请求体：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `question` | string | 是 | 无 | 问题 |
| `answer` | string | 是 | 无 | 答案 |
| `status` | string | 否 | `enabled` | 状态 |
| `source_document_id` | string | 否 | null | 来源文档 ID |
| `source_chunk_ids` | string[] | 否 | null | 来源 chunk ID 列表 |
| `tags` | string[] | 否 | null | 标签 |

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/qa-pairs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "辅修学士学位报名方式是什么？",
    "answer": "资料中说明报名需要按通知要求完成报名和缴费。",
    "status": "enabled",
    "source_document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "source_chunk_ids": ["d50fb469-05a8-4ad0-a53d-222222222222"],
    "tags": ["报名", "辅修"]
  }'
```

响应示例：

```json
{ 
  "code": 0,
  "message": "ok",
  "data": {
    "id": "8e95d856-fc53-43f3-82fe-333333333333",
    "question": "辅修学士学位报名方式是什么？",
    "answer": "资料中说明报名需要按通知要求完成报名和缴费。",
    "status": "enabled",
    "source_document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "source_chunk_ids": ["d50fb469-05a8-4ad0-a53d-222222222222"],
    "source_url": "http://localhost:9002/rag-documents/...",
    "tags": ["报名", "辅修"],
    "version": 1,
    "updated_at": "2026-06-07T13:35:00.000000+00:00"
  }
}
```

说明：当前接口只写入 QA 记录，未在该接口中同步创建 QA embedding。

### 6.3 更新 QA

```http
PUT /api/v1/qa-pairs/{qa_pair_id}
```

是否鉴权：是。

请求体字段均可选：

```json
{
  "question": "更新后的问题",
  "answer": "更新后的答案",
  "status": "enabled",
  "tags": ["标签"]
}
```

调用案例：

```bash
curl -s -X PUT "$BASE/api/v1/qa-pairs/8e95d856-fc53-43f3-82fe-333333333333" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"answer":"报名和缴费按学校通知要求执行。","tags":["报名","缴费"]}'
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "8e95d856-fc53-43f3-82fe-333333333333",
    "question": "辅修学士学位报名方式是什么？",
    "answer": "报名和缴费按学校通知要求执行。",
    "status": "enabled",
    "source_document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "source_chunk_ids": [],
    "source_url": "http://localhost:9002/rag-documents/...",
    "tags": ["报名", "缴费"],
    "version": 2,
    "updated_at": "2026-06-07T13:40:00.000000+00:00"
  }
}
```

### 6.4 删除 QA

```http
DELETE /api/v1/qa-pairs/{qa_pair_id}
```

是否鉴权：是。

实际行为：逻辑删除，并把 `status` 改为 `disabled`。

调用案例：

```bash
curl -s -X DELETE "$BASE/api/v1/qa-pairs/8e95d856-fc53-43f3-82fe-333333333333" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "8e95d856-fc53-43f3-82fe-333333333333"
  }
}
```

### 6.5 修改 QA 状态

```http
PATCH /api/v1/qa-pairs/{qa_pair_id}/status
```

是否鉴权：是。

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | string | 是 | 常用 `enabled` 或 `disabled`，当前代码不做枚举校验 |

调用案例：

```bash
curl -s -X PATCH "$BASE/api/v1/qa-pairs/8e95d856-fc53-43f3-82fe-333333333333/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"disabled"}'
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "8e95d856-fc53-43f3-82fe-333333333333",
    "question": "辅修学士学位报名方式是什么？",
    "answer": "报名和缴费按学校通知要求执行。",
    "status": "disabled",
    "source_document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
    "source_chunk_ids": [],
    "source_url": "http://localhost:9002/rag-documents/...",
    "tags": ["报名", "缴费"],
    "version": 2,
    "updated_at": "2026-06-07T13:40:00.000000+00:00"
  }
}
```

---

## 7. 会话管理

### 7.1 创建会话

```http
POST /api/v1/conversations
```

是否鉴权：是。

请求体：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | string | 否 | `新的对话` | 会话标题 |

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/conversations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"辅修报名咨询"}'
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "65f4c1e6-a746-407e-87ff-444444444444",
    "title": "辅修报名咨询",
    "message_count": 0,
    "last_message_at": null,
    "created_at": "2026-06-07T13:45:00.000000+00:00"
  }
}
```

### 7.2 会话列表

```http
GET /api/v1/conversations
```

是否鉴权：是。

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | ---: | --- |
| `page` | integer | 1 | 页码 |
| `page_size` | integer | 20 | 每页数量 |

调用案例：

```bash
curl -s "$BASE/api/v1/conversations?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": "65f4c1e6-a746-407e-87ff-444444444444",
        "title": "辅修报名咨询",
        "message_count": 2,
        "last_message_at": "2026-06-07T13:46:00.000000+00:00",
        "created_at": "2026-06-07T13:45:00.000000+00:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

### 7.3 会话消息列表

```http
GET /api/v1/conversations/{conversation_id}/messages
```

是否鉴权：是。

调用案例：

```bash
curl -s "$BASE/api/v1/conversations/65f4c1e6-a746-407e-87ff-444444444444/messages" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "id": "0c26dbb8-5ef2-447a-8d4a-555555555555",
      "conversation_id": "65f4c1e6-a746-407e-87ff-444444444444",
      "role": "user",
      "content": "辅修学士学位报名与缴费是怎样的？",
      "rewritten_query": "辅修学士学位报名与缴费是怎样的？",
      "retrieval_trace": {},
      "citations": [],
      "suggested_questions": [],
      "created_at": "2026-06-07T13:46:00.000000+00:00"
    },
    {
      "id": "26174fb3-52f1-43db-a760-666666666666",
      "conversation_id": "65f4c1e6-a746-407e-87ff-444444444444",
      "role": "assistant",
      "content": "根据资料，报名与缴费要求为...",
      "rewritten_query": null,
      "retrieval_trace": {
        "raw_query": "辅修学士学位报名与缴费是怎样的？"
      },
      "citations": [
        {
          "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
          "document_title": "辅修通知.docx",
          "page_start": null,
          "page_end": null,
          "section_path": "报名与缴费",
          "url": "http://localhost:9002/rag-documents/..."
        }
      ],
      "suggested_questions": [
        {
          "question": "这个问题对应的原文条款是什么？"
        }
      ],
      "created_at": "2026-06-07T13:46:10.000000+00:00"
    }
  ]
}
```

### 7.4 删除会话

```http
DELETE /api/v1/conversations/{conversation_id}
```

是否鉴权：是。

实际行为：逻辑删除会话，设置 `deleted_at`。

调用案例：

```bash
curl -s -X DELETE "$BASE/api/v1/conversations/65f4c1e6-a746-407e-87ff-444444444444" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "65f4c1e6-a746-407e-87ff-444444444444"
  }
}
```

---

## 8. 聊天问答

### 8.1 流式问答

```http
POST /api/v1/chat/stream
Accept: text/event-stream
```

是否鉴权：是。

请求体：

| 字段 | 类型 | 必填 | 默认值 | 当前实际行为 |
| --- | --- | --- | --- | --- |
| `conversation_id` | string | 否 | null | 传入有效 ID 则追加到已有会话，否则自动创建 |
| `question` | string | 是 | 无 | 用户问题 |
| `top_k` | integer | 否 | 8 | 每路召回候选数量，会传给检索服务并做上限保护 |
| `rerank_top_k` | integer | 否 | 5 | 最终返回给回答模型的上下文数量 |
| `enable_rewrite` | boolean | 否 | true | 是否对多轮追问执行检索查询改写 |
| `enable_suggested_questions` | boolean | 否 | true | 是否生成推荐追问 |

事件类型：

| 事件 | data 字段 |
| --- | --- |
| `message_start` | `conversation_id`、`user_message_id`、`assistant_message_id`、`history_count` |
| `retrieval_start` | `query`、`uses_history` |
| `retrieval` | `recall_count`、`rerank_count` |
| `retrieval_done` | `recall_count`、`rerank_count`、`citation_count` |
| `answer_cache` | `hit`，仅命中答案缓存时出现 |
| `delta` | `content`，按字符输出 |
| `citations` | `citations` |
| `suggested_questions` | `questions` |
| `message_end` | `message_id`、`latency_ms` |

调用案例：

```bash
curl -N -X POST "$BASE/api/v1/chat/stream" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "conversation_id": null,
    "question": "辅修学士学位报名与缴费是怎样的？",
    "enable_suggested_questions": false
  }'
```

SSE 响应示例：

```text
event: message_start
data: {"conversation_id":"65f4c1e6-a746-407e-87ff-444444444444","user_message_id":"0c26dbb8-5ef2-447a-8d4a-555555555555","assistant_message_id":"26174fb3-52f1-43db-a760-666666666666","history_count":0}

event: retrieval_start
data: {"query":"辅修学士学位报名与缴费是怎样的？","uses_history":false}

event: retrieval_done
data: {"recall_count":25,"rerank_count":5,"citation_count":3}

event: delta
data: {"content":"根"}

event: delta
data: {"content":"据"}

event: citations
data: {"citations":[{"document_id":"0f8b7a1d-0b1d-4a79-b0db-611b11ef0001","document_title":"辅修通知.docx","document_name":"辅修通知.docx","chunk_id":"d50fb469-05a8-4ad0-a53d-222222222222","page_start":null,"page_end":null,"section_path":"报名与缴费","url":"http://localhost:9002/rag-documents/..."}]}

event: suggested_questions
data: {"questions":[]}

event: message_end
data: {"message_id":"26174fb3-52f1-43db-a760-666666666666","latency_ms":5654}
```

### 8.2 非流式问答

```http
POST /api/v1/chat
```

是否鉴权：是。

请求体同 `/api/v1/chat/stream`。

注意：当前非流式接口内部复用流式逻辑，但最终只返回 `answer`、`citations`、`suggested_questions`，不返回 conversation/message ID。

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "合同总价是多少？",
    "enable_suggested_questions": true
  }'
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "answer": "根据资料，合同总价为 80000.00 元。",
    "citations": [
      {
        "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
        "document_title": "sample_contract.pdf",
        "document_name": "sample_contract.pdf",
        "chunk_id": "d50fb469-05a8-4ad0-a53d-222222222222",
        "page_start": 1,
        "page_end": 1,
        "section_path": "合同总价",
        "url": "http://localhost:9002/rag-documents/..."
      }
    ],
    "suggested_questions": [
      {
        "question": "这个问题对应的原文条款是什么？"
      }
    ]
  }
}
```

---

## 9. 检索调试

### 9.1 执行检索

```http
POST /api/v1/retrieval/search
```

是否鉴权：是。

请求体：

| 字段 | 类型 | 必填 | 默认值 | 当前实际行为 |
| --- | --- | --- | --- | --- |
| `query` | string | 是 | 无 | 检索问题 |
| `top_k` | integer | 否 | 30 | 每路召回候选数量，会传给向量、关键词、QA 召回 |
| `rerank_top_k` | integer | 否 | 5 | 最终返回条数 |
| `document_ids` | string[] | 否 | null | 限定文档范围 |
| `enable_rewrite` | boolean | 否 | true | 当前检索调试接口不执行改写，保留字段 |
| `enable_qa_recall` | boolean | 否 | true | 是否启用 QA 召回 |
| `enable_keyword_recall` | boolean | 否 | true | 是否启用关键词召回 |
| `enable_vector_recall` | boolean | 否 | true | 是否启用向量召回 |

响应字段：

| 字段 | 说明 |
| --- | --- |
| `raw_query` | 原始查询 |
| `rewritten_query` | 当前等于原始查询 |
| `recall_results` | 向量、关键词、QA 三路召回合并前结果 |
| `rerank_results` | 重排和本地调权后的最终结果 |
| `final_context` | 当前等于 `rerank_results` |
| `citations` | 从最终结果生成的引用来源，最多 5 条 |

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/retrieval/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "合同总价是多少？",
    "rerank_top_k": 5
  }'
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "raw_query": "合同总价是多少？",
    "rewritten_query": "合同总价是多少？",
    "recall_results": [
      {
        "chunk_id": "d50fb469-05a8-4ad0-a53d-222222222222",
        "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
        "document_title": "sample_contract.pdf",
        "document_name": "sample_contract.pdf",
        "content": "合同总价为 80000.00 元...",
        "page_start": 1,
        "page_end": 1,
        "section_path": "合同总价",
        "url": "http://localhost:9002/rag-documents/...",
        "score": 0.92,
        "source": "keyword"
      }
    ],
    "rerank_results": [
      {
        "chunk_id": "d50fb469-05a8-4ad0-a53d-222222222222",
        "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
        "document_title": "sample_contract.pdf",
        "content": "合同总价为 80000.00 元...",
        "rerank_score": 0.98,
        "combined_score": 6.21
      }
    ],
    "final_context": [
      {
        "chunk_id": "d50fb469-05a8-4ad0-a53d-222222222222",
        "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
        "document_title": "sample_contract.pdf",
        "content": "合同总价为 80000.00 元...",
        "rerank_score": 0.98,
        "combined_score": 6.21
      }
    ],
    "citations": [
      {
        "document_id": "0f8b7a1d-0b1d-4a79-b0db-611b11ef0001",
        "document_title": "sample_contract.pdf",
        "document_name": "sample_contract.pdf",
        "chunk_id": "d50fb469-05a8-4ad0-a53d-222222222222",
        "page_start": 1,
        "page_end": 1,
        "section_path": "合同总价",
        "url": "http://localhost:9002/rag-documents/..."
      }
    ]
  }
}
```

### 9.2 检索日志列表

```http
GET /api/v1/retrieval/logs
```

是否鉴权：是。

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | ---: | --- |
| `keyword` | string | null | 按 `raw_query` 模糊搜索 |
| `page` | integer | 1 | 页码 |
| `page_size` | integer | 20 | 每页数量 |

调用案例：

```bash
curl -s "$BASE/api/v1/retrieval/logs?keyword=合同&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": "8d58904f-2f35-45f5-b301-777777777777",
        "raw_query": "合同总价是多少？",
        "rewritten_query": "合同总价是多少？",
        "latency_ms": 5654,
        "created_at": "2026-06-07T13:50:00.000000+00:00"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 1
  }
}
```

### 9.3 检索日志详情

```http
GET /api/v1/retrieval/logs/{log_id}
```

是否鉴权：是。

注意：当前代码在日志不存在时返回 `ok(null)`，不会返回 404。

调用案例：

```bash
curl -s "$BASE/api/v1/retrieval/logs/8d58904f-2f35-45f5-b301-777777777777" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "8d58904f-2f35-45f5-b301-777777777777",
    "raw_query": "合同总价是多少？",
    "rewritten_query": "合同总价是多少？",
    "recall_results": [],
    "rerank_results": [],
    "final_context": [],
    "citations": [],
    "suggested_questions": [],
    "answer": "根据资料，合同总价为 80000.00 元。",
    "latency_ms": 5654
  }
}
```

---

## 10. 评测接口

### 10.1 评测样本列表

```http
GET /api/v1/evaluation/cases
```

是否鉴权：是。

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | ---: | --- |
| `page` | integer | 1 | 页码 |
| `page_size` | integer | 20 | 每页数量 |

调用案例：

```bash
curl -s "$BASE/api/v1/evaluation/cases?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": "893b66d2-9d87-4e2d-9dd1-888888888888",
        "question": "合同总价是多少？",
        "expected_answer": "80000.00 元",
        "expected_document_ids": ["0f8b7a1d-0b1d-4a79-b0db-611b11ef0001"],
        "expected_chunk_ids": [],
        "tags": ["合同", "金额"],
        "difficulty": "easy",
        "is_active": true,
        "created_at": "2026-06-07T13:55:00.000000+00:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

### 10.2 新增评测样本

```http
POST /api/v1/evaluation/cases
```

是否鉴权：是。

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `question` | string | 是 | 测试问题 |
| `expected_answer` | string | 否 | 期望答案 |
| `expected_document_ids` | string[] | 否 | 期望命中文档 ID |
| `expected_chunk_ids` | string[] | 否 | 期望命中 chunk ID |
| `tags` | string[] | 否 | 标签 |
| `difficulty` | string | 否 | 难度 |

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/evaluation/cases" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "合同总价是多少？",
    "expected_answer": "80000.00 元",
    "expected_document_ids": ["0f8b7a1d-0b1d-4a79-b0db-611b11ef0001"],
    "tags": ["合同", "金额"],
    "difficulty": "easy"
  }'
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "893b66d2-9d87-4e2d-9dd1-888888888888",
    "question": "合同总价是多少？",
    "expected_answer": "80000.00 元",
    "expected_document_ids": ["0f8b7a1d-0b1d-4a79-b0db-611b11ef0001"],
    "expected_chunk_ids": [],
    "tags": ["合同", "金额"],
    "difficulty": "easy",
    "is_active": true,
    "created_at": "2026-06-07T13:55:00.000000+00:00"
  }
}
```

### 10.3 创建评测批次

```http
POST /api/v1/evaluation/runs
```

是否鉴权：是。

请求体：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `name` | string | 是 | 无 | 批次名称 |
| `case_ids` | string[] | 否 | null | 指定样本；不传则执行全部 active 样本 |
| `config` | object | 否 | `{}` | 记录配置用，当前评测逻辑只额外保存 |

实际评测逻辑：

- 后台执行。
- 对每个样本调用 `RetrievalService.search(..., top_k=5)`。
- 只计算 `top3_hit_rate`、`top5_hit_rate`、`case_count`。

调用案例：

```bash
curl -s -X POST "$BASE/api/v1/evaluation/runs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "合同检索回归测试",
    "case_ids": ["893b66d2-9d87-4e2d-9dd1-888888888888"],
    "config": {
      "note": "manual run"
    }
  }'
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "run_id": "92e58f7e-2461-4c5a-a1a7-999999999999",
    "status": "running"
  }
}
```

### 10.4 获取评测批次结果

```http
GET /api/v1/evaluation/runs/{run_id}
```

是否鉴权：是。

调用案例：

```bash
curl -s "$BASE/api/v1/evaluation/runs/92e58f7e-2461-4c5a-a1a7-999999999999" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "92e58f7e-2461-4c5a-a1a7-999999999999",
    "name": "合同检索回归测试",
    "status": "succeeded",
    "metrics": {
      "case_count": 1,
      "top3_hit_rate": 1,
      "top5_hit_rate": 1
    },
    "results": [
      {
        "id": "013299f0-b32e-45cc-a4d8-aaaaaaaaaaaa",
        "case_id": "893b66d2-9d87-4e2d-9dd1-888888888888",
        "hit_top3": true,
        "hit_top5": true,
        "failure_reason": null,
        "trace": {
          "raw_query": "合同总价是多少？",
          "rerank_results": []
        }
      }
    ]
  }
}
```

---

## 11. RAG 设置

### 11.1 获取 RAG 设置

```http
GET /api/v1/settings/rag
```

是否鉴权：是。

调用案例：

```bash
curl -s "$BASE/api/v1/settings/rag" \
  -H "Authorization: Bearer $TOKEN"
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "chunk_size": 800,
    "chunk_overlap": 120,
    "vector_top_k": 30,
    "keyword_top_k": 30,
    "qa_top_k": 10,
    "rerank_top_k": 5,
    "similarity_threshold": 0.35,
    "rerank_threshold": 0.45
  }
}
```

### 11.2 更新 RAG 设置

```http
PUT /api/v1/settings/rag
```

是否鉴权：是。

请求体：

| 字段 | 类型 | 必填 |
| --- | --- | --- |
| `chunk_size` | integer | 是 |
| `chunk_overlap` | integer | 是 |
| `vector_top_k` | integer | 是 |
| `keyword_top_k` | integer | 是 |
| `qa_top_k` | integer | 是 |
| `rerank_top_k` | integer | 是 |
| `similarity_threshold` | number | 是 |
| `rerank_threshold` | number | 是 |
| `rerank_enabled` | boolean | 否 |
| `rerank_max_candidates` | integer | 否 |

实际行为：设置会保存到本地 `.cache/rag_settings.json`，后续请求会读取该覆盖配置，响应中 `persisted=true`。

调用案例：

```bash
curl -s -X PUT "$BASE/api/v1/settings/rag" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chunk_size": 800,
    "chunk_overlap": 120,
    "vector_top_k": 30,
    "keyword_top_k": 30,
    "qa_top_k": 10,
    "rerank_top_k": 5,
    "similarity_threshold": 0.35,
    "rerank_threshold": 0.45
  }'
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "chunk_size": 800,
    "chunk_overlap": 120,
    "vector_top_k": 30,
    "keyword_top_k": 30,
    "qa_top_k": 10,
    "rerank_top_k": 5,
    "similarity_threshold": 0.35,
    "rerank_threshold": 0.45,
    "rerank_enabled": true,
    "rerank_max_candidates": 10,
    "persisted": true
  }
}
```

---

## 12. 当前环境变量

按 `.env.example`，主要环境变量如下：

| 环境变量 | 默认或示例 | 说明 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | `your-deepseek-api-key` | 问答模型 key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | 问答模型 base URL |
| `CHAT_MODEL` | `deepseek-v4-flash` | 问答模型 |
| `STREAM_CHAR_DELAY_MS` | `15` | SSE 按字符输出延迟 |
| `EMBEDDING_API_KEY` | `your-dashscope-api-key` | embedding key |
| `EMBEDDING_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | embedding base URL |
| `EMBEDDING_MODEL` | `text-embedding-v4` | embedding 模型 |
| `EMBEDDING_DIMENSION` | `1024` | pgvector 维度 |
| `EMBEDDING_BATCH_SIZE` | `10` | embedding 批量大小 |
| `RERANK_API_KEY` | `your-rerank-api-key` | rerank key |
| `RERANK_BASE_URL` | DashScope text-rerank endpoint | rerank endpoint |
| `RERANK_MODEL` | `qwen3-vl-rerank` | rerank 模型 |
| `RERANK_ENABLED` | `true` | 是否启用远程 rerank |
| `RERANK_MAX_CANDIDATES` | `10` | rerank 候选上限 |
| `RETRIEVAL_CACHE_ENABLED` | `true` | 是否缓存检索结果 |
| `RETRIEVAL_CACHE_TTL_SECONDS` | `1800` | 检索缓存 TTL |
| `ANSWER_CACHE_ENABLED` | `true` | 是否缓存答案 |
| `ANSWER_CACHE_TTL_SECONDS` | `3600` | 答案缓存 TTL |
| `DATABASE_URL` | `postgresql+asyncpg://rag:rag@127.0.0.1:5433/rag` | 数据库连接 |
| `REDIS_URL` | `redis://127.0.0.1:6380/0` | Redis 连接 |
| `MINIO_ENDPOINT` | `127.0.0.1:9002` | MinIO API |
| `MINIO_PUBLIC_BASE_URL` | `http://localhost:9002` | MinIO 对外 URL 根地址 |
| `JWT_SECRET_KEY` | `change-me` | JWT 密钥 |
| `ADMIN_USERNAME` | `admin` | 初始管理员账号 |
| `ADMIN_PASSWORD` | `admin123` | 初始管理员密码 |

---

## 13. 接口实现注意事项

- `/api/v1/chat/stream` 和 `/api/v1/chat` 的 `top_k` 控制每路召回候选数量，`rerank_top_k` 控制最终上下文数量，`enable_rewrite` 控制追问改写。
- `/api/v1/retrieval/search` 的 `top_k`、`rerank_top_k`、`document_ids` 和召回开关已传给检索服务。
- `POST /api/v1/documents/{document_id}/reparse|rechunk|reembed` 当前没有请求体，参数化切片和 embedding 选项尚未实现。
- `reembed` 现在会校验解析结果和 active chunk；不会再把没有解析结果或 0 chunk 的文档标成 `indexed`。
- `POST /api/v1/documents/{document_id}/qa-pairs/generate` 的 `count` 和 `auto_enable` 是 query 参数，不是 JSON body。
- `PUT /api/v1/settings/rag` 持久化到本地 `.cache/rag_settings.json`，返回值中的 `persisted=true` 是预期行为。
- `GET /api/v1/retrieval/logs/{log_id}` 找不到日志时返回 `{"code":0,"message":"ok","data":null}`。
