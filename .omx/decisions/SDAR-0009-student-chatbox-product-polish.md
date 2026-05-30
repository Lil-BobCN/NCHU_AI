---
id: SDAR-0009
title: Student Chatbox Product Polish Boundary
status: approved
date: 2026-05-26
phase: Phase 3R Student Chatbox Product Polish
decision_owner: Product Manager
technical_owner: Codex
decision_type: product-ui-polish-boundary
reversibility: high
confidence: medium
extends:
  - SDAR-0008-real-model-student-chatbox
related_files:
  - frontend/src/StudentChatboxPage.tsx
  - frontend/src/App.css
  - frontend/package.json
  - .omx/logs/phase-03-real-model-student-chatbox.md
  - .omx/specs/autoresearch-ai-chat-components/report.md
  - .omx/specs/autoresearch-assistant-ui-chat-platform/report.md
  - .omx/prototypes/assistant-ui-chat-platform-capability.html
  - output/playwright/student-chatbox-1440-viewport.png
  - output/playwright/student-chatbox-390.png
  - output/playwright/assistant-ui-chat-platform-desktop.png
  - output/playwright/assistant-ui-chat-platform-mobile.png
---

# SDAR-0009: 学生 Chatbox 会话台产品打磨边界

## 1. 一句话结论

建议将当前 Phase 3R 的下一步定义为“学生 Chatbox 会话台产品级打磨”，采用 assistant-ui 作为学生 Chatbox 与后续多角色 Chat 页的主前端聊天框架，优先修复会话台结构、输入框常驻、历史栏、空态、错误态、流式态、模型选择入口、文案和移动端阅读体验。

本审批包只批准学生端 Chatbox 的前端视觉与交互打磨，以及为该页面新增 assistant-ui 前端依赖与 runtime adapter；不批准后端 API 契约变更、模型 provider 变更、数据库、RAG、真实学生数据、教师端/辅导员端 Chat 页面或首页改版。

## 2. 背景

`SDAR-0008` 已批准并完成学生端真实模型 Chatbox 小闭环：

- 学生 Demo 登录后可进入 `/app/student/chatbox`。
- 前端通过 FastAPI 后端代理调用真实 Qwen/DashScope 模型。
- 已支持流式输出、停止生成、重试、错误态、新会话和当前运行期聊天记录。

当前功能闭环可用，但页面体验仍偏“开发验收页”。产品经理确认本轮优先打磨 Chatbox 会话台，不先处理 `/app/student` 入口页。

## 3. 当前证据

浏览器审计证据：

- 桌面截图：`output/playwright/student-chatbox-1440-viewport.png`
- 移动截图：`output/playwright/student-chatbox-390.png`
- 运行状态：`/app/student/chatbox` 可访问，学生会话记录读取成功，控制台 0 errors / 0 warnings。

关键体验问题：

1. 输入框没有形成会话台常驻底栏。1440x1000 视口下，页面总高度约 2235px，输入框顶部约在 2105px，用户需要滚动到页面底部才能继续输入。
2. 消息区使用整页滚动，不像稳定的工作台。长会话会把操作区推离视口，降低连续对话效率。
3. 历史栏文案和结构偏工程化。“当前运行期记录”不适合学生端主界面，可改为“会话记录”并强化当前会话、消息数量和可继续状态。
4. 顶部文案偏开发说明。“Phase 3R”“Qwen/DashScope 流式代理”适合开发日志，不适合学生端 UI。
5. 空态、错误态、流式态已有功能但表达较基础，需要让学生能明确知道当前可做什么、模型是否正在回复、失败后如何恢复。
6. 移动端可重排，但长回答阅读密度偏紧，历史栏和主会话的优先级需要更明确。

## 4. 目标

把 `/app/student/chatbox` 从功能 Demo 页面打磨为可信、克制、可持续使用的学生端 AI 咨询会话台。

成功标准：

