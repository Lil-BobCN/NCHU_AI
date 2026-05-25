---
id: SDAR-0005
title: Frontend Page Structure And Interaction Flow
status: approved
date: 2026-05-19
phase: Phase 1 Frontend Planning, IA, And Design-System Gate
decision_owner: Product Manager
technical_owner: Codex
decision_type: ui
reversibility: moderate
confidence: medium
supersedes: []
superseded_by:
related_files:
  - .omx/plans/overall-development-plan-ai-counselor-demo.md
  - .omx/decisions/SDAR-0003-frontend-ia-route-map.md
  - .omx/decisions/SDAR-0004-frontend-visual-direction-design-tokens.md
  - .omx/context/frontend-page-structure-20260518T191302Z.md
  - .omx/prototypes/frontend-interaction-flow-demo.html
  - .omx/specs/autoresearch-final-development-workflow/report.md
---

# SDAR-0005: 前端页面结构与用户交互顺序

## 1. 一句话结论

推荐在正式 React 前端实现前，新增一层“前端页面结构与用户交互顺序”门控。

该门控位于 PRD / 总体开发方案之后、路由图和视觉设计之前，用来回答：

- 前端由哪些功能模块组成。
- 每个模块有哪些页面和页面状态。
- 用户从打开网站开始，按什么顺序点击、跳转、完成任务。
- 这些交互顺序如何决定页面排版。
- 每个页面后续如何与 FastAPI API 串联。

## 2. 当前产品经理反馈

产品经理已明确：

- 页面结构第一层希望按“功能模块”组织。
- 网站入口模块和登录认证模块要拆开，不合并。
- 不能只写文字描述用户流程，最好用一个简易页面展示用户交互顺序。
- 最终流程应为：先确定前端骨架，再确定具体前端功能模块，再用交互顺序决定排版，最后确定前端样式。
- 产品经理已认可最终开发流程报告。
- 角色选择可以放在登录页，由登录页根据不同角色展示不同欢迎语和引导文案。
- 主站首页需要重新设计，参考 Linear 官网这类产品主站：顶部导航展示产品特性、资源、登录等入口；首页先呈现产品定位和能力特性；点击登录后再展示不同角色的登录选项。

当前已有讨论原型：

- `.omx/prototypes/frontend-interaction-flow-demo.html`

### 2.1 产品经理新增回复与 Codex 处理

> **产品经理回复**
>
> 我觉得选择学生或者教师的页面可以放在登录页，登录页可以根据不同角色展示不同的欢迎语和引导文案，这样用户体验会更好一些。你是否理解，如果不理解，可以利用 autoresearch 技能搜索，将效果截图下来，进一步询问我，直到你完全理解为止。

**Codex 回应**

我理解该建议，并采纳为本 SDAR 的修订方向。

处理结论：

- 不新增独立“角色选择页”。
- `/login` 承担角色选择、欢迎语、登录引导和 Demo 账号入口。
- 首页 `/` 可以保留产品介绍、主按钮“进入登录”和学生/老师辅导员的角色说明或快捷入口，但用户真正确认身份的位置放在登录页。
- 首页快捷入口如果保留，只作为 `/login?role=student` 或 `/login?role=counselor` 的预选入口；用户仍可在登录页切换角色。
- 管理后台仍保持独立入口，不放在主站公开角色选择里。

我不需要额外启动 autoresearch 才能理解该点；这是常见且合理的登录体验模式。后续如果要比较成熟产品登录页视觉样式，再单独用 `$autoresearch` 查案例。

### 2.2 产品经理新增回复：主站首页参考 Linear

> **产品经理回复**
>
> 主站页面需要重新设计，参考 https://linear.app/ 的主站，点击链接之后，呈现的是我们产品的一些特性，登录等选项，在顶部栏目中展现，点击登录之后才会给客户呈现不同角色的登录选项。

**Codex 回应**

我理解并采纳该修订。

处理结论：

- 主站首页不再设计为“角色选择页”。
- 主站首页改为“产品官网式首页”：顶部导航 + 产品定位首屏 + 产品能力特性 + 登录入口。
- 顶部导航建议包含：产品能力、使用流程、适用角色、资源/文档、登录。
- 首页可以展示学生、老师/辅导员、管理者分别能获得什么价值，但不要求用户在首页完成角色选择。
- 点击顶部“登录”后进入 `/login`。
- `/login` 再展示学生和老师/辅导员两类登录选项，并根据角色展示对应欢迎语和引导文案。
- 管理后台仍保持独立后台入口，不作为主站公开角色入口。

## 3. 推荐方案

