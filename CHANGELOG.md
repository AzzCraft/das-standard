# Changelog

This project follows **Semantic Versioning** for the published standard.

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