- 学生进入页面后，第一眼知道这是“AI 咨询助手”而不是开发测试页。
- 消息列表在会话区域内部滚动，输入框在桌面和移动端保持可见或易于回到可输入位置。
- 历史栏能清楚表达已有会话、当前会话和新会话入口。
- 空态能引导学生开始咨询，不显得空白或技术化。
- 流式输出、停止生成、错误重试、新会话等状态都清晰可见。
- 移动端 390px 宽度下无横向溢出，文本可读，触控目标足够。

## 5. 方案选项

| 方案 | 描述 | 优点 | 风险 | 回滚 | 结论 |
| --- | --- | --- | --- | --- | --- |
| A. 轻量布局修复 | 只固定消息区和输入框，少量修改文案和 spacing | 最快，风险最低 | 视觉与状态仍可能偏粗糙 | 回滚 CSS 与少量 JSX | 可接受但不推荐作为终版 |
| B. 产品级会话台打磨 | 在不改 API 的前提下，重整 Chatbox 头部、历史栏、消息区、输入区、空态、错误态、流式态和移动端 | 影响最大，符合 Phase 3R 目标，仍保持范围可控 | 需要同时修改 JSX 与 CSS，浏览器验证成本更高 | 回滚 `StudentChatboxPage.tsx` 与 `App.css` | 推荐 |
| C. 抽象通用 Chat 组件并预备多角色复用 | 把学生 Chatbox 拆成可复用组件，为教师/辅导员端做准备 | 长期扩展性好 | 会扩大本轮范围，容易提前进入教师/辅导员端 | 回滚面较大 | 暂不推荐 |

## 6. 推荐方案

采用方案 B：产品级会话台打磨。

原因：

- 当前最大问题不是颜色或卡片美化，而是会话台结构不符合聊天产品的连续使用模型。
- 方案 B 能直接解决输入框离开视口、状态表达弱、文案工程化、移动端阅读弱等核心问题。
- 方案 B 不需要新增依赖，不修改后端，不改变数据契约，仍处于 `SDAR-0008` 已批准边界内。
- 方案 C 的复用抽象应等学生端体验稳定后再做，避免为了未来多角色复用牺牲当前学生端质量。

## 7. 设计方向

界面 register：产品 UI。

色彩策略：Restrained。以浅色工作台为主，蓝色仅用于主操作、当前会话、状态提示和焦点，不做装饰性大面积渐变。

使用场景：学生在电脑或手机上带着具体困惑进入会话页，希望快速继续提问、看到回复进度，并在必要时知道如何停止、重试或寻求人工帮助。

参考方向：

- Claude / ChatGPT / Qwen：居中线程式消息流、底部常驻输入框、左侧会话历史、低工程噪音。
- assistant-ui：使用 `Thread`、`Composer`、`ThreadListRuntime`、`LocalRuntime` / `ExternalStoreRuntime`、`ModelSelector` 等能力承接聊天页交互。
- Linear：克制、清晰、低噪音的产品工作台密度。

## 8. 技术栈与后续对接核对

本审批包与 `SDAR-0002` 已批准的核心前端技术栈一致，但组件库边界需要补充确认。

已批准前端技术栈：

- React
- TypeScript
- Vite
- React Router
- Ant Design / shadcn-ui 或自定义样式
- 桌面端优先，移动端同步适配
- 最终必须保持前后端 API 串联完整

原推荐实现采用：

- 继续使用现有 Vite React SPA 工程，不创建第二套前端工程。
- 继续使用 TypeScript，不引入 JavaScript-only 页面或独立静态原型替代正式页面。
- 继续挂载在 React Router 已有路由 `/app/student/chatbox`，不新增并行路由体系。
- 继续使用 Ant Design 的 `Button`、`Input.TextArea`、`Alert`、`Tag`、`Empty` 等现有组件。
- 继续使用 `@ant-design/icons`，不新增图标库。
- 继续使用当前 `App.css` 中的项目级样式方式，但只新增或修改 Chatbox 专属 class，避免影响首页、登录页和其他工作台。
- 不新增 shadcn/ui、Tailwind、CSS-in-JS、状态管理库、请求库或动画库。
- 不修改 FastAPI API 契约；前端仍通过现有 `apiBase` 调用 `/api/v1/student/conversations` 和 `/api/v1/student/chat/stream`。

