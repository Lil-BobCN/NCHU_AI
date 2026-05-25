# Autoresearch Report: Frontend IA Roles And Navigation Patterns

Date: 2026-05-18
Status: completed for SDAR-0003 revision

## Research Goal

Answer the product-manager feedback in `SDAR-0003`:

- What roles are supported by the uploaded requirement documents?
- What exactly is a route map?
- What mature navigation patterns should be considered before approving Phase 1 IA?
- How should SDAR-0003 be revised?

## Local PRD Evidence

### Requirement Checklist

Source: `docs/AI 辅导员系统建设需求清单（2026.4第一版）(1).docx`

The clearest role statement is:

> 搭建三级权限体系：校级学工管理员、院系辅导员、学生用户，权限严格隔离。

The same document also mentions:

- 管理员后台：相关部门自主新增、修改、删除、批量导入问答知识库。
- 辅导员：接收风险提醒、查看对话摘要、生成工作材料和台账辅助。
- 学生：7x24 小时智能答疑、资源查询、匿名情绪倾诉等。
- 技术与运维服务：全年技术运维、BUG 修复、知识库更新、模型微调优化服务。

Interpretation:

- Product-facing roles are `学生用户`、`院系辅导员`、`校级学工管理员`。
- `运维` appears as service/technical operation responsibility, not as a main product role for the public homepage.

### Development Plan

Source: `docs/AI辅导员助手 - 开发计划表.docx`

Relevant frontend/API entries:

- 用户认证与 JWT 鉴权。
- 登录/注册/Token 刷新。
- 知识库管理模块。
- PC 端 + 移动端完整界面。
- PC 端响应式布局。

Interpretation:

- It confirms login/auth, knowledge management, and dual-end adaptation.
- It does not add a fourth product role named `运维人员`.

### Technical Plan

Source: `docs/南昌航空学校RAG智能问答系统技术方案(1).docx`

Relevant frontend/navigation entries:

- 前端跨端复用，一套代码覆盖 PC/移动端。
- Vue 3 + Vant 4（移动端）/ Element Plus（PC端） was the original frontend suggestion, now superseded by the approved React stack.
- 知识库管理：文档上传、解析进度、分类筛选、权限。
- 多轮对话：前端左侧显示历史会话记录，点击后加载该会话全部对话内容。

Interpretation:

- It supports student conversation history and admin knowledge-management pages.
- It supports role/permission separation but does not require `运维人员` as a public role card.

## Role Recommendation

For Phase 1 and the Demo route map, use three product roles:

| Role label shown to user | Internal role name | Reason |
| --- | --- | --- |
| 我是学生 | `student` | Explicit PRD role: 学生用户 |
| 我是老师/辅导员 | `counselor` | Explicit PRD role: 院系辅导员 |
| 管理入口 | `admin` | Explicit PRD role: 校级学工管理员 / 管理员后台 |

`运维人员` should not be a homepage product role in Phase 1.

Recommended handling:

- Do not show `运维人员` as one of the three main homepage cards.
- If needed later, create a separate operations/admin route such as `/ops` or `/admin/system`, but this requires a new SDAR because it affects role model, permissions, and security boundary.
- For Demo, the homepage can show two prominent role cards (`我是学生`、`我是老师/辅导员`) plus a less prominent `管理入口` link or card.

## What A Route Map Means

In this project, the route map is not a picture by default.

It is a structured table that maps:

- URL path, for example `/student/chat`
- Page meaning, for example `问答对话页`
- Phase 1 implementation state, for example `skeleton`
- Later FastAPI integration point, for example `POST /api/v1/student/questions`

The route map is used by developers to decide which pages exist, what each page is responsible for, and which backend API each page will eventually connect to.

If product review needs a visual version, we can add a simple Mermaid diagram or flowchart in the SDAR, but the engineering source of truth should remain the route table.

## Mature Navigation Pattern Research

### Pattern A: Desktop App Shell With Top Bar + Sidebar

Reference:

- Ant Design Layout: https://ant.design/components/layout/
- Ant Design Pro Layout: https://v4-pro.ant.design/docs/layout

Evidence:

- Ant Design Layout is built around `Header`, `Sider`, `Content`, and `Footer`.
- Ant Design Pro `BasicLayout` combines header navigation, sidebar, notification, and content, and maps routes to pages through configuration.

Fit for this project:

- Best fit for counselor/admin workbench.
- Works well with tables, filters, forms, stats cards, audit logs, and knowledge management.
- Matches the approved `Ant Design` stack.

Recommendation:

- Use this as the default authenticated desktop layout.

### Pattern B: Product Homepage + Role Selection Cards

Reference:

