# StudentChatboxQianwenShell Specification

## Overview

- **Target files:** `frontend/src/StudentChatboxPage.tsx`,
  `frontend/src/App.css`
- **Reference screenshots:**
  - `docs/design-references/qianwen/qianwen-original-desktop.png`
  - `docs/design-references/qianwen/qianwen-original-mobile-fixed.png`
- **Interaction model:** input-driven, click-driven, hover-driven, time-driven
  entrance motion

## DOM Structure

Keep the current assistant-ui structure:

- `AssistantRuntimeProvider`
- `ThreadListPrimitive.Root` for conversation history
- `ThreadPrimitive.Root` for the chat surface
- `ThreadPrimitive.Viewport` for message scrolling
- `ThreadPrimitive.Messages` for message rendering
- `ThreadPrimitive.ViewportFooter`
- `ComposerPrimitive.Root`
- `ComposerPrimitive.Input`
- `ComposerPrimitive.Send`
- `ComposerPrimitive.Cancel`
- `MessagePrimitive.Root`
- `MessagePrimitive.Parts`
- `ActionBarPrimitive.Copy`
- `ActionBarPrimitive.Reload`

## Visual Translation

### App Shell

- Shift from warm parchment to Qianwen-like neutral product surface.
- Full height, overflow hidden.
- Main chat surface should feel like a large white canvas.
- Keep restrained institutional tone and Chinese-first labels.

### Conversation Rail

- Desktop width target: about 256px (`16rem` in source).
- Quiet neutral background.
- Top actions: back/workbench, new conversation, current model.
- History remains secondary.
- Mobile: avoid full overlay unless separately approved; existing horizontal
  rail is acceptable if visually simplified.

### Top Bar

- Compact model/status strip.
- Show approved model as Qwen only.
- Do not show API service, provider links, desktop download, or info controls
  copied from Qianwen.

### Empty Launchpad

- Center greeting above composer.
- Replace Qianwen copy with student support copy:
  - Title: `你好，我是 AI 咨询助手`
  - Body: brief AI safety/handoff note
- Replace Qianwen logo with small project-native mark or simple sparkle icon.
- On mobile, translate the corrected Qianwen reference as an app-style launch
  surface: left-aligned greeting, stacked starter prompts, and bottom composer
  rather than a scaled desktop center layout.

### Composer

- Make composer the primary surface.
- Rounded capsule with subtle border and shadow.
- Placeholder remains animated but student-focused.
- Add compact chip/tool row inside or directly under composer:
  `课程规划`, `作业拆解`, `论文润色`, `考试复习`, `校园流程`, `心理支持`.
- Buttons should use icons/symbols when possible; no text-only rounded buttons
  for send/stop if an icon communicates the action.
- Preserve assistant-ui send/cancel behavior.

### Notice Card

- Replace Qianwen download promo with a small student trust/safety card:
  `重要事项请联系辅导员确认`.
- Hover may reveal a close/dismiss affordance if implemented locally.

### Messages

- Keep centered thread.
- Assistant bubbles should be calm, low-border, readable.
- User messages should be right aligned and visually distinct, but not overly
  saturated.

## Motion

Use GSAP via `useGSAP` and scoped selectors:

- Initial load: rail enters from `x: -14`, launchpad/composer from `y: 18`,
  `autoAlpha: 0 -> 1`, duration 0.28-0.36s, `power3.out`.
- Tool chips: CSS hover transform/opacity, 150-200ms.
- Message entrance: `y: 8-10`, `autoAlpha`, duration 0.2-0.24s.
- Send/stop state: CSS opacity/background transition, 200ms.
- Respect `prefers-reduced-motion`.

## Responsive Behavior

- Desktop 1440px: rail visible, central launchpad width around 760-880px.
- Tablet: rail can remain but main composer must stay centered.
- Mobile device reference: no horizontal page overflow; no persistent rail;
  compact top bar; left-aligned greeting; stacked student starter prompts;
  large rounded composer near the bottom with send/stop visible and tappable.

## Non-Goals

- No new dependencies.
- No backend/API contract change.
- No model/provider change.
- No web search/RAG/attachments/real data/persistence.
- No teacher/counselor Chatbox expansion.
