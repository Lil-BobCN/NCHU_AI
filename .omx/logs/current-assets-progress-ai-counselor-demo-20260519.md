# 当前资产与进度台账：AI 辅导员 Demo

日期：2026-05-19
状态：current checkpoint
整理人：Codex

## 1. 当前阶段判断

项目当前处于 **Phase 1：前端规划、信息架构与设计系统门控**。

尚未进入正式前端 React 工程实现，也尚未进入 API 连接型 UI 开发。

当前主线是：

```text
已完成 Phase 0 基线
-> 已补齐后端 AI/RAG 编排决策
-> 已批准前端技术栈
-> 已批准前端信息架构和路由图
-> 已确认最终开发流程
-> 已批准“前端页面结构 + 用户交互顺序 + 低保真原型”这一层
-> 已批准 SDAR-0004 视觉方向与 design token
-> Phase 2 已启动
-> P2-N1 后端 Auth/Session 契约对齐已完成
-> P2-N2 React 登录/角色路由 skeleton 已完成
-> 当前下一步：P2-N3 浏览器验收与交互微调
```

## 2. 已确认的总体开发方式

产品经理已认可最终开发流程：

```text
想法/文档
-> 需求澄清
-> 调研与方案
-> 多方案思想对齐
-> 审批包/SDAR
-> 产品与前端骨架
-> 用户交互顺序和低保真原型
-> 页面结构、路由、API、数据契约
-> 小任务实现
-> 测试验证
-> 验收记录与路径图更新
```

对应报告：
- `.omx/specs/autoresearch-final-development-workflow/report.md`
- `.omx/specs/autoresearch-final-development-workflow/mission.md`
- `.omx/specs/autoresearch-final-development-workflow/result.json`

验证状态：
- `result.json` 已记录 `architect_review.verdict = approved`。
- 产品经理已在 2026-05-19 表示“这个写的很好，我很满意”。

## 3. 规划与治理资产

### 主计划

| 文件 | 状态 | 用途 |
| --- | --- | --- |
| `.omx/plans/overall-development-plan-ai-counselor-demo.md` | accepted master plan | 日常阅读版总体开发方案 |
| `.omx/plans/ralplan-ai-counselor-demo-phased-development-consensus.md` | consensus source | 详细阶段、门控、停止规则依据 |
| `.omx/plans/prd-ai-counselor-demo-phase0.md` | Phase 0 artifact | Demo PRD / old-doc alignment |
| `.omx/plans/test-spec-ai-counselor-demo-phase0.md` | Phase 0 artifact | Demo 测试与验收基线 |
| `.omx/plans/approval-packages-ai-counselor-demo-phase0.md` | Phase 0 artifact | 第一批审批包 |

### 历史输入

以下文件保留为历史输入，不再作为直接实现指令：

| 文件 | 当前处理 |
| --- | --- |
| `.omx/plans/development-plan-ai-counselor-demo-scope-realignment.md` | 已并入主计划 |
| `.omx/plans/development-rules-ai-counselor-demo.md` | 已并入主计划和最终流程 |
| `.omx/plans/prd-ai-counselor-technical-phase1.md` | 已通过 Phase 0 对齐矩阵处理 |
| `.omx/plans/test-spec-ai-counselor-technical-phase1.md` | 已通过 Phase 0 对齐矩阵处理 |
| `.omx/plans/prd-ai-counselor-business-phase1.md` | 已通过 Phase 0 对齐矩阵处理 |
| `.omx/plans/test-spec-ai-counselor-business-phase1.md` | 已通过 Phase 0 对齐矩阵处理 |

## 4. 已有 SDAR 决策资产

| SDAR | 文件 | 状态 | 结论 |
| --- | --- | --- | --- |
| SDAR-0001 | `.omx/decisions/SDAR-0001-backend-ai-rag-orchestration.md` | approved | FastAPI 为后端权威边界；LangGraph 作为后续 RAG/Agent workflow 核心；LangChain 有限使用；LangSmith 不默认进入真实学校数据链路 |
| SDAR-0002 | `.omx/decisions/SDAR-0002-frontend-stack.md` | approved | React + TypeScript + Vite；Ant Design 支撑工作台；shadcn/ui 或自定义样式支撑现代产品感页面 |
| SDAR-0003 | `.omx/decisions/SDAR-0003-frontend-ia-route-map.md` | approved | 独立主站 + 独立管理后台；桌面端优先；Phase 1 skeleton 可不接真实 API，但要标注后续 API 串联点；首页/登录页职责由 SDAR-0005 细化 |
| SDAR-0004 | `.omx/decisions/SDAR-0004-frontend-visual-direction-design-tokens.md` | approved | “正式可信 + 现代科技感 + AI 助手 + 桌面工作台”通过；当前原型不锁定最终视觉 |
| SDAR-0005 | `.omx/decisions/SDAR-0005-frontend-page-structure-interaction-flow.md` | approved | 前端页面结构与用户交互顺序已通过；低保真原型不锁定最终视觉 |
| SDAR-0006 | `.omx/decisions/SDAR-0006-product-data-contract-boundary.md` | approved | 产品数据契约边界已通过；审计策略采用结构化标签和可聚合计数键 |

