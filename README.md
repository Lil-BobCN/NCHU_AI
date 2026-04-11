# NCHU AI 助手 - 航宝智辅

南昌航空大学学工处 AI 智能辅导助手，包含两套**完全独立**的对话系统。

> **项目状态说明**
> - **Flask AI 助手（系统A）** 为早期实验原型（Prototype），用于快速验证 AI 对话功能与前端集成方案。
> - **FastAPI RAG（系统B）** 为后续正式版本的开发方向，将逐步替代 Flask 后端，提供更成熟的 RAG 检索增强对话能力。
> - 当前两套系统并存，均可独立运行。后续迭代将以 FastAPI 为主力框架。

---

## 系统架构概览

| 维度 | 系统A：Flask AI 助手 | 系统B：FastAPI RAG |
|------|---------------------|-------------------|
| **状态** | 实验原型（Prototype） | 正式开发方向 |
| **用途** | 悬浮球式 AI 对话（嵌入学工处页面） | RAG 检索增强对话（独立页面） |
| **后端** | Flask (Python) | FastAPI (Python) |
| **端口** | 5000 | 8000 |
| **认证** | Flask Session Cookie | JWT Bearer Token |
| **用户存储** | Redis DB 0 | PostgreSQL |
| **AI 模型** | Qwen 3.5 + 联网搜索 | Qwen 3.5 + RAG 检索 |
| **前端** | ai-assistant-widget.js (悬浮球) | rag-chat.html (独立页面) |
| **Docker Compose** | `docker-compose.yml` | `backend/docker-compose.rag.yml` |
| **登录页** | `/login` (login.html) | rag-chat.html 内置弹窗 |

两套系统共享 Nginx 反向代理（端口 80），通过路径前缀区分：
- `/api/` → Flask (端口 5000)
- `/api/v1/` → FastAPI (端口 8000)

---

## 快速启动

### 前置条件

- [Docker](https://www.docker.com/get-started/) 已安装并运行
- [通义千问 API Key](https://dashscope.console.aliyun.com/)（从阿里云 DashScope 获取）

### 第一步：克隆项目

```bash
git clone https://github.com/your-org/agentproject.git
cd agentproject
```

### 第二步：配置环境变量

```bash
# Flask 栈配置
cp .env.example .env
# 编辑 .env，将 QWEN_API_KEY 替换为你的 API Key
# 将 SESSION_SECRET_KEY 替换为随机字符串

# FastAPI 栈配置（可选，如果需要 RAG 对话）
cp backend/.env.example backend/.env
# 编辑 backend/.env，将 DASHSCOPE_API_KEY 替换为你的 API Key
# 将 JWT_SECRET_KEY 替换为随机字符串
```

### 第三步：启动服务

```bash
# 启动 Flask AI 助手栈（Flask + Redis + Nginx）
docker compose up -d

# （可选）启动 FastAPI RAG 栈
cd backend
docker compose -f docker-compose.rag.yml up -d
cd ..
```

### 第四步：访问

| 页面 | 地址 |
|------|------|
| 学工处主页 + AI 悬浮球 | http://localhost/ |
| 登录/注册 | http://localhost/login |
| RAG 对话（FastAPI） | http://localhost/rag-chat |
| 管理员用户列表 | http://localhost/admin/users |

### 停止服务

```bash
# 停止 Flask 栈
docker compose down

# 停止 FastAPI 栈
cd backend && docker compose -f docker-compose.rag.yml down
```

---

## 项目文件结构

```
agentproject/
├── docker-compose.yml          # Flask 栈编排
├── Dockerfile                  # Flask 容器镜像
├── nginx.conf                  # Nginx 反向代理配置
├── requirements.txt            # Flask 依赖
├── .env                        # Flask 环境变量
├── .gitignore
│
├── static/                     # 前端静态文件（Nginx 直接服务）
│   ├── index.html              # 主页（http://localhost/）
│   ├── login.html              # 登录/注册页面
│   ├── admin-users.html        # 管理员用户列表
│   ├── rag-chat.html           # RAG 对话界面（FastAPI）
│   ├── config.js               # 前端配置（API 端点、预设问题）
│   ├── ai-assistant-widget.js  # AI 悬浮球 + 对话框逻辑
│   ├── ai-assistant-widget.css # AI 悬浮球样式
│   └── xgc-resources/          # 学工处网站静态资源
│
├── NCHU_XGC.html               # 原版学工处 HTML（file:// 协议访问用）
│
├── src/backend/                # Flask 后端
│   ├── app/
│   │   ├── __init__.py         # Flask 应用工厂
│   │   ├── auth.py             # 认证（注册、登录、登出）
│   │   └── routes.py           # API 路由（/api/chat SSE 流式）
│   └── wsgi.py                 # Gunicorn 入口
│
├── backend/                    # FastAPI RAG 系统
│   ├── docker-compose.rag.yml  # FastAPI 栈编排
│   ├── Dockerfile              # FastAPI 容器镜像
│   ├── .env.example            # FastAPI 环境变量模板
│   ├── .env                    # FastAPI 环境变量（不提交到 Git）
│   ├── app/
│   │   ├── main.py             # FastAPI 应用工厂
│   │   ├── config.py           # Pydantic 配置
│   │   ├── core/auth.py        # JWT 认证
│   │   ├── api/v1/auth.py      # 认证端点
│   │   ├── api/v1/chat.py      # RAG 对话端点
│   │   ├── api/v1/rag.py       # 向量检索端点
│   │   └── api/deps.py         # 依赖注入
│   └── ...
│
├── .env.example                # Flask 环境变量模板
│
├── docs/                       # 架构文档
│   ├── ARCHITECTURE.md         # 系统架构图
│   ├── FLASK-SYSTEM.md         # Flask 系统详解
│   └── FASTAPI-SYSTEM.md       # FastAPI 系统详解
│
└── PROJECT_STATE.md            # 项目状态（开发日志）
```

---

## 环境变量

### Flask 栈（根目录 `.env`）

| 变量 | 说明 | 必填 |
|------|------|------|
| `QWEN_API_KEY` | 通义千问 API 密钥 | 是 |
| `SESSION_SECRET_KEY` | Flask session 加密密钥 | 是 |
| `ADMIN_USERS` | 管理员用户名（逗号分隔） | 否 |
| `CORS_ORIGINS` | 允许的 CORS 来源 | 否 |

### FastAPI 栈（`backend/.env`）

| 变量 | 说明 | 必填 |
|------|------|------|
| `DASHSCOPE_API_KEY` | DashScope API 密钥 | 是 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 是 |
| `DATABASE_URL` | PostgreSQL 连接串 | 是 |
| `EMBEDDING_MODEL` | Embedding 模型名 | 否 |

---

## Docker 容器清单

| 容器名 | 端口 | 服务 | 所属栈 |
|--------|------|------|--------|
| `ai-assistant-api` | 5000 | Flask 后端 | Flask |
| `ai-assistant-nginx` | 80, 443 | Nginx 代理 | Flask |
| `ai-assistant-redis` | 6379 | Redis (DB 0) | Flask |
| `nchu-counselor-api` | 8000 | FastAPI 后端 | FastAPI |
| `nchu-counselor-postgres` | 5432 | PostgreSQL | FastAPI |
| `nchu-counselor-qdrant` | 6333-6334 | Qdrant 向量库 | FastAPI |
| `nchu-counselor-redis` | 6379 | Redis (DB 1) | FastAPI |

---

## 许可证

MIT License

Copyright (c) 2026 南昌航空大学学生工作部(处)
