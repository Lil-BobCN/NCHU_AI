# Autoresearch Report: Vibe Motion Animation Route Evaluation

Date: 2026-05-23
Status: approved-for-review
Scope: Research only. No frontend code, dependency, or asset changes.

## 1. Executive Conclusion

Vibe Motion is worth using as an upstream exploration tool, not as the final production route by itself.

For the NCHU AI homepage wing animation, the practical route should be:

1. Use Vibe Motion / similar AI motion tools to generate motion references, storyboard variants, and possibly a video proof.
2. Product manager selects the desired motion direction.
3. Final production asset is authored as Lottie/dotLottie, Rive, SVG+GSAP, or transparent WebM according to the required fidelity and runtime constraints.
4. The final asset is self-hosted in the project and integrated into React.

If the goal is Ant Design X-like web hero motion, the preferred production route remains Lottie/dotLottie or a professionally authored vector/SVG motion asset. Vibe Motion can help us reduce creative guessing, but prompt-only generation cannot guarantee emblem-accurate geometry, exact final positioning, reusable runtime control, or stable revision behavior.

## 2. What "Vibe Motion" Refers To

"Vibe Motion" is not one stable frontend technology name. Current search results show at least four meanings:

| Meaning | Evidence | Relevance |
| --- | --- | --- |
| Higgsfield Vibe Motion / AI Motion Design | Higgsfield describes AI motion design as text-to-animation with uploaded logos/assets, presets, editable code/controls, and HD/4K video export. | Strong for concept exploration and branded motion drafts. |
| Generic vibe-coding motion generation | Press coverage describes no-code vibe generation for motion graphics that can produce animation and underlying code. | Useful as a workflow idea, but still needs production validation. |
| Specific products using the name "Vibe Motion" | vibemotion.video claims conversational motion generation with MP4/MOV/GIF/WebM and also lists Lottie JSON. | Potentially relevant, but product maturity and export quality need validation before adoption. |
| AI node/canvas motion tools | Motn describes node-based prompt, image, brand, style, code motion, video generation, and reel export workflows. | Useful for ideation and parallel variants, not automatically a final asset pipeline. |

## 3. Evidence Reviewed

| Source | What It Says | Evidence Type | Interpretation |
| --- | --- | --- | --- |
| Higgsfield AI Motion Design: https://higgsfield.ai/ai-motion-design | Text-to-animation, upload logos/SVG/images, motion presets, editable colors/timing/text, export video up to 4K. | Official product claim | Good for generating branded video/motion drafts. The public page emphasizes video export, not production Lottie/dotLottie export. |
| Higgsfield Vibe Motion Guide: https://higgsfield.ai/blog/Higgsfield-Vibe-Motion-Guide-AI-Motion-Design | Positions Vibe Motion for infographics, presentations, logo/brand elements, chat-based iteration, templates, and UI controls. | Official guide | The described workflow matches our need for fast direction-finding, especially if we upload exact school wing assets. |
| SiliconANGLE launch article: https://siliconangle.com/2026/02/05/higgsfield-launches-vibe-editor-creating-motion-graphics/ | Reports a no-code vibe generator for motion graphics, aimed at marketing/demo/visualization workflows. | Third-party report | Confirms market positioning, but does not prove production-grade exactness for our logo animation. |
| vibemotion.video: https://vibemotion.video/ | Claims AI motion graphics generation, brand kit, 4K exports, MP4/MOV/GIF/WebM, and lists Lottie JSON among export options. | Product claim | Worth testing only if we later approve a vendor/tool trial. Need verify actual Lottie quality and local hosting rights. |
| Motn: https://www.motn.ai/how-it-works | Describes prompt/image/brand/style nodes, multiple generated variants, Code Motion, Gen Video, and reel export. | Product claim | Useful workflow model: generate variants, compare, fork. Not enough alone for final integration. |
| Gen2D: https://gen2d.com/ | Image -> motion -> export SVG/SMIL or Lottie JSON. | Product claim | More directly aligned with lightweight web animation than video-first tools, but maturity must be validated. |
| LottieFiles dotLottie web docs: https://developers.lottiefiles.com/docs/dotlottie-player/dotlottie-web/ | Official web player supports Lottie/dotLottie with browser and Node environments; optional workers/offscreen canvas improve performance. | Official runtime docs | Strong production route for Ant Design X-like web animation when final asset is available. |
| LottieFiles React docs: https://developers.lottiefiles.com/docs/dotlottie-player/dotlottie-react/usage/ | React component can load `.lottie`, autoplay/loop, expose playback controls and events. | Official runtime docs | Fits our React + TypeScript frontend. |
| Linearity Lottie export guide: https://www.linearity.io/academy/move/mac/user-guide/export/lottie-files-export/ | Lottie is presented as useful for web/app animation; clean vector shapes export most reliably. | Tool documentation | Supports the requirement that we should provide clean vector wing assets, not rely on video tracing. |
| Rive web runtime: https://rive.app/docs/runtimes/web/web-js | Rive provides JS/WASM runtime, state machines, canvas/WebGL packages, and responsive resizing. | Official runtime docs | Good if we need interactive stateful animation, but it adds a different authoring/runtime path. |
| GSAP docs: https://gsap.com/docs/v3/ | GSAP can animate CSS, attributes, timelines, SVG plugins, responsive/accessibility helpers. | Official runtime docs | Strong if we build the wing from SVG and choreograph exact fly-in/floating behavior in code. |
| Reddit MotionDesign / AfterEffects threads | Motion designers report revision/control concerns for AI-generated motion tools. | Community feedback | Low authority but useful risk signal: prompt-only AI motion may fail normal client feedback loops. |

