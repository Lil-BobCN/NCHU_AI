# Autoresearch Report: Homepage Reference Motion Design

Date: 2026-05-23
Status: draft-for-product-manager-alignment
Scope: Research, decomposition, and interview preparation only. No production frontend changes.

## 1. Executive Direction

The product manager's new homepage direction is feasible, but it should be treated as a homepage redesign node rather than a small visual tweak.

Recommended interpretation:

- First viewport: full-screen cinematic hero with a reserved video/motion layer.
- Top navigation: Linear-like, fixed, translucent, compact, product-site style.
- Initial entrance: hero video loads/plays first; navigation fades/slides downward into place with the hero sequence.
- Scroll behavior: Tongyi-like scroll narrative using large sections, scroll-triggered reveals, video/image panels, and content blocks entering with vertical translation and opacity/blur changes.
- Visual tone: Apple-like minimal glass/liquid material plus aerospace/AI technology atmosphere; avoid generic gradients and decorative blobs.
- Current NCHU wing animation: record as technical debt and reserve the hero slot; do not implement it now.

## 2. Reference Breakdown

### 2.1 Linear: Top Navigation And Product-Site Structure

Observed with Playwright at `https://linear.app/`.

Useful elements to emulate:

- Fixed top navigation with `backdrop-filter: blur(20px)`.
- Compact 72px header.
- Left brand mark, center/right navigation, right-side login/CTA.
- Navigation labels are short and restrained.
- Primary CTA is visually stronger but still compact.
- Hero content starts below the nav and uses a high-end product-site composition.
- Large typography with restrained supporting copy.
- Product preview/media is large and full-width enough to feel substantial.

How this maps to NCHU AI:

| Linear Pattern | NCHU AI Adaptation |
| --- | --- |
| Brand logo left | `NCHU AI` plus small school/AI mark |
| Product / Resources / Customers / Pricing | 产品能力 / 使用流程 / 适用角色 / 技术边界 |
| Log in / Sign up | 登录 / 开始体验 |
| Product screenshot hero | Reserved hero video/motion slot |
| Compact translucent nav | Glass-like fixed nav, appears after hero begins |

Do not copy:

- Linear's exact copy, brand, issue-tracking screenshots, or customer proof.
- Its exact dark/gray UI simulation unless it supports our school/AI/aerospace story.

### 2.2 Tongyi: Hero Media And Scroll Narrative

Observed with Playwright at `https://tongyi.aliyun.com/`.

Key evidence:

- The first viewport contains a large hero video asset: `portal-hero-video-2025-comp.mp4`.
- A poster fallback image is present.
- The hero video layer occupies about 1320px x 1010px at a 1440px viewport and extends behind/around central title content.
- Text entrance uses staged blur/scale/width reveal animation such as `fadeInUp`, `moveMaskSlide`, `blurScaleIn`, `moveGradient`, `revealWidth`.
- The next content sections use `scrollanimation_slidershow`-like classes and transform/transition states.
- Below the first screen, content is organized as large narrative blocks: model family, model cards, divider GIF, case/video grids, enterprise trust, contact.

Useful elements to emulate:

- Hero video with poster fallback.
- Full-screen first visual impact.
- Scroll cue at the bottom of the first viewport.
- Section reveal on scroll: opacity, translateY, blur, and mask/reveal.
- Media-heavy content blocks, not plain text cards.
- Large product capability sections that feel like "chapters".

How this maps to NCHU AI:

| Tongyi Pattern | NCHU AI Adaptation |
| --- | --- |
| Full hero video | Reserved NCHU wing/aerospace AI motion video |
| Large title over media | `NCHU AI` / AI counselor product statement over cinematic background |
| Scroll cue GIF | Minimal scroll indicator, possibly aircraft-line motif |
| Model family sections | 学生问答 / 辅导员辅助 / 知识运维 / 审计与边界 |
| Video case grids | Product capability previews and role workflows |
| Enterprise trust section | Demo honesty, school scenario, FastAPI/backend authority, data boundary |

Do not copy:

