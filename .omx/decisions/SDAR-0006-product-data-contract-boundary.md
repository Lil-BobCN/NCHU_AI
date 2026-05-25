---
id: SDAR-0006
title: Product Data Contract Boundary
status: approved
date: 2026-05-19
phase: Contract/Data Boundary Node
decision_owner: Product Manager
technical_owner: Codex
decision_type: data-contract
reversibility: moderate
confidence: medium
supersedes: []
superseded_by:
related_files:
  - .omx/plans/overall-development-plan-ai-counselor-demo.md
  - .omx/plans/ralplan-ai-counselor-demo-phased-development-consensus.md
  - .omx/decisions/SDAR-0003-frontend-ia-route-map.md
  - .omx/decisions/SDAR-0004-frontend-visual-direction-design-tokens.md
  - .omx/decisions/SDAR-0005-frontend-page-structure-interaction-flow.md
  - backend/app/schemas/business.py
  - backend/app/services/business.py
---

# SDAR-0006: 产品数据契约边界

## 1. 一句话结论

推荐采用“最小 Demo 产品契约 + 明确未来扩展边界”的方案。

本节点只批准前后端串联所需的最小领域契约，不批准最终数据库 schema，不引入真实学生数据，不引入真实学校资源，不引入生产 SSO，不实现 RAG/vector/provider。

审计契约采用结构化事件标签和可聚合计数键，不采用自由文本摘要，不记录完整对话正文、用户输入原文、模型输出全文或敏感内容。

审批通过后，Phase 2+ 的 API 连接型 UI 和后端接口实现必须只使用本文件批准的契约字段。

## 2. 当前上下文

已批准：

- `SDAR-0001`：FastAPI 是后端权威边界；LangGraph/LangChain/RAG 属于后续阶段。
- `SDAR-0002`：React + TypeScript + Vite + Ant Design / shadcn-ui。
- `SDAR-0003`：路由图和 API 串联点作为数据契约审批输入。
- `SDAR-0004`：视觉方向和 design token 已通过。
- `SDAR-0005`：页面结构与用户交互顺序已通过。

当前后端已有内存态业务接口和 schema：

- `UserPublic`
- `KnowledgeResponse`
- `ResourceResponse`
- `ConversationResponse`
- `AuditEventResponse`
- `StatsResponse`
- `CounselorAssistRequest/Response`

但这些属于当前技术基线，不等于最终产品契约。当前节点要做的是把 Demo 前后端串联的最小公共语言固定下来。

## 3. 多方案思想对齐

| 方案 | 描述 | 优点 | 风险 | 是否推荐 |
| --- | --- | --- | --- | --- |
| A. 生产级完整契约 | 一次性定义组织、学院、班级、学号、真实学生档案、数据库字段和完整审计 | 看起来完整 | 过早绑定真实数据和数据库 schema；会拖慢 Demo，并越过审批边界 | 不推荐 |
| B. 最小 Demo 契约 + 未来扩展边界 | 只定义 Demo 必需字段，所有真实数据、持久化、RAG、学校资源都标记为未来阶段 | 足够支撑前后端串联；风险低；可回滚；符合阶段门控 | 后续 Phase 6/7 需要扩展契约 | 推荐 |
| C. 直接沿用当前后端 schema | 以前端直接消费现有 `business.py` 字段 | 最快 | 当前字段是内存态实现细节，不完整，且容易把临时实现误当产品契约 | 不推荐 |

推荐 B。

## 4. 契约总原则

- 所有当前数据均为 Demo/模拟数据。
- 不出现真实学号、真实班级、真实学院、真实心理档案、真实咨询记录。
- 前端可以发起请求，但权威写入和角色校验必须在 FastAPI 后端。
- Phase 2-5 允许内存态 Demo 实现；Phase 6 才讨论 PostgreSQL schema 和迁移。
- 审计先定义事件类型、结构化标签和计数键；持久化审计进入 Phase 6。
- RAG/source citation 的真实检索链路进入 Phase 7；Phase 3 只使用确定性答案来源适配器。
- UI 可以展示字段，但不得暗示 Demo 数据是真实学生记录。