2026-05-19 更新：

- 产品经理反馈：学生/老师辅导员的角色选择可以放在登录页，登录页根据不同角色展示不同欢迎语和引导文案。
- 已修订 SDAR-0005：不新增独立角色选择页；`/login` 承担正式角色选择、欢迎语、登录引导和 Demo 账号入口。
- 已同步低保真原型：`.omx/prototypes/frontend-interaction-flow-demo.html`。

2026-05-19 二次更新：

- 产品经理反馈：主站首页需要重新设计，参考 Linear 官网式产品主站；顶部栏目展示产品特性、资源、登录等入口；点击登录后再展示不同角色登录选项。
- 已修订 SDAR-0005：主站首页定位为“产品官网式首页”，不作为正式角色选择页。
- 已同步低保真原型：首页 now 展示顶部导航、产品定位、能力特性和登录入口；登录页展示学生/老师辅导员角色选择。

2026-05-19 三次更新：

- 产品经理确认对当前页面结构和低保真原型方向满意。
- 已将 SDAR-0005 标记为 approved。
- 附加边界：当前页面样式不锁定，后续在 SDAR-0004 和 React skeleton 阶段继续微调。

2026-05-19 四次更新：

- 已将 SDAR-0004 中旧的“首页两个角色入口”实现依据改为历史背景。
- SDAR-0004 现与 SDAR-0005 对齐：主站首页为产品官网式首页，`/login` 承担学生/老师辅导员角色选择。
- 当前原型继续作为低保真结构与交互参考，不锁定最终视觉样式。
- 当时下一步是产品经理复审 SDAR-0004 的视觉方向与 design token。

2026-05-19 五次更新：

- 产品经理确认 `SDAR-0004` 审批包通过。
- 已将 `SDAR-0004` 状态更新为 approved。
- 已新增开发流程规则：多方案任务必须先说明选项，并与产品经理进行思想对齐，必要时再进入 Deep Interview 式澄清。
- 已新增开发路径结构图：`.omx/logs/development-path-structure-ai-counselor-demo.md`。
- 当前下一步更新为 Contract/Data Boundary Node。

2026-05-19 六次更新：

- 已进入 Contract/Data Boundary Node。
- 已创建 `SDAR-0006-product-data-contract-boundary.md`。
- `SDAR-0006` 推荐“最小 Demo 契约 + 未来扩展边界”方案。
- 当前需产品经理审阅六个最小契约：`User/Role`、`KnowledgeResource`、`Conversation`、`CounselorCase`、`AuditEvent`、`StatsSnapshot`。
- API 连接型 UI 和 Phase 2 相关实现仍等待 `SDAR-0006` 通过。

2026-05-19 七次更新：

- 产品经理已在 `SDAR-0006` 中逐条回复。
- 已确认：采用“最小 Demo 契约 + 未来扩展边界”；当前六个最小契约通过；Phase 2-5 可继续使用内存态 Demo，但需标记为重点技术债，后续必须实现持久化；`CounselorCase.studentLabel` 只能使用模拟标签。
- 产品经理不同意原“审计事件记录动作和摘要”方案，要求改为事件计数或结构化标签。
- 已修订 `AuditEvent`：移除 `metadataSummary` 审计摘要方案，改为 `eventTags` 结构化标签和 `counterKey` 可聚合计数键。
- `SDAR-0006` 状态更新为 `pending-final-approval`，等待产品经理确认修订版后再进入 Phase 2 或 React skeleton 最后检查。

2026-05-19 八次更新：

- 产品经理回复“好的，进入Phase 2”。
- 已将 `SDAR-0006` 状态更新为 `approved`。
- Contract/Data Boundary Node 已完成，Phase 2 登录与角色路由成为当前下一步。
- Phase 2 边界：Demo 登录、session 状态、角色路由、未授权状态、SSO deferral 标签；不引入真实学生数据、生产 SSO、数据库 schema、RAG/vector/provider。

2026-05-19 九次更新：

