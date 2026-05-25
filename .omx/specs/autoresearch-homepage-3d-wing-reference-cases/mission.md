# Autoresearch Mission: Homepage 3D Wing Reference Cases

Date: 2026-05-22
Status: active

## Mission

Find reviewable homepage / hero / motion references that help the product manager verify whether Codex understands the intended NCHU AI homepage direction.

## Product Context

Desired homepage direction:
- Ant Design X-like full-page AI product hero rhythm.
- Left side: product capabilities / AI counselor core emerges through layered motion or structured product copy.
- Right side: large 3D or high-quality 2.5D floating object based on NCHU emblem center wing/aircraft symbol.
- Motion: component parts fly in from left / lower-left, assemble into the final emblem-like wing form, then the whole object gently floats.
- Final symbol should keep the three overlapping wing/aircraft layout, nose pointing upper-right, no circular badge container.

## Constraints

- User is in mainland China network environment; prioritize references likely accessible from China or mirrored/Chinese docs/examples.
- Do not implement or change frontend code in this research task.
- Do not assume the current demo quality is acceptable.
- Separate concrete references from inference.

## Expected Output

Create `report.md` with:
- Candidate references grouped by category.
- Link, accessibility note, what to inspect, match to our target, mismatch/risk.
- Recommendation tier: high / medium / low.
- 3-5 preferred reference directions for product-manager review.
- A translation layer: terms the product manager can use to describe frontend motion/style requirements.

## Validation

The result is complete when `result.json` records architect_review.verdict = approved and output_artifact_path points to the report.
