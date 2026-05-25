# Autoresearch Report: Homepage 3D Wing Reference Cases

Date: 2026-05-22
Status: ready for product-manager review
Scope: research only, no frontend/prototype code changes

## 1. Executive Conclusion

Current demo quality is below the target mainly because we were trying to validate layout, emblem geometry, material, and motion at the same time without first locking a reference direction and a clean vector asset pipeline.

My recommended direction is:

1. Use **Ant Design X** as the homepage layout rhythm reference: full-page AI product hero, dense but polished product capability expression, not a small card-like stage.
2. Use **Tongyi Lab / Linear** as visual storytelling references: credible AI-product atmosphere, feature emergence, refined motion, strong first-screen signal.
3. Build the NCHU wing hero first as **high-quality 2.5D SVG + GSAP timeline**, not immediate true 3D.
4. After the wing silhouette is approved, evaluate **Three.js SVGLoader / Spline-like 3D treatment** for depth, lighting, and floating.

This means the next development should not be "continue blindly adjusting the current demo". It should be: select references -> vectorize the official wing symbol into clean parts -> animate the parts into an emblem-accurate final lockup -> validate with screenshots.

## 2. How To Review These References

Please review the high-priority links first:

- Ant Design X: https://x.ant.design/
- Tongyi Lab: https://tongyi.aliyun.com/
- Spline 3D Websites: https://spline.design/solutions/3d-websites
- Spline Examples: https://spline.design/examples
- Rive for Websites: https://rive.app/use-cases/websites
- GSAP Timeline: https://www.gsap.com/docs/v3/GSAP/Timeline/
- Three.js SVGLoader: https://threejs.org/docs/pages/SVGLoader.html

Main things to inspect:

- Is the first screen full and immersive enough?
- Does the hero visual feel like a product asset rather than a small decoration?
- Does the page explain product capabilities before login?
- Does motion help understanding, or does it become decorative noise?
- Is the visual style credible for a school AI counselor product?

Accessibility note:
I cannot guarantee your exact mainland China network result from here. I have marked links as "likely accessible" only when they are Chinese domestic domains or official Chinese docs. Overseas references may be slow or blocked, so they should be treated as design inspiration, not runtime dependencies.

## 3. Candidate References

