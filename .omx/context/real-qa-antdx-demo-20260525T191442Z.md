# Real QA Ant Design X Demo Context

Task statement: Build a reviewable frontend demo for Scheme A real QA flow. Use Ant Design X chat components and GSAP motion. Do not implant into the production/main homepage yet.

Desired outcome: A compact prompt card first appears, then expands downward from the same position into a chatbox-like QA flow. Student question is right aligned. AI answer is left aligned. Thinking / matching / reasoning is represented by Ant Design X Think or ThoughtChain. Demo should fit the main homepage prompt-card area, roughly max-width 520px, with responsive behavior.

Known facts/evidence: Frontend is Vite React in frontend/. Current dependencies include React 19, antd 6, gsap, @gsap/react, icons, router. @ant-design/x is not yet installed. Existing homepage is large in src/App.tsx. User wants demo first, no implantation.

Constraints: Chinese-first copy. Claude-like restrained chat style adapted to NCHU product identity. Use x-components, GSAP core/timeline/react, karpathy-guidelines, ralph-style verification. Keep scope surgical.

Unknowns/open questions: Exact final homepage insertion point is pending user approval. Current task can proceed as a standalone route/demo.

Likely touchpoints: frontend/package.json, package-lock.json, src/App.tsx route, new src/RealQaFlowDemo.tsx, new src/RealQaFlowDemo.css.