采用“功能模块 + 用户交互顺序 + 低保真原型 + 页面结构表”的前端规划方式。

流程如下：

```text
功能模块
-> 用户交互顺序
-> 低保真交互原型
-> 页面结构文档
-> 路由/API 映射
-> 视觉方向和 design token
-> React skeleton
-> API 串联
-> 响应式 QA
```

## 4. 备选方案

| 方案 | 描述 | 优点 | 缺点 | 是否推荐 |
| --- | --- | --- | --- | --- |
| A. 只写路由图 | 直接用 URL 表格定义页面 | 工程上简单 | 产品经理不容易感知用户如何使用网站；排版依据不足 | 不推荐 |
| B. 功能模块 + 交互原型 + 页面结构表 | 先按模块组织，再用低保真页面模拟用户点击路径 | 直观、可复用、利于产品经理反馈，也能转成工程任务 | 比单纯路由表多一步规划成本 | 推荐 |
| C. 直接做高保真视觉稿 | 先把页面做得很接近最终视觉 | 观感好 | 容易在流程、页面结构、API 边界未定时浪费设计和开发成本 | 暂不推荐 |

## 5. 为什么推荐

当前问题不是“缺一个页面地址”，而是需要把模糊产品想法转成开发能执行的页面结构。

只写路由图可以告诉开发者 `/student/chat` 是学生问答页，但不能说明：

- 用户为什么会来到这里。
- 上一步和下一步是什么。
- 页面主按钮应该放哪里。
- 哪些信息要先展示，哪些可以放到右侧或弹窗。
- 哪些状态是必须设计的。

低保真原型可以让产品经理直接看到用户路径，页面结构表可以让开发者明确工程范围。两者结合，能同时服务产品讨论和工程实现。

## 6. 功能模块第一层

当前前端页面结构第一层按功能模块组织：

| 功能模块 | 作用 | 是否进入 Phase 1 页面结构 |
| --- | --- | --- |
| 网站入口模块 | 主站首页、角色入口、产品可信度建立 | 是 |
| 登录认证模块 | Demo 登录、角色选择后的会话入口、无权限状态 | 是 |
| 学生咨询模块 | 学生问答、来源卡片、历史会话、资源访问 | 是 |
| 辅导员工作台模块 | 案例列表、案例详情、辅助建议、状态操作 | 是 |
| 管理后台模块 | 后台总览、Demo 数据维护、独立后台入口 | 是 |
| 知识资源模块 | 管理员维护 Demo 知识资源，学生端展示来源资源 | 是 |
| 统计与审计模块 | Demo 统计、活动记录、后续审计 | lightweight skeleton |
| 通用状态模块 | 404、无权限、加载、空状态、错误状态 | 是 |

## 7. 用户交互顺序

### 7.1 学生咨询流程

```text
用户打开主站首页 `/`
-> 浏览产品定位和功能特性
-> 点击顶部导航栏“登录”
-> 进入 `/login`
-> 在登录页选择或确认“学生”身份
-> 登录成功
-> 进入 `/student`
-> 点击或直接进入咨询问答
-> 进入 `/student/chat`
-> 输入问题
-> 查看 Demo 回答、来源卡片和兜底提示
-> 可继续查看资源或历史会话
```

排版含义：

- 首页必须像产品官网一样先建立可信度、解释产品特性，并在顶部导航提供清晰登录入口。
- 登录页必须承担角色选择，并根据“学生”身份显示欢迎语和引导文案，避免误入其他端。
- 学生工作台中间应放提问入口。
- 来源卡片适合放在右侧或回答下方，用来解释答案来源。

### 7.2 辅导员案例处理流程

```text
用户打开主站首页 `/`
-> 浏览产品定位和功能特性
-> 点击顶部导航栏“登录”
-> 进入 `/login`
-> 在登录页选择或确认“老师/辅导员”身份
-> 登录成功
-> 进入 `/counselor`
-> 查看待处理案例
-> 进入 `/counselor/cases`
-> 打开 `/counselor/cases/:id`
-> 查看学生上下文、辅助建议和状态操作
```

排版含义：

- 登录页需要根据“老师/辅导员”身份展示工作台、案例处理、辅助建议等登录前说明。
- 辅导员端采用工作台布局。
- 左侧为角色内导航。
- 中间为案例列表或详情主体。
- 右侧可放上下文摘要、AI 辅助建议和操作提醒。
- 辅助建议必须标明“仅供参考，不替代人工判断”。

### 7.3 管理后台知识维护流程

