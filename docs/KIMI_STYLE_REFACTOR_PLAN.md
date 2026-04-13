# Kimi 风格流式输出改造 - 详细实施计划

> 每个实现步骤完成后必须执行：**端到端测试 → 代码审查 → 确认通过后再进入下一步**

---

## Phase 1：系统 Prompt 增强（Markdown 丰富度）

### 1.1 修改 `prompts.py` 中的 `MAIN_INSTRUCTIONS`

**文件**：`src/backend/app/prompts.py`

**具体操作**：
- 在 `## 回答格式` 部分增加明确的 Markdown 格式要求
- 要求 AI 根据内容类型选择合适的结构（表格/粗体/代码块/列表/引用块/标题）
- 添加完整示例展示期望的输出格式

**验证点**：发送问题"南昌航空大学的办学性质和层次是什么"，观察 AI 是否使用表格和粗体。

### 1.2 修改 `FIRST_MESSAGE_INSTRUCTIONS`

**具体操作**：
- 在首次对话提示词中也加入格式要求
- 确保首次欢迎消息简洁但格式清晰

**验证点**：清除会话后重新打开，验证首次消息格式。

---

### ✅ Phase 1 完成检查点

**端到端测试**：
- [ ] 启动 Flask 应用
- [ ] 发送 3 个不同类型的问题（事实查询、对比类、步骤类）
- [ ] 确认输出包含：表格、粗体、列表、引用块等多种格式
- [ ] 确认引用格式仍为 `[^n]` 脚注

**代码审查**：
- [ ] Prompt 变更没有破坏现有的引用格式要求
- [ ] Prompt 没有过长（控制 token 消耗）
- [ ] 示例输出格式与系统能力匹配

---

## Phase 2：后端 SSE 事件增强（搜索关键词 + 思考阶段）

### 2.1 新建 `search_keywords.py`

**文件**：`src/backend/app/search_keywords.py`（新建，~50 行）

**具体操作**：
- 实现 `extract_search_keywords(web_search_event: dict) -> list[str]`
- 从 DashScope `web_search_call` 事件中提取搜索关键词
- 实现 `format_keywords_response(keywords: list, count: int) -> str`
- 生成前端可消费的 SSE 事件 JSON

**验证点**：单元测试验证关键词提取函数。

### 2.2 修改 `qwen_api.py` 增强事件解析

**文件**：`src/backend/app/qwen_api.py`

**具体操作**：
- 在 `stream_chat()` 的 SSE 解析中识别 `response.web_search_call` 类型事件
- 从事件中提取 `search_results` 数组
- 在 `build_payload()` 中添加搜索相关配置

**验证点**：确认 Qwen API 返回的搜索事件能被正确捕获。

### 2.3 修改 `routes.py` 增强流式响应

**文件**：`src/backend/app/routes.py`

**具体操作**：
- 在 `generate()` 中新增事件发送逻辑：
  ```python
  # 检测到 web_search_call 时
  yield f'data: {json.dumps({"type": "search_keywords", "keywords": [...], "count": N})}\n\n'
  ```
- 在搜索完成后、正文开始前发送：
  ```python
  yield f'data: {json.dumps({"type": "thinking_start"})}\n\n'
  ```
- 在第一条正文内容到达时发送：
  ```python
  yield f'data: {json.dumps({"type": "thinking_end"})}\n\n'
  ```
- 保持所有原有事件格式不变（向后兼容）

**验证点**：
- 启动应用，发送联网搜索问题
- 使用浏览器 DevTools Network 面板查看 SSE 流
- 确认事件序列：`search_keywords` → `thinking_start` → `output_text.delta`(xN) → `citations` → `done` → `[DONE]`

---

### ✅ Phase 2 完成检查点

