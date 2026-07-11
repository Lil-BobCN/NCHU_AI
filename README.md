# 南航 Python RAG 项目交付包

本目录是整理后的 Python RAG 交付版本，路径：

```text
D:\job_code\其他项目\南航项目\python_rag
```

交付包只保留可运行代码、部署配置、必要脚本和交接文档，已排除 `.git`、`.env`、虚拟环境、日志、临时密钥、聊天记录、项目记忆、样例合同和历史材料目录。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `backend/` | FastAPI 后端、RAG 服务、数据库模型、Alembic 迁移、单元测试 |
| `frontend/` | Vue 3 + Vite 前端工程、Nginx 配置、前端容器配置 |
| `deploy/` | Docker Compose 部署文件和离线更新 Dockerfile |
| `scripts/` | 本地启动、批量导入、解析校验、检索基线、备份恢复相关脚本 |
| `.env.example` | 环境变量模板，不包含真实密钥 |
| `docs/` | 本次整理的新交接文档 |

## 文档入口

建议接手人员按下面顺序阅读：

1. [交接总览](docs/00-交接总览.md)
2. [部署文档](docs/01-部署文档.md)
3. [系统说明文档](docs/02-系统说明文档.md)
4. [开发文档](docs/03-开发文档.md)
5. [技术框架文档](docs/04-技术框架文档.md)
6. [接口与数据字典](docs/05-接口与数据字典.md)
7. [运维测试与补充交接](docs/06-运维测试与补充交接.md)
8. [代码结构与文件说明](docs/07-代码结构与文件说明.md)

## 快速启动

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

填写 `.env` 中的模型密钥和生产环境密码：

```text
DEEPSEEK_API_KEY
EMBEDDING_API_KEY
RERANK_API_KEY
JWT_SECRET_KEY
ADMIN_USERNAME
ADMIN_PASSWORD
```

启动基础依赖：

```powershell
docker compose -f deploy/docker-compose.yml up -d postgres redis minio
```

初始化数据库和管理员：

```powershell
$env:PYTHONPATH='backend'
python -m alembic -c backend\alembic.ini upgrade head
python -m app.init_admin
```

启动后端和前端：

```powershell
.\scripts\run-backend-dev.cmd
.\scripts\run-frontend-dev.cmd
```

默认访问地址：

| 服务 | 地址 |
| --- | --- |
| 前端 | `http://127.0.0.1:5173` |
| 后端 | `http://127.0.0.1:8010` |
| API 文档 | `http://127.0.0.1:8010/docs` |
| 健康检查 | `http://127.0.0.1:8010/api/v1/health` |

完整部署步骤请看 [部署文档](docs/01-部署文档.md)。
