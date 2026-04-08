# Changelog

All notable changes to the **Docs as Software (DAS) Standard** will be documented in this file.

This project follows a pragmatic versioning approach:

- **MAJOR**: breaking changes to MUST-level requirements or templates that require migration.
- **MINOR**: additive changes (new sections, new appendices, new optional templates).
- **PATCH**: clarifications, typo fixes, non-normative examples.

---

## v1.4.6 — 2026-04-06

### Added

- Formalized the **repo-canonical release bundle** by shipping:
  - `VERSION`,
  - root `scripts/verify`,
  - `.github/workflows/verify.yml`,
  - `verify_registry.json`,
  - and `release_snapshot_manifest.json`.
- Added a machine-readable **suite lock** model:
  - `suite_lock.schema.json`,
  - `suite_lock.example.json`,
  - and a required `suiteLockRef` in `suite_version_closure.schema.json`.
- Added governed **verify execution artifacts**:
  - `verify_registry.schema.json` / example,
  - `verify_report.schema.json` / example,
  - with explicit semantics for per-gate cadence, enforcement class, `failureOnNoResults`, and `not_run`.
- Added governed **release snapshot** artifacts:
  - `release_snapshot_manifest.schema.json` / example,
  - plus a committed `release_snapshot_manifest.json` for the release bundle.
- Added machine-readable governance coverage for:
  - repo roles,
  - tool classes,
  - tool placement targets,
  - verify gate kinds,
  - suite module states,
  - release snapshot kinds,
  - and verify-report outcomes.
- Added **Appendix N** for repo-role taxonomy, tool placement, and execution-lane rules.

### Updated

- Expanded `standard_manifest.json` with `requiredSubsections` support so tooling can check finer-grained Master Doc expectations such as `Document Control -> Doc readiness gate`.
- Added root-level compatibility aliases `interactionProfiles` and `gateCadences` that mirror `enums.interactionProfiles` and `enums.gateCadences`, while keeping `gateCadenceDefinitions` as the richer canonical definition surface.
- Expanded `local_extension_manifest.schema.json` so extensions can target the new suite/tooling registries (`repoRoles`, `toolClasses`, `toolPlacementTargets`, `verifyGateKinds`, `moduleStates`, `releaseSnapshotKinds`).
- Expanded `tooling_lock.schema.json` so governed local mirrors and copies can carry snapshot provenance (`standardSnapshotRef`, mirror purpose, local-modification rules).
- Reworked **Appendix L** to cover suite lock, verify registry/report, release snapshots, and mirror provenance.
- Updated `requiredArtifacts`, `normativeArtifactRefs`, and `supportingArtifactRefs` so the release bundle is machine-readable end to end.

## v1.4.5 — 2026-04-05

### Added

- Added governed subordinate-doc template coverage for:
  - a standalone minimal **PRD template**,
  - a standalone minimal **Runbook template**,
  - and a worker/service-aware **module-doc template** with the conditional interaction-profile line.
- Added a machine-readable **template catalog** (`template_catalog.json` + schema) so factories and scaffolds can discover the shipped templates without scraping Markdown.
- Added a machine-readable **Determinism** enum binding for module docs so package/library governance can verify more than section presence.

### Updated

- Brought the shipped official templates into conformance with the standard they instantiate:
  - Appendix C Master Doc template now includes the canonical governed metadata fields required for `master_doc`.
  - Appendix D UI Spec template now includes the canonical governed metadata fields required for `ui_spec`.
- Tightened **suite version closure** by removing legacy bare-string refs from the governed schema; closure refs are now structured-only.
- Normalized **tooling-lock** ref shape to the same structured form used by suite closure (`kind + uri + pinType + pinValue + floating=false`) and strengthened `suiteVersionClosureRef` to a typed pinned ref.
- Strengthened the **local extension manifest** by:
  - requiring an explicit `extensionPoint`,
  - allowing `upstreamingTrigger` **or** `reviewDate`,
  - and retaining `mapsToCoreDocType` / `satisfiesCoreRequirement` rules for doc-type aliases.
- Removed the undefined `ui_spec_pointer_only` token from conditional rules and moved the pointer-doc restriction back into governed prose plus linked-doc requirements.
- Tightened `standard_manifest.schema.json` so governed releases must carry the expected normative and supporting artifact refs.

## v1.4.4 — 2026-04-05

### Added

