# PRD: AI 辅导员系统技术阶段一开发框架

日期: 2026-05-12
负责人上下文: QL 小组
来源: deep-interview 结论、需求清单、技术方案、当前代码仓库
推荐执行入口: `$ralph` 顺序落地；如需并行拆分再切 `$team`

## 1. 目标

阶段一的目标不是一次性完成需求清单里所有业务功能，而是完成技术方案第一阶段的工程底座，使后续知识库问答、管理后台、模型接入、本地部署和运营维护有稳定边界。

本阶段完成后，项目应具备：
- 一条明确的正式后端路线: `backend/` FastAPI。
- 一套本地/私有部署基础设施: PostgreSQL、Redis、MinIO、Milvus。
- 一个可自动验证的 smoke test 验收口径。
- 一份能让非 AI 参与者继续维护的环境、服务、配置和排障说明。

## 2. 背景与当前仓库证据

当前仓库存在两套后端：
- `src/backend/`: 旧 Flask 原型，保留为功能参考，不作为正式阶段一验收对象。
- `backend/`: FastAPI RAG 骨架，是正式迁移方向。

当前差距：
- `backend/docker-compose.rag.yml` 仍是 FastAPI + PostgreSQL + Qdrant + Redis，缺少 Milvus 和 MinIO。
- `backend/app/config.py` 仍有 `qdrant_url`，缺少 Milvus/MinIO 配置契约。
- `backend/app/api/deps.py`、`backend/app/rag/retriever.py`、`backend/scripts/ingest_documents.py` 仍依赖 Qdrant。
- `backend/app/api/v1/health.py` 只有 API liveness，没有覆盖 PostgreSQL、Redis、MinIO、Milvus 的 readiness/smoke。
- 根目录 `docker-compose.yml` 仍服务于旧 Flask + Nginx + Redis 栈。

## 3. 范围

### 3.1 本阶段必须完成

- 建立 FastAPI + Milvus 的正式后端方向。
- 建立 Docker 编排，至少包含 FastAPI、PostgreSQL、Redis、MinIO、Milvus。
- 明确 `.env.example` 环境变量契约。
- 为 PostgreSQL、Redis、MinIO、Milvus 提供自动化 smoke test。
- FastAPI 提供基础 liveness，并能暴露或触发基础设施 readiness/smoke。
- 明确旧 Flask 和 Qdrant 仅作为迁移参考，不进入验收。
- 更新项目文档，说明启动、停止、验证、故障定位和后续开发边界。

### 3.2 本阶段明确不做

- 不完成完整学生端 7x24 智能问答体验。
- 不完成知识库管理 UI。
- 不完成角色权限、审计日志、统计大屏、通知推送、文档生成。
- 不完成企业微信、公众号或多终端上线。
- 不做完整前端框架迁移。
- 不在新栈 smoke test 通过前删除旧 Flask/Qdrant 代码。

## 4. 用户故事

### US-001: 本地/私有部署启动

作为开发和部署人员，我需要用一个明确命令启动阶段一基础设施，以便在无额外人工拼接步骤的情况下进入联调。

验收标准：
- 文档中给出唯一推荐启动命令。
- Docker Compose 能启动 FastAPI、PostgreSQL、Redis、MinIO、Milvus。
- 服务名、端口、volume 和 network 命名可读且稳定。

### US-002: FastAPI 正式后端边界

作为后续开发人员，我需要明确 `backend/` 是正式后端路径，以便避免在 Flask 和 FastAPI 之间重复开发。

验收标准：
- README/架构文档说明 Flask 为原型参考。
- FastAPI 配置中不再把 Qdrant 作为正式向量库。
- Qdrant 相关实现被替换或隔离为迁移参考。

### US-003: Milvus 向量库接入

作为 RAG 开发人员，我需要 Milvus 作为唯一正式向量库，以便后续知识库问答按技术方案落地。

验收标准：
- 配置包含 Milvus host/port/db/collection/dim/metric/index 参数。
- 向量检索抽象或实现面向 Milvus。
- smoke test 能插入 1024 维测试向量并 TopK 检索。

### US-004: MinIO 原始文档存储

