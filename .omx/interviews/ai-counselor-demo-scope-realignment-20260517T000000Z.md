# Deep Interview: AI Counselor Demo Scope Realignment

Date: 2026-05-17
Profile: standard
Final ambiguity: 13%
Status: complete

## Outcome

The interview clarified the next development direction for the AI counselor system Demo.

The Demo should become a formal-product-like independent website that the school official site can link to. It should include homepage, login page, student side, counselor side, and admin side. Desktop and mobile should be developed together.

## Key Decisions

- Server target: Alibaba Cloud ECS 4 vCPU / 16 GiB is accepted as the recommended future deployment configuration.
- Frontend entry: not embedded into the school official website. The official site links to our independent main website.
- Login: real unified SSO is future work. Demo uses the current local/demo login approach.
- Demo story: student, counselor, and admin flows should be connected into one complete product experience.
- Data: synthetic/simulated data is acceptable, but it must be clearly labeled as demo/simulated data.
- System path: simulated data must still pass through real application flows, APIs, persistence, and knowledge/Q&A paths where implemented.
- Product surface: the Demo must look like a formal standalone product, not rough API screens.
- Mobile: mobile is in scope and should be developed together with desktop.

## Non-Goals For This Demo

- Do not require real school SSO integration.
- Do not use real student private data.
- Do not promise production-grade security audit.
- Do not make ICP filing, formal domain, or HTTPS a Demo success prerequisite.
- Do not require modifying the real school official website.

## Decision Boundaries

Codex may decide directly:

- Page information architecture.
- UI style and visual system.
- Desktop/mobile layout tradeoffs.
- Synthetic demo data content.
- Demo story/script.
- Concrete technical implementation details.
- Incremental implementation order.

Codex should ask before changing:

- Product positioning.
- Real school resource assumptions.
- Real SSO integration.
- Production security or public launch boundaries.
- Any requirement that depends on school IT, school website permissions, or real student data.

## Transcript Summary

1. User confirmed the server discussion can be deferred, and accepted 4 vCPU / 16 GiB as the recommended server configuration.
2. User changed the frontend direction from embedded school-site assistant to an independent main website linked from the official website.
3. User confirmed SSO will be built later; the current Demo should use the existing login direction.
4. User confirmed the Demo should connect student, counselor, and admin flows.
5. User initially wanted real data. After discussion, user accepted synthetic demo data as long as it is clearly labeled.
6. User required a formal-product-like independent homepage, login page, student side, counselor side, and admin side.
7. User rejected excluding mobile; mobile must be developed together with desktop.
8. User asked for the feature plan to be structured as: feature first, development approach, and reason.
9. User authorized Codex to make detailed implementation decisions under this structure, with escalation only for positioning, real school resources, SSO, and launch/security boundaries.

