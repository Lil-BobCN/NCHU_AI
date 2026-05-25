---
id: SDAR-0003
title: Phase 1 Frontend Information Architecture And Route Map
status: approved
date: 2026-05-18
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
  - .omx/decisions/SDAR-0002-frontend-stack.md
  - .omx/plans/ralplan-ai-counselor-demo-phased-development-consensus.md
---

# SDAR-0003: Phase 1 前端信息架构与路由图

## 1. 一句话结论

推荐采用“独立主站 + 双角色公开入口 + 独立管理后台”的信息架构。

公开页面负责产品展示和登录入口；主站首页只展示 `我是老师/辅导员` 和 `我是学生` 两类公开入口。根据已上传 PRD，系统仍保留“校级学工管理员/管理后台”能力，但管理后台不从主站公开进入，只通过独立链接访问。`运维人员` 暂不作为主站公开入口角色，后续如要做独立运维后台，需要另开角色/权限/安全边界 SDAR。

Phase 1 先做桌面端优先的 inert skeleton，并为后续 FastAPI API 串联预留清晰路由和接口边界。

## 2. 产品经理逐条回复与 Codex 回应

本节采用固定互动格式：

- `原问题`：Codex 提出的审批问题。
- `产品经理回复`：保留产品经理原文。
- `Codex 回应`：Codex 对该回复的解释、判断和处理结论。

### 2.1 角色入口与总体信息架构

**原问题**

是否同意采用“独立主站 + 统一登录 + 三个角色工作区”的总体信息架构？

> **产品经理回复**
>
> 我同意
> 我觉得应该这样去做，首先在打开主站页面之后，会有三个角色的选择。左侧分别，左侧到右分别是，我是老师/辅导员、运维人员、我是学生
> 然后点击这三个 DIV。即可跳转对应的界面
> 但是我个人认为，如果说有角色选择的话，运维人员不应该从主站介入，而是从独立的一个网站。
> 由于我并未仔细阅读我上传的三个文档，也就是 PRD。我无法明确，根据文档的需求，我们到底要做几个角色，这个我们需要进行一次讨论，确定好角色之后。前端开发思路是不变的，还是做对应角色的 DIV，点击进行跳转到对应页面即可

**Codex 回应**

我接受“主站首页提供角色入口卡片/DIV”的方向，但需要修订角色模型。

我已读取上传 PRD，当前最明确的角色依据是“三级权限体系：校级学工管理员、院系辅导员、学生用户”。因此 Phase 1 推荐三类产品入口：

- `我是学生`
- `我是老师/辅导员`
- `管理后台`，但不作为主站公开入口

我同意你的判断：`运维人员` 不应该从主站公开入口进入。它更像系统维护/技术服务角色，不是当前 PRD 中面向主站用户的产品角色。若后续需要运维后台，应单独做 `/ops` 或独立运维站点，并另开角色、权限和安全边界 SDAR。

处理结论：主站公开入口修订为 `我是老师/辅导员` 和 `我是学生`；`管理后台` 保留为独立链接访问；不新增 `运维入口`。

### 2.2 路由图是什么

**原问题**

是否同意本文件中的路由图作为 Phase 1 skeleton 的页面范围？

> **产品经理回复**
>
> 我并没有看到路由图，或者我不理解你所说的路由图是什么东西。请你明确一下，路由图是一个什么样的东西？是一个图片吗？还是一个表格？还是一个文本文件？请你明确一下这个路由图是什么样子的东西？

**Codex 回应**

这里的“路由图”不是图片，默认是一个工程表格。

它用来告诉开发人员：

- 用户访问哪个 URL，例如 `/student/chat`。
- 这个 URL 对应哪个页面，例如“学生问答对话页”。
- Phase 1 做到什么程度，例如 skeleton。
- 后续要连接哪个 FastAPI API，例如 `POST /api/v1/student/questions`。

所以本文件第 6 节的表格就是路由图。后续如果你希望更直观，我可以在同一个 SDAR 中补一张 Mermaid 流程图，但真正开发时仍以表格为准。

处理结论：我已在第 6 节补充“路由图是什么”的解释。

