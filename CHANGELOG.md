# Changelog

All notable changes to the **Docs as Software (DAS) Standard** will be documented in this file.

This project follows a pragmatic versioning approach:

- **MAJOR**: breaking changes to MUST-level requirements or templates that require migration.
- **MINOR**: additive changes (new sections, new appendices, new optional templates).
- **PATCH**: clarifications, typo fixes, non-normative examples.

---

## v1.4.0 — 2026-04-06

### Added

- Explicit **conformance profile** and **interaction model** declarations for documents adopted under v1.4.0, including support for headless and operator-facing systems.
- Governed document families, a machine-readable standard manifest, template catalog, chapter/clause indexes, and a stable standards-ID registry.
- A community registry, conformance-report contract, compatibility fixtures, release snapshots, and version-closure checks.
- Appendix M (document-family governance and minimal templates) and Appendix N (repository roles, tooling placement, and execution matrix).

### Compatibility and migration

- Existing documents that conformed to v1.3.x may continue to use the historical L1 and standard_ui defaults during the v1 compatibility period. Verification tools MAY report these legacy defaults as migration warnings.
- Documents newly created or adopted under v1.4.0 MUST state those declarations explicitly. Existing adopters SHOULD materialize the fields before adopting v2.0.0, when omission may become a verification failure.

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

<!-- DAS-EDITION-1.5-CHANGELOG -->

## v1.5.0-beta.1 — unpublished content candidate, 2026-10-06

Normative additions cover approved applicability, precise exchange boundaries,
current authorization, independent isolated verification, immutable candidates,
evidence-bound integration/completion, HTTP/UI/sealed evaluation and release
lifecycle. Original obligations, stable IDs, conditions and historical fixtures
remain preserved against the independent 1.4 baseline. Chapter 13 is generated
from the edition author; the module and leaf catalogs remain separate metadata.

This is a development content edition, not a published beta or a compatibility
approval. Catalog 3.0.0 contains complete mappings for 1,745 legacy leaves and 978
edition leaves across all 21 edition sections, with 518 carriers overall.
The independent original baseline and explicitly pinned supplementary sources
retain leaf or repeated-source mappings. Information duties retain activation/profile
and actual-surface conditions; recommendations and example cells are not
strengthened. Carrier coverage does not establish compatibility, installed
qualification or final compatibility approval.
Versioned reference contracts and consumers are shipped; complete tool scenarios,
installed deployment qualification and publication are unfinished. All 136
product acceptance cases retain their denominator and remain not_run.

The final SemVer/obligation compatibility decision must precede publication.
Readable historical formats do not confer current protected authority.

The existing content snapshot generator can package its verified members as a
deterministic flat ZIP, independently of companion repositories. This runtime
payload is distinct from the source archive and from final release evidence.
