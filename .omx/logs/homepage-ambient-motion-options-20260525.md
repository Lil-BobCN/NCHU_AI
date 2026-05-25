# Homepage Ambient Motion Options

Date: 2026-05-25
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`
Status: review-ready prototype options

## User Request

The highlighted homepage buttons, chips, signal cards, and HUD panels need extra polish after the entrance animation finishes. The effect should feel like a persistent high-end dark technology interface, not a one-time movement.

## References Considered

- Uiverse: dark animated/glow button patterns.
- 21st.dev community components: glowing, shimmer, and animated button component direction.
- MotionSites: dark cinematic motion atmosphere and subtle interface lighting.
- UI/UX Pro Max guidance: continuous decorative animation should be restrained, should respect reduced-motion preference, and should avoid layout shift.
- GSAP guidance: preserve existing timeline sequencing; use transform/opacity and pseudo-elements for continuous effects.

## Implemented Review Options

### A Breathing

Soft Aero breathing light. Applied to eyebrow capsule, process chips, CTA buttons, signal cards, and selected HUD surfaces.

- Motion: gentle vertical micro-float plus soft aura pulse.
- Strength: most suitable default for production because it feels polished and does not compete with reading.
- Risk: may be too restrained if the desired direction is more aggressive sci-fi.

### B Radar

Radar edge sweep. Applied as moving light sweeps across buttons, chips, cards, visual frame, system card, and HUD panel.

- Motion: periodic edge scan / panel scan.
- Strength: best match for aviation/HUD language.
- Risk: if overused, it can read as a scanning gimmick; should remain slow and low-opacity.

### C Flicker

Signal flicker. Applied as brief intermittent signal noise across interactive surfaces and HUD panels.

- Motion: short stepped shimmer/flicker bursts.
- Strength: most futuristic and high-energy.
- Risk: highest distraction risk; best used selectively rather than everywhere.

## Prototype Controls

The review toolbar now includes:

- `A Breathing`
- `B Radar`
- `C Flicker`

The active style is stored on `body[data-ambient-style]`. Ambient motion starts only after the active hero finishes its entrance animation and receives `.is-ambient-ready`.

## Verification

Playwright browser check completed against:
`http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`

Evidence:

- No console errors on desktop.
- No console errors on mobile.
- Desktop width: `scrollWidth=1440`, `clientWidth=1440`, no horizontal overflow.
- Mobile width: `scrollWidth=390`, `clientWidth=390`, no horizontal overflow.
- Option A active animations: `ambient-micro-float`, `ambient-aura`.
- Option B active animations: `ambient-edge-sweep`, `ambient-panel-sweep`.
- Option C active animations: `ambient-signal-flicker`.

Screenshots:

- `output/playwright/homepage-ambient-a.png`
- `output/playwright/homepage-ambient-b.png`
- `output/playwright/homepage-ambient-c.png`
- `output/playwright/homepage-ambient-mobile.png`

## Recommendation

Use A as the base style and borrow B only for the primary CTA or visual/HUD frame if the page needs a stronger aviation signal. Avoid using C globally; keep it as an accent for rare system-status moments.