### 2.3 导航方案与成熟产品参考

**原问题**

是否同意桌面端导航优先采用“顶部栏 + 角色工作区侧边栏”，移动端后续压缩为底部导航或抽屉导航？

> **产品经理回复**
>
> 能否通过Autoresearch进行类似成品方案的搜索。给我一些具体的方案，最好附上图片或者链接，我来去查看
> 然后我去决策最终的导航是什么样子

**Codex 回应**

我已按你的要求做了 Autoresearch，并形成报告：

- `.omx/specs/autoresearch-frontend-ia-navigation/report.md`

目前参考的成熟方案包括：

- Ant Design Layout：适合 `顶部栏 + 侧边栏 + 内容区` 的工作台布局。
- Ant Design Pro Layout：适合管理后台、权限菜单、工作台型系统。
- shadcn/ui dashboard/sidebar：适合更现代、更好看的首页、登录页、学生端和卡片式入口。
- Material navigation：提供移动端底部导航、抽屉导航的成熟思路。

我的修订建议是：

- 公开首页：产品型顶部导航 + 老师/辅导员、学生两类角色入口卡片。
- 桌面端工作区：顶部栏 + 左侧角色菜单。
- 学生端移动版：后续可用底部导航。
- 辅导员端/管理后台移动版：后续可用顶部栏 + 抽屉菜单。

处理结论：当前不要求你立即批准导航最终视觉，只先确认 Phase 1 的结构方向。具体视觉风格会进入 `SDAR-0004`。

**产品经理回复**
我同意你的导航方案，我觉得这个方案是比较合理的。对于桌面端来说，顶部栏加侧边栏的方案是比较成熟的方案，很多产品都在使用。对于移动端来说，底部导航或者抽屉导航也是比较常见的方案，可以根据具体页面内容和用户习惯来选择（这个我们后期再做，作为技术债）。我建议在设计导航的时候，可以参考一些成熟的设计系统和组件库，比如 Ant Design 和 Material Design，这样可以提高设计效率和一致性。同时也要考虑到我们 Demo 的特殊性，确保导航能够清晰地引导用户进入不同的角色工作区，并且能够适应不同的设备和屏幕尺寸。

**Codex 回应**

该点已通过，导航结构方向可以进入后续设计 token 和页面骨架阶段。

处理结论：

- 桌面端工作区采用 `顶部栏 + 左侧角色菜单`。
- 公开首页采用 `产品型顶部导航 + 老师/辅导员、学生两类角色入口卡片`。
- 移动端完整导航体验标记为技术债，后续 Phase 8 重点处理。
- 设计参考优先使用 Ant Design / Ant Design Pro 的工作台布局，以及 Material Design 的移动导航原则。

### 2.4 Phase 1 是否先不接 API

**原问题**

是否同意 Phase 1 页面只做 inert skeleton，不连接真实 API，但每个页面都明确标注后续 API 串联点？

> **产品经理回复**
>
> 我同意

**Codex 回应**

该点已通过。

处理结论：Phase 1 可以只做 inert skeleton，不连接真实 API；但每个页面必须写明后续要接的 FastAPI API 点。任何 mock 或 skeleton 数据都必须明确标注为 Demo/模拟。

**产品经理回复**
  我理解你路由图是什么意思了，我需要你做的是，在你这个路由图的基础上，标注出每个页面后续要串联的 API 是什么。也就是说，虽然我们 Phase 1 不接真实 API，但是我们要明确每个页面后续要接哪个 API，这样我们在 Phase 2、Phase 3 串联 API 的时候，就有一个清晰的目标和指导。比如说，学生端的问答对话页，后续要接 `POST /api/v1/student/questions` 这个 API，那么你就要在路由图里标注出来，这样我们就知道这个页面最终是要和这个 API 对接的。其他页面也是一样，要明确后续的 API 串联点。这样可以确保我们的前后端开发是有条不紊地进行的，也可以避免后续串联时出现接口不清晰或者对接错误的问题。
  最重要的是，你可以在路由图的表格里新增一列，专门用来标注后续 API 串联点，这样信息会更集中、更清晰。每个页面都要有对应的 API 串联点，哪怕是暂时没有具体 API，也要写明后续要接什么类型的 API，比如“学生问答 API”或者“辅导员案例 API”，这样我们就有一个明确的开发方向了。
  还有一点：你需要标注进技术债

