# Phase 3R 日志：真实模型学生端 Chatbox

日期：2026-05-25
状态：待产品复核，已完成节点见下方
分支：`phase/02-demo-login-role-routing`

## 范围

Phase 3R 是对原 Phase 3“仅确定性 Demo 学生端流程”的边界修订。新的产品经理方向是：学生端 Chatbox 使用真实模型 API 回复，同时继续由 FastAPI 作为后端权威边界和 API Key 安全边界。

已确认边界：

- 先把学生端 Chatbox 作为独立页面开发和验证。
- 使用后端代理的真实模型流式响应。
- 复用项目文件中已经配置的 Qwen 模型 API，不新增第二套 provider 配置体系。
- 本阶段聊天记录继续使用当前内存态 Demo runtime。
- 前端不暴露模型 API Key。
- 本节点不引入数据库持久化、RAG/vector/provider retrieval、文档摄取、生产 SSO 或真实学生数据。

## 任务节点

### P3R-N1：边界修订审批包

状态：已完成

产物：

- `.omx/decisions/SDAR-0008-real-model-student-chatbox.md`

验证证据：

- 产品经理已于 2026-05-25 完成文件内审阅。
- 已批准方案：先做学生端独立 Chatbox，FastAPI 代理真实模型 API，聊天历史仅使用 runtime，辅导员/教师端 Chatbox 延后到学生端 Chat 引擎验证后再做。
- 约束：使用项目已配置的 Qwen 模型 API，不新增新的模型 API family。

### P3R-N2：后端真实模型流式代理

状态：已完成

范围：

- 在旧项目环境文件中定位到已有 Qwen/DashScope 配置名：
  - `.env.legacy-20260513T145513`：`QWEN_API_KEY`、`QWEN_MODEL`
  - `backend/.env.legacy-20260513T145513`：`DASHSCOPE_API_KEY`、`DASHSCOPE_API_BASE_URL`、`DASHSCOPE_MODEL`、`ENABLE_THINKING`
- 使用既有配置体系和 legacy alias 增加后端 Qwen/DashScope runtime settings。
- 增加学生端真实模型 SSE 路由：`POST /api/v1/student/chat/stream`。
- 为流式学生消息和助手回复写入内存态 runtime conversation。
- 当模型 provider 配置缺失时，返回明确的 `503` 失败状态。

验证证据：

- 在 `backend/` 执行 `python -m ruff check .`：通过。
- 在 `backend/` 执行 `python -m pytest`：20 个测试通过。

### P3R-N3：独立学生端 Chatbox 页面

状态：已完成

范围：

- 先构建独立学生端 Chatbox 路由/页面，再合并进 `/app/student` 工作区。
- 支持流式输出、停止生成、重试/错误态、新会话和当前内存态聊天历史。
- 保留 `/app/student` 作为现有角色工作区，只增加进入独立页面的入口按钮。
- 新增独立路由：`/app/student/chatbox`。

验证证据：

- 在 `frontend/` 执行 `npm run lint`：通过。
- 在 `frontend/` 执行 `npm run build`：通过，仍存在既有 Vite chunk size warning。

### P3R-N4：验证

状态：已完成

范围：

- 后端定向测试。
- 前端 lint/build。
- 本地服务可用时执行浏览器 smoke。

验证证据：

- 后端：`python -m ruff check .` 通过。
- 后端：`python -m pytest` 通过，20 个测试。
- 前端：`npm run lint` 通过。
- 前端：`npm run build` 通过，仍存在既有 chunk size warning。
- 浏览器 smoke：
  - 前端验证服务：`http://127.0.0.1:5180`。
  - 后端验证服务：`http://127.0.0.1:8001`，因为本地 PostgreSQL 未运行，所以使用 `--lifespan off`。
  - Student Demo 登录后可到达 `/app/student`。
  - `/app/student` 入口可打开 `/app/student/chatbox`。
  - Chatbox 中出现真实 Qwen/DashScope 流式模型回复。
  - 停止生成后状态变为 `已停止`。
  - 新会话现在会保留一个空的新会话状态，同时保留 runtime 历史栏。
  - Playwright 控制台检查：0 errors / 0 warnings。
  - 截图：`output/playwright/p3r-student-chatbox-smoke.png`。

已知验证说明：

- 正常后端 lifespan 启动需要 PostgreSQL。本地浏览器 smoke 使用 `uvicorn --lifespan off`，用于在不启动数据库的情况下验证内存态 Phase 3R Chatbox 路径。

### P3R-N5：Assistant UI 生产版 Chatbox 打磨

状态：已完成

