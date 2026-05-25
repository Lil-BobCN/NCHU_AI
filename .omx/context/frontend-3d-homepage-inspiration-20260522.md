# Frontend 3D Homepage Inspiration: NCHU AI

Date: 2026-05-22
Status: research brief for product-manager selection
Scope: top navigation and homepage first-screen visual direction only

## Goal

Find 3D/motion website cases and asset sources that fit the AI Counselor Demo:

- Formal and credible enough for a school-facing product.
- More expressive than the current static hero.
- 3D and motion should explain the product, not become pure decoration.
- Implementation must remain compatible with the current React + TypeScript + Vite frontend.
- No implementation or dependency introduction is approved by this brief.

## Selection Criteria

| Criterion | Meaning |
| --- | --- |
| Product fit | Supports AI counselor, school services, knowledge/workflow, or education technology story. |
| Visual fit | Modern SaaS/product-site quality, not childish edtech or game-like fantasy. |
| Implementation fit | Can be built in React without replacing current frontend stack. |
| Performance fit | Can degrade gracefully on mobile and avoid blocking login flow. |
| Asset clarity | Assets have a clear source, license, or can be custom-built. |

## Recommended Design Directions

### Direction A: 3D AI Console / Floating Workbench

Concept:
Create a dark, polished product hero where a 3D console floats beside the headline. The console represents three role-aware workspaces: student Q&A, teacher case assistance, and operations knowledge/audit.

Best for:
The current project because we already have a dark product-site hero, role-based login, and dashboard/workbench story.

Motion ideas:

- Subtle floating console.
- Cards rotate slightly with cursor movement.
- Role nodes pulse in sequence: Student -> Teacher -> Operations.
- Login CTA triggers a small handoff animation toward the console.

Reference cases:

- Huly landing page: ultra-detailed SaaS, bento, gradients, animated UI assets.
- Spline 3D websites: interactive 3D elements for product-site engagement.
- Awwwards Nisa AI Chatbot: AI + 3D + interactive landing page pattern.

Implementation options:

- Fast prototype: Spline scene embedded in React.
- More controlled production path: React Three Fiber + Drei with custom GLB assets.
- Motion layer: Motion for React for nav/CTA/cards; optional Three.js/R3F for the 3D scene.

Risks:

- Spline embed is fast but less code-native.
- R3F is more controllable but adds implementation complexity.
- Mobile needs a lighter static or reduced-motion fallback.

Recommendation:
Use this as the primary candidate.

### Direction B: Campus Knowledge Graph / Neural Map

Concept:
The homepage becomes a 3D knowledge graph: nodes for policy, resource, case, conversation, audit, and stats. It visually explains that NCHU AI connects students, teachers, and operations through source-backed knowledge.

Best for:
Explaining RAG/knowledge-boundary vision without claiming Phase 7 RAG is already live.

Motion ideas:

- Slow-moving nodes and lines.
- Hovering role cards highlights matching paths.
- Scroll transitions from graph into product features.
- Demo labels appear as small badges on data nodes.

Reference cases:

- Three.js particle/wave examples for abstract knowledge-field visuals.
- Awwwards AI/3D examples for immersive AI landing treatments.
- Sagenverse and Saras-3D show education technology using 3D/AI storytelling.

Implementation options:

- React Three Fiber point cloud and lines.
- Lightweight CSS/SVG fallback if WebGL is disabled.
- Motion for React for section transitions.

Risks:

- Easy to overpromise RAG/knowledge intelligence before Phase 7.
- Needs copy discipline: "Demo knowledge boundary", not "live production RAG".
- Abstract graphics can feel generic if not tied to role flows.

Recommendation:
Good second candidate if you want the page to emphasize knowledge/RAG vision.

### Direction C: 3D Campus Service Portal

Concept:
Use a stylized 3D campus/service desk scene: a school building, help desk, AI assistant object, and floating service cards. It makes the product feel more campus-specific.

Best for:
Making the NCHU/school identity more explicit.

Motion ideas:

- Camera slowly pans across a campus-service desk.
- Three service cards lift from the desk.
- The AI assistant object lights up when the login CTA is hovered.

Reference cases:

- AR Class and immersive education platforms use 3D/AR framing for learning engagement.
- Sagenverse positions 3D as a way to bring lessons and collaboration to life.
- Spline library/community scenes can provide quick scene starting points.