**Codex 回应**

该建议已采纳。路由图会成为后续前后端串联的导航文件，不只是页面清单。

处理结论：

- 第 6 节路由表保留 `后续 API 串联点` 列。
- 新增 `技术债/待确认` 列，用来标明后续要补的真实 API、数据契约或移动端适配。
- 对于暂时没有具体 API 的页面，不写“无”，而是写清楚“可选公告/系统状态 API”“无业务 API”“权限状态 API”等类型。
- Phase 1 不调用这些 API；Phase 2 以后按该表逐步串联。

### 2.5 页面入口增删改名是什么意思

**原问题**

是否有必须新增、删除或改名的页面入口？

> **产品经理回复**
>
> 这个问题我没理解

**Codex 回应**

这个问题的意思是：是否要调整页面或入口命名。

例子：

- 把“管理员端”改名为“管理后台”。
- 是否新增“运维入口”。
- 是否删除 `/admin/demo-reset`。
- 是否把 `/counselor` 改成 `/teacher`。
- 首页角色卡片是否展示为“我是老师/辅导员、管理入口、我是学生”。

处理结论：根据你的反馈和 PRD 角色证据，我建议先把“管理员端”统一改为“管理后台”，暂不新增“运维入口”。

**产品经理回复**

我同意你的建议，我们先把管理员端改名为管理后台，暂不新增运维入口。对于其他页面入口，我们可以保持不变，或者根据后续的设计和用户反馈进行调整。总之，我们要确保页面入口的命名能够清晰地反映其功能和角色，避免用户混淆。

**Codex 回应**

该点已通过。

处理结论：

- 文档中统一使用 `管理后台`，不再使用 `管理员端` 作为主要展示名。
- Phase 1 不新增 `运维入口`。
- 未来如果要做运维后台，单独进入运维角色、权限和安全边界 SDAR。
- 其他入口暂不调整，后续根据设计和用户反馈再做页面命名修订。

### 2.6 产品经理反馈处理结论

当前反馈不构成 SDAR-0003 直接批准，而是触发修订：

- 已同意：Phase 1 可以先做 inert skeleton，不连接真实 API，但每个页面必须标注后续 API 串联点。
- 已同意：桌面端工作区采用“顶部栏 + 左侧角色菜单”，公开首页采用老师/辅导员、学生两类角色入口卡片。
- 已同意：移动端完整导航体验作为技术债，后续 Phase 8 重点处理。
- 已同意：`管理员端` 展示命名改为 `管理后台`。
- 已同意：Phase 1 暂不新增 `运维入口`。
- 已同意：管理后台不从主站公开进入，只通过独立链接访问。
- 已同意：当前路由表可作为 Phase 1 skeleton 的工程依据，API 串联点作为后续 API/数据契约审批输入。

配套调研报告：

- `.omx/specs/autoresearch-frontend-ia-navigation/report.md`

## 3. 背景与上下文

- 当前阶段：Phase 1 前端规划。
- 已批准技术栈：React + TypeScript + Vite + Ant Design / shadcn-ui。
- 已批准体验方向：桌面端优先，移动端同步兼容，但不牺牲桌面端质量。
- 已批准产品范围：首页、登录页、学生端、辅导员端、管理员/管理后台。
- 已批准数据边界：Phase 1 不接真实学生数据；可使用明确标注的 Demo/skeleton 内容。
- 已批准后端边界：FastAPI 是主后端；最终 Demo 必须完成前后端 API 串联。

## 3.1 上传文档中的角色证据

根据 `.omx/specs/autoresearch-frontend-ia-navigation/report.md` 对三份上传文档的读取：

- `AI 辅导员系统建设需求清单（2026.4第一版）(1).docx` 明确写到“三级权限体系：校级学工管理员、院系辅导员、学生用户”。
- `AI辅导员助手 - 开发计划表.docx` 支持登录/鉴权、知识库管理、PC/移动端界面，但没有新增“运维人员”作为产品角色。
- `南昌航空学校RAG智能问答系统技术方案(1).docx` 支持跨端前端、知识库管理、多轮会话和权限隔离，但没有要求把“运维人员”作为主站入口。