## 5. 最小契约清单

### 5.1 `User` / `Role`

用途：
登录、会话展示、角色路由、权限边界。

| 字段 | 类型意图 | 必需 | 公开/私有 | 可见角色 | 数据标签 | 读写责任 | 持久化状态 | 审计 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | string stable id | 是 | 公开给当前会话 | 当前用户、后端权限判断 | Demo seed | 后端生成/返回 | Phase 2 内存/session；Phase 6 PostgreSQL candidate | 登录事件引用 |
| `displayName` | string | 是 | 公开 | 当前用户 | Demo seed | 后端返回 | 同上 | 无 |
| `role` | enum: `student`/`counselor`/`admin` | 是 | 公开 | 当前用户；后端权限 | Demo seed | 后端权威 | 同上 | 权限拒绝可记录 |
| `demoAccount` | boolean | 是 | 公开 | 当前用户 | Demo seed | 后端返回 | 同上 | 无 |
| `sessionState` | enum: `authenticated`/`anonymous` | 是 | 公开 | 当前用户 | 系统生成 | 后端返回 | 浏览器/session + 后端 token | 登录成功/失败 |

明确不包含：

- 真实姓名、真实学号、学院、班级、手机号、身份证、真实心理档案。
- 生产 SSO 身份字段。

### 5.2 `KnowledgeResource`

用途：
学生端来源卡片、管理员 Demo 知识维护、后续 RAG source citation 的前置边界。

| 字段 | 类型意图 | 必需 | 公开/私有 | 可见角色 | 数据标签 | 读写责任 | 持久化状态 | 审计 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | string stable id | 是 | 公开 | student/counselor/admin | Demo seed 或 admin-entered Demo | 后端生成 | Phase 4 内存/seed；Phase 6 PostgreSQL candidate | 写操作引用 |
| `title` | string | 是 | 公开 | student/counselor/admin | Demo | admin 请求，后端写入 | 同上 | create/update |
| `summary` | string | 是 | 公开 | student/counselor/admin | Demo | 后端返回 | 同上 | update |
| `category` | string enum-like | 是 | 公开 | student/counselor/admin | Demo | admin 请求，后端写入 | 同上 | update |
| `tags` | string[] | 否 | 公开 | student/counselor/admin | Demo | admin 请求，后端写入 | 同上 | update |
| `sourceLabel` | string | 是 | 公开 | student/counselor/admin | Demo label | 后端返回 | 同上；Phase 7 可映射对象存储/文档 | update |
| `active` | boolean | 是 | admin 读写；student 只读 active=true | admin/student | Demo | admin 请求，后端写入 | 同上 | enable/disable |

明确不包含：

- 真实学校文档 URL。
- MinIO object key、Milvus vector id、embedding id。
- 原始文件内容和真实文件上传流程。

### 5.3 `Conversation`

用途：
学生问答、会话历史、来源引用、后续辅导员上下文关联。

| 字段 | 类型意图 | 必需 | 公开/私有 | 可见角色 | 数据标签 | 读写责任 | 持久化状态 | 审计 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | string stable id | 是 | 公开给拥有者/授权角色 | student owner, counselor/admin later | Demo conversation | 后端生成 | Phase 3 内存；Phase 6 PostgreSQL candidate | question event |
| `ownerUserId` | string | 是 | 私有，不在普通 UI 强展示 | owner/counselor/admin | Demo | 后端权威 | 同上 | 访问控制引用 |
| `title` | string | 是 | 公开给授权角色 | owner/counselor/admin | Demo/user-entered Demo | 前端请求，后端写入 | 同上 | update optional |
| `turns` | array of message turns | 是 | 公开给授权角色 | owner/counselor/admin | Demo/user-entered + system-generated | student 写 question；backend 写 answer | 同上 | question/answer event |
| `fallbackState` | enum: `answered`/`fallback`/`crisis` | 是 | 公开 | owner/counselor/admin | system-generated Demo | 后端生成 | 同上 | fallback/crisis event |
| `sourceResourceIds` | string[] | 否 | 公开 | owner/counselor/admin | Demo | 后端生成 | 同上 | source hit event |
| `createdAt` / `updatedAt` | datetime | 是 | 公开 | authorized roles | system-generated | 后端生成 | 同上 | 无 |