| Tier | Reference | Link | Accessibility Note | What To Inspect | Match To Our Target | Mismatch / Risk |
| --- | --- | --- | --- | --- | --- | --- |
| High | Ant Design X homepage | https://x.ant.design/ | Likely accessible. Ant Design ecosystem is commonly reachable in China. | Full-page AI product hero, RICH AI interaction framing, AI component/product positioning. | Closest layout and AI-product rhythm reference. Supports "not a role-selection page". | Its visual object is not our emblem; we should borrow layout rhythm, not copy brand style. |
| High | Ant Design X Chinese docs / overview | https://x.ant.design/components/overview-cn/ | Likely accessible. | AI components such as welcome, prompts, sender, bubble, sources. | Useful after homepage, especially for student Q&A and role workspaces. | More component-level than homepage hero. |
| High | Tongyi Lab homepage | https://tongyi.aliyun.com/ | Likely accessible, Alibaba domain. | Dark AI brand atmosphere, large visual field, capability/model list, cinematic product expression. | Good reference for credible Chinese AI-product tone. | Too broad and model-platform-like; our product must stay school counseling specific. |
| Medium | Baidu Qianfan product page | https://cloud.baidu.com/product/qianfan.html | Likely accessible, Baidu domain. | Enterprise AI product information hierarchy, capability blocks, formal trust language. | Good for later product sections below hero. | Less suitable for the first-screen wing visual; more conventional cloud product page. |
| Medium | Tencent Yuanqi | https://yuanqi.tencent.com/ | Likely accessible, Tencent domain. | AI Agent product positioning, user-facing agent examples. | Useful for understanding "AI assistant/agent platform" communication. | Page is marketplace/content-heavy; not the target hero style. |
| Medium | Linear homepage | https://linear.app/ | Overseas; may be slow or blocked. | Premium product homepage, animated product interface, feature storytelling after hero. | Strong reference for "product before login" and polished product narrative. | Not China-accessible enough to rely on; no emblem-like 3D object. |
| High | Spline 3D websites | https://spline.design/solutions/3d-websites | Overseas; may be slow. | Large right-side / full-hero 3D object scale, materials, lighting, spatial layout. | Good visual reference for 3D object weight and atmosphere. | Spline runtime should not be assumed for production until dependency approval; China access may be unstable. |
| Medium | Spline examples | https://spline.design/examples | Overseas; may be slow. | 3D templates, object lighting, floating elements, hero-ready composition. | Useful for showing the level of polish expected from a right-side hero object. | Template visuals may drift into generic tech decoration if copied directly. |
| High | Rive for websites | https://rive.app/use-cases/websites | Overseas; may be slow. | Interactive hero sections, animated logos, product demos, lightweight web animation. | Very relevant for emblem-like animated symbol behavior. | Requires a dedicated Rive asset workflow; not ideal if we want everything code-native. |
| Medium | LottieFiles featured animations | https://lottiefiles.com/featured-free-animations | Overseas; may be slow. | Animated icons, loaders, UI micro-motion. | Useful for small supporting animations and loading states. | Not enough for our main wing hero; quality varies by asset. |
| High | GSAP Timeline docs | https://www.gsap.com/docs/v3/GSAP/Timeline/ | Overseas docs; usually accessible but not guaranteed. | Sequencing, staggered entry, assembly animation, then idle loop. | Best fit for "parts fly in first, then whole symbol floats". | It is implementation reference, not visual style reference. |
| Medium | GSAP MorphSVG docs | https://gsap.com/docs/v3/Plugins/MorphSVGPlugin/ | Overseas; plugin licensing must be checked before use. | Shape morphing and advanced SVG transitions. | Could help if wing pieces need path morphing. | Not required for first implementation; plugin constraints could complicate approval. |
| High | Three.js SVGLoader docs | https://threejs.org/docs/pages/SVGLoader.html | Overseas docs; usually accessible but not guaranteed. | Loading SVG paths into Three.js shapes; possible path toward real 3D/extrusion. | Good future path after final wing SVG is approved. | True 3D too early will hide geometry problems behind lighting/camera complexity. |
| Medium | Spline code/self-host docs | https://docs.spline.design/doc/exporting-as-code/docDdDWmkQri | Overseas; may be slow. | React/code export and self-hosting possibilities. | Useful only if we later choose Spline as production or prototyping tool. | Self-host/export limits and dependency approval must be handled before adoption. |

## 4. Preferred Direction Options For Review

### Option A: Ant Design X Layout + SVG/GSAP Wing Hero

Recommended.

Description:
Full-screen Ant Design X-like hero. Left side progressively reveals product capabilities. Right side uses a clean SVG wing symbol derived from the official NCHU emblem. GSAP controls the animation: pieces fly in, assemble, then the whole symbol gently floats.

Why it fits:

- Most controllable.
- Best for preserving emblem geometry.
- Does not require heavy 3D runtime immediately.
- Easy to validate with screenshots.
- Good fit for React + TypeScript + Ant Design / shadcn stack.

Main risk:
Requires a clean vector wing asset. If the wing is traced poorly, the result will still look cheap.

### Option B: Tongyi-Like Cinematic AI Hero + 2.5D Wing Object

Description:
Use a darker, more cinematic AI-product page like Tongyi Lab. The wing object is still SVG-based but gets stronger material treatment: gradients, highlights, shadow, depth layers, glow, and subtle atmospheric background.

Why it fits:

- Stronger "AI product" feeling.
- Better for formal public-facing Demo.
- More memorable than a plain enterprise dashboard hero.

Main risk:
Easy to become too decorative if the product message is not clear.

### Option C: Spline-Like 3D Object Direction

Description:
Use Spline examples as visual references for depth, material, and floating. Implementation can be either Spline-exported or custom Three.js, but only after separate approval.

Why it fits:

- Closest to the user's "3D website" ambition.
- Can create a premium hero if executed well.

Main risk:
True 3D adds runtime, performance, accessibility, and China-network risks. It should not be the first repair step until the emblem vector is stable.

### Option D: Rive/Lottie Motion Asset Direction

Description:
Create the wing animation in Rive or Lottie as a dedicated animated asset, then embed in React.

Why it fits:

- Good for logo-like assembly animation.
- Easier for designer-style timeline editing than hand-coded SVG.

Main risk:
Needs external authoring workflow and runtime approval. If we need exact geometry plus programmatic React control, SVG/GSAP may be simpler.