## 4. Can Vibe Motion Achieve The Desired NCHU Wing Effect?

Desired effect:

- Main site hero follows a full-page Ant Design X-like AI product layout.
- Left side: product core/capabilities emerge through motion.
- Right side: three wing/aircraft symbols from the school emblem.
- The three wing symbols keep their relative emblem layout.
- They fly in sequentially from left/lower-left toward upper-right.
- Final still state must match the emblem composition.
- Then the whole wing group gently floats.
- No circular badge container.

Assessment:

| Requirement | Vibe Motion Feasibility | Risk |
| --- | --- | --- |
| Generate mood/reference animation quickly | High | Low |
| Use uploaded logo/SVG/image as visual context | Medium-high, depending on product | Medium |
| Make a polished video sample | Medium-high | Medium |
| Preserve exact school-emblem geometry | Medium if exact vector/final-frame constraints are provided; low if prompt-only | High |
| Export production-ready Lottie/dotLottie | Uncertain; depends on the specific tool and export quality | High |
| Transparent background for hero embedding | Possible with WebM/alpha or Lottie, but must be verified | Medium |
| React runtime control, pause, reduced motion | Strong only after converting to Lottie/Rive/SVG+GSAP or a controlled video component | Medium |
| Easy iterative revisions after PM feedback | Medium for rough variants; low for pixel-exact logo motion if only prompt-based | High |

Conclusion:

Vibe Motion can help us understand and approve the intended motion. It can probably produce a convincing preview video if we give it exact emblem assets and a clear storyboard. It should not be treated as guaranteed final implementation until it passes an asset-quality test:

- final frame matches provided emblem composition;
- transparent background or clean compositing works;
- local self-hosting is allowed;
- exported format is stable in our React page;
- file size and performance are acceptable;
- PM can request small changes without regenerating from scratch.

## 5. Route Comparison

| Route | Best Use | Pros | Cons | Fit For Our Final Hero |
| --- | --- | --- | --- | --- |
| Vibe Motion / AI motion tool | Fast concept, storyboard, reference video | Fast, visual, reduces creative ambiguity, good for PM selection | Exact geometry and revision control uncertain; export formats vary; may require external platform | Good as exploration; risky as final-only route |
| Lottie/dotLottie | Lightweight web/app vector animation | Ant Design X-like, small, self-hostable, React-friendly, controllable playback | Requires clean vector asset and proper authoring/export | Best default final route |
| Rive | Interactive/stateful vector animation | Strong runtime, state machines, responsive canvas, high polish | Requires Rive authoring workflow and runtime dependency | Good if animation must react to user input/state |
| SVG + GSAP | Exact code-controlled logo choreography | Precise, inspectable, good for custom fly-in/floating behavior, no black-box asset | More developer labor; 3D feel must be hand-authored; complex SVG paths can get heavy | Best if final emblem accuracy is highest priority |
| Transparent WebM/MP4 video | Highest visual fidelity, easiest if designer supplies final render | What-you-see-is-what-ships; simplest for complex 3D/rendered motion | Less responsive/interactable; video size; alpha support and mobile behavior need care | Good fallback if we receive a finished approved animation video |
| Three.js / real 3D | Real 3D depth and camera | True 3D control, can be impressive | Most expensive, easiest to overbuild, high visual QA burden | Not recommended for this emblem fly-in unless 3D is non-negotiable |

