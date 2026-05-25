# awesome-design-md Project Configuration Validation

## Mission

Configure `VoltAgent/awesome-design-md` as a project-level design reference for the NCHU AI Counselor repository and explain how to use it without confusing it with the `impeccable` skill.

## Source Evidence

- Upstream repository: https://github.com/VoltAgent/awesome-design-md
- Upstream purpose: curated `DESIGN.md` files that can be copied into a project root for AI agents to read.
- License observed from repository metadata: MIT.

## Local Configuration

The project now has:

- `PRODUCT.md`: product, audience, tone, design priorities, and anti-references.
- `DESIGN.md`: project-level design entry point that references `VoltAgent/awesome-design-md` as an optional external design reference library.
- `docs/design/awesome-design-md.md`: source, selection guide, manual usage examples, optional vendoring path, update procedure, and rollback steps.
- `README.md`: short pointer to the project design context.

## Validation Evidence

The `impeccable` skill context loader was run from the repository root:

```powershell
node .agents\skills\impeccable\scripts\load-context.mjs
```

Observed result:

- `hasProduct: true`
- `productPath: PRODUCT.md`
- `hasDesign: true`
- `designPath: DESIGN.md`
- `contextDir: C:\Users\liuqi\Desktop\agentproject`

This proves the project-level context files are discoverable by `impeccable`. The design configuration is still useful independently of `impeccable`, because `awesome-design-md` is a `DESIGN.md` reference library rather than a skill.

## Usage Rule

Use `PRODUCT.md` and `DESIGN.md` for every design/frontend task. When a specific visual reference is desired, name the upstream reference explicitly, for example:

```text
Use PRODUCT.md and DESIGN.md. For this page, adapt the Linear reference from awesome-design-md, but keep the NCHU AI Counselor product tone and Chinese-first labels.
```

## Conclusion

The configuration is complete and locally validated. `impeccable` is a skill that can consume the files; `awesome-design-md` is the design-reference source configured through `DESIGN.md`.

