# Vibe Coding 开发流程

状态：可迭代的流程基线  
日期：2026-05-25  
适用范围：AI 辅导员 Demo，以及后续类似的软件产品项目

## 1. 一句话总结

我们的开发流程不是“给 AI 一个模糊想法，然后让它直接写代码”，而是：

```text
想法 / 文档 / 反馈
-> 上下文归档
-> 深度澄清
-> 调研与方案比较
-> 产品经理审批 / SDAR
-> 交互、架构、API、数据契约规格
-> 小任务节点实现
-> 验证证据
-> 验收日志与复盘
```

你负责产品意图、边界、优先级和最终验收；AI 负责读取上下文、结构化需求、调研方案、实现代码、验证结果和沉淀文档。

## 2. 我们是怎么人机协同工作的

### 2.1 你的角色：产品经理 + 需求架构师

你不只是“提需求的人”，你在这个流程里承担更高价值的判断：

- 判断这个功能为什么要做。
- 判断哪个用户、哪个场景、哪个问题最重要。
- 确定哪些内容必须做，哪些内容现在不做。
- 审批关键技术路线、产品表达、数据边界和风险。
- 根据可见原型、截图、测试结果和验收记录判断是否通过。

你不需要提前说清每一行代码怎么写，但你需要把方向、边界、取舍和验收标准说清楚。

### 2.2 Codex 的角色：AI 架构执行协作者

Codex 不应该只做“代码生成器”，而应该承担这些工程工作：

- 读取项目文档、代码、日志、SDAR、历史决策和上传材料。
- 把模糊想法转成结构化需求、非目标、约束和验收标准。
- 在需要时用 `$autoresearch` 查相似产品、成熟方案、官方文档和工程实践。
- 在不清楚时用 `$deep-interview` 追问意图、边界、风险和决策权限。
- 给出方案选项、优缺点、推荐、风险、验证方式和回滚方式。
- 编写 SDAR、spec、原型、代码、测试和验收日志。
- 用测试、构建、截图、浏览器 smoke、API smoke 或 review 证据证明交付结果。

Codex 可以自主完成安全、可逆、局部、低风险的工作；但遇到长期产品方向、架构、数据、依赖、模型、真实数据、安全、部署边界时，必须先让你审批。

## 3. 核心原则

### 3.1 先做上下文工程

Vibe Coding 的核心不是 prompt 技巧，而是 Context Engineering。每次开发前，Codex 必须先理解：

- 用户请求和期望结果。
- 上传文档和已有 PRD。
- 当前代码状态。
- 已批准 SDAR。
- 当前阶段边界。
- 非目标和风险。
- 现有测试与验证方式。

必要时产出 `.omx/context/...md`，让后续对话、计划和执行有同一个上下文基线。

### 3.2 规格驱动开发

Prompt 在 AI 协作开发中本质上就是规格说明。正确链路是：

```text
意图
-> 需求规格
-> 决策审批
-> 技术规格
-> 小任务节点
-> 验证
-> 验收
```

项目应优先使用 PRD、SDAR、spec、原型和验收日志，而不是靠聊天记忆推进。

### 3.3 最小可行架构

不要为了“看起来完整”一次性做过大的架构。每个阶段只批准当前闭环需要的最小架构，同时保留未来扩展边界。

当前项目里的例子：

- FastAPI 是后端业务/API 权威边界。
- React + TypeScript + Vite 是前端实现基础。
- Phase 2-5 可使用已批准的内存态 Demo 数据。
- Phase 6 才处理 PostgreSQL 持久化。
- Phase 7 才处理 RAG/vector/source citation。
- 真实学生数据、真实学校资源、生产 SSO、公开部署都必须单独审批。

### 3.4 审批门控下的自主执行

Codex 不是每一步都问“是否继续”。对于安全、局部、可逆的读取、实现、测试和修复，Codex 应该直接推进。

但遇到下列情况必须停下来对齐：