## 6. Recommended Workflow For This Project

### Stage A: PM Asset Package

Ask PM/designer to provide:

- School emblem vector source, preferably SVG/AI/PDF.
- The three wing symbols as separate vector layers.
- Final-frame reference image showing the exact three-wing layout.
- Color rules: official blue/green/red or approved hero colors.
- Desired background: transparent, light, or hero-scene-specific.
- Motion storyboard: entry direction, order, timing, final lockup, floating loop.

### Stage B: Vibe Motion Exploration

Use Vibe Motion or similar tools only to generate options:

- 3 to 5 candidate motion references.
- One selected direction for timing and energy.
- Optional short video that demonstrates the intended narrative.

Acceptance for this stage:

- PM confirms the motion story, not final implementation quality.
- We do not commit the generated asset to production yet.

### Stage C: Production Asset Decision

Choose one final route:

1. Lottie/dotLottie if we can get or author clean vector animation.
2. SVG+GSAP if exact emblem geometry and code-level control matter most.
3. Transparent WebM if PM/designer supplies a final approved rendered animation.
4. Rive only if we need interactive stateful behavior.

### Stage D: React Integration

Integrate into homepage with:

- local self-hosted asset under frontend public/assets or src assets;
- no external CDN dependency for the final demo;
- `prefers-reduced-motion` fallback;
- static poster/final-frame fallback;
- desktop-first layout, with mobile graceful fallback;
- performance check on first load and animation loop.

## 7. Recommendation

Recommended decision:

Use Vibe Motion as an exploration and approval-reference tool, but keep Lottie/dotLottie as the preferred final web animation format. If the final effect cannot be exported cleanly as Lottie/dotLottie, use SVG+GSAP for exact emblem assembly or transparent WebM for a fully pre-rendered motion piece.

Reason:

- The user wants to reduce Codex creative guessing. Vibe Motion helps by producing visible references early.
- The final state must match the school emblem. That requires controlled source assets and deterministic final-frame verification.
- The website should be robust in mainland China. Final runtime assets should be self-hosted and not depend on external generation platforms.
- Prior Ant Design X research found its hero robot motion is Lottie-style asset playback, so Lottie remains the closest analog.

## 8. Risks And Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Prompt-generated output does not match emblem geometry | High | Require vector layers and exact final-frame reference before generation. |
| Tool exports only video, not clean Lottie | Medium-high | Treat video as reference or use transparent WebM fallback; do not promise Lottie unless tested. |
| External platform cannot be reliably accessed in mainland China | Medium | Use external tools only for asset production; self-host final output locally. |
| Licensing/commercial usage unclear | High | Store source, plan, and export-license evidence before committing asset. |
| Animation looks decorative but not product-aligned | Medium | PM reviews storyboard before implementation. |
| Large file or janky loop | Medium | Test file size, load time, reduced-motion fallback, and desktop/mobile rendering. |

## 9. Product-Manager Decision Questions

Before implementation, the PM should confirm:

1. Do we use Vibe Motion only for reference exploration, not as the guaranteed final technical implementation?
2. Can you provide the school emblem source as clean SVG/AI/PDF and the three wing symbols as separate layers?
3. Is the final animation allowed to be a transparent video if Lottie cannot preserve the desired effect?
4. Is exact emblem geometry more important than 3D depth?
5. Should the final asset route be approved through a small SDAR before we add runtime dependencies such as dotLottie, Rive, or GSAP?

## 10. Final Answer To The Research Question

是否可取：

可取，但定位应是“动效方向探索/样片生成”，不是“最终网页动效的唯一生产方案”。

是否能达到最终效果：

能接近，甚至可以产出你想要的视觉样片；但如果要求最终网页中三个飞翼准确组成校徽形态、可自托管、可维护、可响应前端布局，那么必须把 Vibe Motion 的输出转化为受控生产资产。最稳的最终路线仍是 Lottie/dotLottie 或 SVG+GSAP；如果你提供完整成片，透明 WebM/MP4 也可以作为落地路线。