- 已创建 Phase 2 分支：`phase/02-demo-login-role-routing`。
- 已完成 P2-N1：后端 Auth/Session 契约对齐。
- `UserPublic` 已对齐 `SDAR-0006`：`displayName`、`role`、`demoAccount`、`sessionState`。
- SSO callback 已改为明确延期边界，不再签发模拟 SSO token。
- 审计事件已改为结构化 `eventTags` 和 `counterKey`，并覆盖登录失败、权限拒绝、辅导员辅助等 Phase 2 相关动作。
- 验证结果：后端完整测试 17 passed；ruff check 通过。
- 已新增 Phase 2 日志：`.omx/logs/phase-02-demo-login-role-routing.md`。

2026-05-19 十次更新：

- 已完成 P2-N2：React + TypeScript + Vite 前端 skeleton。
- 已新增前端工程 `frontend/`，并安装 Ant Design、Ant Design Icons、React Router。
- 已实现产品官网式首页 `/`、登录页 `/login`、学生/辅导员/管理员工作台路由。
- 已接入 Demo login API，Vite `/api` 代理到 FastAPI `http://127.0.0.1:8000`。
- 前端验证：`npm run build` 通过；`npm run lint` 通过。
- Smoke 验证：`http://127.0.0.1:5173/` 和 `/login` 返回 200；`http://127.0.0.1:5173/api/v1/auth/login` 可通过代理返回 Demo session。
- 当前本地服务：前端 `http://127.0.0.1:5173`，后端 `http://127.0.0.1:8000`。
- 后端当前以 `--lifespan off` 启动，用于 Phase 6 前的内存态 Demo API 调试。

2026-05-19 十一次更新：

- 根据产品经理反馈，当前 Phase 2 skeleton 可用但视觉效果较弱，后续需要基于截图参考和组件库做正式视觉迭代。
- 已执行 `$autoresearch` 前端技能筛选与安装。
- 已安装用户级 Codex skills：`playwright`、`screenshot`、`shadcn-component-discovery`、`shadcn-component-review`、`frontend-design`、`ui-ux-pro-max`。
- 已保留现有项目级 `shadcn` skill 作为 shadcn/ui 主操作技能。
- 调研报告：`.omx/specs/autoresearch-frontend-skills/report.md`。
- 注意：新装技能通常需要重启 Codex 才能自动出现在技能列表；当前会话可手动读取技能文件。

2026-05-19 十二次更新：

- 根据产品经理新增要求，已补充安装 React best practices skill。
- 安装来源：`vercel-labs/agent-skills` 的 `skills/react-best-practices`。
- 安装目录：`C:\Users\liuqi\.codex\skills\react-best-practices`。
- 技能元数据名称：`vercel-react-best-practices`。
- 用途：后续 React + TypeScript + Vite 前端开发时，用于检查组件结构、重渲染风险、bundle/import 选择、客户端数据获取和性能敏感代码；其中 Next.js 专属规则只作为参考，不直接约束当前 Vite SPA。
- 已同步更新：`.omx/specs/autoresearch-frontend-skills/report.md` 与 `result.json`。

2026-05-19 十三次更新：

- 根据产品经理截图反馈，完成 Phase 2 P2-N3 第一轮顶部导航与身份展示微调。
- `frontend/src/App.tsx`：品牌标题改为 `NCHU AI`；顶部导航删除学生工作台、辅导员工作台、管理后台三个直接入口；公共导航仅保留首页/产品能力；右上角采用文字登录 + 圆角主按钮的相似排版。
- `frontend/src/App.tsx`：登录后仍根据 Demo 账号角色自动跳转，学生进入学生工作台，老师进入老师工作台，运维管理人员进入运维管理台；顶部显示检测出的身份标签。
- `frontend/src/App.css`：调整顶部导航布局右移、右侧动作分隔线、圆角主按钮和文字按钮样式。
- 验证：`npm run lint` 通过；`npm run build` 通过；`http://127.0.0.1:5173` 返回 HTTP 200。
- 剩余：该轮改动等待产品经理浏览器视觉验收；当前仍属于 P2-N3，不进入 Phase 3。

2026-05-19 十四次更新：

- 根据产品经理截图反馈，修复点击登录后的登录页排版错乱问题。
- 根因：`.login-hero .ant-card-body` 选择器过宽，误作用到右侧内嵌登录面板的 Ant Design Card body，导致内部内容被套用外层双栏 grid，按钮和文字被挤成竖排。
- 修复：改为 `.login-hero > .ant-card-body`，并为 `.login-panel` 补充稳定宽度、直接子级 body 布局和移动端伸展规则。
- 验证：`npm run lint` 通过；`npm run build` 通过。

2026-05-20 一次更新：

