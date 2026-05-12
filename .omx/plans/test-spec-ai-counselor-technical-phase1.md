# Test Spec: AI 辅导员系统技术阶段一

日期: 2026-05-12
对应 PRD: `.omx/plans/prd-ai-counselor-technical-phase1.md`
测试目标: 证明 FastAPI + PostgreSQL + Redis + MinIO + Milvus 阶段一底座可启动、可连接、可读写、可定位故障。

## 1. 测试范围

本测试规格只覆盖技术方案第一阶段基础设施，不覆盖完整学生端问答业务。

必须验证：
- FastAPI liveness。
- PostgreSQL round-trip。
- Redis round-trip 和过期行为。
- MinIO bucket/object round-trip。
- Milvus collection/vector/index/search round-trip。
- 失败输出可定位到具体服务和操作。

不验证：
- Flask 原型。
- Qdrant 原型。
- 完整 RAG 问答质量。
- 权限系统、后台 UI、通知、大屏、多终端。

## 2. 推荐验证入口

实现阶段应提供以下二选一或同时提供：

首选：
```powershell
cd backend
docker compose -f docker-compose.phase1.yml up -d
python scripts/smoke_phase1.py
```

兼容当前命名时可用：
```powershell
cd backend
docker compose -f docker-compose.rag.yml up -d
python scripts/smoke_phase1.py
```

若提供 HTTP readiness：
```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod http://localhost:8000/api/v1/readiness
```

## 3. 环境前置

- Docker Desktop 已运行。
- `backend/.env` 已由 `backend/.env.example` 创建。
- `JWT_SECRET_KEY` 已设置为非默认值。
- DashScope API Key 可为空或占位，因为本阶段 smoke 不应依赖真实大模型调用。
- 端口未被占用，或文档说明了替代端口。

## 4. 测试用例

### TC-001: Compose 启动

目的: 验证阶段一服务能一键启动。

步骤:
1. 在 `backend/` 下执行推荐 compose 启动命令。
2. 查看容器状态。
3. 等待健康检查完成。

预期:
- FastAPI、PostgreSQL、Redis、MinIO、Milvus 均为 running。
- 有健康检查的服务显示 healthy。
- 不要求 Flask/Qdrant 容器启动。

失败输出要求:
- 指明失败服务名。
- 指明失败阶段: pull/build/start/healthcheck。

### TC-002: FastAPI Liveness

目的: 验证 API 进程可用。

步骤:
1. 请求 `GET /api/v1/health`。

预期:
- HTTP 200。
- 返回包含 `status`、`service`、`version`、`timestamp`。
- `status` 为 `healthy` 或等价成功值。

### TC-003: PostgreSQL Round-trip

目的: 验证结构化数据库可写、可读、可清理。

步骤:
1. 连接 PostgreSQL。
2. 创建或复用 smoke test 表。
3. 插入唯一 test id 和时间戳。
4. 查询并校验写入内容。
5. 删除测试记录。

预期:
- 插入成功。
- 查询结果与写入值一致。
- 清理成功。

失败输出要求:
- `service=postgres`
- `operation=connect|create_table|insert|select|cleanup`
- 原始异常摘要。

### TC-004: Redis Round-trip + TTL

目的: 验证缓存服务可写、可读，并支持过期。

步骤:
1. 连接 Redis。
2. 写入 smoke key，设置短 TTL。
3. 读取 key，校验 value。
4. 校验 TTL 大于 0。
5. 删除 key，或等待过期后确认消失。

预期:
- value 与写入一致。
- TTL 行为有效。

失败输出要求:
- `service=redis`
- `operation=connect|set|get|ttl|delete`
- 原始异常摘要。

### TC-005: MinIO Object Round-trip

目的: 验证原始文档对象存储可用。

步骤:
1. 连接 MinIO。
2. 创建或复用 smoke bucket。
3. 上传一个小文本对象。
4. 下载对象并校验内容。
5. 删除测试对象。

预期:
- bucket 可访问。
- 上传成功。
- 下载内容与上传内容一致。
- 删除成功。

