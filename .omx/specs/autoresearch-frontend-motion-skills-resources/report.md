# Autoresearch Report: Frontend Motion Skills And Resources

Date: 2026-05-23
Status: approved-for-review
Scope: Research only. No skills, packages, assets, or frontend code were installed or changed.

## 1. Executive Conclusion

For the current NCHU AI homepage motion task, we do not need to blindly download more general frontend skills.

Recommended action:

1. Add one optional specialist skill: `LottieFiles/motion-design-skill`, if we decide to use Lottie/dotLottie or want AI to help with motion direction and Lottie-oriented asset review.
2. Do not install additional animation UI libraries yet.
3. Do not add runtime dependencies until the final asset route is approved.
4. The most important missing resources are not skills. They are the school emblem source assets and motion references.

In short:

- Need skill? Optional yes: LottieFiles motion-design-skill.
- Need runtime dependency now? No. Decide after asset route.
- Need design resources now? Yes: exact school emblem vector layers, final-frame reference, and motion examples.
- Need external UI component resources now? No. Our existing shadcn, frontend-design, GSAP, SVG, visual QA skills are enough for the next planning/demo step.

## 2. Current Installed Capability

The current session already exposes relevant local skills:

| Area | Current Skill Coverage | Decision |
| --- | --- | --- |
| shadcn/ui components | `shadcn`, `shadcn-component-discovery`, `shadcn-component-review` | Enough. No extra shadcn skill needed now. |
| General frontend design | `frontend-design`, `ui-ux-pro-max`, `visual-ralph`, `visual-verdict` | Enough for layout and visual iteration. |
| React quality | `vercel-react-best-practices`, `karpathy-guidelines` | Enough for React implementation discipline. |
| GSAP animation | `gsap-core`, `gsap-react`, `gsap-timeline`, `gsap-performance`, `gsap-plugins` | Enough for SVG+GSAP route. |
| SVG animation | `svg-animations` | Enough for emblem/vector animation analysis and custom SVG motion. |
| Browser validation | `playwright`, `screenshot` | Enough for screenshots/video checks after implementation. |

Therefore, the gap is not "lack of generic frontend skill". The gap is "lack of exact production asset and final animation route".

## 3. New Candidate Skill Found

### LottieFiles Motion Design Skill

Source:

- GitHub: https://github.com/LottieFiles/motion-design-skill
- LottieFiles Creator MCP docs: https://docs.lottiefiles.com/en/creator/13_ai-tools/lottie-creator-mcp

What it is:

- A LottieFiles skill intended to improve AI-assisted motion design.
- It includes guidance around motion specs, Lottie JSON, animation quality, and design/animation decision-making.
- It pairs naturally with LottieFiles Creator / Lottie MCP workflows, but the skill itself is useful as design guidance even before a runtime dependency is chosen.

Fit for our project:

| Question | Answer |
| --- | --- |
| Does it help with homepage hero motion? | Yes, especially for motion language, Lottie asset review, and reducing vague prompt guessing. |
| Does it replace final asset production? | No. We still need source vectors or a produced animation asset. |
| Does it require us to use Lottie runtime? | Not strictly, but it is most valuable if Lottie/dotLottie remains the preferred route. |
| Should we install now? | Recommended before the next motion-design iteration, but not required for plain SVG+GSAP coding. |

Recommendation:

Install only this additional skill if we continue the Lottie/dotLottie route. Do not add multiple overlapping motion skills now.

## 4. Runtime Package Decision

Runtime packages are different from skills. Skills help me work. Runtime packages ship in the frontend.

Do not install any runtime animation package until PM approves the final asset route.

| Final Route | Likely Runtime Package | Install Now? | Reason |
| --- | --- | --- | --- |
| Lottie/dotLottie | `@lottiefiles/dotlottie-react` or `lottie-react` | No | Need actual Lottie/dotLottie asset first. |
| SVG+GSAP | `gsap`, likely `@gsap/react` | No | Need confirm we are coding the animation ourselves. |
| Rive | `@rive-app/react-canvas` or Rive runtime | No | Only worth it for interactive/state-machine motion. |
| Transparent video | No animation runtime required | No | Needs final WebM/MP4 asset and video fallback rules. |
| Framer Motion / Motion | `motion` or `framer-motion` | No | Not the best match for emblem-accurate sequential vector assembly. |
| Three.js | `three`, `@react-three/fiber` | No | Overkill unless we truly require real 3D geometry/camera. |

## 5. External UI / Component Resources

Resources reviewed:

- Magic UI: https://magicui.design/docs/components
- Animate UI: https://animate-ui.com/docs
- shadcn-compatible animated component ecosystem