- 根据产品经理要求，遵循当前开发流程开始打磨“顶部导航 + 首页第一屏”。
- `frontend/src/App.tsx`：首页首屏改为正式产品官网式表达，包含 `NCHU AI Counselor Demo` 标识、产品价值主张、Demo 登录 CTA、能力结构 CTA、三项可信状态和右侧 AI Console 预览。
- `frontend/src/App.tsx`：引入现有 `frontend/src/assets/hero.png` 作为首屏右侧产品视觉层。
- `frontend/src/App.css`：首页切换为暗色产品导航与暗色 hero 场景，补充网格背景、渐变光效、产品预览卡、状态卡、桌面和移动端适配。
- 行为边界：登录与角色路由逻辑未改变；仍通过 Demo 账号/session 判断学生、老师或运维管理人员身份。
- 验证：`npm run lint` 通过；`npm run build` 通过；桌面截图 `output/playwright/home-hero-1440-v2.png`；移动截图 `output/playwright/home-hero-mobile-390-v2.png`；`/login` 返回 HTTP 200。
- 已知后续：移动端首屏可用，但仍以完整 hero 表达优先，后续响应式 polish 可继续压缩。

2026-05-27 一次更新：

- 根据产品经理要求，将评审原型 `.omx/prototypes/homepage-dark-hud-variants.html` 迁移到正式 React 首页。
- 新增 `frontend/src/ProductionHomePage.tsx` 与 `frontend/src/ProductionHomePage.css`，正式 `/` 首页采用 Claude 风格产品页结构，保留 NCHU AI 中文产品语境、Light/Dark 主题、顶部导航、首屏提问框、右侧能力图、滚动 reveal 动效和平台章节回退重播逻辑。
- `frontend/src/App.tsx`：`/` 路由改为渲染 `ProductionHomePage`；首页隐藏旧 AppShell 顶栏，避免双导航；非首页仍保留原登录态顶栏、`/login` 和角色工作台路由。
- 验证：`npm run lint` 通过；`npm run build` 通过；`http://127.0.0.1:5173/` 返回 200；Playwright CLI 截图为 `output/playwright/production-homepage-migration-smoke.png`。
- 已知非阻塞项：当前环境无法用临时 Playwright test runner 解析 `@playwright/test` 包，因此未保留自动化 smoke 测试文件；Vite build 仍有既有 chunk size warning。

## 5. 调研资产

| 文件夹 | 用途 |
| --- | --- |
| `.omx/specs/autoresearch-system-positioning/` | 系统定位调研 |
| `.omx/specs/autoresearch-aliyun-deployment-readiness/` | 阿里云部署准备调研 |
| `.omx/specs/autoresearch-approval-package-format/` | 审批包格式调研 |
| `.omx/specs/autoresearch-frontend-ia-navigation/` | 前端信息架构和导航调研 |
| `.omx/specs/autoresearch-frontend-visual-design-systems/` | 前端视觉设计系统调研 |
| `.omx/specs/autoresearch-final-development-workflow/` | 最终可复用开发流程总结 |
| `.omx/specs/autoresearch-frontend-skills/` | 前端开发 skills 筛选与安装记录 |
| `.omx/specs/autoresearch-nchu-sso/` | 南昌航空相关 SSO 调研 |

## 6. 前端讨论资产

| 文件 | 状态 | 用途 |
| --- | --- | --- |
| `.omx/context/frontend-page-structure-20260518T191302Z.md` | active context | 前端页面结构访谈上下文 |
| `.omx/prototypes/frontend-interaction-flow-demo.html` | discussion prototype | 低保真交互顺序原型，用于确认用户点击路径和排版逻辑；当前版本已体现产品官网式首页和登录页内角色选择；不锁定最终视觉 |
| `.omx/logs/development-path-structure-ai-counselor-demo.md` | active log | 开发路径结构图，用于显示已完成节点、当前节点和下一步 |

当前前端页面结构原则：

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

## 7. 工具与环境资产

