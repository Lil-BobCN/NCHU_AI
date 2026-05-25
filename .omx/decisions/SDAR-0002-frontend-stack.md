---
id: SDAR-0002
title: Phase 1 Frontend Stack
status: approved
date: 2026-05-17
phase: Phase 1 Frontend Planning, IA, And Design-System Gate
decision_owner: Product Manager
technical_owner: Codex
decision_type: technical
reversibility: moderate
confidence: medium
supersedes: []
superseded_by:
related_files:
  - .omx/plans/overall-development-plan-ai-counselor-demo.md
  - .omx/plans/ralplan-ai-counselor-demo-phased-development-consensus.md
  - docs/南昌航空学校RAG智能问答系统技术方案(1).docx
  - docs/AI辅导员助手 - 开发计划表.docx
---

# SDAR-0002: Phase 1 前端技术栈

## 1. 一句话结论

采用 React + TypeScript + Vite 作为前端主技术栈。Ant Design 支撑辅导员端/管理员端等工作台能力；shadcn/ui 或自定义样式支撑更现代、更有产品感的主站首页、登录页和学生端体验。

## 2. 需要你统一确认的问题

本决策已由产品经理确认。

审批证据：2026-05-17，用户选择“B：React + TypeScript + Vite + Ant Design / shadcn-ui”。

## 3. 产品经理最新反馈

2026-05-17，产品经理反馈：

- 不同意“移动端优先”。
- 网站桌面端应优先。
- 移动端可以后面再做，但理想情况是桌面端和移动端都做好。
- 前端设计可以自由发挥。
- 只要保证后端与前端串联连贯、完整即可。
- 希望使用好看、生态丰富的前端框架。
- Phase 1 可以暂不连接后端 API，但最终必须实现前后端串联，这一点需要写入方案或日志。

## 4. 背景与上下文

- 当前阶段：Phase 0 已接受；后端 AI/RAG 编排技术方向已批准；接下来需要进入 Phase 1 前端规划。
- 当前约束：主站是独立产品网站，学校官网通过链接跳转；Demo 必须包含首页、登录页、学生端、辅导员端、管理员端。
- 已批准的上游决策：FastAPI 后端权威边界；LangGraph 后续 RAG workflow；模拟数据明确标注；SSO 延后。
- 当前问题为什么必须决策：前端技术栈会影响工程目录、路由、组件库、移动端适配、构建部署、后续 UI 实现效率和视觉质量。

## 5. 原始技术方案是什么

这里的“原始技术方案”指本地上传文档中的前端技术路线，主要来自：

- `docs/南昌航空学校RAG智能问答系统技术方案(1).docx`
- `docs/AI辅导员助手 - 开发计划表.docx`

其中技术方案写到：

- 前端框架：Vue 3 + Vant 4（移动端）/ Element Plus（PC 端）
- 前端适配：Vue3 + TypeScript + Vant4 + Element Plus + Pinia + Axios
- 双端适配：PC 侧边栏，移动端底部导航

这就是我之前推荐 Vue 方案的主要原因：它与原始文档一致。

但产品经理已经明确：前端设计可以自由发挥，只要前后端串联完整、产品好看、生态丰富即可。因此，原始技术方案只能作为参考，不应成为唯一决策依据。

## 6. 决策驱动因素

- 业务目标：快速做出正式产品感的首页、登录页、学生端、辅导员端、管理员端。
- 视觉目标：界面要好看、现代、可信，不能像临时后台或调试页面。
- 技术目标：工程可维护、类型安全、构建简单、适合独立主站。
- 体验目标：桌面端优先；移动端同步适配，但不牺牲桌面端布局质量。
- 集成目标：Phase 1 可先不接 API，但最终必须完成前后端 API 串联。
- 部署目标：前端静态构建产物可由 Nginx 或后续容器部署。

## 7. 方案 A：Vue 3 + TypeScript + Vite + Vant 4 + Element Plus

组成：

- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia
- Vant 4
- Element Plus
- Axios 或 fetch wrapper

优势：