- Tongyi's exact model-family content.
- Its heavy number of asset/video cards unless we can supply meaningful project content.
- The exact Alibaba brand gradient language.

### 2.3 Apple / SpaceX Style Inputs

Apple page evidence:

- Apple iPhone pages use high-quality product imagery, large section titles, strong whitespace, and content grouped by product capabilities.
- Apple explicitly describes Liquid Glass as a consistent visual experience across apps and devices.

SpaceX page role:

- SpaceX-style pages are useful for cinematic aerospace atmosphere: dark/black hero, full-bleed media, concise uppercase/strong typography, high contrast CTAs.

How this maps to NCHU AI:

- Apple influence: glass panels, precise typography, white/black balance, minimal controls, polished spacing.
- SpaceX influence: aerospace storytelling, full-screen motion, dramatic lighting, aircraft/flight direction.
- NCHU-specific correction: keep it credible for a university AI counselor demo; avoid making it look like a rocket launch website or consumer gadget launch only.

## 3. Proposed Homepage Structure

### 3.1 First Viewport

Purpose:

Create the first impression: formal, high-tech, aerospace, AI-enabled school service.

Suggested layers:

1. Background video/motion placeholder
   - Current placeholder only.
   - Future debt: NCHU wing animation video.
2. Top navigation
   - Initially hidden or near top with low opacity.
   - Fades/slides down into fixed glass nav after hero start.
3. Hero copy
   - Minimal, not a long paragraph.
   - Product name as first signal: `NCHU AI`.
   - One-line value statement.
4. CTA cluster
   - `登录体验`
   - `了解能力`
5. Scroll cue
   - Indicates user can scroll into product sections.

### 3.2 Scroll Chapters

Initial placeholder content can be fuzzy, but structure should be intentional:

1. `AI 赋能校园咨询`
   - Student Q&A, source-backed answers, demo boundary.
2. `辅导员工作辅助`
   - Simulated case list, risk/status, advisory output.
3. `知识运维与审计`
   - Knowledge resources, seed/reset, audit trail.
4. `可信边界`
   - Simulated data, no production SSO, no real student data, backend authority.

Each chapter should use:

- Full-width section.
- Large title.
- 1-2 sentence explanation.
- Media mockup area.
- Scroll-triggered reveal.

## 4. Technical Implementation Implications

### 4.1 Required Frontend Techniques

| Need | Technique |
| --- | --- |
| Full-screen video hero | HTML `<video>` with poster fallback, object-fit cover, lazy/fallback states |
| Nav appears with hero | CSS/JS entrance state, IntersectionObserver or timeline |
| Linear-like glass nav | CSS `backdrop-filter`, fixed positioning, compact layout |
| Tongyi-like scroll reveal | IntersectionObserver + CSS transitions, or GSAP ScrollTrigger / Motion useScroll |
| Chapter transitions | opacity/translate/blur/mask transitions |
| Scroll cue | CSS animation or small SVG/GIF |
| Future wing asset | local video/Lottie/SVG slot abstraction |
| Reduced motion | `prefers-reduced-motion` fallback |
| Asset performance | poster image, preload policy, compressed self-hosted media |

### 4.2 Dependency Options

| Option | What It Solves | Pros | Cons | Recommendation |
| --- | --- | --- | --- | --- |
| CSS + IntersectionObserver only | Basic reveal and nav entrance | No new dependency, stable | Less cinematic for scrubbed chapter motion | Good first implementation |
| GSAP + ScrollTrigger | Tongyi-like precise scroll timelines, pin/scrub/reveal | Powerful and already covered by installed skills | Adds runtime dependency, needs cleanup in React | Best if PM wants strong scroll choreography |
| Motion for React | React-native scroll values and component animation | Clean React ergonomics, `useScroll` supports scroll-linked effects | Another runtime dependency; less ideal for complex timeline choreography | Good alternative |
| Lenis | Smooth scrolling feel | Polished scroll feel, used in creative sites | Can affect accessibility/mobile and complicate scroll triggers | Defer; not necessary first |
| Lottie/dotLottie | Future hero wing animation asset playback | Close to Ant Design X style | Needs final asset | Defer until hero asset exists |
| Rive | Interactive vector animation | Strong for stateful motion | Overkill for current homepage | Defer |
| Three.js | True 3D hero | Real 3D depth | High complexity, not needed now | Defer |

