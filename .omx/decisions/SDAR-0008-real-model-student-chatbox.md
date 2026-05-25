---
id: SDAR-0008
title: Real Model Student Chatbox Boundary
status: approved
date: 2026-05-25
phase: Phase 3R Real Model Student Chatbox
decision_owner: Product Manager
technical_owner: Codex
decision_type: model-api-boundary
reversibility: moderate
confidence: medium
supersedes_if_approved:
  - Phase 3 deterministic-answer-only boundary for student Chatbox responses
related_files:
  - .omx/plans/ralplan-ai-counselor-demo-phased-development-consensus.md
  - .omx/plans/overall-development-plan-ai-counselor-demo.md
  - .omx/decisions/SDAR-0006-product-data-contract-boundary.md
  - backend/app/config.py
  - backend/app/api/v1/student.py
  - frontend/src/App.tsx
---

# SDAR-0008: 真实模型学生 Chatbox 边界

## 1. 一句话结论

推荐将 Phase 3 从“确定性 Demo 答案适配器”修订为“真实模型驱动的学生 Chatbox 小闭环”，但必须通过 FastAPI 后端代理调用模型 API，前端不得直接持有或调用模型密钥。

本审批包只批准学生端 Chatbox 的真实模型回复、流式输出和当前 Demo 运行期聊天记录；不批准数据库持久化、RAG/vector/provider 检索链路、真实学生数据、生产 SSO 或真实学校资料接入。

## 2. 背景

原 Phase 3 在共识计划中定义为：

- 学生 Q&A。
- 确定性 answer-source adapter。
- fallback。
- source card。
- conversation UI。

原计划明确将 `model provider`、embedding、vector schema、Milvus、document ingestion 排除在 Phase 3 外。产品经理现在要求：学生端 Chatbox 使用真实模型回复，并补齐流式输出和聊天记录体验。

因此，该变更必须作为 Phase 3 边界修订先审批，再进入实现。

## 3. 方案选项

| 方案 | 描述 | 优点 | 风险 | 回滚 | 结论 |
| --- | --- | --- | --- | --- | --- |
| A. 保持原 Phase 3 确定性 Demo adapter | 继续用固定 Demo 知识匹配和固定回答 | 稳定、测试简单、符合原计划 | 产品真实感弱，不符合最新要求 | 无需变更 | 不推荐 |
| B. 学生端优先：后端代理真实模型 API，独立 Chatbox 页面先行 | 先做学生 Chatbox 独立页面；后端代理真实模型；支持流式输出和当前运行期聊天记录；验收后合并 `/app/student` | 满足真实回复目标；风险集中；可复用到辅导员/教师端；不污染现有首页主线 | 需要新增模型配置、流式接口和错误处理；模型成本与可用性需管理 | 删除 Chatbox 路由和模型代理，保留 Phase 2 | 推荐 |
| C. 学生、辅导员/教师端同时做真实模型 Chat | 同时铺开三类角色的 Chat 页面和后端上下文 | 看起来推进快 | 角色提示词、安全边界、页面结构、验收口径同时展开，风险高 | 回滚面大 | 暂不推荐 |
| D. 前端直接调用模型 API | 浏览器直接调用模型 provider | 实现最快 | 暴露 API Key；绕过 FastAPI 权限/审计/限流；不符合项目后端权威边界 | 需清理密钥和前端调用 | 拒绝 |

## 4. 推荐方案

采用方案 B。

执行顺序：

1. 新增后端模型配置与 FastAPI 代理边界。
2. 新增学生端独立 Chatbox 页面，不立即替换 `/app/student`。
3. 支持真实模型流式输出、停止生成、错误态、重试、新会话和当前运行期聊天记录。
4. 验证通过后，再合并到 `/app/student`。
5. 学生端稳定后，再复用 Chat 组件和后端代理扩展辅导员/教师端。

## 5. 技术边界

### 前端责任

- 渲染学生 Chatbox 页面。
- 发起后端 chat 请求。
- 处理流式 chunk。
- 支持停止生成。
- 展示当前运行期聊天记录。
- 展示错误态、重试态、空状态和加载状态。
- 不存储模型 API Key。