- 与原始技术方案一致。
- Element Plus 对 PC 管理端、表格、表单、弹窗、菜单等很成熟。
- Vant 对移动端表单、列表、底部导航、弹层等成熟。
- Vue 单文件组件对中小型团队友好。

不足：

- 同时使用 Vant 和 Element Plus，视觉风格需要统一。
- 高级视觉表现、复杂 dashboard、现代 SaaS 风格模板的生态丰富度通常不如 React。
- 如果桌面端优先，Vant 的价值会降低，Element Plus 会成为主要 UI 库。

适合情况：

- 如果我们更看重原始方案一致性和 Vue 生态稳定性，选择它。

## 8. 方案 B：React + TypeScript + Vite + Ant Design / shadcn-ui

组成：

- React
- TypeScript
- Vite
- React Router
- Zustand / TanStack Query（后续按需）
- Ant Design 或 shadcn/ui
- Axios 或 fetch wrapper

优势：

- React 生态更大，模板、dashboard、可视化、交互组件、AI 应用样例更丰富。
- Ant Design 非常适合管理端、工作台、表格、筛选、表单、权限系统。
- shadcn/ui 更适合做现代、好看的产品界面，视觉自由度更高。
- 对“桌面端优先的正式主站 + 多角色工作台”很合适。
- AI 辅助生成和维护 React 组件的资料/样例更多。

不足：

- 与原始技术方案不一致，需要明确 supersede 原始前端技术栈建议。
- 移动端需要单独设计响应式和触控体验，不像 Vant 那样有一整套移动组件。
- shadcn/ui 更偏组件源码组合，需要更强的设计一致性控制。

适合情况：

- 如果我们更看重好看、生态丰富、桌面端优先、视觉自由发挥，React 方案更值得重新考虑。

## 9. 方案 C：Next.js + React

优势：

- 更适合正式网站、SEO、服务端渲染和复杂全栈前端。

不足：

- 当前 Demo 阶段会增加部署和工程复杂度。
- 后端已经是 FastAPI，Next.js 的后端能力当前不必要。

结论：

- 不推荐当前阶段使用。

## 10. 当前技术判断

如果严格尊重原始技术方案，选 Vue 3。

产品经理已选择：

**React + TypeScript + Vite + React Router + Ant Design 或 shadcn/ui。**

执行策略：

- React + TypeScript + Vite 作为工程基础。
- React Router 负责路由。
- Ant Design 用于辅导员端、管理员端、复杂表单、表格、筛选、工作台组件。
- shadcn/ui 或自定义 CSS 用于主站首页、登录页、学生端等更需要现代产品感的界面。
- 桌面端优先，移动端同步适配但不牺牲桌面体验。
- Phase 1 可以先做 inert skeleton，不连接真实 API；最终 Demo 必须完成前后端 API 串联。

## 11. 影响范围

- 前端：决定 `frontend/` 工程框架、路由、状态管理、组件库、样式体系。
- 后端：Phase 1 不改后端；后续通过 FastAPI API 对接。
- 数据库：无影响。
- API：Phase 1 只预留 integration map，不调用真实 API。
- 测试：后续需增加 frontend build、lint、route smoke、responsive QA。
- 部署：后续前端静态构建可由 Nginx 托管或独立容器部署。
- 文档：需新增 Phase 1 IA、route map、design token 和 frontend stack 文档。

## 12. 前后端串联承诺

Phase 1 可以先做 inert skeleton，不连接真实 API。

但最终 Demo 必须完成前后端串联：

- 登录页连接 FastAPI auth API。
- 学生端连接问答、资源、会话 API。
- 辅导员端连接案例/辅助输出 API。
- 管理员端连接知识资源、统计、审计 API。
- 前端状态、错误、loading、空状态必须来自真实 API 或明确的 Demo service。
- 任何 mock 数据必须标明是 Phase 1 skeleton 或 Demo seed，不得混淆为真实后端数据。

## 13. 数据边界与合规影响

- 是否涉及真实学生数据：否。
- 是否涉及学校资源：否，Phase 1 可使用仿真展示文案和占位结构。
- 是否涉及第三方服务：前端 npm 依赖；不涉及第三方数据服务。
- 是否存在数据出域：否。
- 脱敏/审计要求：所有 Demo 文案和样例数据必须标注模拟/仿真。