日期：2026-05-26

范围：

- 使用 `@assistant-ui/react` runtime 和 primitives 重构 `/app/student/chatbox`。
- 保持既有 FastAPI endpoints 不变：
  - `GET /api/v1/student/conversations`
  - `POST /api/v1/student/chat/stream`
- 保留后端代理 Qwen 流式输出、前端无 Key 边界、runtime 会话历史、停止生成、重试和新会话。
- 应用 Claude 风格的产品布局：温暖克制的页面基底、左侧会话栏、居中线程、底部固定输入框、移动端横向历史栏。
- 增加局部 GSAP 入场/消息动效，并加入 reduced-motion 保护。
- 继续隐藏未审批的模型/模式/搜索/RAG/附件控制项；首轮只展示 Qwen。

验证证据：

- 在 `frontend/` 执行 `npm run lint`：通过。
- 在 `frontend/` 执行 `npm run build`：通过，仍存在既有 Vite chunk size warning。
- 浏览器路由 smoke：Student Demo 登录后，`http://127.0.0.1:5180/app/student/chatbox` 可加载。
- 后端/API smoke：
  - `GET /api/v1/student/conversations` 返回 `200 OK`。
  - `POST /api/v1/student/chat/stream` 返回 `200 OK`。
  - SSE body 包含 `conversation`、`delta` 和 `done` events。
- 真实流式 UI smoke：
  - 生成中，输入框按钮从 `发送` 切换为 `停止`。
  - 生成完成后，状态回到 `就绪`，模型回复可见。
  - 已验证响应文本：`第二次流式烟测响应正常。`
- Playwright 控制台检查：0 errors。
- 截图：
  - `output/playwright/student-chatbox-assistant-ui-production-desktop.png`
  - `output/playwright/student-chatbox-assistant-ui-production-mobile.png`

已知验证说明：

- 移动端 390px 按设计使用横向会话历史栏。隐藏移动端 topbar exit button 后，`documentElement.scrollWidth` 等于 viewport 宽度；历史栏自身包含在独立横向滚动容器中，可容纳屏幕外条目。

### P3R-N5 最终复核：Assistant UI 结构与视觉 Smoke

状态：已完成

日期：2026-05-26

范围：

- 按 assistant-ui 文档中的 primitive 结构，将生产版输入框对齐为：在 `ThreadPrimitive.ViewportFooter` 内放置 `ComposerPrimitive.Root`。
- 保留已审批的 FastAPI SSE 边界、首轮仅展示 Qwen、隐藏附件/搜索/RAG/模式控制项，以及局部 GSAP 动效。
- 增加 Chatbox 局部移动端内容高度修复，避免全局 app content wrapper 在 390px 下产生页面级滚动。

验证证据：

- 在 `frontend/` 执行 `npm run lint`：通过。
- 在 `frontend/` 执行 `npm run build`：通过，仍存在既有 Vite chunk size warning。
- LSP diagnostics：
  - `frontend/src/StudentChatboxPage.tsx`：0 errors。
  - `frontend/src/App.css`：0 errors。
- `git diff --check`：通过。
- 浏览器布局指标：
  - 桌面端 `1440x1000`：`scrollWidth=1440`，`bodyScrollHeight=1000`，输入框在 viewport 底部可见。
  - 移动端 `390x844`：`scrollWidth=390`，`bodyScrollHeight=844`，输入框在 viewport 底部可见。
- Playwright 控制台检查：0 errors / 0 warnings，已排除 React DevTools 开发提示信息。
- 真实流式 UI smoke：
  - `POST /api/v1/student/chat/stream` 返回 `200 OK`。
  - 最终可见响应：`Assistant UI 最终烟测响应正常。`
- 截图：
  - `output/playwright/student-chatbox-assistant-ui-production-desktop-final.png`
  - `output/playwright/student-chatbox-assistant-ui-production-mobile-final.png`

### P3R-N6：学生端 Chatbox 极简视觉对齐

状态：已完成

日期：2026-05-27

范围：

- 仅打磨 `/app/student/chatbox`。
- 保持 `@assistant-ui/react` runtime/primitives 以及既有 FastAPI SSE endpoints 不变。
- 将消息呈现进一步贴近 Qwen/Claude：更轻的线程布局、不使用厚重用户消息框、不使用头像圆形强调。
- 从可见聊天界面移除每条消息的 hover 文本操作，例如复制/重试。
- 移除装饰性消息入场动效；动效只保留在状态清晰度和 reduced-motion 支持相关场景。
- 使用已审批 homepage HUD prototype palette，增加 Chatbox 局部 Light/Dark 主题支持。

