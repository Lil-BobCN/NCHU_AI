# NCHU AI 助手 - 项目状态文档

> 最后更新: 2026-04-12
> 项目路径: C:\Users\liuqi\Desktop\agentproject\

---

## 一、项目概述

南昌航空大学(NCHU)学工处网站的 AI 智能辅导助手。包含两套**完全独立**的对话系统。

### 系统A：Flask AI 助手（悬浮球）
- 用户在学工处网站上浏览内容时，通过右下角悬浮球打开 AI 对话窗口
- 联网搜索 + 流式输出 + 实时引用渲染
- 基于 Flask Session 的用户认证

### 系统B：FastAPI RAG 系统（独立页面）
- 独立的 RAG 对话页面，使用向量检索增强生成
- 基于 JWT 的用户认证
- PostgreSQL + Qdrant 存储

---

## 二、系统架构

```
浏览器
  ├── file:// 协议访问 NCHU_XGC.html（本地打开）
  └── http://localhost/ 访问 index.html（nginx 服务）

Nginx (端口 80)
  ├── 静态文件: static/ 目录
  ├── API 代理: /api/v1/ → FastAPI RAG (端口 8000) [优先匹配]
  ├── API 代理: /api/ → Flask AI 助手 (端口 5000)
  └── 其他页面: /login, /rag-chat, /admin/users

Flask 后端 (端口 5000) - AI 助手系统（独立）
  ├── 认证: 基于 Flask session cookie
  ├── AI 对话: 调用 DashScope/Qwen API (联网搜索)
  ├── 用户管理: Redis DB 0 存储
  └── SSE 流式响应

FastAPI 后端 (端口 8000) - RAG 系统（独立）
  ├── 认证: JWT Bearer Token
  ├── 对话管理: PostgreSQL
  ├── 向量检索: Qdrant
  └── RAG 增强生成

Redis (端口 6379 DB 0) - Flask 用户存储 + 缓存
Redis (端口 6379 DB 1) - FastAPI 缓存
PostgreSQL (端口 5432) - FastAPI 数据
Qdrant (端口 6333) - 向量数据库
```

---

## 三、关键技术文件

### 前端文件 (static/)
| 文件 | 作用 |
|------|------|
| `index.html` | 主页面（http://localhost/ 返回此文件） |
| `login.html` | 登录/注册页面 |
| `rag-chat.html` | RAG 对话界面（使用 FastAPI） |
| `ai-assistant-widget.js` | AI 助手悬浮球+对话框核心逻辑 |
| `ai-assistant-widget.css` | 悬浮球样式 |
| `config.js` | 前端配置（API 端点、预设问题等） |
| `admin-users.html` | 管理员用户列表页面 |
| `xgc-resources/` | 学工处网站静态资源 |
| `AI_ASSISTANT_IMAGE.svg` | AI 悬浮球图标 |

### Flask 后端 (src/backend/)
| 文件 | 作用 |
|------|------|
| `app/__init__.py` | Flask 应用工厂，初始化配置 |
| `app/auth.py` | 认证逻辑（注册、登录、登出、管理员） |
| `app/routes.py` | API 路由（/api/chat 有 @login_required） |
| `wsgi.py` | Gunicorn WSGI 入口 |

### FastAPI 后端 (backend/app/)
| 文件 | 作用 |
|------|------|
| `main.py` | FastAPI 应用工厂 + CORS/NullOrigin 中间件 |
| `config.py` | Pydantic 配置类 |
| `core/auth.py` | JWT 认证（创建/验证 token） |
| `api/v1/auth.py` | JWT 认证端点 |
| `api/v1/chat.py` | 对话管理 + RAG 对话 |
| `api/v1/rag.py` | 向量检索 |
| `api/deps.py` | 依赖注入（LLM、Embedding、Qdrant 单例） |

### 基础设施
| 文件 | 作用 |
|------|------|
| `docker-compose.yml` | Flask + Redis + Nginx 编排 |
| `backend/docker-compose.rag.yml` | FastAPI + Postgres + Qdrant + Redis 编排 |
| `nginx.conf` | Nginx 反向代理 + 静态文件配置 |
| `Dockerfile` | Flask 容器镜像 |

### 文档
| 文件 | 作用 |
|------|------|
| `README.md` | 项目概览 + 快速启动 |
| `docs/ARCHITECTURE.md` | 系统架构图 |
| `docs/FLASK-SYSTEM.md` | Flask 系统详解 |
| `docs/FASTAPI-SYSTEM.md` | FastAPI 系统详解 |
| `PROJECT_STATE.md` | 本文件 - 开发状态 |

---

## 四、认证系统详解

### Flask Session 认证 (端口 5000)

**用户数据存储**: Redis
- Key: `user:{username}` (JSON: username, email, password_hash, created_at)
- 密码: `hashlib.scrypt` (512 字节)
- Session: Flask `session['user_id']` (HttpOnly cookie)

**认证流程**:
1. `POST /api/auth/register` → 创建用户 → 自动登录
2. `POST /api/auth/login` → 验证密码 → 设置 session
3. `GET /api/auth/me` → 检查 session → 返回用户信息
4. `POST /api/auth/logout` → 清除 session
5. `POST /api/chat` → `@login_required` 检查 session

**关键装饰器**:
- `login_required` (auth.py): 检查 `'user_id' in session`，失败返回 401
- `admin_required` (auth.py): 检查 `user_id` 是否在 `ADMIN_USERS` 环境变量中

### FastAPI JWT 认证 (端口 8000)

**用户数据存储**: PostgreSQL
- 密码: `passlib.scrypt`
- Token: `python-jose` HS256 加密