作为知识库维护人员，我需要保存原始文档对象，以便后续解析、重建索引和审计可追溯。

验收标准：
- Docker Compose 包含 MinIO。
- 配置包含 endpoint、access key、secret key、bucket。
- smoke test 能创建/使用 bucket，上传、下载、删除测试对象。

### US-005: 基础设施可验证

作为项目负责人，我需要通过自动化 smoke test 判断部署是否真正可用，以便阶段一验收不依赖人工猜测。

验收标准：
- PostgreSQL、Redis、MinIO、Milvus 都有真实 round-trip 验证。
- 任一服务失败时，输出明确服务名和失败操作。
- smoke test 可在本地命令行或 FastAPI readiness 入口触发。

## 5. 功能需求

### 5.1 Docker 编排

建议文件策略：
- 保留根目录 `docker-compose.yml` 作为旧 Flask 原型栈。
- 将正式阶段一编排放在 `backend/docker-compose.rag.yml` 或新增更明确的 `backend/docker-compose.phase1.yml`。
- 文档中标明正式阶段一推荐使用哪一个 compose 文件。

正式阶段一服务：
- `api`: FastAPI。
- `postgres`: PostgreSQL。
- `redis`: Redis。
- `minio`: MinIO。
- `milvus`: Milvus standalone 及其必要依赖。

### 5.2 配置契约

