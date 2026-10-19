# The Docs as Software (DAS) Standard
> **The Unified Engineering Methodology for AI-Enabled Products**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Version: v1.5.0-beta.1](https://img.shields.io/badge/Version-v1.5.0-beta.1-blue.svg)](CHANGELOG.md)

**Name:** Docs as Software (DAS) Standard (中文：**文码合一标准**)
**Maintained by:** AzzCraft Inc. (重庆艾之舟科技有限公司)
**Copyright:** © 2026 AzzCraft Inc. (重庆艾之舟科技有限公司)
**Last updated:** 2026-10-06

---

## Introduction

This document defines the **engineering methodology** used to build AI-enabled products safely and efficiently. It serves as a **canonical reference** for:

* **System topology:** Explicit rules for monorepo vs. multi-repo splitting to avoid runtime complexity.
* **Contract governance:** Strict schemas, semantics, and fixtures for all cross-boundary artifacts.
* **SDMM (Single-Deploy Modular Engineering):** Patterns for keeping AI changes bounded and reviewable.
* **Canonical contracts:** Standardized envelope shapes to prevent "adapter-by-accident" drift.
* **Verification:** One-command `verify` gates and AI-friendly task decomposition.
* **DDD/BDD alignment:** Integration of Bounded Contexts (DDD) and Executable Scenarios (BDD) into the engineering lifecycle.

This standard is designed to be forked and adopted by organizations seeking rigorous AI engineering practices.


## Normative language

This standard uses **BCP 14** requirement keywords (RFC 2119 + RFC 8174).

- The primary normative keywords used in this document are: **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**.
- If synonymous terms appear (e.g., **REQUIRED**, **SHALL**, **SHALL NOT**, **RECOMMENDED**, **OPTIONAL**), they MUST be interpreted as the corresponding BCP 14 keyword; authors SHOULD prefer the primary keywords above for clarity.
- Lowercase forms (“must”, “should”, etc.) are non-normative unless explicitly marked.

Interpretation guidance:

- **MUST / MUST NOT**: required for correctness, safe evolution, security, or drift prevention.
- **SHOULD / SHOULD NOT**: strongly recommended; deviation requires explicit justification and compensating controls.
- **MAY**: optional.

## 1. What this standard optimizes for

AI-assisted development changes the dominant failure modes. This methodology optimizes for:

1. **AI-safe change scoping**
Modular boundaries that allow an AI agent (or a human) to modify one unit without implicit coupling across the system.

1. **Contract-driven integration**
Anything that crosses a repo boundary, service boundary, or persists beyond a deploy is treated as a contract surface: schema + semantics + fixtures + executable checks.

1. **Replayability and debuggability**
If a run produces an output, there is a bounded, reviewable artifact (RunManifest + PipelineResult + JobEnvelope) that explains why.

1. **Budgeted computation**
Algorithm/model workloads enforce budgets in-loop. Budget exhaustion is explicit and machine-readable.

1. **Compatibility-aware evolution**
Mixed-version reality is assumed (rolling deploys, caches, queues, dashboards). Expand/dual-support/contract is the default for externally observed or persisted surfaces.

1. **One-command verification**
A single `verify` entrypoint exists per repo, and a system-level `verify` exists in the integration harness.

1. **Ubiquitous language & bounded contexts (DDD)**
Domain terms, ownership boundaries, and invariants are explicit and traceable to contracts and code.

1. **Executable behavior specifications (BDD)**
Critical workflows are specified as Given/When/Then scenarios and enforced via automated checks so documentation stays “alive”.

## 2. Scope, precedence, and core definitions

### 2.1 Precedence and conflict resolution

1. **Security / compliance policy** takes precedence over all engineering methodology.
1. This unified standard is the governing rule set across repos.
1. Appendices are included for completeness and deep-dive reference. If any appendix conflicts with the Main Body, the Main Body takes precedence. **Examples are non-normative**; when in doubt, implement the definitions in §4 and treat inconsistent examples as bugs to be fixed.
1. **Linked addenda and template files** referenced by this standard (even if stored as separate `.md` files) are considered **normative appendices** unless explicitly labeled as *informative*. If any linked addendum conflicts with the Main Body, the Main Body takes precedence.
1. Repo-local docs MAY add stricter rules, but MUST NOT relax any **MUST/MUST NOT** requirements in this standard.


### 2.2 Core definitions

- **Repo boundary**: a source-control boundary (separate repo or package with an independent release lifecycle).
- **Runtime boundary**: a deployed process/service boundary (introduces network hops and distributed failure modes).
- **Contract surface**: any interface that is externally observed and/or persisted and read later. Contract surfaces are **Compatibility Mode by default**.
- **Compatibility Mode**: producer and consumer do **not** ship atomically; mixed versions are observable. Requires explicit compatibility windows and expand/contract evolution.
- **Refactor Mode**: a boundary behaves “atomically” from the perspective of the environment observing it (either within a single deployable artifact, or via a strictly enforced atomic cutover where no requests observe mixed versions). No persisted/external observation crosses the boundary.
  - **Clarification:** If you cannot *prove and enforce* “no mixed versions,” treat the boundary as **Compatibility Mode**.

- **Contract hub**: the canonical home for cross-boundary contracts shared across repos: schemas, **semantics** (invariants/defaults/redaction), fixtures, stable identifiers, and executable checks. For HTTP surfaces, this includes (or references) a machine-readable endpoint inventory (e.g., `contracts/api/`).
- **SDMM / Single-Deploy Modular Engineering**: build-time modularization inside a repo while shipping as one deployable artifact per app/service/library.
- **Doc set (Master Doc set)**: a versioned set of documents that collectively satisfy the Master Doc requirements (§9.1), consisting of a single **canonical index entrypoint** (the Master Doc) plus zero or more linked sub-docs.
- **Context Pack**: a token-budgeted, read-optimized slice of the doc set intended for fast onboarding and AI/human execution (typically includes scope, invariants, contract inventory, `verify` commands, and current tasks).
- **Doc drift**: any inconsistency between documentation (Master Doc / UI Spec / addenda) and the actual behavior, contracts, fixtures, or verification gates of the codebase.

### 2.3 Conformance profiles and cost controls (scalable adoption)

This standard is intended to work for both small, fast-moving teams and large, multi-team organizations. To avoid accidental over-engineering (or accidental under-governance), every project MUST declare a **conformance profile** in the canonical Master Doc header (Document Control):

- **L0 - Prototype**: exploration or pre-product; prioritize speed while still protecting users and data.
- **L1 - Product**: a shipped product with regular iteration; balance speed with reliability.
- **L2 - Platform/Enterprise**: multi-team, high-trust, or regulated; maximize stability, compatibility, and auditability.

Rules:

- **MUST:** Declare exactly one profile (`L0|L1|L2`) in the canonical Master Doc.
- **MUST:** Documents newly created or adopted under v1.4.0 MUST state the declaration explicitly in merged documentation.
- **SHOULD:** Legacy documents that conformed to v1.3.x SHOULD materialize an explicit profile before adopting v2.0.0. During the v1 compatibility period, tooling MAY report a missing legacy declaration as a migration warning and use the historical `L1` value; v2.0.0 MAY make omission a verify failure.
- **MUST:** Regardless of profile, externally observed or persisted surfaces (public APIs, stored artifacts, identifiers) MUST use **Compatibility Mode** and MUST be fixture-backed.
- **SHOULD:** Teams SHOULD evolve profiles over time (typical path: `L0 → L1 → L2`).
- **SHOULD:** Tooling SHOULD source the allowed enum from `standard_manifest.json` rather than hard-coding local copies.

Terminology note: this document uses **P0/P1/P2** in checklists to mean priority/severity; conformance profiles are **L0/L1/L2**.

Practical profile guidance (non-exhaustive):

| Area | L0 - Prototype | L1 - Product | L2 - Platform/Enterprise |
| --- | --- | --- | --- |
| Docs as Software (DAS) | Master Doc required but MAY be short; keep traceability limited to critical flows. | Master Doc required; traceability for critical flows is expected. | Master Doc required; traceability SHOULD be automated and comprehensive for all critical surfaces. |
| Compatibility discipline | Compatibility for persisted/external only; internal boundaries MAY use Refactor Mode if you can deploy atomically. | Compatibility default for cross-boundary; Refactor Mode allowed for truly internal, atomically deployed surfaces. | Compatibility is the default; refactor-mode exceptions are rare and must be documented. |
| Design tokens | Tokens REQUIRED only for shared UI kit; prototypes MAY use “magic values” in bounded areas. | Tokens REQUIRED for shared surfaces; use token incubation for rapid iteration. | Strict token enforcement across the codebase (no “magic values” outside token sources). |
| Verify gates | PR gates MUST be fast; heavy E2E/visual gates MAY run nightly or pre-release. | Balanced PR gates + nightly full gates. | Comprehensive gates; visual + E2E are expected as merge gates for critical repos. |
| Determinism / replay | Replay harness SHOULD exist for Tier 0/1, but can be non-blocking early; prefer invariant-based assertions. | Replay harness required for Tier 0/1 critical paths; keep fixtures small and maintainable. | Replay and evaluation gating are strict and audited. |

Profiles are cost controls, not loopholes.

- **MUST (when selecting `L0`):** If the project selects conformance profile `L0`, it MUST document what is intentionally deferred, who owns that debt, and when/why it will be revisited (date or explicit trigger).

### 2.4 Interaction profiles (HFVI extension)

Conformance profiles (L0/L1/L2) control engineering cost and gate strictness. Some products also have materially different interaction risk: classic workflow UIs, **headless** services/workers, and high-fidelity visual interaction surfaces (canvas/WebGL/game-like UI). To keep these products implementable and testable, each project MUST additionally declare an interaction profile in its canonical Master Doc.

Interaction profiles:

- `standard_ui`: form/workflow-centric UI where Appendix D is typically sufficient.
- `headless`: no primary end-user screen inventory; the governed interaction surfaces are operator commands, APIs, jobs, packets, runtime surfaces, or machine-to-machine integrations.
- `hfvi_canvas_webgl_game`: high-fidelity visual interaction (canvas/WebGL/game-like interaction surfaces).

Rules:

- **MUST:** Declare exactly one interaction profile (`standard_ui|headless|hfvi_canvas_webgl_game`) in the canonical Master Doc.
- **MUST:** Documents newly created or adopted under v1.4.0 MUST state the declaration explicitly in merged documentation.
- **SHOULD:** Legacy documents that conformed to v1.3.x SHOULD materialize an explicit interaction profile before adopting v2.0.0. During the v1 compatibility period, tooling MAY report a missing legacy declaration as a migration warning and use the historical `standard_ui` value; v2.0.0 MAY make omission a verify failure.
- **MUST:** If `headless` is declared, the project MUST provide a **Headless Surface Note** (see Appendix M) or a local-extension-declared equivalent that maps back to core doc type `headless_surface_note` for machine checks.
- **MAY:** A repo MAY keep a thin `UI_SPEC = N/A` pointer doc for navigation or legacy compatibility, but that pointer doc MUST link to the governing Headless Surface Note (or extension-mapped equivalent) and is **not sufficient by itself**.
- **MUST:** The governing screenless-surface doc MUST identify the operator surface, CLI/API surfaces, job/runtime surfaces, packet/export surfaces, and why no screen inventory exists.
- **MUST:** If `standard_ui` or `hfvi_canvas_webgl_game` is declared, the project MUST maintain a UI Spec Appendix or a local-extension-declared equivalent that maps back to core doc type `ui_spec` for machine checks.
- **MUST:** If `hfvi_canvas_webgl_game` is declared, the project MUST adopt the HFVI requirements in §6.8 and Appendix K.
- **SHOULD:** Tooling SHOULD source the allowed enum from `standard_manifest.json` rather than hard-coding local copies.
- **SHOULD:** HFVI projects SHOULD treat interaction surfaces as contract surfaces for the purposes of fixtures, replayability, and verification gates.

### 2.5 Machine-readable standard manifest, repo-canonical release artifacts, and extension mechanism

Human-readable prose is not enough for suites, factories, verify runtimes, or released standard bundles. Each governed release of this standard MUST ship machine-readable artifacts that tools can consume without scraping Markdown, and the **standard repo/bundle itself** MUST be self-describing enough to be locked, mirrored, and verified.

Required artifacts for a governed **repo-canonical release** of the standard:

- `VERSION`
- `CHANGELOG.md`
- `SPECIFICATION.md`
- `scripts/verify`
- `.github/workflows/verify.yml`
- `standard_manifest.json`
- `standard_manifest.schema.json`
- `suite_version_closure.schema.json`
- `suite_lock.schema.json`
- `tooling_lock.schema.json`
- `local_extension_manifest.schema.json`
- `verify_registry.schema.json`
- `verify_report.schema.json`
- `release_snapshot_manifest.schema.json`
- `template_catalog.json`
- `template_catalog.schema.json`
- `verify_registry.json`
- `release_snapshot_manifest.json`

Release-package completeness rules:

- **MUST:** Every path listed in `requiredArtifacts` for a governed release MUST physically exist in the published release bundle at the declared relative path.
- **MUST:** Repo-canonical release bundles MUST ship an actual `release_snapshot_manifest.json` and an actual `verify_registry.json` for the standard repo/bundle itself.
- **MUST:** Internal links from `SPECIFICATION.md` to externalized appendices, companion addenda, examples, and machine-readable artifacts MUST resolve inside the release bundle; broken release-bundle links are a release failure.
- **SHOULD:** Release CI SHOULD run a package-completeness self-check that validates `requiredArtifacts`, `normativeArtifactRefs`, and `supportingArtifactRefs` against the actual bundle contents before publication.

`standard_manifest.json` MUST include, at minimum:

- `standardVersion`
- normative enums for:
  - conformance profiles,
  - interaction profiles,
  - document status values,
  - gate cadences,
  - gate enforcement classes,
  - doc-family roles used by the templates,
  - module kinds used by module docs,
  - addendum kinds used by governed release companions,
  - determinism values used by module docs,
  - repo roles,
  - tool classes,
  - tool placement targets,
  - verify gate kinds,
  - suite module states,
  - release snapshot kinds,
  - and verify-report outcomes,
- machine-readable **metadata-field -> enum bindings** for canonical governed metadata fields (for example `Status -> docStatuses`, `Interaction profile -> interactionProfiles`, `Addendum kind -> addendumKinds`) so verify runtimes do not need repo-local hard-coded mappings,
- machine-readable **section-value -> enum bindings** where a governed section uses normative enum values (for example `module_doc -> Determinism -> determinismValues`),
- required metadata fields by doc type,
- required sections and, where applicable, required **subsections** by doc type/profile,
- machine-readable **conditional requirements** when a rule depends on profile, interaction profile, or module kind (for example `L2` requiring a Context Pack, or `headless` requiring a Headless Surface Note),
- machine-readable cadence / enforcement definitions sufficient for suites, factories, and dashboards to display gate meaning without scraping prose,
- machine-readable definitions for repo roles, tool classes, tool placement targets, verify gate kinds, suite module states, and release snapshot kinds,
- references to appendix files and other normative machine-readable artifacts,
- tooling expectations required by Appendix L,
- any shipped **normative addenda** that are part of the governed release package,
- the machine-readable **template catalog** mapping core doc types to official shipped templates,
- and schema refs for `suite_lock`, `verify_registry`, `verify_report`, and `release_snapshot_manifest` when those mechanisms are part of the governed release.

Release manifests MAY additionally expose **supporting example artifact refs** separately from normative artifact refs so tools can discover shipped examples without misclassifying them as normative inputs.

Status metadata rules:

- **MUST:** The document status enum is normative: `draft | active | frozen | deprecated`.
- **MUST:** Docs that declare a status MUST use only the normative enum values from `standard_manifest.json`.
- **SHOULD:** Verify tooling SHOULD fail on unknown status values rather than silently normalizing them.

Machine-readable conditional rules MAY require not only the presence of metadata fields, but also specific **metadata values** when a doc type has a fixed semantic role (for example `Doc family role = canonical_entrypoint`, or `Interaction profile = headless` for a Headless Surface Note).

- **MUST:** If the release package uses governed companion docs of type `normative_addendum`, the machine-readable manifest/schema pair MUST require those entries explicitly rather than leaving them optional in schema validation.
- **MUST:** `Addendum kind` MUST be governed by a normative enum in the machine-readable manifest/schema pair rather than existing only as free-text template metadata.
- **MUST:** Repo-canonical standard bundles MUST declare a `VERSION` file, a self-verify command, and CI metadata in `requiredArtifacts`; a bundle that lacks those repo-canonical artifacts MUST NOT be presented as the canonical governed release.
- **SHOULD:** Suites and verify runtimes SHOULD consume metadata-field enum bindings from `standard_manifest.json` instead of inferring them from prose or hard-coded field-name heuristics.

Standard-release companion docs such as deployment/governance companions SHOULD be represented as governed doc type `normative_addendum` in the release manifest rather than sitting outside the machine-readable doc-family model.

Extension mechanism:

- **MAY:** Repos MAY define local extensions to profiles, doc families, gate packs, repo roles, tool classes, tool placement targets, verify gate kinds, release snapshot kinds, metadata fields, or other governed registries, but only through an explicit **local extension manifest** referenced from the project Master Doc.
- **MUST:** Extension identifiers MUST be namespaced (for example `x-...` or `org.example....`) so they cannot be mistaken for core DAS enums.
- **MUST:** Each extension MUST declare: `name`, `namespace`, `kind`, `extensionPoint`, `owner`, `scope`, and `compatibilityNote`.
- **MUST:** Each extension MUST also declare at least one review/normalization trigger: `upstreamingTrigger` **or** `reviewDate`.
- **MUST:** If an extension defines a repo-local **doc type** intended to satisfy a core DAS doc-type requirement, it MUST declare `mapsToCoreDocType` so tooling can treat the alias as satisfying the core requirement.
- **SHOULD:** Local extension manifests SHOULD validate against `local_extension_manifest.schema.json` shipped with this release of the standard.
- **MUST NOT:** Repos MUST NOT silently widen normative DAS enums in code or docs without declaring the extension in machine-readable form.


## 3. System topology and repo boundaries (monorepo vs multi-repo)

### 3.1 Critical distinction: repo boundaries vs runtime boundaries

A common failure mode is equating “more repos” with “more services.”

- **Repo split** is a development organization decision: it reduces change scope, clarifies ownership, and improves AI edit safety.
- **Service split** is a runtime architecture decision: it introduces network hops, operational complexity, and distributed failure modes.

**MUST:** Do not introduce a new runtime service solely to make code “smaller” or “AI-sized.” **SHOULD:** Prefer SDMM-style modularization inside a single runtime until operational requirements justify service splits.

### 3.2 Topology choices (choose the smallest topology that works)

#### Topology A - Monorepo with strict internal packages (SDMM)

Use when:

- one team owns most of the surface area,
- atomic refactors are practical,
- you want simplest integration and fastest iteration.

Risks:

- ownership and release coupling,
- insufficient discipline can devolve into “monolith with folders.”

#### Topology B - Multi-repo with a contract hub

Use when:

- teams have independent release cadences,
- different languages/toolchains dominate,
- platform/security boundaries require repo separation.

Non-negotiable requirement:

- a **contract hub** repo + compatibility-mode evolution discipline.

#### Topology C - Hybrid (common and recommended)

Typical for AI products:

- a dedicated contract hub,
- separate `algo` and `backend`,
- optional separate `frontend`,
- an `integration` repo for system-level verification.

### 3.3 Recommended multi-repo baseline (Topology B / Hybrid)

A typical system is organized as:

1. `contracts` - canonical contract hub (schemas, fixtures, identifiers, API registry, codegen config)
1. `backend` - system-of-record + orchestrator (preferred owner for long-running jobs)
1. `algo` - model/compute service or algorithm library
1. `frontend` - UI client (if applicable)
1. `integration` - docker-compose/dev env + end-to-end smoke tests + compatibility runners (high leverage)
1. `data-evals` - offline datasets and benchmark reports (no secrets / no raw PII; optionally a separate artifact store)

**MUST:** Treat all cross-repo boundaries as **Compatibility Mode** unless you can prove and enforce atomic cutover.

### 3.4 What each repo owns (normative)

#### Repo: `contracts` (Contract Hub)

Owns:

- canonical schemas (JSON Schema / Protobuf; OpenAPI fragments only when OpenAPI-first or stored as generated snapshots),
- contract semantics notes (field meaning, invariants, defaults, error mapping, redaction rules), preferably stored under `contracts/semantics/` (or embedded in schema descriptions with stable refs),
- machine-readable API registry / endpoint inventory (recommended): `contracts/api/` (HTTP/RPC surfaces),
- fixtures (known-good and known-bad),
- stable identifier sets (route IDs, job types, stage IDs, error codes, permission codes, feature flags),
- codegen configuration and generated clients (when applicable),
- executable checks (schema validation, contract tests, drift detection).

**MUST NOT:** contain business logic or runtime orchestration.

#### Repo: `frontend`

Owns:

- UI/UX and view state,
- client-side validation and user-visible mapping from error codes → UI states,
- generated API clients or thin wrappers.

**SHOULD:** Internally modularize using SDMM Frontend Track (§6).

#### Repo: `backend` (system-of-record + orchestrator)

Owns:

- stable public APIs for clients and integrations,
- canonical validation and canonical error mapping,
- long-running job orchestration for AI workloads,
- idempotency, retries, and cancellation policy.

**SHOULD:** Remain a modular monolith unless runtime splits are operationally justified.

#### Repo: `algo` (model/compute service)

Owns:

- core algorithm/pipeline execution,
- model inference, prompt pipelines, retrieval/tool calling (if applicable),
- strict validation/normalization of model outputs against schemas,
- run manifests and replay tooling (in collaboration with `integration`).

**SHOULD:** Internally modularize using SDMM Algorithm Track (§7).

#### Repo: `integration`

Owns:

- system-level `verify` (smoke tests, compatibility runners, replay runners),
- local dev environment composition,
- release-sequencing tests (old/new contract decode fixtures across repos).

#### Repo: `data-evals` (optional but high leverage)

Owns:

- evaluation datasets, rubrics, and benchmark harnesses,
- versioned dataset manifests,
- evaluation reports used for gating releases.

**MUST:** contain scrubbed/synthetic data only unless explicitly approved by compliance.

### 3.5 Contract hub requirements (non-negotiable for multi-repo)

If your system is multi-repo (Topology B/C) or hybrid, a canonical **contract hub** is not optional.

The contract hub MAY be implemented as:

- a dedicated `contracts` repo (common), or
- a versioned `contracts/` package published from a monorepo, or
- another versioned package boundary, as long as it is the **single source of truth** for cross-boundary schemas/IDs/fixtures.

Cost-control rules:

- **MUST:** In CI and production builds, consumers MUST depend on a **pinned** contract version (not `latest`).
- **SHOULD:** For local development, teams SHOULD support a **local override** (workspace/path dependency, git submodule, etc.) so contract changes can be developed without breaking developer flow.

**MUST:** The contract hub MUST treat contracts as **complete artifacts**, not “just schemas”. A contract is only complete when it has:

1. **Schema**: machine-validated structure (JSON Schema / Protobuf; OpenAPI components only when OpenAPI-first).
1. **Semantics**: field meaning, invariants, defaults, error conditions, redaction rules.
1. **Fixtures**: known-good and known-bad examples, including edge cases.
1. **Executable checks**: CI that validates schemas and fixtures, plus compatibility runners for versioned surfaces.

**SHOULD:** Contracts that are used across languages SHOULD have:

- generated types/clients (or at least strongly-typed adapters),
- a single canonical identifier set (error codes, stage IDs, job types).

#### Minimal contract hub layout (recommended)

> **SSOT note:** If multiple representations exist (e.g., OpenAPI + separate payload schemas), you MUST designate exactly one as the **authoring SSOT** and treat the others as generated artifacts with drift checks.

```
contracts/
  api/                    # (recommended) machine-readable endpoint inventory (method/path/auth/status codes)
  schemas/                # payload structures (JSON Schema / Protobuf / etc.)
    run_manifest.schema.json
    pipeline_result.schema.json
    job_envelope.schema.json
  semantics/              # non-schema semantics (invariants/defaults/error mapping/redaction); stable refs
    run_manifest.md
    pipeline_result.md
    job_envelope.md
  fixtures/               # golden samples (valid/invalid; optionally compat)
    run_manifest/
      valid/
      invalid/
    pipeline_result/
      valid/
      invalid/
  identifiers/            # (aka ids/) stable value domains (error codes, permission codes, job types, route IDs)
    error_codes.(json|ts)
    stage_ids.(json|ts)
    job_types.(json|ts)
  openapi/                # (optional) generated snapshots for publishing/SDKs (DO NOT EDIT by hand)
    public-api.yaml
  codegen/
    generators/
  scripts/
    verify
    compatibility_runner
  CHANGELOG.md
  README.md
```

**Semantics location rule:** Every cross-boundary schema or API surface MUST have a stable Semantics reference. Semantics MAY be encoded directly in schema constraints/`description` fields, but SHOULD also be linkable as a dedicated doc (e.g., `contracts/semantics/<contract_id>.md`) so Master Docs and tooling can reference it consistently.



### 3.6 Integration harness requirements (system truth source)

Multi-repo without an integration harness degenerates into “it compiles in my repo” drift.

**MUST:** Provide an `integration` repo (or an equivalent location) that can:

- stand up the minimal system locally (compose/k8s/devcontainer),
- run an end-to-end smoke flow across Frontend → Backend → Algorithm,
- run **compatibility-mode decoding tests** using fixtures from the contract hub,
- run replay tests for algorithm runs when external dependencies exist.

**SHOULD:** Treat the integration harness as the canonical place for:

- cross-repo release sequencing tests,
- “old consumer reads new producer” and “new consumer reads old producer” checks.

## 4. Canonical contracts and naming (cross-boundary + persisted)

### 4.1 Casing policy

#### C1 - Serialized contracts use `camelCase`

**MUST:** All serialized contracts that cross a repo boundary, service boundary, or are persisted MUST use `camelCase`.

Examples: `runId`, `jobId`, `stageId`, `sideEffectsMode`, `inputHash`, `manifestHash`.

#### C2 - Internal code conventions are separate

Internal implementation MAY use language idioms (e.g., `snake_case` in Python), but **serialization at boundaries** MUST conform to this canonical standard.

#### C3 - Protobuf / gRPC note (allowed)

- `.proto` field names SHOULD follow Protobuf style (`snake_case`).
- If a Protobuf surface is exposed via **JSON** (REST gateway, fixtures, logs, debug exports), the JSON field names **MUST** be `camelCase`.
  - Use the default Protobuf JSON mapping (which emits lowerCamelCase) or explicit options/mappings.
- This casing rule applies to **serialized payloads**, not to in-memory property names.

### 4.2 Contract surfaces and evolution modes

**MUST:** Treat the following as **Compatibility Mode** surfaces even inside a “single deploy” repo:

- API responses and error envelopes
- events/messages/stream frames
- persisted artifacts (files, cached results, queue payloads, run manifests)
- dashboards/metrics schemas relied upon operationally
- long-lived sessions (SSE/WS) spanning deploy boundaries

**MUST:** Any breaking change to a Compatibility Mode surface MUST use expand/dual-support/contract with an explicit compatibility window.

#### 4.2.1 Compatibility rules (tolerant readers, explicit defaults)

For Compatibility Mode surfaces:

- **MUST:** Readers MUST be tolerant of unknown fields (ignore what you do not understand).
- **MUST:** Writers MUST NOT remove or repurpose existing fields without a dual-support window.
- **MUST:** Defaults MUST be explicit and documented (do not rely on “missing means false” without stating it).
- **SHOULD:** Prefer additive fields over changing meaning of existing fields.
- **SHOULD:** When deprecating, add an explicit `deprecatedFields` note in schema docs and a removal date.

#### 4.2.2 Versioning guidance

- **SHOULD:** Include `schemaVersion` on persisted artifacts (RunManifest, PipelineResult, JobEnvelope, DatasetManifest, EvalReport).
- **MUST:** A breaking schema change MUST increment major version (SemVer) and MUST be guarded by compatibility runners.
- **MUST:** A compatibility window MUST be defined when producers and consumers do not ship atomically.

### 4.3 Canonical identifiers (stability requirements)

These identifiers MUST be treated as contract surfaces (do not rename without Compatibility Mode handling):

- `jobType`, `jobId`
- `runId`
- `profileId`
- `configId` / `configHash`
- `stageId`
- error `code` values
- diagnostic `codes[]`
- dataset IDs / metric IDs / score IDs used for gating
- prompt IDs / tool allowlist IDs (when applicable)

### 4.4 Canonical envelope shapes (normative)

This section defines the canonical JSON shapes used across repos. If you already have an equivalent envelope, you MUST provide a documented mapping and keep it lossless.

#### 4.4.1 ErrorEnvelope (cross-boundary, bounded)

```
{
  "code": "validation.failed",
  "kind": "invalidArgument|unauthorized|forbidden|notFound|conflict|rateLimited|timeout|unavailable|internal",
  "message": "Short, user-safe summary (no PII).",
  "retryable": false,
  "details": {},
  "correlation": { "requestId": "req_…", "traceId": "trace_…" }
}
```

Rules:

- **MUST:** `code` is stable and machine-readable.
- **MUST:** `message` is bounded and redaction-safe by default.
- **SHOULD:** `details` is shallow and bounded; avoid embedding large payloads.

#### 4.4.2 Diagnostics (bounded, structured, safe to log)

```
{
  "codes": ["ok"],
  "kv": { "modelId": "gpt-4.1", "profileId": "prod@4" },
  "counters": { "tokens": 812, "dbQueries": 3 },
  "notes": ["optional bounded strings"]
}
```

Rules:

- **MUST:** `codes` is an array (multiple reasons are common).
- **SHOULD:** `kv` values are scalars/short strings.
- **MUST:** diagnostics are redaction-safe by default.

#### 4.4.3 Budget (ledger-friendly; allocated/consumed/remaining)

Budgets MUST be explicit for algorithm execution and SHOULD be recorded in both manifests and job envelopes.

```
{
  "scope": "pipeline|stage:llm|tool:webSearch",
  "allocated": { "timeMs": 1500, "tokens": 2000, "externalCalls": 50 },
  "consumed": { "timeMs": 108, "tokens": 812, "externalCalls": 3 },
  "remaining": { "timeMs": 1392, "tokens": 1188, "externalCalls": 47 },
  "termination": { "code": "ok|tokens_exhausted|time_exhausted|external_calls_exhausted|cancelled" },
  "children": []
}
```

Rules:

- **MUST:** resource names are stable (`timeMs`, `tokens`, `externalCalls`, etc.).
- **MUST:** if budget exhaustion occurs, `termination.code` MUST be set to a stable value.
- **SHOULD:** hierarchical `children` budgets exist for non-trivial pipelines (pipeline → stage → tool/model).

#### 4.4.4 RunManifest (required for production algorithm outputs)

A RunManifest answers: **“Why did we produce this output?”** It is a persisted artifact and therefore **Compatibility Mode** by default.

Minimum required fields (normative):

- `schemaVersion` (SemVer recommended)
- `runId`
- `createdAt`
- `correlation.requestId` and/or `correlation.traceId` (when applicable)
- `pipeline.id`
- `algorithm.version` (git SHA/build version/container digest)
- `contracts` (contract pins: IDs → versions/hashes)
- `config.profileId` + (`config.configId` OR `config.configHash`) (or equivalent; MUST be immutable)
- `inputRef.rawInputId` AND at least one of: `inputRef.inputHash` or `inputRef.snapshotId`
- `sideEffectsMode` (**required**): `dryRun|sandbox|live`
- `budget` (at least pipeline-level allocated/consumed/remaining)
- `determinism.tier` (tier0|tier1|tier2) and any required determinism parameters (seed, concurrency, model pins)

Illustrative shape:

```
{
  "schemaVersion": "1.0.0",
  "runId": "2026-01-10T18:00:01Z/9b1d…",
  "createdAt": "2026-01-10T18:00:01Z",

  "correlation": { "requestId": "req_abc", "traceId": "trace_xyz" },

  "pipeline": { "id": "summarize.v2" },
  "algorithm": { "version": "git:abc123" },

  "contracts": {
    "run.manifest.v1": "1.0.0",
    "pipeline.result.v1": "1.0.0",
    "job.envelope.v1": "1.0.0"
  },

  "config": { "profileId": "prod@4", "configId": "cfg_01HZ…", "configHash": "sha256:…" },

  "inputRef": {
    "rawInputId": "s3://bucket/raw/01HZ…",
    "inputHash": "sha256:…",
    "snapshotId": "snap_01HZ…"
  },

  "sideEffectsMode": "dryRun",

  "determinism": {
    "tier": "tier1",
    "seed": 123456,
    "concurrency": { "workers": 4 }
  },

  "budget": {
    "scope": "pipeline",
    "allocated": { "timeMs": 1500, "tokens": 2000, "externalCalls": 50 },
    "consumed": { "timeMs": 108, "tokens": 812, "externalCalls": 3 },
    "remaining": { "timeMs": 1392, "tokens": 1188, "externalCalls": 47 },
    "termination": { "code": "ok" },
    "children": []
  },

  "stageSummaries": [
    { "stageId": "retrieve", "status": "ok", "timeMs": 31, "codes": ["ok"] },
    { "stageId": "llm", "status": "degraded", "timeMs": 77, "codes": ["tokens_exhausted"] }
  ],

  "diagnostics": { "codes": ["run.succeeded"] }
}
```

Notes (normative):

- **MUST NOT:** embed `manifestHash` inside the RunManifest payload. `manifestHash` is the content hash of the **persisted RunManifest artifact** and MUST live in referencing objects (e.g., `PipelineResult.manifestRef`, `JobEnvelope.runs[].manifestRef`) or in storage metadata.
- **SHOULD:** compute `manifestHash` over a canonical serialization of the stored RunManifest (stable key ordering + no insignificant whitespace) so independent services can verify integrity.

#### 4.4.5 PipelineResult (algorithm output envelope)

A PipelineResult is the canonical “algorithm response” object. It MUST be losslessly wrappable into a JobEnvelope.

```
{
  "schemaVersion": "1.0.0",
  "runId": "2026-01-10T18:00:01Z/9b1d…",
  "pipeline": { "id": "summarize.v2" },
  "status": "ok|degraded|error|cancelled",

  "output": {},
  "warnings": [],

  "stageSummaries": [
    { "stageId": "retrieve", "status": "ok", "timeMs": 31 },
    { "stageId": "llm", "status": "ok", "timeMs": 77 }
  ],

  "budget": { "scope": "pipeline", "allocated": {}, "consumed": {}, "remaining": {}, "termination": { "code": "ok" }, "children": [] },
  "diagnostics": { "codes": ["pipeline.succeeded"] },

  "manifestRef": { "runId": "2026-01-10T18:00:01Z/9b1d…", "manifestHash": "sha256:…" },

  "error": null
}
```

Rules:

- **MUST:** `runId` links to a RunManifest.
- **MUST:** `status` and `error` are consistent (error present when status is error/cancelled).
- **SHOULD:** `stageSummaries` are present for non-trivial pipelines.

#### 4.4.6 JobEnvelope (orchestrator-level; long-running jobs)

A JobEnvelope is the canonical state/reporting object for long-running AI jobs orchestrated by the Backend. It is the **system-of-record** for job lifecycle and the integration object where Backend and Algorithm artifacts meet.

##### Job vs Run mapping (normative)

- A **Job** is the orchestrator record (`jobId`, queueing, retries, cancellation, SLA).
- A **Run** is a single execution attempt of the algorithm pipeline (`runId`, RunManifest, PipelineResult).
- **MUST:** A JobEnvelope MUST represent **multiple runs** when retries/fallbacks occur (`runs[]`), even if the common case is 1:1.
- **SHOULD:** A JobEnvelope SHOULD expose overall `startedAt`/`finishedAt` as job-level timestamps (first attempt start; final attempt finish).

Illustrative shape:

```
{
  "schemaVersion": "1.0.0",
  "jobId": "job_123",
  "jobType": "document.summarize",
  "status": "succeeded",
  "createdAt": "2026-01-10T18:00:00Z",
  "updatedAt": "2026-01-10T18:00:02Z",
  "startedAt": "2026-01-10T18:00:01Z",
  "finishedAt": "2026-01-10T18:00:02Z",

  "profileId": "prod@4",
  "configId": "cfg_01HZ…",
  "configHash": "sha256:…",
  "attempt": { "count": 1, "max": 5 },

  "correlation": { "requestId": "req_abc", "traceId": "trace_xyz" },

  "sideEffectsMode": "dryRun",

  "inputRef": {
    "rawInputId": "raw_01HZ…",
    "inputHash": "sha256:…",
    "snapshotId": "snap_01HZ…"
  },

  "runs": [
    {
      "attempt": 1,
      "startedAt": "2026-01-10T18:00:01Z",
      "finishedAt": "2026-01-10T18:00:02Z",
      "manifestRef": { "runId": "2026-01-10T18:00:01Z/9b1d…", "manifestHash": "sha256:…" },
      "result": {
        "schemaVersion": "1.0.0",
        "runId": "2026-01-10T18:00:01Z/9b1d…",
        "pipeline": { "id": "summarize.v2" },
        "status": "ok",
        "output": {},
        "warnings": [],
        "stageSummaries": [
          { "stageId": "retrieve", "status": "ok", "timeMs": 31, "codes": [] },
          { "stageId": "llm", "status": "ok", "timeMs": 842, "codes": [] }
        ],
        "budget": {
          "scope": "pipeline",
          "allocated": { "timeMs": 1500, "tokens": 2000, "externalCalls": 50 },
          "consumed": { "timeMs": 873, "tokens": 812, "externalCalls": 3 },
          "remaining": { "timeMs": 627, "tokens": 1188, "externalCalls": 47 },
          "termination": { "code": "ok" },
          "children": []
        },
        "diagnostics": { "codes": ["pipeline.succeeded"] },
        "manifestRef": { "runId": "2026-01-10T18:00:01Z/9b1d…", "manifestHash": "sha256:…" },
        "error": null
      }
    }
  ],

  "diagnostics": { "codes": ["job.succeeded"] },
  "error": null
}
```

Rules:

- **MUST:** include `sideEffectsMode` so the orchestrator can request replay-safe runs.
- **MUST:** include `profileId` AND (`configId` OR `configHash`) so the execution configuration is reproducible.
- **MUST:** include `runs[].manifestRef` so results are explainable and auditable.
- **MUST:** if both `runs[].manifestRef` and `runs[].result.manifestRef` are present, they MUST be identical. Treat `runs[].manifestRef` as the canonical pointer; `runs[].result.manifestRef` exists because PipelineResult is portable outside the JobEnvelope.
- **MUST:** ignore unknown fields (“tolerant reader”) to enable additive evolution.

#### 4.4.7 DatasetManifest (evaluation inputs; pinned datasets)

Dataset manifests are immutable, versioned records used to pin evaluation inputs and enable reproducible scoring. They also capture the governance metadata needed to safely share and reuse datasets (provenance, license, and intended use).

```
{
  "schemaVersion": "1.0.0",
  "datasetId": "ds_summarization_core",
  "datasetVersion": "2026-01-10",
  "owner": "ml-platform",
  "pointOfContact": "slack:#ml-quality",

  "intendedUse": {
    "purpose": "CI gating for summarization",
    "restrictions": ["no-external-distribution"]
  },
  "provenance": {
    "source": "internal-labeling",
    "collectionMethod": "curated sample",
    "generatedAt": "2026-01-10",
    "generatedBy": "pipeline:dataset_build@9b1d4c7"
  },
  "license": {
    "terms": "internal",
    "restrictions": ["no-external-distribution"]
  },
  "sensitivity": {
    "pii": "none",
    "accessLevel": "restricted"
  },

  "schemaRef": "schemas/ds_summarization_core.schema.json",

  "splits": {
    "ci": { "count": 200 },
    "offline": { "count": 5000 }
  },

  "snapshotId": "registry://datasets/ds_summarization_core@2026-01-10",
  "contentHash": "sha256:…",
  "contentHashMethod": "sha256",

  "artifactRefs": {
    "raw": { "uri": "s3://datasets/ds_summarization_core/2026-01-10/raw.jsonl" },
    "normalized": { "uri": "s3://datasets/ds_summarization_core/2026-01-10/normalized.jsonl" }
  },

  "retention": { "windowDays": 90, "deletionOwner": "ml-platform" }
}
```

Rules:

- **MUST:** `intendedUse`, `provenance`, and `license` MUST be present.
- **MUST:** at least one of `snapshotId` or `contentHash` MUST be present.
- **MUST:** if `contentHash` is present, `contentHashMethod` MUST be present.
- **MUST:** once published, `datasetId + datasetVersion` is immutable.
- **MUST:** at least one entry in `artifactRefs` MUST be present.
- **SHOULD:** prefer content-addressing (`contentHash`) when feasible.
- **SHOULD:** `schemaRef` SHOULD point to a machine-checkable record schema (JSON Schema, Protobuf descriptor, etc.).
- **MAY:** include additional fields such as `storageUri` (convenience pointer) or `notes`; consumers MUST ignore unknown fields.

#### 4.4.8 EvalReport (bounded summary + pointers)

```
{
  "schemaVersion": "1.0.0",
  "evalId": "summarize.v2.ci",
  "runAt": "2026-01-10T18:05:00Z",
  "dataset": { "datasetId": "ds_summarization_core", "datasetVersion": "2026-01-10" },
  "thresholds": { "rougeL": 0.25 },
  "metrics": { "rougeL": 0.28, "p95LatencyMs": 900 },
  "status": "pass|fail",
  "artifacts": {
    "fullReportRef": "s3://…/evalReports/…",
    "samplesRef": "s3://…/evalSamples/…"
  },
  "diagnostics": { "codes": ["eval.passed"] }
}
```

#### 4.4.9 AnnotatedContent and CitationSet (AI answers with references)

Many AI-enabled products rely on retrieval (RAG) and must render **citations** in a way that is consistent across backend/algo/frontend. This section defines a **pragmatic** contract that is robust to:

- model variability (hallucinated or missing citation markers),
- partial/streaming outputs,
- and privacy constraints (snippets may contain sensitive text).

At a minimum, producers MUST provide a machine-checkable mapping from **rendered content** to **reference records**. The contract MAY be embedded inside `PipelineResult.output` or referenced by URL; the shape below is **conceptual**.

Recommended representation (marker-based; avoids offset bugs):

```
{
  "schemaVersion": "1.0.0",
  "format": "markdown|plaintext",
  "text": "…answer text… [[ref:R1]] …more… [[ref:R2]]",
  "markers": { "syntax": "[[ref:{refId}]]" },
  "references": [
    {
      "refId": "R1",
      "label": "[1]",
      "sourceUri": "s3://…|https://…|doc://…",
      "title": "…",
      "snippet": "…",
      "metadata": { "chunkId": "…", "publishedAt": "2026-01-10" }
    }
  ],
  "integrity": {
    "status": "ok|partial|invalid",
    "issues": ["missing_ref:R2", "untrusted_marker:[doc_3]"]
  }
}
```

Optional representation (offset-based; only when you truly need positional spans):

```
{
  "format": "markdown|plaintext",
  "text": "…answer text…",
  "offsetUnit": "utf16CodeUnit|unicodeCodePoint",
  "inlineRefs": [
    { "refId": "R1", "start": 120, "end": 123, "label": "[1]" }
  ],
  "references": [ { "refId": "R1", "label": "[1]", "sourceUri": "…", "title": "…", "snippet": "…" } ]
}
```

Rules:

- **MUST:** `references[].refId` values are unique within the payload.
- **MUST:** Every rendered reference marker (or `inlineRefs[].refId`) MUST exist in `references[]`.
- **MUST:** Producers MUST apply a **sanitization layer** before emitting citations to the UI. Raw LLM output MAY contain bogus markers; the system MUST either:
  - convert them into a valid `AnnotatedContent` payload (setting `integrity.status` accordingly), or
  - drop/strip citations and return `integrity.status = invalid` with user-safe messaging.
- **MUST:** Producers MUST NOT include sensitive content in `snippet` by default; apply redaction/sanitization.
- **MUST (when `start/end` is used):** `offsetUnit` MUST be explicitly set and treated as part of the contract. For web UIs, `utf16CodeUnit` is RECOMMENDED to match JavaScript string indexing; prefer marker-based rendering to avoid cross-language offset bugs.
- **MUST:** Consumers MUST degrade gracefully if refs are missing/malformed (render text; do not crash the UI).

If the UI supports reference interactions (hover preview, side panel, click-through), that behavior MUST be specified in the UI Spec Appendix (Appendix D) for any screen that renders citations.

#### 4.4.10 StreamFrame (SSE/WS incremental updates)

If an operation streams progress or partial outputs to the UI, the stream MUST be defined as a canonical contract (schema + semantics + fixtures + checks). The goal is to allow independent iteration across repos without breaking streaming UX.

Canonical frame shape (conceptual):

```
{
  "schemaVersion": "1.0.0",
  "streamId": "stream_01HZ…",
  "laneId": "main",
  "seq": 12,
  "eventId": "evt_01HZ…",
  "kind": "delta|progress|lane_start|lane_end|final|error",
  "timestamp": "2026-01-15T12:34:56Z",

  "delta": {
    "mode": "append|replace",
    "path": "output.answer.text",
    "text": "…partial text…"
  },

  "progress": {
    "phase": "retrieval|tool|generation|postprocess",
    "percent": 0.4,
    "message": "Retrieving 3 documents…"
  },

  "final": { "pipelineResultRef": "s3://…/pipelineResult.json" },

  "error": { "code": "…", "message": "…", "details": {}, "retryable": false }
}
```

Notes:

- `laneId` enables **parallel agent/tool activity** (multiple lanes per `streamId`). If a system is strictly linear, use `laneId = "main"` only.
- `path` uses a JSON-pointer-like convention into the final materialized payload (e.g., `PipelineResult.output.*`).

Rules:

- **MUST:** `seq` is monotonically increasing per (`streamId`, `laneId`). Clients use it for ordering and de-duplication.
- **MUST:** Streams MUST end in `final` or `error` (no silent hangs). Consumers MUST time out and surface recovery actions.
- **MUST:** Producers MUST set `kind` and MUST only include the matching payload field (`delta|progress|final|error`) for that frame.
- **MUST:** Clients MUST support `delta.mode = append` for streaming text surfaces.
- **SHOULD:** `delta.mode = replace` SHOULD be used sparingly (e.g., patching a single bounded field). If used, producers SHOULD ensure the UI can apply it without jitter (avoid frequent rewrites of large buffers).
- **SHOULD:** For compute-bound AI tasks, producers SHOULD emit `progress` frames when feasible. This is not required for correctness: UIs MUST still render a generic “Thinking/Working” state if progress is unavailable.

### 4.5 Design system contracts (tokens + components)

Design systems are cross-team, cross-repo integration surfaces. In AI-enabled products, **UI trust** is a primary quality attribute; accidental token drift or component regressions frequently cause user-facing inconsistency and undermine trust.

#### 4.5.1 Design tokens as contracts (required when using a shared design system)

- **MUST:** Design tokens (colors, spacing, typography, radii, shadows, motion) MUST be defined in a canonical, versioned contract surface:
  - either in the `contracts/` hub (recommended), or
  - in a dedicated `design-system` package that is consumed as a pinned dependency.
- **MUST:** Tokens MUST have a machine-readable schema (e.g., `tokens.schema.json`) and an explicit owner.
- **MUST:** Token changes MUST follow Compatibility Mode semantics:
  - **Breaking:** renaming/removing a token (consumers cannot read).
  - **Behavioral:** changing a token value in a way that materially changes appearance (requires explicit review and visual regression checks).
  - **Safe expand:** adding new tokens (non-breaking).
- **MUST:** Token names MUST be semantic and stable. Avoid “temp” tokens (e.g., `color-temp-1`). If temporary experimentation is needed, it MUST be done via a documented **incubator namespace** (e.g., `incubator.*`) with an owner and an expiry date.
- **MUST:** Frontend CI MUST forbid “magic” raw values where tokens exist (e.g., raw hex colors) **except** in the token source itself.
- **MAY (L0 prototypes):** “Magic values” MAY be used in clearly bounded prototype-only areas (e.g., `proto/` or feature-flagged experiments), but MUST NOT leak into shared UI kit components or shared surfaces consumed by multiple teams.

#### 4.5.2 Shared component contracts (recommended)

- **SHOULD:** Shared UI components SHOULD have stable identifiers (e.g., `COMP-###`) and documented props/events contracts (Storybook/docs).
- **MUST (when UI kit exists):** Every UI kit component state that is referenced by the UI Spec Appendix MUST:
  - exist as a Storybook story (or equivalent),
  - and be protected by visual regression snapshots in the frontend `verify` gate.
- **SHOULD:** Component contract changes should be treated like API changes: expand/contract, deprecations, and compatibility windows for major consumers.

## 5. SDMM core principles (Single-Deploy Modular Engineering)

SDMM (“Single-Deploy Modular Engineering”) is an architecture discipline for **one deployable** that is still split into **many independently understandable modules**. Legacy note: some earlier documents expanded SDMM as “Single-Deploy Modular Monorepo”; this unified standard uses “Engineering” to avoid implying a repo topology. It is the default pattern for:

- Frontend applications (one web app deploy, many feature modules).
- Backend services (one service deploy, many domain modules).
- Algorithm libraries/services (one pipeline deploy, many algorithm modules).

SDMM is not the only topology in this standard; see §3 for **multi-repo** systems. SDMM principles still apply *within* a repo even when the overall system is multi-repo.

### 5.1 SDMM goals

SDMM is designed to optimize for:

- **Local reasoning:** a developer can change one module without understanding the entire system.
- **Mechanical enforcement:** boundary rules are enforced by tools (linters), not memory.
- **Safe evolution:** clear rules for refactors vs compatibility changes.
- **Replaceability:** modules can be replaced or re-implemented behind stable public APIs.

### 5.2 Terms (normative)

- **Module:** a directory/package that owns a cohesive responsibility and has a **public entrypoint**.
- **Public API:** the only import surface other modules may use (e.g., `module/__init__.py`, `module/index.ts`).
- **Deep import:** importing anything inside another module that is *not* part of its public API (e.g., `module/internal/foo`).
- **Composition root:** the single place where concrete implementations are wired together (DI, factories, pipeline assembly). Modules MUST NOT self-assemble across boundaries.

### 5.3 Boundary rules (non-negotiable)

These rules apply to *all* SDMM tracks.

1. **Public API only**
- **MUST:** All cross-module imports go through the module’s public entrypoint.
- **MUST NOT:** Import from another module’s internal paths (“deep imports”).

1. **Explicit dependency graph**
- **MUST:** Define an explicit allowed dependency graph (layers or DAG).
- **MUST:** Enforce the graph mechanically (see Appendix A tooling).

1. **Acyclic dependencies**
- **MUST:** The module dependency graph is acyclic.

1. **No import-time side effects**
- **MUST:** Importing a module MUST be safe and fast.
- **MUST NOT:** Perform I/O, network calls, global mutations, or expensive initialization at import time.
- **SHOULD:** Put initialization behind functions, factories, or composition roots.

1. **Stable seams**
- **MUST:** Every module defines:
  - its public API surface,
  - the contracts it consumes and produces,
  - and the tests that validate those contracts.

### 5.4 Evolution modes (core concept)

This standard uses two evolution modes. They determine whether changes MUST preserve backward compatibility.

- **Compatibility Mode**: required when the artifact or interface is **externally observed or persisted** (APIs, events, DB rows, on-disk manifests, job envelopes, evaluation datasets, logs consumed by other systems).
  - **MUST:** Use additive changes and tolerant readers.
  - **MUST:** Provide migration windows for breaking changes (expand/contract).

- **Refactor Mode**: allowed when the interface is **internal and not persisted**.
  - **MAY:** Make breaking changes if all callers are updated in the same deploy.
  - **MUST:** Still respect SDMM boundaries and dependency graph rules.

**Important:** Most SDMM code changes are in refactor mode; most **contracts** (§4) are in compatibility mode.

### 5.5 SDMM structure patterns (recommended)

These are recommended patterns that reduce coupling:

- **Thin module boundaries:** expose small, stable interfaces; hide internals.
- **Dependency inversion:** depend on interfaces/contracts, not concrete implementations.
- **Ports & adapters:** isolate I/O behind adapter modules; keep core deterministic.
- **Single composition root:** assemble pipelines/apps in one top-level module.

### 5.6 Anti-patterns (high-impact)

Avoid these; they reliably destroy SDMM over time:

- **Cross-module “helpers”** that become universal dependencies.
- **Feature modules importing each other’s internals** (hidden coupling).
- **“God modules”** that own too many responsibilities.
- **Implicit runtime wiring** (modules discovering each other at import time).

### 5.7 Enforcement (minimum)

- **MUST:** boundary enforcement tooling in CI (Appendix A).
- **MUST:** one canonical repo verify command (see §10.1).
- **SHOULD:** a “module map” doc (or generated graph) in the repo root.

## 6. SDMM Frontend Track (UI applications)

This track applies to web/mobile applications where the primary output is UI and user workflows.

### 6.1 Frontend module taxonomy (recommended)

A practical SDMM taxonomy for UI apps:

- `app/` (or `apps/web/`): the **app shell** (routing, providers, composition root).
- `features/`: user-facing feature modules (workflow-oriented).
- `ui/`: reusable UI components (design-system level).
- `core/`: cross-cutting utilities and domain-agnostic services (logging, auth client, telemetry).
- `contracts/` (or `contract_types/`): generated/imported contract types + stable identifiers (NOT the SSOT Contract Hub; see §3.4).


**Note:** In multi-repo topologies where the canonical Contract Hub is a repo/folder named `contracts/`, avoid naming an internal package `contracts/` if it causes confusion. Prefer `contract_types/`, `boundary_contracts/`, or similar for repo-local generated types and adapters.

### 6.2 Recommended dependency graph

A common graph that scales:

```
app (shell)
  -> features
      -> ui
      -> core
      -> contracts
ui
  -> contracts
core
  -> contracts
contracts
  -> (imports nothing)
```

Rules:

- **MUST:** `features/*` MUST NOT deep-import from other `features/*`.
- **MUST:** `ui/*` MUST NOT import from `features/*` (UI kit stays generic).
- **SHOULD:** Prefer “feature API” exports (e.g., `features/orders/public.ts`) rather than shared internal imports.

### 6.3 App shell rules (composition root)

The app shell owns:

- dependency injection / provider wiring,
- routing and navigation,
- feature registration,
- environment/config loading.

Modules MUST NOT:

- read environment/config at import time,
- register routes implicitly,
- instantiate global singletons outside the app shell.

### 6.4 Feature module rules

Each feature module MUST provide:

- a stable feature-level public API (routes, entry components, feature services),
- explicit states (loading/empty/ready/error/permission; plus AI-native states when applicable; see §6.7),
- tests for at least one critical happy path and one failure path.

Each feature module SHOULD:

- include a feature “contract map” that lists backend routes/job types it depends on,
- define stable test selectors for critical UI interactions.

### 6.5 UI kit rules

The UI kit is **not** a dumping ground. It is a shared **contract surface**.

- **MUST:** UI kit components are generic and do not encode product workflows.
- **MUST:** UI kit MUST NOT call backend APIs directly (no network I/O). It MAY expose primitives, hooks, and adapters that the app shell wires to real services.
- **MUST:** UI kit MUST consume design tokens from the canonical token contract (see §4.5.1). Raw “magic” values are forbidden outside token sources.
- **MUST (when a UI kit exists):** UI kit MUST publish Storybook (or equivalent) and treat its stories as the canonical visual contract for atomic components.
- **SHOULD:** Shared components SHOULD have stable identifiers (e.g., `COMP-###`) and documented props/events; changes SHOULD follow expand/contract + deprecation windows.

### 6.6 Frontend testing gates (minimum)

Every frontend repo MUST provide a single `verify` entrypoint that runs locally and in CI.

Cost-control principle (aligned with §10):

- **MUST:** `verify` MUST be “review-loop fast” and deterministic.
- **SHOULD:** If full end-to-end or visual suites are slow, repos SHOULD provide a **full mode** (e.g., `./scripts/verify --full`) used in nightly or pre-release gates rather than on every PR.

Minimum required gates (run in the default `verify` unless explicitly documented otherwise):

- **Boundary lint:** no deep imports; dependency graph enforced (Appendix A).
- **Unit tests:** key utilities + reducers/state machines.
- **Type/lint:** language-appropriate type checking and linting.
- **E2E smoke tests:** a **minimal** set of top workflows, traceable to the UI Spec Appendix (Appendix D). These tests MUST use stable selectors and SHOULD run against deterministic/stubbed dependencies whenever feasible.

Additional gates for AI-enabled UI (profile-aware):

- **MUST (L1/L2; for shared UI kit in all profiles):** **Token enforcement** - forbid raw “magic” styling values (hex colors, spacing, typography) where design tokens exist (see §4.5.1).
- **MUST (when a UI kit exists):** **Atomic component visual contract** - UI kit component states referenced by the UI Spec Appendix MUST be snapshotted (Storybook/Playwright/Percy/etc.). Running these snapshots in PR gates is RECOMMENDED when UI kit code changes; otherwise they MAY run in `--full` or nightly gates.
- **SHOULD (L1/L2):** **Accessibility gate** (axe-core or equivalent) on critical flows (keyboard, labels, focus, contrast).
- **SHOULD:** **Contract rendering tests** for AI-specific contracts consumed by the UI (citations, streaming frames, error code mapping).
- **SHOULD:** **Screen-level visual regression** for critical “trust” surfaces (approvals, billing, admin, safety settings).

Optional advanced automation:

- **SHOULD (advanced):** **Design-to-code traceability check** (e.g., `UI-###` ↔ named Figma frames via Figma API). This detects “orphaned specs” and “rotating links”.

### 6.7 AI-Native UX patterns (streaming, thinking, repair, citations)

AI-enabled UIs have failure modes that classic CRUD UIs often do not: probabilistic latency, streaming partials, tool-call fan-out, citation integrity drift, and “repair” loops. Standardizing these patterns improves user trust and reduces cross-team integration churn.

#### 6.7.1 Distinguish “Loading” from “Thinking”

- **Loading** (network latency): the UI is waiting for I/O (request in flight, polling, cache miss).
- **Thinking** (AI processing): the backend is executing a compute-bound step (retrieval, ranking, reasoning, composition) and may have meaningful progress to report.

Rules:

- **MUST:** For AI flows, the UI MUST render a distinct “Thinking/Working” state when the system is compute-bound (not only a generic network spinner).
- **SHOULD:** If AI compute time exceeds ~2 seconds, producers SHOULD emit structured progress frames (StreamFrame `kind=progress`) so the UI can show credible progress (e.g., “Retrieving 3 documents…”). If progress is unavailable, the UI MUST still show a generic Thinking state after an appropriate threshold.

#### 6.7.2 Streaming output

When a screen renders streamed content (chat, generation, long-form output):

- **MUST:** Streaming payloads MUST use the `StreamFrame` contract (§4.4.10) and be fixture-backed.
- **MUST:** The UI MUST preserve usability during streaming (scroll anchoring, selection stability, and the ability to cancel/stop generation).
- **MUST:** The UI MUST handle partial vs final states explicitly (e.g., render a “draft/streaming” indicator until `final`).
- **SHOULD:** Prefer `delta.mode = append` for text streaming. Use `replace` sparingly and only when the UI Spec explicitly calls it out (to avoid jitter and complex diff logic).

#### 6.7.3 Repair / recovery loops

For AI actions with meaningful failure recovery (rate limits, tool failures, invalid inputs, safety blocks):

- **MUST:** Map backend error codes to user-facing recovery actions (retry, edit inputs, switch mode, contact support) using stable error identifiers (see §4.4.1/§4.4.2).
- **SHOULD:** Provide a “repair” UX when the system can suggest a minimal fix (e.g., missing permission, malformed document) rather than forcing users to start over.

#### 6.7.4 Optimistic updates

For low-risk, easily reversible actions (rename a chat, add a tag, reorder a list):

- **SHOULD:** The UI SHOULD apply the change optimistically and roll back on error.
- **MUST (if optimistic UI is used):** The UI MUST implement rollback correctly and surface user-safe error messaging.
- **MUST:** The backend MUST support idempotency (and stable error codes) so retries do not create duplicates.

#### 6.7.5 Citations and references (high-trust RAG UI)

If the product renders citations/references:

- **MUST:** The system MUST use the structured citation contract (AnnotatedContent/CitationSet, §4.4.9), including an explicit integrity signal (`integrity.status`).
- **MUST:** UI interactions for citations MUST be specified (hover preview vs side panel vs new tab) and MUST be accessible (keyboard + screen readers).
- **SHOULD:** The UI SHOULD degrade gracefully when citations are missing/invalid (show “No sources available” or “Sources unavailable” rather than broken links).

### 6.8 High-fidelity visual interaction (HFVI) extension (canvas/WebGL/game surfaces)

This section is normative when the Master Doc declares `interactionProfile = hfvi_canvas_webgl_game`.

HFVI systems (games, drawing tools, Konva/Pixi/WebGL canvases) have a dominant failure mode: the most important requirements are spatial and temporal (geometry, hit areas, motion curves, z-order, camera transforms). Pure prose is often ambiguous; without explicit technical anchors and fixtures, AI-generated UI code frequently drifts.

HFVI requirements extend (not replace) Appendix D (UI Spec Appendix). Projects MUST continue to maintain Appendix D for screen/workflow traceability. HFVI adds an additional, contract-like appendix for interaction surfaces and entities.

#### 6.8.1 Interaction profile declaration

- MUST: Declare `interactionProfile = hfvi_canvas_webgl_game` in the Master Doc when the product contains high-fidelity canvas/WebGL interaction surfaces.
- SHOULD: Identify the concrete rendering engine(s) and libraries used per surface (e.g., Konva.js, PixiJS, Three.js, Unity WebGL).

#### 6.8.2 Visual Interaction Spec Appendix (VIS)

- MUST: Additionally maintain Appendix K (VIS - Visual Interaction Spec Appendix) for each HFVI surface.
- MUST: Appendix D MUST reference the relevant VIS Scene IDs for any screen that includes an HFVI surface.

Minimum VIS coverage (per Appendix K):

- coordinate system and transforms (DPR, scaling, camera)
- layer/z-order rules
- input model (mouse/touch/keyboard/gamepad mapping)
- visual aggregates and invariants
- visual component spec table with technical props/config anchors
- motion tokens referenced (no magic motion)
- debug overlay contract
- verification mapping to replay cassettes and visual baselines

#### 6.8.3 Technical anchors and ubiquitous language

- MUST: HFVI specs MUST include library-level technical anchors (e.g., Konva `Stage/Layer/Group`, `hitStrokeWidth`, `dragBoundFunc`, CSS `cubic-bezier`, etc.) instead of relying on aesthetic prose.
- SHOULD: Add HFVI terms to the project glossary so prompts, specs, and code share the same ubiquitous language.

#### 6.8.4 Motion tokens (no magic motion)

- MUST: HFVI interactions MUST NOT hardcode motion parameters (durations, easings, spring constants) outside token sources.
- MUST: HFVI motion MUST be expressed via motion tokens (see §4.5.1) and referenced by stable IDs (e.g., `MOT-SNAP`, `MOT-REJECT`).
- MAY (L0 only, bounded): Prototypes MAY use magic motion values only inside an explicitly bounded prototype namespace with owner + expiry.

#### 6.8.5 Debug overlay and invariants

- MUST: HFVI components MUST implement a debug overlay mode (Appendix K) that can render hit areas, bounding boxes, anchor points, and key vectors.
- SHOULD: HFVI visual aggregates SHOULD define explicit invariants (spatial relationships) and validate them in debug mode (fail fast with actionable errors).

#### 6.8.6 Verification gates: replay + visual regression

HFVI correctness is often best verified via a combination of input replay and visual baseline comparison.

- MUST: Frontend repos that ship HFVI surfaces MUST provide a visual verification gate (e.g., `verify --visual`).
- MUST: The visual gate MUST run deterministic input replay (cassette-based) for critical interactions and capture screenshot baselines for key frames.
- SHOULD: Prefer invariant assertions (Appendix K invariants + debug checks) in addition to screenshot diffs to reduce brittleness.
- SHOULD: Keep PR gates review-loop fast: run a minimal cassette set in `verify` and run broader visual suites in `verify --full` (or nightly) per §10.3.

#### 6.8.7 AI task decomposition for HFVI

In addition to the standard AI task template (§11.1), HFVI tasks MUST:

- reference the relevant Appendix K entries (Scene/VC IDs),
- specify the technical anchors to be used (props/config),
- specify the replay cassette(s) to update or add,
- specify the visual baseline update policy.

Recommended sequence (schema/props first):

- MUST: Require "schema/props first" generation: the agent produces the HFVI component props/anchors as types or JSON config (from Appendix K) before generating implementation code.
- SHOULD: Implement rendering as pure constructors first; bind interactions/events second; add replay fixtures third.

## 7. SDMM Algorithm Track (pipelines, libraries, services)

This track applies to algorithm/pipeline code (LLM pipelines, ranking, extraction, evaluation harnesses). The dominant risks here are: **non-determinism**, **hidden side effects**, and **contract drift**.

### 7.1 Recommended module layout

A scalable algorithm SDMM layout:

- `algo/contracts/` - contract bindings and schema adapters (imports nothing)
- `algo/core/` - deterministic business logic and pure transforms
- `algo/prompts/` - prompt templates and prompt policies (no I/O)
- `algo/tools/` - tool interfaces and tool policies (no I/O)
- `algo/adapters/` - I/O implementations (LLM clients, DB clients, HTTP, files)
- `algo/pipelines/` - pipeline assembly and orchestration (composition root per pipeline)
- `algo/evals/` - evaluation runners and scoring
- `algo/integration/` - system wiring, CLI entrypoints, server endpoints

### 7.2 Dependency graph (normative)

Algorithm projects are best represented as a **DAG**, not a strict stack. The minimum constraints:

- `contracts` and `core` are **base layers**.
- `pipelines` and `integration` are **top layers**.
- `prompts` and `tools` are **parallel siblings** that pipelines can consume.

Practical rule set:

```
integration -> evals -> pipelines
pipelines -> adapters
pipelines -> prompts
pipelines -> tools
adapters -> core
prompts -> core
tools -> core
core -> contracts
contracts -> (imports nothing)

Forbidden:
adapters -> prompts
adapters -> tools
core -> adapters|pipelines|integration|evals
prompts -> adapters|pipelines|integration|evals
tools -> adapters|pipelines|integration|evals
```

Enforce with tooling (Appendix A). Do not rely on reviewer memory.

### 7.3 Determinism & replay tiers (required)

Each pipeline MUST declare a determinism tier in its Master Doc and record it in the RunManifest (`determinism.tier`, §4.4.4).

These tiers are intentionally simple and map to serialized values `tier0`, `tier1`, `tier2`:

- **Tier 0 (replay via cassettes):** non-deterministic or externalized behavior (live LLMs, live tools, live networks). CI reproducibility is achieved by recording inputs/outputs (“cassettes”, tool transcripts, snapshot IDs) so verification can run offline.
- **Tier 1 (stable given pinned dependencies):** repeatable given pinned model/tool versions and pinned datasets; outputs are stable enough for gating but not necessarily bitwise identical.
- **Tier 2 (bitwise / fully deterministic):** identical outputs across runs; prohibits uncontrolled randomness, concurrency races, and hardware-sensitive operations (rare in LLM-heavy pipelines).

Rules:

- **MUST:** For Tier 0/Tier 1 pipelines, the RunManifest MUST record the configuration and relevant dependency pins (see §4.4.4).
- **MUST:** Tier 0/Tier 1 pipelines MUST have a replay harness and golden fixtures that run in CI (see Appendix F.6). How often they block merges is a cost decision governed by the project profile (§2.3) and the CI tiering policy (§10.3).
- **SHOULD:** Prefer invariant-based assertions over brittle full-string equality (e.g., schema validity, citation integrity status, presence of required fields, bounded score thresholds).
- **SHOULD:** Keep cassettes small and stable by recording **tool outputs / retrieved documents / structured intermediate states**, not raw LLM token streams, unless tokens are the product output.
- **SHOULD:** Prefer moving pipelines upward (Tier 0 → Tier 1 → Tier 2) over time as the product stabilizes.

### 7.4 Side effects and `sideEffectsMode` (required)

All algorithm execution MUST accept `sideEffectsMode` (see §4.4.4 and §4.4.6):

- `dryRun`: no external writes; safe for validation and replay.
- `sandbox`: writes allowed only to sandbox namespaces/resources.
- `live`: production writes allowed.

Rules:

- **MUST:** Any adapter that can write externally MUST check `sideEffectsMode` before writing.
- **MUST:** In `dryRun`, adapters MUST be read-only or use fakes/cassettes.
- **MUST:** The orchestrator MUST pass `sideEffectsMode` through (JobEnvelope → pipeline execution).

### 7.5 Budgets (required)

Budgets prevent runaway cost and make failures explainable. Budgets are recorded in:

- RunManifest (`budget.allocated`, `budget.consumed`, `budget.remaining`)
- PipelineResult (`budget`)
- JobEnvelope (`runs[].result.budget`)

Rules:

- **MUST:** Each pipeline defines a budget policy (tokens, timeMs, externalCalls, bytes, etc.).
- **MUST:** Budgets are enforced at runtime, not just measured.
- **MUST:** If a budget limit affects execution, the result MUST include (a) a stable `budget.termination.code` when the run terminates due to a hard budget (e.g., `tokens_exhausted`, `time_exhausted`, `external_calls_exhausted`, `cancelled`) and (b) diagnostics codes (e.g., `budget.exhausted`, `budget.exceeded`).

Use the canonical Budget shape in §4.4.3. Do not invent alternative budget schemas in module docs.

### 7.6 Run manifests, pipeline results, and explainability (required)

- **MUST:** Every run produces a RunManifest (see §4.4.4) and a PipelineResult (see §4.4.5).
- **MUST:** The PipelineResult MUST carry a `manifestRef` pointer to the exact RunManifest used.
- **MUST:** The orchestrator MUST wrap the PipelineResult without lossy translation (JobEnvelope, §4.4.6).
- **SHOULD:** Stage summaries are included for multi-stage pipelines.

### 7.7 Evaluations and gating (required for material changes)

- **MUST:** Material algorithm changes are gated by evaluations.
- **MUST:** Datasets are pinned via DatasetManifest (§4.4.7).
- **MUST:** Evaluation outputs are summarized via EvalReport (§4.4.8) and stored as artifacts.

Recommended practice:

- A small **CI eval split** for fast gates (minutes).
- A larger offline eval split for releases (hours), run on schedule or prior to deployment.

### 7.8 Algorithm testing gates (minimum)

Each algorithm repo MUST provide:

- Boundary checks (graph enforcement).
- Unit tests for core deterministic transforms.
- Deterministic CI eval suite (pinned dataset split).
- Replay verification for Tier 0/Tier 1 pipelines (cassette replays for Tier 0; pinned snapshot/fixture replays for Tier 1).

Cost-control note:

- **SHOULD:** If replay suites are slow, run them in a `verify --full` tier (nightly/pre-release) while keeping at least a minimal offline replay smoke in the default `verify` for critical paths.

### 7.9 Refactoring & migration patterns

Large algorithm refactors MUST use safe migration patterns:

- branch-by-abstraction,
- parallel run/shadow mode,
- expand/contract contracts,
- golden fixtures and replay harnesses.

See Appendix F for the detailed playbook.

## 8. Backend / Orchestrator Engineering (AI Product Engineering Principles)

Key requirements (summary):

- Backend owns **job orchestration** for long-running AI work (queueing, retries, cancellation, idempotency).
- Backend owns **canonical validation** and **canonical error mapping** at the system boundary.
- Algorithm services MUST return **PipelineResult** and a pointer to **RunManifest**.
- Orchestrator wraps results into **JobEnvelope** without lossy translation.

For full detail, see **Appendix G (AI Product Engineering Principles Addendum)**.

## 9. Project documentation requirements (Master Doc + doc families + UI Spec)

### 9.1 Project Master Doc (required)

Every project MUST maintain a canonical Master Doc that is versioned with code and reviewed like code (Docs as Software). The Master Doc MUST:

- include an explicit **Doc readiness gate** in its `Document Control` section (or an extension-mapped equivalent subsection) so tooling and reviewers know what blocks the doc from becoming canonical,
- declare the project’s **conformance profile** (`L0|L1|L2`, §2.3) explicitly,
- declare the project’s **interaction profile** (`standard_ui|headless|hfvi_canvas_webgl_game`, §2.4) explicitly,
- declare `Doc family role = canonical_entrypoint` explicitly,
- declare document status using the normative enum from `standard_manifest.json`,
- declare the governing standard reference used by the project,
- define product scope and constraints,
- define system topology (monorepo vs multi-repo) and the contract hub location,
- enumerate contract surfaces and owners (APIs, events, persisted artifacts),
- include a **Contract Inventory Index** (schema IDs + owners + compatibility windows),
- include a **Traceability Index** that maps:
  - requirements → contracts → tests/gates,
  - UI workflows → routes/jobs → run/pipeline artifacts,
- define verification gates and exact `verify` commands (per repo and system-level),
- include an execution plan (tasks with acceptance criteria and test evidence).

For machine-readable checks, the Master Doc required-section model SHOULD explicitly cover at least `Document Control`, `Contracts`, `Contract Inventory Index`, `Traceability Index`, and `AI Execution Plan`, and the required-subsection model SHOULD explicitly cover `Document Control -> Doc readiness gate`, so tools do not mistake a broad top-level `Contracts` heading for full doc completeness.

Doc update policy (to control cost and avoid “checkbox docs”):

- **MUST:** If a change modifies requirements, workflows, contract surfaces, budgets, determinism tiering, security posture, or verification gates, the same PR MUST update the Master Doc (or include a documented waiver with owner + expiry).
- **MAY:** Pure refactors that do not change behavior/contracts/workflows MAY omit Master Doc edits.
- **SHOULD:** For L0 projects, the Master Doc SHOULD remain short and focus on critical flows and risks; expand as the product stabilizes.

### 9.2 Doc-family governance and subordinate docs (required)

Real repos rarely stop at a single Master Doc. Typical doc families include PRDs, UI specs, package/module docs, runbooks, deployment docs, context packs, and support notes. These subordinate docs MUST be governed consistently enough that tooling and reviewers can trust them.

The same metadata discipline also applies to **release-companion docs bundled with the standard itself**; those are classified in the release manifest as `normative_addendum` rather than being treated as out-of-band Markdown.

Minimum rules:

- **MUST:** Every subordinate doc that is part of the governed doc set MUST have a small **Document Control** header including, at minimum:
  - `Doc ID`,
  - `Owner`,
  - `Status`,
  - `Governing standard`,
  - `Last updated`,
  - `Scope` (what the doc covers / does not cover).
- **MUST:** `Owner` is the canonical minimum metadata key for machine checks. Repos MAY add richer `Owners` / RACI detail, but they SHOULD NOT omit the canonical `Owner` field.
- **MUST:** Subordinate docs that define executable or reviewable behavior (PRD, UI Spec, module MASTER_DOC, Headless Surface Note, deployment/runbook docs used for release decisions) MUST point back to the canonical Master Doc.
- **MUST:** Subordinate docs MUST use the normative status enum from `standard_manifest.json`.
- **MUST:** If a subordinate doc is intentionally `N/A`, it MUST say **why** it is not applicable and where the governing truth lives instead.
- **SHOULD:** Subordinate docs SHOULD be structurally minimal when possible; small docs with valid metadata are better than large docs that rot.
- **SHOULD:** Teams SHOULD use Appendix M for doc-family matrices and minimal subordinate-doc templates instead of inventing repo-local conventions from scratch.
- **MUST:** Official templates shipped with this standard MUST themselves satisfy the metadata and section rules of the doc types they are meant to instantiate; otherwise the standard would emit non-compliant scaffolds.

Recommended minimum by doc type:

| Doc type | Must declare status | Must declare governing standard | Must link to Master Doc | Special rule |
| --- | --- | --- | --- | --- |
| Master Doc | Yes | Yes | N/A | Canonical entrypoint |
| PRD | Yes | Yes | Yes | Requirements-only docs still need scope + owner |
| UI Spec | Yes | Yes | Yes | Use Appendix D unless `headless` |
| Headless Surface Note | Yes | Yes | Yes | Required when `interactionProfile = headless` and no UI screen inventory exists |
| Package / module MASTER_DOC | Yes | Yes | Yes | Required when the module is shipped, shared, or verify-critical |
| Runbook | Yes | Yes | Yes | Must declare operational owner |
| Deployment doc used for release | Yes | Yes | Yes | Must declare rollout / rollback ownership and environment scope |
| Context Pack | Yes | Yes | Yes | May be short, but must stay current |
| Support note / incident-support doc | Yes | Yes | Yes | Must declare audience, evidence scope, and redaction/export behavior |
| Normative addendum / release companion doc | Yes | Yes | Links to parent standard | Use governed metadata even when shipped with the standard release itself |

### 9.3 UI Spec Appendix (required for UI products, explicitly handled for headless)

If the project has a user-facing UI (web/mobile/admin), it MUST maintain a UI Spec Appendix (Appendix D) that defines:

- stable Screen IDs and Route IDs,
- explicit `Loading/Empty/Ready/Error/Permission` states, plus AI-specific `Thinking/Streaming/Repair` states when applicable (see §6.7),
- workflow-to-screen-to-contract traceability,
- stable test selectors for critical interactions,
- AI interaction mode per screen (static/streaming/async_job) and the referenced contracts when applicable (citations §4.4.9; streaming §4.4.10),
- design system contract references (tokens/components) for shared UI surfaces (see §4.5).

Headless exception:

- **MUST:** If the project declares `interactionProfile = headless`, it MAY omit a screen-based UI Spec, but it MUST provide a Headless Surface Note (Appendix M) or an extension-declared equivalent that maps back to core doc type `headless_surface_note` for machine checks.
- **MAY:** A thin `UI_SPEC = N/A` pointer doc MAY exist for navigation or legacy compatibility, but it MUST point to the governing Headless Surface Note (or extension-mapped equivalent) and MUST NOT be treated as the substantive headless interaction spec.
- **MUST NOT:** Headless projects MUST NOT silently skip UI-spec governance; they still need an explicit doc-family member covering operator and machine-facing interaction surfaces.

Design review (recommended):

- Use **Appendix H - UI Design Review Checklist** as the cross-functional UI review checklist (Design + PM + Eng).
- Items marked **automatable** SHOULD be enforced in the frontend `verify` gate; other items must be reviewed by a human (LLM assistance is optional, not authoritative).

### 9.4 Package / library / worker / infra module docs model

Monorepos and hybrid repos often contain more than deployable apps: packages, SDKs, workers, shared generators, policy packs, and infra modules. The standard MUST say when these modules need docs and when they need determinism metadata.

Rules:

- **MUST:** A package/library/module MUST have its own module-level MASTER_DOC (or an equivalent doc-family member) if it is:
  - published outside its local module boundary,
  - shared across repos or teams,
  - consumed by code generation or verify gates,
  - responsible for persisted artifacts, contracts, policy packs, or runtime-critical behavior.
- **MUST:** Module docs MUST declare a `Module kind` using the normative machine-readable enum (`package|library|worker|service|infra_module|tooling_module|generator|policy_pack|other`).
- **MUST:** Module docs MUST declare `Doc family role = module_doc` explicitly.
- **MUST:** A worker or service module doc MUST declare an explicit `Interaction profile`.
- **MUST:** If a worker or service module has no primary end-user UI, its module-doc interaction profile MUST be `headless` and the doc MUST describe its operator/API/job/runtime surfaces.
- **MAY:** If a worker or service module participates in a UI-bearing product surface, the module doc MAY declare the applicable project interaction profile (`standard_ui` or `hfvi_canvas_webgl_game`) instead of `headless`.
- **MUST NOT:** Pure package/library/tooling modules MUST NOT be forced to invent a fake interaction profile; if interaction profile is not applicable, the doc MUST say so explicitly outside the project-level interaction-profile enum.
- **MUST:** Module docs MUST declare whether determinism is applicable.
- **MUST:** A `Determinism` section is required when the module contains:
  - algorithmic logic,
  - generators,
  - validators,
  - scoring/eval logic,
  - replay or fixture-based checks,
  - or any logic whose outputs are used as release/verify evidence.
- **MAY:** Pure static asset packages, style/token packages, or trivial type-only packages MAY declare `Determinism: not_applicable`, but they MUST provide a one-line reason.
- **MUST NOT:** Repos MUST NOT place packages into a “half-governed” state where package docs are metadata-checked but structurally exempt from the rules they are expected to satisfy.
- **SHOULD:** Appendix M SHOULD be used for the minimal package/library/worker template and the determinism applicability table.

### 9.5 Traceability automation (strongly recommended)

Manual traceability tables rot quickly unless the maintenance cost is near-zero. Projects SHOULD automate where feasible:

- Generate Traceability Index tables from code metadata (e.g., test names containing `FR-###`, Storybook stories containing `UI-###`, contract schemas containing `SCHEMA-###`).
- Provide a `scripts/traceability` (or equivalent) that fails CI when referenced IDs are missing or orphaned.

If a project does not automate traceability:

- **MUST:** Keep the Traceability Index minimal and focused on critical workflows and externally observed/persisted surfaces.
- **MUST:** Assign an owner for the Traceability Index and review it at least once per release milestone.

### 9.6 Master Doc modularization and Context Packs (token-cost control)

Long, monolithic documents are expensive for both humans and LLMs. This standard explicitly supports **doc sets** (§2.2) so teams can keep a small canonical index while moving detail into scoped sub-docs.

Rules:

- **MUST:** Each project MUST have exactly **one canonical Master Doc entrypoint** (an index document).
- **MAY:** The Master Doc entrypoint MAY delegate detail to linked sub-docs (architecture, API registry, deployment, UI spec, etc.).
- **MUST:** Delegation MUST NOT create a “link farm.” The Master Doc entrypoint MUST still contain, at minimum:
  - conformance profile + interaction profile declarations,
  - a topology summary and contract hub location,
  - the Contract Inventory Index (or a single authoritative link to it),
  - the Traceability Index (or a single authoritative link to it),
  - canonical `verify` commands (per repo + system),
  - an execution plan (task list + acceptance criteria).
- **SHOULD:** Each sub-doc SHOULD have its own mini **Document Control** header: `Doc ID`, `Owner`, `Last updated`, and `Version/Status` (even if it is not separately versioned from the repo).
- **SHOULD:** Teams SHOULD keep any single doc under a practical model context budget. As a rule of thumb, **SHOULD** keep per-doc size under ~10–20k tokens; if it grows beyond that, split by **stable boundaries** (repo/module, workflow, or contract surface).

**Context Pack pattern (recommended; high leverage):**

- **SHOULD:** Provide a `docs/context-pack.md` (or `AI_README.md`) kept intentionally small (often 2–6k tokens) containing:
  - glossary + key invariants,
  - system diagram + critical workflows,
  - contract inventory summary (IDs + links),
  - exact `verify` commands,
  - current task board / next actions,
  - “how to run locally” in one screen.
- **MUST (L2):** The Context Pack MUST be kept current (updated in the same PR when changing workflows/contracts/gates), because it becomes a control surface for multi-team execution.

Automation (strongly recommended):

- **SHOULD:** `verify` SHOULD include a docs check that fails on:
  - broken relative links,
  - missing required Document Control fields,
  - duplicate IDs (Route IDs, Screen IDs, Contract IDs) referenced from docs.

### 9.7 Doc drift and inconsistency handling (code ↔ Master Doc)

Even with Docs-as-Software discipline, teams will sometimes discover mismatches between **current code behavior** and the **Master Doc** (or other docs). This is “doc drift” (§2.2).

Rules:

- **MUST:** When drift is discovered, the discoverer MUST record it immediately as one of:
  - a PR note (if discovered during implementation), or
  - a tracked issue labeled `doc-drift` (if discovered outside an active PR).
- **MUST:** The team MUST resolve drift by choosing **exactly one** of the following outcomes and documenting the decision (ADR or a short “Drift Decision Record” section in the PR):
  1. **Doc is wrong / outdated** → update the docs (Master Doc / UI Spec / addenda) to match intended and shipped behavior.
  2. **Code is wrong** → change code (or revert) to match the documented intent.
  3. **Intent changed** → write an ADR, then update both docs and code to the new intent with an explicit compatibility/migration plan if any contract surfaces are impacted.
- **MUST:** If drift impacts an **externally observed or persisted surface** (APIs, events, stored artifacts, identifiers), the fix MUST include:
  - an explicit compatibility plan (expand/dual-support/contract),
  - updated fixtures for both old and new shapes during the window,
  - updated verification gates that reproduce the drift class.
- **MUST:** If drift is not fixed in the same PR, a waiver MAY be used, but it MUST include an owner, scope, and an expiry (date or release milestone).

Drift-prevention controls (recommended):

- **SHOULD:** Mechanically generate or validate API inventories (router → registry) to avoid “docs say X, code does Y.”
- **SHOULD:** Treat contract fixtures + contract tests as the primary executable source of truth for cross-boundary behavior.
- **MUST (L2):** L2 projects MUST have at least one automated drift check (API registry diff, schema/fixture validation, or traceability script) that runs in CI.

### 9.8 Multi-party / multi-company documentation governance (humans + tools)

Large programs often require multiple teams or companies to co-author the Master Doc set. The goal is to keep a single canonical intent while allowing parallel work.

Minimum governance rules:

- **MUST:** Every doc in the Master Doc set MUST have an explicit **Owner** (individual or team) and a review rule (e.g., `CODEOWNERS`) that can enforce approvals.
- **MUST:** Cross-boundary sections (contracts, identifiers, deploy rules, security posture) MUST have a single **decision owner** accountable for final arbitration.
- **MUST:** Changes MUST flow through version control via PRs. “Out-of-band” edits (shared docs not tied to code) MUST be reconciled back into the repo promptly or treated as non-canonical.
- **SHOULD:** For multi-company programs, teams SHOULD adopt a lightweight RFC process for contentious or high-impact changes (topology, contract evolution rules, security posture, environment strategy).
- **MUST:** Disputes MUST be resolved by an explicit decision record (ADR/RFC outcome) so future contributors don’t re-litigate history.

For a concrete playbook (roles, approval matrix, RFC templates, and dispute resolution), see **DAS Governance & Collaboration Addendum**: `DAS_GOVERNANCE_COLLABORATION.md`.

## 10. Verification and CI gates (minimum)

### 10.1 One canonical `verify` per repo

Each repo MUST provide a single canonical entrypoint:

- `./scripts/verify` (or equivalent) is the canonical local and CI gate.
- It MUST be deterministic, and MUST fail fast on boundary / contract violations before running expensive suites.

To control cost while keeping discipline, `verify` MUST support **two standard modes**:

1. **Fast mode (review-loop gate)**  
   The default `./scripts/verify` behavior MUST correspond to “fast mode”.
   - It SHOULD complete in **< 5 minutes** on a standard developer machine for typical PRs.
   - It MUST include: formatting/lint/type checks, boundary checks, contract validation (changed surfaces), document metadata gates, and a minimal smoke test set.
   - It MUST NOT require external, non-hermetic dependencies unless explicitly documented and stubbed.

2. **Full mode (coverage gate)**  
   Repos SHOULD provide a full gate that can be scheduled nightly and/or pre-release:
   - Canonical invocation: `./scripts/verify --full` (or `./scripts/verify-full`).
   - It MAY include slow suites (full E2E, visual regression, long evals), and it MAY take hours.

Interface rules:

- `./scripts/verify` MAY accept flags (e.g., `--full`, `--ci`), but the default behavior MUST be well-defined and documented in the Master Doc.
- Repos SHOULD provide convenience wrappers `./scripts/verify-fast` and `./scripts/verify-full` (or make targets) to reduce ambiguity, while keeping `./scripts/verify` as the canonical entrypoint.
- `verify` output MUST print: mode, git SHA/build ID, pinned tool versions, and the `standardManifestVersion` used by the repo.

### 10.2 Minimum per-repo gates

- `contracts`: schema validation + fixture validation + compatibility checks for changed contracts.
- `algo`: boundary checks + unit tests + deterministic CI eval suite + replay (offline) where applicable.
- `backend`: unit + integration + contract tests + idempotency/retry tests for job flows.
- `frontend`: boundary checks + unit + minimal E2E smoke for critical flows.
- `integration`: end-to-end smoke + compatibility runner (old/new fixtures) + system verify.
- `docs/meta` (whenever a repo carries a governed doc set): status enum validation, governing-standard presence/correctness, required-section checks for canonical docs, and placeholder-residue checks.

### 10.3 Gate cadence taxonomy (required)

Not every check belongs in the same execution lane. Every governed gate or report SHOULD declare exactly one **gate cadence** from the machine-readable standard manifest:

- `pr_blocking`
- `merge_to_main`
- `nightly`
- `pre_release`
- `adoption_migration`

Cadence semantics:

1. **PR blocking**
   - **MUST:** Catch explicit correctness failures that should never merge.
   - Typical examples: placeholder residue, invalid status enum, missing governing standard, contract validation for changed surfaces, fail-open workflow lint, tooling-lock validation.

2. **Merge to main / post-merge**
   - **SHOULD:** Run aggregate audits that may be too wide for every PR but still need continuous enforcement.
   - Typical examples: inventory sync reports, package-doc completeness audits, route/build/release drift summaries.

3. **Nightly**
   - **SHOULD:** Run slow, deep, or trend-oriented checks.
   - Typical examples: full trace graph builds, deep contract completeness audits, full AI eval suites, broken-link scans, regression dashboards.

4. **Pre-release**
   - **MUST:** Validate release-surface parity and closure before promotion.
   - Typical examples: Docker/build-context parity, release-lane status checks, full contract mirror sync, suite-level version closure, release pack verification.

5. **Adoption / migration**
   - **MAY:** Run only when onboarding legacy repos, upgrading the standard, slicing contracts, or migrating policy packs.
   - Typical examples: `adopt-existing-repo`, `repo-normalize`, `upgrade-standard`, `contract-slice`.

Rules:

- **MUST:** Repos MUST document which cadences they implement in the Master Doc, a repo-local verify registry, or an equivalent governed artifact.
- **MUST NOT:** Report-only or migration-only tools MUST NOT be presented as equivalent to PR-blocking conformance gates.
- **SHOULD:** Suites SHOULD aggregate cadence metadata from multiple repos rather than inferring it from CI job names.
- **SHOULD:** Machine-readable manifests SHOULD publish cadence and enforcement definitions, not only enum names, so dashboards and upgrade tools can explain gate intent without scraping Markdown.

### 10.3.1 Verify registry (required when a repo has multiple governed gates)

A repo with more than one governed gate, or with gates that differ by cadence, enforcement class, or artifact expectations, MUST publish a machine-readable **verify registry** validated against `verify_registry.schema.json`.

Each governed gate entry MUST declare, at minimum:

- `gateId`
- `kind`
- `cadence`
- `enforcementClass`
- `command`
- owner/maintainer information
- scope / touched-surface expectations
- whether `failureOnNoResults` is true
- and the expected artifact classes or refs when the gate is meant to produce governed output

Rules:

- **SHOULD:** Suites and dashboards SHOULD read verify-registry metadata rather than inferring gate semantics from CI job names.
- **MUST:** A repo MUST NOT claim that a gate is governed if it is omitted from the verify registry while other governed gates are registry-backed.
- **SHOULD:** Repos SHOULD keep a committed `verify_registry.json` (or schema-equivalent serialization) alongside `scripts/verify` so review and automation consume the same truth.

### 10.3.2 Verify report (governed output)

Governed verify runs SHOULD emit a machine-readable **verify report** validated against `verify_report.schema.json`.

Rules:

- **MUST:** A governed verify report MUST record: mode, build ref / repo SHA, `standardManifestVersion`, toolchain pins, start/end time, and per-gate outcomes.
- **MUST:** Expected-but-not-executed gates MUST be represented explicitly as `not_run` or `error`; they MUST NOT disappear from the report.
- **MUST:** When `failureOnNoResults = true` for a blocking or `source_of_truth` gate, “no result artifacts found” MUST produce an explicit failing outcome rather than a synthetic PASS summary.
- **MUST NOT:** A verify report MUST NOT summarize overall PASS when every expected gate is skipped / not-run, or when required source-of-truth artifacts are missing.
- **SHOULD:** Verify reports SHOULD link to artifact refs (logs, packets, replay reports, screenshots, traces) rather than embedding large blobs inline.

### 10.4 Flakiness policy

- **MUST:** Tests that gate merges MUST be stable. Flaky tests MUST be quarantined with an owner and a plan (do not “retry forever”).
- **SHOULD:** Prefer deterministic substitutes (record/replay, contract fixtures, stubs) over live external dependencies in CI.
- **MUST:** “No results found” or “suite did not run” MUST be treated as an explicit failure for gates that are expected to produce governed output.

### 10.5 Tooling reproducibility, enforcement classes, and source-of-truth rules

`verify` only provides durable guarantees if the toolchain is reproducible, the output semantics are explicit, and local mirrors of canonical artifacts remain traceable back to a released snapshot.

Rules:

- **MUST:** `verify` MUST be runnable in a hermetic environment (container or equivalent) that pins tool versions.
- **MUST:** The repo MUST define a **tooling lock** mechanism (e.g., `tooling.lock`, `tool-versions`, or an image digest) that can be used to reproduce the exact toolchain used by CI.
- **SHOULD:** When a repo uses a standalone `tooling.lock` manifest, that manifest SHOULD validate against `tooling_lock.schema.json` shipped with this release of the standard.
- **MUST NOT:** CI pipelines MUST NOT depend on floating tool tags (e.g., `latest`) for the `verify` environment.
- **MUST:** Each governed gate/check MUST declare an **enforcement class**:
  - `report_only`
  - `blocking`
  - `source_of_truth`
- **MUST:** Repos and suites MUST distinguish “metadata collection” from “enforcement”. A check that only reports state MUST NOT be counted as a passing enforcement gate unless it is explicitly classified as `blocking` or `source_of_truth`.
- **MUST:** If a repo keeps a local copy/mirror of the canonical standard, policy pack, or another governed artifact, that mirror MUST be declared as a **mirror** in tooling lock / release snapshot metadata, with a source-of-truth ref, mirror purpose, and `localModificationsAllowed=false` unless the divergence is governed as an explicit extension.
- **SHOULD:** `verify` SHOULD emit a machine-readable summary (`verify_report.json`) including: mode, toolchain pins, gate results, gate cadence, enforcement class, and links to key artifacts (logs, manifests, snapshots).
- **SHOULD (regulated / high-stakes):** verification tooling itself SHOULD have self-tests (pass-case + fail-case) to avoid “who validates the validator?” failures.

### 10.6 Suite lock (required when standard, factory, and verify runtime are split)

When the standard, suite orchestration, repo factory, verify runtime, policy packs, or control-plane-adjacent tooling live in separate repos/modules, a suite-level **lock artifact** is required in addition to repo-local tooling locks.

Rules:

- **MUST:** A suite that governs multiple separately versioned modules MUST maintain a machine-readable **suite lock** (`suite.lock` or equivalent) validated against `suite_lock.schema.json`.
- **MUST:** The suite lock MUST pin, at minimum:
  - the governed modules,
  - each module’s primary repo role,
  - locked refs,
  - override policy,
  - and the allowed local state model (`missing`, `present_locked_match`, `present_locked_mismatch`, `present_local_override`, `dirty`).
- **MUST:** Locked sync MUST be the default for release-critical/adoption-critical flows; suites MUST NOT use clone-tip / floating HEAD as their effective source of truth.
- **SHOULD:** Suites SHOULD publish a module-state report derived from the suite lock rather than inferring state ad hoc from git output.

### 10.7 Suite-level version closure (required when standard, factory, and verify runtime are split)

When the standard, repo factory, verify runtime, policy packs, and multi-repo orchestration live in separate repos/modules, local tooling locks are not enough. The system also needs a **suite-level version closure**.

Rules:

- **MUST:** If a governed workflow depends on separately versioned components such as:
  - the DAS standard,
  - a repo factory / scaffold layer,
  - a verify runtime,
  - policy packs,
  - or multi-repo orchestration tooling,
  then the suite MUST maintain a machine-readable **version closure manifest** validated against `suite_version_closure.schema.json`.
- **MUST:** The version closure manifest MUST pin, at minimum:
  - `standardVersion`,
  - `standardManifestVersion`,
  - `suiteVersion`,
  - `factoryVersion`,
  - `verifyRuntimeVersion`,
  - `policyPackVersion` (if applicable),
  - `generatorTemplateVersion` (if applicable),
  - `suiteLockRef`,
  - and the exact refs/digests used by CI/release-critical flows.
- **MUST NOT:** Release-critical tooling flows MUST NOT clone “latest tip” / unpinned HEAD as their effective source of truth.
- **MUST:** Closure manifests for governed release/adoption flows MUST use **structured pinned refs** (`kind`, `uri`, `pinType`, `pinValue`, and `floating=false`) so “no clone-tip / no floating tags” can be machine-checked. Governed schemas MUST NOT accept legacy bare string refs in place of structured refs.
- **MUST:** Machine-readable ref schemas MUST reject nonsensical `kind × pinType` pairs (for example `container_image + path`, `git + digest`) in governed closure/lock artifacts.
- **SHOULD:** Pre-release gates SHOULD validate suite lock + suite version closure before promotion.
- **SHOULD:** Adoption/migration tools SHOULD update the closure manifest as part of the same change rather than leaving it to a later manual step.

### 10.8 Standard release snapshots and local mirror provenance

Canonical standard releases MUST be consumable as immutable snapshots, not only as ad-hoc document drops.

Rules:

- **MUST:** A governed standard release bundle MUST ship a machine-readable `release_snapshot_manifest.json` validated against `release_snapshot_manifest.schema.json`.
- **MUST:** The release snapshot manifest MUST record: `standardVersion`, `standardManifestVersion`, snapshot kind, build ref, source repo ref, bundle digest, and per-artifact digests (or an equivalent immutable artifact inventory).
- **MUST:** Repo-local mirrors/copies of the standard, policy packs, or other governed release artifacts MUST reference the originating release snapshot via tooling-lock or equivalent pinned metadata.
- **MUST NOT:** Factories or product repos MUST NOT treat mutable, template-seeded local copies of the standard as canonical unless they are explicitly governed mirrors with snapshot provenance.
- **SHOULD:** Adoption and `standard-diff` tools SHOULD compare repo-local mirrors against the release snapshot manifest before mutation or upgrade.
- **SHOULD:** Appendix N and Appendix L be used together: Appendix N for placement/ownership, Appendix L for lock/report/snapshot mechanics.

See Appendix L plus the machine-readable schemas shipped with this version of the standard.

## 11. AI-assisted development workflow (minimum)


### 11.1 AI task template (MUST)

Each AI task or PR MUST state:

- **Scope**: which repo(s), which module(s), which contract surfaces.
- **Contract impact**: none/additive/breaking (with compatibility plan if breaking).
- **Determinism & replay**: declared tier; whether replay is expected.
- **Budgets**: what budgets are enforced/changed.
- **Verification**: exact `verify` commands and expected outcomes.

### 11.2 Cross-repo sequencing

When contract changes are needed:

1. Expand contract in `contracts` hub (additive, backward-compatible).
1. Update tolerant readers first (consumers).
1. Update producers to emit new fields/forms.
1. Dual-support for a bounded window.
1. Contract/remove legacy.

This sequencing MUST be documented in the Master Doc and enforced via the integration harness.

## 12. DDD + BDD integration (domain + behavior as first-class artifacts)

This unified standard is **compatible with** and **strengthened by**:

- **DDD (Domain-Driven Design)**: clarifies domain ownership, boundaries, and invariants so modularity has *semantic* integrity (not just folder boundaries).
- **BDD (Behavior-Driven Development / Specification by Example)**: turns requirements and workflows into executable scenarios so verification is aligned to product intent.

The goal is not to “rename” this standard into DDD/BDD, but to make DDD/BDD **cheaper to practice** and **harder to drift** by connecting them to: contracts, fixtures, `verify` gates, and traceability.

### 12.1 Mapping: this standard ↔ DDD ↔ BDD

**Repo / SDMM module boundaries ↔ bounded contexts (DDD)**

- A repo boundary or SDMM module boundary SHOULD correspond to a **bounded context** with a clear owner, a clear system of record, and a clear public contract surface.
- If a boundary exists *without* a bounded-context rationale, it SHOULD be treated as suspect and either:
  - merged back into a single bounded context, or
  - formalized as a bounded context (language + invariants + contracts).

**Canonical contracts ↔ ubiquitous language (DDD)**

- Contract identifiers, field names, and enums are part of the **ubiquitous language**.
- Once released, contract terminology MUST NOT “silently rename” concepts (renames are breaking semantics even if schema-compatible). Use explicit deprecations and compatibility windows.

**Master Doc acceptance criteria ↔ scenarios (BDD)**

- The Master Doc’s “Given/When/Then” acceptance criteria are the minimum BDD layer.
- For critical workflows, teams SHOULD promote acceptance criteria into **executable scenarios** that run in `verify` and in the integration harness.

### 12.2 DDD requirements (minimum practical bar)

Projects SHOULD apply DDD proportionally (DDD is not an excuse for ceremony). The minimum bar for non-trivial domains is:

1. **Ubiquitous language glossary**
  - The Master Doc SHOULD contain a glossary (or link to one) for domain terms that appear in:
    - UI labels and screen names,
    - API routes and schema fields,
    - job types and state machines,
    - analytics/telemetry events.
  - Terms that drive product meaning (e.g., status enums, reason codes, permission names) MUST be treated as **contracts**.

1. **Bounded context ownership**
  - Each bounded context MUST have an explicit owner (team/person) and an explicit **system of record**.
  - Data ownership MUST be enforced:
    - No “backdoor” writes to another context’s tables/collections.
    - Cross-context reads/writes MUST go through the owning context’s public API/event contracts.

1. **Explicit invariants and aggregate boundaries**
  - For each core entity, invariants MUST be stated (and tested) where the system of record enforces them.
  - Aggregate boundaries SHOULD be chosen to keep invariants enforceable without cross-context transactions.

1. **Context mapping for integrations**
  - For external/legacy systems, teams SHOULD use an **anti-corruption layer** (ACL) that translates into the ubiquitous language and shields the domain model from foreign semantics.
  - ACL translations MUST be deterministic and covered by fixtures.

### 12.3 DDD → contracts: commands, events, and state machines

Where the system uses commands/events (HTTP, queues, pub/sub, streams):

- Each **command** or **domain event** that crosses a boundary MUST be represented as a first-class contract surface:
  - schema,
  - semantics/invariants,
  - fixtures,
  - executable checks (schema validation + compat + contract tests).
- Domain events SHOULD be named in the ubiquitous language and MUST avoid leaking internal implementation details (e.g., database field names).
- State machines defined in the Master Doc (jobs/workflows) SHOULD align with:
  - contract envelopes (JobEnvelope/PipelineResult),
  - stable diagnostic codes,
  - and idempotency/cancellation rules in the backend orchestrator.

### 12.4 BDD requirements (minimum practical bar)

BDD is most valuable when it becomes **living documentation** backed by automation.

1. **Scenario naming and traceability**
  - Critical behaviors SHOULD be written as scenarios using `Given/When/Then`.
  - Scenarios MUST be traceable to:
    - workflows (`W#`) and functional requirements (`FR-###`),
    - the contract surfaces they exercise (schema IDs / route IDs / job types),
    - and the verification gate that runs them (`verify`, `smoke`, `compat`, `replay`, `eval`).

1. **Where scenarios live**
  - Repo-local scenarios SHOULD live near the boundary they test:
    - backend: API/job orchestration scenarios,
    - algo: pipeline scenarios (replay/eval),
    - frontend: workflow/UI scenarios (E2E smoke).
  - Cross-repo end-to-end scenarios MUST live in the **integration harness** so they can pin versions and run compat checks.

1. **Deterministic BDD for AI systems**
  - Tier 0/Tier 1 pipelines MUST have deterministic verification paths (replay harness + golden fixtures). BDD scenarios that cover these paths MUST run offline-by-default.
  - If a scenario depends on nondeterministic external services, it MUST be tagged and isolated from the default `verify` path, with an explicit, documented runner.

### 12.5 AI-assisted development: making DDD/BDD cheaper (but still correct)

AI assistance is helpful for producing drafts (glossaries, scenarios, fixtures, boilerplate tests), but it is not authoritative.

- Teams MAY use AI to draft:
  - glossary terms and entity/invariant tables,
  - scenario outlines and edge cases,
  - contract fixtures and negative cases,
  - step definitions and test scaffolding.
- However, the **owner** of the bounded context MUST review and accept:
  - semantic definitions,
  - invariants,
  - and any scenario that becomes a release gate.

### 12.6 Classes, inheritance, and “domain objects” (implementation guidance)

This standard is language-agnostic and does not mandate OOP. However, when modeling domains with classes:

- **Prefer composition over inheritance** for most production code. Deep inheritance trees amplify drift and make AI-assisted change riskier.
- If you use inheritance, it MUST represent a stable “is-a” relationship in the ubiquitous language (not a code reuse trick).
- Avoid shared base classes **across bounded contexts**. Sharing should happen via contracts and adapters, not via coupled class hierarchies.
- Domain model classes SHOULD be:
  - small and explicit,
  - invariant-bearing (validate on construction or on state transition),
  - and testable without infrastructure (no DB/network in constructors).
- Favor explicit “type” / “kind” enums over implicit behavior in subclasses when the behavior is primarily branching logic and when compatibility must be maintained.

# Appendices

Appendices include templates, enforcement tooling, checklists, and selected deep-dive references. The main body remains the authoritative standard; if an appendix conflicts with the main body, the main body wins.

## Appendix A - Boundary enforcement tooling (examples)

These examples are illustrative. Use equivalents appropriate for your language/toolchain. The objective is the same everywhere: **enforce the dependency graph mechanically** so architecture does not rely on memory or code review alone.

### A.1 Python: `import-linter` configuration (layers + forbidden edges)

Key semantic: a `layers` contract is interpreted **highest → lowest**. Higher layers MAY import lower layers; lower layers MUST NOT import higher layers.

Important nuance: real architectures often have **siblings** (e.g., `prompts/` and `tools/`) that should not depend on each other. A single linear `layers` list forces you to pick an ordering between siblings (which implies an allowed dependency). Prefer multiple `layers` contracts plus explicit `forbidden` edges to model a DAG without inventing fake hierarchy.

Example (`.importlinter`):

```
[importlinter]
root_package = algo

# NOTE: The double-bracket sections below (e.g., [[importlinter:contract:layers]]) are import-linter config syntax, not document placeholders.

# Spine: integration depends on evals depends on pipelines depends on core/contracts.
[[importlinter:contract:layers]]
name = spine layering
layers =
    algo.integration
    algo.evals
    algo.pipelines
    algo.core
    algo.contracts

# Pipelines may depend on adapters/prompts/tools (all are “siblings” beneath pipelines).
[[importlinter:contract:layers]]
name = pipelines may depend on adapters
layers =
    algo.pipelines
    algo.adapters
    algo.core
    algo.contracts

[[importlinter:contract:layers]]
name = pipelines may depend on prompts
layers =
    algo.pipelines
    algo.prompts
    algo.core
    algo.contracts

[[importlinter:contract:layers]]
name = pipelines may depend on tools
layers =
    algo.pipelines
    algo.tools
    algo.core
    algo.contracts

# Sibling isolation: siblings must not import each other.
[[importlinter:contract:forbidden]]
name = adapters must not import prompts or tools
source_modules =
    algo.adapters
forbidden_modules =
    algo.prompts
    algo.tools

[[importlinter:contract:forbidden]]
name = prompts must not import adapters or tools
source_modules =
    algo.prompts
forbidden_modules =
    algo.adapters
    algo.tools

[[importlinter:contract:forbidden]]
name = tools must not import adapters or prompts
source_modules =
    algo.tools
forbidden_modules =
    algo.adapters
    algo.prompts
```

Operational notes:

- If `evals` legitimately needs adapters (online eval), model that explicitly (e.g., a separate `eval_online` package) rather than weakening core rules.
- If your graph cannot be expressed cleanly with one contract, add multiple contracts instead of relaxing the rules globally.

### A.2 TypeScript/JavaScript: package boundary linting

Recommended options:

- ESLint boundary plugins (workspace-aware), configured to forbid cross-scope deep imports.
- `dependency-cruiser` rules to enforce allowed import paths and prevent cycles.
- Monorepo tooling (e.g., Nx) module-boundary rules if applicable.

Minimum requirements:

- **No deep imports** across package boundaries.
- **Acyclic dependency graph** at the package level.
- Enforced “public entrypoint only” imports.

### A.3 “No deep imports” guard (minimal, language-agnostic)

Even without a sophisticated tool, you can catch most deep-import violations:

- Maintain an allowlist of package public entrypoints.
- Fail CI if any import path crosses a boundary without using the public entrypoint.

### A.4 Contract validation in CI

At minimum, the `contracts` repo SHOULD provide:

- schema validation (`jsonschema`, `openapi`, or equivalent),
- fixture validation (known-good and known-bad),
- compatibility checks (old fixtures MUST decode under new readers during the compatibility window),
- versioning rules (no silent breaking changes to persisted artifacts).

## Appendix B - Checklists (copy/paste)

### B.1 “Split into a new repo?” checklist

Before creating a new repo boundary:

- [ ] Does this split reduce change scope and improve ownership, without forcing a new runtime service?
- [ ] Can you maintain a **contract hub** with schemas + fixtures + executable checks?
- [ ] Do you have an `integration` harness to run system-level `verify`?
- [ ] Is there a clear Compatibility Mode evolution plan for all surfaces that will cross the new boundary?
- [ ] Is there an explicit owner for the new repo and for each contract surface?

### B.2 Contract change checklist

For any change to a **Compatibility Mode** contract surface (cross-repo, runtime boundary, or persisted artifact):

- [ ] Decision owner approved; the contract surface is explicitly named and owned.
- [ ] Change classified: **additive**, **behavioral**, or **breaking**.
- [ ] If behavioral/breaking: compatibility plan defined (window, versioning/dual-support, rollout + cutover criteria).
- [ ] Fixtures updated (happy-path + representative failures).
- [ ] Producer enforcement tests updated (schema validation + encode/constraint checks).
- [ ] Consumer decode/compat tests updated (old fixtures still decodable during the window).
- [ ] Integration harness checks updated and passing (when downstream integrations exist).
- [ ] Versioning / stability tier / contract registry updated (if your standards use tiers).

### B.3 AI PR checklist

- [ ] Scope is small and stated (files/modules/repos).
- [ ] Boundary rules respected (no deep imports, no new cycles).
- [ ] Contract impact classified (none/additive/breaking + plan).
- [ ] Determinism tier declared and tested.
- [ ] Budgets enforced and recorded (RunManifest/PipelineResult when applicable).
- [ ] `verify` commands provided and executed.

### B.4 Release sequencing checklist (cross-repo)

- [ ] Expand contract in `contracts` hub.
- [ ] Ship tolerant readers (consumers) first.
- [ ] Ship producers emitting new fields.
- [ ] Maintain dual-support for the compatibility window.
- [ ] Contract/remove legacy fields and finalize docs.

---

## Appendix C–N (Externalized)

> The following appendices are intentionally **externalized into separate files** to keep `SPECIFICATION.md` shorter (LLM context window/token efficiency) and to reduce Markdown rendering drift in long documents.
> This section preserves the original appendix headings/anchors for backward compatibility.

Index:
- **Appendix C - Project Master Doc Template** → [`appendices/appendix-c-project-master-doc-template.md`](appendices/appendix-c-project-master-doc-template.md)
- **Appendix D - UI Spec Appendix Template** → [`appendices/appendix-d-ui-spec-appendix-template.md`](appendices/appendix-d-ui-spec-appendix-template.md)
- **Appendix E - Multi-Repo Contract-Driven Standard** → [`appendices/appendix-e-multi-repo-contract-driven-standard.md`](appendices/appendix-e-multi-repo-contract-driven-standard.md)
- **Appendix F - SDMM refactoring & migration playbook (safe change patterns)** → [`appendices/appendix-f-sdmm-refactoring-migration-playbook.md`](appendices/appendix-f-sdmm-refactoring-migration-playbook.md)
- **Appendix G - AI Product Engineering Principles Addendum** → [`appendices/appendix-g-ai-product-engineering-principles-addendum.md`](appendices/appendix-g-ai-product-engineering-principles-addendum.md)
- **Appendix H - UI Design Review Checklist** → [`appendices/appendix-h-ui-design-review-checklist.md`](appendices/appendix-h-ui-design-review-checklist.md)
- **Appendix I - DDD playbook for SDMM + contract-driven systems** → [`appendices/appendix-i-ddd-playbook.md`](appendices/appendix-i-ddd-playbook.md)
- **Appendix J - BDD scenarios + verification playbook** → [`appendices/appendix-j-bdd-scenarios-verification-playbook.md`](appendices/appendix-j-bdd-scenarios-verification-playbook.md)
- **Appendix K - High-Fidelity Visual Interaction (HFVI) Extension: Visual Interaction Spec Appendix (VIS) Template** → [`appendices/appendix-k-hfvi-vis-template.md`](appendices/appendix-k-hfvi-vis-template.md)
- **Appendix L - DAS Tooling Standard (Reproducible Verify + Version Closure)** → [`appendices/appendix-l-tooling-standard.md`](appendices/appendix-l-tooling-standard.md)
- **Appendix M - Doc-family governance and subordinate-doc templates** → [`appendices/appendix-m-doc-family-governance-and-module-doc-templates.md`](appendices/appendix-m-doc-family-governance-and-module-doc-templates.md)
- **Appendix N - Repo-role taxonomy, tool placement, and execution matrix** → [`appendices/appendix-n-repo-roles-tooling-placement-and-execution-matrix.md`](appendices/appendix-n-repo-roles-tooling-placement-and-execution-matrix.md)

## Appendix C - Project Master Doc Template

> **Moved out of the main spec.** See [`appendices/appendix-c-project-master-doc-template.md`](appendices/appendix-c-project-master-doc-template.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and avoid long-document rendering/layout drift.

<a id="appendix-d-ui-spec-appendix-template-v1"></a>

## Appendix D - UI Spec Appendix Template

> **Moved out of the main spec.** See [`appendices/appendix-d-ui-spec-appendix-template.md`](appendices/appendix-d-ui-spec-appendix-template.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and avoid long-document rendering/layout drift.

## Appendix E - Multi-Repo Contract-Driven Standard

> **Moved out of the main spec.** See [`appendices/appendix-e-multi-repo-contract-driven-standard.md`](appendices/appendix-e-multi-repo-contract-driven-standard.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and avoid long-document rendering/layout drift.

## Appendix F - SDMM refactoring & migration playbook (safe change patterns)

> **Moved out of the main spec.** See [`appendices/appendix-f-sdmm-refactoring-migration-playbook.md`](appendices/appendix-f-sdmm-refactoring-migration-playbook.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and avoid long-document rendering/layout drift.

## Appendix G - AI Product Engineering Principles Addendum

> **Moved out of the main spec.** See [`appendices/appendix-g-ai-product-engineering-principles-addendum.md`](appendices/appendix-g-ai-product-engineering-principles-addendum.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and avoid long-document rendering/layout drift.

## Appendix H - UI Design Review Checklist

> **Moved out of the main spec.** See [`appendices/appendix-h-ui-design-review-checklist.md`](appendices/appendix-h-ui-design-review-checklist.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and avoid long-document rendering/layout drift.

## Appendix I - DDD playbook for SDMM + contract-driven systems

> **Moved out of the main spec.** See [`appendices/appendix-i-ddd-playbook.md`](appendices/appendix-i-ddd-playbook.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and avoid long-document rendering/layout drift.

## Appendix J - BDD scenarios + verification playbook

> **Moved out of the main spec.** See [`appendices/appendix-j-bdd-scenarios-verification-playbook.md`](appendices/appendix-j-bdd-scenarios-verification-playbook.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and avoid long-document rendering/layout drift.

## Appendix K - High-Fidelity Visual Interaction (HFVI) Extension: Visual Interaction Spec Appendix (VIS) Template

> **Moved out of the main spec.** See [`appendices/appendix-k-hfvi-vis-template.md`](appendices/appendix-k-hfvi-vis-template.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and avoid long-document rendering/layout drift.

## Appendix L - DAS Tooling Standard (Reproducible Verify + Version Closure)

> **Moved out of the main spec.** See [`appendices/appendix-l-tooling-standard.md`](appendices/appendix-l-tooling-standard.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and make tooling-lock / version-closure guidance consumable by both humans and automation.

## Appendix M - Doc-family governance and subordinate-doc templates

> **Moved out of the main spec.** See [`appendices/appendix-m-doc-family-governance-and-module-doc-templates.md`](appendices/appendix-m-doc-family-governance-and-module-doc-templates.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and make subordinate-doc / headless / package governance reusable across repos. The machine-readable template catalog in `template_catalog.json` maps core doc types to their shipped templates.

## Appendix N - Repo-role taxonomy, tool placement, and execution matrix

> **Moved out of the main spec.** See [`appendices/appendix-n-repo-roles-tooling-placement-and-execution-matrix.md`](appendices/appendix-n-repo-roles-tooling-placement-and-execution-matrix.md).
> 
> Rationale: keep the main standard within a smaller context window for LLMs, reduce token cost, and make repo-role / tool-placement / execution-lane rules reusable without hard-coding monorepo-specific tooling assumptions into every section of the core spec.

<!-- DAS-GENERATED-EDITION-1.5: tools/validate_modules.py -->

<a id="edition-1-5"></a>
## 13. Edition 1.5 normative additions

Generated view. Edit modules/edition-1.5.md and modules/acceptance-1.5.md; never edit this tail independently.

Effect: **normative**. Edition: `1.5.0-beta.1`. Lifecycle: **draft / unpublished content candidate**.

This file is the single author for the new edition's requirements. Chapter 13 of
[SPECIFICATION.md](SPECIFICATION.md#edition-1-5) is its generated reading view.
The pre-1.5 body and existing addenda remain normative; old IDs and conditions
retain their meanings. The module catalog owns assignment and dependency metadata,
not the meaning of these paragraphs. A draft lifecycle does not waive a requirement.

本文明确为规范性正文。“必须 / 须 / 不得 / 禁止”表达 MUST / MUST NOT；“应”表达 SHOULD；
“可以 / 可”表达 MAY，按上下文中明确的适用条件解释。规范性表格中的强制结果亦为 MUST。
标题 S01–S19 是本版变更的稳定导航标签，不是全部叶子要求的数量。

旧格式可读性、采用本版后的合规义务和当前受保护权限分别判断。内容候选可供阅读和
隔离验证，不能据本版 VERSION、目录、签名或自检结果启用未通过准入的工具能力。
公共接口和 MUST 变化的最终兼容裁定仍须在发布前完成；这里不宣称 1.5 是兼容 minor。

本版交付边界如下。S 为本文件的规范章节；O/C 是配套实现责任标签，不是必需产品依赖。
其他实现可提供相同语义和同等证据。不得通过不部署某个指定产品逃避实际适用要求。

| ID | 内容 | 必须达到的结果 | 对应实施条目 |
|---|---|---|---|
| F01 | 规范模块与适用性 | Core、规范模块、领域模块、指南、模板职责明确；依据经核准事实计算 Bundle；未知事实不可自动按不适用处理 | S01–S03；O01–O02；C01–C02 |
| F02 | 规范与机器契约层级 | 对现有 canonical shapes 分类；保留有效语义及已允许的无损映射；精确交换契约具备 schema、语义、正反例 | S04；C03 |
| F03 | 契约缺口修正 | 正式定义新流式路径契约；未知字段按信任边界处理；命名和摘要规则有明确适用范围及迁移路径 | S05–S08；C03 |
| F04 | Agent 零信任最低控制 | 本文件 Z01–Z12 全部具备可执行门禁及拒绝测试；不存在 Agent 可触达的无门禁旁路 | S09–S13；O04–O10；C04–C09 |
| F05 | 变更与完成治理 | 任务意图、修订、尝试、完成周期、候选、验证和目标集成分离；历史追加保留；终态不可普通重开 | S14；O06–O08；C07 |
| F06 | HTTP 契约治理 | 对实际存在的纳管 HTTP surface 明确事实权威、覆盖与身份；生成方向可重建；禁止同一事实双写 | S15；O11；C10 |
| F07 | UI 交付治理 | 对实际存在且受变更影响的工作流，验证结果、恢复行为、设计覆盖和适用无障碍要求 | S16；O11；C11 |
| F08 | 评测与声明资格 | 数据用途与暴露分离；密封评测具备冻结候选、隔离评分、持久预算、受限反馈及追加式处置 | S17；O11；C12 |
| F09 | 元数据与索引闭包 | 状态和版本无漂移；稳定旧条款 ID；附录、模板、schema、fixtures 与完整阅读视图均可追溯 | S03、S18；O12；C01、C14 |
| F10 | 兼容读取与防降级 | 保留声明支持的旧读写接口；v1.5 资格独立校验；旧工具、旧报告与旧政策不能绕过受治理目标 | S18；O12；C13 |
| F11 | 发布与采用验收 | 标准内容、工具实现、参考部署及具体产品采用分别出具证据；正式配套就绪必须有三仓联验与真实隔离测试 | S19；O13；C14 |

[验收与契约交付](modules/acceptance-1.5.md)保留本版 136 个子用例的分母；表中预期行为不是执行结果。

<a id="s01"></a>
### 13.1 建立规范模块，保留既有术语与规范效力

 使用 `Standard Module / 规范模块` 表示规范单元，保留 SDMM Module 的原义。Core 保留采用规则、既有 profile、兼容原则、零信任最低原则及统一 verify 入口。规范模块按职责分为 architecture-modularity、contracts-compatibility、ai-runtime-evaluation、interaction.headless、interaction.standard-ui、interaction.hfvi、governance.documentation、governance.verification-release、security-agent。安全控制正文只在 security-agent 有一处权威定义；其他模块引用适用控制。

Guide 明确 informative；Template 必须逐一声明哪些部分为规范性要求、哪些为示例。`draft` 只描述生命周期，不自动撤销规范效力。不得把现有有效 MUST 移入 informative 文件后使之失效。

Core 的稳定 ID 为 `das.core`，其他模块使用 `das.` 前缀的稳定 ID。语义正文、目录映射和生成视图分别只有一个作者源；目录负责归属与解析元数据，规范正文负责要求本义。粒度较粗的旧 clause 可以作为导航父节点；其可执行叶子要求各有唯一模块归属。跨域旧章节通过父子映射连接，禁止为满足目录树形状而复制 MUST 或改变旧条款含义。

**强制验证边界。** 标准自检核对每个规范来源的效力标记、条款唯一归属和依赖闭包；建立提取前后规范文本/规则强度对照。纯提取提交不得改变适用性或 MUST/SHOULD。发现缺失条款、冲突归属或规范效力空档时阻断发布。

<a id="s02"></a>
### 13.2 依据经核准事实计算适用 Bundle

 保留 `L0/L1/L2` 和三个 interaction profile 的既有含义。另行记录 `componentRoles`、实际交互 surface、产品能力、Agent 可达动作、数据和运行风险。`repoRoles` 继续描述标准/工厂/验证/产品仓等工具生态角色，不与产品组件角色合并。

事实记录必须绑定 scope、来源、确认责任、候选/部署基线和生效政策。Agent 可提交事实提案；独立控制面批准后才进入当前求值。`resolvedModules` 为派生值，不能通过编辑结果文件减少义务。

解析顺序固定为：确认事实来源 → 执行受限声明式规则 → 求依赖闭包 → 计算条款级适用性 → 依据既有 profile 决定相应工程 gate 强度 → 检查不可减免的零信任底线。HFVI 包含适用的 Standard UI 基础要求；混合项目还须按实际 surface 纳入 headless/UI 要求，不能只看主 profile。

采用 `true / false / unknown` 三值事实语义。`not unknown = unknown`；`exists` 只能说明字段存在，不能把存在的 unknown 变成安全否定事实。安全相关 unknown、来源缺失或事实冲突阻断对应资格。风险控制规则采用可证明单调的添加式规则；普通展示筛选可以使用 `not`，不得借此降低安全最低控制。

缺失值先转换为 `unknown`；冲突保留各来源并阻断受影响裁定，不能按字段覆盖顺序取最后值。安全规则中的 AND/OR 采用强 Kleene 三值逻辑，unknown 不等价于 false。单调性约束针对同一已批准规则/政策下增加风险事实的求值；真实能力退役可经独立批准形成新事实快照，并重算受影响证据，不能伪装成普通扫描结果覆盖。与目标无关的 unknown 可以保留，受影响的强制义务未决时不得宣称完整符合。

**求值器的错误边界。** 三值事实是本规范的数据语义；解析器异常、类型错误、超限、插件失效和没有输出属于求值失败，不能自动变成安全否定事实。受影响决定失败关闭；与该决定无依赖关系的独立观察按 S12 处理。原生策略引擎的缺省值、否定即失败或 undefined 不自动等价于 `unknown`。例如 OPA 对部分内置函数运行错误默认返回 undefined，严格错误模式的支持也与执行后端有关。[OPA](#ref-opa)。采用此类引擎时，适配器须显式保留事实状态、错误类别和规则输出，独立通过 DAS fixtures；不要求部署 OPA。

| 受保护输入/求值结果 | DAS 处理 | 禁止的折叠 |
|---|---|---|
| 缺失或已声明未知事实 | `unknown`，追踪影响范围 | 默认补 `false`、空集合或安全值 |
| 来源冲突 | 保留冲突来源，阻断受影响资格 | 最后写入覆盖、任取一个“可信”值 |
| 类型错、无效运算、超限或无结果 | 求值失败，不能产生允许裁定 | 当作“不存在风险”使否定条件成功 |
| 成功求值得到 `false` | 仅表示该规则明确为假 | 自动推断其他规则也不适用 |
| 独立政策均批准同一动作 | 按 S10 取各层约束的交集 | 用某一个 allow 结果覆盖其他层的拒绝/未决 |

**强制验证边界。** 合格验证实现重算 Bundle，并核对事实、政策、规则及解析器身份。模块规则不得执行项目代码或联网。冻结组合 fixtures、unknown/冲突 fixtures、风险增加不能减少控制的性质测试。发现实际能力与声明冲突时不能输出完整符合结论。

<a id="s03"></a>
### 13.3 模块目录、索引与 manifest 的兼容扩展

 首期增加受治理 `standard_modules.json` 与 schema，通过现有 `normativeArtifactRefs` 引用，并进入 `requiredArtifacts` 和发布快照。该目录是模块定义与条款归属的作者源；派生索引和完整视图不得独立编辑。

模块至少具有稳定 ID、title、规范来源、效力、status、activation、dependsOn、clauseIds、requiredArtifactRefs、gate 映射以及引入/修改记录。所有模块共享标准版次，不独立发版。旧章节 ID 保留；需要精确追踪的新增或细分要求登记稳定 requirement ID，并保留父 clause 关系，不能用重新编号覆盖旧语义。

优先保留旧 chapter/clause index 的合法形状，新增模块映射使用 sidecar；确需输出增强索引时使用明确 schema 身份和能力协商。artifact 可以被多个模块引用；唯一性要求针对 ID 及条款作者归属，不应禁止合法共享引用。

叶子 requirement 的完整性同时使用规范文本清单与独立维护的映射基线检验，不能让“目录”和“检查分母”同时从已被删减的索引生成后互相证明完整。新增目录/规则文件经锁定 schema 与解析器读取；`$ref` 只能解析到已锁定工件，禁止校验过程中隐式联网获取新规则。

已有 manifest 的 `conditionalRequirements` 与新目录中的 activation/条款级规则按稳定 requirement 身份映射，登记作者位置、生成方向和适用版次。[MAN](#ref-man)。结构迁移阶段，尚未迁出的规则继续以原位置为作者源；迁出后原位置仅保留由同一作者源生成的兼容视图。两处不得独立维护同一规范条件，也不得以加载顺序、文件优先级或“新目录存在”静默覆盖旧义务。解析器合成全部适用义务；同一义务的冲突、漏映射或无法证明等价的双重定义阻断受影响裁定。标准整体 MUST 的增减仍经规范变更治理，不能借视图生成改变。

**强制验证边界。** schema 校验结构；verifier 检查 ID、引用存在、DAG、效力和发布闭包。新目录的路径、内容摘要、schema 身份进入锁定。旧消费者与新发布包仍需真实兼容测试，不能仅凭“sidecar”推定可用。

<a id="s04"></a>
### 13.4 Canonical Shape 的定义分级

 每个定义显式标注三类之一：`normative_semantic_model`、`normative_reference_contract`、`informative_example`。保留 Reference Profile 的“精确机器表示”含义，采用 Reference Contract 名称，避免继续增加 profile 歧义。

| 对象 | 定义类型 | 本次处理 |
|---|---|---|
| ErrorEnvelope、Diagnostics、Budget、RunManifest、PipelineResult、JobEnvelope、DatasetManifest、EvalReport | `normative_semantic_model` | 保留已有规范语义及无损映射；使用特定工具交换时再绑定其精确 schema |
| AnnotatedContent / CitationSet | `normative_semantic_model` | 保留最低映射、消毒、引用一致性和降级语义；不强制所有实现采用示例字段布局 |
| 现有 StreamFrame | `normative_semantic_model` | 保留 legacy 语义和映射；新精确文本增量契约按 S05 管理 |
| 标准 manifest、registry/report、locks 等已有正式 schema | `normative_reference_contract` | 按其已发布 schema 处理，不降级成可任意改字段的模型 |
| 新授权、证据绑定和受保护完成交换对象 | `normative_reference_contract` | 精确 Reference Contract，含失败行为及兼容 fixtures |

文档分类不得撤销已有 required 字段语义。上述语义模型中的 JSON 展示为 `informative_example`，不据此强制示例字段布局；其中已声明的最低信息义务仍须保留。映射必须同时保存错误、缺省、枚举、身份和安全限制的含义；仅能将对象转成 JSON 不构成无损证明。

**强制验证边界。** 发布时检查定义类型与相应 schema/fixture/映射证据；Round-trip 测试覆盖最低信息义务。规范性字段被映射丢失时失败。

<a id="s05"></a>
### 13.5 精确化 StreamFrame 的路径与增量行为

 新增独立标识的文本增量 Reference Contract，path 使用 RFC 6901 的 JSON string representation，根为最终物化的 PipelineResult；允许写入的路径集合由契约显式声明，通常在 `/output` 下。RFC 允许的 root pointer 不自动取得替换整个对象的权限。

`append` 仅向已存在字符串末尾追加 `text`；`replace` 仅替换已存在且获准的字符串。不存在路径、类型不符、越权路径、无效转义或不支持操作均拒绝；首期不隐式创建对象、不把 `-` 自动解释为数组追加，不暗含 JSON Patch/merge 语义。

按 `(streamId, laneId, seq)` 去重；相同位置的重复帧只有在合同规定的内容身份一致时才可忽略，不同内容视为冲突。正式交换必须选择已锁定的 transport 契约，明确序号起点、后继/缺口判定、游标、重连、缓冲上限及超时；仅规定“单调递增”不足以证明没有丢帧。至少交付一个逐 lane 从 0 起连续递增的参考 transport：缺口未补齐前不能确认最终完成，越限时显式失败或从受信快照恢复。初始化状态和结束时的 lane 水位、受控物化内容摘要必须可核对；结束帧不能单独证明此前增量完整。多 lane 默认只写互不冲突的目标；共享目标需契约声明全序规则。终结后拒绝新增量，已接收帧的相同重传可按既定去重规则确认。

路径授权以解码后的 token 序列及实际 JSON 节点为准，不能用原始字符串的 `/output` 前缀判断权限。只访问 JSON 对象自身成员，不遍历语言原型或执行属性访问器；数组下的 `01` 非法，对象中名为 `01` 的成员可合法存在。参考 transport 只接受已声明的 JSON string representation，不自动解码 URI fragment、百分号或额外转义。独立 fixtures 包含 `/outputX`、`~01`、对象数字 key 与数组索引的区分。

**流全程的资源与提交边界。** 参考 transport 的批准计划同时限定单帧、累计接收字节/帧数、物化字符串大小、lane数、乱序缓冲、总运行时长和重连/重传额度；必要的编码前后计量按合同确定。仅限每帧大小不能限制无限合法小帧。重复帧不重复应用业务内容，但其实际传输/解析消耗仍计量；重连、游标清空或重建客户端不能重置同一受治理操作的历史与额度。检查通过后原子更新物化状态及水位；追加将越限时保留最后一致状态并明确中断，不截断后签发成功。获批新操作的独立预算仍按S10建立。

采用 SSE 时，接收器按原生事件分帧后交给本合同；空行终结事件，EOF处尚未终结的事件不分发。`Last-Event-ID`仅是传输恢复线索，不替代DAS的任务/流/lane/seq身份、权限或完成水位。自动重连受同一操作预算和当前授权约束；HTTP结束、SSE连接关闭或自定义终止字符串，只有经明确应用合同校验后才支持其声明的状态。客户端可展示已验证的中间文本，但业务最终完成仍依赖完整结束证据。[SSE-TRANSPORT](#ref-sse-transport)。本条不要求新增SSE支持。

**强制验证边界。** 新旧契约使用不同 contract identity/协商选择；禁止在同一旧 schemaVersion 下静默重解释 path。旧 dot-path 仅在语法明确且映射无歧义时转换，含有点号的 key 等歧义必须失败或使用项目明确映射。 在可信接收/物化入口核对累计限额、原子水位和应用结束证据；A25.5覆盖小帧累积、重连重放和未完整终结事件。

<a id="s06"></a>
### 13.6 未知字段策略按安全语义分层

 开放的响应、事件和扩展型输出允许忽略未知非关键字段，但仍执行已知字段校验。命令、授权、policy、部署控制配置与影响安全判断的报告 envelope 默认关闭，扩展只能进入显式命名空间且不能自动获得安全语义。已声明 closed 的对象依其契约拒绝未知字段；需要新的关键语义时使用能力协商或明确 critical-extension 规则，旧消费者不理解即拒绝该动作。

接收方必须限制大小、嵌套和解析成本。安全对象拒绝重复 key、歧义类型、未定义枚举和隐式类型转换。允许透传的未知字段不得被中间代理解释成权限。

**Schema 通过的含义。** 精确交换合同登记 schema dialect、词汇表、验证器与配置、格式断言、数值/Unicode 行为和引用闭包。JSON Schema 的 `default`、`readOnly`、`writeOnly` 不会自行实施缺省填充、授权或脱敏；`uniqueItems` 比较数组整体元素，不保证其中某个 ID 字段唯一。[SCHEMA-2020](#ref-schema-2020)。安全入口另行验证跨字段、按 ID 的唯一性及权限约束。必需格式用真实断言或等效语义检查实施，未支持的必需词汇/方言拒绝，不能降级成“忽略未知关键词”。

解析、schema 校验和语义裁定使用同一份经验证输入。禁止验证后重新解析未固定的原文，或由下游库悄悄插入默认值、删除字段、强制转换类型后执行不同含义。合同明确允许的映射在固定版本的边界完成，保留原始输入与映射身份。历史格式仍按已承诺规则读取；上述新受治理语义不通过全局修改旧 schema 静默实现。

**有界归档和批量材料输入。** 包、缓存、候选输出和批量证据在解析/解压前确定支持格式、成员类型和资源预算；消费中同时约束实际传输字节、展开后累计/单项字节、成员数量、路径长度/深度及 CPU、内存和截止时间。声明长度、压缩比、签名正确或 `Content-Type` 均不替代实际消耗计量。未支持的嵌套压缩拒绝；批准的嵌套层级共享同一外层预算，不能每层重置计数。

参考接收器在与候选和受信安装目录隔离的新暂存区物化，规范化后的重复成员、跨平台路径碰撞、未批准链接/特殊文件及文件—目录类型冲突直接拒绝，不接受后到成员覆盖前者。安全关键拒绝不得被“记录 warning 后跳过”降为完整包成功。只有全部必需成员、格式完整性、清单和摘要校验完成，才按受保护发布协议把材料登记为可消费；解压中断或超限后的部分目录不能参与验证或激活。所需链接或原生归档功能可经精确合同及隔离测试批准，默认不扩展权限。[ARCHIVE-SAFETY](#ref-archive-safety)。

采用HTTP承载安全命令时，在JSON/schema之前先建立无歧义的消息边界。网关、代理、协议转换及资源处理器对实际请求目标、权限相关头和消息体必须一致；未完整或有歧义的有界授权/完成消息不能先执行副作用。分帧一致性及原生HTTP允许的归一化遵从S15；明确批准的逐帧流式操作仍按S05/S10逐单元控制。

**JSON 输入与运行时对象的一致性。** 新安全契约在会丢失信息的宿主对象构造之前，按解码后的精确成员名检查重复项，并执行对应对象的大小写敏感字段规则；`action` 与 `Action` 在 JSON 中是不同名称，关闭对象未声明后者时应拒绝，开放数据字典仍保留合法的不同名称。转义后相同的 key 不能以不同原文绕过去重。每个有界消息/帧只接受合同规定的一个完整 JSON 值及允许的空白，禁止读取首个值成功后忽略第二个值或垃圾尾部；流式协议在各自明确帧边界验证，不等待整个长连接结束。

字段的缺失、`null`、零、`false` 和空集合分别按 schema/语义判断。解析时不得把前一请求对象的旧字段、未定义默认值或部分错误结果带入本次决定。无效 UTF-8、孤立 UTF-16 代理项及超出字段可表示域的数值，在安全判断前明确拒绝；禁止先替换字符、浮点舍入或整数溢出再校验。序号、额度和代次的解析、比较及加法均须精确且检查界限；允许的字符串表示遵从具体合同，不能全局改变旧数值字段。Go `encoding/json` v1 的大小写匹配、替换无效字符和浮点解码等行为需要适配层补足；`DisallowUnknownFields`、`UseNumber` 或换用另一库均不单独证明以上全部条件。[JSON-RUNTIME](#ref-json-runtime)。安全入口使用同一经过验证的值及明确映射执行，原生签名字节仍按 S08 保留。

**YAML 配置的精确接入。** 采用 YAML 承载事实、policy、gate 或部署配置的入口，登记实际版本、解析器/标量解析规则、标签、文档数量及到受治理对象的映射。新的参考安全配置限定为单文档、字符串 key 和合同明确的标量类型；默认禁用 merge key、自定义对象构造、循环 alias 及未批准的 alias 展开。引用/合并功能确有需求时，必须有独立批准的确定性展开、冲突处理、成本上限和无损映射，展开也不能形成重复语义字段或绕过权限。YAML 规范允许的图结构和非字符串 key，不自动进入这个受限配置合同。[YAML-PROFILE](#ref-yaml-profile)。

重复 key、标签和标量类型须在构造成可能覆盖或合并键值的宿主 map 前检查；布尔值、数字、日期和字符串不能凭某个 loader 的默认规则悄然互换。`safe_load` 只承担其明确的构造限制，不表示已完成 schema、唯一性、资源和权限校验。版本指令、锚点和多文档输入不能临时切换已批准解析规则。历史 YAML 保留原生读取及有记录的兼容 mapper，升级由 S18 管理，不通过全局替换 loader 重解释历史事实。

**强制验证边界。** 对新安全契约在 parser/schema 层强制拒绝；旧契约不追溯重解释，增加独立接入适配和兼容窗口。禁止把历史合法开放字段一律按“安全修复”删除。 授权、验证、索引和参数消费使用一致的字段/类型规则；解析失败后的部分对象不得进入状态写入。解析器或配置升级须重跑差分与兼容 fixtures，不能以序列化后相同或库未抛错代替原始输入合规。

<a id="s07"></a>
### 13.7 明确 camelCase 的边界与原生格式映射

 DAS 自有的 canonical JSON 字段继续使用 camelCase。外部协议、遗留和法规指定格式可保留原生命名，通过有记录、确定性且不丢失语义的适配边界进入系统。动态数据 key、用户内容、HTTP header 名等不得被误当作 DAS schema 字段统一改名。Protobuf 现有规则保留，不制造第二套相反映射。

**强制验证边界。** 契约 inventory 标注格式所有者与 mappingRef；字段碰撞、大小写折叠丢失和不可逆转换失败。不得借外部例外改写已经发布的 DAS 自有字段。

<a id="s08"></a>
### 13.8 区分原始字节摘要、语义摘要与来源证明

 文件/制品完整性采用明确字节流的摘要；新跨语言 JSON 语义摘要采用 RFC 8785 JCS + UTF-8 + SHA-256，绑定 contract identity 与 canonicalization 方法。明确拒绝不符合该契约的重复 key、非有限数值和无效 Unicode；大整数或高精度金额等使用契约规定的字符串表示，不能静默四舍五入。JCS 不进行 Unicode 归一化，禁止额外“修正”输入。

签名/授权 envelope 与被摘要 payload 分开，避免循环。RunManifest 不嵌入自身 manifestHash 的规则保留。旧 manifestHash 的输入定义保留；方法变更使用独立字段/对象或新契约，不复用原名伪装相同含义。

这里的 JCS 摘要标识同一契约下的规范化 JSON 值，不声称证明任意业务语义等价。安全关键的契约身份、消息用途、受众及绑定字段必须处于已签名载荷内；使用已选 envelope 的明确签名输入编码，不能仅签 reportDigest 后信任未签名的 policy 或 task 字段。引用图按照 Task → Candidate → Verification → Integration → Completion 的依赖顺序构造，后产生的证据不得进入前一对象的自身摘要。发布包的外部摘要/签名同样与包内被摘要内容分离。

**摘要层与签名层分工。** JCS 仅用于合同明确指定的 JSON 语义摘要/序列化；原生签名协议先按其精确算法验证原始签名字节。采用 DSSE 时，签名输入为协议定义的类型与 payload 的 PAE 编码；验证通过的同一 payload 才进入应用解析，不能先重排 JSON 再验签，或验签后重新从另一份 envelope 取值。DSSE 的 key ID 只是选钥提示，不能单独决定可信身份；有多签要求时按不同受信密钥及批准主体关系计数，重复签名不增加批准数。[DSSE](#ref-dsse)。外层协议的扩展规则与内层安全 payload 的闭合规则分别执行，不擅改既有协议。

使用证书或无长期密钥的签发方案时，消费端仍须核对受信 issuer、批准的签发身份/工作流、用途、候选与制品摘要、签发时间依据及当前资格政策。透明日志包含记录或证书链正确只证明相应来源事实，不能代替授权、测试执行或业务完成。[SIGSTORE](#ref-sigstore)。已有 Cadence envelope 能满足上述语义时直接复用；DSSE/Sigstore 是可选映射，不增加第二套必需签名平台。

**令牌型适配的互斥验证。** 某个已选授权或证据适配器使用 JWT/JWS 时，必须为访问授权、身份登录、验证证据及动作回执定义不可混用的接收规则。入口从受保护配置选择协议、允许算法和 issuer—key 绑定，校验预期受众、主体、消息种类、必要声明及 S12 时效；不能以“同一组织签发”或成功 decode 代替这些规则。`typ` 可承担显式类型的一部分，单查 `typ` 仍需其余互斥规则。未选用 JWT 的部署无需新增 JWT 依赖。[JWT-BCP](#ref-jwt-bcp)。

`kid` 只在获准 issuer 的受保护密钥集合内作为有界查找键，不能拼接 SQL、文件路径或执行命令；`jku/x5u` 等地址不得触发按不可信消息自动联网。需要密钥刷新时，只访问当前批准的提供者及端点，经 S10/S13 的目的地、重定向、时效和披露检查更新受保护缓存。用于可携带签名证明的 DAS 证据路径拒绝无签名、错误算法、错误密钥类型和算法混淆。仅受本地认证通道保护的记录使用其明确合同，不能标成已经具备独立可携带签名。

**经 HTTP 获取材料的摘要域。** 每个被验证摘要须明确其对象、算法和字节边界：原生消息 content、选定 representation、获准解码后的工件或语义对象不能混用。采用 RFC 9530 时，Content-Digest 对应本条消息的 content 字节，Repr-Digest 对应选定 representation 的数据；例如单段206的 content 摘要仅覆盖所传部分，不能当成完整 representation 的摘要。HTTP transfer coding 的分帧字节不混入 content 摘要，Content-Encoding 的实际编码字节也不能被客户端自动解码后无声替换。[HTTP-DIGEST](#ref-http-digest)。摘要可信来源来自批准绑定或受信证明；服务端同时提供数据和一个相符 hash 不独立证明来源或任务适用性。

下载器须记录实际获取视图与工件合同的映射。依赖原始编码摘要时，对自动解码前的原始字节视图计算并完成校验，按计划保留必要原始材料；解码可以在受限暂存域流式执行，但其输出不得提前取得可信身份。不能把已解码内容重新 gzip 来重建“原始响应”。工件合同若固定解码后字节，则另行校验该域的最终摘要、大小和批准转换，不能拿部分 content 的摘要冒充完整工件摘要。HTTP 头部、trailer、原生签名与最终文件各按自身合同校验，必需 trailer 未到达时不发布可信完整工件。未使用原生摘要头的来源，可以按已有锁定工件摘要全量获取，不强制新增协议头。

**强制验证边界。** 摘要方法必须可识别；未知算法/方法拒绝用于安全决定。跨语言 known-answer fixtures 比较字节和摘要；签发身份另由 S12 校验。

<a id="s09"></a>
### 13.9 增加 Agent 零信任与可信计算基要求

 标准规定 Z01–Z12；Agent 与其生成产物均为不可信输入。可信计算基必须明确资产、owner、更新权限、版本/摘要、运行身份和失陷后的停止条件。Prompt、AGENTS.md、同一模型的第二个角色、工作树、租约与“审查过”声明均不能独立证明隔离或授权。

Agent 不得写入当前控制面政策、信任根、受保护验收基线、证据签发器和发布保护。Agent 可以提交这些对象的变更提案，须独立批准并形成新政策身份。

初始信任根由有权维护者在 Agent 可控执行之前，通过独立安装/管理通道建立；仓库附带的 key、根证书或 `approved: true` 都只是输入。信任根、政策、验证器、验收实现和部署权限的变更，须由当前有效控制面授权、用当前受保护验收检查，形成新身份后原子激活。不得以候选自带的新规则证明其有权替换旧规则。切换时处理在途请求、旧代次、凭据撤销及恢复边界；批准人和执行 Agent 的独立性按真实控制关系判断，换账号、换模型或换进程不自动构成独立。

所有受保护写路径纳入部署清单：Git refs、tags、发布包、完成状态、CI/check 状态、对象库、管理 API 及其旁路凭据。可运行旧 CLI 不构成失败；旧 CLI 能改变这些目标或伪造目标接受的证明即构成失败。信任根防回滚与过期检查可借鉴 [TUF](#ref-tuf) 的机制，具体采用不以完整 TUF 部署为强制依赖。

**强制验证边界。** 受治理执行前验证部署能力与信任根。缺少隔离/授权能力时允许安全的只读诊断，不允许默认为具备零信任执行能力。A02–A08、A17、A32 必须实测。

<a id="s10"></a>
### 13.10 受保护动作的授权与副作用门禁

 有效动作权限为组织/项目政策、任务边界、委派范围、工具政策、资源政策、所需批准及当前运行能力的交集。绑定主体、目标、具体动作和参数、期限、授权代次、预算与幂等键。未授权默认拒绝；委派只能衰减；实际副作用入口逐次校验。

提交候选、修改保护分支、关闭任务、修改关键配置和生产发布分别授权。长任务定期检查撤销，并在每个受保护写入点重新检查。外部系统无幂等保证时，必须记录已知成功/失败/结果未知和恢复步骤，不能宣称通用 exactly-once。

发生委派时，控制面保存有效授权依据的父子关系；执行点核对当前行为主体、获准代表的主体、祖先授权有效性及衰减后的资源/动作/参数/用途/期限/额度。子授权不得超出任一有效祖先的限制，续期不能延长已失效的上游权限；父授权撤销确认生效后，其派生授权不得继续支持新动作。委派层数、大小与求值成本有界；首期可以限制层级，未支持的再委派直接拒绝。额度在共享祖先及实际业务归属上原子约束，不能为每个子令牌复制完整预算。该授权依据由受保护授权服务求值，不能把客户端附带的角色历史或 token 中仅供审计的 actor 链当作权威。

资源授权针对受控解析器最终确定的资源域、租户、对象、动作及参数约束；入口保留原始请求与规范化结果的绑定。路径/别名解析、adapter 参数转换或重定向若改变实际资源或请求含义，须重新检查批准范围；只批准域名、字符串前缀或初始 URL 不授予该服务全部对象的访问权。拒绝有歧义的多次解码与未批准目标，不利用网关自身较高权限代替调用者的授权。

受保护资源身份须区分对象的持续存在与删除后的同名重建。内部 resourceId 在其权威域内不重新分配；外部服务仅提供可复用名称/编号时，通过受保护映射绑定提供者、租户及可验证的对象创建实例，必要时分配本地不透明身份。名称、路径、内容摘要及可重置版本号均不能单独证明实例连续性；创建实例与同一对象的内容版本、授权代次分别保存。对象实例退役或映射改指另一实例时，依赖旧实例的当前授权、Decision、待发送请求和缓存关联失效，实际入口须重验；历史记录保留原绑定。无法区分实例时，停止依赖旧实例绑定的动作，须先建立可验证的当前实例绑定并重新批准；所需连续性仍无法证明的组合标为不支持。新实例登记不得重置同一业务义务的预算、已执行事实或未知结果；连续改名且实际对象未变时保留对象身份，涉及授权路径/用途变化仍按本条重新检查。

授权授予和结果回执分别校验：Action Receipt 证明某动作的执行事实，不能直接作为后续动作的授权。策略中分别保存 authority epoch、授权代次、协调 lease generation 和目标版本；这些值承担不同职责，不能共用一个笼统的 epoch。资源入口定义实际副作用的线性化点：在该点之前撤销或代次变化的请求必须拒绝；此前已经线性化的动作如实记录；是否需要且能够补偿按业务合同和当前独立授权判断。合法已提交动作不因稍后撤销自动回滚，不可逆副作用不得伪装为补偿完成。外部资源无法直接检查 fencing 时，可以由可信单写网关封闭直连凭据并串行化准入/发送；是否满足目标提交的 fencing 仍须按该资源合同实测。连所需等效边界也无法建立时，该动作标为 unsupported。

业务动作身份、请求指纹与授权实例分别保存。受保护业务唯一键为 `(authorityDomain, resourceId, actionClass, businessActionId)`；`businessActionId` 由批准计划或受保护状态分配、与业务义务绑定，客户端幂等键只能作为其别名。参数摘要、任务身份和经认证的原始发起主体属于不可变请求指纹，不能放进唯一键来容许“同键改参数”创建新动作。当前执行/恢复主体独立记录并逐次认证；接手者不得伪装原主体，也不得把自身身份覆盖进已登记指纹。policy、authority epoch、授权代次、lease generation、attempt 与令牌轮换均不得重置该业务唯一键。

同一业务动作、相同请求返回原结果或执行中/未知状态；不同请求指纹拒绝。返回历史结果仍须具有当前读取权限。能够证明尚未执行的动作可以经新的有效授权继续，接手记录关联同一业务动作、原始指纹与当前执行主体；已执行或结果未知时，更新授权不能使之重新执行。交接只传递状态引用，既有令牌、批准和租约不会随引用自动转移；接手者须取得自身所需授权及协调资格。真正的新业务动作须独立满足任务义务、批准及共享预算约束。限额执行前原子预留，超时不自动退还可能已使用的额度。去重保留期必须覆盖仍可能到达的请求、回调和重试；期满请求明确失效，不得自动当成从未执行。

资源合同必须区分网关准入、不可撤回发送和远端实际提交。仅写入意图或排入 outbox 尚未产生外部副作用，撤销后不得继续发送；实际发送前再次核对当前授权。已在撤销前获准并不可撤回发出的请求可能晚于撤销产生远端结果，按在途动作核对，不能保证远端瞬时停止。需要“远端提交前撤销必拒”的动作必须有目标侧条件提交/fencing 或经实测的等效协议；单写网关本身不自动提供这个保证。无法满足目标所需语义时标为 unsupported。晚到的可信回执可用于归档真实历史及恢复核对，不能自动授权新的副作用、集成或完成。

**远端条件与重试的实际语义。** 对依赖目标基线的 HTTP 变更，适配器须证明条件在实际产生副作用的目标执行点检查。采用 `If-Match` 时保留源站原生强比较语义；`W/` 弱标签不能作为匹配强条件，`If-Match: *` 只表达当前存在性，不能代替预期版本。表示摘要可在 A→B→A 时重现，需要历史代次或对象创建实例的控制继续按 S10/S14 另行绑定；不能把普通 ETag 声称为唯一事务代次。[HTTP-SEMANTICS](#ref-http-semantics)。不支持原子条件的目标不具备该 CAS 保证；可提供与声明相符的受控动作，但需要 CAS 的集成/发布路径保持关闭或使用经证明的等效资源入口。

HTTP `202 Accepted`、队列入队、SDK 正常返回分别按远端合同记录为受理或发送事实。受理之后的失败、取消和结果未知仍须保留；实际完成凭绑定业务动作的终态结果、目标状态或可验证回执确认。状态查询/轮询与取消请求各有当前授权、目的地和有界额度，响应中的状态地址不直接授予访问权。非成功状态及网络超时不能单独证明没有副作用；条件失败可以按提供者的精确语义核对，不能自动换基线、换动作键继续执行。

SDK、HTTP 客户端、代理、任务重投和业务层的重试共同进入同一批准执行计划。计划固定实际尝试上限、累计时限、退避/抖动、可重试错误、幂等保留期及结果未知核对方式；内层默认自动重试必须关闭，或通过已证明受治理的钩子/资源入口使每次实际发送受当前授权和限额控制。[RETRY-PRACTICE](#ref-retry-practice)。业务副作用额度与传输尝试/资源消耗按已批准口径分别记账，合法同键重传不重复扣同一已预留业务义务，也不免费复制网络或评测额度。幂等键、请求指纹及资源实例不因重试变化；仅有相同键而远端保留期已过，不足以继续重发结果未知的动作。

**操作参数到实际程序的边界。** 受保护执行器把获批操作映射到固定程序/API、子命令及参数语法；结构化参数或无 shell 启动仍须防止目标程序把候选数据解释为新增选项、响应文件、配置/插件加载或其他未批准行为。选项、操作数、标准输入、工作目录和环境均绑定到本次获批调用；真实 parser 的归一化若改变动作或资源，须重新核对权限。`--` 仅在对应程序/子命令明确支持时用于结束选项，不能假定所有工具对 `-`、`@file`、路径及 URL 有相同含义。[PROCESS-ARGUMENTS](#ref-process-arguments)。合法特殊字符数据可通过支持的定界/API表达；无法无歧义表达的组合拒绝，不开放任意 extra-args 兜底。

**异步取消与实际终结。** 调用方停止等待、发出取消请求、本地运行域终止和远端业务终态是独立事实。超时、Future/Task 被取消、连接关闭或取消 API 返回成功，只有在其明确合同覆盖的范围内才支持相应结论；它们不能单独证明底层线程、子进程或已经发出的远端动作未执行。发生交接或异步派发前，持久动作身份和必要预留按 S13 生效；监督服务独立于调用会话跟踪实际执行及迟到结果。不能证明未发送/未执行时保持结果未知和原预算/去重关系，按 O10 核对，禁止重建动作或自动退款。[ASYNC-CANCELLATION](#ref-async-cancellation)。

取消后不得再产生未获当前授权的新业务发送；已不可撤回发送的结果按原边界记录。清理、轮询、补偿及继续执行各按实际行为取得所需授权，受保护 supervisor 的本地安全停止继续遵从 S13。需要证明运行终止时，以 S11 的整个运行域为准；未终止的写入者和未知清理结果不得被隐藏为已完成或环境可复用。异步框架中保留工作的机制须由有界监督登记和截止管理，不能用无限屏蔽取消或脱离管理的后台任务绕过停止。

**强制验证边界。** 权限校验位于不可由 Worker 绕过的实际资源入口；逐次核对规范化目标、当前主体、有效授权依赖及共享预算。权威不可达或授权关系不明时拒绝相应动作；令牌不进入 Git、日志和任务文档。批准、防重放与状态提交采用原子校验/预留及可恢复记录。 适配器登记原生条件/状态/重试映射，入口计数实际发送并核对终态；不得仅按 HTTP 2xx 或客户端调用次数计作完成和预算。 在实际程序启动前核对参数解释及授权绑定，取消/超时之后由独立监督器维护同一动作的发送屏障、终态和预算。

<a id="s11"></a>
### 13.11 独立验证、执行隔离与验收基线保护

 独立 verifier 针对不可变候选执行已批准检查，使用受保护工具和规则。可信验收选择不受候选自改 gate、skip 标记或测试删除控制。候选测试仍可提供有价值证据，但关键验收需已有受保护测试、独立审查或明确批准的补充测试支持。

执行候选代码的 runner 与裁定/签发器分离；runner 不持有发布和签发凭据。网络、文件系统、进程、设备、环境与资源限制必须实际生效。报告中区分检查执行事实、业务要求覆盖与人工判断。标准不要求将设计质量等定性判断伪装为自动布尔真理。

验证运行的批准计划同时限定实际服务/租户、测试账户、数据域、允许读写、出口、额度，以及初始化和清理动作。HTTP、UI、评测及其探针默认使用隔离测试资源；“测试”“GET”或“非管理员”标签不免除实际资源授权。需要访问真实业务资源时，读取、状态变更、费用及信息披露按其实际语义取得 S10/S13 的当前独立授权；允许由受控低风险政策预批准。验证用途的 Decision、本地 runner 权限或测试计划通过，均不自行授予这些业务权限。负向探针只能使用获准的受控目标。

远端测试初始化、重置、删除测试数据等清理操作遵从相同资源边界、幂等、额度与结果未知规则；不能借清理脚本扩大账户权限或重试未确认副作用。清理自身的结果与测试断言分别记录，未决清理若影响隔离、环境复用或任务完成，则阻断对应资格。本地隔离/终止仍按 S13 的有界安全停止执行，外部业务补偿需独立授权。

进一步区分不可信候选执行域与受信测试驱动/观察域。用于 Z01–Z12 的关键断言须由候选无法修改、调试、注入或冒充的检查器产生；只读测试文件、不同进程名及同 UID 的独立进程均不足以证明隔离。与候选共享可污染解释器、进程或可写结果目录的单元测试可以提供辅助证据，不能单独满足安全关键断言。共享地址空间导致无法建立独立观察时，安全关键运行断言须改用候选不可控制的域外实测；无法建立该边界则相应能力不受支持。受限静态分析和独立受权审查可以证明各自明确的工程要求，不能代替 Z01–Z12 所需的运行隔离、授权拒绝或不可篡改实测。

启动器在候选域外验证实际镜像、身份、文件描述符、挂载、网络与进程边界；每次运行绑定配置，关键变化使旧环境证据失效。构建器、HTTP/视觉 runner、评分 adapter 也遵守此边界。真实负向测试须有可达性/正向对照，证明受测代码确实执行；“命令没启动”或“探针本身报错”不能计作成功拒绝。受保护来源证明的原则可参照 [SLSA build requirements](#ref-slsa)，这里不声明满足某个 SLSA 等级。

构建后才产生的安装包、镜像或其他交付物，须以独立输出清单绑定实际输入候选、构建器/配置与精确输出字节，并针对实际交付物取得适用验证。输入候选不包含未来输出的摘要；输出证明在构建完成后产生。发布时重新构建所得的新字节不得沿用旧输出证明。来源绑定只说明产物从何而来，仍须满足其行为验收；不要求所有业务构建天然逐字节可重复。

运行终结以受控执行域为单位确认。主进程退出或超时不证明其后代、后台线程/任务、继承句柄及待发送请求已停止；所有候选进程须留在可管理的运行域，CPU/内存/进程数及相关输出额度按域聚合。域外 supervisor 确认写入者已退出或被不可绕过地隔离，再冻结输出、结束采集并回收环境。无法确认终结或清理时保留异常/待核对状态，隔离该环境，不签发相应完整运行成功或释放可能已消耗的预算。受保护资源上已发出的动作继续按 S10 核对，不以杀死本地进程推定外部动作已撤销。

**CI 身份和不可信工作流。** 候选中的 CI YAML、复用 workflow、测试脚本和依赖安装步骤属于候选输入。受保护签发/集成 job 只能运行已批准版本的控制代码，不能在持有写权限或签发材料的上下文检出并执行待验证 PR；跨 workflow 传来的 artifact 仍按来源和原始运行身份核验。测试 job 使用其获准测试资源和隔离域；签发 job 不直接信任上游文件名、退出码或自由格式 JSON。Action/workflow/镜像等执行材料固定到经审查的不可变身份，并限制令牌权限、共享缓存与工作目录。GitHub 官方资料中的 `pull_request_target`、`workflow_run` 风险是此边界的实施例证，不要求所有项目使用 GitHub。[CI-SECURITY](#ref-ci-security)。

**源树、物化视图与发布产物。** 候选身份同时确定纳管源对象清单及实际执行/检查视图。Git 的 committed tree、工作区、`git archive` 和构建输出各有不同内容语义，不能只凭同一 commit 标签认定它们逐字节相同。Git `export-ignore` 可省略文件，`export-subst` 可改写内容；归档成功或归档摘要固定不足以证明源候选完整。[GIT-SNAPSHOT](#ref-git-snapshot)。

快照入口从受控导入的原始对象树/已冻结内容生成独立清单，核对受影响源文件、任务/文档、配置、测试、模式和必要外部材料；物化与构建变换登记批准规则、工具/配置和输入输出摘要。源码包按批准规则排除发布不需要的文件可以合法，但完整验收候选及义务分母不随 `export-ignore`、稀疏工作区或安装包精简自动缩小。需纳管的 dirty/untracked 内容必须先显式冻结或拒绝缺口；秘密、非纳管缓存和本机状态不得因追求“全目录”被自动上传。

不可信来源提供的 `.git`、配置、hooks、attributes 外部命令和对象替换/外部对象引用均属于受审查输入。受治理执行器不在此类 `.git` 中以高权限运行 Git，不通过更改所有权或 `safe.directory=*` 授予执行信任。必要的导入/读取在无秘密低权限域完成，只向受保护候选库发布校验后的对象、清单与批准物化结果；递归子模块和 LFS 获取继续逐项校验目的地、提交及实际字节。这里只要求可信快照边界，不要求替换 Git 或建立完整仓库托管平台。

**容器材料与实际执行实例。** 选用 OCI 镜像时，运行绑定同时覆盖获准 index（如存在）、实际选中的子 manifest、平台条件、config、按顺序应用的层以及实际启动/挂载配置。固定多平台 index 不能单独证明某个运行使用了已验证子镜像。原生 descriptor digest 对应原始对象字节；压缩层摘要与 config 中未压缩层的 diff_id 分别验证。[OCI-IDENTITY](#ref-oci-identity)。运行前核对实际选择，不让调度、缓存、仿真或回退静默更换平台/子工件；新增获批组合需要对应证据。

只要求获取并验证本次执行所依赖的闭包。未选中的可选描述符按原生协议处理；不能因 index 中存在未选的未知 mediaType 就把原本合法的 index 判成格式错误。选中/必需对象无法解析或验证时，该组合保持 unsupported。层间覆盖及 whiteout 是 OCI 的原生变换，按受控层顺序解释；普通证据归档的重复路径拒绝规则不跨层误用。单层自身的重复条目、越界路径及未获准特殊文件仍按对应协议和运行权限拒绝。最终 rootfs 上的挂载和注入配置同样进入执行身份，镜像签名不覆盖未绑定的宿主挂载内容。

**系统调用通知的能力边界。** Linux 适配器若使用 seccomp user notification，不能以“读取候选内存中的路径并返回 CONTINUE”作为资源授权的唯一执行点；候选线程和共享状态可能在核验后变化，notification ID 有效也不证明参数内容固定。[SECCOMP-NOTIFY](#ref-seccomp-notify)。真正的拒绝边界来自候选无法绕过的内核/文件/网络限制及受权资源入口。需要代理动作时，代理对自己持有的受控参数和资源句柄重新鉴权、独立执行并返回有界结果，候选自身的对应直连能力保持受限；不能借通知通道继承代理的通用权限。本条限定所选机制的保证，不要求部署 seccomp 通知或另一套沙箱产品。

**准备阶段属于代码执行面。** 不可信源码的依赖解析、包元数据准备、动态构建需求、生成步骤、测试发现/收集和插件初始化，均可能执行候选或第三方代码。纯静态读取保留为低权限有界解析；需要动态钩子时进入已批准隔离域，固定输入、后端/插件、网络目的地、依赖及输出，不继承审批、验证驱动、签发或资源管理权限。`dry-run`、`collect-only`、虚拟环境及构建依赖隔离都不单独证明安全隔离。[PYTHON-BUILD](#ref-python-build)、[PYTEST-DISCOVERY](#ref-pytest-discovery)。

动态生成的元数据和收集结果仍是待核验输出；不得在可信控制进程中再次导入候选以确认它们。构建依赖和运行依赖分别固定，后端动态要求的工具、in-tree backend及传递依赖进入实际材料闭包。发布包元数据中的可用版本范围可以保留；受治理构建实际选中的包/来源/摘要必须可重建。包 hash只证明其指定内容一致，不能授予构建钩子控制面权限。

**挂载的实际拓扑与写入能力。** 所选隔离组合须核对实际挂载视图，包括嵌套子挂载、传播关系、宿主写入者、共享卷和获准可写 scratch。顶层只读标记不证明所有子挂载只读，也不禁止宿主侧仍有权限的主体修改其底层文件；镜像摘要不能覆盖后来挂入的可变内容。[MOUNT-TOPOLOGY](#ref-mount-topology)。纳管候选与受信验收输入须在运行期间保持获批内容身份；只读映射仍需不可变快照或覆盖全部相关写入者的保护，不能等运行后发现摘要变化再追认此前结果。

参考部署可以排除未批准子挂载，或采用实际支持的递归只读与受控传播机制；遇到不支持的组合明确拒绝，不静默退化为部分可写。已批准输入更新须形成新的绑定及相应运行，动态业务测试数据按 S11 的资源合同单独管理。此要求不统一指定内核版本、容器产品或全局禁止挂载；受保护范围之外的合法可写输出继续可用。

**强制验证边界。** 可信 runner 配置禁止宿主回退，清洗环境/工作目录/插件来源；对验收文件和 policy 变更单独审批。启动前核对实际测试目标、账户及允许动作；远端初始化和清理同样经过实际资源入口。独立签发器从受控执行元数据和原始工件构造证明，不签署 Agent 提交的任意 PASS 文本。 导入器以独立清单核对原始源树、获批物化视图与实际 runner 输入，未解释差异及不可信仓库元数据进入特权域均阻断。 启动及关键挂载变更时核对实际拓扑与有效权限，受信输入的任何未批准可写别名或漂移阻断该运行的有效证明。

<a id="s12"></a>
### 13.12 证据绑定、可信签发与完整覆盖

 原始 verify report 保持原有作用域；受治理合规决定另外绑定以下最小信息：

| 绑定域 | 必须能确定的信息 |
|---|---|
| 身份与版本 | 契约身份、schema 版本、签发者、受众、验证器/适配器及规则制品身份 |
| 被验证对象 | authorityDomain/scope、完整 taskKey、定义修订、completion cycle、候选摘要、必要目标基线 |
| 决策上下文 | 标准制品摘要、政策摘要、批准验收计划及 required-for-action 槽位/聚合集合摘要、Bundle 及事实摘要 |
| 证据 | 原始报告与制品摘要、执行身份、计划槽位与原始运行/来源结果关联、运行环境及适用人工审查引用 |
| 时效与防重放 | 签发/有效期、独立 authority epoch 与授权代次、签发 ID、运行/attempt 关联及按消息用途定义的重放约束 |

字段布局通过已有 Cadence envelope 的无损映射或经治理扩展实现；不得强行塞入闭合的旧 report 对象。消费端验证可信来源、摘要与上下文，不能只验证签名数学正确性。签发密钥和受众规则来自控制面，禁止接受候选自带信任根。

完整资格必须满足所有适用 blocking 要求、必要 source-of-truth 制品和声明覆盖。`expected` 记录本次报告预期执行的检查，不独立决定某动作的必需分母。对已批准 required-for-action 中的必需槽位，没有满足批准执行/复用规则的有效结果、结果不满足批准判定规则或必需制品缺失均阻断该动作资格，报告填写 `expected=false`、`report_only` 或更改 `failureOnNoResults` 不能解除该义务。原报告仍按其已发布合同显式记录预期但未执行的 `not_run/error`、缺结果失败及整体 outcome；禁止将失败改写为通过，或删除未执行观察项。[STD](#ref-std) §§10.3.2–10.5；。

预先批准且不承担该动作必需义务的 report_only 观察项，失败、未运行或观察制品缺失不自动阻断该动作；原始异常必须可追溯，也不能被算作控制通过。只有明确不影响必需证据、采集完整性和执行边界的观察异常才可按此处理；共同采集失效、信任状态不明或是否影响必需项尚不明确时，阻断受影响资格。Waiver 保留独立事实，不能改写原始 outcome。完整符合仍需全部适用强制义务的证据；不得仅凭项目把某项 MUST 的 gate 标成 report_only，就将该义务移出符合性分母。适用条款或已批准计划要求整体 verify 成功时，整体失败仍阻断对应动作；限定 Decision 不替代该前置条件。具体动作的允许结果不等于项目整体符合声明。

裁定按动作阶段计算：允许“提交候选”不能被解释为允许“合并、发布或完成”。受保护决定由已批准计划确定 required-for-action 的要求、检查槽位及制品集合，不能从候选报告的 expected 字段反推分母。计划槽位使用 `(planId, checkSlotId)` 或等价的受保护唯一身份，预先绑定 gate ID、配置、目标、环境和适用分片；实际 run ID/attempt 在运行时另行关联，不能由新 run ID 改写必验分母。同一 gate ID 可在不同槽位合法出现；同一槽位的重复计数、同一运行/结果身份的相互矛盾、必需槽位遗漏或必需制品不完整均阻断受影响决定。计划中的观察槽位未执行也须有显式状态，不能通过漏报隐藏失败或制造报告完整性。合法重试的不同结果保留并按预定策略聚合，不将它们误判为同一原始结果被改写。

要求与槽位允许多对多映射，但各自证明的断言、全部必需条件及明确批准的替代/聚合规则须在结果产生前固定。一个检查支持多个要求不等于多个独立运行；同一运行的报告重传、重新签发或缓存复用也不增加独立样本数。证据保留原始运行及来源结果身份；只有实际重跑才产生新的执行事实，且独立性仍按批准条件检查。分片和重试不得拼出未经批准的全绿子集。计划允许复用时，使用仍有效、满足槽位断言的原始运行证据及获准映射；本次未执行状态如实保留，不登记新运行。要求独立重跑或关键前提失效时不得复用。旧 report 的结构保持不变，槽位与来源关系由受治理绑定合同承载。

不可变验证证据可在授权范围内被多次查阅，或供同一上下文的不同合法阶段引用；每次仍重新检查政策、时效、撤销与目标。单次授权、预算预留和 Completion 消费使用受保护唯一性约束。重新运行产生新的 run ID；失败历史保留，重试上限及判定规则由受保护政策决定，不能靠挑选一次通过抹去不稳定结果。

必需证据的引用还须能在获准消费域内解析到其绑定字节，并有访问范围、保留期与失效规则。只有摘要、已删除制品的路径或无读取权的 URI 不足以支持新的受保护决定。保留和清理按受保护政策执行，清理事件及历史完成事实保留；证据失效后的现时资格重新判断，不能把曾经完成改写成从未发生。受限制品可由有权验证器读取，再签发不含秘密的限定裁定；不要求向 Worker 公开全部原始证据。

授权撤销、签发密钥正常轮换与签发身份失陷分别记录原因、生效顺序和影响范围。旧操作授权失效不必然否定已发生的历史事实；该事实须由当前有权核对者通过仍可信的来源验证。签发密钥泄漏或控制面失陷时，载荷自带 `issuedAt` 无法证明签名产生于失陷之前，禁止仅凭“日期早于撤销”恢复信任。按当前事故政策核对独立检查点/此前受保护接收记录中固定的确切字节、可信资源历史或重新验证结果；缺少足够独立依据时，相关证据隔离待查，不用于新的资格。正常轮换可保留明确的历史校验策略，但不绕过当前用途、有效期和授权检查。

**托管 CI 结果的映射。** 平台 check/job 的 `success`、`neutral`、`skipped` 与本规范的必需槽位通过分别处理。GitHub 的条件跳过 job 可报告成功，工作流级过滤又可能留下 Pending；仅将 check 名称设为 required 不能证明必需检查执行。[CI-CHECKS](#ref-ci-checks)。受保护最终 gate 从已批准计划枚举必需槽位，核对真实运行、终结状态、证据来源及 I/目标前提；缺失、取消、过滤跳过或依赖未运行不能被空集合通过掩盖。明确批准的原始证据复用继续依 S12 执行，不伪记为新运行。

最终 gate 的调度须覆盖被声明支持的事件与合并机制，并在依赖失败后仍能生成拒绝或由入口以缺证据拒绝。`always()` 等调度条件不定义通过语义；退出状态与受保护裁定同时正确才有资格。使用 merge queue 的适配器须验证 merge-group 对应实际候选；PR HEAD、平台测试合并提交与最终目标内容的关系按 S14 记录，不能互换。

**时间、租约与恢复。** 时间合同分别定义跨进程/跨系统的有效区间、当前受信时间及误差上限、当前启动/控制代次内的已用时，以及撤销状态最大陈旧度。参考授权窗口使用半开区间 `[notBefore, expiresAt)`；原生协议允许的偏差须固定在适配配置中，不得由调用者扩大，也不得越过更严格的组织权限截止。当前时间的不确定区间跨越关键边界、时间来源不可确认或恢复后出现无法解释的回退时，停止依赖该判断的新动作。

进程内相对倒计时不能只依赖可回拨的 wall clock。Linux 参考实现对需要随挂起消耗的授权时长使用包含 suspend 时间的时钟或获准等效方法；普通 `CLOCK_MONOTONIC` 在 suspend 期间停止，不能单独覆盖这类时限。[CLOCK-SEMANTICS](#ref-clock-semantics)。每次相对期限绑定当前启动/实例及控制代次，不能将其裸数值跨重启、虚机快照恢复或另一宿主比较。恢复后重新核对当前权威、绝对截止和历史消耗，不能从完整 TTL 重新开始。

相对剩余时长、可信绝对截止及祖先授权限制同时满足才可继续；新的时钟校准不能自行延长已批准的最晚截止或重置预算。可信当前授权明确续期时记录新授权依据及当前判断，保持原动作身份和去重历史。公开历史证据的真实性核对可按其限定用途继续，不能借历史时间材料产生现时权限。参考部署记录时钟来源、误差预算、校准/重启/挂起检测及异常处置；无需建设独立全球时间服务或修改全部历史报告格式。

**原生测试状态与要求证据分开。** 适配器将实际收集节点、配置/插件身份、运行/选择记录映射到获批槽位。框架的成功退出、预期失败、跳过或选择器排除均不自动证明对应要求。pytest的XFAIL表示预期失败，`strict=True`主要使意外通过XPASS影响套件退出，XFAIL仍可保留成功退出；`run=False`还可使测试体不运行。[PYTEST-OUTCOMES](#ref-pytest-outcomes)。承担必需断言的槽位须取得批准规则所要求的实际有效结果；测试失败或未运行不能因标记为XFAIL而充当通过。非必需观察项保留其原生状态及既定不阻断规则，负向安全测试则由受信驱动确认预期拒绝和正向可达。原报告枚举不扩写，原生状态通过版本化适配/证据绑定准确表达。

**强制验证边界。** 可信签发服务或独立签发进程形成 envelope；Cadence/集成入口验证完整绑定、计划槽位及原始运行来源，按预先批准规则聚合。受保护写入在其线性化点检查该资源当前权威状态中的授权、撤销及代次；离线快照单独校验只支持其声明范围内的证据分析，不能据此授予新的受保护动作。控制面可以位于同机受保护事务存储，无需连接公网；当前权威不可达时停止相应动作。`validUntil`、最大快照陈旧度和时钟容差由受保护政策明确，禁止以过期快照或未知时间继续判断有效。异步撤销必须明确生效线性化点与确认语义；对外确认撤销已生效后，所有相关入口必须拒绝旧授权，不能留下继续接受旧授权的离线网关。

<a id="s13"></a>
### 13.13 最小安全控制、审计与例外

以下 Z01–Z12 仅在此定义；其他章节引用其适用控制，不独立维护第二套最低控制。

| ID | 强制结果 | 实际 enforcement 点 | 必需证据 |
|---|---|---|---|
| Z01 | 未识别、未授权、授权过期的主体没有受保护操作权限；Agent 不得自批 | 部署身份与操作网关 | 有效授权与匿名、错主体、过期授权拒绝记录 |
| Z02 | 当前政策、适用事实和验收范围有独立批准；未知风险事实阻断相应资格 | 政策控制面、Bundle resolver | 政策摘要、事实来源、批准与三值求值结果 |
| Z03 | Worker 不能修改当前验证器、政策、保护规则、签发密钥或可信证据库 | 操作系统/CI 身份、挂载和权限边界 | 使用真实 Worker 身份的负向访问结果 |
| Z04 | 每次受保护动作都重新校验主体、资源、动作、期限、预算和当前授权代次；委派不能扩大权限 | 副作用入口与受保护写入入口 | Action Receipt、撤销与过期代次拒绝证据 |
| Z05 | 不可信代码在已证明可用的隔离环境运行；不可访问宿主秘密、控制 socket 或未批准网络 | 隔离适配器与宿主控制面 | 实际运行的隔离探针、配置摘要和适配器身份 |
| Z06 | 验证与集成绑定不可变候选，以及代码、文档、配置、依赖和必要外部工件的完整身份 | 候选快照与制品库 | 候选摘要、依赖闭包、构建/快照来源 |
| Z07 | 验证独立于候选编写者；Agent 编写的测试不得单独定义验收成功 | Cadence 与受保护测试/人工审查入口 | 已批准验收版本、实际测试结果、必要人工签署 |
| Z08 | 报告需验证来源、完整性、受众、范围、政策、候选与有效期；本地自签和裸 hash 不构成可信证明 | Cadence 证据消费端、受保护签发器 | 受信签发链、内容摘要、绑定字段和重放拒绝记录 |
| Z09 | 集成检查目标基线；竞争、重基、merge 结果改变时重新验证 | 受保护 Git/制品集成入口 | 目标基线、实际集成结果、CAS/等效原子提交证据 |
| Z10 | 完成状态依赖适用证据；Agent 的 `DONE`、`--force` 或 waiver 不得产生合规完成 | dasops 完成投影、Cadence 裁定、集成入口 | 完成记录与原始结果；无证据完成拒绝记录 |
| Z11 | 审计不可被 Worker 删除、替换或回滚；秘密不进入普通日志和工件 | 分离身份的审计存储、可信检查点 | 连续事件、检查点、脱敏及篡改检测结果 |
| Z12 | 工具、插件、规则、缓存和适配器有受控来源；缺失能力、撤销、事故和降级尝试安全停止 | 三仓调用边界与部署策略 | 工具锁、来源校验、kill switch、旧版本绕过测试 |

上述控制不要求每次动作均由人类点击批准。低风险、可逆、范围确定的动作可以由有权主体预先批准政策，再由独立控制面逐次执行。策略提升、保护规则修改和高风险动作必须走相应独立批准路径。

 以 security-agent 模块统一承载身份授权、威胁边界、输入输出、秘密/私有材料、供应链、审计、防降级、撤销与恢复的最低控制；复用现有治理和安全要求。项目风险事实可内嵌 Master Doc 的受治理章节，部署绑定留在受保护配置，不强制另建 Security Profile 文档类型。

审计事件至少绑定主体、动作、对象、决策、授权/政策身份、候选和可信时间/顺序。Worker 不能删改；哈希链必须锚定到 Worker 不可回滚的检查点。秘密脱敏与访问控制同时执行。零信任底线不允许普通 waiver；应急动作另走有权批准，保留失败事实，不能自动取得完整 v1.5 符合结论。

需要审计的正常业务写入、集成、完成及治理变更，先持久化意图/预留，再执行副作用，再追加结果。副作用已经发生而结果写入失败时，保留 `unknown`/待核对状态并冻结相关后续动作，通过可信资源状态核对完成恢复；不得倒填成功、自动重放或假定“没记录就没发生”。行政应急权限属于独立恢复通道，不能把非合规动作投影为 v1.5 已通过。已完成记录是历史事实；当前可采用资格还需查询撤销、事故处置与目标状态，历史证据不能被无限期当作现时许可。

审计或授权服务不可用时，正常受保护写入停止；由受保护 supervisor/资源入口执行预先批准的本地安全停止，不以先成功写入故障中的主审计库或取得新的业务授权为前提。允许范围仅为拒绝新请求、收回本地候选能力、隔离或终止已纳管不可信运行，不包含扩大权限、解除保护、业务补偿、重新发送外部请求或宣布完成。该能力不能由 Worker 通过通用应急参数取得。仅允许部署预先核准的安全动作；可能产生额外业务损害的处置仍走相应管理授权。

可用时将故障与停止事实写入独立受保护的最小记录通道；该通道也不可用时仍须执行有界停止，恢复后追加所能证实的故障区间与证据缺口，不倒填不存在的原记录或成功结论。局部停止不代表全域撤销完成：对不可达入口和已发出的远端动作保留未确认状态，满足 S12 的确认边界后才能宣布撤销已生效。恢复开放业务必须重新核对当前权威、审计能力、未决动作及部署条件。

受保护读取也要鉴权。报告、缓存、候选、审计和私有材料的引用须绑定资源域、调用主体、用途与输出受众；内容摘要和普通不带权 URI 只标识对象。含访问签名、令牌或会话能力的地址属于授权材料，必须按其真实权限处理，不得当作普通 artifactRef 公开、转交或写入日志。使用此类地址仍须满足当前调用身份、受众、资源范围及撤销要求，不能只凭地址可访问就接受授权。诊断模式不能借只读名义获取其他项目或密封评分域的数据。低熵秘密的普通摘要仍可能被枚举推断；完整性摘要保存在获准域，面向开发侧的索引使用不暴露受限值的引用，导出裁定另行控制字段。审计脱敏不得靠可枚举的裸 hash 或仅去除原文来宣称已消除泄漏。

持续下载、分页、订阅和延迟反馈须定义有界发送单元、单元的字节/记录及时间上限、续读检查点、撤销生效与确认语义。每个新发送单元在实际释放前核对当前身份、用途、披露政策和适用额度；受信域已取回或缓存数据，不自动取得随后向开发域释放的权利。到期、撤销或当前权威不可达时，停止新单元和仍可中止的释放；先前已获准且不可撤回发出的单元作为在途披露如实核对。合同须限制可能剩余的在途数据量和时长，不要求逐字节授权，也不声称撤销能收回已经合法披露的数据。

撤销确认覆盖相关持续会话、重连/Range 请求及此前发出的带权地址；仍可借旧路径取得新的受限内容时，不得报告该范围撤销完成。仅停止签发新地址或等待客户端自行停读不满足该确认条件。参考实现可由受保护交付网关执行有界释放；外部存储的签名地址仅能证明其自身明示的访问语义，无法满足所需边界时不向该受众开放该路径。公开资料与经批准完整披露的内容按其实际数据政策处理，不统一要求所有普通下载经过私有数据网关。

**持久化承诺与故障模型。** 动作意图、预算预留、去重身份、完成唯一键及状态代次的成功确认，须达到已声明故障模型下的持久化边界。仅从写 API 返回、写入缓存、数据库事务逻辑提交或终止后可重启，均不独立证明已承诺的断电持久性。实际存储、journal/WAL、同步设置、文件系统与恢复前提列入受保护部署配置；主机/系统崩溃与仅进程崩溃分开测试。SQLite WAL 的 `synchronous=NORMAL` 可能在断电或系统崩溃后丢失已提交事务，是需要明确配置的实例。[SQLITE-DURABILITY](#ref-sqlite-durability)。

未达到所需持久化边界时不发送新的正常副作用、不确认预算可再次使用，也不签发已持久完成。I/O 错误或丢失响应使提交结果不明时，按同一业务动作键核对，保留 unknown。恢复业务状态不能回退授权、去重、预算或审计历史；本地安全停止仍按本条独立能力执行。该要求不引入多区域复制或任意灾难下零丢失保证。

**持久关系与唯一性。** 权威 Task/Change、动作、预算及完成记录的关键身份、周期、代次和指纹不得使用缺失或 `NULL` 值参与去重；相等比较规则与其身份合同一致。每次完成/关闭在受保护事务内同时核对父子关系、当前代次、必需证据和唯一完成约束，不能依赖候选提供的关联 ID 或仅验证 schema。已有历史与去重记录不可被通用“存在则替换”写入覆盖，冲突必须比较同一不可变请求指纹并返回原状态或拒绝；授权更新只修改合同允许的字段，另追加历史。

参考状态存储应证明每条承担权威写入的连接实际启用其依赖的约束；约束错误、更新零行、事务提交失败或未知不得映射为成功。语句失败未必撤销前序语句，故障后须明确核对事务状态并回滚未提交权威变更；提交结果未知时进入已有恢复协议。SQL 表的声明、内存锁或单次 ORM 调用不独立证明这些关系在真实写入路径生效。SQLite 参考实现必须验证非空键、连接级外键和冲突处理；替代数据库使用等效强制与对照测试。[SQLITE-INTEGRITY](#ref-sqlite-integrity)。

**事务启动与集合不变量。** 数据库事务必须在数据库内用于决定写入的集合/状态读取之前实际开始，并覆盖关联的预算、父子状态、唯一键和审计意图提交。ORM 注解、上下文管理器、逐行 CAS 或各条 SQL 独立成功不能单独证明完整事务。共享预算剩余额度、父 Change 的完整必需任务集合以及“没有未决动作”等谓词，须在所有相关 writer 之间形成可串行化的决定；只防同一行覆盖仍可能遗漏跨行写偏差。采用可串行化隔离或经验证、所有 writer 共用的保护记录/版本约束，按所选数据库实测。[SQL-TRANSACTIONS](#ref-sql-transactions)。不要求所有只读观察查询使用最高隔离等级，也不据此宣称跨系统授权瞬时一致。

确认事务回滚后，针对可重试冲突重新读取当前权威和业务数据，并重算完整事务逻辑；不能只重放失败 UPDATE 或沿用已失效读取。重试保留稳定业务动作键，受累计尝试/时间和当前权限限制。未提交事务中的读到值或暂定成功不得触发外部动作；外部发送通过已持久化意图的独立执行点，提交结果未知继续走核对路径。副作用和长时间网络请求不放入可自动重试的数据库事务体。

**审计内容与控制通道分离。** 候选 stdout/stderr、测试报文和附加文档即使已经被可信采集，内容仍属所声明来源的数据。可信事件字段通过封闭结构分别赋值，不能把候选多行文本拼进事件头、批准字段、CI 命令或可执行模板。按输出上下文处理换行/分隔符、终端控制序列、HTML/Markdown 中的脚本及自动资源加载；明确区分结构化事件、受限原始字节和展示副本。[LOG-DATA](#ref-log-data)。

原始字节按 S12 的来源、保密及保留范围进入受限工件库；面向人的安全展示和脱敏副本作为派生视图，记录原引用、转换规则及必要的新摘要。展示转换不能改写原签名所绑定内容，也不能把被转义的文本当作新增可信事件。已有 CLI、CI 报告、审查页面及证据导出均遵从这一边界，无须新建统一 Dashboard。

**引擎修复状态与一致性恢复。** 权威状态存储除同步、约束和隔离配置外，还要有实际加载的引擎/驱动/编译配置、制品来源、已知完整性缺陷适用性及修复依据；不能用宿主命令行版本替代进程实际库。影响批准模式的数据损坏缺陷未修复或适用性不明时，停止相应受保护写路径；一次压力测试未复现不能替代修复证据。参考 SQLite 的模式、实际加载制品、修复条件和回补证据在受保护部署记录中登记，其他引擎证明等效受控来源和完整性。[SQLITE-WAL-FIX](#ref-sqlite-wal-fix)。

备份必须对应经过确认的一致状态边界，覆盖实际事务存储和必要恢复材料；普通文件逐个复制、无条件删除恢复日志或只检查数据库能打开，均不足以证明已保留已提交意图/额度/完成。跨多个物理库的写入只在机制明确保证时才声明共同原子性。恢复后的数据库快照还需与独立检查点、已发生外部动作及当前撤销核对；快照完整不代表已包含备份完成后的事实。历史缺口和未决动作保持待核对，不能重置预算或开放重复执行。[SQLITE-BACKUP](#ref-sqlite-backup)。

**制品存储与状态引用的持久提交。** 引用候选、报告或安装材料的数据库事务与其文件/对象存储提交分别确认。声明覆盖系统崩溃的实现，在把工件登记为可用于资格裁定之前，须完成其完整字节校验、存储持久化及引用关系的受保护提交；命名可见、原子 rename、进程正常退出或仅同步数据库都不足以证明工件内容与目录关系已经持久。Linux 文件系统路径中，`fsync` 文件并不单独保证其目录项已经同步；具体协议须同步所需目录并核对所有返回结果。[ARTIFACT-DURABILITY](#ref-artifact-durability)。原有 S18 的实际修改边界、冲突保护和 no-clobber 要求继续适用。

参考顺序为持久意图/登记 → 隔离暂存与完整校验 → 存储按声明故障模型确认 → 持久化可消费引用；实现可以合并同一事务域内的阶段，但不能声称不存在的跨存储原子性。已存好但未登记的孤立工件只在核对身份及原操作后恢复登记；数据库有引用但必需工件缺失/不完整时，停止其相关资格并如实记录事故。不得通过重建不同字节、删除失败或清空动作/预算把引用修成假成功。同步或提交结果未知时保留原动作核对，不能因临时文件/最终文件可见就假定整个操作已成功或未发生。

**强制验证边界。** 标准检查控制唯一正文和证据映射；部署执行真实权限、审计、撤销与恢复测试。过期 waiver、缺审批、审计截断或控制面不可达时停止相应业务动作；独立停止路径按上文收敛权限，不承担业务恢复。实际注入主审计不可写和控制面不可达故障，核对新写入被阻断、纳管运行可被安全隔离及无伪造通过。 对存储确认、引用提交及恢复的每个交接点注入故障，缺少必需持久证据时不得签发依赖它的资格；已发生业务动作仍保留历史和未知状态。

<a id="s14"></a>
### 13.14 工具中立的 Change / Task 完成语义

 一个 Task 身份对应同一验收义务。完整身份为 `taskKey = (authorityDomain, projectId, changeId, taskId)`；这些分量由受保护命名空间解析，不能靠可修改目录名或 URL 别名决定。既有 `T-167` 等局部 taskId 继续合法，不假定其跨 Change 唯一；正式交换必须携带完整 taskKey，或携带与其一一绑定的受保护不透明 ID。所有任务授权、候选、证据、完成与恢复记录使用同一身份规则。

projectId、changeId 和完整 taskKey 的权威分配不得在对象删除、归档或显示名称再次使用时转交另一对象；同一 Change 内已使用的局部 taskId 保留其历史指向。显示标签可以复用，新对象须映射到不同的受保护身份。保留既有 taskKey 结构；外部可复用编号经显式映射进入受保护不透明 ID，不在旧闭合 schema 中暗加字段。退役记录与映射历史保存在受保护状态，迟到证据仍指向原对象；恢复原对象须证明其身份及历史连续性，不能借重建空记录继承旧 Completion 或重新发放额度。此身份规则与 S10 的资源实例绑定一致；[RESOURCE-ID](#ref-resource-id) 的不可重新分配 ID 仅作机制参考，不要求部署其协议。

意图、行为变更、设计取舍、执行计划可内嵌或引用，不要求固定四个文件。实质变更目标/范围/合同/责任/验收义务时新建 Task 并保留 lineage；非实质澄清可增 revision。失败重试增 attempt；同一义务完成后返工增 cycle。

父 Change active 时可按规则返工；closing 要先撤回关闭准备；closed/cancelled/superseded 后通过关联新 Change 承接。行政误关闭撤销沿用  §4.1 的窄例外：仅适用于能够证明无部署、无迁移、无外部依赖影响的误关闭，并核对该关闭是否已被后续资格或动作消费。存在外部影响、真实返工需求或事实不明时，通过后继 Change 处理。符合例外时由独立有权主体批准，追加 `closureRescinded`、保留原关闭事件并更新状态代次；不得改写原义务、原结果或把取消/替代包装成行政误关闭。

父 Change 的当前状态、受批准任务集合、任务集合摘要、关闭义务与状态代次属于受保护权威，不能从可编辑子任务列表即时推定。进入 closing 时固定当前任务集合及关闭条件，禁止并发新增、删除任务或开启返工周期；已纳入关闭计划的在途任务只可按明确许可继续结算。普通 closed 提交须在同一受保护事务内核对状态代次、完整任务集合、各必需任务当前 cycle 的有效完成、Change 级验收及不存在未决副作用。任务完成、返工和关闭使用同一串行化边界，避免“检查全部完成之后又新增任务”。取消、被替代和行政终止保留独立终态，不计作合规成功；实质缩减目标须按新 Change/Task 及 lineage 承接，不能删掉失败任务来关闭原义务。

<a id="change-state-rules"></a>
| 父 Change 状态 | 可接受的受治理行为 | 必须拒绝或另行处理 |
|---|---|---|
| draft | 有权主体登记/审查事实、任务与执行计划 | 尚未激活的任务不得产生业务执行或合规完成 |
| active | 当前获批任务按独立授权执行、完成；同一义务返工走新 cycle | 实质变化仅增 revision、复用失效授权或证据 |
| closing | 当前关闭计划明确允许的既有任务/周期可继续集成或完成；入口重验当前授权及状态代次 | 新任务、新周期、扩大义务或计划未批准的动作；需要时先受控撤回 closing |
| closed | 当前有权主体读取历史、核对已有动作、归档；受权验证服务可按下文限定规则重新验证；符合上文窄例外才可行政撤销关闭 | 普通重开、新业务执行或新增子任务完成；后继工作另建 Change |
| cancelled / superseded | 追加在途动作真实结果与处置，关联后继或受权恢复流程 | 继续使用原执行授权产生新动作或新 Completion；取消不证明已回滚外部副作用 |

历史核对可以补录已经在终态前权威提交的事实，不能在终态后创造新的合规完成。closing 内合法结算与父关闭按同一事务顺序处理：先结算则关闭读取新完成；先检查发现义务未齐则关闭不提交。无需让每一项并发请求都失败；不满足当前状态、计划或代次的请求才拒绝。终态转换停止尚未发出的普通业务动作，在途已发请求按 S10/S13 核对；未决恢复可留在取消/替代记录中，普通成功关闭仍不得遗留未决副作用。

完成需满足当前候选的验证、必要责任确认、适用集成及迁移/回滚证据。仅有仓库外分析且不改共享状态的任务可以经批准声明无需集成。archive 为物理管理动作，不决定语义终态。

任务定义、执行尝试与完成周期具有独立身份。revision 变化必须经独立判定；即使属于非实质澄清，旧证据也只能通过明确的受权等价/重绑定记录被当前任务引用，不能静默忽略摘要变化。attempt 变化不允许重置预算或丢弃失败历史。Task 义务摘要按已批准抽取规则覆盖目标、范围、约束、验收与责任，执行状态投影和运行日志不作为义务作者源；候选内容摘要仍须覆盖实际纳管文件，不能据此排除代码或文档变化。每个 `(taskKey, cycle)` 至多有一次合规完成提交；revision、attempt、显示 ID、授权代次或请求 ID 的变化不能绕过该唯一性，返工遵从新 cycle 规则。

源候选与实际集成候选分别记录。merge/rebase 产生的实际集成内容须获得匹配该内容和目标基线的新验证；原验证可按受保护复用规则作为输入证据，不能直接冒充新候选验证。Integration Receipt 绑定原候选、实际集成候选、验证引用、目标及提交前后版本。跨 Git 与完成状态库采用持久化动作 ID、CAS 和可恢复记录，不能声称存在未实现的跨系统原子事务。

Completion 置于候选之外的受保护事件存储。将 DONE 投影写回 Git 会改变候选，不能继续使用原候选摘要；首期默认生成工作区/状态界面的非权威视图。确需提交投影时，作为单独受治理的确定性元数据变更验证与集成，不把未来 Completion 纳入其所证明候选的摘要，也不以回写投影重新触发同一任务的完成循环。Completion 证明指定候选曾在指定目标版本完成，不证明分支之后永远保持该内容。

证据到期或当前资格需复核，不自动重开 Task、增加 cycle 或产生第二份 Completion。义务、候选和相关条件未发生实质变化时，受权验证服务可以在当前批准的验收计划、验证专用授权及预算下重新核验或运行必要检查，追加新的 Verification Evidence 与动作专属 Decision，并引用原 Completion。它属于验证服务的当前受控运行，不恢复终态 Task 的 Worker 业务权限；不得修改候选、触发任务业务副作用或重做集成，验证产生的记录也不改写历史事实。重新验证失败或依据不足时保留历史完成，拒绝依赖现时资格的后续动作。

重新验证可以按 S11 在获准测试空间中执行必要的初始化、检查与清理；这些动作使用验证服务本次有界授权和额度，不恢复原任务的业务动作权限。

Change 关闭、发布或采用须满足其当前计划规定的目标状态与 Change 级验收；仅重新验证旧候选，不能掩盖当前目标已移除相应成果。真实返工或实质义务变化仍按 cycle/后继规则处理；取消或替代的义务不能通过重新验证恢复为成功。当前新证据不追授过去缺失的授权、隔离或执行证明。

父关闭和共享额度检查依赖集合状态时，执行 S13 的谓词/集合并发要求。每个子行独立 CAS 成功不代表“全部任务已经完成”这个决定仍有效。事务重试不得跨越新的父状态、任务集合代次或授权条件；重试成功只形成一个当前有效完成/关闭记录。所选参考存储的具体事务启动、锁竞争及恢复规则由 O09 落实，替代实现提供等效证据。

**强制验证边界。** 完成与 Change 关闭在受保护入口核对完整身份、当前任务集合、状态代次和可信证据；状态判断与提交共享原子边界。tasks.md 只投影已成立的新完成事实。旧状态保持读取与历史展示，不直接映射为新完成。旧 schema 不可表达的权威状态由明确版本的绑定/事件合同承载。

<a id="s15"></a>
### 13.15 HTTP 事实权威、覆盖与稳定身份

 每个纳管 surface 记录范围、事实来源、来源优先级及确定性覆盖。OpenAPI-first、code-first 和组合来源均可采用，但同一事实只能有一个有效作者源。新增 declaration 和 normalized inventory 的精确合同；operation 定位与长期身份分开，满足稳定及不复用条件的 operationId 可兼作身份。

selector 在指定来源快照上物化操作集合；解析外部引用受批准范围与摘要约束。Overlay 必须有所有权和单向生成链。自动兼容检查覆盖结构及已形式化语义，未能判断的业务含义进入独立评审。

**HTTP 描述的原生语义。** 声明所用 OpenAPI/JSON Schema 的精确版本与 dialect，适配器仅在实测支持范围内解析。不能把 OpenAPI 3.0 Schema Object、3.1 及其他版本当作同一 JSON Schema；未支持的语义须明确拒绝或经批准的无损映射，不能静默移除限制。不强制所有项目升级到某个最新 OpenAPI 版本。

事实归一化须保留 root 与 operation 的覆盖关系、每份文档的基 URI，以及安全要求的组合语义。在 OpenAPI 3.1.1 中，同一 Security Requirement Object 内的方案为同时满足，`security` 数组的不同对象为可选方案；操作级 `security: []` 可移除继承要求，空对象 `{}` 表达允许匿名。公开端点可合法声明匿名；与已批准应受保护事实冲突时才拒绝，不能把所有空声明一律当漏洞。[OAS](#ref-oas)。

规范化 Inventory 分别记录声明与真实边界证据。OpenAPI 描述认证要求不证明资源入口已实施授权；经过访问过滤的空 Paths 也不证明项目没有 HTTP surface。受保护候选中的实际路由、网关/部署事实、适用 webhook/callback 及范围声明进行覆盖对照，只对项目实际提供的面纳管。外部引用先在受控材料解析步骤固定原始字节、来源及基 URI，后续解析离线进行；合法 schema 递归按方言处理，有界遍历不能简单将所有循环都当作模块依赖环。

**请求边界与鉴权对象一致。** 实际纳管HTTP链按协议版本固定消息分帧及转发规则；网关、代理、协议降级和应用处理器须对同一次受保护请求得到一致的目标、权限相关字段和消息体。存在解析分歧的请求在资源动作前拒绝并结束可能失步的连接，不把前端拒绝记录当作后端未执行的证明。

HTTP/1.1参考入口对同时携带Transfer-Encoding和Content-Length的受保护请求采取拒绝并关闭连接的严格策略。RFC 9112也允许按Transfer-Encoding处理此类请求，但规定了连接关闭及转发去除Content-Length等条件；替代实现须证明其原生处理不造成下游边界分歧。不同Content-Length、非法Host、多义换行、无效分块及截断按原生错误规则处理。同值重复Content-Length或合法列表头按获批协议规则拒绝/归一化，不能把所有重复字段一概视为攻击。[HTTP-FRAMING](#ref-http-framing)。

验收在隔离链路使用原始协议输入，验证网关和最终处理器的实际请求数、对象、正文及副作用；会自动修正头部的高级客户端不单独覆盖此场景。未支持的代理/协议组合保持关闭；正常分块、连接复用及已批准的逐单元流式请求有正向对照。本条约束所用入口，不要求建立新HTTP服务器或扫描真实第三方系统。

**HTTP 早期数据与重放。** 对采用 TLS 早期数据及相应代理链的受保护 surface，按 RFC 8470/TLS 1.3 的实际重放边界审查。参考部署默认不以 early data 执行受保护写入、消耗不可重复额度或释放密封反馈；GET 等方法名不免除其真实副作用与披露约束。不需要引入 TLS 1.3、HTTP/3 或早期数据功能，关闭该能力可以成为经实测的参考路径。[HTTP-EARLY-DATA](#ref-http-early-data)。

经过 TLS 终止或多级代理时，入口核对可信连接元数据与原生 `Early-Data` 传播；等待当前一跳握手完成，不能消除先前链路接受早期数据所带来的重放可能。按 RFC 处理标记和重试，不允许代理丢失标记后省略所需的早期数据重放检查。返回适用的 `425 Too Early` 应在相应副作用前完成；随后重试不再使用早期数据，并继续绑定原业务动作/参数、当前授权及累计尝试额度。拒绝早期数据不解除应用层幂等、防重放或当前授权要求。支持其他原生合法策略的实现须有明确动作适用性和端到端证据，不能仅凭 session ticket、连接加密或一次观察未重放宣称保证成立。

**强制验证边界。** Cadence 检查来源完整性、重复定义、覆盖差异、引用闭包、ID 历史及生成漂移。删除声明不能让已批准 surface 无声退出范围。 所选入口核对 TLS 终止、代理传播和实际发送路径，未能证明所需重放边界时关闭对应优化或受影响动作。

<a id="s16"></a>
### 13.16 UI 以工作流和行为证据验收

 复用 UI Spec、W#/UI 标识、interaction profile 和既有页面/工作流条目。冻结受影响任务、用户/角色、支持面、设计来源或批准替代基线、状态与验收分母。scope、实现、验证、excluded、waived 分开记录；设计引用缺失时明确使用批准 UI Spec，不填写虚构设计 ID。

**页面约定的最低信息。** 在 Appendix D 的既有 Per-screen specification 中补足以下信息，已有 workflow/state/design/test 条目可直接引用；项目可以用等价结构表达，不必增建页面合同文件或 UI manifest。

| 信息 | 约定内容 | 交付与检查边界 |
|---|---|---|
| 任务与默认区 | 任务、指定受众、主内容、按需入口及多个协作区域的职责 | 检查任务可完成；专业工作台可有多个重要区域，不以卡片/按钮数量代替任务判断 |
| 内容受众与必要提示 | 自有业务文案、必要风险/权限/结果提示、帮助与内部调试说明的来源及呈现位置 | 必要提示适时可见或可达；技术用户正文、上传内容和授权运维内容按真实受众处理 |
| 阅读与导航 | 任务所需完整内容的获取、载体、定位、滚动、深链接及适用返回行为 | 允许分页、虚拟化、分屏和抽屉；不能以短预览或只有摘要的节点冒充完整阅读 |
| 异步与编辑恢复 | 操作/对象归属，切换、取消、返回、刷新、保存及未保存输入的处理 | 描述实际支持的恢复范围；浏览器/宿主能力限制显式列明，不承诺无法实现的崩溃后输入恢复 |
| 基线与证据 | 视觉/行为基线、token 来源版本、适用无障碍断言及回归链接 | 引用原有设计/状态/测试条目，避免第二份独立权威清单 |

**可执行行为要求。** 以下强制行为成为 Standard UI 模块中对应稳定 requirement 的唯一语义来源；Appendix D 提供填写位置，Appendix H 提供检查与证据映射。HFVI 仅继承其实际适用的基础行为。

| 领域 | 规范要求 | 正向与负向判定 |
|---|---|---|
| 默认任务区与内容 | 界面 MUST 支持获批任务及必要信息；仅供开发、编排或内部调试的指令 MUST NOT 被误投影为普通用户业务正文 | 允许多区工作台、合法帮助和用户技术正文；内部指令误显、必要风险提示丢失均不通过。关键词扫描仅为线索，来源/受众/语义需独立确认 |
| 导航职责 | 重复导航 SHOULD 按区域、目标和交互目的评估，保持命名与行为一致 | 允许面包屑、页尾、局部及响应式导航的合理重复；不制定全局链接去重门禁 |
| 持续阅读 | 对声明的阅读任务 MUST 提供获授权且属于该任务范围的完整内容与适用定位/返回能力 | 分页未完、不可达尾部、正文被截断不通过；获批抽屉/分屏能完成任务时可以通过。授权限制不通过复制受限全文来规避 |
| 异步状态归属 | 成功、错误、进度、清理及副作用回执 MUST 仅更新仍然有效的操作/对象/状态范围 | A→B→A、旧请求晚到和取消后回调按操作代次核对；较早发起的请求不自动视为无效，已批准后台刷新按明确新旧规则合并 |
| 保存与本地编辑 | 保存结果 MUST 绑定实际提交的内容/版本；提交之后新增的编辑不能因旧保存成功而丢失或被误标已保存 | 保留 submitted snapshot 与当前编辑版本；失败/重试/返回不得以新对象结果覆盖旧对象或清空无关 dirty 状态 |
| 历史与对象解析 | 依赖唯一性自动选择对象时 MUST 具有足够的集合完整性与身份依据；未知、损坏或读取失败 MUST NOT 支持唯一性推断 | 0/1/多项、未取完分页和损坏历史分别处理；有效明确 ID 可按授权直接读取，毋须先修复全部历史。存在同名对象时遵从身份合同 |
| token 与基线 | 继续执行既有 token 来源、版本、消费及例外规则；受影响组件须有足以支持实际消费关系的证据 | 静态引用与运行样式结合，代表组件受控扰动/隔离构建可选；不以新增 SHOULD 降低旧 MUST，不规定唯一检测算法 |
| 模态与无障碍 | 实际模态行为、焦点/键盘及适用无障碍要求 MUST 与获批交互约定一致 | 模态检查背景不可交互、焦点进入/循环/关闭及合理返回；非模态抽屉按非模态行为检查，不强制焦点陷阱 |

异步拒绝更新不会撤销已经提交的远端业务动作；操作状态未知时引用 S10/S14 的回执与恢复语义。取消可作为资源优化，但不能单独证明旧结果已失去更新权。React 的官方 race-condition 示例支持清理/忽略旧结果这一机制；操作代次、缓存策略和保存版本的完整边界由此处 UI 合同定义，不要求使用 React。[UI-ASYNC](#ref-ui-async)。

**检查能力与基线。** Appendix H 的 Accessibility 自动化标记为 `Partial`，分别映射静态/自动扫描、真实浏览器键盘焦点行为及人工语义/辅助技术判断。自动扫描、截图、录像各自只能证明其覆盖的断言；无障碍外部标准的版次、级别与范围来自适用条款及项目批准，不因使用工具或 APG 模式自动取得 WCAG 符合性。APG 属实施指导；所采用的规范性要求与指导分别标明。宣称 WCAG 符合时另须满足其相应完整页面/完整流程等要求，不以代表页面的样本通过推定整个站点通过。[A11Y](#ref-a11y)、[ARIA](#ref-aria)、[WCAG](#ref-wcag)。

首次行为/视觉基线由独立有权主体批准；回归比较绑定旧批准基线和当前候选。没有既有基线时按首次验收产生证据，不能自动创建基线后宣称“没有回归”。基线更新、范围缩减和排除项事前独立批准；失败后缩小分母不得自动提高完成率。必需槽位与合法原始证据复用按 S12 判定，`not_run` 保持真实含义，不另建 UI 特有的空通过规则。

**强制验证边界。** UI 断言先证明目标 origin/route、对象、当前业务状态和采集完整；需要正常态的检查不能在登录页、错误壳或空页面上判通过。检查旧错误已消失前应证明对应错误确实被触发，指定坏样例须仍到达受测业务状态。此类前置与健康/坏样例/恢复对照映射到已有 A27，不强制每次普通提交运行全部产品。dasops 按 O11 补模板位置和引用；标准检查器核对 requirement 唯一归属、Appendix D/H 的强度与映射。Cadence C11 消费受保护验收计划、受限 UI runner 的真实断言和必要人工判断；候选不得修改驱动、批准基线或验收分母。行为证据绑定实际构建、环境、测试账户范围、状态数据、设计/token 基线及来源运行。仅有 selector、截图数量、自评得分或页面中的成功文本均不足以满足上述行为义务。

<a id="s17"></a>
### 13.17 算法评测、密封数据与声明资格

 普通评测记录数据用途、已知暴露、协议与候选身份；公开回归数据继续使用。新密封声明须证明开发主体不能访问私有评测输入及秘密评分材料；候选执行域只可接收协议批准的推理输入，不可访问标签、答案、未授权保留集或秘密评分材料。候选执行域与评分域分离，评分域不执行候选代码或任意对象反序列化。公开评分公式无需一概保密；保护范围以协议中的秘密材料为准。

候选域只接收协议允许的有界评测输入；这不授权读取标签、隐藏评分规则或整个保留集。候选结果经大小受限、无代码语义的输出合同送入评分域，不能指定任意目的地。私有输入、原始预测、日志、缓存和受限报告不得回流开发身份。

数据划分先于有状态拟合；例外 transductive 设置预先声明。首次私有输入发放前冻结代码/模型/Prompt/依赖/预处理、协议、评分器和反馈规则。预算跨会话、别名、账户和 Runner 持久归属；未知执行结果不得轻率作预算中性重试。

预算主体由受保护控制面根据实际开发/提交控制关系确定，不能接受客户端自报的新账户来重置。首次泄露任何私有输入或数据相关反馈前，原子预留适用额度；重试、失败类型、退出码、耗时/大小信息和完成 gate 的通过/拒绝，只要对开发侧透露数据相关信息，均纳入预先批准的反馈合同。禁止输出任意候选字符串或逐样本调试材料；释放的指标精度、错误类别、次数和通道应有界。只允许协议内反馈，不能把“没有原始数据下载”表述为零信息泄漏。开发控制面与私有运行缓存/日志按身份及数据域分离；清理不完整时不得复用运行环境。

EvalReport 保持有界摘要 + 引用，补充协议/评分器/数据与完整报告的稳定身份及摘要。优先映射现有 `dataset` 和 `artifacts.fullReportRef`，不机械新增同义 datasetRef/reportRef。指标达标、发布决定、报告有效性与未见声明资格分开。污染后追加处置，保留评测时点事实。

预算主体映射的保证限定于已登记、经独立核准的真实控制关系。新账号或不明控制关系先进入待核准状态，不能自动取得新的密封预算；迁移身份保留原预算 lineage。本要求不宣称可自动识别互联网中一切隐蔽关联账号。签发和消费域可以读取经授权的受限证据，开发域只能取得批准反馈；数据摘要、对象存在性、诊断错误和下载接口均遵从 S13 的读取与披露边界。

**评测结果的声明边界。** 隔离有效、预算有界及评分可复现，不能单独证明统计有效、差分隐私、样本未被间接用于选择或模型可泛化。普通测试集不得参与拟合、特征选择、预处理统计量估计及依结果调参；交叉验证中的有状态预处理按获批划分在训练折内拟合，时间/主体分组约束由实际数据和声明决定。[EVAL-PRACTICE](#ref-eval-practice)。

协议在结果产生前确定分母、失败/超时/缺样本处理、聚合、重复运行与允许声明。失败样本不能从指标分母中静默消失；无法计算指标时输出独立状态，不用伪造零值或通过值占位。开发者依据保留集反馈选择下一候选时，后续结果不能继续沿用“独立未见”标签。已有研究给出了在特定机制及假设下重复使用保留集的保证；本版不实施或认证该类算法，有限次数的普通评分不自动获得同等保证。[ADAPTIVE-EVAL](#ref-adaptive-eval)。已有反馈历史仍完整保留，新的声明依其实际暴露和协议判定。

**强制验证边界。** Cadence 校验合同、资格及运行证明；实际 IAM/文件/网络/反馈/预算由评测部署执行。工具静态通过不替代真实隔离测试。旧报告保持读取，缺失新证据不得取得密封资格。

<a id="s18"></a>
### 13.18 元数据、版本来源与旧工件迁移

 文档状态继续使用 `draft | active | frozen | deprecated`；Change、Task 和执行阶段各自独立。标准版次以 VERSION 为单一作者源，manifest、索引和报告取值并做一致性验证。历史快照和 fixtures 中的旧版本保留，不全仓替换。

消费者能力、输入契约、输出契约、采用目标和合规资格分别声明。新 reader 先上线，新 writer 后启用；不能将 optional 等同于旧 reader 兼容。旧数据迁移保留原始值、摘要、来源和差距，不补造原本不存在的证据。受治理目标的最低政策和工具版本由控制面锁定，不能由 Agent 编辑仓库降级。

格式兼容和当前安全授权分别判断。支持窗口内的旧合法数据继续按其原义解析；已撤销或存在阻断性漏洞的旧可执行工具不得因兼容承诺重新获得受保护执行权限。旧对象可以作为隔离诊断输入，不能迫使新目标放宽身份、解析资源限制或最低控制。

修改或回滚文件时，预期内容检查与实际替换必须处于同一不可绕过的修改边界。工具内部锁、journal 和单次原子 rename 不足以排除仍可直接编辑目标的主体。参考路径可从受保护基线生成独立版本树，经核验后条件切换受保护引用；原地修改则须证明相关文件、目录项及已有写入能力均已纳入控制，再复核 preimage/postimage 并保持到提交结束。无法建立该边界时只输出新候选或差异，保留当前用户内容，不将“先检查再覆盖”声明为安全事务。

受治理入口的盘点、诊断及 dry-run 的只读承诺针对受分析业务状态；明示的计划/诊断工件输出须另有有界写入权限。默认通过无特权客户端输出或在获准、与受分析内容隔离的工件区创建新对象；不得借输出路径覆盖源码、任务、锁/政策、Git 元数据、缓存或已有用户文件。输出目标先按真实目录与对象身份核对，再采用不覆盖已有对象的安全发布方式；位置/权限不成立时只返回错误或受控结果引用，不能转用执行器权限兜底写入。工件生成失败不进入 apply/rollback，候选判定也不能因输出目录被自动纳入扫描而改变。

**版本与渠道。** 首个试用发行目标为 `1.5.0-beta.1`；必要的公开修复递增beta编号，达到试用及正式门槛后直接发布`1.5.0`。具体规则以[发布生命周期](#release-lifecycle)为唯一说明来源。`1.5.0+beta.1`属于构建元数据，Git tag的`v`前缀也不属于`standardVersion`值。[SEMVER](#ref-semver)。旧manifest字段为string不代表其消费者能够正确解析beta；脚本、schema dispatcher、镜像/锁、索引及安装器分别验证。既有gate cadence `pre_release`保留检查频率原义，不授予发行或采用权限。

DAS 标准目标、dasops/Cadence 软件包版本、交换协议版本、发布渠道和部署资格分别记录。工具维持独立版本序列，支持矩阵绑定确切目标及制品摘要；不得为了看齐标准号而跳过其自身公共接口的兼容评估。每项新义务、旧 ID/锚点、CLI/schema 改动和支持窗口均有兼容裁定。已承诺遵守 SemVer 的公共合同存在破坏性变更时，必须保留兼容接口/版本化新接口，或按该合同规则升级其主版本；预发布标签和“新版版次”称谓不能免除已作出的兼容承诺。DAS 正式版本策略及公开治理声明应与该裁定一致，不把“旧项目仍可锁 1.4”单独作为整个 1.5 为兼容 minor 的证明。

**发布包激活。** 受控更新同时核对来源、获准渠道、标准/工具/协议支持矩阵、完整摘要闭包、信任状态及受保护更新代次。同名镜像/tag、分别签名的不同代包、只改顶层版本、回放旧获批包或过期元数据不能拼出新的有效激活。借鉴 TUF 的版本/摘要关联、过期与防回滚机制，首期可用受保护本地锁和状态服务实施，不要求完整 TUF 服务。[TUF](#ref-tuf)。离线验证历史包仅证明其历史内容；新激活需要当前授权。回退业务代码采用新的获批激活事务，保留防回滚下界、去重、预算与审计，不能回滚控制面历史。

**强制验证边界。** 元数据生成检查、schema dispatcher、旧新读写测试和受治理防降级测试；格式错误、未知版本和 unsupported 能力给出明确失败，不静默规范化安全关键输入。

<a id="s19"></a>
### 13.19 自验证、参考部署与配套发布门槛

 标准包包含离线完整正文、模块目录、schema、fixtures、迁移映射、条款/规则/工具覆盖及可重复生成的完整视图。标准仓自身不必为了区分 default/--full 人为制造不同检查；输出必须真实列出执行集合。

正式配套就绪要求：标准自检、dasops/Cadence 自身完整测试、精确支持矩阵、最小参考部署及 A01–A32 适用联验。内容、工具和部署证据分别签发，但 DAS `1.5.0` 正式发布与对应工具的正式支持声明必须共同满足冻结门槛；此前可独立分发标明能力限制的候选内容包。任何具体产品仍须完成采用层验证。A30 的通用授权事故、撤销和恢复不得按“没有评测”判为不适用。

发布验收逐项映射 F01–F11、S/O/C 责任与 A 场景，区分规范内容、工具实现、参考部署和具体项目采用的分母。F06–F08 的条件性允许无相应业务的项目证明不适用；不能让官方配套以自身无 HTTP/UI/密封业务为由跳过已冻结的契约消费与控制实现。用最小受控 HTTP、UI 和密封评测样本证明各自承诺的支持，既不要求完整业务平台，也不要求每个采用项目部署这些样本。unsupported 用于尚未支持的环境、适配器或动作组合，不能替代整个冻结能力的交付。

正式采用结论须绑定采用主体、标准/工具精确制品、部署配置、受保护目标、事实/政策、适用范围和证据有效区间。它只证明所记录范围与时点的条件，不能形成永久可信标记。身份、隔离、目标保护、信任根或相关运行材料发生影响控制的漂移时，停止受影响动作；经可信影响分析与必要重验后才恢复。新的受保护动作仍逐次检查当前权威，参考部署通过或一次采用批准不能替代该检查。

**验证器自身的可执行门禁。** 安全与发布判定必须使用在支持运行模式下仍然生效的显式检查和失败传播。`assert`、调试日志或被优化器移除的契约检查不能作为唯一授权/摘要/闭包门禁。固定公开基线的 `scripts/verify` 在版本、路径和摘要检查中使用了 Python `assert`；Python 优化模式可移除断言。[VERIFY](#ref-verify)、[PY-ASSERT](#ref-py-assert)。应改成明确条件与异常/非零退出，限制受治理启动环境，并覆盖优化模式、环境注入及未支持运行参数的反例。测试框架内的开发断言与面向不可信输入的生产拒绝分开管理。

整个验证入口只有在全部所需子步骤结束、完整报告和必须工件写入成功后才产生最终成功。阶段日志必须标明阶段，不能提前输出易被消费为全链完成的 PASS；包装器正确传播子进程、管道和报告写入失败。消费端按 S12 核验实际报告与执行链，不能搜索控制台中的 PASS 字样决定发布。

Beta包分发、受控试用和正式发布遵守 13.21 节生命周期。标准内容可独立阅读、分发和验证；官方配套的正式发布门槛仍按冻结范围联验。技术中立的标准语义允许其他实现提供等效证据，不要求采用项目部署指定工具或业务产品才能理解/实现标准。公开 README、兼容矩阵和发布治理须把这一分工写清，保持与规范一致。

**最终发布材料的可重取性。** 标准发布入口将精确源码 revision、可重建内容及实际分发压缩包作为不同身份。平台自动生成的源码归档可能保持内容而重新生成不同压缩字节；获批的不可变正式/预发布包应自行封存并作为固定资产分发，或使用提供等效字节保证的工件存储。[RELEASE-ASSETS](#ref-release-assets)。自动源码归档可用于受控获取与源码清单核对，不能仅凭其 commit URL 承诺同一压缩包 hash 永久可重取。附加签名和证明留在包外或按既有无自引用结构绑定。

发布实现先准备非生效暂存/草稿，核对全部必需资产及其实际下载字节，再在受权入口完成可见发布。平台支持不可变 release 时先附齐全部必需资产再发布；不支持时采用等效受保护存储与激活入口。发布后读取平台回执和完整资产集合，确认不存在漏项、同名错包或竞态替换；结果未知保留同一动作身份核对，不能把半包发布记为完整成功。准备步骤属于同一个发布动作计划，不增加标准版本或独立治理系统。

**强制验证边界。** 发布入口核对实际工件摘要、来源、支持矩阵、测试覆盖和所有硬停止条件。必须 gate 缺结果、已知绕过未修复或证据来自不同候选时，拒绝配套正式就绪。

正式包必须是从已验证候选生成并核验的精确制品。纯版本/打包身份变化也需重新核对顶层摘要、锁、manifest 与签发，不能直接把预发布包的顶层证明附到不同字节的正式包；允许按受保护影响分析复用未变子工件的有效证据。发布签名不得要求包内嵌入其自身最终压缩包摘要，避免发布闭包自引用。

<a id="shared-contracts"></a>
### 13.20 共享契约与受保护决定

本节是 S09–S14 的共同实施语义。交换对象正式启用前，必须落成 schema、语义说明、合法/非法 fixtures、错误契约与 producer/consumer 互操作测试；下表中的语义名称不表示当前 CLI 或协议已经实现。标准定义最低语义、精确合同的规范身份及兼容义务；每份 schema/签名合同只有一个受治理作者源。官方配套复用唯一受治理协议作者；发布闭包固定其版本、摘要和规范映射，各消费者使用同一合同。相同合同可由其他合格实现独立实现；不得将某个可执行工具或未经锁定的上游分支变成规范权威。不同表示须通过明确批准的无损适配进入相同合同，不能绕过精确 schema 或签名绑定。

#### 13.20.1 消息职责与签发权限

| 对象 | 最低绑定 | 有权产生者 | 不得承担的职责 |
|---|---|---|---|
| 经核准事实/政策引用与 Bundle Resolution | scope、来源、批准、标准/规则/事实/政策摘要、目标、unknown/conflict | 事实由有权控制面批准；Bundle 由受保护解析器计算 | 不能让扫描结果自我批准或让派生列表成为作者源 |
| Change / Task Binding | 不重新分配的受保护 Change/Task 身份、状态代次/任务集合、完整 taskKey、义务摘要、revision、cycle、目标与 required-for-action、批准主体 | 受保护治理批准入口 | 不能仅凭可编辑任务列表产生当前权威，不能把取消或替代当成功 |
| 动作裁定 Decision | 指定主体/受众/scope/action、taskKey、候选/目标前提、计划/证据引用、事实/政策/信任状态摘要、有效区间、限定结论及原因 | 受信 Cadence 裁定链 | 不授予业务权限，不证明动作已经发生，不允许跨阶段复用为许可 |
| Candidate Binding | 内容闭包摘要、Task 引用、源版本、外部材料与构建来源 | 受保护快照执行器 | 不证明测试通过，不包括未来验证/完成记录 |
| 动作授权 | 发起/当前行为主体、受众、动作、规范化资源及创建实例、taskKey、businessActionId、参数摘要、有效授权依赖、有效期、policy、authority epoch、授权代次及共享额度 | 当前受权政策/批准服务 | 不兼任执行结果；不授权合同以外动作 |
| Verification Evidence | 精确候选、已批准验收/计划槽位、实际 run/attempt 与原始来源、分母/聚合、制品、工具、环境、结果与时效 | 受信采集/裁定/签发链 | 不直接授予资源写入权限，不把候选原始输出当可信断言 |
| Action Receipt | 稳定业务动作 ID、含原发起主体的不可变请求指纹、实际执行主体/授权引用、最终资源前提、受理/发送/提交阶段、执行结果、可信顺序与副作用状态 | 实际受保护资源执行点 | 不作为新动作授权，不以超时代表未执行 |
| Integration Receipt | 源候选、实际集成候选、后者的验证、目标、提交前后版本、动作 ID | 受保护集成入口 | 不把旧分支名或准备状态当已集成 |
| Completion 记录 | taskKey/revision/cycle、父 Change 及状态前提、适用验证/集成/责任证据、当前政策、完成唯一键 | 受保护完成入口 | 不修改原始 outcome，不作为无限期现时许可 |

所有安全对象区分 `contract identity`、schema 身份、消息用途与范围。正式 wire 合同必须精确规定 required/optional、缺省值、时间/代次类型、消息大小、摘要算法、签名覆盖范围和错误行为。编号、时间和预算不能依赖可能丢精度的隐式数字转换。现有 Cadence envelope 可满足的部分直接映射；无法无损承载的部分用明确的新契约身份，保持旧 schema 的读写承诺。

#### 13.20.2 裁定与结果保持独立

原 verify report 仍使用原有 outcome。受治理裁定单独表达是否允许某个指定动作，以及机器可识别的原因：授权缺失、上下文不匹配、验收未满足、必需证据缺失、前提已变化、能力不支持、信任状态不可用、外部结果未知。任何未知、错误或缺失不能默认允许。

Decision 的允许/拒绝是针对精确上下文的资格裁定，与原报告 outcome 分开；错误、unknown 和 unsupported 使用明确拒绝原因，不产生隐式允许。仅允许提交候选的 Decision 不能用于 integrate、complete、close 或 release。资源入口在实际动作线性化前重新认证当前调用者，取得独立有效授权，复核 Decision 的用途、受众、taskKey、候选、规范化资源/目标版本/代次、父子状态、政策、有效授权依赖及必需证据有效性。读取快照后发生相关变化时，重新裁定或经受保护等价规则确认；仅验证旧 Decision 的签名和有效期不足以继续执行。

对零信任最低控制，实际拒绝/隔离/不可篡改结果必须由强制机制和实测证据支持，人工签字不能替代。设计质量、需求取舍等定性义务可以由独立有权审查满足；审查记录必须有明确 scope、候选、义务、决策和有效期。允许工程层例外时，原失败和例外分别保存，受保护裁定明确其适用限制；不能标为无条件完整通过。

#### 13.20.3 受保护完成顺序

```text
当前控制面 → 批准 Task / 事实 / 验收
         → 固定源候选 C
         → 物化目标基线 B 上的实际集成候选 I
         → 验证 I（允许按受保护规则复用 C 的有效子证据）
         → 当前 Change / Task / 目标前提及动作裁定复核
         → 独立授权 / 预算 / 代次复核与稳定业务动作意图
         → 目标入口 CAS(B → I) / 等效不可绕过提交
         → 记录实际 Integration Receipt
         → 核对当前任务与政策，唯一提交 Completion
         → 生成非权威状态投影
```

不需要集成的任务使用预先批准的完成分支。集成成功但完成持久化失败时，根据动作 ID 与可信目标历史恢复，只补记真实完成所需事实，不再次执行集成；资格条件尚不成立时保持已集成但未完成。目标发生 ABA 式回退/回放时，使用受保护目标代次或等效不可回滚事务序列检测，不能仅比较一个可往返的分支值。

<a id="release-lifecycle"></a>
### 13.21 Beta 预发布、受控试用与正式发布

本节规定 F10/F11 的交付生命周期：`1.5.0-beta.1 → 必要的后续 1.5.0-beta.N → 1.5.0`。N 为本项目从 1 开始递增的正整数，采用不带前导零的十进制标识。后续 beta 只在需要向试用者交付新的发行工件时发布，不为每次讨论、文档编辑或源码提交发版；无需经过 alpha 或 RC。方案、开发提交和实际发行分别识别，本文件不证明任何版本已经发布或通过部署验收。

#### 13.21.1 发行身份与使用准入

| 对象/状态 | 身份与最低条件 | 可以支持的结论 | 受保护使用边界 |
|---|---|---|---|
| Beta 目标的开发与方案 | 首个拟发行目标 `1.5.0-beta.1`；每次受测源码、构建、合同及配置固定提交和摘要；缺口明确 | 该精确输入的设计、自检或隔离实验结果 | 缺少适用 Z01–Z12 的能力保持关闭，仅做获准只读分析或无真实权限隔离实验 |
| 首个可发行 beta | F01–F11 的拟交付语义、试用交换合同与对应实现齐备；三仓试用组合、开源参考执行链及最小领域样本可运行；拟开启动作无未关闭硬停止问题 | `1.5.0-beta.1` 的实际支持范围与获准试用结果 | 实际启用路径具有适用控制和准入证据；未支持环境/组合关闭，尚未完成正式试用退出不能声明正式配套就绪 |
| 后续必要 beta | 修复范围、兼容影响、迁移/回退及证据复用已经判定；新包完整自检、受影响测试和准入批准完成 | 该精确 `1.5.0-beta.N` 的限定结论，保留旧版本问题及试用记录 | 原包不覆盖；安装和激活独立批准；新编号不能自动清除事故、预算、待核对动作或证据缺口 |
| 正式 `1.5.0` | 本版全部正式门槛、适用 A01–A32、三仓及参考部署、试用退出、最终兼容裁定、最终包核验和独立发布批准完成 | 正式标准及已验证工具组合的支持；具体项目另有采用证据 | 单次动作继续检查当前权威；正式号不授予永久信任 |

首个 beta 的准入条件是项目规定的交付门槛，SemVer 不替项目定义成熟度。开发中能力未齐时继续保持未发布状态；不得通过 beta 名称把未实现能力标为已支持。正式验收仍按原冻结分母完成，不以预发布自检替代。

**精确选择与版本比较。** 预发布渠道由有权主体显式选择，继续锁定1.4的项目不自动迁入。DAS版本采用 SemVer 解析，`beta.2 < beta.10 < 1.5.0`；不得按普通字符串排序或删除后缀。`+beta.1` 是构建元数据，不能表达相同的预发布优先级。[SEMVER](#ref-semver)。版本优先级、包管理器匹配范围和资源授权分别判断。受保护入口核对获批目标、源码、实际包摘要、支持矩阵、协议及当前信任；未来 beta 未在验证过的支持关系中时拒绝新用途，不能仅凭共同 `1.5.0` 前缀接受。

**发行不可变性与必要修复。** 每个已经发布的 `1.5.0-beta.N` 及正式版均固定其包、清单和 tag 绑定。同一精确坐标不得换字节；相同字节的重传/镜像可以按幂等规则核对。公开交付修复后的包时分配下一个尚未使用的 beta 编号，重新验证及发布，保留原包与原始事件。失败或撤销的已发布编号不重复使用。无需公开发行的受控开发修订按精确提交/摘要/批准试用，明确标为未发布，不能借相同版本字符串覆盖任何已发布对象。

**Beta 间兼容与状态迁移。** 逐次明确 reader、writer、schema/协议、部署及存储支持关系。beta 名称不免除已作出的兼容承诺；确有不兼容试验变更时，版本化交换合同并提供明确迁移或拒绝，禁止同 schema identity 改义。升级先核验新制品及迁移计划，再在受保护边界切换；状态库采用 S13 的事务、备份及恢复要求。代码回退不能回滚授权撤销、预算、业务动作去重、Completion 或审计历史；旧工具无法读取新状态时，使用获批恢复/前向修复路径，不强开旧 writer。

**标准号与工具包号。** DAS 采用目标、dasops/Cadence 自身发行版本、协议版本和部署代次分别管理。Python 包规则接受带分隔符的 beta 拼写并规范化：`1.5.0-beta.1` 可解析为 `1.5.0b1`。[PY-PACKAGING](#ref-py-packaging)。工具包使用其生态的规范化合法版本；DAS 目标字段保持获批 SemVer 表示。两者允许不同编号，不要求三个仓库同时递增；支持矩阵通过精确版本和摘要关联，不能把包解析成功等同于标准支持或受保护授权。SemVer 的构建元数据规则不得直接套用到 PEP 440 的 local version 比较。

#### 13.21.2 试用计划及退出条件

试用复用已有 Change/Task、检查计划和部署记录；在结果产生前批准验收分母，调整时保留原计划、失败与影响判断，不新增平行审批系统。

| 计划信息 | 必须明确的内容 |
|---|---|
| 精确对象 | 本次 beta 号或明确未发布修订、源码/内容摘要、三仓制品及协议、运行库/适配器、系统配置、政策、试用主体和资源/数据范围 |
| 覆盖分母 | 通用受保护执行链及配套最小 HTTP/UI/密封样本；实际采用项目的领域适用性单独证明；业务循环、正常成功及状态转换的计量口径 |
| 观察安排 | 事先确定观察窗口、有效负载、并发、故障及恢复场景、可接受非安全缺陷和性能范围；静置天数不能替代实际覆盖 |
| 升级与恢复 | 必要 beta 间安装/激活、旧新消费者、状态迁移、代码回退、撤销、目标竞争、进程/系统故障和备份核对；退出方法与负责人 |
| 证据与问题 | 原始运行、候选/计划身份、失败/重试/事故、N/A批准、修复、受影响重验及旧证据复用映射；对外信息按 S13 披露 |
| 停止与批准 | 硬停止问题关闭受影响路径；影响未明阻断相关资格；继续试用和正式发布由独立有权主体批准 |

不规定统一试用天数或统一业务评分阈值。转正式同时要求观察条件和实际覆盖完成、全部适用强制验收通过、兼容/迁移/恢复证据有效、硬停止问题关闭。无反馈、长期未修改或一次绿色 CI 均不能单独满足条件。仅有第一份 beta 且条件已经满足时可以直接正式发布；后续 beta 不构成必经次数。

修复或配置变更后，按可信影响关系决定旧运行证据及观察覆盖是否仍有效。关系不明时不复用；明确无关的文字修复不机械重跑全部业务。安全边界、失败处理、运行库修复或关键版本适配改变时，重新覆盖有关拒绝测试、正向对照、恢复及观察。不得把多个不同实现各自通过的子集拼成从未共同验收过的最终部署。

#### 13.21.3 最终制品与证据绑定

正式 `1.5.0` 形成新的不可变发布身份。它可以采用已验证 beta 内容及完成必要重验的开发修订；发布前逐项核对最终输入、输出、工具支持与部署关系。只有未变且仍符合批准计划、来源和有效期的子工件证据可复用。版本、manifest、索引、锁、签名或安装元数据改变时，重新核对最终包闭包和顶层证据，不能将某个 beta 包的顶层签名附给不同字节。

发布元数据记录标准目标、渠道、源码 revision、工具/内容摘要、状态和签发依据。实际发布事件由包外追加的受保护回执记录，绑定此前封存的包、目标和平台结果；不得事后回写包内时间改变已验证字节。旧 `releasedAt` 保留原合同的值及精度，新映射区分包内日期声明和包外实际事件。计划日期、源码提交时间和 `SOURCE_DATE_EPOCH` 不能填作实际发布回执时间。[RELEASE-TIME](#ref-release-time)。文档状态、gate cadence、版本渠道和部署资格分开表达。

平台预发布/最新标记、标题和说明只用于展示与发现。取消预发布勾选不产生正式 `1.5.0`；受权事故公告不改变已发布包、tag绑定或原始回执。[RELEASE-ASSETS](#ref-release-assets)。下载、安装和激活分别验收；历史签名或试用通过不自动转成新的正式采用记录。事故处置和业务回退保留当前安全下界及历史账本。

#### 13.21.4 发布入口判定顺序

1. 读取独立批准的本次精确目标、渠道及支持矩阵，允许获批 `1.5.0-beta.N` 或正式 `1.5.0`；核对编号分配、兼容裁定和阶段准入，拒绝 Agent 擅自改目标。
2. 核验最终制品、来源提交、依赖闭包、三仓/协议关系及当前信任，确认已发布坐标不被覆盖，禁止跨 beta 混装。
3. 按本次目标的获批计划核对检查槽位、实际运行/合法复用、试用覆盖及硬停止问题；正式目标满足全部正式门槛，未运行保持 `not_run`。
4. 重新校验发布身份、授权、预算、目标代次和持久化意图；暂存/草稿、资产上传、最终公开各有稳定动作键，发布后回读完整工件并追加实际回执。结果未知时核对原动作，不换键重发。
5. 具体项目核对最终包与自身真实部署后取得限定采用结论；后续变更、撤销及单次动作继续执行原控制。

#### Informative references

These links identify mechanisms; they are not dynamically loaded normative rules or proof of a deployment.

<a id="ref-a11y"></a>
- **A11Y**: [WAI：Selecting Web Accessibility Evaluation Tools](https://www.w3.org/WAI/test-evaluate/tools/selecting/); [Appendix D](https://raw.githubusercontent.com/AzzCraft/das-standard/cd4398f6df5574813f40bb7ab62404a31ed38b50/appendices/appendix-d-ui-spec-appendix-template.md); [Appendix H](https://raw.githubusercontent.com/AzzCraft/das-standard/cd4398f6df5574813f40bb7ab62404a31ed38b50/appendices/appendix-h-ui-design-review-checklist.md)
<a id="ref-adaptive-eval"></a>
- **ADAPTIVE-EVAL**: [Dwork 等：Generalization in Adaptive Data Analysis and Holdout Reuse，2015](https://arxiv.org/abs/1506.02629); [作者论文介绍](https://www.cis.upenn.edu/~aaroth/reusable.html)
<a id="ref-archive-safety"></a>
- **ARCHIVE-SAFETY**: [Python tarfile：Extraction filters 与 Hints for further verification](https://docs.python.org/3/library/tarfile.html#extraction-filters)
<a id="ref-aria"></a>
- **ARIA**: [WAI-ARIA APG：Dialog Modal Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/); [WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)
<a id="ref-artifact-durability"></a>
- **ARTIFACT-DURABILITY**: [Linux fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html); [rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html)
<a id="ref-async-cancellation"></a>
- **ASYNC-CANCELLATION**: [Python 3.13 asyncio任务文档](https://docs.python.org/3.13/library/asyncio-task.html); [asyncio异常](https://docs.python.org/3.13/library/asyncio-exceptions.html); [concurrent.futures](https://docs.python.org/3.13/library/concurrent.futures.html)
<a id="ref-ci-checks"></a>
- **CI-CHECKS**: [GitHub：Troubleshooting required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks); [About status checks](https://docs.github.com/en/pull-requests/reference/status-checks)
<a id="ref-ci-security"></a>
- **CI-SECURITY**: [GitHub Actions Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
<a id="ref-clock-semantics"></a>
- **CLOCK-SEMANTICS**: [Linux Kernel：ktime accessors](https://www.kernel.org/doc/html/latest/core-api/timekeeping.html)
<a id="ref-dsse"></a>
- **DSSE**: [协议 1.0.2，2024-05-10](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md)
<a id="ref-eval-practice"></a>
- **EVAL-PRACTICE**: [scikit-learn：Common pitfalls / Data leakage](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage)
<a id="ref-git-snapshot"></a>
- **GIT-SNAPSHOT**: [Git archive：ATTRIBUTES](https://git-scm.com/docs/git-archive#_attributes); [Git：SECURITY](https://git-scm.com/docs/git#_security)
<a id="ref-http-digest"></a>
- **HTTP-DIGEST**: [RFC 9530 §§2–3、6.4–6.5、Appendix A](https://www.rfc-editor.org/rfc/rfc9530.html); [RFC 9110 §14 Range](https://www.rfc-editor.org/rfc/rfc9110.html#section-14); [§15.4.5 304](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.4.5)
<a id="ref-http-early-data"></a>
- **HTTP-EARLY-DATA**: [RFC 8470 §§3–6](https://www.rfc-editor.org/rfc/rfc8470.html); [RFC 8446 §8](https://www.rfc-editor.org/rfc/rfc8446.html#section-8)
<a id="ref-http-framing"></a>
- **HTTP-FRAMING**: [RFC 9112 §§2–3、6、11](https://www.rfc-editor.org/rfc/rfc9112.html); [Crystal HTTP::Server解析分歧公告（2026-05-26）](https://crystal-lang.org/2026/05/26/http-request-smuggling-vulnerability-in-http-server/)
<a id="ref-http-semantics"></a>
- **HTTP-SEMANTICS**: [RFC 9110 §13.1.1 If-Match](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.1); [§13.2.1 条件求值](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.2.1); [§15.3.3 202 Accepted](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3)
<a id="ref-json-runtime"></a>
- **JSON-RUNTIME**: [Go 1.25.0 encoding/json 文档](https://pkg.go.dev/encoding/json@go1.25.0); [对应固定源码](https://raw.githubusercontent.com/golang/go/go1.25.0/src/encoding/json/decode.go)
<a id="ref-jwt-bcp"></a>
- **JWT-BCP**: [RFC 8725 §§3.1–3.12](https://www.rfc-editor.org/rfc/rfc8725.html#section-3)
<a id="ref-log-data"></a>
- **LOG-DATA**: [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html); [Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
<a id="ref-man"></a>
- **MAN**: [Standard manifest](standard_manifest.json)
<a id="ref-mount-topology"></a>
- **MOUNT-TOPOLOGY**: [Docker bind-mount 文档](https://docs.docker.com/engine/storage/bind-mounts/)
<a id="ref-oas"></a>
- **OAS**: [OpenAPI Specification 3.1.1](https://spec.openapis.org/oas/v3.1.1.html)
<a id="ref-oci-identity"></a>
- **OCI-IDENTITY**: [Image Index](https://github.com/opencontainers/image-spec/blob/v1.1.0/image-index.md); [Descriptor](https://github.com/opencontainers/image-spec/blob/v1.1.0/descriptor.md); [Configuration](https://github.com/opencontainers/image-spec/blob/v1.1.0/config.md)
<a id="ref-opa"></a>
- **OPA**: [Policy Language：Errors](https://www.openpolicyagent.org/docs/policy-language#errors)
<a id="ref-process-arguments"></a>
- **PROCESS-ARGUMENTS**: [OWASP OS Command Injection Defense Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html); [Python 3.13 subprocess 文档](https://docs.python.org/3.13/library/subprocess.html#security-considerations)
<a id="ref-py-assert"></a>
- **PY-ASSERT**: [Python 语言参考 §7.3](https://docs.python.org/3.13/reference/simple_stmts.html#the-assert-statement)
<a id="ref-py-packaging"></a>
- **PY-PACKAGING**: [Python Packaging：Version specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/)
<a id="ref-pytest-discovery"></a>
- **PYTEST-DISCOVERY**: [pytest插件加载顺序](https://docs.pytest.org/en/stable/how-to/writing_plugins.html#plugin-discovery-order-at-tool-startup); [插件管理](https://docs.pytest.org/en/stable/how-to/plugins.html); [verify脚本](https://raw.githubusercontent.com/AzzCraft/das-standard/cd4398f6df5574813f40bb7ab62404a31ed38b50/scripts/verify)
<a id="ref-pytest-outcomes"></a>
- **PYTEST-OUTCOMES**: [pytest skip/xfail、strict和run参数](https://docs.pytest.org/en/stable/how-to/skipping.html)
<a id="ref-python-build"></a>
- **PYTHON-BUILD**: [PEP 517](https://peps.python.org/pep-0517/); [pip Build System Interface](https://pip.pypa.io/en/stable/reference/build-system/); [pip install / dry-run](https://pip.pypa.io/en/stable/cli/pip_install/)
<a id="ref-release-assets"></a>
- **RELEASE-ASSETS**: [GitHub：Downloading source code archives](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives); [Managing releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository); [Immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
<a id="ref-release-time"></a>
- **RELEASE-TIME**: [GitHub：About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases); [Reproducible Builds：SOURCE_DATE_EPOCH specification](https://reproducible-builds.org/specs/source-date-epoch/)
<a id="ref-resource-id"></a>
- **RESOURCE-ID**: [RFC 7643 §3.1：Common Attributes](https://www.rfc-editor.org/rfc/rfc7643.html#section-3.1)
<a id="ref-retry-practice"></a>
- **RETRY-PRACTICE**: [AWS SDK retry behavior](https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html); [Amazon Builders’ Library：Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
<a id="ref-schema-2020"></a>
- **SCHEMA-2020**: [JSON Schema Validation，Draft 2020-12 发布文本](https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-validation-01)
<a id="ref-seccomp-notify"></a>
- **SECCOMP-NOTIFY**: [Linux man-pages：seccomp_unotify(2)，NOTES](https://man7.org/linux/man-pages/man2/seccomp_unotify.2.html); [Linux Kernel：Seccomp BPF/User notifications](https://docs.kernel.org/userspace-api/seccomp_filter.html)
<a id="ref-semver"></a>
- **SEMVER**: [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
<a id="ref-sigstore"></a>
- **SIGSTORE**: [Cosign：Verifying signatures](https://docs.sigstore.dev/cosign/verifying/verify/); [Sigstore threat model](https://docs.sigstore.dev/about/threat-model/)
<a id="ref-slsa"></a>
- **SLSA**: [Build requirements v1.2](https://slsa.dev/spec/v1.2/build-requirements)
<a id="ref-sql-transactions"></a>
- **SQL-TRANSACTIONS**: [Python sqlite3：连接上下文与事务控制](https://docs.python.org/3/library/sqlite3.html#how-to-use-the-connection-context-manager); [SQLite Isolation](https://www.sqlite.org/isolation.html); [SQLite BEGIN/事务](https://www.sqlite.org/lang_transaction.html)
<a id="ref-sqlite-backup"></a>
- **SQLITE-BACKUP**: [SQLite Online Backup API](https://sqlite.org/backup.html); [WAL §1、§4](https://sqlite.org/wal.html)
<a id="ref-sqlite-durability"></a>
- **SQLITE-DURABILITY**: [SQLite PRAGMA synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous); [WAL](https://www.sqlite.org/wal.html); [2021-07-08 讨论](https://sqlite.org/forum/info/d1a6bc7c4cd2baca)
<a id="ref-sqlite-integrity"></a>
- **SQLITE-INTEGRITY**: [SQLite CREATE TABLE](https://www.sqlite.org/lang_createtable.html); [Foreign Key Support](https://www.sqlite.org/foreignkeys.html); [ON CONFLICT](https://www.sqlite.org/lang_conflict.html)
<a id="ref-sqlite-wal-fix"></a>
- **SQLITE-WAL-FIX**: [SQLite WAL §11](https://sqlite.org/wal.html); [3.51.3 发布说明](https://sqlite.org/releaselog/3_51_3.html); [运行库version/source ID](https://sqlite.org/c3ref/libversion.html)
<a id="ref-sse-transport"></a>
- **SSE-TRANSPORT**: [WHATWG HTML：Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)
<a id="ref-std"></a>
- **STD**: [Standard specification](SPECIFICATION.md)
<a id="ref-tuf"></a>
- **TUF**: [The Update Framework specification 1.0.19](https://theupdateframework.github.io/specification/v1.0.19/)
<a id="ref-ui-async"></a>
- **UI-ASYNC**: [React：useEffect 的数据获取示例](https://react.dev/reference/react/useEffect#fetching-data-with-effects); [Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)
<a id="ref-verify"></a>
- **VERIFY**: [Standard verify entrypoint](scripts/verify)
<a id="ref-wcag"></a>
- **WCAG**: [WCAG 2.2：Conformance](https://www.w3.org/TR/WCAG22/#conformance); [Understanding Conformance](https://www.w3.org/WAI/WCAG22/Understanding/conformance)
<a id="ref-yaml-profile"></a>
- **YAML-PROFILE**: [YAML 1.2.2 规范](https://yaml.org/spec/1.2.2/); [PyYAML 文档](https://pyyaml.org/wiki/PyYAMLDocumentation); [PyYAML #165](https://github.com/yaml/pyyaml/issues/165)

#### Edition acceptance obligations (generated)

Effect: **normative**; lifecycle: **draft / unpublished content candidate**.

This is the adopted acceptance denominator, not a run report. All 136 product cases remain **not_run** until protected evidence proves their actual outcomes. S labels refer to [the normative additions](modules/edition-1.5.md); O/C identify companion implementation responsibilities. Equivalent implementations must satisfy the same obligations. The case table must not be reduced to make a candidate qualify.

#### 2. 契约交付清单

每个正式互操作对象须有唯一规范来源、精确 schema、字段语义、失败行为、正反 fixtures 和消费端验证；安全输入还需固定实际 JSON/YAML 解析及类型绑定规则；下列名称是职责标识，不能当作当前仓库已存在的文件或命令。已有合同能够无损满足时直接复用，新增映射不得破坏旧消费者。

| 工件族/接口 | 主定义 | 产生/消费责任 | 正式交付证据 |
|---|---|---|---|
| Standard Module 目录、requirement 映射、Bundle | S01–S03 | DAS 定义；Cadence 解析；dasops 消费 | schema/dialect/配置、闭包、单一作者映射、三值/冲突/引擎错误、组合 fixtures、生成视图 |
| 经核准事实与政策引用 | S02/S09 | 控制面批准；dasops 提案；Cadence 验证 | 来源/批准/目标绑定、实际控制权限与变更生效测试 |
| Change / Task / Candidate Binding | S08/S11/S14、共享契约 | 受保护治理与快照入口产生；Cadence/集成/完成入口消费 | 完整 taskKey、身份不重分配/退役映射、非空/唯一/父子关系、状态代次与动作表、行政误关闭窄条件、原始树/物化/输出清单、OCI实际child/平台/层映射与并发测试 |
| 动作裁定 Decision | S12、[共享契约 §13.20.2](modules/edition-1.5.md#shared-contracts) | Cadence 对固定上下文裁定；资源入口复核当前前提 | 精确用途/受众/动作、资格与授权分离、必需/观察槽位分层、对象实例与过时快照及跨阶段拒绝 |
| 动作授权与 Action Receipt | S10/S13/S18、共享契约 | 授权服务批准；实际资源入口执行并出据 | 稳定业务动作键、有效委派与共享预算、规范化资源/创建实例、发送/披露/撤销边界、持续读取、原生条件/受理/终态、跨层重试、实际argv解释、异步取消及未知结果；迁移计划的 preimage/postimage、实际修改边界与只读输出权限 |
| 验证与签发 envelope | S08/S11/S12、共享契约 | 域外采集/裁定/签发；各受保护入口消费 | 精确签名 profile/原始字节、令牌用途互斥与受保护密钥解析、可信时间/实例恢复、CI 最终 gate/计划槽位及原生测试状态映射、实际测试资源及初始化/清理授权、原始运行/缓存来源、工件持久登记、HTTP摘要字节域与重组、原始数据/安全展示、历史核对/现时资格、失陷倒签/撤销/时效/重放 fixtures |
| Integration / Completion 记录 | S14、共享契约 | 集成入口及完成入口分别签发 | C→I 映射、目标前后身份、CAS/代次、唯一键、恢复及不重开任务的限定重新验证 |
| 新文本增量 Reference Contract / transport | S05–S08 | 受支持 producer/consumer；Cadence 验证 | Pointer、增量、全程资源/重连预算、原子水位、传输/应用结束、最终摘要与兼容 fixtures |
| HTTP 声明与 normalized inventory | S15 | 产品提供事实；Cadence adapter 校验 | 作者源、覆盖、ID 历史、OpenAPI/dialect、安全组合/继承、分帧/转发一致性、引用闭包及实际入口证据 |
| UI 工作流与行为证据映射 | S16 | 产品定义；受控 runner/独立审查产生 | 既有页面约定、固定分母、内容/阅读/异步/保存/历史/token、构建/基线/环境及分层无障碍证据 |
| 普通/密封评测协议与资格证据 | S17 | 评测系统执行；Cadence 校验；dasops 只处理受限引用 | 候选/协议/评分器/数据、访问边界、分母/失败处理、反馈与选择历史、预算及追加处置 |
| 锁定支持矩阵与发布/部署证据 | S18/S19 | 三仓发布及部署 owner | 本次 beta/正式目标、不可变发布坐标、受控未发布源码修订及摘要、包生态映射、三仓支持、试用/转版证据、存储持久/关系约束/真实事务及集合串行化、固定发布资产与包外回执、采用有效期及漂移失效 |

正式交换前必须明确签名算法与密钥策略、时间/撤销界限、消息大小、结果未知处理、错误码及支持窗口。无法给出精确合同或真实 enforcement 的组合标为 unsupported；不得以占位字段、演示密钥或“后续配置”开启受保护运行。

#### 3. 最小参考部署责任矩阵

以下为逻辑权限角色，可以在同一受控 Linux 主机上实现；是否允许合并进程/身份取决于能否保持相应隔离。不能仅凭角色名称、不同账号字符串或配置字段证明独立。

| 角色 | 允许 | 禁止/必须隔离 |
|---|---|---|
| Agent 开发/提交身份 | 修改获准候选工作区；提交有界请求；读取获准反馈 | 生效政策、管理/签发身份、受保护 refs/发布库、宿主秘密、密封运行的私有输入/日志/缓存 |
| 隔离候选执行身份 | 使用锁定候选；仅接收合同批准的任务输入和有界密封推理输入；写本次独立输出 | 标签、秘密评分材料、控制面/驱动/签发权限、未授权网络；不得向开发身份导出私有运行材料 |
| 受权管理员/批准者 | 可信初始化、事实/政策/验收批准、撤销恢复 | 将自身凭据交给 Worker；只靠 Agent 自述批准控制生效 |
| dasops 受治理执行器 | 经授权快照、受保护版本树/条件迁移、事务状态、对接集成和完成；在隔离工件区发布有界计划 | 在特权地址空间执行候选/hooks；任意 shell/输出路径写入；借 dry-run 覆盖业务文件；仅凭工具锁覆盖仍可被直接编辑的目录；将数据参数解释为未批准选项/响应文件 |
| 测试驱动/观察器与 supervisor | 在 S11 获准测试资源上初始化、执行和清理；观察完整运行域、聚合限额；按 S13 执行预批准本地停止 | 与候选共享可污染解释器/结果目录；把测试身份当业务写权限；导出浏览器认证状态；以主进程/调用任务结束推定整域清理；仅凭顶层ro忽略子挂载；以审计故障阻塞停止或放行业务；仅凭用户态通知后的CONTINUE决定资源许可 |
| Cadence 裁定/签发 | 校验固定上下文、计划与可信结果；签发有用途/范围限制的证据 | 为任意 JSON 签章；继承候选身份；获得通用生产写权限；将候选文本解释为CI命令、批准字段或控制域主动内容 |
| 集成/资源入口 | 当前主体/授权依赖及最终资源复核、共享额度、fencing/CAS、实际执行并出据；受限读取入口执行有界交付及撤销确认 | 无门禁直写/续读；信任 owner 字符串/同名 CI 状态；把 receipt 当新授权；普通日志暴露带权链接 |
| 受保护审计/状态存储 | 持久化意图、结果、唯一键、身份分配/退役映射、检查点、恢复和历史；恢复后如实追加故障区间及记录缺口 | Worker 删除/覆盖/回滚；把旧身份分配给重建对象；业务 rollback 回滚审计；未知状态自动当未发生；补造未写成的原记录；未实际开启事务或不保护集合谓词就提交权威决定 |

参考部署清单还须给出实际发行版/内核、执行器/镜像摘要、受信安装与启动方式、网络/文件/设备/资源限制、递归挂载及传播/宿主写入关系、身份认证、时钟来源/误差/挂起/恢复及撤销策略、数据库/journal/同步、driver事务模式与writer/集合约束、工件/目录持久提交与跨存储恢复、实际取消/发送屏障及故障模型、目标保护、CI 身份/检查映射和操作恢复流程。探针在真实 Worker 身份运行，并有合法请求成功的对照。参考部署中只使用受控测试秘密及合成/批准样本。

#### 4. 验收子用例

共同证据至少包含：子用例 ID、父 A 编号、需求与检查实例映射、真实运行 ID、候选/政策/工具/部署身份、受测主体、前置状态、实际触发、可信观察、预期与实际结果、目标副作用前后状态、原始制品摘要与受保护证据引用。负向测试须记录实际拒绝点及可达性对照；测试框架异常、探针未执行和偶发不可达均不能记录为安全控制通过。

A01–A25、A30.1、A31–A32 中适用于工具/受治理执行链的要求不得通过业务标签规避。A26–A29 与 A30.2 的业务运行按经核准能力适用；配套工具对其宣称支持的领域必须用受控示例执行支持测试。任何 N/A 均独立保存事实和批准。子用例可以分解成更多 fixture，但不能用删除子用例缩小父场景含义。

| 子用例 | 输入/故障注入 | 预期行为 | 必需证据 | 责任映射 |
|---|---|---|---|---|
| A01.1 | 受权低风险修改，完成快照、独立验证、集成及完成 | 合法链成功；引用的任务、实际集成候选、政策和目标一致 | 完整回执链；正向运行与目标读取证据 | S10–S14；O05–O08；C04–C08 |
| A01.2 | 事前批准的纯分析任务，未改共享目标 | 按批准规则完成；不得事后临时取消集成要求 | Task Binding 的无集成条件、独立审查、Completion | S14；O06/O08；C07 |
| A01.3 | 首个beta的参考链与限定试用；必要后续beta及满足门槛后正式采用 | 只声明本次实际支持；缺少控制不开启；正式目标另行核验最终包及真实部署 | 精确beta/正式目标、三仓支持、当前批准、真实成功链和采用记录 | S19/发布生命周期；O01/O13；C14 |
| A02.1 | 在 CLI/RPC 中自报 admin、owner 或批准人 | 真实调用身份无相应权限时拒绝；不以字符串授予权限 | 认证身份、拒绝原因、无受保护写入的目标快照 | S09/S10；O04/O05；C04 |
| A02.2 | 同一 Agent 控制两个账号/进程互相批准 | 不得据此认定独立审批；未获外部授权时拒绝 | 主体控制关系、受权审批映射、正反身份对照 | S09；O04；C04 |
| A02.3 | 用其他项目的合法 hash/URI 取报告、缓存或密封材料，或借诊断接口导出 | 摘要不授予读取权；跨域/用途不匹配拒绝；有权验证器可在受限域核验 | 当前身份、对象域/用途、真实读取拒绝与合法读取对照 | S12/S13；O07/O10；C06/C12 |
| A03.1 | 修改仓库政策、验收 gate、scope 或标准目标 | 仅形成提案；当前已批准控制保持 | 生效政策摘要、提案内容、实际 required-for-action | S02/S09；O01/O02；C02/C04 |
| A03.2 | 用候选新根/新政策为自身激活签字 | 拒绝自举循环；合法轮换由当前信任链批准后生效 | 旧权威批准、激活事务、在途请求及旧代次处理 | S09/S12；O01/O10；C04/C06 |
| A04.1 | 缺字段、unknown、冲突来源或 exists(unknown) | 受影响强制义务未决；不能当 false 或 N/A | 求值轨迹、来源冲突、资格拒绝 | S02；O02；C02 |
| A04.2 | 隐藏已有 UI/HTTP 能力，或真实退役已独立批准 | 未批准删减被拒；获批真实退役按新快照重算 | 前后事实、扫描范围、批准与控制集合 | S02；O02；C02/C10/C11 |
| A04.3 | 策略内置函数错误/超时/无结果被映射为 undefined，再经否定；另测合法 false | 受影响求值失败或 unknown 保留，不能变成安全否定；合法全定义结果正常裁定 | 引擎/配置、完整求值轨迹、三值独立预期及正向对照 | S02；O02；C02 |
| A05.1 | 改写 resolvedModules 或解析器/规则摘要 | 重新计算发现不一致；不接受伪造 Bundle | 输入摘要、重算结果、拒绝记录 | S02/S03；O02；C01/C02 |
| A05.2 | 模块循环、叶子漏项、重复归属或允许的共享引用 | 非法闭包失败；合法 artifact 共享通过 | 独立正文清单、目录映射、DAG 正反 fixtures | S01/S03；C01 |
| A05.3 | 旧 manifest 条件与模块规则冲突、双写或漏映射；合法规则提取 | 冲突/漏项阻断；单一作者生成兼容视图并保持义务等价，不靠加载顺序覆盖 | 作者/派生映射、独立预期 fixtures、提取前后分母及冲突结果 | S02/S03；O02；C01/C02 |
| A06.1 | 真实 Worker 读取密钥/秘密、访问控制 socket 或调试驱动 | 实际权限拒绝；探针启动与目标存在得到正向确认 | Worker 身份、受保护审计、可达性对照 | S09/S11；O04；C05 |
| A06.2 | 经继承 fd、共享目录、代理或元数据服务获取权限 | 候选无旁路访问；合法有界业务连接仍可用 | 启动配置、fd/挂载/网络核验、连接正反结果 | S11；O04；C05/C09 |
| A07.1 | T-167/T-168/非数字 ID 加 force 完成 | 所有合法 ID 使用同一门禁；无证据不完成 | CLI、库、状态入口三层拒绝与状态差异 | S14；O06/O08；C07 |
| A07.2 | 手写 DONE 或通过直接库调用/投影回写改变完成 | 候选文本不成为权威；投影不偷换已验证摘要 | 候选摘要前后值、事件存储、投影再生成结果 | S08/S14；O06/O08；C07 |
| A08.1 | 调用旧工具、core-only、host-local 后提交受保护目标 | 可保留旧诊断；不能取得新目标写权限或资格 | 真实资源入口拒绝、工具身份、最低策略 | S09/S18；O01/O08/O12；C13 |
| A08.2 | 绕过分支经 tag/发布 API/管理 bypass 或伪造同名 CI check | 保护覆盖实际目标和签发身份；旁路失败 | 入口/凭据清单、check 发行者、目标拒绝记录 | S09；O08；C06/C13 |
| A08.3 | CI job 条件跳过显示成功、空矩阵、依赖取消或 merge-group 未运行；另测全部获批槽位完成 | 平台绿灯不能补足缺证据；准确 I 与计划有效时正常允许 | 平台事件与原始结论、最终 gate、槽位差异、目标入口拒绝/成功 | S12/S14；O08；C08/C13 |
| A09.1 | 授权撤销与副作用提交并发交错 | 线性化点前撤销必须拒绝；已发生动作如实记录 | 可控交错时序、资源版本、授权代次、回执 | S10；O05/O09；C07 |
| A09.2 | 离线快照过期、时钟回退或撤销状态不可取得 | 依赖失效状态的正常受保护写入停止；诊断可保留；本地安全停止按 S13 执行 | 时间/快照边界 fixtures、拒绝与恢复证据 | S12；O05/O10；C06/C13 |
| A09.3 | 请求已入 outbox 未发送时撤销，或已发出后远端晚到结果 | 未发送项停止；在途动作如实核对；迟到事实不产生新许可；缺目标 fencing 时不声称远端立即拒绝 | 发出/提交线性化记录、撤销顺序、远端状态及恢复轨迹 | S10；O05/O10；C07 |
| A09.4 | 父授权撤销/过期但子令牌仍未过期；分拆子令牌并发用额度；超出支持委派层级 | 上游失效后拒绝新动作；共享额度不复制；不支持层级拒绝，正常有界委派可用 | 受保护授权关系、当前主体、撤销顺序、额度事务及合法对照 | S10；O05；C04/资源入口 |
| A09.5 | 受限下载/订阅进行中撤销或到期；缓存反馈待释放；用旧带权地址重连、Range 或转交另一主体 | 新发送单元及可中止释放被拒；在途披露如实核对；旧路径仍可续读则不确认撤销完成；合法有界读取成功 | 当前受众/授权、发送单元上限、实际出口字节/顺序、旧地址拒绝、延迟反馈/预算与撤销确认记录 | S10/S13；O10；C06/C12/读取入口 |
| A09.6 | wall clock 回拨/误差越界、挂起超过授权期、重启或VM快照恢复旧相对deadline；另测明确续期 | 旧TTL和预算不重置；当前时间不可确认则停止相关新动作；合法续期/历史核对按其范围工作 | 受控时钟及实际支持环境记录、实例/控制代次、绝对/相对截止、入口拒绝与成功对照 | S12；O05/O10；C06/C14 |
| A09.7 | 对未发送、已交接线程/子进程、已不可撤回发送的动作分别取消等待；超时或屏蔽取消的工作随后产生结果 | 区分取消请求与实际终态；未知结果保留原动作/预算；不先冻结仍可写输出，不因换会话重放；合法未发送停止及迟到核对成功 | 受保护发送屏障/监督记录、前后资源与预算、清理状态；无效终态拒绝与正常完成对照 | S10/S11/S13；O05/O10；C05/C06 |
| A10.1 | 租约回收后旧 generation 续租、提交或完成 | 旧持有者在最终写入口被 fencing | 租约状态、资源拒绝、并发历史 | S10；O09；C07 |
| A10.2 | 并发完成或目标先变化再恢复原分支值（ABA） | 无重复完成/丢失更新；使用目标代次检测 ABA | CAS/事务序列、唯一键冲突、目标历史 | S14；O08/O09；C07 |
| A10.3 | with/自动提交未实际包住读写、延迟事务旧快照升级/拿锁后仍读旧集合、两个子项竞争共享额度/父关闭；合法串行及完整重试 | 写入前建立真实事务；集合决定可串行化；确认回滚后重读重算，不重复外部动作或发布暂定成功 | 实际driver/连接配置、BEGIN/COMMIT/ROLLBACK轨迹、两writer可控交错、前后集合/预算、错误分类和正向对照 | S13/S14；O06/O09；C07/C14 |
| A11.1 | 冻结后修改代码、文档、配置、测试、模型或 LFS/子模块 | 形成新候选；旧证据不可覆盖 | 内容闭包清单、真实材料摘要、新旧候选 | S08/S11；O07；C07 |
| A11.2 | 采集快照时并发写入，或依赖内容与名称不一致 | 不能发布撕裂快照；固定实际字节后才接受 | 暂存/冻结日志、逐项复核、并发与供应材料反例 | S11；O07；C09 |
| A11.3 | Worker 投毒计算缓存，或验证后重建成不同安装包/镜像 | 不得将普通缓存补签成可信来源；实际交付输出缺匹配验证时拒绝 | 输入/构建/输出清单、缓存来源、安装与发布字节身份 | S11；O07；C09/C14 |
| A11.4 | export-ignore/subst隐藏或改写纳管文件、dirty/untracked缺口、不可信.git配置；批准的精简导出 | 源树/物化/执行视图逐项绑定；无解释缺口和特权执行拒绝；合法发布变换不改变完整验收分母 | 原始tree与独立清单、变换规则及摘要、runner输入、低权限导入拒绝和合法映射 | S11；O04/O07；C09 |
| A11.5 | 同index选不同平台child、层顺序/diff_id错误、未知非选描述符、合法whiteout及挂载覆盖 | 实际child/平台/配置须匹配批准；非法或缺必需材料拒绝；合法层间变换及可跳过非选扩展不误拒 | index/child/config/原生层摘要与diff_id、实际启动/挂载、物化结果及单平台成功对照 | S08/S11；O07；C03/C05/C09 |
| A11.6 | pip dry-run/元数据后端产生无害标记、动态构建依赖换包、元数据回退构建 | 动态准备在受限域且无控制权限；不可信依赖不自动纳入；合法固定后端和输入可生成可核验工件 | 实际后端/动态依赖清单、构建域身份、目标写入拒绝、来源摘要及批准构建成功对照 | S11；O02/O04/O07；C05/C09 |
| A12.1 | 候选删除 gate、测试恒真或自动更新批准基线 | 已批准验收不变；变更只能进入独立审批 | 旧/新验收摘要、必要 gate 集合、审批隔离 | S11；O07；C04/C08 |
| A12.2 | 候选修改结果文件、共享解释器或对驱动注入/调试 | 不能产生安全关键可信 PASS；同进程结果仅按辅助证据使用 | 域外断言、权限反例、来源类型与正向测试 | S11/S12；C05/C06 |
| A12.3 | 特权 workflow 检出候选、跨 workflow 上传伪结果或污染共享缓存 | 候选不进入签发/写权限域，文件仍按原始来源鉴别；合法隔离测试与域外签发可用 | 真实权限/checkout/共享路径、执行材料身份、拒绝探针和正向链 | S11；O04；C05/C06/C09 |
| A12.4 | 禁用entrypoint autoload后conftest/显式插件/测试模块在collect-only时运行 | 从发现阶段即隔离；可信驱动只加载批准实现；候选收集不能写控制面或冒充驱动断言 | 启动配置、实际导入路径、标记触发与真实权限拒绝、合法隔离收集成功 | S11；O04；C04/C05 |
| A13.1 | 向签发/完成接口提交自制 PASS JSON | 不可信结果拒绝，不替任意 JSON 签章 | 认证采集入口与签发拒绝、未变化的完成库 | S12；O08；C06 |
| A13.2 | 将候选 stdout 伪装成 supervisor/驱动断言 | 保留原始工件身份，不提升可信级别 | 原始流、可信运行 ID、采集来源映射 | S11/S12；C05/C06 |
| A13.3 | 候选日志含CR/LF伪事件、终端控制、CI命令/输出分隔符、主动HTML/资源请求；合法多行日志 | 原始内容保留受限身份；展示不执行控制语法，不改变状态/批准/后续job输出；无未授权资源读取 | 原始及派生摘要、输出/控制文件权限、渲染和网络记录、真实事件字段前后值及合法展示 | S12/S13；O04/O10；C06 |
| A14.1 | 自签、错 issuer、错 audience、撤销密钥或篡改 payload | 签名或信任/上下文校验拒绝 | 签名 known-answer 与各类拒绝 fixtures | S08/S12；C03/C06 |
| A14.2 | 签名只覆盖报告，替换未签 policy/task/消息用途 | 不接受安全字段覆盖不完整或跨用途替换 | 精确签名输入、契约身份与字段篡改测试 | S08/S12；C03/C06 |
| A14.3 | 已失陷密钥签发倒填时间的回执；正常轮换前已被独立检查点固定的真实证据 | 自报早期时间不足以可信；按当前事故政策隔离/独立核对，合法历史不自动授予新许可 | 失陷范围、独立接收/检查点、确切字节、目标历史与限定裁定 | S12；O10；C06 |
| A14.4 | DSSE payload 重排、类型/keyid 替换、重复密钥多签；合法原生 envelope 或批准证书身份 | 按原生协议验证同一确切 payload；keyid 不授权，重复签名不增批准数；合法映射可用 | 原始字节/PAE已知答案、受信身份/算法、上下文及跨协议对照 | S08/S12；C03/C06 |
| A14.5 | 同issuer不同用途令牌互换、错误算法/密钥类型、任意jku/x5u或恶意kid；合法授权/证据分别输入 | 按已选协议互斥验证与受保护查键；不隐式回源，不把身份/授权令牌当证据；合法原生路径通过 | 协议/算法/issuer-key/audience/用途矩阵、网络拒绝、原始签名与上下文；非JWT实现等效用例 | S08/S10/S12；O05；C06 |
| A15.1 | 跨任务/revision/cycle/候选/政策/目标使用旧证据 | 拒绝不匹配；受权等价重绑定有明确记录 | 绑定校验与合法/非法等价映射 | S12/S14；O06/O08；C07 |
| A15.2 | 合法重复查阅证据、同键重试动作、同键改参数 | 证据可依法复用；动作不重复执行；改参数拒绝 | 证据消费记录、幂等表、实际副作用计数 | S10/S12；O05/O08；C06/C08 |
| A15.3 | 两个 Change 或项目均有 T-167，交换候选/完成证据 | taskKey 不同；合法各自完成可并存，交叉消费拒绝 | 完整命名空间、任务键、独立完成键及拒绝记录 | S14；O06/O08；C07 |
| A15.4 | 成功/unknown 后轮换 epoch/Worker 重试；另测尚未发送动作的合法交接与冒用原主体 | 已发生/未知动作不重发；未发送动作经接手授权可继续；发起主体/指纹不改写，当前主体真实认证，预算不重置 | 业务动作键、原始指纹、接手主体与新授权/协调资格、实际执行次数 | S10；O05/O10 |
| A15.5 | 删除项目/Change/目标资源后以同名或同内容重建，再提交旧授权、证据或待发送动作；另测同一对象改名 | 新实例不继承旧身份/Completion/许可；旧回执只归原历史；合法改名保持身份，新实例须重新批准且不重置原业务预算 | 受保护身份分配/退役记录、外部创建实例、解析前后身份、当前入口拒绝、合法映射及预算对照 | S10/S14；O05/O06/O10；C07 |
| A16.1 | 必需 gate 缺失、skipped/not_run/error 或插件不可用，且无满足批准复用规则的有效原始证据 | 不能得到该动作资格；完整通过不能依赖空集合 | 可信计划与结果精确集合差异、复用规则及不可满足依据、限定裁定 | S12；C08 |
| A16.2 | 同一计划槽位重复计数/同一来源结果冲突、替换低强度配置、虚报 artifactCount、挑选成功分片或必需引用已清理 | 拒绝不足覆盖及无法核验的必需证据；保留失败/重试/清理和历史完成事实 | 检查实例、配置/制品摘要、实际解析与保留状态、分片与重试记录 | S12；C06/C08/C09 |
| A16.3 | 将 submit 的允许 Decision 用于集成，或裁定后改变政策/任务/目标 | 跨阶段用途拒绝；当前前提重新校验并重裁定，不凭旧签名直接执行 | Decision 上下文、独立授权、可控交错和入口拒绝 | S12、[共享契约 §13.20.2](modules/edition-1.5.md#shared-contracts)；O08；C04/C07/C08 |
| A16.4 | 同 gate 的获批多环境/分片全部运行；另测漏槽位、重签同一运行或缓存伪充独立重复 | 合法矩阵与批准的多要求映射可通过；缺槽位、重复贡献或不满足独立性条件拒绝 | 计划/槽位/要求映射、聚合规则、实际 run 与来源结果、缓存复用依据及合法对照 | S12；C04/C06/C08/C09 |
| A16.5 | 必需槽位全部满足（含计划允许的有效原始证据复用），独立获批观察项 expected=true 但未执行/缺制品；另测必需项伪标 report_only/expected=false、共享采集器失效或动作明确要求整体 verify 成功 | 观察异常按批准范围处理；必需缺口、报告遗漏、共同信任故障及未满足的整体成功前提均阻断；旧 outcome/退出语义不改写，不宣称全检通过 | 事前计划/必需观察映射、原始报告及合法复用绑定、独立采集证据、限定 Decision、不阻断理由和必需失败对照 | S12；O08；C06/C08/C13 |
| A16.6 | 必需检查xfail、strict xfail、run=False、选择器漏收集而exit 0；非必需观察及正常负向断言 | 原生结果保留；无有效必需断言拒绝；观察按计划分层；真实拒绝由受信断言证明 | 批准槽位/节点映射、collected/selected/deselected、真实执行与原生结果、普通失败及通过对照 | S12；C04/C08 |
| A17.1 | 通过环境变量或工作目录放置假 adapter | 实际启动来源校验失败；无受治理运行资格 | launcher 配置、已批准摘要与拒绝记录 | S11；O04；C05 |
| A17.2 | 探针通过后更换挂载/镜像/网络策略，或仅伪报 observedChecks | 运行绑定失效或重验；不能继承过时环境证明 | 每次启动配置、变更检测、实测拒绝 | S11；C05/C14 |
| A17.3 | 主进程退出但子进程持有输出 fd、延迟写入或迁出运行域；仅改权限标志就采集；清理失败后请求复用 | 整域受控且资源聚合；先使全部相关写入者不可达，再冻结及采集；未证明终结不签完整成功、不复用环境 | 真实后代/句柄探针、运行域限制、终止与输出摘要、清理失败隔离及正常对照 | S11；O07/O10；C05/C06 |
| A17.4 | 通知检查后修改候选路径参数/共享状态或用有效notification ID冒充参数固定；合法受限调用 | 不能仅靠用户态检查后CONTINUE获得权限；实际内核/资源入口拒绝越界；有界代理和合法调用正常 | 所选适配器、可控交错、被检查与实际资源身份、独立拒绝点及合法调用对照；未用通知保留通用隔离证据 | S11；O04；C05 |
| A17.5 | 顶层只读下存在嵌套可写挂载、未批准传播或宿主写入者；候选另有获准scratch | 实际拓扑不满足保护时拒绝/隔离，不能只凭ro字段签发；不可变快照或有效递归保护及正常scratch通过 | 真实运行命名空间/挂载表、实际主体读写探针、输入身份与传播控制；合法路径对照 | S11；O07；C05/C09 |
| A18.1 | 回滚事件库、删审计或同时提供旧检查点 | 检测不连续/回退并停止；Worker 不可重建权威历史 | 独立检查点、受保护单调序列、恢复前后比对 | S13；O09/O10；C06 |
| A18.2 | 意图落库前、执行后、结果/完成落库前崩溃；恢复早于副作用的备份并轮换 epoch | 意图前不执行；已执行未知时核对恢复；旧备份/新 epoch 不重置动作身份、预算或去重墓碑 | 故障注入、journal/outbox、独立检查点、目标历史、预算与恢复记录 | S10/S13/S14；O05/O08/O10 |
| A18.3 | 候选运行期间主审计不可写且在线权威不可达；再故障独立记录通道，并尝试借应急恢复业务 | 正常写入拒绝；预批准本地停止仍可隔离候选；不放行补偿/重发/完成；缺口如实保留，局部停止不冒充全域撤销 | 真实故障注入、supervisor/入口状态、权限收敛与候选停止观察、记录缺口、恢复前置检查和非法应急对照 | S13；O10；C05/C06 |
| A18.4 | 必要预留/完成已返回后注入系统崩溃、同步失败或恢复旧 WAL；另测正确持久配置 | 在声明故障模型下成功确认可恢复；不能证明时停止副作用并核对；进程终止不冒充断电测试 | 有效连接PRAGMA/等效配置、持久卷故障注入、动作/预算/完成恢复和正向对照 | S13；O09/O10；C14 |
| A18.5 | NULL复合键、writer连接外键关闭、REPLACE覆盖历史、IGNORE误报成功、零行CAS、事务部分失败及并发完成 | 权威约束在实际入口生效；旧历史不替换；明确回滚或未知核对；同任务周期只完成一次 | 实际DDL/索引/连接设置、事务前后记录与行数、错误/恢复路径、合法幂等和状态转换 | S13/S14；O06/O08/O09；C07/C14 |
| A18.6 | 实际嵌入SQLite旧于宿主CLI、WAL-reset补丁缺失/未知、受信回补、加载库替换 | 受影响多连接WAL路径不开启；实际受支持且修复可证的工件可继续完整验收；未复现不替代补丁 | 进程内version/source ID、驱动/编译/制品及补丁来源、适用性和真实准入拒绝/合格对照 | S13；O09；C09/C14 |
| A18.7 | 活动WAL仅复制主DB、不同时间逐文件复制、ATTACH多库被当原子、合法在线备份/恢复 | 不完整或不支持跨库保证拒绝；成功一致备份可核验；恢复与独立检查点/外部结果核对，历史和额度不重置 | 活动库提交/WAL、备份完成身份、单库事务关系、恢复约束/历史、未决动作及合法恢复对照 | S13/S14；O09/O10；C14 |
| A18.8 | 在工件写入、文件/目录同步、命名发布及数据库引用提交间注入故障；恢复出孤立工件或有引用但无完整内容 | 未确认材料不可用于资格；同键核对后恢复合法登记；缺原件保留事故/未知状态，不重建新字节冒充；既有业务事实不被抹除 | 固定故障模型、存储实际确认、工件与引用前后状态及恢复记录；进程与系统故障证据分别标识 | S13/S18；O03/O07/O10；C06/C09/C14 |
| A19.1 | 路径穿越、symlink/hardlink 替换、恶意归档成员或物化路径碰撞 | 拒绝越界/共享写风险；不覆盖用户或控制面文件 | 目录句柄/等效机制测试、前后文件摘要 | S06/S11；O03/O07；C01/C09 |
| A19.2 | 重复 JSON key、危险 YAML 标签、超大嵌套、远程 $ref/重定向 | 有界解析；不执行代码、不隐式联网、不发生 SSRF | 解析资源限制、出站拒绝、恶意输入 fixtures | S06；O02/O04；C01/C03/C05 |
| A19.3 | 重复ID但 uniqueItems 为真、非法 format、default 补安全字段、readOnly 误当权限、未知 dialect | schema/语义/资源权限分别检验；拒绝未支持必需语义及未批准输入变形 | 验证器/选项、原文与解析值、独立 expected fixtures、合法旧合同对照 | S06；O02；C03 |
| A19.4 | 小压缩包大展开、嵌套超限、重复/冲突成员、过滤后跳过、截断尾部或半成品缓存；合法有界包 | 受限暂存、实际累计计量和完整校验后发布；失败/超限不留下可用证明或覆盖生效目录 | 传输/展开计数、类型/规范化清单、限额及拒绝点、暂存清理/隔离、合法完整导入 | S06/S11；O07；C03/C09 |
| A19.5 | gzip原始/解码摘要混用、跨版本Range拼接、Range返回200、304但缓存缺失、必需trailer未到；合法全量/批准续传 | 按合同字节域验证；不完整/错误重组不得发布；200重建完整暂存，304不补造数据；最终完整摘要匹配才消费 | 受控原始/解码字节、期望摘要来源、状态头/范围与缓存身份、最终对象及预算、正反获取轨迹 | S08/S11；O07；C03/C06/C09/C10 |
| A19.6 | 隔离HTTP链的TE+CL、冲突长度、非法Host/换行/分块/截断、代理转发差异 | 按批准原生策略拒绝/去歧义并终结失步连接；最终资源无不同正文或额外请求被执行；合法协议请求成功 | 原始字节fixture、前后端实际解析/请求数、绑定目标/正文及副作用、正常分块/复用对照 | S06/S15；O05；C10 |
| A19.7 | JSON字段大小写替换、转义重复key、尾随第二值、null/缺失/旧对象残留、无效Unicode及大整数/加法越界 | 按精确合同在信息丢失前拒绝；不以宽松struct映射或舍入结果执行；合法Unicode、开放字典和字段边界值一致通过 | 原始有界消息、parser版本/配置、producer/consumer值及动作映射；差分与合法历史样例 | S06/S08；O02/O04；C03/C06 |
| A19.8 | YAML重复key、隐式布尔/日期、非字符串key宿主碰撞、merge/循环alias、标签及额外文档；合法引用型历史配置 | 新安全配置按受限合同检查；未批准扩展及歧义拒绝，不执行构造器或丢失原值；历史mapper与明确字符串正例无损 | 原始节点/标签、版本/resolver/mapper、重复与类型判定、资源上限和合法兼容输出 | S06/S18；O02；C03 |
| A20.1 | 动作超预算、换幂等键、换目的地或并发预留 | 批准与额度不能绕过；不产生额外副作用 | 参数绑定、唯一业务动作约束、额度事务 | S10；O05 |
| A20.2 | 外部请求超时且无法确认是否执行 | 标记 unknown 并核对；不默认退款/重试/exactly-once | 外部资源状态、恢复记录、无重复执行证明 | S10/S13；O05/O10 |
| A20.3 | 已获准域名下改租户/对象；别名、路径解码、adapter 或重定向改变最终资源 | 对最终语义资源重新鉴权；不借网关凭据越权，不因初始 URL/域名获准而放行 | 原始/规范化请求绑定、真实资源身份、重定向/转换记录、拒绝和合法对照 | S10；O04/O05；C04/C05/资源入口 |
| A20.4 | 验证或 cleanup 身份只有运行检查许可，却尝试跨测试租户写入模拟业务目标；远端清理超时后再次请求 | 未获准业务动作拒绝；测试用途/非管理员标签不扩大权限；未知清理不盲目重试，合法有界测试与清理可用 | 测试计划、真实目标/账户权限、资源入口拒绝、前后数据/副作用计数、清理回执及未知结果 | S10/S11/S13；O05/O11；C05/C10/C11/C12 |
| A20.5 | 外层一次调用触发SDK/代理多次发送、退避后授权过期、幂等保留期外重放、202后远端失败；合法同键重试 | 所有发送受批准计划/授权和累计限额约束；不改键；受理不计完成，未知先核对；合法有界重试可用 | 实际发送计数/时间/键及参数、SDK配置、授权/预算、终态资源观察和正常对照 | S10；O05/O10；C10 |
| A20.6 | 无shell的argv中混入目标程序选项、配置/插件参数或响应文件；有特殊字符的合法操作数 | 固定操作合同拒绝未批准行为；定界只用于实际支持工具；合法数据保留，不开放任意extra-args；执行资源仍受限 | 程序/子命令/原始及有效参数绑定、真实parser结果、授权与资源前后值；合法API/定界对照 | S10；O04/O05；C09 |
| A20.7 | 所选HTTP/TLS链路接受早期数据或425重试，代理可能丢失Early-Data语义；对同一业务动作重复送达 | 参考受保护路径禁用/副作用前拒绝早期执行；合法重试非早期且同键/同参/当前授权；握手或GET不独立证明安全 | 实际客户端/终止点/代理策略与连接证据、标记传播、重试/副作用计数；关闭优化及普通成功对照 | S10/S15；O05；C10 |
| A21.1 | 验证后目标 B 发生变化或授权代次失效 | CAS/资源前提校验拒绝；生成新集成候选后再验证 | B 与目标代次、拒绝、重验记录 | S10/S14；O08/O09；C07 |
| A21.2 | merge/rebase/squash 得到 I，与源候选 C 不同 | 使用匹配 I 的验证；集成成功后完成失败可恢复 | C→I lineage、I 的证据、实际回执、补记而非重合并 | S14；O07/O08；C07 |
| A21.3 | If-Match被代理移除、弱/通配条件冒充预期版本、目标A→B→A及202回执冒充集成 | 实际条件点拒绝不满足前提的动作；ETag不能替代实例/代次；有终态和匹配证据后才集成完成 | 目标前后版本/代次、条件请求与原生响应、并发时序及合法原子更新 | S10/S14/S15；O08；C07/C10 |
| A22.1 | closed/cancelled/superseded Change 普通重开 | 拒绝；新关联 Change 承接；历史终态保留 | 状态迁移日志、lineage、非法迁移 fixtures | S14；O06；C07 |
| A22.2 | 实质改验收只增 revision，或合法非实质澄清/返工 | 实质变化新 Task；非实质重绑定；attempt/cycle 不混用 | 义务对比、审批、状态与证据映射 | S14；O06；C07 |
| A22.3 | 父关闭与新增任务/返工竞争；closing 计划允许的最后完成与关闭并发 | 合法既有结算可串行成功，父关闭读取最终条件；未获准动作/旧代次拒绝；未齐义务不关闭 | closing 计划与集合摘要、当前 cycle、可控交错的事务顺序、未决动作 | S14；O06/O08/O09；C07 |
| A22.4 | 管理员对已部署/被后续使用或影响未知的关闭请求行政撤销；真实无影响误关闭；终态后迟到回执 | 不满足窄例外则拒绝重开并使用后继 Change；合法误关闭追加撤销及新代次；历史核对不新增终态后 Completion | 外部影响与消费核对、独立批准、前后状态/代次、完整历史及非法重开对照 | S14；O06/O08/O10；C07 |
| A22.5 | 已完成任务证据到期但义务/候选未变；另测当前目标已不满足要求或试图恢复终态 Worker 权限 | 受权验证服务可追加必要新证据和现时裁定；原 Completion 唯一且不重开；目标缺失、未授权业务或取消义务恢复均拒绝 | 当前验证计划/授权/预算、原完成与新验证引用、完成条数/周期/父状态不变、当前目标检查及正反对照 | S12/S14；O06/O08；C04/C07/C08 |
| A23.1 | apply 最后一次 preimage 检查后由不遵守工具锁的进程改内容/目录项，或事务中读取半成品；另测合法版本树切换 | 实际修改边界阻止竞争，或拒绝覆盖并保留编辑；中间态不成为已验证候选；合法条件切换可用 | 检查—写入交错、真实写入权限/句柄、文件前后字节、版本代次/事务标记及正向对照 | S18；O03/O12 |
| A23.2 | 多文件 apply 掉电；rollback 最后一次 postimage 检查后再次发生用户编辑或目录项替换 | 在实际修改边界内核对恢复；冲突保持隔离且不覆盖用户内容；合法恢复可完成，审计不回滚 | journal、可控交错、用户内容保留、受保护修改边界及恢复/冲突对照 | S13/S18；O03/O10 |
| A23.3 | inspect/plan/诊断导出指向已有文档、Git/政策目录、链接别名或并发新建同名文件；另测合法隔离工件输出 | 不覆盖或新增影响业务的文件，不借服务权限兜底；冲突/输出失败不触发迁移；合法新工件可导出且不改变扫描事实 | 真实目录/对象及调用者权限、排他创建/条件发布轨迹、业务文件/Git/缓存前后状态、并发与正常输出对照 | S18；O02/O03/O04；C06 |
| A24.1 | 支持窗口内旧合法输入/输出与历史状态 | 按原义读写；不追授新零信任完成 | 旧新 reader/writer fixtures 与新资格拒绝 | S18；O12；C13 |
| A24.2 | 旧格式可读但其旧工具已被撤销 | 历史解析可用；受保护执行拒绝被撤销实现 | 格式兼容结果与独立当前授权判定 | S18；O12；C09/C13 |
| A25.1 | 向不支持的新/旧 consumer 写入新字段、状态或路径语法 | 显式协商/版本化输出或拒绝；不静默重解释 | 双向 producer/consumer 矩阵、错误语义 | S04–S08/S18；O12；C03/C13 |
| A25.2 | 流缺帧却结束、乱序/冲突重传、非法 Pointer 或摘要不一致 | 缺口未闭合不能完成；按已锁 transport 恢复或失败 | 独立 producer/consumer、最终水位/摘要、恢复 fixtures | S05/S08；C03 |
| A25.3 | 使用 /outputX、URI fragment、~01 或对象/数组的 01 路径混淆 | 按已选表示、解码 token 和实际容器定位；越权拒绝，合法对象 key 不误拒 | 独立实现正反 fixtures、授权路径与最终物化结果 | S05/S06；C03 |
| A25.4 | beta后缀被删、beta.2/beta.10普通字符串排序、加号metadata冒充预发布、Python规范化和未知未来beta | SemVer数值顺序正确；1.5.0-beta.1可映射工具原生1.5.0b1且不改DAS字段；未知支持组合拒绝 | 标准与包原值、原生解析/dispatcher、双向映射、reader/writer与实际采用目标 | S18/S19；O01/O12；C13 |
| A25.5 | 合法小帧累计越限、重传/重连重置预算、追加后水位不一致、选用SSE的未终结末事件 | 全程有界、重复不重复应用但计量消耗；越限原子保留旧一致状态；传输关闭不产生业务完成；合法恢复成功 | 接收与物化计数、预算归属、水位/摘要、结束证据及支持transport双端记录 | S05；C03；O10 |
| A26.1 | HTTP 作者源冲突、覆盖遗漏、operation 身份重用 | 对应 gate 失败；派生 inventory 不作为第二作者源 | 固定来源、历史 ID、覆盖与重建差异 | S15；O11；C10 |
| A26.2 | 候选动态枚举路由不完整或删除声明 | 保留 unknown/独立核对；不能按未观察到判不存在 | 受控枚举、批准覆盖基线、缺口裁定 | S02/S15；O02；C10 |
| A26.3 | OpenAPI security OR/AND 或继承被改写、合法匿名、空过滤描述、不同 dialect 和递归ref | 按原生语义解析；声明与实际授权/覆盖分别校验；合法匿名及有界递归不误拒 | 精确版本/基URI、归一化前后事实、真实入口探针和公开端点对照 | S15；O11；C03/C10 |
| A27.1 | 删除 workflow、换成旧构建截图、自动批准视觉基线 | 对应覆盖或基线检查失败 | 工作流/构建/环境身份及独立批准 | S16；O11；C11 |
| A27.2 | 候选页面伪报成功、焦点/恢复错误、污染 UI runner，或借 trace/HAR/storageState 导出测试会话 | 域外驱动断言有效；行为缺陷失败；认证材料不进入未授权报告，候选不能改结果 | 可信浏览器驱动、正反行为、实际账户范围、会话导出拒绝及合法脱敏报告 | S11/S13/S16；C05/C06/C11 |
| A27.3 | 内部开发指令混入用户正文、必要提示遗漏；另测用户技术文本和合法多区工作台 | 来源/受众/任务语义决定；误显与提示缺失失败，合法内容与复杂布局通过 | 获批页面约定、真实文案/状态、浏览器证据和独立语义审阅 | S16；O11；C11 |
| A27.4 | 长文尾部不可达、分页/返回/未保存编辑异常；另测稳定抽屉或分屏完整阅读 | 完整任务与约定恢复可验证；不按载体名称一律拒绝或强制单页 | 批准阅读范围、全文/页面状态、history/返回与dirty行为证据 | S16；O11；C11 |
| A27.5 | A→B→A旧响应、旧error/progress/finally、保存后继续编辑和取消后晚到 | 按操作/对象/提交版本决定更新，保留新编辑；远端结果未知不假定取消成功 | 可控调度、请求代次、submitted/current版本、UI及真实回执轨迹 | S10/S16；O11；C11 |
| A27.6 | 历史0/1/多项、缺页/损坏/请求失败；使用有效明确对象ID | 缺完整性时不推断唯一；明确ID或完整集合的合法解析继续可用 | host API/数据fixture、完整性依据、实际选中身份与合法对照 | S16；O11；C11 |
| A27.7 | token 名称存在但实际样式被覆盖；另测批准例外/代表组件真实消费 | 实际消费与获批例外匹配才通过；双扰动可选，不以工具方法缺失自动拒绝等效证据 | token/组件版本、运行样式或等效产物、扰动/依赖证据与批准例外 | S16；O11；C11 |
| A27.8 | 扫描全绿但键盘/模态错误、候选自动建基线；另测非模态抽屉及首次独立批准 | 适用断言逐项验收；自动能力Partial；首次基线独立批准，样本不被扩称全站WCAG | 扫描/浏览器/人工分工、实际焦点/背景行为、批准基线与声明范围 | S16；O11；C11 |
| A27.9 | 登录/错误/空页上隐藏断言通过、locator无匹配、坏样例破坏启动；另测合法健康/缺陷/恢复链 | 先核验实际业务就绪；测试设置失败不记作检出；指定缺陷可达且被同一检查识别 | origin/route/对象状态、采集记录、健康与坏样例及恢复的实际断言 | S16；O11；C11 |
| A28.1 | 开发者取私有输入，或候选取标签/秘密评分材料 | 开发与候选权限分别限制；协议允许的推理输入可达 | 真实身份访问拒绝、允许输入对照、评分域配置 | S17；O11；C12 |
| A28.2 | 私有内容经日志、输出、缓存、网络、报告或可枚举低熵摘要回流开发 | 未授权通道拒绝；受限摘要留在获准域，只释放合同批准的有界反馈 | 数据域权限、引用与导出策略、出口/缓存/摘要反例、反馈记录 | S11/S13/S17；C05/C06/C09/C12 |
| A28.3 | 测试集参与预处理拟合、失败样本从分母删除、保留集反馈参与选模后仍称独立未见 | 泄漏/分母不符或声明资格失败；批准的真实自适应结果可按正确标签保留 | 划分/拟合来源、协议/分母、失败历史、候选选择及反馈记录 | S17；O11；C12 |
| A29.1 | 换账号、会话、Runner 或候选别名重置预算，或新增未知控制关系账号 | 已登记关联主体共享预算；未知新身份先核准，不自动发新额度 | 受保护主体映射、未知身份拒绝、持久预算与跨会话测试 | S17；C12/评测部署 |
| A29.2 | 并发取私有输入、结果未知重试，或借错误/时间/gate 反馈取数 | 先预留额度；反馈有界；不退款掩盖可能已泄露信息 | 预算交错、反馈合同、错误/时间/大小处理证据 | S17；C12/评测部署 |
| A30.1 | 授权事故、信任根/密钥撤销、停止及恢复；有权核对者接收迟到执行事实 | 全部受治理部署必验；旧权限不支持新动作；可信历史可核对，签发失陷按独立依据处置，恢复重判资格 | 撤销/kill switch、当前核对身份、可信历史依据、旧动作权限拒绝与正常恢复 | S09/S12/S13；O10；C06/C14 |
| A30.2 | 私有评测污染、反馈用于调参或材料泄漏 | 停止后续新未见声明；追加处置，不擦除原时点事实 | 污染与反馈来源、资格撤销、受权恢复/新协议 | S17；O11；C12 |
| A31.1 | 重复生成模块/完整视图，离线核验发布包 | 内容确定；无漏项、远程依赖或摘要自引用 | 两次生成结果、独立正文清单、包内闭包 | S01/S03/S08/S19；C01/C14 |
| A31.2 | 正式包与预发布包字节不同，尝试沿用预发布顶层证明 | 重新核验正式包绑定；只按政策复用未变子证据 | 正式包摘要、锁、安装验证、签发与复用范围 | S19；O13；C14 |
| A31.3 | 官方配套把整个冻结领域能力标 N/A/unsupported，或无该业务的产品声明 N/A | 官方冻结功能仍须有受控支持测试；真实业务不适用有证据时允许 | F/S/O/C/A 分层映射、受控领域样本、独立产品事实 | S19；O13；C14 |
| A31.4 | 不同候选的合法签名文件混装、旧包回放、未经批准候选渠道或直接重命名预发布包 | 拒绝混装/回退/误渠道；正式版新闭包核验，合法未变子工件依批准规则复用 | 包代次/摘要、渠道授权、信任状态、原始与最终签发/闭包 | S08/S18/S19；O01/O10；C01/C13/C14 |
| A31.5 | Python优化模式移除assert、提前打印PASS后子步骤失败、管道/报告写入失败 | 安全检查仍显式拒绝或启动前拒绝未支持模式；无完整终结证据不通过 | 正常/优化模式对照、各步骤退出码、最终报告/工件、无发布副作用 | S19；O04/O13；C03/C08/C14 |
| A31.6 | 同beta号换字节、必要beta.1→beta.2修复、已用编号复用、未发布提交试用、旧writer/状态迁移与正式提升 | 同坐标拒绝覆盖；必要新beta独立批准；精确修订可受控试用；不支持旧writer关闭；升级/回退保留账本；满足条件可从beta.1直接正式 | 两份精确包及固定旧包、兼容/迁移/回退前后状态、修复重验/试用覆盖、发布回读及正式包新证据 | S18/S19/发布生命周期；O01/O12/O13；C13/C14 |
| A31.7 | 自动源码包内容相同而压缩字节变化、缺资产就公开、发布返回未知、改prerelease标记、回写包内实际时间 | 固定分发资产与源码视图区分；未齐不确认完整发布，未知按同键核对；正式身份独立；包外回执不改变包摘要 | 获批资产清单、暂存/发布/回读状态、包与源码摘要、真实时间依据、受控发布成功/失败及不可变性 | S18/S19/发布生命周期；O01/O13；C01/C13/C14 |
| A32.1 | 移除隔离、独立身份、保护规则或可信签发能力 | 明确 unsupported/失败；禁止降级运行 | 能力探测、真实拒绝、受保护目标未改变 | S09/S11；O13；C05/C14 |
| A32.2 | 探针根本未执行、故障导致一切请求均失败，或测试/签发同受候选控制 | 不能计作控制通过；合法正向与恶意负向必须同时成立 | 探针执行轨迹、可达对照、角色权限矩阵 | S11/S19；O13；C05/C14 |
| A32.3 | 采用已通过后改变关键权限/目标保护/配置，或证据过期仍发起动作 | 历史结论保留；当前受影响能力停止，可信核准与必要重验后恢复 | 采用绑定、漂移/有效期检测、实际停止与恢复对照 | S09/S12/S19；O13；C05/C14 |
| A32.4 | beta拟开启动作缺控制、试用仅静置或CI全绿、修复后沿用旧观察、未来beta自动激活 | 不可靠能力关闭；发行/试用按阶段实际准入；正式退出需获批覆盖和有效重验；未来组合无批准不激活 | 本次beta/正式计划、开关/真实拒绝、负载与故障/成功覆盖、影响分析、当前支持及独立退出批准 | S19/发布生命周期；O13；C13/C14 |

#### 5. 结果归档与资格消费

用例结果、原始 verify report、受治理资格裁定分别保存。原报告顶层 `overallOutcome` 仅为 `pass/fail/error`，逐 gate 的 `outcome` 为 `pass/fail/error/skipped/not_run`；Decision 的限定结论独立承载，不给旧报告添加新枚举。[REPORT](verify_report.schema.json)。子用例是计划分母，不以本索引中的文字生成“通过”记录。原始失败、重试、豁免、污染和撤销事实保留，最新资格由受保护入口按当前状态判断。

计划槽位、真实运行及证据签发身份分别核对；重签或复用不增加独立执行次数。历史 Completion 与当前资格分别消费，证据到期不能经复制完成记录恢复通过；按 S14 重新验证也不追授历史缺失的事实。

报告中的 expected、执行 outcome 与受保护计划的动作必需性分别校验。观察异常显式保留；仅在预先批准且不影响必需证据/可信运行时不阻断限定动作。必需项缺结果、原报告被删改、共享采集失效及零信任控制缺口仍阻断；不得把未执行观察项写成通过。对象同名重建按 S10/S14 的身份分配与创建实例规则处理，旧记录不转移到新对象。

签发链必须证明原始结果来自声明的执行或观察主体。测试源码、脚本退出码、完整 JSON 和签名数学有效都不能单独证明要求已满足。发布证据须指向实际正式制品；生产采用须指向实际项目部署，不能继承参考部署的环境结论。


原始证据与展示副本分别绑定，展示转义/脱敏不能覆盖原始签名输入；下载与解压路径按批准字节域完成最后校验。发布层区分精确源码、实际固定分发包、可编辑渠道展示与包外真实回执，平台标记不能提升正式资格。外部实现机制只在对应adapter被选择时测试；其未被选用不豁免通用冻结控制。

##### 5.1 发布与采用的证据分母

| 判定层 | 必须覆盖 | 条件性与结论边界 |
|---|---|---|
| 规范内容 | 全部 F01–F11、规范性条款/合同/映射及发布闭包 | 领域适用规则也属于必交内容，不能因标准仓无业务而省略 |
| 工具实现 | 各 S/O/C 责任、兼容矩阵、负向用例及实际安装输出 | 责任可分仓或分 adapter；冻结能力不可整体标为 unsupported 来完成发布 |
| 参考部署 | 通用 Z01–Z12、适用 A 场景及最小受控领域支持样本 | 只证明已实测的环境组合；样本不构成业务效果或私有未见性认证 |
| 具体项目采用 | 真实身份/配置/目标、经核准事实、适用门禁及其证据有效期 | HTTP/UI/密封业务可据事实 N/A；通用 Agent 门槛仍强制，漂移后重判 |
| 单次受保护动作 | 当前身份/独立授权、动作专属 Decision、对象/目标前提、额度、代次和证据 | 一次采用批准、历史 Completion 或有效签名均不能单独授权本次动作 |

判定依据为 [S19 发布与采用门槛](modules/edition-1.5.md#s19)。测试分母由受保护计划确定；本文件中的 `not_run` 不能经格式转换变成任何判定层的通过证据。

<a id="sources"></a>

<a id="component-responsibilities"></a>
#### 配套责任标签定义

O/C 是验收表的配套责任索引，不增加叶级义务或用例，也不表示实现已经通过。规范义务仍由 S 条款及各场景确定；公开工具入口的实际支持范围以其版本说明为准。

| ID | 配套职责 | 公开入口 |
|---|---|---|
| O01 | 识别标准目标与工具能力，安全创建项目 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O02 | 只读盘点、事实提案与模块上下文 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O03 | 事务化 plan / apply / rollback | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O04 | 无特权客户端与受治理执行器分离 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O05 | 动作授权、批准与副作用引用 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O06 | Task 身份、修订、完成周期与旧状态映射 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O07 | 候选快照、提交与验证绑定 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O08 | 集成与完成入口，消除编号和 force 旁路 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O09 | 最小协调、租约代次与并发安全 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O10 | 追加式审计、撤销与恢复 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O11 | HTTP / UI / 评测与安全模板 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O12 | 兼容迁移与错误契约 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| O13 | 配套自检、参考部署与交付证明 | [dasops 源码与支持说明](https://github.com/AzzCraft/dasops#readme) |
| C01 | 规范包、模块与索引闭包校验 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C02 | 共享、确定性的适用性 Resolver | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C03 | 精确契约、路径语义及兼容适配 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C04 | 受治理验证上下文与独立验收基线 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C05 | 真实隔离、受控适配器与禁止静默降级 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C06 | 可信结果采集与薄证据 Envelope | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C07 | 任务—候选—验证—集成关系校验 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C08 | 检查分母、结果语义与工件完整性 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C09 | 工具、插件、缓存与运行供应链 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C10 | HTTP 事实、覆盖与确定性 Inventory | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C11 | UI 工作流、浏览器与无障碍证据 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C12 | 评测资格与密封运行边界 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C13 | 兼容模式、默认入口与防降级 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
| C14 | 自检、配套发布与参考部署证据 | [cadence-oss 源码与支持说明](https://github.com/AzzCraft/cadence-oss#readme) |