产品经理最新反馈：

- React + TypeScript + Vite 已确认。
- 产品经理更偏好 Claude / ChatGPT / Qwen 风格的居中线程式聊天页面。
- 2026-05-26，产品经理审阅 assistant-ui 专项调研后，批准采用 assistant-ui 作为学生 Chatbox 与后续 Chat 页的主前端聊天框架，放弃 Ant Design X 作为 Chatbox 主路线。

因此，本轮组件库路线已确认，可进入后续小任务实现节点。

### assistant-ui 审批边界

assistant-ui 是 React AI Chat UI/runtime 框架，方向上最匹配 Claude / ChatGPT / Qwen 式聊天页面。产品经理已批准将其作为本轮学生 Chatbox 的主前端方案。

批准内容：

- 新增 `@assistant-ui/react` 作为学生 Chatbox 主前端聊天框架。
- 可按需新增 `@assistant-ui/react-markdown` 支撑 AI 回复 Markdown 渲染。
- 首轮优先使用 assistant-ui primitives / runtime adapter，与本项目 CSS 结合，不默认引入 Tailwind / shadcn 初始化。
- 通过 `LocalRuntime` 或 `ExternalStoreRuntime` 适配现有 FastAPI SSE 与当前运行期会话记录。
- 使用 `Thread` / `Composer` 承接居中消息流和底部输入区。
- 使用 `ThreadListRuntime` 或自定义历史栏接入现有 `/api/v1/student/conversations`。
- 可加入 `ModelSelector`，但首轮只启用已批准的 Qwen 模型；其他模型不得暗示已可用。

明确不批准：

- 不使用浏览器直连模型 provider。
- 不在前端保存或暴露模型 API Key。
- 不在本轮启用未审批的多模型 provider。
- 不在本轮启用 web search、RAG、真实学校资源检索、附件上传处理或数据库持久化。
- 不在本轮实现教师端/辅导员端 Chatbox。

后续对接预留：

- 本轮可先在学生端页面内部建立 assistant-ui runtime adapter，不提前抽象多角色通用 Chat shell。
- 如果后续扩展教师端/辅导员端 Chatbox，需要单独审批复用边界，再决定是否提取共享 Thread shell、message list、composer、history rail 和 role-specific prompt。
- 本轮 polish 不改变消息数据结构、会话 id、SSE 事件解析或 token/session 传递方式，因此不会阻断后续 API、持久化或多角色对接。

结论：`SDAR-0009` 不更换核心 React + TypeScript + Vite 技术方案，但组件库路线更新为 assistant-ui 主路线。Ant Design X 不再作为学生 Chatbox 主实现方案。

## 9. 具体打磨范围

### 本轮做

1. 固定 Chatbox 会话台结构：
   - 页面主体控制在视口内。
   - 左侧历史栏和右侧会话区各自内部滚动。
   - 输入区固定在会话区底部。

2. 优化顶部与文案：
   - 弱化 `Phase 3R` 和 provider 技术说明。
   - 页面主标题转为学生可理解的“AI 咨询助手”或同等表达。
   - 保留 Demo/AI 生成边界，但放在次级说明位置。

3. 优化历史栏：
   - “当前运行期记录”改为“会话记录”。
   - 明确当前选中会话。
   - 空历史时给出清楚提示。
   - 保持选择会话时不能中断当前流式生成的安全行为。