- 多个可行方案会影响产品方向。
- 新增依赖、模型 provider、数据库 schema、RAG/vector、真实数据、SSO、部署或安全边界。
- UI/交互表达会影响长期产品形象。
- 数据契约或 API 边界发生变化。
- 当前阶段边界被突破。

### 3.5 证据优先

功能不是“看起来做完了”就完成。完成必须有证据：

- 前端：lint、build、浏览器 smoke、截图、控制台错误检查、响应式检查。
- 后端：ruff、pytest、API smoke、health/readiness、错误状态测试。
- AI/model：缺配置错误、超时、流式输出、取消、fallback、密钥不暴露。
- 数据/安全：无真实学生数据泄露、无前端密钥、权限失败路径明确、审计边界清楚。

## 4. 完整开发流程

### Step 0：需求入口与上下文归档

目标：先搞清楚“我们现在到底要解决什么”，而不是直接开写。

Codex 要做：

- 读取上传文档、项目文档、现有代码、`.omx/decisions`、`.omx/specs`、`.omx/logs`。
- 判断当前任务属于哪个阶段。
- 找出已批准内容、未批准内容和不能碰的边界。
- 记录未知问题和决策权限。

产物：

- `.omx/context/...md`
- 必要时补 `.omx/interviews/...md`

停止条件：目标、非目标、验收标准或审批边界不清楚时，不进入实现。

### Step 1：需求深度澄清

使用 `$deep-interview` 的场景：

- 需求模糊。
- 用户只描述了感觉，没有说明验收标准。
- 存在多个可能方向。
- 涉及产品、架构、数据或安全边界。
- 用户明确要求不要自行假设。

必须澄清：

- Intent：为什么做。
- Outcome：完成后应该是什么状态。
- Scope：本轮做什么。
- Non-goals：本轮明确不做什么。
- Constraints：产品、技术、数据、安全、时间限制。
- Success criteria：怎么判断完成。
- Decision boundaries：Codex 可以自己决定什么，什么必须你确认。

产物：

- `.omx/specs/deep-interview-*.md`
- `.omx/interviews/*.md`

停止条件：非目标和决策边界没有明确前，不进入实现。

### Step 2：相似内容调研与方案比较

使用 `$autoresearch` 的场景：

- 需要查官方文档或行业实践。
- 需要比较技术路线、组件、框架、模型 provider。
- 需要参考成熟产品的 UI/交互/动效。
- 需要判断安全、隐私、部署、质量体系。
- 需要把“感觉上的方案”变成有证据的推荐。

调研报告必须包含：

- 资料来源。
- 备选方案。
- 推荐方案。
- 为什么推荐。
- 风险。
- 验证方式。
- 回滚方式。

产物：

- `.omx/specs/autoresearch-*/mission.md`
- `.omx/specs/autoresearch-*/report.md`
- `.omx/specs/autoresearch-*/result.json`

停止条件：关键技术或产品选择没有证据时，不直接拍板。

### Step 3：多方案思想对齐

当一个任务存在多个可行路径时，Codex 必须先给你看：

- A/B/C 方案。
- 优点和缺点。
- 对范围的影响。
- 风险。
- 回滚方式。
- Codex 推荐。
- 需要你确认的问题。

适用范围：

- UI/产品表达。
- 页面结构和交互。
- 数据契约。
- API 边界。
- 后端架构。
- 组件和依赖。
- AI provider/model。
- 部署和安全策略。

停止条件：产品经理未审批前，不做长期影响大的实现。

### Step 4：SDAR / 审批包

SDAR 用来记录长期决策，不是普通聊天记录。

SDAR 必须包含：

- 一句话结论。
- 背景。
- 选项。
- 推荐方案。
- 影响范围。
- 风险。
- 回滚方式。
- 验收方式。
- 需要产品经理确认的问题。
- 审批结果和日期。

本项目已经使用的 SDAR：