| 资产 | 状态 | 说明 |
| --- | --- | --- |
| `.agents/skills/shadcn/` | present / untracked | 已安装 shadcn 相关 skill，用于后续 shadcn/ui 工作 |
| `~/.codex/skills/shadcn-component-discovery` | installed | shadcn 生态组件发现 |
| `~/.codex/skills/shadcn-component-review` | installed | shadcn 组件/布局审查 |
| `~/.codex/skills/frontend-design` | installed | 前端视觉方向与非模板化设计 |
| `~/.codex/skills/ui-ux-pro-max` | installed | UI/UX 风格、色彩、字体、React 指南检索 |
| `~/.codex/skills/playwright` | installed | 浏览器自动化和 UI flow 验证 |
| `~/.codex/skills/screenshot` | installed | 桌面/系统截图捕获 |
| `~/.codex/skills/react-best-practices` | installed | Vercel React/Next.js 最佳实践；当前主要用于 React 组件质量、性能、bundle/import 和数据获取审查 |
| `~/.codex/skills/gsap-core` | installed | GSAP 基础补间、transform、opacity、easing 控制 |
| `~/.codex/skills/gsap-timeline` | installed | 首页飞翼“部件飞入 -> 拼合定格 -> 整体悬浮”的时间轴编排 |
| `~/.codex/skills/gsap-plugins` | installed | 仅在核心 GSAP 不足时评估插件；默认不扩大动效复杂度 |
| `~/.codex/skills/gsap-react` | installed | 原型通过后移植到 React 时的 GSAP/React 集成模式 |
| `~/.codex/skills/gsap-performance` | installed | 动效性能约束、transform 优先、reduced-motion 处理 |
| `~/.codex/skills/svg-animations` | installed | 飞翼 SVG 几何、分组、路径、渐变和可动画结构设计 |
| `skills-lock.json` | present / untracked | skill 安装锁定文件 |
| `.omx/state/*` | runtime state | OMX 运行状态文件，不应当被误解为业务实现 |

Git 当前显示的主要未提交/未跟踪项：

```text
modified: .omx runtime state files
untracked: .agents/
untracked: skills-lock.json
```

当前没有正式前端工程实现，也没有业务运行时代码改动被本台账认定为已交付功能。

## 8. 当前未完成事项

| 事项 | 当前状态 | 下一步 |
| --- | --- | --- |
| SDAR-0004 视觉方向与 design token | approved | 已通过，后续视觉实现仍可微调 |
| 前端页面结构与交互顺序 | approved | SDAR-0005 已通过；后续视觉细节不被当前原型锁定 |
| Contract/Data Boundary Node | approved | `SDAR-0006` 已通过 |
| Phase 2 登录与角色路由 | in progress | P2-N1/P2-N2 已完成；P2-N3 顶部导航/身份展示第一轮微调完成，等待浏览器验收 |
| React frontend skeleton | done | 首页、登录页、角色 workspace 路由框架已实现 |
| API 连接型 UI | in progress | Demo login 已接入；后续仍需保持在 Phase 2 approved scope 内 |
| 持久化数据库 schema | not started | Phase 6 前单独审批 |
| RAG/Agent 真实集成 | not started | Phase 7 前单独审批 |

## 9. 首页 3D 飞翼共识 Demo

2026-05-22 更新：

- 产品经理确认首页新方向：左侧采用“产品能力浮现型”，右侧采用“产品化抽象”的南昌航空大学校徽飞翼飞机符号 2.5D 主视觉。
- 飞翼叙事修订：不是三个独立纸飞机，而是校徽内完整飞翼飞机符号的组成部件；部件从左侧依次飞入，最终拼合为尽量接近校徽裁剪图的几何形态，随后整体轻微悬浮。
- 排版修订：参考 Ant Design X 的全幅首屏，不再使用窄卡片舞台。
- 第一版不直接做真 3D，不引入 React Three Fiber / Three.js / Spline 依赖；先制作共识 Demo 验证排版和理解。
- 新增/更新讨论原型：`.omx/prototypes/homepage-3d-wing-consensus-demo.html`。
- 本地预览地址：`http://127.0.0.1:5181/.omx/prototypes/homepage-3d-wing-consensus-demo.html`。
- 验证证据：原型文件存在；本地 HTTP 访问返回 200；文件包含 `NCHU AI`、`智能辅导新秩序`、`piece-main`、`piece-top`、`piece-tail`、`flyMain`、`aircraftIdle`、学生咨询、老师个案辅助、运维知识管理等关键结构。
- 验证限制：Chrome headless 截图命令当前未稳定写出截图文件，因此本轮未把截图作为验收证据；产品经理应直接打开本地预览地址检查动效。
- 产品经理复核后认为当前效果较差，要求先补强动效 skills，再进行下一轮原型开发。
- 已补充安装：`gsap-core`、`gsap-timeline`、`gsap-plugins`、`gsap-react`、`gsap-performance`、`svg-animations`。
- 下一轮原型应先解决飞翼 SVG 几何准确度和动效时间轴质量，再考虑正式 React 首页实现。
- 2026-05-22 修订：`.omx/prototypes/homepage-3d-wing-consensus-demo.html` 已改为官网校徽中心飞翼提取资产 + CSS mask 分层动效。新增资产位于 `.omx/prototypes/assets/`：
  - `nchu-wing-symbol-full.png`
  - `nchu-wing-part-upper.png`
  - `nchu-wing-part-middle.png`
  - `nchu-wing-part-lower.png`
  - `nchu-wing-symbol-full-preview.png`