### FastAPI 后端责任

- 持有模型 provider 配置和 API Key。
- 验证学生 session/token。
- 代理调用真实模型 API。
- 将模型输出以流式响应返回前端。
- 管理超时、失败、取消和错误响应。
- 在当前内存态 Demo runtime 中维护聊天消息。

### 本阶段不做

- PostgreSQL 聊天记录持久化。
- RAG/vector/embedding/Milvus 检索。
- 文档 ingestion。
- 真实学生资料。
- 生产 SSO。
- 真实学校资源。
- 辅导员/教师端首轮同时实现。

## 6. 配置影响

当前 `backend/app/config.py` 和 `backend/.env.example` 尚未包含模型 provider 配置。若本审批通过，需要新增后端环境变量：

- `CHAT_MODEL_API_KEY`
- `CHAT_MODEL_NAME`
- `CHAT_MODEL_API_BASE_URL`
- `CHAT_MODEL_TIMEOUT_SECONDS`
- `CHAT_MODEL_SYSTEM_PROMPT`

默认 provider 采用项目文件中已配置的 Qwen 模型 API；不得为本阶段另行引入第二套模型 API 配置。若该 Qwen 配置暴露的是 OpenAI-compatible chat-completions / streaming 形态，则后端代理按该形态实现。

## 7. 验收方式

最小验收路径：

1. 学生 Demo 账号登录成功。
2. 打开独立学生 Chatbox 页面。
3. 输入问题。
4. 前端显示真实模型流式输出。
5. 可以停止生成。
6. 可以开始新会话。
7. 当前运行期内可以看到聊天记录。
8. 模型配置缺失时，后端返回明确错误，前端显示可理解错误态。
9. 前端 build/lint 通过。
10. 后端测试通过。

明确不作为本阶段验收：

- 服务重启后聊天记录仍保留。
- RAG 引用真实知识库。
- 向量检索。
- 真实学校资料问答。
- 生产环境安全审计闭环。

## 8. 风险与缓解

| 风险 | 严重性 | 缓解 |
| --- | --- | --- |
| API Key 泄露 | 高 | 只放后端环境变量，前端只调用 FastAPI |
| 模型输出不稳定 | 中 | 前端展示“AI 生成内容”边界；后端限制系统提示词 |
| 成本不可控 | 中 | 后续实现中加入 max token、timeout、错误处理 |
| 流式接口复杂度上升 | 中 | 先做学生端单一路径，不同时扩展多角色 |
| 与 Phase 6 持久化混淆 | 中 | 明确本阶段只做内存态聊天记录 |
| 与 Phase 7 RAG 混淆 | 高 | 明确真实模型回复不等于 RAG，不声明知识库检索 |

## 9. 回滚方式

如方案不达预期：

- 删除独立 Chatbox 路由和页面。
- 删除后端模型代理 endpoint 和 provider 配置。
- 保留 Phase 2 登录/角色路由成果。
- Phase 3 可回到原 deterministic adapter 路线或重新审批。

## 10. 产品经理需确认

1. 是否批准方案 B：学生端优先，后端代理真实模型 API，独立 Chatbox 页面先行。
模型 API用我们项目文件中已经配置好的qwen模型的api即可，不需要额外配置新的模型API。
2. 是否接受本阶段聊天记录只保留在当前 Demo 运行期，不做数据库持久化。
我同意
3. 是否同意辅导员/教师端不在第一轮同时实现，而是在学生端 Chat engine 验收后复用扩展。
我同意

## 11. 审批记录

Status: `approved`

Product Manager decision:

- Approved on 2026-05-25 by in-file review.
- Approved scope: 方案 B；学生端优先；FastAPI 后端代理真实模型 API；独立 Chatbox 页面先行；本阶段聊天记录仅保留在当前 Demo 运行期；辅导员/教师端在学生端 Chat engine 验收后复用扩展。
- Approval constraint: 使用项目文件中已经配置好的 Qwen 模型 API，不额外配置新的模型 API。