- shadcn/ui blocks and dashboard/auth examples: https://ui.shadcn.com/docs/changelog/2024-03-blocks
- shadcn dashboard example: https://ui-v4.shadcn.com/examples/dashboard
- shadcn sidebar component: https://ui.shadcn.com/docs/components/sidebar

Evidence:

- shadcn/ui blocks explicitly include dashboard layouts and authentication pages.
- The blocks are designed as composable layouts for modern product interfaces.

Fit for this project:

- Best fit for homepage, login page, and student-facing product feel.
- Gives us more visual freedom than pure Ant Design.

Recommendation:

- Use role cards on homepage/login entry, but keep actual authorization controlled by login/session, not only by the card click.

### Pattern C: Mobile Bottom Navigation / Drawer

Reference:

- Material navigation pattern overview: https://m1.material.io/patterns/navigation.html
- Adaptive navigation scaffold example: https://pub.dev/documentation/material3_layout/latest/material3_layout/NavigationScaffold-class.html
- Ant Design Mobile can be referenced later if we add mobile-specific components: https://ant.design/docs/react/introduce/

Evidence:

- Mobile navigation generally prefers simpler primary destinations.
- Deep navigation hierarchies can move into a drawer.
- Adaptive layouts switch navigation type by screen size.

Fit for this project:

- Student mobile pages can use bottom navigation because there are few top-level actions: 问答、资源、历史。
- Counselor/admin mobile pages should use a top bar plus drawer because their menus are deeper and more workbench-like.

Recommendation:

- Keep Phase 1 desktop-first.
- Guarantee mobile readability and no severe overflow.
- Defer complete mobile product polish to Phase 8.

## Revised IA Recommendation

### Public Homepage Entry

Recommended homepage entry structure:

- Main hero area: product positioning and Demo label.
- Role entry area:
  - Primary card: `我是学生`
  - Primary card: `我是老师/辅导员`
  - Secondary/less prominent entry: `管理入口`

Click behavior in Phase 1 skeleton:

- Card click can navigate to the matching login intent or role workspace placeholder.
- In Phase 2, card click should set intended role, then login/session decides actual access.

### Route Map Revision

Keep the same core route map, but revise labels:

- Rename public explanation from “三个角色工作区” to “学生、辅导员、管理后台三类入口”.
- Rename `管理员端` display wording to `管理后台` or `校级学工管理员后台`.
- Do not use `运维人员` as a public role.
- If product manager wants a true operations role, create a new `Ops Role SDAR` later.

### Navigation Revision

Recommended default:

- Public pages: product-style top navigation + role cards.
- Authenticated workspaces desktop:
  - Top bar: product name, role, Demo label, session/exit.
  - Left sidebar: role-specific menu.
- Student mobile:
  - Bottom navigation for 问答/资源/历史.
- Counselor/admin mobile:
  - Top bar + drawer menu.

## Decision Status

`SDAR-0003` should not be marked approved yet.

Current status should be `revision-required` because:

- Product manager approved inert skeleton/API placeholder principle.
- Product manager requested role-model clarification from PRD.
- Product manager requested navigation examples/research before deciding final navigation.
- Product manager did not understand route map, so the SDAR needs an explanatory section.

## Recommended Next Action

Revise `SDAR-0003` with:

- A product-manager feedback summary.
- Role evidence from uploaded docs.
- Explanation of what a route map is.
- Mature navigation references and links.
- Revised homepage role-entry recommendation.
- New confirmation questions:
  1. Use three product roles: student, counselor, school admin?
  2. Keep `运维人员` out of homepage and defer it to a future ops/security decision?
  3. Use homepage role cards with `管理入口` secondary?
  4. Use top bar + sidebar for desktop workspaces?
  5. Keep Phase 1 skeleton API-placeholder-only?

## Sources

- Local requirement checklist: `docs/AI 辅导员系统建设需求清单（2026.4第一版）(1).docx`
- Local development plan: `docs/AI辅导员助手 - 开发计划表.docx`
- Local technical plan: `docs/南昌航空学校RAG智能问答系统技术方案(1).docx`
- Ant Design Layout: https://ant.design/components/layout/
- Ant Design Pro Layout: https://v4-pro.ant.design/docs/layout
- shadcn/ui Blocks announcement: https://ui.shadcn.com/docs/changelog/2024-03-blocks
- shadcn dashboard example: https://ui-v4.shadcn.com/examples/dashboard
- shadcn sidebar component: https://ui.shadcn.com/docs/components/sidebar
- Material navigation overview: https://m1.material.io/patterns/navigation.html
- Adaptive navigation scaffold example: https://pub.dev/documentation/material3_layout/latest/material3_layout/NavigationScaffold-class.html
