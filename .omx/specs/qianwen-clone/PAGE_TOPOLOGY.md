# Qianwen Page Topology

Date: 2026-05-27

## Reference State

- Desktop reference: `output/playwright/qianwen-original-desktop.png`
- Mobile reference: `output/playwright/qianwen-original-mobile-fixed.png`
- Rendered DOM: `output/playwright/qianwen-original-dom.html`

The captured state is the unauthenticated first-screen chat launchpad. It is the
only visual state proposed for this task unless the product manager requests a
different target state.

The earlier mobile capture `qianwen-original-mobile.png` is superseded. It was
not accepted as evidence because the mobile input bar proportions had not
settled before capture.

## Desktop Topology

1. **App Shell**
   - Full-height, light neutral canvas.
   - Main DOM root uses `data-theme="light"` and `class="qwen-root"`.
   - Content is a fixed app surface, not a marketing page scroll.

2. **Left Conversation Rail**
   - Width: `16rem`.
   - Contains logo, sidebar collapse control, `新建对话`, temporary chat icon,
     `我的空间`, `智能体`, empty history state `暂无对话`, and bottom login CTA.
   - Interaction model: click-driven navigation and drawer/collapse controls.
   - Motion: width/transform transition around 300ms in DOM classes.

3. **Top Model Bar**
   - Height around 48px.
   - Left side: model selector `Qwen3.6-千问` with chevron.
   - Right side: `API 服务`, `下载电脑端`, info icon.
   - Interaction model: click-driven selectors/links. For NCHU adaptation,
     external API/download affordances are excluded.

4. **Central Launchpad**
   - Large negative space.
   - Greeting centered slightly above the composer: blue Qianwen mark and
     `你好，我是千问`.
   - Interaction model: static greeting with entrance motion.

5. **Composer Capsule**
   - Central primary affordance.
   - Rounded white container, subtle border/shadow, max width visually around
     760px.
   - First line placeholder: `向千问提问`.
   - Bottom row: add, task assistant, thinking, research, PPT, HappyHorse,
     more, mic, disabled send.
   - Interaction model: text input, hover/click tool chips, send enabled after
     content.

6. **Promotion Card**
   - Centered under composer, max width around 620px.
   - `新功能`, title, short description, dark rounded CTA.
   - Close button exists but appears only on hover through opacity/pointer state.
   - For NCHU adaptation this becomes a student-support notice card, not a
     download advertisement.

7. **Footer Consent Copy**
   - Small centered text at bottom.
   - For NCHU adaptation this becomes AI safety/handoff boundary copy.

## Mobile Topology

1. **No Persistent Left Rail**
   - Desktop rail is removed/collapsed.
   - Header keeps a compact row: menu/sidebar icon, new chat icon, centered
     model selector, info icon, and an `打开APP` action.

2. **Mobile App Launch Surface**
   - The desktop centered greeting does not simply scale down.
   - Greeting becomes a large left-aligned headline `我是千问` with a muted
     supporting line below.
   - There is substantial vertical breathing room above the greeting.

3. **Suggested Prompt Stack**
   - Three rounded prompt chips stack vertically under the greeting.
   - Chips are wide enough for one-line Chinese prompts and keep generous touch
     targets.

4. **Bottom Composer Capsule**
   - Composer is a large rounded rectangle near the bottom of the viewport.
   - First row contains placeholder copy.
   - Lower row contains add, thinking/tool control, and a circular send button.
   - Consent copy sits below the composer.
   - The corrected reference shows this capsule fully loaded and stable.

5. **NCHU Mobile Adaptation**
   - Keep the app-like mobile launch composition: compact top bar, left-aligned
     greeting, stacked student starter prompts, and bottom composer.
   - Avoid copying Qianwen's `打开APP`, external provider, download, or brand
     controls.
   - Avoid horizontal overflow; starter chips may stack or scroll within their
     own row.

## Adaptation Summary

Use Qianwen's calm launchpad pattern, not its brand/product affordances:

- Keep: full-height chat app shell, secondary history rail, centered greeting,
  prominent composer, compact tool chips, small safety copy, 100-300ms motion.
- Replace: API/download/multi-product tools with student-safe actions such as
  `课程规划`, `作业拆解`, `论文润色`, `考试复习`, `校园流程`, `心理支持`.
- Preserve: assistant-ui primitives, FastAPI SSE boundary, stop/retry/new-chat,
  no browser-side model keys, no unapproved RAG/search/attachments/persistence.
