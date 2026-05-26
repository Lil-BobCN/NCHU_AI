# Chatbox Typewriter Placeholder

- Task statement: Replace the current static student chatbox placeholder with an in-input, left-to-right typed prompt animation matching the user's reference image.
- Desired outcome: The chat composer shows a grey placeholder-like sentence that types one character at a time inside the text box, hides when the user focuses or types, and does not interfere with real input.
- Known facts/evidence:
  - The active IDE file path is `frontend/src/components/ui/text-scramble.tsx`, but the file did not exist in the current worktree.
  - The real chat composer is in `frontend/src/StudentChatboxPage.tsx`.
  - The composer CSS is in `frontend/src/App.css`.
  - `frontend/package.json` already includes `gsap` and `@gsap/react`.
- Constraints:
  - Use GSAP as the main animation library.
  - Follow Karpathy guidelines: small, surgical, verifiable changes.
  - Do not revert unrelated dirty worktree changes.
  - Keep the UI consistent with the existing Ant Design chat composer.
- Unknowns/open questions:
  - Whether the text should loop forever or only run once. Current implementation will choose a subtle looping prompt because the user requested a placeholder-style affordance.
- Likely codebase touchpoints:
  - `frontend/src/components/ui/text-scramble.tsx`
  - `frontend/src/StudentChatboxPage.tsx`
  - `frontend/src/App.css`