因此 Phase 1 推荐产品角色为：

| 展示名称 | 内部角色 | 处理建议 |
| --- | --- | --- |
| 我是学生 | `student` | 主站角色入口卡片 |
| 我是老师/辅导员 | `counselor` | 主站角色入口卡片 |
| 管理后台 | `admin` | 不在主站公开展示；通过独立链接访问 |

`运维人员` 暂不进入 Phase 1 主站入口。若后续需要运维后台，另开 `Ops Role / Security Boundary SDAR`。

## 4. 决策驱动因素

- Demo 可信度：首屏和工作区必须像正式产品，不能像临时测试页。
- 角色清晰度：学生、辅导员、管理员要进入不同工作区，避免权限和任务边界混乱。
- 开发可控：Phase 1 先做 skeleton，避免提前定义未批准的数据字段。
- 后续可串联：每个页面都要能自然映射到 FastAPI API。
- 桌面优先：学校演示、评审和后台工作台大概率先在桌面端进行。
- 移动可用：移动端要保留可用性，但完整移动端 polish 放到 Phase 8。

## 5. 推荐信息架构

### 公开区

公开区用于建立产品信任和引导登录。

- 首页：正式产品主站首页，只展示老师/辅导员和学生两类公开入口。
- 登录页：统一 Demo 登录入口；管理后台可通过独立链接进入对应登录/入口页面。
- 无权限页：处理角色不匹配或访问受限。
- 404 页：处理未知路径。

### 认证后 App 区

认证后根据角色进入不同工作区。

- 学生端：围绕问答、资源、会话。
- 辅导员端：围绕案例、学生上下文、辅助建议。
- 管理后台：围绕知识资源、统计、审计、Demo 数据维护；不作为主站公开入口。

## 6. 推荐路由图

这里的“路由图”不是图片，而是工程表格。它说明：

- 用户访问什么 URL，例如 `/student/chat`。
- 这个 URL 对应什么页面，例如“问答对话页”。
- Phase 1 先做到什么程度，例如 skeleton 或 lightweight skeleton。
- 后续要串联哪个 FastAPI API，例如 `POST /api/v1/student/questions`。

如果产品评审需要视觉化版本，后续可以补一张 Mermaid 流程图；但开发源头仍以表格为准。

### Public Routes

| 路由 | 页面 | Phase 1 状态 | 后续 API 串联点 | 技术债/待确认 |
| --- | --- | --- | --- | --- |
| `/` | 主站首页 | skeleton/静态产品页；只展示老师/辅导员和学生入口卡片 | 可选：公告/系统状态 API；也可长期保持静态 | 主站不展示管理后台或运维入口；是否需要 `GET /api/v1/public/announcements` 或 `GET /api/v1/system/status` 后续确认 |
| `/login` | 统一登录页 | skeleton，展示老师/辅导员和学生 Demo 账号入口 | Phase 2 接 `POST /api/v1/auth/login`；可扩展 `POST /api/v1/auth/logout`、`GET /api/v1/auth/session` | Demo 账号、token/session 形态进入 Phase 2 Auth SDAR；管理后台是否复用该登录页或独立 `/admin/login` 后续确认 |
| `/unauthorized` | 无权限页 | skeleton | Phase 2 接权限状态或前端路由守卫结果；后端返回 401/403 | 错误码、重定向策略进入 Phase 2 Auth SDAR |
| `*` | 404 页 | skeleton | 无业务 API；前端本地路由兜底 | 是否上报前端 404 埋点后续确认 |

### Student Routes