非目标：

- 不改后端、模型 provider、API contract、数据库、持久化、RAG、web search、附件、教师端或辅导员端。
- 不新增依赖或替换前端技术栈。
- 不替换 P3R-N5 已完成的 assistant-ui 集成。

验证证据：

- 在 `frontend/` 执行 `npm run lint`：通过。
- 在 `frontend/` 执行 `npm run build`：通过，仍存在既有 Vite chunk size warning。
- Playwright CLI 浏览器检查：
  - Light desktop：`scrollWidth=1280`，`clientWidth=1280`，输入框可见，`actionElements=0`，`avatarElements=0`。
  - Dark desktop：`scrollWidth=1280`，`clientWidth=1280`，输入框可见。
  - Dark mobile 390x844：`scrollWidth=390`，`clientWidth=390`，`bodyScrollHeight=844`，输入框可见，`actionElements=0`，`avatarElements=0`。
- 视觉和流式 smoke 后的 Playwright 控制台检查：0 errors / 0 warnings。
- 真实流式 UI smoke：
  - 发送 prompt：`P3R-N6 smoke 1779840197249`。
  - 生成期间状态变为 `正在回复`，完成后回到 `就绪`。
  - 最终可见响应：`收到 P3R-N6 烟测信号，系统响应正常。`
- 截图：
  - `output/playwright/student-chatbox-p3r-n6-light-desktop.png`
  - `output/playwright/student-chatbox-p3r-n6-dark-desktop.png`
  - `output/playwright/student-chatbox-p3r-n6-dark-mobile.png`

已知验证说明：

- 仓库级 `git diff --check` 仍被 `frontend/src/App.tsx:540` 的既有无关空行问题阻塞；本节点编辑文件的 scoped diff check 通过。

### P3R-N6 收口复验：Assistant UI 移动抽屉可访问性与真实流式 Smoke

状态：已完成

日期：2026-05-27

范围：

- 继续保持 `/app/student/chatbox` 的 Assistant UI 官方风格组件层、shadcn/Radix Sheet、FastAPI SSE + `ExternalStoreRuntime` adapter 不变。
- 修复移动端会话记录 Sheet 的 Radix 可访问性 warning：补充隐藏的 `SheetDescription`。
- 不改变后端 API、模型 provider、消息协议、视觉布局、主题 token 或未审批能力边界。

变更文件：

- `frontend/src/components/assistant-ui/assistant-sidebar.tsx`

验证证据：

- 在 `frontend/` 执行 `npm run lint`：通过。
- 在 `frontend/` 执行 `npm run build`：通过，仍存在既有 Vite chunk size warning。
- LSP diagnostics：
  - `frontend/src/components/assistant-ui/assistant-sidebar.tsx`：0 errors。
  - `frontend/src/StudentChatboxPage.tsx`：0 errors。
- Playwright CLI 桌面 Light 验证：
  - `scrollWidth=1280`，`clientWidth=1280`。
  - `bodyScrollHeight=720`，`bodyClientHeight=720`。
  - `composerVisible=true`。
  - `viewportScrollable=true`。
  - `messageButtons=0`，`avatarLike=0`。
- Playwright CLI 桌面 Dark 验证：
  - `data-chat-theme=dark`。
  - `--chat-bg=#0d131a`。
  - `--chat-primary=#ab5924`。
  - `composerVisible=true`。
- Playwright CLI 移动端 390x844 验证：
  - `scrollWidth=390`，`clientWidth=390`。
  - `bodyScrollHeight=844`，`bodyClientHeight=844`。
  - 桌面侧栏隐藏，移动会话记录按钮可见。
  - `composerVisible=true`。
  - `messageButtons=0`，`avatarLike=0`。
- 移动端会话记录 Sheet 打开后控制台：0 errors / 0 warnings。
- 真实流式 UI smoke：
  - 发送 prompt：`P3R final smoke 20260527 请用一句中文回复：流式正常。`
  - 网络请求：`POST http://127.0.0.1:8001/api/v1/student/chat/stream => 200 OK`。
  - 会话刷新：`GET http://127.0.0.1:8001/api/v1/student/conversations => 200 OK`。
  - 最终可见响应：`流式正常。`
- 截图：
  - `output/playwright/student-chatbox-p3r-final-light-desktop.png`
  - `output/playwright/student-chatbox-p3r-final-dark-desktop.png`
  - `output/playwright/student-chatbox-p3r-final-dark-mobile.png`
  - `output/playwright/student-chatbox-p3r-final-mobile-after-stream.png`

已知验证说明：

