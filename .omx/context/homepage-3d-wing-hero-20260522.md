# Homepage 3D Wing Hero Context

Date: 2026-05-22
Status: deep-interview context snapshot

## Task Statement

Clarify the intended homepage hero redesign for NCHU AI before implementation.

## Desired Outcome

Create a homepage direction inspired by Ant Design X's dark AI product hero:

- Left side: product core emerges through layered motion, text, and subtle interface hints.
- Right side: a large, full-hero visual area rather than a narrow component card.
- Right side visual should be based on the complete aircraft/wing symbol from the Nanchang Hangkong University emblem, not three unrelated paper-plane objects.
- The final fixed state should reproduce the emblem's aircraft/wing geometry as closely as possible: overlapping wing blocks, nose pointing upper-right, and the original spatial relationship.

## Known Facts

- Homepage should remain a formal product site, not a role-selection page.
- Login leads to role-specific authentication/selection.
- The project visual tone should be modern, technological, credible, and not traditional-school-admin-like.
- Product manager provided Ant Design X screenshot as a visual reference and NCHU emblem as source inspiration.
- No code implementation is approved in this interview round.

## Key Unknown

The main unresolved design choice is how the aircraft/wing symbol should fly into its final emblem-matching state.

## Current Inference

The best likely direction is a full-width Ant Design X-like hero: left-side product capability emergence and right-side emblem-accurate aircraft/wing symbol. Productized abstraction is still allowed through material, light, shadow, depth, and motion, but the final symbol geometry should remain emblem-accurate.

## Deep Interview Transcript

### Round 1

Question:
Should the right-side 3D wing visual use strong emblem fidelity, productized abstraction, or fully abstract tech styling?

Product manager answer:
B. Productized abstraction.

Interpretation:
Preserve the three-wing geometry and the lower-left to upper-right flight narrative from the NCHU emblem, but modernize material, lighting, scale, and motion so it feels like an AI product hero rather than a literal logo display.

### Round 2

Question:
Should the left-side product core expression be brand-slogan style, product-capability emergence, or process narrative?

Product manager answer:
B. Product-capability emergence.

Interpretation:
The left side should include a strong headline, but should not be only a slogan. It should progressively reveal several core product capabilities, such as student consultation, teacher/counselor case assistance, knowledge-resource operations, and traceable Demo boundaries.

### Round 3

Question:
Should the first version of the right-side wing visual be a high-quality 2.5D prototype, true 3D, or static/video-like visual?

Product manager answer:
A. High-quality 2.5D prototype.

Additional requirement:
Before formal implementation, create a shared-consensus webpage demo so the product manager can inspect layout and verify that Codex understands the intended effect.

Interpretation:
The next artifact should be a lightweight prototype under `.omx/prototypes/`, not a production React change. It should demonstrate:

- left-side product capability emergence,
- right-side three-wing visual inspired by the NCHU emblem,
- lower-left to upper-right motion narrative,
- dark modern AI-product atmosphere similar in spirit to Ant Design X,
- no locked final visual style and no new frontend dependency.

### Round 4

Product manager correction:
The prior prototype misunderstood the visual in two ways:

- Layout was too narrow and component-like. It should fill the page more like Ant Design X's hero.
- The aircraft/wing visual should not be three separate paper-plane-like shapes. It should reproduce the complete emblem aircraft/wing symbol shown in the cropped emblem image.

Question:
How accurate should the final fixed aircraft/wing symbol be?

Product manager answer:
A. Geometrically as close as possible to the emblem symbol.

Interpretation:
The final fixed state should preserve the original emblem aircraft/wing geometry, overlap, and upper-right nose direction. Productization may add material, lighting, shadow, glow, and 2.5D depth, but should not noticeably change the silhouette or relative layout.

### Round 5

Question:
Should the flight animation be separate parts flying in, the complete symbol flying in, or parts flying in and then the whole symbol gently floating?

Product manager answer:
C. Parts fly in first, then the whole symbol gently floats.

Interpretation:
The animation should have two stages:

1. Assembly stage: the emblem aircraft/wing symbol's component blocks fly in from the left/left-lower side in sequence and lock into the emblem-accurate final geometry.
2. Idle stage: after assembly, the complete aircraft/wing symbol behaves as one unified 2.5D object with subtle floating/breathing motion.

### Round 6

Question:
After the symbol reaches its fixed state, should the right-side visual include only the wing symbol itself, an abstract circular light ring, or a badge-like circular container?

Product manager answer:
A. Keep only the wing symbol itself.

Interpretation:
The final hero should not include a full emblem circle or badge container. It may use productized background atmosphere such as glow, depth, soft trails, faint grids, blurred UI panels, or orbit-like abstract accents, but the main fixed object is the aircraft/wing symbol itself.

## Current Consensus

- Layout should follow Ant Design X's full-page hero rhythm: not a narrow card or small component stage.
- Left side uses product-capability emergence rather than pure slogan or process flow.
- Right side uses the NCHU emblem aircraft/wing symbol.
- Final symbol geometry should be as close as possible to the emblem crop.
- Motion: component blocks fly in sequentially, assemble into the emblem-accurate symbol, then the complete symbol gently floats as one object.
- No circular emblem container in the hero; only the wing symbol itself is retained.
- First implementation/prototype path remains high-quality 2.5D, not true 3D.
