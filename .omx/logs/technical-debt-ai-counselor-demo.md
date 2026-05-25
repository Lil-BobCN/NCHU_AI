# Technical Debt: AI Counselor Demo

Date: 2026-05-23
Status: active

## TD-0001: Homepage NCHU Emblem Wing Motion Asset

Status: deferred
Owner: Product Manager + Codex
Recorded: 2026-05-23

### Context

The homepage was previously explored with several 3D/SVG/PNG wing animation prototypes. Current visual quality did not meet the product-manager target. The product manager has decided to pause this line and continue polishing the website structure and visual design first.

### Desired Future Outcome

The first viewport should reserve a video/motion area for a future NCHU emblem wing animation:

- User lands on the homepage and sees a full-viewport cinematic video/motion scene.
- The video/motion will later contain the school-emblem wing animation discussed in prior alignment.
- The top navigation should appear progressively with the hero sequence.
- The motion asset should support local hosting and a static fallback.

### Deferred Work

- Produce final wing animation asset.
- Decide final route: Lottie/dotLottie, SVG+GSAP, Rive, transparent WebM/MP4, or other.
- Provide source assets: school emblem vector, three wing layers, final-frame lockup, approved colors, licensing/usage confirmation.
- Integrate final motion into the React homepage.

### Current Rule

Do not continue implementing the wing animation now. Reserve the hero video/motion slot and continue with homepage layout, navigation, scroll interaction, visual system, and content-section structure.

### Current Homepage Direction

2026-05-23: Product manager chose to prioritize strong cinematic scroll narrative from the first homepage redesign pass. This does not reopen the wing animation implementation. It only means the homepage will reserve a full-screen motion/video slot and build the surrounding navigation and scroll narrative first.

### Reopen Trigger

Reopen this debt only when the product manager provides reference motion and/or source assets, or explicitly asks to resume the wing animation implementation.