## 14. 设计 token 统一是什么意思

“设计 token”是把 UI 的基础视觉规则抽成统一变量，例如：

- 颜色：主色、辅助色、成功/警告/错误色、背景色、边框色。
- 字体：字号、行高、字重。
- 间距：4px、8px、12px、16px、24px 等 spacing scale。
- 圆角：按钮、卡片、输入框的统一 radius。
- 阴影：浮层、卡片、弹窗的 shadow。
- 断点：桌面、平板、手机的 responsive breakpoint。

“设计 token 统一”的意思是：

即使用了两个组件库，按钮颜色、字号、间距、圆角、卡片风格也要像同一个产品，而不是一部分像移动 App，一部分像后台管理系统。

例子：

```css
:root {
  --color-primary: #2563eb;
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --radius-card: 8px;
  --space-4: 16px;
}
```

以后组件样式都尽量从这些变量取值，避免页面风格散掉。

## 15. 风险、缓解与回滚

| 风险 | 严重性 | 缓解方式 | 回滚方式 |
| --- | --- | --- | --- |
| 只按原始方案选 Vue，牺牲更丰富的视觉生态 | 中 | 把 React 重新列为同级候选 | Phase 1 未实现前可切换 |
| React 方案偏离原始文档 | 中 | 在 SDAR 中明确 supersede 原始前端建议 | 回退 Vue 方案 |
| 前端过早假设 API 字段 | 高 | Phase 1 只做 inert skeleton；API-connected UI 等 Contract/Data Boundary Node | 删除 mock 字段和调用 |
| 桌面端和移动端同时做导致范围膨胀 | 中 | 桌面端优先，移动端保证关键路由可用，后续 Phase 8 深度 polish | 延后移动端增强 |
| 组件库风格不统一 | 中 | 先定义 design token 和 layout rules | 替换组件层，不影响后端 |

## 16. 验收方式

审批通过后，Phase 1 的后续验收应包含：

- 前端栈文档存在。
- IA 和 route map 存在。
- Design token 和响应式规则存在。
- API integration map 标明哪些是 placeholder。
- 如果实现 inert skeleton：`npm run build` 或等价构建通过。
- 首页、登录页、学生端、辅导员端、管理员端在桌面路由可访问。
- 移动端关键路由不崩、不遮挡、不严重溢出。

## 17. 非目标

- 本次不实现 API-connected UI。
- 本次不接入真实登录。
- 本次不引入真实学生数据。
- 本次不实现 RAG 对话。
- 本次不确定最终数据库 schema。

## 18. 审批结果

- 状态：approved
- 审批日期：2026-05-17
- 审批证据：用户选择“B：React + TypeScript + Vite + Ant Design / shadcn-ui”
- 修改要求：桌面端优先；移动端同步适配但不牺牲桌面体验；最终必须完成前后端串联。

## 19. 后续任务

- 下一任务节点：产品经理选择前端技术栈后，进入 Phase 1 信息架构和路由图 SDAR。
- 需要新增的计划/测试/代码文件：
  - `.omx/decisions/SDAR-0003-frontend-ia-route-map.md`
  - `.omx/plans/frontend-stack-ai-counselor-demo-phase1.md`
  - 后续如进入实现，再新增 `frontend/`
- 停止规则：如果本 SDAR 未获批准，不创建前端工程。

## 20. 参考来源

- Local original technical plan: `docs/南昌航空学校RAG智能问答系统技术方案(1).docx`
- Local development plan: `docs/AI辅导员助手 - 开发计划表.docx`
- Vue official TypeScript guide: https://vuejs.org/guide/typescript/overview
- Vue 3 migration guide recommends Vite for new toolchain: https://v3-migration.vuejs.org/recommendations.html
- Element Plus official installation guide: https://element-plus.org/en-US/guide/installation
- Ant Design with Vite official guide: https://ant.design/docs/react/use-with-vite/
- React TypeScript official guide: https://react.dev/learn/typescript