`turns` 最小字段：

| 字段 | 类型意图 | 必需 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | message id |
| `role` | enum: `student`/`assistant` | 是 | 不使用真实人员姓名 |
| `content` | string | 是 | Demo 对话内容 |
| `createdAt` | datetime | 是 | 后端生成 |
| `resourceIds` | string[] | 否 | 指向 `KnowledgeResource` |

明确不包含：

- 真实咨询记录。
- 真实心理状态评估。
- 模型 prompt、embedding、token usage。

### 5.4 `CounselorCase`

用途：
辅导员工作台案例列表/详情、建议性辅助输出、状态更新。

| 字段 | 类型意图 | 必需 | 公开/私有 | 可见角色 | 数据标签 | 读写责任 | 持久化状态 | 审计 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | string stable id | 是 | 公开给 counselor/admin | counselor/admin | simulated case | 后端生成 | Phase 5 内存/seed；Phase 6 PostgreSQL candidate | status/action update |
| `studentLabel` | string | 是 | 公开给 counselor/admin | counselor/admin | simulated label, not real student | 后端 seed | 同上 | 无 |
| `topic` | string | 是 | 公开 | counselor/admin | simulated | 后端 seed 或系统生成 | 同上 | 无 |
| `status` | enum: `new`/`reviewing`/`follow_up`/`closed` | 是 | 公开 | counselor/admin | simulated/system | counselor 请求，后端写入 | 同上 | required |
| `riskLevel` | enum: `low`/`medium`/`high`/`crisis` | 是 | 公开 | counselor/admin | system-generated Demo | 后端生成 | 同上 | required when changed |
| `summary` | string | 是 | 公开 | counselor/admin | simulated/system | 后端生成 | 同上 | 无 |
| `suggestedAction` | string | 是 | 公开 | counselor/admin | advisory system-generated Demo | 后端生成 | 同上 | assistance event |
| `linkedConversationIds` | string[] | 否 | 公开给 counselor/admin | counselor/admin | Demo | 后端关联 | 同上 | access/update |

边界：

- `suggestedAction` 必须标记为“辅助建议”，不得暗示自动决策。
- `studentLabel` 只能是模拟标签，例如“学生 A”或“Demo Student 01”。

### 5.5 `AuditEvent`

用途：
登录、知识维护、辅导员案例动作、Demo reset、权限拒绝和后续合规追踪。

| 字段 | 类型意图 | 必需 | 公开/私有 | 可见角色 | 数据标签 | 读写责任 | 持久化状态 | 审计 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | string stable id | 是 | admin only | admin | system-generated Demo | 后端生成 | Phase 2-5 log/in-memory；Phase 6 durable | self |
| `actorId` | string | 是 | admin only | admin | Demo/system | 后端生成 | 同上 | self |
| `actorRole` | role enum | 是 | admin only | admin | Demo/system | 后端生成 | 同上 | self |
| `action` | string enum-like | 是 | admin only | admin | system-generated | 后端生成 | 同上 | self |
| `targetType` | string | 是 | admin only | admin | system-generated | 后端生成 | 同上 | self |
| `targetId` | string | 是 | admin only | admin | system-generated | 后端生成 | 同上 | self |
| `result` | enum: `success`/`failure`/`denied` | 是 | admin only | admin | system-generated | 后端生成 | 同上 | self |
| `eventTags` | controlled string[] | 否 | admin only; no free-text sensitive content | admin | system-generated | 后端生成 | 同上 | self |
| `counterKey` | controlled string enum-like | 否 | admin only | admin | system-generated | 后端生成 | 同上 | self |
| `createdAt` | datetime | 是 | admin only | admin | system-generated | 后端生成 | 同上 | self |