4. 优化消息区：
   - 学生消息和 AI 消息保持稳定视觉区分。
   - 长回答改善段落宽度、行高、间距。
   - 流式回复时显示明确的“正在回复”状态。

5. 优化输入区：
   - 输入框始终可见。
   - `Enter` 发送、`Shift+Enter` 换行保持不变。
   - 发送、停止、重试、新会话的可用/禁用状态更清晰。
   - 支持 assistant-ui Composer 的停止、重试、编辑、复制等标准聊天交互入口。

6. 优化空态、错误态和移动端：
   - 空态用问题 starter 引导学生开始。
   - 错误态提供明确恢复路径。
   - 390px 移动宽度下避免横向溢出，降低气泡宽度和 padding 压力。

7. 模型与模式入口：
   - 首轮可展示模型选择入口，但只启用已批准 Qwen 模型。
   - 模式选择只允许表达已批准的咨询体验；联网搜索、RAG、附件上传等能力不得在 UI 中伪装为可用。

### 本轮不做

- 不修改 `POST /api/v1/student/chat/stream`。
- 不修改 `/api/v1/student/conversations`。
- 不新增数据库持久化。
- 不接入 RAG、真实学校资料或真实学生数据。
- 不新增教师端/辅导员端 Chatbox。
- 不新增除 assistant-ui 及必要配套包之外的组件库或设计依赖。
- 不重做首页或 `/app/student` 入口页。

## 10. 小节点拆分

| 节点 | 内容 | 验收 |
| --- | --- | --- |
| P3R-N5A | 会话台布局重构 | 桌面端输入区首屏常驻，消息区内部滚动 |
| P3R-N5B | 历史栏与头部文案打磨 | 工程文案降级，学生端主任务清晰 |
| P3R-N5C | 空态、错误态、流式态打磨 | 无会话、生成中、停止、失败、重试均可理解 |
| P3R-N5D | 移动端阅读与触控优化 | 390px 截图无横向溢出，输入和按钮可用 |
| P3R-N5E | 验证与日志更新 | `npm run lint`、`npm run build`、桌面/移动截图、日志同步 |
| P3R-N5F | assistant-ui adapter POC | 保留现有 FastAPI SSE、停止、重试、会话记录，不暴露前端密钥 |

## 11. 验收方式

实现后必须验证：

1. `frontend> npm run lint` 通过。
2. `frontend> npm run build` 通过，允许保留既有 Vite chunk size warning。
3. 浏览器打开 `/app/student/chatbox`，控制台 0 errors。
4. 桌面端截图证明输入区在会话台底部常驻。
5. 移动端 390px 截图证明无横向溢出，消息和输入区可读可用。
6. 发送真实消息后能看到流式输出。
7. 停止生成、重试、新会话仍可用。
8. 会话历史选择仍可用。

## 12. 风险与缓解

| 风险 | 严重性 | 缓解 |
| --- | --- | --- |
| CSS 改动影响登录页或首页 | 中 | 只使用 Chatbox 专属 class，避免扩大选择器 |
| 固定高度导致小屏内容拥挤 | 中 | 桌面使用视口高度，移动端使用分段布局和内部滚动 |
| 状态文案过度简化导致边界不清 | 中 | 保留 Demo/AI 生成说明，但放在次级状态区 |
| 视觉 polish 误伤流式逻辑 | 高 | 不改 SSE 解析和 API 调用主逻辑，只调整渲染结构与状态表达 |
| 多角色复用提前膨胀 | 中 | 本轮不抽象通用 Chat engine UI，学生端稳定后另行审批 |
| 打磨时偏离已批准前端技术栈 | 中 | React + TypeScript + Vite 不变；组件库新增必须经本审批包确认 |
| 引入 assistant-ui 后误以为可绕过后端代理 | 高 | assistant-ui 只负责前端 Chat UI/runtime；模型调用、密钥、权限、会话权威数据仍由 FastAPI 负责 |
| 模型选择 UI 暗示多模型已批准 | 中 | 首轮只启用 Qwen，其余模型隐藏或标注待审批 |
| 模式/附件入口暗示 web search、RAG 或上传已启用 | 高 | 未审批能力不显示为可用；真实搜索、RAG、附件上传单独审批 |