Decision:

Do not download or adopt animated component packs for the NCHU wing hero right now.

Reason:

- These libraries help with generic animated cards, text reveals, gradients, buttons, and background effects.
- Our main difficulty is not "make something move"; it is "make the school emblem wing symbols assemble accurately and tastefully".
- Adding decorative component packs risks moving away from the approved formal AI product direction.

Possible later use:

- Text reveal on the left product capability copy.
- Subtle CTA/button or feature-card entrance animation.
- Not the core school-emblem wing animation.

## 6. Resources We Actually Need From The Human Side

These are higher priority than installing more skills:

| Resource | Required? | Why |
| --- | --- | --- |
| Official school emblem vector source: SVG/AI/PDF | Yes | Enables exact geometry and color extraction. |
| Three wing symbols as separate vector layers | Yes | Required for sequential fly-in and final lockup. |
| Final-frame reference image | Yes | Lets us verify the end state matches the emblem layout. |
| Motion reference video/gif | Strongly recommended | Reduces ambiguity in timing, easing, depth, and visual quality. |
| Official/approved color values | Strongly recommended | Avoids inaccurate brand colors. |
| Decision on transparent video acceptability | Required before implementation | Determines whether video fallback can be used if Lottie is insufficient. |
| License/usage confirmation for school emblem | Required before final shipping | Avoids asset-rights ambiguity. |

## 7. Recommended Workflow From Here

### Step 1: Install Only One Additional Skill If Approved

Install:

- `LottieFiles/motion-design-skill`

Purpose:

- Improve Lottie/motion design judgment.
- Help write better motion specs.
- Help review whether an exported Lottie asset is production-usable.

Do not install:

- More random animated UI packs as skills.
- More GSAP skills; current GSAP skill set is already sufficient.
- Rive-specific skills unless PM chooses Rive.
- Three.js skills unless PM chooses a true 3D implementation.

### Step 2: Build A Motion Asset Package

Before any implementation, collect:

- school emblem source vector;
- wing symbols split into 3 vector layers;
- final lockup reference;
- one or more motion reference videos;
- desired final route preference: Lottie, SVG+GSAP, or transparent video.

### Step 3: Decide Production Route

Use a short SDAR-style approval:

- Option A: Lottie/dotLottie
- Option B: SVG+GSAP
- Option C: Transparent WebM
- Option D: Rive

Recommended default:

- Lottie/dotLottie if an accurate exported asset exists.
- SVG+GSAP if exact geometry must be coded and controlled.
- Transparent WebM if the designer gives a finished approved animation.

### Step 4: Only Then Install Runtime Package

Examples:

- Lottie route: install `@lottiefiles/dotlottie-react` or `lottie-react`.
- SVG+GSAP route: install `gsap` and `@gsap/react`.
- Video route: no animation package.
- Rive route: install Rive React runtime.

## 8. Mainland China / Local Hosting Constraint

Final implementation should not depend on loading animation files or scripts from external websites.

Rules:

- Download/generate final assets once, then store them locally in the project.
- Avoid CDN runtime dependencies in production demo.
- Keep a static fallback image for reduced motion and failed animation load.
- Prefer file formats that can be self-hosted: `.lottie`, `.json`, `.svg`, `.webm`, `.mp4`, `.png`.

## 9. Decision Summary

| Item | Decision |
| --- | --- |
| Download more generic frontend skills? | No. |
| Download a Lottie/motion-specific skill? | Yes, recommended: `LottieFiles/motion-design-skill`, if PM approves. |
| Install runtime dependency now? | No. Wait for final route approval. |
| Download animated shadcn/Magic UI blocks now? | No. Use only as inspiration later if needed. |
| Need human-provided resources? | Yes. This is the critical blocker. |
| Best next action | Prepare asset checklist and approve whether to install LottieFiles motion-design-skill. |

## 10. Sources

- LottieFiles motion-design-skill: https://github.com/LottieFiles/motion-design-skill
- LottieFiles Creator MCP: https://docs.lottiefiles.com/en/creator/13_ai-tools/lottie-creator-mcp
- dotLottie React docs: https://developers.lottiefiles.com/docs/dotlottie-player/dotlottie-react/usage/
- GSAP installation/docs: https://gsap.com/docs/v3/Installation/
- Rive React runtime docs: https://rive.app/docs/runtimes/react/react
- Magic UI components: https://magicui.design/docs/components
- Animate UI docs: https://animate-ui.com/docs
- Local report: `.omx/specs/autoresearch-vibe-motion-animation-route/report.md`