### Option E: Linear-Like Product Storytelling Below Hero

Description:
Keep the first hero AI/wing-focused, then use Linear-like full-width product sections below it to explain student, counselor, admin, knowledge, audit, and Demo boundaries.

Why it fits:

- Excellent for "click link -> see product features -> login" behavior.
- Avoids turning homepage into a login panel.

Main risk:
Linear is a product-development tool, so its exact visual language should not be copied.

## 5. Terms The Product Manager Can Use

Use these terms when describing what you want. They map fuzzy visual intent into frontend/design language.

| What You Might Say | Frontend / Design Term | Meaning For Development |
| --- | --- | --- |
| 网站点开后的第一屏 | Hero section / above-the-fold | The first viewport before scrolling. |
| 页面要铺满，不要太细 | Full-bleed / 100vh hero / large visual stage | Use the whole viewport, not a narrow card. |
| 左边逐渐浮现产品内核 | Staggered capability reveal / progressive disclosure | Headline, subtitle, and feature chips/cards animate in sequence. |
| 右边是 3D 浮动元素 | Hero visual / 2.5D object / 3D scene | Main visual object on the right side. |
| 三个飞翼从左下往右上飞 | Staggered fly-in / diagonal entry animation | Each piece starts off-screen or lower-left and enters in sequence. |
| 最后定格成校徽里的形状 | Final lockup / emblem fidelity / silhouette fidelity | Final geometry must match the official emblem symbol. |
| 飞翼不要变成纸飞机 | Preserve source silhouette | Do not replace the emblem geometry with generic icons. |
| 最后整体轻微起伏 | Idle float / breathing loop | After assembly, the full object moves subtly as one group. |
| 不要外面那个圆形校徽框 | Symbol-only lockup / no badge container | Use only the wing/aircraft symbol, not the full emblem circle. |
| 现在质感差 | Weak material / poor lighting / raster artifact | Need better vector shape, gradients, shadows, and anti-aliasing. |
| 动效要高级但不要乱 | Purposeful motion / restrained choreography | Motion should explain the product/brand, not distract. |
| 产品功能要出现 | Value proposition + capability cards/chips | Show what the product does before login. |
| 后面可以继续展开 | Product narrative sections | Sections below hero for student/counselor/admin/admin knowledge flows. |

## 6. Proposed Formal Development Path After Review

No implementation is done in this research task. If the product manager approves the direction, the formal path should be:

1. Pick one primary layout reference and one visual/motion reference.
2. Create a clean vector asset from `.omx/references/nchu-emblem-official.png`.
3. Split the wing into named vector groups, for example:
   - `wing-main`
   - `wing-upper`
   - `wing-lower`
   - optional highlight/shadow groups
4. Build a static hero composition first:
   - full-width hero,
   - left product message,
   - right final wing lockup,
   - desktop-first layout,
   - mobile fallback layout.
5. Add animation only after static geometry is accepted:
   - entry timeline,
   - assembly lock,
   - idle float,
   - reduced-motion fallback.
6. Validate with:
   - desktop screenshot,
   - mobile screenshot,
   - build/lint,
   - visual-verdict score,
   - product-manager review.
7. Only after the 2.5D SVG version is accepted, decide whether to:
   - keep SVG/GSAP,
   - convert to Three.js,
   - use Spline/Rive as an authored asset path.

## 7. My Recommendation

For the next round, I recommend selecting:

- Layout baseline: **Ant Design X**.
- Visual atmosphere: **Tongyi Lab**, with some Linear-style product storytelling restraint.
- Motion implementation: **SVG + GSAP timeline**.
- Future 3D exploration: **Three.js SVGLoader** or **Spline-style reference**, only after wing geometry approval.

This is the shortest path to a high-quality result because it separates three problems that were previously mixed together:

- What should the page layout be?
- What should the wing symbol look like at rest?
- How should the wing animate into that final state?

## 8. Product Manager Review Checklist

Please review and answer these points when ready:

1. Do you agree that Ant Design X should be the primary layout reference?
2. Do you prefer the visual atmosphere closer to Tongyi Lab, Spline, or Linear?
3. Should the next prototype stay 2.5D SVG, or do you want true 3D explored immediately despite the extra risk?
4. Should the wing be more metallic/glass-like, or flatter and more institutional?
5. Should the animation be subtle/formal or more cinematic/strong?