**端到端测试**：
- [ ] 启动 Flask 应用
- [ ] 打开浏览器 DevTools → Network → WS/SSE
- [ ] 发送需要联网搜索的问题
- [ ] 确认 SSE 流中包含 `search_keywords` 事件（带关键词列表和结果数）
- [ ] 确认 SSE 流中包含 `thinking_start` 和 `thinking_end` 事件
- [ ] 确认原有的 `choices`、`citations`、`[DONE]` 事件格式不变
- [ ] 发送不需要搜索的问题，确认不会产生搜索事件
- [ ] 缓存命中场景，确认行为正常

**代码审查**：
- [ ] 新增代码没有破坏现有的 SSE 事件格式
- [ ] 异常处理完善（搜索事件解析失败不影响正文流）
- [ ] 没有引入导入循环
- [ ] 日志输出适当（便于排查问题）

---

## Phase 3：前端 — 搜索关键词栏 + 思考卡片

### 3.1 实现搜索关键词栏组件

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 新增 `renderSearchKeywordsBar(keywords: string[], count: number)` 函数
- 渲染样式：深色背景行（`#1e1e2e`），关键词为圆角标签（`#2a2a3e` 背景，`#a0a0b0` 文字）
- 右侧显示 "N 个结果 ›" 文字
- 在消息列表中插入为特殊类型的消息项

**修改 `callRagflowAPI()`**：
- 在 `onmessage` 中处理 `parsed.type === 'search_keywords'` 事件
- 创建搜索关键词栏消息并插入消息列表
- 替换原来的 "正在搜索相关资料..." loading 消息

### 3.2 实现思考卡片组件

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 新增 `renderThinkingCard()` 函数
- 渲染样式：左侧蓝色脉冲点（`#4285f4` 呼吸动画）+ "正在思考中" 文字 + 可折叠箭头
- 修改 `callRagflowAPI()` 处理 `thinking_start` 和 `thinking_end` 事件
- 思考卡片显示在搜索关键词栏下方，正文消息之前

### 3.3 修复流式光标 CSS

**文件**：`static/ai-assistant-widget.css`

**具体操作**：
- 为 `.streaming-cursor` 添加 CSS 规则（闪烁光标效果）
- 或直接改用已定义的 `.typing-indicator` 类

### 3.4 修改消息渲染逻辑

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 在 `renderMessage()` 中新增 `message.type === 'search-keywords'` 分支
- 在 `renderMessage()` 中新增 `message.type === 'thinking'` 分支
- 确保搜索栏和思考卡片可以折叠/展开

---

### ✅ Phase 3 完成检查点

**端到端测试**：
- [ ] 启动应用，发送联网搜索问题
- [ ] 确认立即出现搜索关键词标签栏（而非 "正在搜索相关资料..." 文字）
- [ ] 确认关键词标签栏显示正确的关键词和结果数量
- [ ] 确认搜索完成后出现"正在思考中"卡片（蓝色脉冲点可见）
- [ ] 确认正文开始输出时思考卡片收起/消失
- [ ] 确认发送不需要搜索的问题时不显示搜索栏
- [ ] 在不同浏览器（Chrome/Firefox/Safari）测试
- [ ] 在移动端（375px 宽度）测试响应式布局

**代码审查**：
- [ ] 新增的 `search-keywords` 和 `thinking` 消息类型不影响现有 `user`/`ai`/`error` 类型
- [ ] CSS 新增样式使用独立命名空间（如 `.ai-search-bar`）
- [ ] 折叠/展开功能不依赖外部库
- [ ] 动画性能达标（CSS `transform`/`opacity` 而非 `width`/`height`）
- [ ] 没有内存泄漏（事件监听器正确移除）

---

## Phase 4：前端 — 引用 Pill + Hover 预览

### 4.1 实现引用 Pill 组件

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 修改 `convertCitationsToLinks()` 函数
- 将 `[^n]` 格式渲染为 pill 元素：
  ```html
  <span class="citation-pill" data-citation="1" data-url="..." data-title="...">
    <span class="citation-number">1</span>
    <span class="citation-domain">百度百科</span>
  </span>
  ```