Implementation options:

- Start in Spline with library objects, then embed.
- Use open GLB assets for desk/campus/assistant props.
- Replace with custom Blender/Spline assets later if branding needs precision.

Risks:

- Can become too literal or childish if the 3D scene looks like a toy.
- Campus building assets may not match NCHU identity unless custom-modeled.
- More asset-selection overhead.

Recommendation:
Use only if you want strong "school/campus" identity on the first screen.

### Direction D: Cinematic Scroll / 3D Frame Sequence

Concept:
Instead of realtime WebGL, use a scroll-driven cinematic sequence: abstract AI/campus/knowledge visuals play as the user scrolls.

Best for:
High visual impact with predictable rendering if we generate or source a short animation.

Motion ideas:

- Hero begins with a 3D abstract layer.
- Scroll reveals role cards and product console.
- CTA and navigation remain conventional.

Reference cases:

- Draftly describes converting generated/cinematic motion into scroll-driven frame sequences without WebGL.

Implementation options:

- Generated video/image sequence.
- CSS scroll/timeline or JS frame interpolation.
- Motion for React for text/card transitions.

Risks:

- Less interactive than actual 3D.
- Asset generation quality controls the result.
- Can increase network weight if images/video are not optimized.

Recommendation:
Good if you want cinematic feel but lower 3D implementation risk.

## Asset And Material Sources

### Spline Library / Community

Use for:

- Fast 3D scene prototyping.
- Objects, scenes, material studies, interactive hover/mouse events.

Why relevant:

- Spline has official website use cases for interactive 3D websites.
- Spline docs state its library includes free scenes and objects that can be commercially used.

Potential search terms:

- AI assistant
- dashboard
- abstract data
- robot assistant
- education
- glass panel
- knowledge graph

### Open GLB / CC0 Sources

Use for:

- Supporting props: desk, panels, abstract objects, icons, service objects.
- Assets imported into Three.js/R3F or Spline.

Sources to inspect:

- Open Source 3D Assets: GLB-focused assets and tooling.
- BlenderKit free technical assets.
- Pixabay/Sketchfab only after license review.

License note:
Prefer CC0 or explicitly commercial-friendly assets. Avoid unclear marketplace downloads.

### Motion / Microinteraction Sources

Use for:

- Non-3D UI motion: nav reveal, CTA hover, card entrance, feature-section scroll animations.

Candidates:

- Motion for React: best fit for React UI motion.
- Rive: strong for stateful interactive illustrations/icons.
- LottieFiles: useful for simple prebuilt animation packs, but less interactive than Rive.

## Implementation Path Options

| Option | What it means | Pros | Cons | Best phase |
| --- | --- | --- | --- | --- |
| Spline embed first | Build/remix scene in Spline, embed in React hero | Fastest visual improvement; good for PM selection | Less code-native; performance and ownership depend on embed | Prototype / Phase 2 visual polish |
| React Three Fiber | Build the hero scene in code with GLB assets | Maximum control; React-native; easier to test and degrade | More implementation time; needs performance tuning | After selected design is approved |
| Motion-only 2.5D | Use CSS, Motion, layered images/cards, no WebGL | Low risk; fast; accessible | Not a true 3D website | Immediate fallback or conservative option |
| Cinematic frame sequence | Use generated image/video frames tied to scroll | High-impact; predictable rendering | Asset-heavy; less interactive | If we choose cinematic direction |

## Current Recommendation

Recommended first selection set:

1. Direction A: 3D AI Console / Floating Workbench.
2. Direction B: Campus Knowledge Graph / Neural Map.
3. Direction C: 3D Campus Service Portal.

Recommended implementation default after approval:

- Start with a low-risk visual prototype using either Spline embed or Motion-only 2.5D.
- If the selected direction requires true interaction, move to React Three Fiber + Drei with optimized GLB assets.
- Keep a mobile/reduced-motion fallback from the start.

## Product Manager Selection Questions

Please choose one primary direction:

1. A: 3D AI Console / Floating Workbench
2. B: Campus Knowledge Graph / Neural Map
3. C: 3D Campus Service Portal
4. D: Cinematic Scroll / 3D Frame Sequence

Also answer:

