# 总体开发方案：AI 辅导员 Demo

日期：2026-05-17
状态：已由产品经理确认为当前 Demo 主计划
主要依据：`.omx/plans/ralplan-ai-counselor-demo-phased-development-consensus.md`

## 目的

本文档将当前 RALPLAN 共识方案、此前的 Demo 范围调整方案、开发规则方案合并为一份可读性更强的总体开发方案。

后续开发以本文档作为日常阅读版主计划；更细的治理规则、阶段边界和停止规则，仍以 RALPLAN 共识文件为详细依据。

## 旧计划处理

以下文件现在作为历史输入和参考资料保留，不再作为直接开发指令：

- `.omx/plans/development-plan-ai-counselor-demo-scope-realignment.md`
- `.omx/plans/development-rules-ai-counselor-demo.md`
- `.omx/plans/prd-ai-counselor-technical-phase1.md`
- `.omx/plans/test-spec-ai-counselor-technical-phase1.md`
- `.omx/plans/prd-ai-counselor-business-phase1.md`
- `.omx/plans/test-spec-ai-counselor-business-phase1.md`

旧的技术 Phase 1 和业务 Phase 1 计划不会删除。它们已经通过 Phase 0 的旧 PRD/Test Spec 对齐矩阵进行处理，对齐矩阵位于 `.omx/plans/prd-ai-counselor-demo-phase0.md`。

## 产品目标

建设一个正式产品形态的独立 AI 辅导员 Demo 网站。学校官网未来只需要通过链接跳转到该主站，而不是把 AI 助手嵌入官网内部。

Demo 必须包含：

- 独立主站首页。
- 登录页。
- 学生端工作区。
- 辅导员端工作区。
- 管理员端工作区。
- 桌面端和移动端可用性。
- 明确标注的仿真/模拟数据。
- 在对应阶段已经实现的真实应用流程，而不是静态假页面。

## 当前技术基线

- `backend/` 是正式 FastAPI 后端路径。
- 当前技术后端基线已经覆盖 FastAPI、PostgreSQL、Redis、MinIO、Milvus、Docker Compose、liveness、readiness 和 smoke test。
- 当前业务接口已经覆盖 auth、student、counselor、admin 相关接口面。
- 当前业务行为仍然是内存态，并且属于 Demo 范围。
- 当前仓库还没有正式的前端产品界面。

## 已发现的后端方案缺口

当前总体方案此前只把后端 AI 能力写成了较泛化的“RAG/vector/provider 集成”，没有明确纳入原始技术方案中的 AI 编排技术路线。这是不完整的。

原始技术方案和开发计划中已经出现或强相关的后端 AI/RAG 技术点包括：

- FastAPI + LangChain + LangGraph 作为后端 RAG 工作流方向。
- LangGraph 工作流用于调度用户输入、查询改写、意图识别、加载记忆、三路检索、重排序、答案生成、更新记忆和返回来源。
- Redis 用于短期会话记忆。
- PostgreSQL 用于历史会话和结构化业务数据。
- Milvus 用于向量检索。
- MinIO 用于原始文档、解析结果和图片等对象存储。
- Redis Stream 用于异步解析任务队列。
- BM25、向量检索、查询扩展、rerank、HyDE、查询改写等检索增强策略。
- LangSmith 或同类可观测/评测工具需要作为候选项进入后续审批，而不是被默认忽略。

因此，后续在进入真正后端 AI/RAG 实现前，必须增加一个独立的后端 AI 编排审批包。该审批包至少需要回答：

- 是否采用 LangGraph 作为 RAG/Agent 工作流编排核心。
- LangChain 在项目中承担什么角色：文档处理、retriever 组合、prompt/template、model adapter，还是只作为局部工具库。
- 是否引入 LangSmith；如果引入，如何处理私有化部署、数据出域、成本和学校隐私合规问题。
- 如果不使用 LangSmith，是否选择 Langfuse、OpenTelemetry、Phoenix、Prometheus/Grafana 或自建日志评测方案。
- LangGraph/LangChain 与 FastAPI service layer 的边界如何划分。
- RAG 工作流如何与 PostgreSQL、Redis、Milvus、MinIO、Redis Stream 对接。
- 哪些能力进入 Demo，哪些能力延后到 Phase 7 或后续阶段。

## 交付策略

采用 RALPLAN 中的 Option B 路线：基于阶段门控的主线开发，并允许有限的并行只读调研。

具体含义：

- 开发按阶段推进，每个阶段有进入条件、审批包、验收证据和停止规则。
- 优先拆成小任务节点，避免一次性做过大的功能批次。
- 在某个阶段等待审批或验证时，可以提前做下一阶段的只读调研或草拟审批包。
- 未经审批，不实现新的 UI 结构、API 契约、数据库结构、RAG/vector/provider 集成或开源组件引入。
- FastAPI 保持后端权威边界。
- 外部成熟开源组件可以辅助系统，但不能替代 FastAPI 作为业务编排和 API 边界。

## 开发流程补充规则

### 多方案任务思想对齐

在遵循既有审批原则的基础上，如果某个开发任务出现多个可替代方案、实现路径或产品表达方式，Codex 必须先向产品经理说明：