- 动效修订：下/中/上三层飞翼从左侧依次飞入，最终拼合为接近官网校徽中心飞翼的形态，然后整体轻微悬浮。
- 验证证据：
  - 桌面最终截图：`output/playwright/homepage-wing-prototype-v9-1440.png`
  - 移动端最终截图：`output/playwright/homepage-wing-prototype-v9-mobile-390.png`
  - 动效过程截图：`output/playwright/homepage-wing-prototype-v9-frame-0900ms.png`、`output/playwright/homepage-wing-prototype-v9-frame-1900ms.png`、`output/playwright/homepage-wing-prototype-v9-frame-3100ms.png`
  - 本地 HTTP 访问 `.omx/prototypes/assets/nchu-wing-symbol-full.png` 返回 200；原型结构包含 `aircraft-mask`、`wing-layer lower/middle/upper`、`wingLowerIn`、`wingMiddleIn`、`wingUpperIn` 和 `prefers-reduced-motion`。
- 当前视觉 verdict：84/100。可作为产品经理讨论原型；若通过，正式 React 实现前建议重绘为矢量级飞翼资产或获取更高清原始徽志资源，避免 bitmap mask 放大后的边缘柔化。
- 2026-05-22 修复：产品经理截图显示右侧飞翼主体未渲染，只剩背景光场。原因是上一版依赖 CSS `mask-image` + PNG alpha 作为主视觉显示链路，在当前本地预览/浏览器环境下不稳定。已改为普通透明 PNG `<img>` 分层显示，保留飞入和整体悬浮动画，不再依赖 CSS mask 渲染飞翼主体。
- 修复验证：
  - `output/playwright/homepage-wing-prototype-imgfix-1920.png`
  - `output/playwright/homepage-wing-prototype-imgfix-1920-1000ms.png`
  - `output/playwright/homepage-wing-prototype-imgfix-1920-2200ms.png`
  - 本地 HTTP 访问原型返回 200；HTML 中飞翼主体为 `<img class="wing-layer ...">`，图片 URL 已加 `?v=2` 以降低旧缓存影响。
- 2026-05-22 二次修订：产品经理批准修复计划后，停止继续打磨低质量 PNG/mask 主线，新增独立视觉实验页 `.omx/prototypes/homepage-wing-visual-lab.html`。
- SVG v1 结论：可稳定显示，但更像抽象飞行器，右侧“机身/尾翼”过强，未充分接近校徽中心飞翼符号。
- SVG v2 结论：使用校徽提取图 alpha 轮廓转 SVG 面片后，一度出现主视觉不渲染或只显示黑色面片的问题；根因是 SVG filter/动画可见态组合不稳定。已移除 SVG filter 依赖，并为最终可见态建立兜底。
- SVG v3 当前结果：使用校徽提取图 alpha 轮廓作为 SVG 面片约束，渲染稳定，最终定格更接近校徽中心符号；仍存在右侧竖面偏重、整体偏“徽标切片”、早期飞入帧不够可读的问题。
- SVG v3 验证证据：
  - `output/playwright/wing-lab-v3-1440-5200ms.png`
  - `output/playwright/wing-lab-v3b-1440-0500ms.png`
  - `output/playwright/wing-lab-v3b-1440-1200ms.png`
  - `output/playwright/wing-lab-v3b-1440-2300ms.png`
  - `output/playwright/wing-lab-v3b-1440-4200ms.png`
  - `output/playwright/wing-lab-v3b-mobile-390-4200ms.png`
- 当前视觉 verdict：76/100。该实验页可进入产品经理复核，但不建议直接进入 React 首页；下一轮应先处理右侧竖面厚重感、飞入可读性、主站首屏整体版式衔接。

2026-05-23 更新：

- 产品经理决定：校徽飞翼终版动效先写入技术债，后续如果需要再做；当前回到主站打磨。
- 已新增技术债记录：`.omx/logs/technical-debt-ai-counselor-demo.md`，条目为 `TD-0001: Homepage NCHU Emblem Wing Motion Asset`。
- 已创建并通过 `SDAR-0007-homepage-cinematic-hero-scroll-narrative.md`：首页采用深色电影感首屏、Linear-like 玻璃导航、通义千问式强滚动叙事、Apple/SpaceX 式高科技氛围。
- 已批准新增运行时依赖：`gsap`、`@gsap/react`。
- 明确禁止项：本节点不引入 Three.js、Lottie、Rive、Lenis、随机网络视频、真实学校素材、真实学生数据、生产 SSO、数据库 schema、RAG/vector/provider。
- 已实现 React 主站第一版：
  - `frontend/src/App.tsx`：首页首屏改为电影感动效槽位；顶部导航保持 `NCHU AI`、产品栏目、登录/开始体验 CTA；滚动章节为学生咨询、辅导员辅助、知识运维、可信边界；登录、session 和角色路由逻辑保持不变。
  - `frontend/src/App.css`：补充深色电影感背景、玻璃导航、首屏本地 SVG/CSS 航空 AI 动效层、章节卡和移动端降级样式。
  - `frontend/package.json` / `frontend/package-lock.json`：记录 `gsap` 和 `@gsap/react` 依赖。