- `SDAR-0001`：后端 AI/RAG 编排边界。
- `SDAR-0002`：前端技术栈。
- `SDAR-0003`：前端 IA 与路由图。
- `SDAR-0004`：视觉方向与 Design Token。
- `SDAR-0005`：页面结构与交互流程。
- `SDAR-0006`：产品数据契约边界。
- `SDAR-0007`：首页电影感首屏与滚动叙事。
- `SDAR-0008`：真实模型学生 Chatbox 边界。

停止条件：未审批的架构、数据、依赖、真实模型、真实数据和部署决策，不进入实现。

### Step 5：产品结构与用户流程

前端不能直接从视觉开始。正确顺序是：

```text
功能模块
-> 用户交互顺序
-> 低保真原型
-> 页面结构文档
-> 路由/API 映射
-> 视觉方向和 design token
-> React skeleton
-> API 串联
-> 响应式 QA
```

目的：先让你“看见用户怎么用”，再决定页面怎么排，最后才做正式视觉和代码。

产物：

- `.omx/prototypes/*.html`
- 页面结构表。
- 路由/API 映射表。
- Playwright 截图或浏览器验证记录。

停止条件：核心用户路径没走通，不进入正式 UI 实现。

### Step 6：架构、API 与数据契约

正式 API 串联前，必须明确：

- 谁读这个数据。
- 谁写这个数据。
- 哪个后端服务有权威。
- 哪些字段只是 Demo。
- 哪些字段可能是真实数据。
- 是否持久化。
- 是否需要审计。
- 哪个阶段批准扩展。

当前项目原则：

- FastAPI 负责 API、鉴权、session、密钥、模型代理、审计和权限。
- 前端不得持有模型 API Key。
- Phase 2-5 允许内存态 Demo，但不能伪装成真实数据。
- Phase 6 处理数据库 schema。
- Phase 7 处理 RAG/vector/source citation。

停止条件：没有数据契约审批，不做 API-connected UI。

### Step 7：小任务节点拆分

每个实现任务必须能单独做、单独验证、单独回滚。

每个任务节点必须写清：

- 目标。
- 范围。
- 可能涉及文件。
- 不做什么。
- 验证方式。
- 回滚方式。

合适粒度：

- 一个页面 skeleton。
- 一个 API endpoint。
- 一个 UI 状态。
- 一个数据契约。
- 一个低保真原型。
- 一条用户流程。

不合适粒度：

- “把整个前端做完。”
- “把所有后端 API 做完。”
- “一次性加入真实模型、RAG、持久化和完整 UI。”

### Step 8：实现

实现规则：

- 贴合现有代码结构。
- 小改动。
- 不引入未审批依赖。
- 不扩大阶段范围。
- 不把 Demo 数据伪装成真实数据。
- 不把密钥放到前端。
- 不破坏已验证功能。

使用方式：

- 小而清晰的任务：solo execute。
- 需要持续修复和验证：`$ralph`。
- 多个独立任务并行：`$team`。
- 视觉反复对齐：`$visual-verdict` / `$visual-ralph`。

停止条件：实现中发现新的产品、架构、数据、依赖、模型或安全决策，先补审批包。

### Step 9：验证

验证按任务类型选择。

前端：

- `npm run lint`
- `npm run build`
- 浏览器打开页面。
- Playwright 截图。
- 控制台错误检查。
- 桌面/移动响应式检查。
- 交互状态检查。

后端：

- `python -m ruff check .`
- `python -m pytest`
- API smoke。
- health/readiness。
- 权限失败和错误状态测试。

AI/model/RAG：

- provider 缺配置时有清晰错误。
- 流式输出可用。
- 可取消生成。
- provider 超时/失败可处理。
- source/fallback 标识准确。
- 前端不暴露 API Key。
- 没有把真实模型回答误称为真实学校知识库检索结果。

停止条件：没有验证证据，就不能说完成。

### Step 10：验收、日志与路径图更新

每个节点结束后记录：