| 路由 | 页面 | Phase 1 状态 | 后续 API 串联点 | 技术债/待确认 |
| --- | --- | --- | --- | --- |
| `/student` | 学生首页/问答工作台 | skeleton | Phase 3 接学生概览/问答入口 API，例如 `GET /api/v1/student/summary` 或复用问答 API | 是否需要独立 summary API 进入 Student Flow SDAR |
| `/student/chat` | 问答对话页 | skeleton | Phase 3 接 `POST /api/v1/student/questions` 或 `POST /api/v1/student/conversations/:id/messages` | 会话 API 命名、流式输出、来源卡片 contract 后续确认 |
| `/student/resources` | 资源与来源列表 | lightweight skeleton | Phase 3 接 `GET /api/v1/student/resources` | 资源分类、来源链接、真实学校资源审批后续确认 |
| `/student/conversations` | 历史会话 | lightweight skeleton | Phase 3 接 `GET /api/v1/student/conversations` | 会话保存范围、删除权限、隐私边界后续确认 |
| `/student/conversations/:id` | 会话详情 | 后续加深 | Phase 3 接 `GET /api/v1/student/conversations/:id` 和追加消息 API | 多轮上下文、历史加载、脱敏展示后续确认 |

### Counselor Routes

| 路由 | 页面 | Phase 1 状态 | 后续 API 串联点 | 技术债/待确认 |
| --- | --- | --- | --- | --- |
| `/counselor` | 辅导员工作台首页 | skeleton | Phase 5 接 `GET /api/v1/counselor/summary` 或 case summary/stats API | 统计口径和可见范围后续确认 |
| `/counselor/cases` | 案例列表 | skeleton | Phase 5 接 `GET /api/v1/counselor/cases` | 案例状态、筛选字段、分页后续确认 |
| `/counselor/cases/:id` | 案例详情 | lightweight skeleton | Phase 5 接 `GET /api/v1/counselor/cases/:id` 和 `PATCH /api/v1/counselor/cases/:id` | 状态流转、人工审核边界、审计事件后续确认 |
| `/counselor/assist` | 辅助建议生成 | lightweight skeleton | Phase 5 接 `POST /api/v1/counselor/assist` 或确定性 Demo generator | 建议性输出免责声明、AI 不替代人工决策后续确认 |

### Admin Routes

| 路由 | 页面 | Phase 1 状态 | 后续 API 串联点 | 技术债/待确认 |
| --- | --- | --- | --- | --- |
| `/admin` | 管理后台首页 | skeleton；独立链接访问，不从主站公开入口进入 | Phase 4 接 `GET /api/v1/admin/stats` 或 `GET /api/v1/admin/activity` | 管理首页统计卡片口径后续确认；管理后台入口链接和鉴权方式进入 Phase 2/4 审批 |
| `/admin/knowledge` | 知识资源列表 | skeleton | Phase 4 接 `GET /api/v1/admin/knowledge` | 知识分类、启停状态、分页后续确认 |
| `/admin/knowledge/new` | 新增知识资源 | lightweight skeleton | Phase 4 接 `POST /api/v1/admin/knowledge` | 表单字段、校验规则、是否支持文件上传后续确认 |
| `/admin/knowledge/:id` | 知识资源详情/编辑 | lightweight skeleton | Phase 4 接 `GET /api/v1/admin/knowledge/:id`、`PATCH /api/v1/admin/knowledge/:id`、`DELETE /api/v1/admin/knowledge/:id` | 删除策略、审计事件、知识影响范围后续确认 |
| `/admin/stats` | Demo 统计 | lightweight skeleton | Phase 4 接 `GET /api/v1/admin/stats` | 指标口径、时间范围、导出能力后续确认 |
| `/admin/audit` | 审计/活动记录 | lightweight skeleton | Phase 4/6 接 `GET /api/v1/admin/audit` | 持久化审计进入 Phase 6；Phase 4 可先用 Demo log |
| `/admin/demo-reset` | Demo 数据重置 | lightweight skeleton | Phase 4 接 `POST /api/v1/admin/demo-reset` | 高风险操作确认、权限、回滚提示后续确认 |

## 7. 桌面端导航结构

推荐桌面结构：

- 顶部栏：
  - 产品名称。
  - 当前角色。
  - Demo 数据标识。
  - 登录/退出入口。
- 左侧边栏：
  - 角色内一级导航。
  - 学生端：问答、资源、历史会话。
  - 辅导员端：工作台、案例、辅助建议。
  - 管理后台：知识库、统计、审计、Demo 重置。
