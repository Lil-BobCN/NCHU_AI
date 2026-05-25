# Autoresearch Mission: Ant Design X Hero Motion Inspection

Date: 2026-05-23
Status: active

## Mission

Inspect Ant Design X homepage as a live animated page, not a static screenshot, and determine what type of animation the right-side robot/hero visual uses.

## Questions

- Does the hero use video, canvas/WebGL/Three.js/Spline, Lottie/Rive, or layered image/SVG/CSS/JS animation?
- What visible motion exists in the right-side robot visual and surrounding hero layers?
- Which implementation approach is closest for the NCHU wing hero?
- What evidence supports the answer?

## Constraints

- Research only.
- Do not edit production frontend files.
- Use real-browser inspection where possible.
- Separate observed facts from inference.

## Expected Output

Create `report.md` with observed evidence, screenshots/artifact paths, classification, implementation implications, and recommendation for the NCHU wing hero.

## Validation

Complete when `result.json` includes `architect_review.verdict = "approved"` and points to the report.