Recommended first technical route:

- Build with CSS + IntersectionObserver for the first polished version.
- If the scroll chapter motion still feels weak, approve GSAP + ScrollTrigger as a second node.
- Keep the hero motion slot format-neutral: it can later host `<video>`, Lottie, or SVG.

## 5. Skills / Resources Decision

### 5.1 Skills

Already installed/available skills are sufficient for the next design/planning pass:

- `frontend-design`
- `ui-ux-pro-max`
- `shadcn`
- `shadcn-component-discovery`
- `shadcn-component-review`
- `gsap-core`
- `gsap-react`
- `gsap-timeline`
- `gsap-performance`
- `gsap-plugins`
- `svg-animations`
- `visual-verdict`
- `playwright`
- `vercel-react-best-practices`

Potential optional skill:

- `LottieFiles/motion-design-skill`: still useful later when the deferred wing video/Lottie asset work resumes.

Do not install now:

- New random animated component skills.
- Three.js/R3F skills.
- Rive-specific skills.
- More shadcn animation registries.

### 5.2 Runtime Dependencies

Do not install runtime dependencies yet until the homepage motion SDAR is approved.

Potential future packages:

- `gsap` + `@gsap/react` if we approve GSAP ScrollTrigger route.
- `motion` if we choose Motion for React.
- `@lottiefiles/dotlottie-react` or `lottie-react` only after final hero asset route.
- `lenis` only if smooth-scroll feel is explicitly approved.

### 5.3 Assets Needed

Need later:

- Hero video placeholder asset or local temporary placeholder.
- Poster image for hero video.
- Future wing animation asset.
- Product mockup screenshots/videos.
- Optional aerospace abstract image/video, preferably generated or locally owned.

For first implementation, use neutral placeholder surfaces and CSS composition rather than external copyrighted assets.

## 6. Technical Debt Recorded

Recorded in:

- `.omx/logs/technical-debt-ai-counselor-demo.md`

Debt:

- `TD-0001: Homepage NCHU Emblem Wing Motion Asset`

Decision:

- Pause wing animation implementation now.
- Reserve hero video/motion slot.
- Continue homepage design and scroll narrative.

## 7. Recommended Development Node

Create a new approval/design node before implementation:

`SDAR-0007: Homepage Cinematic Hero And Scroll Narrative`

It should approve:

- first viewport structure;
- Linear-like top navigation behavior;
- Tongyi-like scroll narrative behavior;
- hero video placeholder and future asset slot;
- desktop-first scope;
- first implementation dependency policy;
- whether to start with CSS+IntersectionObserver or GSAP ScrollTrigger.

## 8. Deep Interview Readiness

The request is now clear enough to ask targeted confirmation questions. The biggest unresolved decision is not visual preference in general, but the implementation intensity for scroll motion.

The first interview question should decide the first technical route:

- A: CSS + IntersectionObserver first, then upgrade to GSAP if weak.
- B: GSAP + ScrollTrigger from the start.
- C: Motion for React from the start.

Recommendation:

Choose A unless the product manager wants the first redesign to prioritize strong cinematic scroll choreography over implementation simplicity.

## 9. Sources And Evidence

- Tongyi: https://tongyi.aliyun.com/
- Linear: https://linear.app/
- Apple iPhone page: https://www.apple.com/iphone/
- SpaceX homepage: https://www.spacex.com/
- GSAP ScrollTrigger docs: https://gsap.com/docs/v3/Plugins/ScrollTrigger/
- Motion `useScroll` docs: https://motion.dev/docs/react-use-scroll
- Lenis GitHub/docs reference: https://github.com/darkroomengineering/lenis
- Local Playwright evidence:
  - `output/playwright/reference-sites/linear-home.png`
  - `output/playwright/reference-sites/tongyi-current.png`