## 13. 回滚方式

如本轮打磨不达预期：

- 回滚 `frontend/src/StudentChatboxPage.tsx` 的结构调整。
- 回滚 `frontend/src/App.css` 中 Chatbox 专属样式。
- 删除新增 assistant-ui 依赖和 runtime adapter。
- 保留 `SDAR-0008` 已实现的真实模型 API、流式输出和运行期历史能力。

## 14. 产品经理需确认

1. 是否批准方案 B：产品级会话台打磨。
批准
2. 是否确认本轮只打磨 `/app/student/chatbox`，暂不处理 `/app/student` 入口页。
批准，但是后续需要做 `/app/student` 入口页的改版，以保持整体风格一致。（写入开发路线中）
3. 是否接受本轮不做多角色通用组件抽象，先把学生端会话台打磨稳定。
批准，优先稳定学生端体验，教师/辅导员端后续再审批复用边界和抽象程度。
4. 是否确认本轮继续沿用 `SDAR-0002` 已批准的 React + TypeScript + Vite + Ant Design 技术路线，不新增并行前端技术栈。
React + TypeScript + Vite确定，但是组件库我们需要进行探讨，我在看ant design X组件库的效果

放弃 Ant Design X 作为 Chatbox 主路线，采用 assistant-ui 作为学生 Chatbox 与后续 Chat 页主前端聊天技术栈
5. 是否批准新增 assistant-ui 作为学生 Chatbox 与后续 Chat 页主前端聊天框架，放弃 Ant Design X 作为 Chatbox 主路线。
批准。采用 assistant-ui，保留 FastAPI 后端代理和前端无密钥边界。首轮只接学生端，模型选择只启用已批准 Qwen；web search、RAG、附件上传、持久化和多角色 Chatbox 后续单独审批。

新增内容（重要）
下一步不需要开发代码在详细阅读我的审批回复之后，和我确定一下我们学生端聊天页面的风格以及排版，在所有前端基础信息全部确定之后，再开始开发

## 14.1 官方 Assistant UI 示例迁移与配色/依赖审批补充

日期：2026-05-27  
状态：待产品经理文件内审批  
关联方案文档：`.omx/specs/assistant-ui-ai-sdk-official-example-adoption-plan.md`

### 补充背景

产品经理进一步指定目标效果参考 Assistant UI 官方 AI SDK 示例：`https://www.assistant-ui.com/examples/ai-sdk`。

本次补充的目标不是继续手写近似样式，而是迁移官方示例截图中的组件结构和页面布局，包括：

- 全高应用壳。
- 左侧会话历史栏。
- 顶部工具栏。
- 模型选择入口。
- 居中线程式聊天区。
- 底部常驻 composer。
- 桌面/移动端 Light/Dark 模式。

同时，产品经理补充要求：配色方案遵循 `http://127.0.0.1:5173/` 当前首页的配色方案，而不是照搬官方示例默认黑灰色。

### 当前核对结论

官方示例可以迁移为本项目学生 Chatbox 的目标组件结构，但不能整套一键搬运运行时和后端协议。

可迁移：

- Assistant UI 官方 `thread`、`thread-list`、`assistant-sidebar` registry 组件结构。
- 官方示例中的 sidebar/header/thread/composer 页面骨架。
- 官方示例中的移动端折叠/抽屉式会话导航思路。

不在本轮迁移：

- `useChatRuntime` / Vercel AI SDK runtime。
- Next.js API route。
- `streamText().toUIMessageStreamResponse()` 协议。
- web search、RAG、附件、slash command、mention、真实 tool-call、多模型真实切换。

### 配色基准