- 做了什么。
- 没做什么。
- 如何验证。
- 已知风险。
- 回滚方式。
- 下一步。

产物：

- `.omx/logs/...md`
- `.omx/logs/development-path-structure-ai-counselor-demo.md`
- 必要时更新 SDAR/spec。

停止条件：完成的节点必须可追踪，不能只存在聊天上下文里。

### Step 11：复盘与能力沉淀

每个关键阶段结束后，做一次短复盘：

- What worked：哪些做法有效。
- What didn't：哪些假设失效。
- What to improve：下一步改进什么。
- 哪些规则应该固化为流程。
- 哪些技术债新增或关闭。

这一步把 Vibe Coding 从“更快写代码”升级为“持续提升架构判断力”。

## 5. 什么时候用哪个工作流

| 场景 | 使用方式 |
| --- | --- |
| 需求不清楚 | `$deep-interview` |
| 需要外部资料、成熟案例、官方文档、方案比较 | `$autoresearch` |
| 需要架构计划或测试形状评审 | `$ralplan` |
| 已批准任务需要持续做到完成并验证 | `$ralph` |
| 多个独立任务可并行 | `$team` |
| 前端视觉需要截图对齐 | `$visual-verdict` / `$visual-ralph` |
| 代码完成后做质量检查 | `$code-review` / `$ultraqa` |
| 简单局部修改 | solo execute |

## 6. 前端专用流程

固定流程：

```text
模块地图
-> 用户旅程
-> 低保真原型
-> 页面/状态清单
-> 路由/API 映射
-> 视觉方向和 token
-> React 实现
-> 浏览器验证
```

前端门控：

- 页面目的清楚。
- 用户从哪里来、到哪里去清楚。
- 空状态、加载、错误、无权限状态清楚。
- Demo 数据和真实数据边界清楚。
- 后续 API 串联点清楚。
- 视觉不覆盖未确认的产品流程。
- 移动端要可用，但不能为了移动端牺牲桌面工作台质量，除非审批。

## 7. 后端专用流程

固定流程：

```text
业务目标
-> API 职责
-> 数据契约
-> service 边界
-> 存储决策
-> 鉴权与审计
-> 实现
-> 测试和 smoke
```

后端门控：

- FastAPI 保持业务/API 权威边界。
- 前端不持有 provider key。
- 内存态 Demo 只用于批准阶段。
- 数据库 schema 变更必须审批。
- 真实学生数据必须审批。
- 真实学校资源必须审批。
- RAG/vector/storage 必须审批。

## 8. AI / RAG / 模型 Provider 流程

AI 功能影响成本、隐私、正确性和信任边界，因此更严格。

固定流程：

```text
使用场景
-> model/provider 边界
-> prompt 与安全契约
-> 后端代理
-> fallback 行为
-> 日志/审计边界
-> UX 标识
-> 验证
```

规则：

- 真实模型调用必须经过后端。
- 模型输出必要时标注 AI 生成。
- provider 缺配置必须有明确错误。
- 真实模型 chat 不等于 RAG。
- source card 不能暗示已检索真实学校知识库，除非 RAG/source path 已审批。
- provider、web search、文档 ingestion、vector storage、真实数据都要单独审批。

## 9. 质量标准

一次交付必须同时通过四类检查：

1. 产品检查：是否满足用户目标。
2. 架构检查：是否遵守已批准边界。
3. 工程检查：是否通过相关测试、lint、build、smoke。
4. 证据检查：是否有日志、截图、测试输出或 review 记录。

长期交付质量可以参考 DORA 指标：

- 变更前置时间。
- 发布频率。
- 变更失败率。
- 故障恢复时间。
- 用户可见可靠性。

## 10. 必须停下来的情况

遇到下列情况，Codex 必须先让你审批：