审计字段边界：

- `eventTags` 只能使用受控标签，例如 `demo`、`role:student`、`role:counselor`、`role:admin`、`source:deterministic`、`result:denied`、`fallback:true`。
- `counterKey` 用于后端派生统计，例如 `auth.login.success.count`、`auth.login.failure.count`、`conversation.question.count`、`conversation.fallback.count`、`knowledge.write.count`、`case.status.update.count`、`permission.denied.count`。
- 不使用自由文本 `metadataSummary` 作为 Phase 2-5 审计契约。
- 不记录完整对话正文、用户输入原文、模型输出全文、真实身份信息或心理隐私内容。
- 管理员看到的是事件列表、结构化标签和聚合统计，不看到敏感文本审计摘要。

必须记录的动作：

- `auth.login.success`
- `auth.login.failure`
- `conversation.question.submit`
- `conversation.answer.generated`
- `conversation.fallback.triggered`
- `conversation.crisis.flagged`
- `knowledge.create`
- `knowledge.update`
- `knowledge.delete`
- `knowledge.enable`
- `knowledge.disable`
- `case.status.update`
- `counselor.assistance.generate`
- `admin.demo_reset`
- `auth.permission.denied`

### 5.6 `StatsSnapshot`

用途：
管理员首页、Demo 统计、活动概览。

| 字段 | 类型意图 | 必需 | 公开/私有 | 可见角色 | 数据标签 | 读写责任 | 持久化状态 | 审计 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `totalUsers` | number | 是 | admin only | admin | derived Demo | 后端派生 | Phase 4 derived in-memory；Phase 6 from DB | source events audited |
| `conversationCount` | number | 是 | admin only | admin | derived Demo | 后端派生 | 同上 | source events audited |
| `messageCount` | number | 是 | admin only | admin | derived Demo | 后端派生 | 同上 | source events audited |
| `fallbackCount` | number | 是 | admin only | admin | derived Demo | 后端派生 | 同上 | source events audited |
| `knowledgeResourceCount` | number | 是 | admin only | admin | derived Demo | 后端派生 | 同上 | source events audited |
| `activeKnowledgeResourceCount` | number | 是 | admin only | admin | derived Demo | 后端派生 | 同上 | source events audited |
| `counselorCaseCount` | number | 是 | admin only | admin | derived Demo | 后端派生 | Phase 5+ | source events audited |
| `topCategories` | array | 否 | admin only | admin | derived Demo | 后端派生 | Phase 4+ | source events audited |
| `generatedAt` | datetime | 是 | admin only | admin | system-generated | 后端生成 | derived snapshot | read audit optional |

## 6. API 责任边界

本 SDAR 不最终批准具体 URL，但批准 API 责任边界：

| 领域 | 前端责任 | FastAPI 后端责任 |
| --- | --- | --- |
| Auth/session | 提交 Demo 登录请求，读取当前 session，按 role 导航 | 验证 Demo 用户、签发 session/token、返回 `User/Role`、记录审计 |
| Student Q&A | 提交问题，展示 answer/source/fallback | 生成 answer turn、选择 source、标记 fallback/crisis、记录事件 |
| Knowledge | admin 发起增删改启停请求；student 只读 active source cards | 校验 admin 权限、写入 Demo resource、派生 source card、记录审计 |
| Counselor case | counselor 读取列表/详情、提交状态动作 | 校验 counselor/admin 权限、维护 case 状态、生成辅助建议、记录审计 |
| Audit | admin 只读审计列表 | 后端权威写入和过滤 |
| Stats | admin 只读统计 | 后端派生统计快照 |

## 7. 影响范围

通过后影响：

