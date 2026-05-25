---
id: SDAR-0001
title: Backend AI/RAG Orchestration
status: approved
date: 2026-05-17
phase: Backend AI/RAG planning gate before Phase 1 continuation
decision_owner: Product Manager
technical_owner: Codex
decision_type: technical
reversibility: moderate
confidence: medium
supersedes:
  - .omx/plans/approval-package-backend-ai-rag-orchestration.md
superseded_by:
related_files:
  - .omx/plans/overall-development-plan-ai-counselor-demo.md
  - .omx/plans/approval-package-backend-ai-rag-orchestration.md
  - docs/南昌航空学校RAG智能问答系统技术方案(1).docx
  - docs/AI辅导员助手 - 开发计划表.docx
---

# SDAR-0001: 后端 AI/RAG 编排技术路线

## 1. 一句话结论

采用 FastAPI 作为主后端权威边界，LangGraph 作为后续 RAG/Agent workflow 编排核心，LangChain 有限用于模型、retriever、prompt 和 tool 集成，LangSmith 不默认进入真实学校数据链路。

## 2. 需要你统一确认的问题

本决策已由产品经理确认。

审批证据：2026-05-17，用户回复“我同意此方案”。

## 3. 背景与上下文

- 当前阶段：Phase 0 已通过，Phase 1 前端规划前发现后端 AI/RAG 编排路线缺口。
- 当前约束：FastAPI 已是正式后端；学校场景存在私有化、隐私、审计和可维护性要求。
- 已批准的上游决策：Phase 0 baseline、独立主站 Demo 路线、模拟数据标注、SSO 延后。
- 当前问题为什么必须决策：前端对话 UI、来源引用、流式输出、历史会话、RAG API 边界都会受后端 AI/RAG 编排方式影响。

## 4. 决策驱动因素

- 业务目标：支撑学生问答、来源引用、多轮会话和后续知识库能力。
- 技术目标：把 RAG 工作流做成可编排、可插拔、可观测、可回滚的后端能力。
- 合规/隐私目标：避免真实学生数据默认进入第三方 SaaS 链路。
- 成本/部署目标：优先支持本地/私有化部署路径。
- 可维护性目标：保持 FastAPI/service/repository 边界清晰。

## 5. 推荐方案

- FastAPI 对外提供 API、鉴权、权限、schema、审计和错误边界。
- Service layer 承担业务规则、数据访问、会话、知识资源、审计、case/admin/student domain logic。
- LangGraph 承担 AI/RAG workflow 编排：query rewrite、intent routing、memory loading、retrieval orchestration、rerank、answer generation、source citation assembly、workflow state transitions。
- LangChain 只作为局部工具库，用于 model adapter、retriever、prompt/template、tool integration 等。
- LangSmith 只作为开发期可选评估对象；真实学校数据阶段必须重新审批。
- RAG workflow 通过 service 层连接 PostgreSQL、Redis、Milvus、MinIO、Redis Stream，不在 LangGraph node 中散落底层存储操作。

## 6. 备选方案对比

| 方案 | 优点 | 缺点 | 成本 | 风险 | 是否推荐 |
| --- | --- | --- | --- | --- | --- |
| FastAPI + LangGraph + limited LangChain | 工作流清晰，适合有状态 RAG，保留 FastAPI 权威边界 | 需要学习和设计 workflow 边界 | 中 | workflow 设计过度复杂 | 推荐 |
| FastAPI + handwritten pipeline | 依赖少，初期简单 | 后期 query rewrite、memory、rerank、fallback、观测会变乱 | 低到中 | 技术债累积 | 不推荐作为长期路线 |
| LangChain-heavy application | 上手快，生态组件多 | 抽象过重，业务/权限/数据边界容易模糊 | 中 | 学校部署和排错难度上升 | 不推荐 |
| Full custom RAG framework | 完全可控 | 成本高，交付慢 | 高 | Demo 周期失控 | 不推荐 |

## 7. 为什么推荐

原始技术方案明确提出 FastAPI + LangChain + LangGraph。我们的产品流程也不是简单单轮问答，而是需要多步骤、有状态、可观测的 RAG 工作流。LangGraph 适合承载这类流程；FastAPI 保持外部 API 和业务系统边界；LangChain 只做局部工具，避免全栈抽象过重。

## 8. 影响范围

- 前端：对话 UI、来源引用、流式输出、历史会话 API 需要与后端 workflow contract 对齐。
- 后端：新增 LangGraph workflow 层，但不替代 FastAPI/service/repository。
- 数据库：后续 PostgreSQL schema 仍需单独审批。
- API：RAG API contract 仍需单独审批。
- 测试：需要 workflow 单元测试、API 测试、RAG 质量测试和 fallback 测试。
- 部署：LangSmith 或替代观测组件不得默认进入真实数据部署链路。
- 文档：后续所有 RAG 细化方案使用 SDAR 记录。

## 9. 数据边界与合规影响

- 是否涉及真实学生数据：本决策不批准真实学生数据接入。
- 是否涉及学校资源：后续 RAG 会涉及学校资源，但需单独审批。
- 是否涉及第三方服务：LangSmith、模型 provider、embedding/rerank provider 都需单独审批。
- 是否存在数据出域：默认不允许真实学校数据进入未审批第三方链路。
- 脱敏/审计要求：开发期使用仿真或脱敏数据；真实数据阶段必须补隐私、审计、部署审批。

## 10. 风险、缓解与回滚

| 风险 | 严重性 | 缓解方式 | 回滚方式 |
| --- | --- | --- | --- |
| LangGraph workflow 过度复杂 | 中 | Phase 7 前先画清节点和 service 边界 | 回退到 deterministic adapter 或 handwritten minimal pipeline |
| LangChain 抽象污染业务层 | 高 | 限定 LangChain 只在 AI 工具层使用 | 把 LangChain 调用封装到 adapter，替换实现 |
| LangSmith 数据合规不清 | 高 | 不默认进入真实数据链路 | 使用自建日志或私有化可观测替代 |
| RAG 过早进入 Demo | 中 | Phase 3 明确仍为 deterministic answer-source adapter | 配置关闭 RAG，恢复 Phase 3 fallback |

## 11. 验收方式

- 本 SDAR 已记录审批证据。
- 后续 RAG 实现前，必须另行审批 RAG API contract、数据 schema、Milvus schema、MinIO 存储结构、模型 provider 和可观测方案。
- Phase 3 不以 RAG 作为验收目标。

## 12. 非目标

- 本次不实现 LangGraph/LangChain 代码。
- 本次不审批模型 provider、embedding、rerank、LangSmith 真实数据使用。
- 本次不审批数据库 schema、Milvus collection、MinIO bucket 结构。

## 13. 审批结果

- 状态：approved
- 审批日期：2026-05-17
- 审批证据：用户回复“我同意此方案”
- 修改要求：无

## 14. 后续任务

- 下一任务节点：Phase 1 前端技术栈 SDAR 审批。
- 需要新增的计划/测试/代码文件：后续 RAG 细化时新增独立 SDAR。
- 停止规则：任何 RAG 实现超出本决策边界时，必须新增审批包。

## 15. 参考来源

- Local original technical plan: `docs/南昌航空学校RAG智能问答系统技术方案(1).docx`
- Local development plan: `docs/AI辅导员助手 - 开发计划表.docx`
- LangGraph official docs: https://docs.langchain.com/oss/python/langgraph
- LangChain/LangGraph 1.0 release: https://www.langchain.com/blog/langchain-langgraph-1dot0
- LangSmith evaluation docs: https://docs.langchain.com/langsmith/evaluation