**认证流程**:
1. `POST /api/v1/auth/register` → PostgreSQL 创建用户
2. `POST /api/v1/auth/login` → 返回 JWT access_token
3. 前端存储 token 到 localStorage
4. 后续请求在 `Authorization: Bearer <token>` 头中携带

---

## 五、Docker 容器状态

| 容器名 | 端口 | 服务 |
|--------|------|------|
| `ai-assistant-api` | 5000 | Flask 后端 |
| `ai-assistant-nginx` | 80, 443 | Nginx 代理 |
| `ai-assistant-redis` | 6379 | Redis |
| `nchu-counselor-api` | 8000 | FastAPI 后端 |
| `nchu-counselor-postgres` | 5432 | PostgreSQL |
| `nchu-counselor-qdrant` | 6333-6334 | Qdrant 向量库 |
| `nchu-counselor-redis` | 6379 | Redis (FastAPI 用) |

---

## 六、已修复的问题

### 6.1 file:// 协议下 CORS 拒绝请求
- **修复**: CORS 配置添加 `null` origin + `NullOriginMiddleware`

### 6.2 Nginx 嵌套 alias 导致 301 重定向
- **修复**: 移除嵌套 location 中的 alias 指令

### 6.3 file:// 下登录跳转错误
- **修复**: 检测 file:// 协议，默认跳转到 http://localhost/

### 6.4 未登录用户可绕过认证对话
- **修复**: 前端改为通过 Flask `/api/chat` 端点发起请求

### 6.5 fetch credentials 不匹配
- **修复**: 所有 fetch 改为 `credentials: 'include'`

### 6.6 静态资源缓存过长
- **修复**: nginx.conf 改为 JS/CSS 1 小时 + must-revalidate

### 6.7 AI 回复需要刷新才能完整显示
- **根因**: 后端在 `[DONE]` 之后才发送引用数据，前端缓冲区未刷空
- **修复**: 后端拦截 `[DONE]`，先发引用再发 `[DONE]`；前端 `fetchEventSource` 在 `done=true` 前处理缓冲区

### 6.8 Nginx 统一代理两个后端
- **修复**: nginx.conf 添加 `/api/v1/` location 代理到 FastAPI

### 6.9 Redis 数据库分离
- **修复**: Flask 使用 DB 0，FastAPI 使用 DB 1

### 6.10 流式过程中实时渲染引用链接
- **修复**: 移除 `isFinal` 对引用转换的限制，后端实时推送引用映射，前端 300ms 节流渲染

### 6.11 Gunicorn worker 超时导致连接中断
- **根因**: Gunicorn 默认 30s 超时，长对话超过后被强制中止
- **修复**: Dockerfile 添加 `--timeout 300 --graceful-timeout 300`

---

## 七、环境变量

### 根目录 .env
```
QWEN_API_KEY=sk-*** (已配置)
QWEN_MODEL=qwen3.5-plus
CORS_ORIGINS=http://localhost,null
SESSION_SECRET_KEY=*** (开发用)
ADMIN_USERS=flaskdemo
```

### backend/.env
```
DASHSCOPE_API_KEY=sk-*** (已配置)
DASHSCOPE_MODEL=qwen3.5-plus
EMBEDDING_MODEL=text-embedding-v3
CORS_ORIGINS=...null (已配置)
JWT_SECRET_KEY=*** (已配置)
DATABASE_URL=postgresql+asyncpg://counselor:***@postgres:5432/counselor_db
```

---

## 八、重要代码模式

### 前端 file:// 协议检测
```javascript
const API_BASE = window.location.protocol === 'file:'
    ? 'http://localhost'
    : window.location.origin;
```

### 登录 URL 构建
```javascript
function getLoginUrl() {
    if (window.location.protocol === 'file:') {
        return 'file:///' + baseDir + 'static/login.html';
    }
    return '/login';
}
```

### 前端认证状态检查
```javascript
// Flask (cookie-based)
const res = await fetch('/api/auth/me', { credentials: 'include' });

// FastAPI (JWT-based)
const res = await fetch(API_BASE + '/auth/me', {
    headers: { 'Authorization': 'Bearer ' + authToken }
});
```

---

## 九、启动方式

### Docker 方式（推荐）
```bash
# 启动 Flask 栈
docker compose up -d

# 启动 FastAPI/RAG 栈
cd backend
docker compose -f docker-compose.rag.yml up -d
```

### 本地开发方式
```bash
# Flask 后端
启动API代理服务器.bat

# 前端静态服务器
启动服务器.bat
```

---

## 十、待办/已知问题

1. **管理员功能**: 仅有用户列表查看功能，无用户编辑/删除
2. **RAG 向量库**: Qdrant 已运行但文档数据待填充
3. **HTTPS**: 当前仅 HTTP，生产环境需要 HTTPS
4. **速率限制**: Flask 有基础 brute-force 保护，FastAPI 无速率限制

---

## 十一、系统独立性说明

两套系统**完全独立**，可同时运行进行对比：

| 维度 | Flask AI 助手 | FastAPI RAG |
|------|--------------|-------------|
| **入口页面** | http://localhost/ | http://localhost/rag-chat |
| **后端端口** | 5000 | 8000 |
| **认证方式** | Session Cookie | JWT Token |
| **用户存储** | Redis DB 0 | PostgreSQL |
| **前端文件** | ai-assistant-widget.js (悬浮球) | rag-chat.html (独立页面) |
| **Docker Compose** | docker-compose.yml | backend/docker-compose.rag.yml |
| **登录页面** | /login (login.html) | rag-chat.html 内置登录弹窗 |
| **AI 能力** | 直接对话 Qwen + 联网搜索 | RAG 检索增强对话 |
