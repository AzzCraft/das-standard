# The Docs as Software (DAS) Standard
> **The Unified Engineering Methodology for AI-Enabled Products**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Version: v1.4.6](https://img.shields.io/badge/Version-v1.4.6-blue.svg)](CHANGELOG.md)

**Name:** Docs as Software (DAS) Standard (中文：**文码合一标准**)
**Maintained by:** AzzCraft Inc. 
**Copyright:** © 2026 AzzCraft Inc. (重庆艾之舟科技有限公司)
**Last updated:** 2026-04-06

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
- **MUST:** The declaration MUST be explicit in merged documentation. Missing profile declarations are a **verify failure**, not an implicit pass.
- **MUST NOT:** Repos and suites MUST NOT rely on “default if missing” semantics once a document has entered version control. Scaffolding MAY materialize an initial value during generation, but the generated document MUST write the explicit value before first merge.
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
- **MUST:** The declaration MUST be explicit in merged documentation. Missing interaction profile declarations are a **verify failure**, not an implicit pass.
- **MUST NOT:** Repos and suites MUST NOT rely on “default if missing” semantics for interaction profiles once a document has entered version control.
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
  "schemaVersion": "1.1.0",
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
  "schemaVersion": "1.1.0",
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

- **MUST:** Suites and dashboards SHOULD read verify-registry metadata rather than inferring gate semantics from CI job names.
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