Chatbox 的 Light/Dark 主题以 `http://127.0.0.1:5173/` 当前首页 token 为基准，并映射到 shadcn/Assistant UI 语义 token。

当前首页 Light token 参考：

- `--bg: #faf9f5`
- `--bg-elevated: #fffdf8`
- `--surface: #f0eee7`
- `--surface-strong: #e7e3da`
- `--ink: #242321`
- `--ink-strong: #141413`
- `--muted: #53534f`
- `--subtle: #77766f`
- `--line: rgba(20, 20, 19, 0.14)`
- `--primary: #122e8a`
- `--primary-ink: #fbf8f2`
- `--secondary: #d8dcea`

当前首页 Dark token 参考：

- `--bg: #0d131a`
- `--bg-elevated: #121a23`
- `--surface: #17212d`
- `--surface-strong: #1e2a36`
- `--ink: #efd6c0`
- `--ink-strong: #fff0df`
- `--muted: #d69a72`
- `--subtle: #a86d4c`
- `--line: rgba(171, 89, 36, 0.24)`
- `--line-strong: rgba(171, 89, 36, 0.48)`
- `--primary: #ab5924`
- `--primary-ink: #0d131a`
- `--secondary: #c27645`

### 推荐方案

采用“官方 UI 组件层迁移 + 保留当前 FastAPI SSE runtime”。

具体含义：

- 在现有 React + TypeScript + Vite 前端中引入 shadcn/Tailwind/lucide 及 Assistant UI 官方 registry 组件。
- 组件结构迁移官方 AI SDK 示例截图。
- Light/Dark 配色遵循 `http://127.0.0.1:5173/` 当前首页主题。
- runtime 保留当前 `ExternalStoreRuntime` + FastAPI SSE。
- 后端接口保持不变：
  - `GET /api/v1/student/conversations`
  - `POST /api/v1/student/chat/stream`
- 首轮只显示/启用已批准 Qwen。
- 未审批能力不展示为可用。

### 最终需求边界确认

本轮需求确定为：前端 UI 层尽可能采用 Assistant UI 官方成品组件与 shadcn 组件体系；协议适配层保留最小自研 adapter。

具体边界：

- UI 层成品化：`Thread`、`ThreadList`、`AssistantSidebar`、`Composer`、Markdown 渲染、空态、加载态、错误态、流式态等优先采用官方 registry 或等价移植组件。
- 协议层最小胶水：当前 FastAPI SSE 到 Assistant UI 消息状态的转换不能完全成品化，本轮保留 `ExternalStoreRuntime` + adapter。
- 页面布局稳定：桌面端为左侧会话栏 + 居中线程式聊天区 + 底部常驻 composer；移动端为会话历史折叠/抽屉化 + 主聊天单列。
- 体验约束：去掉不必要的消息 hover 复制/重试浮层动画；保留必要的发送、停止、重试、流式输出、错误恢复、会话历史。
- 范围约束：本轮不切换到 `useChatRuntime` / Vercel AI SDK runtime，不引入 Next.js 前端，不开放 web search、RAG、附件、真实工具调用、多模型真实切换。

### 后续 FastAPI + LangGraph 衔接策略

项目总规划中的 FastAPI + LangGraph 路线与本轮前端组件化不冲突。后续进入 FastAPI + LangGraph 阶段时，以 `Yonom/assistant-ui-langgraph-fastapi` 作为后端流协议与 LangGraph 路由参考；前端保留本轮已迁移的 Assistant UI 成品组件层，仅评估替换 runtime adapter / streaming protocol，不重新设计 Chatbox 页面。

后续可复用 Yonom 方案的内容：

- FastAPI 路由包装 LangGraph graph 的方式。
- 将前端消息转换为 LangChain/LangGraph messages 的思路。
- 使用 LangGraph `astream` 进行流式输出的方式。
- 使用 `assistant-stream` 将 LangGraph 输出转为 assistant-ui 兼容流的方式。
- 未来 tool call / frontend tool 的协议参考，但需单独审批后才能开放。

