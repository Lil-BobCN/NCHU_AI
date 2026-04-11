# 系统B：FastAPI RAG 系统

## 概述

基于 RAG（检索增强生成）的 AI 对话系统，使用向量数据库检索学校文档，提供更精准的回答。独立页面运行，与 Flask AI 助手完全独立。

## 技术栈

- **后端**: FastAPI + uvicorn
- **AI**: 通义千问 Qwen 3.5 + RAG
- **向量数据库**: Qdrant
- **关系数据库**: PostgreSQL (asyncpg)
- **缓存**: Redis DB 1
- **认证**: JWT (python-jose + passlib)
- **前端**: 原生 HTML/JS（rag-chat.html 内置登录弹窗）
- **部署**: Docker Compose

## 文件清单

| 文件 | 作用 |
|------|------|
| `backend/docker-compose.rag.yml` | FastAPI + PostgreSQL + Qdrant + Redis 编排 |
| `backend/Dockerfile` | FastAPI 容器镜像 |
| `backend/.env` | 环境变量 |
| `backend/app/main.py` | FastAPI 应用工厂 + CORS/NullOrigin 中间件 |
| `backend/app/config.py` | Pydantic 配置类 |
| `backend/app/core/auth.py` | JWT 认证（创建/验证 token） |
| `backend/app/api/v1/auth.py` | JWT 认证端点 |
| `backend/app/api/v1/chat.py` | 对话管理 + RAG 对话 |
| `backend/app/api/v1/rag.py` | 向量检索 |
| `backend/app/api/deps.py` | 依赖注入（LLM、Embedding、Qdrant 单例） |
| `static/rag-chat.html` | RAG 对话前端页面 |

## API 端点

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 注册（PostgreSQL 存储） |
| POST | `/api/v1/auth/login` | 登录 → 返回 JWT access_token |
| GET | `/api/v1/auth/me` | 获取当前用户（Bearer Token） |

### RAG 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat/` | RAG 对话（需 JWT） |
| GET | `/api/v1/chat/` | 获取对话列表 |
| POST | `/api/v1/rag/search` | 向量检索 |

## 认证流程

1. `POST /api/v1/auth/register` → PostgreSQL 创建用户
2. `POST /api/v1/auth/login` → 返回 JWT `access_token`
3. 前端存储 token 到 `localStorage`
4. 后续请求在 `Authorization: Bearer <token>` 头中携带
5. 后端通过 `get_current_user` 依赖验证 token

## Docker 启动

```bash
cd backend
docker compose -f docker-compose.rag.yml up -d
```

启动 4 个容器：FastAPI、PostgreSQL、Qdrant、Redis。

## 数据库分离

- **PostgreSQL**: 用户数据、对话历史、文档
- **Qdrant**: 向量索引（文档嵌入向量）
- **Redis DB 1**: 缓存（与 Flask 的 Redis DB 0 隔离）