失败输出要求:
- `service=minio`
- `operation=connect|ensure_bucket|put_object|get_object|delete_object`
- 原始异常摘要。

### TC-006: Milvus Vector Round-trip

目的: 验证正式向量库可用。

测试参数:
- collection: 使用 smoke 专用 collection，避免污染业务 collection。
- dim: 1024。
- metric: 根据配置，一般为 `COSINE` 或 `IP`。
- top_k: 至少 1。

步骤:
1. 连接 Milvus。
2. 创建或复用 smoke collection。
3. 插入一条 1024 维测试向量和 metadata。
4. flush。
5. 如需要，创建索引并 load collection。
6. 使用同一向量执行 TopK search。
7. 校验能检索到测试记录。
8. 清理测试 collection 或测试记录。

预期:
- collection 创建/复用成功。
- 向量插入成功。
- search 返回至少一条结果。
- top result 能匹配测试记录。

失败输出要求:
- `service=milvus`
- `operation=connect|create_collection|insert|flush|create_index|load|search|cleanup`
- 原始异常摘要。

### TC-007: Smoke 汇总报告

目的: 验证验收输出可读、可用于排障。

步骤:
1. 执行完整 smoke 命令。
2. 观察输出和退出码。

预期:
- 全部通过时退出码为 0。
- 输出包含每个服务的 PASS 状态。
- 任一失败时退出码非 0。
- 失败时只要有可能，应继续检查其他服务并汇总结果，而不是第一个失败就完全吞掉上下文。

建议输出格式:
```text
PASS postgres connect/insert/select/cleanup
PASS redis set/get/ttl/delete
PASS minio bucket/put/get/delete
PASS milvus collection/insert/search/cleanup
PASS fastapi health
```

失败示例:
```text
FAIL milvus operation=search error="collection not loaded"
```

## 5. 回归测试

实现阶段至少运行：
```powershell
cd backend
pytest
```

若项目暂时无法完整运行 pytest，需要在最终报告说明失败原因，并至少提供：
- smoke 脚本运行结果。
- `GET /api/v1/health` 结果。
- 受影响 Python 文件的静态导入检查或语法检查。

## 6. 验收门槛

阶段一实现不得标记完成，除非：
- Compose 启动成功。
- FastAPI liveness 成功。
- PostgreSQL smoke 通过。
- Redis smoke 通过。
- MinIO smoke 通过。
- Milvus smoke 通过。
- 文档中的启动命令与实际验证命令一致。
- 验收报告明确说明 Flask/Qdrant 未作为通过条件。

## 7. 风险与专项检查

### Milvus 依赖复杂度

风险: Milvus standalone 可能需要 etcd/minio 等内部依赖，和项目外部 MinIO 产生命名混淆。

检查:
- Docker 服务命名区分 `minio` 与 Milvus 内部依赖。
- 文档说明 Milvus 使用的依赖与业务 MinIO 的边界。

### 端口冲突

风险: 本机已有 PostgreSQL/Redis/MinIO/Milvus 占用端口。

检查:
- Compose 端口映射集中记录。
- smoke 输出连接目标 host/port。

### Qdrant 残留

风险: 代码或文档仍把 Qdrant 作为正式向量库。

检查:
```powershell
rg -n "qdrant|QDRANT|Qdrant" backend docs README.md
```

预期:
- 只允许出现在“历史/迁移参考/旧栈说明”上下文。
- 不允许出现在正式阶段一配置和验收路径中。

### 过度实现

风险: 阶段一实现时提前做完整问答、后台、权限和多端，拉大范围。

检查:
- PRD 中 out-of-scope 不被实现任务吞并。
- 最终报告把需求清单 Phase 1 业务功能列为后续路线。

## 8. 执行交接

给 `$ralph` 的执行提示:
- 先实现 Docker 与配置，再实现 smoke。
- 每完成一个服务就运行局部 smoke，最后运行完整 smoke。
- 不删除 Flask/Qdrant 代码。
- 修改文档必须和实际命令一致。

给 `$team` 的执行提示:
- Docker/配置、后端依赖、smoke、文档可并行。
- 最终由 verifier 统一跑完整 smoke 和 grep 检查。