- Pill 显示来源域名而非 `[数字]`（从 citation URL 提取域名）
- 域名获取逻辑：从 URL 提取主机名，映射常见域名到中文名称

**域名映射表**：
```javascript
const DOMAIN_NAMES = {
  'baike.baidu.com': '百度百科',
  'zh.wikipedia.org': '维基百科',
  'www.nchu.edu.cn': '南昌航空大学官网',
  'jwc.nchu.edu.cn': '教务处',
  'xgc.nchu.edu.cn': '学工处',
  // ... 可配置扩展
};
```

### 4.2 实现 Hover 预览弹窗

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 新增 `showCitationPreview(pillElement)` 函数
- 预览卡片结构：
  ```html
  <div class="citation-preview-popover">
    <div class="preview-header">
      <img class="preview-favicon" src="https://www.google.com/s2/favicons?domain=DOMAIN&sz=32" />
      <span class="preview-domain">baike.baidu.com</span>
    </div>
    <div class="preview-title">页面标题</div>
    <div class="preview-snippet">3 行摘要内容...</div>
    <a class="preview-link" href="URL" target="_blank">打开链接 →</a>
  </div>
  ```
- 鼠标悬停在 pill 上 200ms 后显示预览（防抖）
- 鼠标离开预览卡片 100ms 后隐藏
- 点击 pill 直接打开链接

**移动端适配**：
- 移动端改为点击 pill 显示预览（非 hover）
- 第二次点击打开链接

### 4.3 实现引用提前渲染（占位符策略）

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 在 `updateMessageDisplay()` 中，即使没有 URL 映射，也把 `[^n]` 渲染为灰色占位 pill
- 收到 `{citations: {...}}` SSE 事件后，原地升级占位 pill：
  - 添加 URL（可点击）
  - 添加域名名称
  - 添加 hover 预览功能
- 使用 `MutationObserver` 或定时扫描检测新出现的引用标记

### 4.4 引用数据流优化

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 修改 `callRagflowAPI()` 的 `onmessage` 中 `parsed.citations` 处理逻辑
- 收到引用后不重建整个消息，而是：
  1. 更新 `message.citationUrls`
  2. 查找 DOM 中对应的占位 pill
  3. 原地更新 pill 的属性和样式

---

### ✅ Phase 4 完成检查点

**端到端测试**：
- [ ] 发送联网搜索问题
- [ ] 确认正文中的引用标记实时出现（不等流结束）
- [ ] 确认引用显示为灰色 pill，带有来源域名名称
- [ ] 确认悬停在 pill 上出现预览卡片（favicon + 标题 + 域名 + 摘要）
- [ ] 确认预览卡片中的链接可点击并正确跳转
- [ ] 确认收到引用元数据后，pill 原地升级（无闪烁/重布局）
- [ ] 移动端测试：点击 pill 显示预览
- [ ] 测试无 URL 映射的引用（保持占位状态）
- [ ] 测试多个连续引用（如 `[^1][^2][^3]`）

**代码审查**：
- [ ] DOM 遍历替换引用不影响其他消息的渲染
- [ ] Hover 预览不会造成内存泄漏（及时移除 DOM 和事件监听器）
- [ ] 占位符策略不会导致 Markdown 解析错误
- [ ] 移动端适配完善
- [ ] Favicon 加载失败时有降级方案

---

## Phase 5：前端 — 底部来源卡片

### 5.1 实现来源卡片列表

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 新增 `renderSourceCards(citationMap: CitationMap)` 函数
- 在收到 `{"citations": {...}, "done": true}` 后渲染来源卡片
- 每张卡片结构：
  ```html
  <div class="source-card" onclick="window.open('URL', '_blank')">
    <img class="source-favicon" src="favicon_url" onerror="this.style.display='none'" />
    <div class="source-info">
      <div class="source-title">页面标题</div>
      <div class="source-domain">baike.baidu.com</div>
    </div>
    <div class="source-expand-icon">›</div>
  </div>
  ```