- 验证证据：
  - `frontend> npm run build` 通过。
  - `frontend> npm run lint` 通过。
  - 本地前端服务：`http://127.0.0.1:5173` 返回 200。
  - 本地后端服务：`http://127.0.0.1:8000` 端口监听中，`/api/v1/health` 可用于健康检查。
  - 首页 CTA smoke：`/` 点击“进入登录”进入 `/login`。
  - 学生 Demo 登录 smoke：`/login` 点击“以 学生 Demo 登录”进入 `/app/student`。
  - 截图证据：
    - `output/playwright/homepage-cinematic-desktop.png`
    - `output/playwright/homepage-cinematic-mobile.png`
    - `output/playwright/homepage-cinematic-scroll-chapter.png`
    - `output/playwright/homepage-login-after-cta.png`
    - `output/playwright/homepage-student-login-smoke.png`
    - `output/playwright/homepage-student-workspace-smoke.png`
- 已知非阻塞项：Vite build 存在 chunk size warning，主要来自 React/Ant Design/GSAP 同包体积；后续可在性能优化节点评估路由级 lazy load 或手动 chunk。

2026-05-24 更新：

- 针对产品经理反馈 `.omx/prototypes/homepage-linear-text-motion-demo.html` “动效无法展现”，完成原型级诊断，不修改正式首页 React 代码。
- 诊断结论：GSAP 已正常加载，控制台 0 errors / 0 warnings；元素 `opacity`、`transform`、`filter` 会从隐藏态变为显示态，说明动画技术上在运行。问题主要是原型默认播放过快、打开页面时容易错过首帧，且没有播放状态反馈，导致肉眼感受接近“没有动效”。
- 原型修正：为 `.omx/prototypes/homepage-linear-text-motion-demo.html` 增加 0.35x 慢速预览、1x 正常预览、0.5 秒延迟自动播放、播放状态文字和进度条；同时提高入场位移与 blur 幅度，增强可感知性。
- 验证证据：Playwright 采样显示 B 方案在 0ms 为隐藏态，500ms/2400ms/4200ms 持续从隐藏过渡到显示；控制台保持 0 errors / 0 warnings。
- 根据产品经理澄清，实际需修复的是“高级动效 Lab”而非普通动效 Demo；已同步修复 `.omx/prototypes/homepage-tech-text-motion-lab.html`。
- 高级 Lab 修复内容：补齐强制预览、单独重播、全部重播、0.5x 慢速、1x 正常、播放状态和进度条；修复 `tl.defaults is not a function` 脚本错误；将三种高级方案接入统一 GSAP timeline 控制；增强 Glass Scan 的扫光反馈。
- 高级 Lab 验证证据：Playwright 控制台 0 errors / 0 warnings；`2 光扫` 在 2400ms 采样时 `opacity=0.9647`、`visibility=visible`、进度条正在推进。

## 10. 推荐下一步

当前最合理的下一步是进入：

```text
Phase 2: Demo Login & Role Routing
```

该阶段用于实现或补齐：

- Demo 登录入口。
- 当前 session 状态。
- `student` / `counselor` / `admin` 角色路由。
- 未授权状态。
- 生产 SSO deferral 标签。

Phase 2 不处理数据库 schema、真实学生数据、真实学校资源、生产 SSO 或 RAG/vector/provider。

当前 Phase 2 验证证据：

```text
backend> ..\.venv\Scripts\python.exe -m pytest -q
17 passed

backend> ..\.venv\Scripts\python.exe -m ruff check .
All checks passed
```

## 2026-05-24 更新：Homepage Dark HUD Variant Prototype

- 产品经理方向：采用 A 的克制高级风格 + C 的分层 HUD 启动动画交互；配色进一步转向暗色、高级、航空科技感。
- 参考来源：`https://21st.dev/community/components` 的成熟首页/卡片/导航/文字/按钮区块思路，以及 `https://motionsites.ai/` 的暗色动效首页方向。
- 已创建评审原型：`.omx/prototypes/homepage-dark-hud-variants.html`。
- 三个候选方案：
  - A1 Obsidian Command：更接近 Linear/Apple 的克制暗色产品页。
  - A2 Aero Glass：更强调航空/HUD/仪表质感，使用青色与跑道琥珀色点缀。
  - A3 Liquid Intelligence：更接近 Apple 液态玻璃与低噪音 AI 赋能界面。