- 新框架或新依赖。
- UI/产品方向存在多个可行表达。
- 页面职责或路由结构变化。
- API/data contract 变化。
- 数据库 schema 或持久化。
- 模型 provider/API family。
- web search。
- RAG/vector/embedding/document ingestion。
- 真实学校资源。
- 真实学生数据。
- 生产 SSO。
- 公开部署或安全边界。
- 密钥处理方式。
- 审计/隐私策略。
- 大范围重构。

## 11. 可复用模板

### 11.1 任务节点模板

```md
## Task Node

目标：
范围：
非目标：
已批准输入：
可能涉及文件：
实现计划：
验证方式：
回滚方式：
残留风险：
```

### 11.2 SDAR 模板

```md
# SDAR-XXXX: 标题

状态：
日期：
决策 owner：
技术 owner：

## 一句话结论
## 背景
## 方案选项
## 推荐方案
## 影响范围
## 风险
## 回滚
## 验收方式
## 产品经理确认问题
## 审批记录
```

### 11.3 验收日志模板

```md
# Acceptance Log: 节点名称

日期：
状态：

## 已变更
## 未变更
## 验证证据
## 已知风险
## 回滚方式
## 下一步
```

### 11.4 AI 协作 Prompt 模板

```text
上下文：
目标：
当前阶段：
已批准决策：
约束：
非目标：
需要比较的选项：
期望输出：
必须验证：
需要产品经理确认的问题：
```

## 12. 当前项目流程总结

AI 辅导员 Demo 当前实际工作流可以概括为：

```text
上传需求 / 产品想法
-> 需求澄清
-> autoresearch
-> SDAR 审批
-> 产品与前端 skeleton
-> 交互顺序和低保真原型
-> 页面结构 / 路由 / API / 数据契约
-> 小节点实现
-> 验证
-> 验收日志和开发路径图更新
```

这个流程已经支撑了：

- 后端 AI/RAG 编排边界审批。
- 前端技术栈审批。
- 信息架构与路由审批。
- 视觉方向与 design token 审批。
- 页面结构与交互流程审批。
- 产品数据契约审批。
- 首页动效方向审批。
- 真实模型学生 Chatbox 边界审批。

因此，本文件应作为后续默认开发流程基线。若后续要改变流程，应通过新的 SDAR 或流程修订记录审批。

## 13. 参考来源

本地来源：

- `C:/Users/liuqi/WPSDrive/565982054/WPS云盘/Vibe+Coding架构师成长学习计划.docx`
- `.omx/specs/autoresearch-final-development-workflow/report.md`
- `.omx/decisions/SDAR-0001-backend-ai-rag-orchestration.md`
- `.omx/decisions/SDAR-0002-frontend-stack.md`
- `.omx/decisions/SDAR-0003-frontend-ia-route-map.md`
- `.omx/decisions/SDAR-0004-frontend-visual-direction-design-tokens.md`
- `.omx/decisions/SDAR-0005-frontend-page-structure-interaction-flow.md`
- `.omx/decisions/SDAR-0006-product-data-contract-boundary.md`
- `.omx/decisions/SDAR-0007-homepage-cinematic-hero-scroll-narrative.md`
- `.omx/decisions/SDAR-0008-real-model-student-chatbox.md`
- `.omx/logs/phase-03-real-model-student-chatbox.md`

外部参考：

- GitHub Docs, Vibe coding with GitHub Copilot: https://docs.github.com/copilot/tutorials/vibe-coding
- GitHub Docs, Best practices for using GitHub Copilot: https://docs.github.com/en/enterprise-cloud@latest/copilot/using-github-copilot/best-practices-for-using-github-copilot
- GitHub Docs, Review AI-generated code: https://docs.github.com/en/copilot/tutorials/review-ai-generated-code
- Atlassian Product Discovery: https://www.atlassian.com/agile/product-management/discovery
- NIST Secure Software Development Framework SP 800-218: https://csrc.nist.gov/pubs/sp/800/218/final
- OWASP SAMM: https://owaspsamm.org/model/
- DORA software delivery metrics: https://dora.dev/guides/dora-metrics/
- C4 model: https://c4model.com/