```text
管理员通过独立后台链接进入 `/admin`
-> 进入后台登录或完成会话校验
-> 进入后台总览
-> 打开 `/admin/knowledge`
-> 查看、筛选、启停、新增或编辑 Demo 知识资源
-> 可进入 `/admin/stats` 查看 Demo 统计
-> 可进入 `/admin/audit` 查看活动记录
-> 可进入 `/admin/demo-reset` 执行 Demo 数据重置
```

排版含义：

- 管理后台不从主站公开入口进入。
- 后台采用高密度工作台布局。
- 知识资源页以表格、筛选、表单为核心。
- Demo 数据重置属于高风险操作，需要独立确认区域。

## 8. 页面结构初稿

| 功能模块 | 页面/界面 | 路由 | Phase 1 形态 | 后续 API 串联点 |
| --- | --- | --- | --- | --- |
| 网站入口模块 | 主站首页 | `/` | skeleton；参考 Linear 式产品官网结构，包含顶部导航、产品定位首屏、能力特性、适用角色说明和登录入口；不作为正式角色选择页 | 可选 `GET /api/v1/public/announcements` 或长期静态 |
| 登录认证模块 | 统一登录页 | `/login` | skeleton；内置学生/老师辅导员角色选择、对应欢迎语、登录引导和 Demo 账号入口 | `POST /api/v1/auth/login`、`GET /api/v1/auth/session`、`POST /api/v1/auth/logout` |
| 通用状态模块 | 无权限页 | `/unauthorized` | skeleton | 前端路由守卫和后端 401/403 状态 |
| 通用状态模块 | 404 页 | `*` | skeleton | 无业务 API |
| 学生咨询模块 | 学生工作台 | `/student` | skeleton | `GET /api/v1/student/summary` 或复用问答 API |
| 学生咨询模块 | 问答对话页 | `/student/chat` | skeleton | `POST /api/v1/student/questions` 或 conversation messages API |
| 知识资源模块 | 学生资源页 | `/student/resources` | lightweight skeleton | `GET /api/v1/student/resources` |
| 学生咨询模块 | 历史会话页 | `/student/conversations` | lightweight skeleton | `GET /api/v1/student/conversations` |
| 学生咨询模块 | 会话详情页 | `/student/conversations/:id` | later | `GET /api/v1/student/conversations/:id` |
| 辅导员工作台模块 | 辅导员工作台 | `/counselor` | skeleton | `GET /api/v1/counselor/summary` |
| 辅导员工作台模块 | 案例列表 | `/counselor/cases` | skeleton | `GET /api/v1/counselor/cases` |
| 辅导员工作台模块 | 案例详情 | `/counselor/cases/:id` | lightweight skeleton | `GET /api/v1/counselor/cases/:id`、`PATCH /api/v1/counselor/cases/:id` |
| 辅导员工作台模块 | 辅助建议 | `/counselor/assist` | lightweight skeleton | `POST /api/v1/counselor/assist` 或 deterministic Demo generator |
| 管理后台模块 | 管理后台首页 | `/admin` | skeleton | `GET /api/v1/admin/stats` 或 `GET /api/v1/admin/activity` |
| 知识资源模块 | 知识资源列表 | `/admin/knowledge` | skeleton | `GET /api/v1/admin/knowledge` |
| 知识资源模块 | 新增知识资源 | `/admin/knowledge/new` | lightweight skeleton | `POST /api/v1/admin/knowledge` |
| 知识资源模块 | 知识资源详情/编辑 | `/admin/knowledge/:id` | lightweight skeleton | `GET/PATCH/DELETE /api/v1/admin/knowledge/:id` |
| 统计与审计模块 | Demo 统计 | `/admin/stats` | lightweight skeleton | `GET /api/v1/admin/stats` |
| 统计与审计模块 | 审计/活动记录 | `/admin/audit` | lightweight skeleton | `GET /api/v1/admin/audit` |
| 管理后台模块 | Demo 数据重置 | `/admin/demo-reset` | lightweight skeleton | `POST /api/v1/admin/demo-reset` |

## 9. 页面状态要求

每个正式进入页面结构的页面，都应至少考虑：

- 默认状态。
- 加载状态。
- 空状态。
- 错误状态。
- 无权限状态。
- Demo/模拟数据标识。

对话、案例、知识资源、Demo 重置等页面还应额外考虑：

- 提交中状态。
- 成功反馈。
- 失败反馈。
- 高风险操作确认。
- 后续审计事件。

## 10. 与 SDAR-0003 的关系

SDAR-0003 解决的是信息架构和路由图。

本文件解决的是更高一层的页面结构和交互顺序。

两者关系：

