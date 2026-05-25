# Deep Interview Spec: Vibe Coding Development Process

Date: 2026-05-25
Profile: standard
Context type: brownfield documentation/process work
Final ambiguity: 0.14
Threshold: 0.20

## 1. Intent

The user wants a durable, professional development process that explains how the product manager and AI coding agent collaborate from vague idea to verified software delivery. The process must reflect the user's current project, the uploaded Vibe Coding architecture learning plan, and similar mature software engineering practices.

## 2. Desired Outcome

Create `Development process.md` at the repository root. The document should be understandable to a product manager and actionable for Codex/OMX agents.

## 3. In Scope

- Summarize the current project workflow.
- Define human-AI collaboration roles.
- Integrate the uploaded learning plan's core ideas: context engineering, spec-driven development, architecture thinking, AI orchestration, and quality gates.
- Use `$autoresearch` style evidence gathering for similar processes.
- Use `$deep-interview` style clarification to make intent, non-goals, decision boundaries, and acceptance criteria explicit.
- Define artifacts, approval gates, stop rules, implementation workflow, verification workflow, and retrospectives.

## 4. Out of Scope / Non-goals

- Do not change application code.
- Do not redesign the AI Counselor product.
- Do not replace existing SDAR decisions.
- Do not introduce a new toolchain, dependency, or workflow runtime.
- Do not claim this process is final for all future projects without review; it is a living process baseline.

## 5. Decision Boundaries

Codex may decide:

- The document structure.
- Which local project artifacts are relevant evidence.
- Which external engineering references are useful.
- How to map OMX workflows to development stages.
- Reasonable wording for the first version.

Codex must escalate to the product manager before:

- Changing approved product/technical decisions.
- Removing approval gates.
- Adding new dependencies, providers, real data, production deployment, SSO, or RAG/vector implementation.
- Treating the process as approved policy after this draft without product-manager review.

## 6. Acceptance Criteria

- `Development process.md` exists at the repository root.
- It contains a clear end-to-end workflow from idea intake to acceptance/retro.
- It explains "you are product manager / AI is architect-executor-verifier" collaboration.
- It includes when to use `$deep-interview`, `$autoresearch`, `$ralplan`, `$ralph`, `$team`, `$visual-verdict`, and review/QA modes.
- It includes frontend, backend, AI/RAG/model-provider, data-contract, and verification gates.
- It includes templates or checklists for future task nodes.
- It includes local and external references.

## 7. Evidence vs Inference

Evidence:

- The uploaded DOCX emphasizes requirement clarification, PRD/user stories, technical selection, architecture decisions, development specifications, testing/delivery, context engineering, spec-driven development, MVA, ADR/C4, and AI orchestration.
- Existing SDAR files demonstrate approval-gated product/technical decisions.
- Existing logs demonstrate small-node implementation and verification evidence.

Inference:

- The most appropriate durable process is a specification-first and approval-gated workflow because it matches both the uploaded learning plan and this project's current practice.

## 8. Pressure Pass

Earlier project practice could be summarized as "AI writes code after product feedback", but that is too shallow. The more accurate model is:

```text
human product intent + AI research/planning/execution + explicit approval gates + verification evidence
```

This prevents vibe coding from becoming unbounded code generation.

## 9. Handoff

Proceed to write `Development process.md` directly. No application implementation is part of this handoff.
