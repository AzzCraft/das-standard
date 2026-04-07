# Changelog

All notable changes to the **Docs as Software (DAS) Standard** will be documented in this file.

This project follows a pragmatic versioning approach:

- **MAJOR**: breaking changes to MUST-level requirements or templates that require migration.
- **MINOR**: additive changes (new sections, new appendices, new optional templates).
- **PATCH**: clarifications, typo fixes, non-normative examples.

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