- Do you prefer the 3D visual to feel like a product dashboard, an AI brain/network, or a campus service space?
- Should the page be more dark/tech like the current version, or brighter/education-facing?
- Should we prioritize fast visual prototype with Spline, or code-native implementation with React Three Fiber?

## References

- Spline 3D websites: https://spline.design/solutions/3d-websites
- Spline docs: https://docs.spline.design/
- Spline 3D Library: https://docs.spline.design/designing-in-3-d/3d-library
- Huly landing reference: https://saaspo.com/pages/huly-landing-page
- Huly stack/palette reference: https://saaslandingpage.com/huly/
- Awwwards Nisa AI 3D reference: https://www.awwwards.com/inspiration/3d-web-design-meets-ai-nisa-ai-chatbot-landing-page
- LitStage education AI/3D reference: https://www.litstage.ai/
- Saras-3D AI Tutor reference: https://saras3d.ai/
- Sagenverse 3D education reference: https://www.sagenverse.com/education
- Motion for React: https://motion.dev/docs/react
- Rive React runtime: https://rive.app/docs/runtimes/react
- LottieFiles Marketplace: https://lottiefiles.com/marketplace
- Open Source 3D Assets: https://www.opensource3dassets.com/

## Mainland China Accessible Reference Set

Date added: 2026-05-22

The product manager is in mainland China, so design review should prioritize sites and resources that are more likely to open reliably from a mainland network. Overseas examples such as Linear, Spline, Awwwards, Rive, and Lottie remain useful references, but they should not be the only materials used for approval.

### UI/Product Website References

| Source | URL | Use for this project |
| --- | --- | --- |
| Ant Design | https://ant.design/index-cn | Enterprise-grade React component language, tables, forms, layout density, dashboard polish. |
| Arco Design | https://arco.design | Modern React enterprise visual system from ByteDance; useful for polished admin/workbench references. |
| TDesign | https://tdesign.tencent.com | Tencent design system; useful for dashboard, navigation, forms, and enterprise interaction references. |
| Semi Design | https://semi.design/zh-CN | Data/product-heavy React design system; useful for dense workbench pages and modern cards/tables. |
| AntV G6 | https://g6.antv.antgroup.com | Knowledge graph and relationship visualization reference for a future campus knowledge graph direction. |

### Design Tool And Inspiration Sources

| Source | URL | Use for this project |
| --- | --- | --- |
| 即时设计 | https://js.design | UI inspiration, component layout references, and design collaboration reference. |
| MasterGo | https://mastergo.com | UI design resources and product design references. |
| Pixso | https://pixso.cn | UI design resources and collaborative design references. |
| 墨刀 | https://modao.cc | Prototype and interaction-flow reference. |
| 站酷 | https://www.zcool.com.cn | Search for domestic AI, education, dashboard, and 3D web visual references. |

### 3D / Visualization References

| Source | URL | Use for this project |
| --- | --- | --- |
| Three.js 中文网 | http://www.webgl3d.cn | Chinese Three.js learning/reference site; useful if we choose React Three Fiber or native Three.js. |
| AntV G6 | https://g6.antv.antgroup.com | Good fit for non-WebGL graph/knowledge-map prototypes before full 3D. |
| DataV | https://datav.aliyun.com | Big-screen visualization inspiration; useful for operations/admin visual language, but avoid overusing "large-screen command center" style on the homepage. |
| IconPark | https://iconpark.oceanengine.com | Consistent icon source from ByteDance; useful for nav/actions/features if we do not use Lucide everywhere. |

### Practical Recommendation For Review

Use these mainland-accessible sources first:

1. Ant Design / Arco / TDesign / Semi for page layout and product polish.
2. AntV G6 for knowledge graph inspiration if Direction B is selected.
3. DataV only as selective inspiration for operations/data surfaces, not as the main homepage style.
4. 站酷 / 即时设计 / MasterGo / Pixso for visual screenshots that the product manager can open, annotate, and compare.

Keep the 3D direction choices unchanged:

- Direction A: 3D AI Console / Floating Workbench remains the recommended primary direction.
- Direction B: Campus Knowledge Graph / Neural Map remains the recommended backup.
- Direction C: 3D Campus Service Portal is still possible but depends heavily on asset quality.
- Direction D: Cinematic Scroll / 3D Frame Sequence is still useful if WebGL risk is too high.