- 主内容区：
  - 卡片、表格、详情页、对话页。
- 右侧或局部辅助区：
  - 来源卡片、上下文摘要、状态提示，按页面需要出现。

## 7.1 成熟导航方案参考

本轮 autoresearch 参考了以下成熟方案：

- Ant Design Layout：`Header + Sider + Content` 适合后台/工作台布局，见 https://ant.design/components/layout/
- Ant Design Pro Layout：适合管理后台、权限菜单、工作台型应用，见 https://v4-pro.ant.design/docs/layout
- shadcn/ui dashboard/auth/sidebar：适合现代产品感首页、登录页、学生端和卡片式入口，见 https://ui-v4.shadcn.com/examples/dashboard 与 https://ui.shadcn.com/docs/components/sidebar
- Material navigation：移动端可使用底部导航或抽屉导航思路，见 https://m1.material.io/patterns/navigation.html

当前修订建议：

- 公开首页：产品型顶部导航 + 老师/辅导员、学生两类角色入口卡片。
- 桌面端工作区：顶部栏 + 角色侧边栏。
- 学生端移动版：后续可采用底部导航。
- 辅导员端/管理后台移动版：后续可采用顶部栏 + 抽屉菜单。
- 技术债：移动端完整导航体验后续 Phase 8 处理，本阶段只保证关键路由可访问、不遮挡、不严重溢出。

## 8. 移动端导航策略

Phase 1 不做移动端优先，但保留移动端可用策略：

- 公开首页和登录页必须在移动端可读。
- 学生端保留核心入口：问答、资源、历史。
- 辅导员端和管理后台移动端只保证关键路由不崩、不遮挡、不严重溢出。
- 后续 Phase 8 再做完整移动端产品打磨。

移动导航候选：

- 学生端：底部导航。
- 辅导员端/管理后台：顶部栏 + 抽屉菜单。

## 9. 页面优先级

### Phase 1 必做 skeleton

- `/`
- `/login`
- `/student`
- `/student/chat`
- `/counselor`
- `/counselor/cases`
- `/admin`
- `/admin/knowledge`

### Phase 1 可做 lightweight skeleton

- `/student/resources`
- `/student/conversations`
- `/counselor/cases/:id`
- `/counselor/assist`
- `/admin/stats`
- `/admin/audit`
- `/admin/demo-reset`

### 后续阶段再加深

- 学生会话详情和多轮上下文。
- 管理员知识新增/编辑的完整校验。
- 辅导员案例状态流转。
- 审计查询、过滤、导出。
- Demo 数据 reset 的真实行为。

## 10. API 串联原则

Phase 1 可以不连接后端 API，但每个页面必须明确后续 API 串联点。

后续串联原则：

- 登录由 FastAPI auth API 负责。
- 前端只保存必要 session/token 状态。
- 角色路由由前端守卫和后端权限共同保证。
- 学生问答、资源、会话必须来自 FastAPI student API。
- 辅导员案例和辅助建议必须来自 FastAPI counselor API。
- 管理后台知识、统计、审计必须来自 FastAPI admin API。
- 所有 loading、error、empty 状态都要为真实 API 情况预留。
- 本路由图中的后续 API 是 Phase 2 以后 API SDAR/Contract Data Boundary Node 的输入，不等于本 SDAR 已批准最终 API contract。

## 11. 备选方案

| 方案 | 优点 | 缺点 | 是否推荐 |
| --- | --- | --- | --- |
| 独立主站 + 双公开入口 + 独立管理后台 | 面向普通用户更清晰，降低误点管理后台风险，同时保留管理能力 | 管理后台入口需单独说明和鉴权 | 推荐 |
| 首页直接进入一个混合后台 | 快，页面少 | 学生/辅导员/管理员边界不清，不像正式产品 | 不推荐 |
| 三个完全独立子站 | 角色隔离强 | Demo 阶段工程和导航复杂度过高 | 不推荐 |
| 先只做学生端 | 交付快 | 不满足已确认的主站、学生端、辅导员端、管理员端范围 | 不推荐 |

## 12. 数据边界与合规影响