- Phase 2：登录、角色路由、未授权状态。
- Phase 3：学生问答、来源卡片、会话历史。
- Phase 4：管理员知识资源、统计、审计、Demo reset。
- Phase 5：辅导员案例、辅助建议、状态更新。
- Phase 6：数据库 schema 审批输入。
- Phase 7：RAG/source citation 审批输入。

不直接影响：

- 当前运行时代码。
- 最终 PostgreSQL 表结构。
- Milvus/MinIO/vector schema。
- 生产 SSO。

## 8. 风险与缓解

| 风险 | 严重性 | 缓解方式 | 回滚方式 |
| --- | --- | --- | --- |
| 字段过少，后续 UI 不够用 | 中 | 只允许小幅补充字段，新增字段需记录在 contract amendment | 回退到当前 SDAR 字段表 |
| 字段过多，提前绑定真实 schema | 高 | 明确不批准真实学生资料和生产 schema | 删除超范围字段，回到最小 Demo 契约 |
| 前端把 Demo 字段当真实数据展示 | 高 | 每个相关 UI 保持 Demo/模拟标签 | 移除真实暗示文案 |
| 审计字段泄露敏感内容 | 高 | 不使用自由文本摘要；只使用受控 `eventTags` 和 `counterKey` | 清空标签并回退为只记录 `action/result/targetType` 的最小事件 |
| 当前后端 schema 与契约命名不同 | 中 | 实现阶段可做 adapter/mapping，不把当前实现名强行作为产品字段名 | 回退 adapter，不改契约 |

## 9. 验收方式

本 SDAR 通过后，应满足：

- 状态为 `approved`。
- 六个最小契约均有字段边界。
- 每个契约都有 Demo/真实数据标签、读写责任、持久化状态和审计要求。
- 明确哪些字段不包含真实学生/学校数据。
- 明确 API 连接型 UI 必须等待本契约通过。
- 明确 Phase 6/7 才处理数据库 schema 和 RAG/vector/storage 扩展。

## 10. 非目标

- 不创建或修改数据库 migration。
- 不实现前端页面。
- 不实现 API 连接型 UI。
- 不改现有 FastAPI 代码。
- 不引入真实学生数据。
- 不引入真实学校资源。
- 不批准生产 SSO。
- 不批准 RAG/vector/provider 实现。

## 11. 需要产品经理确认的问题

1. 是否同意采用方案 B：最小 Demo 契约 + 未来扩展边界？
同意
2. 是否同意当前六个最小契约：`User/Role`、`KnowledgeResource`、`Conversation`、`CounselorCase`、`AuditEvent`、`StatsSnapshot`？
同意
3. 是否同意在 Phase 2-5 继续使用内存态 Demo，实现时只保证契约边界，不提前做 PostgreSQL schema？
同意，但标记为重点技术债，后续必须实现
4. 是否同意 `CounselorCase.studentLabel` 只能使用模拟标签，不展示真实学生身份？
同意
5. 是否同意审计事件记录动作和摘要，不记录完整对话正文或敏感内容？
不同意，建议改为事件计数或结构化标签。

Codex 修订结果：
已移除原 `metadataSummary` 审计摘要方案，改为 `eventTags` 结构化标签 + `counterKey` 可聚合计数键。该方案保留审计和统计能力，但不记录完整对话正文、用户输入原文、模型输出全文或敏感内容。

## 12. 审批结果

- 状态：approved
- 审批日期：2026-05-19
- 审批证据：产品经理逐条回复：1-4 同意；第 5 项不同意原“动作和摘要”审计方案，要求改为事件计数或结构化标签。Codex 修订后，产品经理回复“好的，进入Phase 2”。
- 修改要求：已完成。审计契约改为 `eventTags` 结构化标签和 `counterKey` 可聚合计数键。

## 13. 后续任务

- 已批准：进入 Phase 2 Demo 登录与角色路由。
- 停止规则：Phase 2 不新增真实学生数据字段；不写数据库 schema；不接生产 SSO；不实现 RAG/vector/provider。