- 有哪些可选方案。
- 每个方案的影响范围、优缺点、风险和回滚方式。
- Codex 的推荐方案和推荐理由。
- 哪些问题需要产品经理做思想对齐或进入 Deep Interview 式澄清。

该规则适用于技术实现路径、UI/交互结构、页面排版、数据契约、组件选择、后端服务边界、部署方式等会影响后续开发方向的任务。

低风险、已有明确本地模式的小修复可以直接执行；但只要选择会影响产品体验、架构边界、数据责任或后续阶段成本，就必须先对齐。

### 开发路径结构图与项目日志

除常规项目日志外，项目必须维护一份开发路径结构图，让产品经理能一眼看到：

- 当前有哪些阶段和任务节点。
- 已完成、进行中、待审批、待实现、被阻塞的节点分别在哪里。
- 当前正在做什么，下一步是什么。
- 哪些节点受审批门控、数据契约门控或实现停止规则约束。

路径图位置：

- `.omx/logs/development-path-structure-ai-counselor-demo.md`

每完成一个开发任务节点、审批包或验收节点，Codex 都应同步更新项目日志和该路径图。

## 审批治理

用户是产品经理。

Codex 是主程序员。

以下事项在实现前必须先提供审批包：

- 关键技术选型。
- UI 结构。
- 数据库结构。
- 数据契约。
- 开源组件引入。
- 产品定位变化。
- 真实学校资源。
- SSO。
- 真实学生数据。
- 公开部署或生产安全边界。

每个审批包必须包含：

- 推荐方案。
- 备选方案。
- 为什么推荐。
- 影响范围。
- 风险与回滚。
- 验收和验证方式。
- 需要产品经理确认的问题。
- 审批结果和日期。

## 阶段路线图

### Phase 0：需求与测试基线更新

更新独立 Demo 的 PRD/test baseline，并对旧计划文件进行明确对齐。

本阶段不改运行时代码。

退出条件：
Phase 0 PRD、测试规格、旧文档对齐矩阵、首个审批包、证据清单、风险登记、回滚说明都已经存在并被接受。

### Phase 1：前端规划、信息架构与设计系统门控

在正式前端实现前，先审批前端技术栈、信息架构、路由图、设计 token、响应式导航模式和 API 对接点。

当前调整：
在进入 Phase 1 前端栈审批前，先补充“后端 AI/RAG 编排技术审批包”。原因是原始技术方案明确包含 LangGraph/LangChain 等后端工作流能力，前端对话 UI、来源引用、流式输出、历史会话和 API 边界都依赖该后端边界。

退出条件：
前端规划审批包被接受。只有在审批通过后，才允许在明确范围内使用团队执行。

### Contract/Data Boundary Node：产品数据契约门控

在实现任何 API 连接型 UI 前，先审批最小产品数据契约：

- `User/Role`
- `KnowledgeResource`
- `Conversation`
- `CounselorCase`
- `AuditEvent`
- `StatsSnapshot`

退出条件：
数据契约审批包被接受。Phase 2 及之后的实现必须严格在已批准的数据契约内进行。

### Phase 2：Demo 登录与角色路由

实现 Demo 登录、会话行为、角色路由保护、未授权状态和 SSO 延后边界。

退出条件：
学生、辅导员、管理员 Demo 账号都能登录，并进入正确的角色工作区。

### Phase 3：学生端流程与确定性答案来源适配器

实现学生问答流程。该阶段使用确定性的 Demo 来源匹配、来源卡片、兜底回答和对话 UI。

退出条件：
学生可以提出已覆盖的 Demo 问题并得到预期答案和来源；也可以提出未覆盖问题并得到明确兜底回答。本阶段不声称已经实现 RAG。

### Phase 4：管理员知识域与 Demo 种子/重置

实现管理员端 Demo 知识管理、种子数据/重置、统计/活动展示和角色保护。

本阶段不引入真实数据库 schema，也不引入 RAG。

退出条件：
管理员可以管理 Demo 资源并重置 Demo 数据；在范围允许时，学生端确定性答案会受管理员 Demo 知识行为影响。

### Phase 5：辅导员端流程

实现辅导员工作台、仿真案例列表/详情、建议性辅助输出和状态/动作处理。

退出条件：
辅导员可以查看仿真案例，看到建议性辅助内容，并更新案例状态。

### Phase 6：持久化加固

在数据库 schema 和迁移方案审批通过后，将已批准的 Demo 关键数据从内存服务迁移到 PostgreSQL。

退出条件：
已批准的数据在服务重启后仍然存在，并且迁移证据已经记录。

### Phase 7：知识库/RAG 集成

在 RAG 架构、vector schema、embedding/model provider、存储组件等审批通过后，引入知识检索能力，同时保留兜底行为和来源引用。

该阶段必须补充后端 AI 编排审批包，重点覆盖 LangGraph、LangChain、LangSmith/同类可观测方案、RAG 工作流边界、检索链路和评测链路。

退出条件：
学生回答可以通过已批准的检索路径引用 Demo 知识库来源；确定性 Phase 3 fallback 可以通过配置恢复。

