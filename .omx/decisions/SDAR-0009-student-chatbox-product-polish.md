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

### Ant Design X 边界判断

Ant Design X 属于 Ant Design 体系下的 React AI 界面组件库，方向上匹配 Chatbox 场景，但引入 `@ant-design/x` 仍然会改变本轮“只使用现有 Ant Design 组件和自定义 CSS”的原边界。

可选方案：

| 方案 | 描述 | 优点 | 风险 | 结论 |
| --- | --- | --- | --- | --- |
| X-A. 不引入 Ant Design X | 沿用现有 `antd` + `@ant-design/icons` + 自定义 CSS 完成 Chatbox 打磨 | 不新增依赖；实现可控；最快进入打磨 | 需要手写消息气泡、输入区和历史栏细节 | 保守推荐 |
| X-B. 引入 Ant Design X UI 组件，但只用展示层组件 | 评估使用 `Bubble`、`Sender`、`Conversations` 等 AI 对话 UI 组件；仍保留现有后端 API 与 SSE 逻辑 | 更贴合 AI Chatbox 场景；与 Ant Design 视觉体系一致；未来多角色 Chat 复用更自然 | 新增依赖；需要适配现有消息结构和状态；需要重新验证打包体积与样式一致性 | 可选，需产品经理批准 |
| X-C. 引入 Ant Design X SDK / request 流程 | 使用 `useXAgent`、`useXChat`、`XRequest` 等数据流能力 | 可能减少前端会话状态代码 | 容易绕过当前 FastAPI 后端权威边界；可能与现有 SSE 代理重复；增加 API 安全风险 | 暂不推荐 |

推荐判断：

- 如果目标是尽快打磨当前页面并保持最小风险，采用 X-A。
- 如果产品经理明确认可 Ant Design X 的视觉效果，并接受新增依赖，则采用 X-B，但只允许使用 UI 展示层组件，不使用浏览器直连模型 API 或 `dangerouslyApiKey` 形态。
- X-C 不进入本轮，因为 `SDAR-0008` 已明确模型 API 必须走 FastAPI 后端代理，前端不得持有模型密钥。

后续对接预留：

- 若采用 X-A，本轮不抽象通用多角色 Chat 组件，但 JSX 结构和 class 命名应避免学生端专属视觉硬编码污染未来复用。
- 若采用 X-B，可把 Ant Design X 组件适配层限制在学生端页面内部，不在本轮扩展到教师/辅导员端。
- 如果后续扩展教师端/辅导员端 Chatbox，需要单独审批复用边界，再决定是否提取共享 Chat shell、message list、composer 和 history rail。
- 本轮 polish 不改变消息数据结构、会话 id、SSE 事件解析或 token/session 传递方式，因此不会阻断后续 API、持久化或多角色对接。

结论：`SDAR-0009` 不需要更换核心前端技术方案，但需要在实现前确认组件库路线：X-A 现有 Ant Design 组件路线，或 X-B Ant Design X UI 展示层路线。

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

6. 优化空态、错误态和移动端：
   - 空态用问题 starter 引导学生开始。
   - 错误态提供明确恢复路径。
   - 390px 移动宽度下避免横向溢出，降低气泡宽度和 padding 压力。

### 本轮不做

- 不修改 `POST /api/v1/student/chat/stream`。
- 不修改 `/api/v1/student/conversations`。
- 不新增数据库持久化。
- 不接入 RAG、真实学校资料或真实学生数据。
- 不新增教师端/辅导员端 Chatbox。
- 不新增组件库或设计依赖。
- 不重做首页或 `/app/student` 入口页。

## 10. 小节点拆分

| 节点 | 内容 | 验收 |
| --- | --- | --- |
| P3R-N5A | 会话台布局重构 | 桌面端输入区首屏常驻，消息区内部滚动 |
| P3R-N5B | 历史栏与头部文案打磨 | 工程文案降级，学生端主任务清晰 |
| P3R-N5C | 空态、错误态、流式态打磨 | 无会话、生成中、停止、失败、重试均可理解 |
| P3R-N5D | 移动端阅读与触控优化 | 390px 截图无横向溢出，输入和按钮可用 |
| P3R-N5E | 验证与日志更新 | `npm run lint`、`npm run build`、桌面/移动截图、日志同步 |

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
| 引入 Ant Design X 后绕过后端代理 | 高 | 若批准 X-B，只使用 UI 展示层组件，不使用前端直连模型 API、`XRequest` 或 `dangerouslyApiKey` |

## 13. 回滚方式

如本轮打磨不达预期：

- 回滚 `frontend/src/StudentChatboxPage.tsx` 的结构调整。
- 回滚 `frontend/src/App.css` 中 Chatbox 专属样式。
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
## 15. 审批记录

Status: `pending-component-library-review`

Product Manager decision:

- 2026-05-26：产品经理批准方案 B、确认本轮只打磨 `/app/student/chatbox`、确认不先做多角色通用组件抽象。
- 2026-05-26：产品经理要求继续探讨组件库；React + TypeScript + Vite 已确认，Ant Design X 是否进入本轮待定。
- 当前停止点：组件库路线未定前，不进入实现。
