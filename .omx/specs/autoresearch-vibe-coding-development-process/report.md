# Autoresearch Report: Vibe Coding Development Process

Date: 2026-05-25
Status: accepted
Output artifact: `Development process.md`

## 1. Research Summary

The recommended process is a specification-first, approval-gated, evidence-driven human-AI development loop:

```text
idea / document / feedback
-> context intake
-> deep clarification
-> research and option comparison
-> SDAR / approval package
-> product structure and interaction prototype
-> architecture / API / data contract
-> small task node implementation
-> verification
-> acceptance log and retrospective
```

This matches the user's uploaded architecture-learning plan: the user's role moves from "code requester" to "requirements architect, process guide, and quality reviewer", while AI becomes the implementation/research/verification accelerator.

## 2. Local Evidence

- `Vibe+Coding架构师成长学习计划.docx` emphasizes context engineering, PRD/user stories, framework selection, architecture decisions, development specifications, and testing/delivery.
- `.omx/specs/autoresearch-final-development-workflow/report.md` already records the approved process: clarify, research, approve, prototype, split tasks, implement, verify.
- `.omx/decisions/SDAR-0001` to `SDAR-0008` show the project's actual approval-gated decisions: backend AI/RAG boundary, frontend stack, IA/route map, visual direction, page structure, data contract, homepage motion, and real-model student Chatbox.
- `.omx/logs/phase-03-real-model-student-chatbox.md` shows the current small-node execution pattern: approval package -> backend stream proxy -> isolated frontend page -> verification.

## 3. Similar Process References

- GitHub Copilot Vibe Coding: agentic coding should start with research/planning, then implementation, then user verification in a browser.
- GitHub Copilot best practices: AI helps with code, tests, debugging, and explanation, but does not replace human expertise; generated code must be checked.
- Atlassian Product Discovery: product discovery should validate customer needs and ideas before building, and connect discovery with delivery.
- NIST SSDF SP 800-218: secure software practices should be integrated into the SDLC, not bolted on after development.
- OWASP SAMM: security maturity should be measured and improved continuously.
- DORA metrics: delivery health should balance throughput and instability, not just speed.
- C4 model: architecture should be communicated through context, container, component, and code views as needed.

## 4. Recommended Rules

1. Do not start implementation from vague intent.
2. When multiple viable choices exist, present options, tradeoffs, recommendation, risks, and rollback to the product manager.
3. Use `$deep-interview` when intent, non-goals, success criteria, or decision boundaries are unclear.
4. Use `$autoresearch` when external precedent, technical choice, component choice, UX pattern, model/provider, or security practice affects the decision.
5. Use SDAR documents for decisions that affect architecture, data contracts, UI/product expression, dependencies, real data, SSO, deployment, or model providers.
6. Implement in small task nodes that are independently testable and reversible.
7. Verification must produce evidence: tests, lint/typecheck/build, smoke checks, screenshots, or review artifacts.
8. Every completed node must leave an acceptance/log trail and known residual risks.

## 5. Sources

Local:

- `C:/Users/liuqi/WPSDrive/565982054/WPS云盘/Vibe+Coding架构师成长学习计划.docx`
- `.omx/specs/autoresearch-final-development-workflow/report.md`
- `.omx/decisions/SDAR-0001-backend-ai-rag-orchestration.md`
- `.omx/decisions/SDAR-0002-frontend-stack.md`
- `.omx/decisions/SDAR-0003-frontend-ia-route-map.md`
- `.omx/decisions/SDAR-0004-frontend-visual-direction-design-tokens.md`
- `.omx/decisions/SDAR-0005-frontend-page-structure-interaction-flow.md`
- `.omx/decisions/SDAR-0006-product-data-contract-boundary.md`
- `.omx/decisions/SDAR-0007-homepage-cinematic-hero-scroll-narrative.md`
- `.omx/decisions/SDAR-0008-real-model-student-chatbox.md`
- `.omx/logs/phase-03-real-model-student-chatbox.md`

External:

- GitHub Docs: Vibe coding with GitHub Copilot, https://docs.github.com/copilot/tutorials/vibe-coding
- GitHub Docs: Best practices for using GitHub Copilot, https://docs.github.com/en/enterprise-cloud@latest/copilot/using-github-copilot/best-practices-for-using-github-copilot
- GitHub Docs: Review AI-generated code, https://docs.github.com/en/copilot/tutorials/review-ai-generated-code
- Atlassian: Product Discovery, https://www.atlassian.com/agile/product-management/discovery
- NIST SP 800-218 SSDF, https://csrc.nist.gov/pubs/sp/800/218/final
- OWASP SAMM, https://owaspsamm.org/model/
- DORA metrics, https://dora.dev/guides/dora-metrics/
- C4 model, https://c4model.com/