- Phase 1 不接真实学生数据。
- skeleton 中出现的学生、案例、知识资源、统计都必须标注为 Demo/模拟。
- 不使用真实学校办事链接，除非后续经过真实学校资源审批。
- 不在 Phase 1 定义最终数据字段，字段以展示占位为主。

## 13. 风险、缓解与回滚

| 风险 | 严重性 | 缓解方式 | 回滚方式 |
| --- | --- | --- | --- |
| 页面范围过大 | 中 | 区分必做 skeleton、lightweight skeleton、后续加深 | 缩回必做 skeleton |
| skeleton 假设了未批准数据结构 | 高 | 只写展示占位，不写最终字段 contract | Contract gate 后重写页面数据层 |
| 移动端被拖成完整产品 | 中 | Phase 1 只保证不崩，Phase 8 再 polish | 延后移动端增强 |
| 三角色导航不一致 | 中 | 统一 AppShell，角色菜单配置化 | 重构菜单配置，不影响页面 |

## 14. 验收方式

审批通过后，Phase 1 IA/route map 验收应包含：

- 路由图文件存在。
- 首页、登录页、学生端、辅导员端、管理后台均有明确路由。
- 主站首页不展示管理后台或运维入口，管理后台通过独立链接进入。
- 每个路由标注 Phase 1 skeleton 状态和后续 API 串联点。
- 桌面导航结构明确。
- 移动端最小可用策略明确。
- 不引入真实数据和真实 API 调用。

## 15. 非目标

- 本次不实现页面代码。
- 本次不接真实 API。
- 本次不定义最终数据 contract。
- 本次不确定视觉风格和设计 token；它们进入 SDAR-0004。
- 本次不实现完整移动端产品。

## 16. 审批结果

- 状态：approved
- 审批日期：2026-05-18
- 审批证据：产品经理已在本文件第 2 节和第 18 节逐项回复；已同意 Phase 1 skeleton/API 标注原则、导航结构方向、移动端导航作为技术债、管理后台命名、暂不新增运维入口；最终确认主站只展示老师/辅导员和学生入口，管理后台通过独立链接进入，并接受第 6 节路由表作为 Phase 1 skeleton 的工程路由图。
- 修改要求：无。后续在 Phase 2/4 审批中确认管理后台独立链接、登录鉴权方式和最终 API contract。

## 17. 后续任务

- 已批准：进入 `SDAR-0004-frontend-visual-direction-design-tokens.md`。
- 若需修改：按产品经理反馈继续调整角色入口、路由范围或页面优先级。
- 停止规则：SDAR-0004 未批准前，不创建前端工程或页面代码。

## 18. 产品经理最终确认

1. Phase 1 是否按三类产品角色处理：学生、老师/辅导员、管理后台？

管理后台直接舍弃，我们管理后台页面不公开，只有老师和学生可以从主站进入，管理后台只能通过独立链接进入，这样也能弱化管理后台的入口，避免用户误点。

2. 是否同意 `运维人员` 不作为主站公开入口，后续如需要再单独做运维/安全边界 SDAR？

我同意，运维人员不应该从主站介入，而是从独立的一个网站。

3. 首页是否采用角色入口卡片：`我是学生`、`我是老师/辅导员`、较弱化的 `管理入口`？

管理入口舍弃

4. 桌面端工作区是否采用“顶部栏 + 左侧角色菜单”，并以 Ant Design Layout/Pro Layout 为主要参考？

我同意

5. 是否接受第 6 节路由表作为 Phase 1 skeleton 的工程路由图，并把其中 API 串联点作为后续 API/数据契约审批输入？

没问题

**Codex 回应**

最终确认已收到，SDAR-0003 批准通过。

处理结论：

- 主站公开入口只保留 `我是老师/辅导员` 和 `我是学生`。
- `管理后台` 不在主站公开展示，只通过独立链接进入。
- `运维人员` 不作为主站入口；后续如需要运维站点，单独做运维/安全边界 SDAR。
- 桌面端工作区采用 `顶部栏 + 左侧角色菜单`。
- 第 6 节路由表作为 Phase 1 skeleton 的工程路由图；其中 API 串联点作为后续 API/数据契约审批输入。
