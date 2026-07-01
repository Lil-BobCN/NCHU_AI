# 学校 RAG 智能问答系统

一期 MVP：FastAPI + Vue + PostgreSQL/pgvector + Redis + MinIO。

## 功能范围

- 简单管理员登录
- 文档上传，单文件不超过 100MB
- MinIO 保存原始文件，回答来源展示可点击 URL
- PDF / Word / Excel / Markdown / TXT 基础解析
- 文档分块、向量化、pgvector 入库
- 关键词召回 + 向量召回 + QA 对召回 + rerank
- 流式问答
- 回答末尾返回参考来源：文档名、页码/章节、URL
- 回答后返回 0-3 个推荐追问
- 文档管理、QA 对管理、检索调试、评估接口

## 环境配置

复制环境文件：

```powershell
Copy-Item .env.example .env
```

在 `.env` 中填写：

- `DEEPSEEK_API_KEY`
- `EMBEDDING_API_KEY`
- `RERANK_API_KEY`
- `JWT_SECRET_KEY`

本地开发默认连接：

- PostgreSQL: `127.0.0.1:5433`
- Redis: `127.0.0.1:6380`
- MinIO API: `127.0.0.1:9002`
- MinIO Console: `127.0.0.1:9003`

索引预算相关默认配置：

- `TABLE_CHUNK_ROWS=50`：表格按固定行数切片，不复用普通文本字符窗口。
- `TABLE_FULL_INDEX_MAX_ROWS=500`：超过该行数的表格进入受限索引。
- `TABLE_SAMPLE_ROWS=50`：受限索引时保留字段摘要和前若干行样例。
- `MAX_DOCUMENT_CHUNKS=300`：单文档最多入库切片数。
- `MAX_EMBEDDING_CHARS_PER_DOCUMENT=200000`：单文档默认向量化字符预算。

## 启动基础设施

```powershell
docker compose -f deploy/docker-compose.yml up -d postgres redis minio
```

## 初始化管理员

```powershell
$env:PYTHONPATH='backend'
.\.venv311\Scripts\python.exe -m app.init_admin
```

初始化管理员账号请以本地 `.env` 和部署环境配置为准。

## 数据库迁移

当前已提供 Alembic 脚手架，初始迁移复用 `backend/sql/001_init.sql`。

```powershell
.\.venv311\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
```

## 本地启动后端和前端

后端：

```powershell
.\scripts\run-backend-dev.cmd
```

前端：

```powershell
.\scripts\run-frontend-dev.cmd
```

访问地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8010`
- API 文档：`http://127.0.0.1:8010/docs`

## Docker 完整启动

```powershell
docker compose -f deploy/docker-compose.yml up --build
```

Docker 模式下：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8010`

## 验证命令

后端编译和基础单元测试：

```powershell
.\.venv311\Scripts\python.exe -m compileall backend\app backend\tests
.\.venv311\Scripts\python.exe -m unittest discover -s backend\tests
```

前端构建：

```powershell
D:\Office_procedures\nodejs\npm.cmd --prefix frontend run build
```

## 样本文档

当前样本文档目录：

```text
D:\job_code\其他项目\agent_rag\10个合同
```

## 当前注意事项

- 本机 Windows shell 下，uvicorn/Vite 后台常驻启动不稳定；建议直接运行上面的 `.cmd` 脚本并保持窗口打开。
- `text-embedding-v4` 通过 DashScope OpenAI-compatible API 调用。
- `.env.example` 只保留占位符，不应写入真实密钥。