```text
SDAR-0005：用户怎么使用、模块怎么组织、页面为什么这样排
SDAR-0003：这些页面对应什么 URL，后续接什么 API
```

后续如果两者冲突，以本文件确认的模块和交互顺序为产品结构依据，再回写修订 SDAR-0003 的路由/API 表。

## 11. 与 SDAR-0004 的关系

SDAR-0004 负责视觉方向和 design token。

本文件确认前端结构和交互顺序后，SDAR-0004 的视觉方向才有明确承载对象。

推荐顺序：

```text
先确认 SDAR-0005 页面结构与交互顺序
再确认或修订 SDAR-0004 视觉方向与 design token
再进入 React skeleton
```

## 12. 影响范围

### 前端

- React route skeleton 的页面范围以本文件为输入。
- 首页、登录页、学生端、辅导员端、管理后台的页面优先级以本文件为输入。
- 低保真原型可作为开发前的交互参考，但不作为正式代码。
- 登录页需要支持角色选择状态，学生和老师/辅导员选择不同角色时，展示不同欢迎语、引导文案和登录后跳转目标。
- 首页需要按产品官网结构设计，顶部导航展示产品特性、资源和登录入口；角色选择不在首页完成。

### 后端

- 后续 FastAPI API 设计需要覆盖本文件列出的 API 串联点。
- API 连接型 UI 必须等待 Contract/Data Boundary Node 通过。

### 文档

- 总体开发流程需要保留“低保真交互原型”步骤。
- SDAR-0003 的路由/API 表可在本文件批准后保持同步。

## 13. 风险与回滚

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| 页面结构过细，拖慢 Phase 1 | 规划成本上升 | 只把核心页面列入 skeleton，其他标记为 lightweight 或 later |
| 原型被误认为正式 UI | 审美误判或范围误解 | 明确 `.omx/prototypes` 只是低保真讨论资产 |
| API 串联点提前写死 | 后端 contract 压力过大 | Phase 1 只写 API 意图，真实 contract 进入 Contract/Data Boundary Node |
| 管理后台入口被误放到主站 | 权限边界混乱 | 保持独立后台链接，不作为主站公开入口 |
| 首页和登录页职责混乱 | 用户不知道在哪里选择角色 | 首页负责介绍和进入系统；登录页负责正式角色选择和登录 |
| 过度照搬 Linear | 与学校 AI 辅导员场景不匹配 | 只参考信息结构和产品官网节奏，不复制品牌、文案或视觉细节 |

回滚方式：

- 如本 SDAR 不通过，删除或废弃 `.omx/decisions/SDAR-0005-frontend-page-structure-interaction-flow.md`。
- `.omx/prototypes/frontend-interaction-flow-demo.html` 可保留为讨论草稿，不进入正式实现依据。
- 已批准的 SDAR-0001/0002/0003 不受影响。

## 14. 验收方式

本 SDAR 通过后，应满足：

- 产品经理能从功能模块看懂前端由哪些大块组成。
- 产品经理能从交互顺序看懂用户如何一步步使用网站。
- 开发者能从页面结构表看懂 Phase 1 要做哪些 skeleton 页面。
- 每个页面都有后续 FastAPI API 串联点或明确说明无业务 API。
- 低保真原型和页面结构文档能互相对应。
- 登录页可以展示学生和老师/辅导员两类角色选择，并根据角色改变欢迎语、引导文案和登录后跳转目标。
- 主站首页能表达产品定位、主要特性和登录入口，不把学生/老师辅导员选择作为首页主任务。

## 15. 需要产品经理确认的问题

1. 是否同意把本文件作为 Phase 1 前端页面结构与交互顺序门控？
同意
2. 是否同意当前功能模块第一层：网站入口、登录认证、学生咨询、辅导员工作台、管理后台、知识资源、统计与审计、通用状态？
同意
3. 是否同意当前三条主流程：学生咨询流程、辅导员案例处理流程、管理后台知识维护流程？
具体修改建议见产品经理回复。
4. 是否同意 `.omx/prototypes/frontend-interaction-flow-demo.html` 只作为低保真讨论原型，不作为正式视觉稿？
同意
5. 是否需要在进入 React skeleton 前新增或删除任何页面？
具体修改建议见产品经理回复。
## 16. 审批结果

2026-05-19：产品经理确认本轮修订，SDAR-0005 通过。

附加边界：

- 当前低保真原型和页面结构用于确认流程与层级，不锁定最终视觉。
- 样式允许后续在 SDAR-0004 和 React skeleton 阶段做细微调整。
- 首页与登录页的职责分界已确认，但具体视觉细节仍可优化。
