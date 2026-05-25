# Ralph Context Snapshot: Homepage Cinematic Scroll Implementation

Task statement:
- Implement the approved SDAR-0007 homepage direction for NCHU AI.

Desired outcome:
- The homepage opens with a dark cinematic full-screen motion/video placeholder.
- The Linear-like top navigation appears with glass styling and keeps `/login` as the primary entry.
- Scrolling reveals four product narrative chapters with Tongyi-like staged motion.
- Existing Demo login, identity detection, and role routing remain intact.

Known facts/evidence:
- Frontend stack is React + TypeScript + Vite + Ant Design.
- Approved new runtime dependencies are only `gsap` and `@gsap/react`.
- SDAR-0007 forbids adding Three.js, Lottie, Rive, Lenis, real school resources, real student data, production SSO, backend/API changes, and final NCHU wing animation work in this node.
- The final NCHU emblem/wing animation is technical debt `TD-0001`.

Constraints:
- Desktop-first, mobile-readable.
- Use local generated motion layers, not network video assets.
- Use GSAP React cleanup patterns and reduced-motion fallback.
- Keep work scoped to homepage/front-end presentation plus dependency metadata.
- Update development path/log after completion.

Unknowns/open questions:
- Final video/wing asset is not available yet and remains intentionally replaceable.
- Exact future copy can be revised after product review.

Likely codebase touchpoints:
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/App.tsx`
- `frontend/src/App.css`
- `.omx/logs/development-path-structure-ai-counselor-demo.md`
- `.omx/logs/current-assets-progress-ai-counselor-demo-20260519.md`
