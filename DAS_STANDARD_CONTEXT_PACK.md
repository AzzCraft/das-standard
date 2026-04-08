# DAS Standard Context Pack (v1.4.6)

## Document Control
- Doc ID: DAS-STANDARD-CONTEXT-PACK
- Owner: DAS Maintainers
- Status: active
- Governing standard: SPECIFICATION.md
- Last updated: 2026-04-06
- Scope: Read-optimized quick reference for humans and AI agents working from the DAS v1.4.6 release bundle.
- Parent Master Doc: SPECIFICATION.md

## 1. What DAS is (in one paragraph)

DAS is a unified engineering methodology for AI-enabled products. It treats docs like code (versioned, reviewed, verified) and treats anything crossing a boundary (repo, service, storage, or release artifact) as a governed contract surface with schema + semantics + fixtures + executable checks. In v1.4.6, the standard itself also ships as a repo-canonical release bundle with machine-readable manifests, verification metadata, and release snapshots.

## 2. Glossary

- **Compatibility Mode**: mixed-version reality is observable; expand/contract is required for governed surfaces.
- **Refactor Mode**: safe only when atomic cutover can be proven and enforced.
- **Contract surface**: any externally observed or persisted interface that requires schema + semantics + fixtures + checks.
- **Context Pack**: a token-budgeted, read-optimized slice of the governed doc set for fast onboarding and execution.
- **Headless interaction profile**: a governed interaction mode where operator, API, job, packet, and runtime surfaces replace a screen inventory.
- **Suite-level version closure**: machine-readable pinning of standard, factory, verify runtime, and related suite components.
- **Release snapshot**: the machine-readable digest inventory for a governed release bundle.

## 3. Invariants / minimum non-negotiables

- **MUST:** Declare exactly one conformance profile (`L0|L1|L2`) and one interaction profile in the canonical Master Doc.
- **MUST:** Maintain a canonical, versioned Master Doc with contract inventory, traceability, `verify` commands, and an execution plan.
- **MUST:** Treat cross-boundary and persisted interfaces as Compatibility Mode unless atomic cutover can be proven and enforced.
- **MUST:** For each governed contract surface, provide schema + semantics + fixtures + executable checks.
- **MUST:** Provide exactly one canonical `verify` entrypoint per repo.
- **MUST:** Keep machine-readable release artifacts aligned with the prose standard and shipped templates.
- **MUST:** Declare local extensions explicitly rather than silently widening core enums or requirements.
- **MUST:** Resolve doc drift through doc updates, code fixes, or explicit ADR/RFC decisions.

## 4. Boundary thinking you should not get wrong

- **Repo boundary** is not the same thing as a **runtime boundary**.
- Split repos to reduce change scope; do not split runtime services unless there is a concrete operational reason.
- Default to monorepo + SDMM or a hybrid model with a contract hub; add runtime services only when justified.
- Headless systems still need governed interaction documentation even when there is no traditional UI spec.

## 5. Machine-readable release surface

The v1.4.6 release bundle adds governed machine-readable artifacts at the repo root:

- `standard_manifest.json` + schema define canonical enums, required artifacts, and governed doc metadata.
- `suite_version_closure.*` and `suite_lock.*` pin multi-repo and multi-tooling relationships.
- `verify_registry.*` and `verify_report.*` define governed gate semantics and machine-readable verify output.
- `release_snapshot_manifest.*` captures artifact digests for the release bundle itself.
- `template_catalog.*` exposes the official shipped templates without Markdown scraping.

These root JSON/schema/example files are part of the governed release surface, not optional supporting clutter.

## 6. Verify

A release or repo adopting DAS should expect verification to cover at least:

- version marker + manifest consistency,
- schema/example validation for shipped machine-readable artifacts,
- release-bundle completeness against `requiredArtifacts`,
- internal link integrity for the spec, appendices, and companion docs,
- and repo-local docs/meta checks where a governed doc set is present.

## 7. Deployment and environments (DAS-Deploy)

For real products (especially L1/L2), adopt the deployment companion guidance:

- maintain an Environment Matrix with data-class rules and rollback ownership,
- document a Deployment Pipeline with artifact identity, promotion, migrations, and runbooks,
- track external vendors and AI providers in a Dependency Registry,
- and keep supply-chain controls, release readiness, and rollback constraints explicit.

See: `DAS_DEPLOYMENT_ADDENDUM.md`.

## 8. Multi-team / multi-company governance (DAS-Gov)

- Every governed doc needs an Owner; cross-boundary decisions need a Decision Owner.
- Approval rules should live in tooling (`CODEOWNERS`, branch protection, or equivalent), not only prose.
- Use RFCs or ADRs for contentious or high-impact changes.
- Break-glass use must be explicit, audited, and paid back quickly.

See: `DAS_GOVERNANCE_COLLABORATION.md`.

## 9. Current tasks / focus

- Keep the specification, appendices, companion docs, and machine-readable artifacts closed as one governed release bundle.
- Preserve machine-readable compatibility for tooling locks, suite version closure, verify registry/report, release snapshots, and template discovery.
- Keep official templates aligned with the metadata and section rules declared by `standard_manifest.json`.
- Keep the human-readable companion docs substantive enough to match the guarantees and references made by the main spec and changelog.