- Shipped the full externalized appendix set, companion addenda, context pack, and example schema artifacts to close the previously incomplete release bundle.

### Updated

- Added explicit release-package completeness language to the specification.

## v1.4.3 — 2026-04-05

### Added

- Introduced `normative_addendum` into the governed doc-family model.
- Added `mapsToCoreDocType` for repo-local doc-type aliases.

### Updated

- Strengthened package, module, and headless-surface governance.

## v1.4.2 — 2026-04-05

### Added

- Added machine-readable conditional requirements for L2 Context Packs, UI Spec vs. headless note, and worker/service module interaction profiles.
- Added `standard_manifest.schema.json` and broadened doc-family governance coverage.

## v1.4.1 — 2026-04-05

### Updated

- Tightened `headless` semantics, template metadata, and schema coverage for tooling locks and suite closure.

## v1.4.0 — 2026-04-05

### Added

- Introduced the v1.4 line with headless-profile formalization, standard manifest, suite-level version closure, package/library doc governance, and gate cadence taxonomy.

---

## v1.3.0 — 2026-02-07

### Added

- Formalized **verify modes**: default fast mode (review-loop), and a full mode for nightly/pre-release gates (§10.1–§10.3).
- Added **tooling reproducibility** requirements for `verify` (§10.5) and a concrete **Tooling Standard** (Appendix L).
- Added a standardized **break-glass protocol** for Sev1/Sev2 incidents (Governance addendum §6.3).
- Expanded **supply chain controls** (deployment addendum §6.3) with dependency pinning, SBOM, scanning policy, and signing guidance.

### Updated

- Clarified that repos MAY provide `./scripts/verify-fast` / `./scripts/verify-full` wrappers, while keeping `./scripts/verify` as the canonical entrypoint.
- Strengthened guidance on avoiding floating tool/image tags and capturing pinned tool versions in verify output.

---

## v1.2.0 — 2026-01-29

### Added

- **Doc set support + token-cost controls**
  - Added the **Doc Set / Context Pack** definitions in §2.2.
  - Added §9.4 describing how to split Master Docs into modular sub-docs while preserving a single canonical entrypoint.

- **Doc drift / inconsistency handling**
  - Added §9.5 with a required protocol for resolving **code ↔ Master Doc** mismatches, including waivers and L2 automation expectations.

- **Multi-party / multi-company governance**
  - Added §9.6 summarizing minimum governance requirements and pointing to the Governance addendum.
  - Added **DAS Governance & Collaboration Addendum**: `DAS_GOVERNANCE_COLLABORATION.md`.

- **Deployment + environment coverage**
    - Added **DAS Deployment & Environment Addendum (DAS-Deploy)**: `DAS_DEPLOYMENT_ADDENDUM.md`.

### Updated

- Updated **Appendix C (Project Master Doc Template)** to include:
  - §4.4 **Environments & deployment pipeline**.
  - §4.5 **External dependencies & vendor integrations**.

- Clarified §2.1 precedence rules for **linked addenda and template files**.

---

## v1.1.0 — 2026-01-24

Minor release focused on clarity, internal consistency, and drift-prevention ergonomics.

Highlights:
- Expanded the definition of the **Contract Hub** to explicitly include **semantics** and a machine-readable **API registry** (recommended: `contracts/api/`), with clearer SSOT guidance for OpenAPI vs schema-first approaches.
- Strengthened **conformance profile** guidance by moving the requirement into the Master Doc header (Document Control) and requiring explicit deferrals/ownership/revisit triggers when selecting `L0`.
- Improved the **Project Master Doc** template: added doc lineage fields (Supersedes/Superseded by/Migration mapping), expanded the API contracts table (Canonical ref/Auth/Status codes), and added a multi-worker implementation protocol to reduce parallel-change drift.
- Added stronger execution/traceability mechanics in the **AI Execution Plan** (task Evidence column + status vocabulary + rules).
- Clarified **storage/migrations** expectations (DB engine/version, migration policy; DB schema treated as a persisted contract surface).
- Updated examples and layouts (recommended `contracts/` repo structure, clarified repo-local `contracts/` folders are not the SSOT hub, and fixed minor reference/naming inconsistencies).

## v1.0.0 — 2026-01-20

First public release of the DAS: Docs as Software Standard.

Notes:
- Only the public SemVer tags in this repository are normative for the open-source standard.
