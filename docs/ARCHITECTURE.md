# 系统架构

## 总体架构

```
                    ┌─────────────────────────────────┐
                    │         浏览器 (Browser)          │
                    │  http://localhost 或 file://      │
                    └──────────┬───────────────────────┘
                               │
                    ┌──────────▼───────────────────────┐
                    │       Nginx (端口 80, 443)         │
                    │  ┌──────────────────────────────┐ │
                    │  │  静态文件: static/ → alias     │ │
                    │  │  /api/v1/  → FastAPI :8000   │ │
                    │  │  /api/     → Flask   :5000   │ │
                    │  │  /login    → login.html       │ │
                    │  │  /rag-chat → rag-chat.html    │ │
                    │  │  /admin/*  → admin-pages      │ │
                    │  └──────────────────────────────┘ │
                    └─────┬──────────────────┬──────────┘
                          │                  │
          ┌───────────────▼──┐    ┌──────────▼───────────────┐
          │  Flask 后端 :5000 │    │  FastAPI 后端 :8000       │
          │  (ai-assistant-api)│   │  (nchu-counselor-api)    │
          │                   │    │                          │
          │  认证: Session    │    │  认证: JWT               │
          │  存储: Redis DB 0 │    │  存储: PostgreSQL        │
          │  AI: Qwen + 搜索  │    │  AI: Qwen + RAG         │
          └───────┬───────────┘    └─────┬────────────────────┘
                  │                      │
          ┌───────▼───────┐    ┌─────────▼─────────┐
          │  Redis DB 0   │    │  PostgreSQL        │
          │  (用户/缓存)   │    │  (用户/对话/文档)   │
          └───────────────┘    │                    │
                               │  Qdrant (向量库)   │
                               │  Redis DB 1 (缓存)  │
                               └────────────────────┘
```

## 两系统独立性

Flask AI 助手和 FastAPI RAG 系统**完全独立**，可分别启动、停止、部署：

| 维度 | 独立项 |
|------|--------|
| **Docker** | 不同的 docker-compose.yml |
| **网络** | 不同的 Docker network |
| **认证** | Flask Session vs JWT |
| **用户** | Redis vs PostgreSQL（各自管理） |
| **数据库** | Redis DB 0 vs DB 1 |
| **前端** | 悬浮球 vs 独立页面 |
| **AI** | 联网搜索 vs RAG 检索 |
| **API** | `/api/` vs `/api/v1/` |

唯一共享点：Nginx 反向代理（属于 Flask 栈），通过 `host.docker.internal:8000` 跨栈代理到 FastAPI。

## 请求流程

### Flask AI 助手流程

```
1. 用户点击悬浮球 → 打开对话框
2. 输入问题 → POST /api/chat (SSE)
3. Nginx 代理到 Flask :5000
4. Flask @login_required 检查 session cookie
5. Flask 调用 DashScope/Qwen API (stream)
6. 流式 SSE 返回给浏览器
7. fetchEventSource 解析 SSE → 实时渲染 Markdown + 引用链接
```

### FastAPI RAG 流程

```
1. 用户打开 /rag-chat → 加载 rag-chat.html
2. 输入问题 → POST /api/v1/chat/ (Bearer Token)
3. Nginx 代理到 FastAPI :8000
4. FastAPI 验证 JWT → 查询 Qdrant 向量库
5. 检索相关文档 → 组装 prompt → 调用 Qwen
6. 返回增强后的 AI 回复
```