### Phase 8：响应式 QA 与产品打磨

验证首页、登录页、学生端、辅导员端、管理员端在桌面端和移动端的完整体验。

退出条件：
关键流程可用，文字没有明显溢出或错位，Demo 脚本可以端到端跑通。

### Phase 9：Docker/部署 Smoke

为 Demo 准备本地/私有化部署路径，并以阿里云 ECS 4 vCPU / 16 GiB 作为目标假设。

退出条件：
Compose 栈可以启动，health/readiness 通过，后端测试和前端构建通过，Demo 脚本可以在组合栈上完成。

## 当前已完成的 Phase 0 首批工作

当前批次：

- P0-N1：证据清单与假设清理。
- P0-N4：首个审批包，覆盖产品范围、PRD 结构、测试范围和旧文档 supersession。
- P0-N7：旧 PRD/Test Spec 对齐矩阵。

本批次停止条件：

- 相关 artifacts 已写入 `.omx/plans/` 和 `.omx/logs/`。
- 没有进行运行时代码实现。
- 产品经理已于 2026-05-17 批准该 Phase 0 baseline。

## 审批记录

2026-05-17：产品经理以“我同意”确认 Phase 0 baseline 和旧文档 supersession 路线。

## 计划修正记录

2026-05-17：产品经理指出总体开发方案缺少 LangGraph、LangChain、LangSmith 等后端 AI 编排技术路线。已将该问题记录为后端方案缺口，并要求在后端 AI/RAG 实现前新增独立审批包。

2026-05-17：产品经理同意先补充后端 AI/RAG 编排技术审批包，再继续 Phase 1 前端栈审批。该同意只确认流程调整，不代表已批准具体引入 LangGraph、LangChain 或 LangSmith。

2026-05-17：产品经理批准后端 AI/RAG 编排推荐路线：LangGraph 作为后续 RAG/Agent workflow 编排核心；LangChain 有限用于模型、retriever、prompt 和工具集成；LangSmith 不默认进入真实学校数据链路，需在开发期/真实数据期分别评估和审批。

2026-05-17：开始采用 SDAR（结构化决策审批记录）作为后续关键决策审批格式。已新增 `.omx/decisions/SDAR-0001-backend-ai-rag-orchestration.md` 和 `.omx/decisions/SDAR-0002-frontend-stack.md`。

2026-05-17：产品经理反馈 Phase 1 前端不应移动端优先，而应桌面端优先，同时尽量兼顾移动端。Phase 1 可以先做 inert skeleton，不连接真实 API，但最终 Demo 必须完成前后端串联：登录、学生问答/资源/会话、辅导员案例/辅助输出、管理员知识/统计/审计都要通过 FastAPI API 形成完整闭环。

2026-05-17：产品经理批准 Phase 1 前端技术栈选择 B：React + TypeScript + Vite + Ant Design / shadcn-ui。执行方向为 React + TypeScript + Vite 作为工程基础，Ant Design 支撑工作台能力，shadcn/ui 或自定义样式支撑现代产品感界面。

2026-05-18：已创建 `SDAR-0003-frontend-ia-route-map.md`，用于审批 Phase 1 前端信息架构与路由图。该审批包已根据产品经理反馈进入修订态，当前不创建前端工程或页面代码。

2026-05-18：已完成针对上传 PRD 的角色与导航调研，结论记录在 `.omx/specs/autoresearch-frontend-ia-navigation/report.md`。结论为：产品角色应优先按学生、老师/辅导员、管理后台三类处理，`运维人员` 不作为主站公开入口角色。

2026-05-18：产品经理批准 `SDAR-0003-frontend-ia-route-map.md`。最终入口策略为：主站首页只展示老师/辅导员和学生入口；管理后台通过独立链接进入；运维人员不作为主站入口；桌面端采用顶部栏 + 左侧角色菜单；第 6 节路由表作为 Phase 1 skeleton 工程路由图，API 串联点作为后续 API/数据契约审批输入。

2026-05-18：已创建 `SDAR-0004-frontend-visual-direction-design-tokens.md`，用于审批 Phase 1 前端视觉方向与设计 token。该审批包处于 pending-review，未批准前不创建前端工程或页面代码。

2026-05-19：产品经理批准 `SDAR-0005-frontend-page-structure-interaction-flow.md`。该决策细化并修订首页/登录页职责：主站首页采用产品官网式结构，展示产品定位、能力特性和登录入口；学生与老师/辅导员的正式角色选择放在 `/login`；管理后台仍为独立入口。当前低保真原型只作为结构与交互参考，不锁定最终视觉。

2026-05-19：产品经理批准 `SDAR-0004-frontend-visual-direction-design-tokens.md`。视觉方向和 design token 通过；当前低保真原型仍只作为结构与交互参考，不锁定最终视觉。

2026-05-19：产品经理新增开发流程规则：遇到多方案任务必须先说明选项并进行思想对齐；每完成一个任务节点，应更新项目日志，并维护 `.omx/logs/development-path-structure-ai-counselor-demo.md` 作为开发路径结构图。
