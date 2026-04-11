# 系统A：Flask AI 助手

## 概述

悬浮球式 AI 对话助手，嵌入南昌航空大学学工处网站。用户浏览学工处页面时，可通过右下角悬浮球打开对话窗口。

## 技术栈

- **后端**: Flask + Flask-CORS + Flask-Session
- **AI**: 通义千问 Qwen 3.5 + 联网搜索 (DashScope API)
- **缓存**: Redis DB 0
- **前端**: 原生 JavaScript + CSS（无框架）
- **部署**: Gunicorn + Nginx (Docker)

## 文件清单

| 文件 | 作用 |
|------|------|
| `docker-compose.yml` | Flask + Redis + Nginx 容器编排 |
| `Dockerfile` | Flask 容器镜像构建 |
| `nginx.conf` | Nginx 反向代理 + 静态文件 |
| `requirements.txt` | Python 依赖 |
| `.env` | 环境变量（API Key、Session Secret 等） |
| `src/backend/app/__init__.py` | Flask 应用工厂 |
| `src/backend/app/auth.py` | 认证逻辑（注册、登录、登出、管理员） |
| `src/backend/app/routes.py` | API 路由（`/api/chat` SSE 流式） |
| `src/backend/wsgi.py` | Gunicorn WSGI 入口 |
| `static/ai-assistant-widget.js` | AI 悬浮球 + 对话框核心逻辑 (~4600 行) |
| `static/ai-assistant-widget.css` | 悬浮球样式 |
| `static/config.js` | 前端配置（API 端点、预设问题） |
| `static/index.html` | 主页面 |
| `static/login.html` | 登录/注册页面 |
| `static/admin-users.html` | 管理员用户管理页面 |
| `NCHU_XGC.html` | 原版学工处 HTML（file:// 协议访问用） |
| `static/xgc-resources/` | 学工处网站静态资源（CSS/JS/图片） |

## API 端点

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册（支持邮箱可选） |
| POST | `/api/auth/login` | 登录（设置 session cookie） |
| GET | `/api/auth/me` | 获取当前用户信息 |
| POST | `/api/auth/logout` | 登出 |

### AI 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | AI 对话（SSE 流式，需登录） |
| GET | `/api/config` | 前端配置获取 |
| GET | `/health` | 健康检查 |

## 认证流程

1. `POST /api/auth/register` → Redis 存储用户 → 自动登录
2. `POST /api/auth/login` → 验证密码 → `session['user_id']` (HttpOnly cookie)
3. 后续请求通过 cookie 自动携带 session
4. `@login_required` 装饰器检查 session
5. `@admin_required` 装饰器检查用户是否在 `ADMIN_USERS` 环境变量中

## Docker 启动

```bash
docker compose up -d
```

启动 3 个容器：Flask API、Redis、Nginx。

## 本地开发

```bash
# 启动 Flask 后端
启动API代理服务器.bat

# 启动前端静态文件服务器
启动服务器.bat
```
