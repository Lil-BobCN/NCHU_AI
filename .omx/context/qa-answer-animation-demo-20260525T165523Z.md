# Context Snapshot: QA Answer Animation Demo

Task statement: User wants an animation based on the provided input-card image and inspired by qwen.ai input text animation, showing a realistic QA flow: user uploads/submits a question, model thinks, model outputs an answer.
Desired outcome: First align on effect via deep-interview, then create a demo version for review, and only after approval implant into the product.
Stated solution: Use Doing skills / implementation workflow after alignment to build demo.
Probable intent hypothesis: Demonstrate an AI counseling/consultation interaction with a polished micro-animation that feels like a real user-model exchange rather than just placeholder typing.
Known facts/evidence: Reference image shows a compact input box with Chinese prompt text, chips (学生问答 / 辅导员协助 / 知识维护), and CTA 开始咨询. Reference URL qwen.ai/home has input typing motion but does not cover the full desired flow.
Constraints: Do not implement before effect alignment. Need demo first, review before integration. Brownfield frontend exists under frontend with Vite.
Unknowns/open questions: Desired realism level, duration, exact stages, visual style, demo location, whether upload is file/image or question text, final answer format.
Decision-boundary unknowns: What can be invented in demo vs must match existing product; whether to use real app components or standalone route; what is explicitly out of scope.
Likely codebase touchpoints: frontend package, existing route/component structure after alignment.
Prompt-safe initial-context summary status: not_needed