- 原型能力：变体切换、重播当前、轮播三版、0.5x/1x 速度、播放状态与进度条。
- 范围边界：本次只做评审原型；未修改正式 React 首页；未新增依赖；未引入真实学校素材、真实学生数据、后端/API/schema/RAG 变更。
- 验证证据：
  - `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html` 返回 200。
  - Playwright 浏览器检查：控制台 `0 errors / 0 warnings`。
  - A1 标题从隐藏态过渡到显示态；A2/A3 变体切换后均可见。
  - 截图证据：`output/playwright/homepage-dark-hud-variants-1280-v2.png`、`output/playwright/homepage-dark-hud-variants-verify.png`。

## 2026-05-24 更新：Homepage Dark HUD Motion Enhancement

- 针对产品经理反馈“好多动效没有加进去”，已在评审原型范围内增强 `.omx/prototypes/homepage-dark-hud-variants.html`，未修改正式 React 首页。
- 增强内容：
  - 首屏启动分镜：boot curtain、导航玻璃扫光、背景网格漂移和大气光线。
  - Linear-like 文本入场：标题逐行遮罩上浮，补充行内扫光反馈。
  - 产品能力序列：新增“识别角色身份 / 匹配可信来源 / 生成工作流下一步”三段流程标签。
  - 右侧 HUD 分镜：雷达扫描、飞翼轨迹线、飞翼飞入 keyframes、HUD 数据条和日志行逐步进入。
  - 滚动叙事：新增左侧章节卡 + 右侧 sticky chapter screen，滚动时切换学生咨询、辅导员辅助、知识运维、可信边界。
  - 默认播放速度改为 `1x`，保留 `0.5x` 慢速复核入口，减少打开页面后长时间空屏的误解。
- 为避免产品经理停留在旧的 Linear 文本 Demo 看不到新版方案，已在 `.omx/prototypes/homepage-linear-text-motion-demo.html` 顶部增加“打开暗色高级动效方案”入口。
- 验证证据：
  - `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html` 可访问。
  - Playwright 浏览器脚本验证：控制台 `0 errors / 0 warnings`。
  - 首屏状态：标题 opacity `1`、流程标签 opacity `1`、流程标签 active `true`、雷达 opacity `0.4799`、飞翼 opacity `1`、导航 booted `true`。
  - 滚动章节状态：滚动采样时 active card 为“知识运维”，active panel 为 `CHAPTER 03 / ADMIN`。
  - 变体切换状态：点击 A2 后 active variant 为 `aero`，active button 为 `aero`。
  - 截图证据：
    - `output/playwright/homepage-dark-hud-variants-final-t0700.png`
    - `output/playwright/homepage-dark-hud-variants-final-t2800.png`
    - `output/playwright/homepage-dark-hud-variants-enhanced-browser-hero.png`
    - `output/playwright/homepage-dark-hud-variants-enhanced-browser-story.png`
    - `output/playwright/homepage-linear-demo-with-dark-link.png`
## 2026-05-25 更新：Phase 3R 学生 Chatbox 小闭环

- 审批状态：`SDAR-0008` 已批准并完成实现验证；范围为学生端优先、FastAPI 后端代理真实 Qwen/DashScope 模型 API、独立 Chatbox 页面、运行期内存聊天记录。
- 后端新增：`POST /api/v1/student/chat/stream`，使用 SSE 流式返回；配置复用既有 `DASHSCOPE_*` 与 legacy `QWEN_*` 环境变量，不新增第二套模型 API family；缺配置时返回明确 `503`。
- 前端新增：`/app/student/chatbox` 独立页面；`/app/student` 只增加入口按钮，不替换现有学生工作台。
- Chatbox 能力：流式输出、停止生成、重试、错误态、新会话、当前运行期会话历史侧栏。
- 验证证据：backend `python -m ruff check .` passed；backend `python -m pytest` 20 passed；frontend `npm run lint` passed；frontend `npm run build` passed with existing chunk size warning。
- 浏览器烟测：学生 Demo 登录、进入 Chatbox、真实 Qwen/DashScope 流式回复、停止生成、新会话、运行期历史侧栏均通过；Playwright console `0 errors / 0 warnings`。
- 截图证据：`output/playwright/p3r-student-chatbox-smoke.png`。
- 本地烟测说明：常规后端 lifespan 启动仍依赖 PostgreSQL；本次浏览器烟测使用 `uvicorn --lifespan off` 验证内存态 Chatbox 路径。