后续不直接照搬的内容：

- Yonom 的 Next.js 前端工程。
- Yonom 的 `useEdgeRuntime` 作为当前 Vite 前端的直接替代。
- Yonom 默认 OpenAI/LangChain provider 配置。
- 未审批的工具调用、web search、RAG、附件或多模型切换能力。

预期迁移影响：

- 如果未来 LangGraph 后端继续输出当前 `/api/v1/student/chat/stream` SSE 合同，前端 UI 基本不变，adapter 小幅调整。
- 如果未来改为 `assistant-stream` 或 assistant-ui 兼容数据流，主要替换 runtime adapter / streaming protocol，保留本轮迁移后的 Thread、ThreadList、Sidebar、Composer 页面组件。
- 因此，本轮必须把 UI 组件层与 runtime adapter 层分离，避免未来后端升级导致聊天页面大幅重做。

### 本补充批准内容

待产品经理确认：

1. 是否批准在现有 Vite 前端中初始化 shadcn/Tailwind。
2. 是否批准新增 `lucide-react`。
3. 是否批准新增 Assistant UI registry 所需的 shadcn 基础组件，例如 `button`、`skeleton`、`sheet`、`resizable`、`tooltip` 等。
4. 是否批准新增 `@assistant-ui/react-markdown`，用于 AI 回复 Markdown 渲染。
5. 是否明确本轮不采用 `@assistant-ui/react-ai-sdk` 和 `ai` runtime，只保留当前 FastAPI SSE。
6. 是否确认 Chatbox 的 Light/Dark 配色基准来自 `http://127.0.0.1:5173/` 当前首页主题；官方 Assistant UI 示例只作为组件结构、布局和交互参考。
7. 是否确认后续 FastAPI + LangGraph 阶段参考 `Yonom/assistant-ui-langgraph-fastapi` 的后端协议与 LangGraph 路由思路，但本轮不引入 LangGraph、不切换后端协议；未来只优先替换 runtime adapter，不重新设计 Chatbox 页面。

产品经理回复区：

- 1：批准
- 2：批准
- 3：批准
- 4：批准
- 5：批准本轮不采用 `@assistant-ui/react-ai-sdk` 和 `ai` runtime，只保留当前 FastAPI SSE + `ExternalStoreRuntime` adapter；未来如需切换 AI SDK、assistant-stream 或 LangGraph 协议，单独审批。
- 6：批准
- 7：同意

## 15. 审批记录

Status: `approved`

Product Manager decision:

- 2026-05-26：产品经理批准方案 B、确认本轮只打磨 `/app/student/chatbox`、确认不先做多角色通用组件抽象。
- 2026-05-26：产品经理要求继续探讨组件库；React + TypeScript + Vite 已确认，Ant Design X 是否进入本轮待定。
- 2026-05-26：产品经理审阅 assistant-ui 专项调研与原型后，批准采用 assistant-ui 作为学生 Chatbox 与后续 Chat 页主前端聊天框架；放弃 Ant Design X 作为 Chatbox 主路线。
- 当前状态：组件库路线已批准；但产品经理新增前置门控，下一步先确认学生端聊天页面的风格与排版，所有前端基础信息确定后，再进入 assistant-ui 学生端 Chatbox adapter POC 与页面打磨实现节点。
- 2026-05-27：已补充官方 Assistant UI AI SDK 示例迁移、shadcn/Tailwind/lucide 依赖、`5173` 首页 Light/Dark 配色基准等审批项；等待产品经理在第 14.1 节文件内审批。
- 2026-05-27：根据产品经理进一步确认，补充“UI 层成品化、协议层保留最小 adapter、Yonom 仅作为后续 FastAPI + LangGraph 后端协议参考”的最终需求边界；待产品经理审阅后进入实现流程。
