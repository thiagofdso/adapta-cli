<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles:
  - [PRINCIPLE_1_NAME] -> I. Documentation-First Development
  - [PRINCIPLE_2_NAME] -> II. Architecture Decisions Must Be Recorded
  - [PRINCIPLE_3_NAME] -> III. Test-First Delivery
  - [PRINCIPLE_4_NAME] -> IV. Integration and Operational Validation
  - [PRINCIPLE_5_NAME] -> V. Simplicity, Consistency, and Learning
- Added sections:
  - Additional Constraints
  - Development Workflow
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ updated /mnt/c/whatsweb/adapta-cli/.specify/templates/plan-template.md
  - ✅ updated /mnt/c/whatsweb/adapta-cli/.specify/templates/spec-template.md
  - ✅ updated /mnt/c/whatsweb/adapta-cli/.specify/templates/tasks-template.md
  - ⚠ pending /mnt/c/whatsweb/adapta-cli/.specify/templates/commands/*.md (directory not present)
  - ✅ updated /mnt/c/whatsweb/adapta-cli/AGENTS.md
- Follow-up TODOs:
  - None
-->

# adapta-cli Constitution

## Core Principles

### I. Documentation-First Development

Every meaningful change MUST be grounded in the required project documentation in
`docs/`. Before starting work, contributors MUST consult `docs/features.md` to
understand functional context and `docs/arquitetura.md` to understand system fit.
When changing existing code, contributors MUST consult `docs/code-map.md`; when
touching data or integrations, they MUST consult `docs/modelo-dados.md` and
`docs/integracoes.md` respectively.

The repository MUST maintain, at minimum, the following documentation structure:
`docs/code-map.md`, `docs/arquitetura.md`, `docs/adr/`, `docs/features.md`,
`docs/modelo-dados.md`, `docs/integracoes.md`, `docs/licoes-aprendidas.md`, and
`docs/guia-uso-documentacao.md`.

Rationale: work done without current documentation increases drift, slows onboarding,
and causes avoidable regressions.

### II. Architecture Decisions Must Be Recorded

Any decision that impacts architecture, introduces a trade-off, or is likely to be
questioned later MUST be captured as an ADR in `docs/adr/`. Contributors MUST read
existing ADRs before making similar decisions and MUST not override prior decisions
implicitly.

When architecture changes materially, `docs/arquitetura.md` MUST be updated in the
same change set. New integrations or major integration contract changes MUST also be
reflected in `docs/integracoes.md`.

Rationale: explicit decision records prevent repeated debate, undocumented divergence,
and costly rediscovery of past trade-offs.

### III. Documentation-First and Test-First Delivery

Before creating tests or implementation, contributors MUST document the intended
change at both business and technical levels. This means updating or creating the
relevant items in `docs/features.md`, `docs/code-map.md`, `docs/arquitetura.md`,
`docs/modelo-dados.md`, `docs/integracoes.md`, and `docs/adr/` when applicable.

After the necessary documentation is in place, TDD is mandatory for implementation
work in this repository. Unit tests MUST be written before implementation and MUST
fail before production code is added. The expected cycle is Documentation -> Red ->
Green -> Refactor.

Integration tests MUST be added after the relevant unit suite is green and MUST cover
real command behavior, packaging flow, or external interactions that matter to the
feature. No implementation is complete until its required automated tests pass.

Rationale: documenting first keeps business and technical intent explicit, while
test-first work provides fast local feedback and reduces regressions in user-facing
flows.

### IV. Integration and Operational Validation

Features that affect external services, authentication, installation, or operational
flows MUST include explicit validation of those interactions. This includes command
execution, external authentication, installation scripts, `Makefile` shortcuts, and
cleanup behavior for remote resources.

Operational defaults MUST remain intentional and documented. If a feature changes
runtime behavior such as logging, installation, environment loading, or cleanup, the
feature docs and quickstart guidance MUST be updated in the same delivery.

Rationale: CLI tools fail most visibly at boundaries with users and external systems,
so those boundaries require deliberate validation and documentation.

### V. Simplicity, Consistency, and Learning

Contributors MUST prefer the smallest correct solution and MUST not introduce layers,
patterns, or abstractions without a concrete need. Existing repository conventions
for structure, naming, and interfaces MUST be followed unless an ADR explicitly
changes them.

Every relevant mistake, incident, or time-consuming debugging discovery MUST be
recorded in `docs/licoes-aprendidas.md`. Documented mistakes MUST NOT be repeated;
contributors are expected to consult that file before making risky changes.

Rationale: simplicity keeps the codebase maintainable, and explicit lessons prevent
the team from paying for the same error multiple times.

## Additional Constraints

- Contributors MUST update impacted documentation in `docs/` in the same change set
  as the code.
- Contributors MUST NOT code "in the dark" without first consulting the required
  documentation for the task type described in `docs/guia-uso-documentacao.md`.
- Features, integrations, data changes, and architecture changes MUST be reflected in
  the corresponding mandatory documents before the work is considered complete.
- If an error or incident is fixed, updating `docs/licoes-aprendidas.md` is mandatory.

## Development Workflow

- Before starting any task, read `docs/features.md` and `docs/arquitetura.md`.
- Before editing existing code, read `docs/code-map.md`.
- Before changing data shape or persistence behavior, read `docs/modelo-dados.md`.
- Before changing or adding external dependencies, read `docs/integracoes.md`.
- Before making architectural decisions, read `docs/adr/` and
  `docs/licoes-aprendidas.md`.
- Before writing tests, update the affected business and technical documentation.
- During implementation, keep the affected documents in sync with code and tests.
- After debugging a meaningful issue or incident, append a new lesson entry to
  `docs/licoes-aprendidas.md` with problem, cause, solution, what not to do, and what
  to do instead.

## Governance

This constitution supersedes informal local practice for this repository. Every plan,
specification, task list, code review, and implementation change MUST verify
compliance with these principles.

Amendments require: (1) explicit update to this file, (2) synchronization of affected
templates or guidance files, (3) a semantic version update, and (4) a short rationale
captured in the Sync Impact Report at the top of this file.

Versioning policy:
- MAJOR: remove or redefine a principle in a backward-incompatible way.
- MINOR: add a new principle, mandatory section, or materially expand governance.
- PATCH: clarify wording, fix ambiguity, or make non-semantic editorial improvements.

Compliance review expectations:
- Plans MUST include constitution and documentation impact checks.
- Tasks MUST include documentation work before tests and implementation when features
  change system behavior.
- Implementations MUST not be marked complete while required docs remain outdated.

**Version**: 1.0.0 | **Ratified**: 2026-04-12 | **Last Amended**: 2026-04-12
