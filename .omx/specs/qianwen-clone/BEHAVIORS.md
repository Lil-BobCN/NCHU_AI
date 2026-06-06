# Qianwen Behavior And Motion Notes

Date: 2026-05-27

## Evidence

- Desktop screenshot: `output/playwright/qianwen-original-desktop.png`
- Mobile screenshot: `output/playwright/qianwen-original-mobile-fixed.png`
- DOM dump: `output/playwright/qianwen-original-dom.html`

The previous mobile artifact `qianwen-original-mobile.png` is invalid for
implementation reference because the input/composer proportions had not settled.
Use only the `mobile-fixed` artifact for mobile layout analysis.

## Interaction Model

The target is a chat launchpad, not a scroll narrative. The visible interactions
are click, hover, input, and state-driven transitions.

## Motion Timings

Observed from DOM classes and style tokens:

- Common controls use `duration-200` or `duration-300`.
- Sidebar/drawer uses `transition-[width] duration-300` and
  `transition-transform duration-300`.
- Buttons use `transition-[opacity,shadow,transform] duration-200` or
  `transition-[background-color,color,opacity] duration-200`.
- Promotion close button uses `transition-opacity duration-200` and is revealed
  by `group-hover`.
- Loading rotation class exists with `1s linear infinite`.

## States

### Sidebar Collapse / Mobile Drawer

- Trigger: sidebar icon click.
- State A: persistent desktop rail at `16rem`.
- State B: collapsed width or off-canvas mobile overlay.
- Transition: width and transform, 300ms.
- NCHU implementation: keep existing rail on desktop; mobile can remain a
  compact horizontal history strip unless a drawer is separately approved.

### Composer Empty / Ready

- Trigger: user enters text.
- State A: placeholder visible, send button disabled and gray.
- State B: send button active, primary circular action.
- Transition: background/color/opacity, about 200ms.
- NCHU implementation: preserve assistant-ui `ComposerPrimitive.Send` and
  `ComposerPrimitive.Cancel`; style send/stop as circular icon buttons.

### Tool Chips

- Trigger: hover or click.
- State A: transparent chip with icon/text.
- State B: subtle gray hover background and text emphasis.
- Transition: color/background, 200ms.
- NCHU implementation: chips are student workflow starters, not unapproved
  capabilities. They may submit approved prompt starters or simply populate
  suggested text.

### Promotion / Notice Card

- Trigger: hover on card.
- State A: close button invisible and non-interactive.
- State B: close button visible, pointer enabled.
- Transition: opacity, 200ms.
- NCHU implementation: can use a safety/handoff notice card; close behavior is
  optional and local-only.

### Message Entrance

- Qianwen initial visible state has no messages, but the product's motion tokens
  suggest restrained transform/opacity.
- NCHU implementation: keep existing GSAP message entrance with `y` and
  `autoAlpha`, 0.2-0.36s, scoped by `useGSAP`.

## Responsive Notes

- Desktop: persistent 16rem rail, top bar, centered launchpad.
- Mobile device reference: no persistent rail; top controls compress into a
  single icon/model/action row; the page becomes a mobile app-style launch
  surface rather than a scaled desktop layout.
- Mobile greeting: large left-aligned `我是千问` title with supporting line below.
- Mobile suggestions: three stacked prompt chips appear before the composer.
- Mobile composer: large rounded bottom capsule, stable after load, with prompt
  placeholder on the first row and add/thinking/send controls in the lower row.
- NCHU implementation should avoid horizontal page overflow, keep the composer
  visible and tappable near the bottom, and use stacked or horizontally
  scrollable student starter prompts depending on available width.

## Exclusions

Do not clone:

- Qianwen logo/brand.
- API service/download CTAs.
- Guest login quota.
- Direct provider calls.
- Web search, RAG, attachments, file upload, image generation, code, translation,
  or recording controls unless separately approved.