- 仓库级 `git diff --check` 当前仍被无关文件阻塞：
  - `.omx/decisions/SDAR-0009-student-chatbox-product-polish.md:289-290` 存在 Markdown 尾随空格。
  - `frontend/src/App.tsx:538` 存在既有 EOF 空行。
- 本轮收口补丁未修改这些无关内容。

### P3R-N6B：SDAR-0009 可见打磨收口

状态：已完成，待产品经理视觉审阅

日期：2026-05-27

范围：

- 按 `SDAR-0009` 继续打磨 `/app/student/chatbox` 可见体验。
- 保持 Assistant UI 组件层、`ExternalStoreRuntime`、FastAPI SSE、Qwen-only 首轮模型展示不变。
- 去除用户消息强气泡/卡片感，改为更接近 Claude/Qwen 的右侧轻文本呈现。
- 删除 Chatbox 整页 GSAP 入场动效，避免页面审阅和截图捕获到半透明过渡态。
- 修正移动端输入区：发送按钮恢复紧凑按钮形态，隐藏移动端不可用/截断的重试文本入口。
- 调轻 composer 聚焦光圈，只保留外层输入区焦点表达，不再出现内部输入框矩形描边。

非目标：

- 不改后端 API、模型 provider、SSE 协议、数据库、持久化、RAG、web search、附件、工具调用、多模型真实切换、教师端或辅导员端 Chatbox。
- 不新增依赖，不替换前端技术栈。

变更文件：

- `frontend/src/StudentChatboxPage.tsx`
- `frontend/src/components/assistant-ui/thread.tsx`
- `frontend/src/App.css`

验证证据：

- 在 `frontend/` 执行 `npm run lint`：通过。
- 在 `frontend/` 执行 `npm run build`：通过，仍存在既有 Vite chunk size warning。
- LSP diagnostics：
  - `frontend/src/StudentChatboxPage.tsx`：0 errors。
  - `frontend/src/App.css`：0 errors。
  - `frontend/src/components/assistant-ui/thread.tsx`：0 errors。
- 代码边界复核：
  - `frontend/src/StudentChatboxPage.tsx` 继续使用 `useExternalStoreRuntime`。
  - 模型调用继续通过 `/api/v1/student/chat/stream`。
  - 会话历史继续通过 `/api/v1/student/conversations`。
  - 当前 Chatbox 代码中未保留 `ActionBar` / `message-action-button` 类消息 hover 操作浮层。
- 最终截图：
  - `output/playwright/student-chatbox-sdar0009-final-light-desktop.png`
  - `output/playwright/student-chatbox-sdar0009-final-dark-desktop.png`
  - `output/playwright/student-chatbox-sdar0009-final-light-mobile.png`
  - `output/playwright/student-chatbox-sdar0009-final-dark-mobile.png`

已知验证说明：

- Playwright CLI 截图已完成并可作为当前视觉审阅依据。
- 额外 DOM 指标脚本受当前 Windows `npx -p playwright` 包解析限制未形成稳定输出；本次收口不以该脚本作为通过条件。
- 仓库仍存在与本轮无关的其他未提交/未跟踪变更；本轮未回滚或清理用户已有工作。

### P3R-N6C：流式状态重复动画修复

状态：已完成

日期：2026-05-29

范围：

- 修复 `/app/student/chatbox` 中“正在回复”流式状态在 hover 或 token 增量渲染时出现快速重复播放动画的问题。
- 保持 Assistant UI 组件层、`ExternalStoreRuntime`、FastAPI SSE、Qwen-only 模型展示不变。
- 不修改后端 API、SSE 协议、模型 provider、会话历史、停止生成或重试逻辑。

变更文件：

- `frontend/src/components/assistant-ui/thread.tsx`
- `frontend/src/App.css`

实现说明：

- 将 assistant 回复正文的 `MarkdownText smooth` 固定为 `false`，避免流式 token 更新时反复触发平滑文本动画。
- 移除 `.aui-streaming-label span` 的无限 pulse 动画和对应 keyframes，保留静态“正在回复”状态点。

验证证据：

- 在 `frontend/` 执行 `npm run lint -- --quiet`：通过。
- 在 `frontend/` 执行 `npm run build`：通过，仍存在既有 Vite chunk size warning。
- LSP diagnostics：
  - `frontend/src/components/assistant-ui/thread.tsx`：0 errors。
  - `frontend/src/App.css`：0 errors。
- Playwright CLI 控制台检查：0 errors / 0 warnings。
- 截图：
  - `output/playwright/student-chatbox-stream-animation-fix.png`
