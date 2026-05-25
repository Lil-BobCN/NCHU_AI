# QA Answer Animation Reference Research

Date: 2026-05-25 UTC

## Mission

Find or create visual reference material for aligning a QA animation before implementation. The target animation should show:

- A user submitting or uploading a question.
- The model entering a thinking / reasoning state.
- The model streaming or revealing the final answer.

The user explicitly said that text-only descriptions are hard to evaluate, so alignment must use visual material.

## External References

1. Qwen home input interaction
   - URL: https://qwen.ai/home
   - Useful part: compact prompt input, type-in feel, immediate CTA focus.
   - Gap: it does not clearly show the complete answer workflow from submission to reasoning to final answer.

2. LottieFiles chatbot / typing animation references
   - URL: https://lottiefiles.com/search?q=chatbot%20typing
   - Useful part: visual vocabulary for thinking dots, bot response states, lightweight looped motion.
   - Gap: most examples are generic chatbot loops, not product-specific institutional QA flows.

3. CodePen / CSS chat animation patterns
   - URL: https://codepen.io/search/pens?q=chatbot%20typing%20indicator
   - Useful part: simple CSS patterns for typing indicators, message bubble entrance, streaming text.
   - Gap: examples usually cover only one micro-interaction, not a full scenario.

## Local Visual Reference Created

Prototype board:

- `output/prototypes/qa-answer-animation-reference-board.html`

Screenshot evidence:

- `output/playwright/qa-answer-animation/reference-board-real.png`

The board contains three playable directions:

1. **Real QA Flow**
   - Shows the input card, staged processing, model thinking, and streamed answer.
   - Best fit for actual product embedding because it feels like a real support workflow.

2. **Brand Demo**
   - Keeps the UI minimal and hero-friendly, closer to Qwen-like input motion.
   - Best fit for homepage first-screen brand demonstration.

3. **Teaching Breakdown**
   - Makes each step explicit: upload, extraction, process matching, answer generation.
   - Best fit for product review, stakeholder explanation, or demo pages.

## Recommendation

Use **Real QA Flow** as the primary implementation direction unless the target placement is strictly a marketing-style homepage hero. It best satisfies the user's stated requirement: "真实的答疑过程".

For the later implant step, keep the implementation modular:

- A standalone demo route/component first.
- No business route mutation until the user approves the visual direction.
- A reduced-motion fallback for accessibility.
- The animation should be CSS-first unless real uploaded assets or live model statuses are required.

## Remaining Alignment Questions

1. Which route should the approved demo eventually be implanted into?
2. Should "上传问题" literally include file/image upload, or is typed question submission enough for the first demo?
3. Should the model thinking stage look abstract and polished, or explicit with labels like "识别意图 / 检索知识 / 生成回答"?

