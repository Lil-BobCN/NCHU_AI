# Context Snapshot: Theme Switch Alignment

Task statement: Fix the visible misalignment in the theme switch on
`.omx/prototypes/homepage-dark-hud-variants.html`.

Desired outcome: The Uiverse-inspired switch replaces the old Light/Dark text
control without visual offset. In both light and dark states, the icon is
centered inside the circular knob and the existing page colors remain unchanged:
light uses the blue theme variables, dark uses the brown theme variables.

Known facts/evidence:
- The affected file is `.omx/prototypes/homepage-dark-hud-variants.html`.
- The user provided a screenshot showing the dark-state moon icon shifted left
  relative to the orange knob.
- The current switch moves both the knob pseudo-element and `.theme-switch__icon`
  with `translateX(...)`.
- The dark-state moon shape additionally sets the first icon part to `left: -3px`,
  causing a visible off-center result.

Constraints:
- Surgical change only.
- Do not change the broader page layout, theme palette, or React application.
- Keep the existing `body[data-theme]` and `localStorage` theme behavior.
- Use `$karpathy-guidelines` and `$ralph` expectations: small scoped edit,
  explicit verification, and completion evidence.

Unknowns/open questions:
- No ambiguity requiring user input; the screenshot identifies the visual defect.

Likely codebase touchpoints:
- `.omx/prototypes/homepage-dark-hud-variants.html` CSS for `.theme-switch`.
- Existing 5188 static server for preview.