### 5.2 折叠/展开控制

**具体操作**：
- 卡片列表默认折叠，显示 "N 个来源 ▼" 可点击标题
- 点击展开/折叠卡片列表
- 折叠时只显示来源数量和 favicon 缩略图行

### 5.3 集成到消息渲染

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 在 `renderMessage()` 中为 `ai` 类型消息添加来源卡片区域
- 当 `message.citationUrls` 有数据时渲染卡片
- 来源卡片渲染在消息内容下方、操作栏上方

---

### ✅ Phase 5 完成检查点

**端到端测试**：
- [ ] 发送联网搜索问题
- [ ] 确认流结束后在消息底部出现来源卡片区域
- [ ] 确认卡片显示正确的 favicon、标题、域名
- [ ] 点击卡片正确打开来源链接
- [ ] 折叠/展开功能正常工作
- [ ] 确认有多个来源时卡片正确排序
- [ ] 无来源的消息不显示卡片区域
- [ ] 测试 favicon 加载失败时的降级显示

**代码审查**：
- [ ] 卡片渲染不阻塞主线程（使用 requestAnimationFrame）
- [ ] 大量来源（>20）时的滚动性能
- [ ] 卡片与现有样式无冲突
- [ ] 移动端适配（卡片宽度、点击区域大小）

---

## Phase 6：操作栏增强 + 表格样式

### 6.1 操作栏增强

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 在消息操作栏新增按钮：
  - 🔄 重新生成（所有消息）
  - 📤 分享（复制消息内容为文本）
  - 👍 点赞（记录到本地，可后续对接后端）
  - 👎 点踩（记录到本地）
- 操作栏改为始终显示（不再 hover 才出现）
- 添加来源图标行（favicon 小图标 + "引用" 文字）

### 6.2 表格深色样式

**文件**：`static/ai-assistant-widget.css`

**具体操作**：
- 为 `.markdown-table` 添加深色主题样式
- 表头：`#2a2a2e` 背景，`#e0e0e0` 文字
- 表格行：交替 `#1e1e22` / `#25252a` 背景
- 边框：`#3a3a3e` 颜色
- 表格右上角添加复制和下载按钮（浮动在表格上方）

### 6.3 表格操作按钮

**文件**：`static/ai-assistant-widget.js`

**具体操作**：
- 新增 `addTableActions(tableElement)` 函数
- 复制按钮：将表格内容转为 CSV 并复制到剪贴板
- 下载按钮：将表格内容下载为 CSV 文件
- 使用 `MutationObserver` 检测新渲染的表格并绑定操作

---

### ✅ Phase 6 完成检查点

**端到端测试**：
- [ ] 确认操作栏始终可见（无需 hover）
- [ ] 测试重新生成按钮功能
- [ ] 测试分享按钮（复制消息内容）
- [ ] 测试点赞/点踩按钮（视觉反馈）
- [ ] 发送包含表格的问题
- [ ] 确认表格使用深色主题样式
- [ ] 确认表格有复制和下载按钮
- [ ] 测试表格复制到剪贴板
- [ ] 测试表格下载为 CSV

**代码审查**：
- [ ] 操作栏新增按钮不影响现有复制/删除功能
- [ ] 表格深色主题在浅色模式下也可读
- [ ] CSV 生成正确处理特殊字符和换行
- [ ] 移动端表格操作按钮可点击

---

## Phase 7：端到端回归测试 + 文档

### 7.1 完整用户流程测试

**测试矩阵**：

