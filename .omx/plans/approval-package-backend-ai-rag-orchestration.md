# 审批包草案：后端 AI/RAG 编排技术路线

日期：2026-05-17
状态：approved by product manager
关联主计划：`.omx/plans/overall-development-plan-ai-counselor-demo.md`

## 决策标题

在继续 Phase 1 前端规划前，先确认后端 AI/RAG 编排技术路线。

## 当前已确认的流程调整

产品经理已同意：

- 暂停继续推进 Phase 1 前端技术栈审批。
- 先补充后端 AI/RAG 编排技术审批包。
- 该审批包必须覆盖 LangGraph、LangChain、LangSmith 或同类可观测方案。

该同意不是具体技术引入审批。最终是否采用某个组件，仍需本审批包完成调研、对比、风险说明和产品经理确认。

## 审批结果

产品经理已于 2026-05-17 同意本审批包的推荐技术路线。

审批证据：用户 stated "我同意此方案"。

## 已批准的推荐方案

- 采用 LangGraph 作为后续 RAG/Agent 工作流编排核心。
- 有限采用 LangChain，仅用于模型适配、retriever/prompt/tool 等局部能力；不让 LangChain 接管 FastAPI API、权限、业务 service、数据库 repository、审计或 SSO。
- LangSmith 不默认进入学校真实数据链路；开发期可以用脱敏/仿真数据调研，真实学校数据阶段必须单独做隐私、部署和成本审批。
- 若 LangSmith 不适合私有化/合规要求，优先调研 Langfuse、OpenTelemetry、Phoenix、Prometheus/Grafana 或自建日志评测方案。
- FastAPI 保持主后端权威；LangGraph 是内部 AI/RAG workflow 编排层，不替代 FastAPI。
- RAG workflow 通过 service 层连接 PostgreSQL、Redis、Milvus、MinIO、Redis Stream，不在 workflow 节点中散落直接数据库/对象存储/向量库操作。

## 边界说明

本审批通过的是后端 AI/RAG 编排技术方向，不代表立即进入运行时代码实现。

真正实现前仍需按阶段继续完成：

- 数据契约审批。
- RAG API contract 审批。
- 数据库 schema/migration 审批。
- Milvus collection/vector schema 审批。
- MinIO 存储结构审批。
- 模型 provider/embedding/rerank 审批。
- 可观测/评测方案审批。

## 背景证据

原始技术方案和开发计划明确包含以下后端路线：

- 后端框架方向：FastAPI + LangChain + LangGraph。
- LangGraph 工作流：用户输入 -> 查询改写 -> 意图识别 -> 加载记忆 -> 三路检索 -> 重排序 -> 答案生成 -> 更新记忆 -> 返回结果+来源。
- Redis 短期会话记忆。
- PostgreSQL 历史会话与结构化数据。
- Milvus 向量检索。
- MinIO 原始文档、解析结果和图片存储。
- Redis Stream 异步解析任务。
- BM25、查询扩展、rerank、HyDE、查询改写等 RAG 增强策略。

## 待调研问题与当前结论

- LangGraph 是否适合作为本项目 RAG/Agent 工作流编排核心。
  - 当前结论：适合，并作为后续 RAG/Agent workflow 编排核心方向。
- LangChain 在项目中应承担哪些职责，哪些职责应由我们自写 service 层完成。
  - 当前结论：LangChain 只承担局部 AI 工具能力；业务边界、权限、数据访问和审计由 FastAPI/service/repository 层负责。
- LangSmith 是否适合当前学校私有化/隐私边界；如果不适合，选择什么可观测和评测替代方案。
  - 当前结论：不默认进入真实数据链路；开发期可用脱敏数据评估，真实数据阶段单独审批。替代方案进入后续调研。
- FastAPI service layer 与 LangGraph workflow 的边界如何划分。
  - 当前结论：FastAPI 对外，service 层管业务，LangGraph 管 AI/RAG 流程。
- RAG 工作流如何连接 PostgreSQL、Redis、Milvus、MinIO、Redis Stream。
  - 当前结论：通过 service 层连接，LangGraph 节点调用 service，不直接散落底层存储操作。
- 哪些能力进入 Demo，哪些能力延期到 Phase 7 或更后阶段。
  - 当前结论：Phase 3 仍为确定性 answer-source adapter；LangGraph/LangChain/RAG 正式接入进入 Phase 7 或经单独审批提前切片。

## 推荐审批包结构

后续正式审批包必须包含：

- 推荐方案。
- 备选方案。
- 为什么推荐。
- 影响范围。
- 数据边界与隐私影响。
- API/UI/数据库/组件影响。
- 风险与回滚。
- 验收方式。
- 需要产品经理确认的问题。
- 审批结果和日期。

## 下一步

在后续进入 RAG 实现前，继续使用 `$autoresearch` 或等价的官方文档调研流程，细化 LangGraph、LangChain、LangSmith/替代观测方案的版本、部署方式、隐私边界和实现细节。