必须整理 `backend/.env.example`，至少覆盖：
- `DATABASE_URL`
- `REDIS_URL`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET`
- `MILVUS_HOST`
- `MILVUS_PORT`
- `MILVUS_DB_NAME`
- `MILVUS_COLLECTION`
- `MILVUS_VECTOR_DIM=1024`
- `MILVUS_METRIC_TYPE`
- `DASHSCOPE_API_KEY`
- `EMBEDDING_MODEL`
- `JWT_SECRET_KEY`

### 5.3 后端服务边界

FastAPI 当前阶段只需要证明框架可用，不需要完成完整业务闭环。

建议端点：
- `GET /api/v1/health`: API liveness，只证明 FastAPI 进程可用。
- `GET /api/v1/readiness`: 检查依赖服务连接状态，可返回分项状态。
- `POST /api/v1/admin/smoke` 或 CLI `python scripts/smoke_phase1.py`: 执行真实 round-trip smoke。

若担心 HTTP smoke 端点被误用，优先使用 CLI smoke 脚本，HTTP readiness 只做轻量连通性检查。

### 5.4 文档与运维

必须更新或新增：
- 阶段一启动说明。
- 环境变量说明。
- 服务端口与容器清单。
- smoke test 使用说明。
- 常见失败原因与定位方式。
- 旧 Flask/Qdrant 迁移边界说明。

## 6. 非功能需求

- 可维护性: 配置集中到 `backend/app/config.py`，避免散落硬编码。
- 可排障: smoke 输出必须分服务、分操作。
- 可回滚: 不删除旧代码，直到新栈通过 smoke gate。
- 可移交: 文档足够让非 AI 参与者完成启动、验证和基础排障。
- 可扩展: 向量库、对象存储、数据库访问边界应支持后续知识库导入和问答服务接入。

## 7. 文件级迁移计划

第一批规划文件：
- `.omx/plans/prd-ai-counselor-technical-phase1.md`
- `.omx/plans/test-spec-ai-counselor-technical-phase1.md`

实施时优先文件：
- `backend/docker-compose.rag.yml` 或新增 `backend/docker-compose.phase1.yml`: 替换/新增 Milvus、MinIO。
- `backend/.env.example`: 增补 Milvus/MinIO 配置。
- `backend/app/config.py`: 从 Qdrant 配置迁移到 Milvus/MinIO 配置。
- `backend/app/api/deps.py`: 替换 Qdrant client 注入，增加 Milvus/MinIO/PostgreSQL/Redis 依赖边界。
- `backend/app/rag/retriever.py`: 改为 Milvus 检索实现或抽象接口。
- `backend/scripts/ingest_documents.py`: 暂不要求完成完整业务导入，但不得继续把 Qdrant 作为正式目标。
- `backend/scripts/smoke_phase1.py`: 新增阶段一 smoke 脚本。
- `backend/app/api/v1/health.py`: 保留 liveness，可新增 readiness。
- `README.md`、`docs/ARCHITECTURE.md`、`docs/FASTAPI-SYSTEM.md`: 更新正式阶段一说明。

## 8. RALPLAN-DR 摘要

### 原则

- 先稳定工程底座，再做业务闭环。
- 正式路径唯一: FastAPI + Milvus。
- 旧系统可参考，不参与验收。
- 验收必须自动化、可复现、可定位。
- 文档和配置优先支持后续运营维护。

### 决策驱动

- 技术方案阶段一要求 Docker、PostgreSQL、Redis、MinIO、Milvus。
- 用户已确认 Milvus 和 FastAPI 是正式方向。
- 当前仓库仍混有 Flask 原型与 Qdrant 实现，需要清晰迁移边界。

### 可选方案

方案 A: 在 `backend/docker-compose.rag.yml` 上直接迁移到 Milvus/MinIO。
- 优点: 文件少，现有 FastAPI 启动习惯保留。
- 风险: 历史 Qdrant 命名残留较多，需要文档同步清理。

方案 B: 新增 `backend/docker-compose.phase1.yml` 作为正式阶段一栈，旧 `docker-compose.rag.yml` 暂留参考。
- 优点: 新旧边界最清晰，风险小。
- 风险: 短期多一个 compose 文件，文档必须写清推荐入口。

推荐: 方案 B。等 FastAPI + Milvus + MinIO smoke gate 稳定后，再决定是否合并或删除旧 Qdrant compose。

## 9. ADR

决策: 当前阶段采用 FastAPI + PostgreSQL + Redis + MinIO + Milvus，旧 Flask/Qdrant 不进入验收。

驱动:
- 用户明确选择 Milvus 和 FastAPI。
- 技术方案第一阶段要求基础设施优先。
- 当前代码存在双系统和 Qdrant 偏差，必须先收敛正式路径。

被拒方案:
- 继续让 Flask 和 FastAPI 双主线并行: 会扩大维护成本并造成验收混乱。
- 当前阶段完成需求清单所有 Phase 1 业务功能: 范围过大，会拖慢基础设施稳定。
- 立即删除旧 Flask/Qdrant: smoke gate 未稳定前会丢失参考行为，迁移风险偏高。

后果:
- 当前阶段主要交付工程框架和可验证部署，不承诺完整学生问答体验。
- 后续业务功能必须在新底座上分阶段规划。

## 10. 执行顺序

1. 新增/调整正式阶段一 Docker Compose。
2. 补齐 `.env.example` 和 `Settings` 配置。
3. 增加 Milvus、MinIO、Redis、PostgreSQL 客户端边界。
4. 编写 smoke 脚本。
5. 增加 readiness/liveness 区分。
6. 更新文档。
7. 运行验证并修复。

## 11. 可用 Agent 类型与后续分工

若用 `$ralph`:
- `executor`: 单线实现 Docker、配置、脚本、文档更新。
- `verifier`: 最终检查 smoke/test/build 证据。
- `architect`: 审核架构边界，确认 Flask/Qdrant 没有进入验收。

若用 `$team`:
- Lane 1 `executor`: Docker Compose 与环境变量。
- Lane 2 `executor`: FastAPI 配置、依赖、readiness。
- Lane 3 `executor`: smoke 脚本。
- Lane 4 `writer`: README/架构/运维文档。
- Lane 5 `verifier`: 验证命令与验收证据。

建议推理强度:
- Docker/配置: medium。
- Milvus/MinIO 客户端与 smoke: high。
- 文档: medium。
- 最终架构审查: high。

## 12. 完成定义

阶段一计划完成的定义:
- 本 PRD 存在。
- 测试规格存在。
- 下一步执行不需要再询问范围问题。

阶段一实现完成的定义:
- 一键启动成功。
- FastAPI liveness 成功。
- PostgreSQL、Redis、MinIO、Milvus smoke 全部成功。
- 文档说明与实际命令一致。
- 当前验收报告明确排除 Flask/Qdrant。