| 用户行为 | 预期结果 | 优先级 |
|---------|---------|--------|
| 首次打开 widget | 预设问题面板 | P0 |
| 发送首次消息 | 欢迎语 + 询问学院（格式清晰） | P0 |
| 回复学院信息 | 固定回复（无多余信息） | P0 |
| 发送联网搜索问题 | 搜索关键词栏 → 思考卡片 → 丰富格式正文 + 引用 pill | P0 |
| 悬停引用 pill | 显示预览卡片 | P0 |
| 流结束后 | 底部来源卡片列表 | P0 |
| 发送普通问题（无需搜索） | 直接流式输出 + 丰富格式 | P1 |
| 缓存命中 | 秒回缓存内容 | P1 |
| 操作栏功能 | 复制、重新生成、分享、👍👎 均正常 | P1 |
| 表格操作 | 复制、下载正常 | P2 |
| 移动端适配 | 所有功能在 375px 宽度下可用 | P1 |
| API 错误 | 友好错误提示 | P1 |
| 网络中断 | 提示连接中断 | P2 |

### 7.2 性能测试

**测试项**：
- [ ] 首屏加载时间 < 1s
- [ ] SSE 连接建立时间 < 500ms
- [ ] 流式输出帧率 > 24fps（无明显卡顿）
- [ ] 大消息（>2000 字）渲染无冻结
- [ ] 内存使用稳定（无泄漏）

### 7.3 跨浏览器测试

- [ ] Chrome 最新版
- [ ] Firefox 最新版
- [ ] Safari（macOS/iOS）
- [ ] Edge 最新版

### 7.4 更新文档

- [ ] 更新 `README.md` 中的功能说明
- [ ] 更新前端组件文档
- [ ] 记录新增的 SSE 事件类型

---

## 总体验证标准

所有 Phase 完成后，以下标准必须全部满足：

- [ ] 搜索过程展示（关键词栏 + 思考卡片）完整可用
- [ ] 引用 pill 实时渲染（不等流结束）
- [ ] Hover 预览弹窗功能正常
- [ ] 底部来源卡片完整展示
- [ ] Markdown 输出丰富（表格、粗体、列表等）
- [ ] 操作栏功能齐全
- [ ] 表格深色主题 + 操作按钮
- [ ] 移动端适配完善
- [ ] 性能达标（无卡顿、无泄漏）
- [ ] 所有 Phase 的代码审查均通过
- [ ] 无 P0/P1 级别的已知 bug

---

## 回退策略

每个 Phase 都应该是**可独立回退**的：
- Phase 1：还原 `prompts.py` 即可
- Phase 2：还原 `routes.py` + 删除 `search_keywords.py`
- Phase 3：还原 `widget.js` 和 `widget.css` 中的搜索/思考相关代码
- Phase 4：还原引用渲染逻辑
- Phase 5：还原来源卡片代码
- Phase 6：还原操作栏和表格样式

每个 Phase 完成后应提交独立 commit，方便回退。

---

## 已知 Bug 待办

### BUG-001: SSE 流 UTF-8 编码截断问题

**文件**：`src/backend/app/qwen_api.py` 第 160-164 行

**问题**：`response.iter_lines()` 按 `\n` 字节分割，可能在多字节 UTF-8 字符（如中文）的字节边界处截断，导致下游收到的 SSE 数据中中文字符损坏。

**表现**：
- Python `requests` 客户端直接读取 SSE 流时，中文字符显示为乱码
- 浏览器端 JavaScript 的 `TextDecoder` 流式解码能正确处理，因此**浏览器端用户体验不受影响**

**当前状态**：已确认但不阻塞（浏览器端正常），待 Phase 2 一并修复

**修复方案**：将 `iter_lines()` 改为 `iter_content(decode_unicode=True)` + 手动按行缓冲，避免字节边界截断。

**涉及修改**：
```python
# 当前（有问题）
for line in response.iter_lines():
    decoded_line = line.decode('utf-8')

# 修复后
buffer = ''
for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
    buffer += chunk
    while '\n' in buffer:
        line, buffer = buffer.split('\n', 1)
        ...
```

**优先级**：P1（当前不阻塞开发，但应在 Phase 2 修复）
