# The Docs as Software (DAS) Standard
> **The Unified Engineering Methodology for AI-Enabled Products**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Version: v1.0.0](https://img.shields.io/badge/Version-v1.0.0-blue.svg)](CHANGELOG.md)

**Name:** Docs as Software (DAS) Standard (中文：**文码合一标准**)
**Maintained by:** AzzCraft Inc. 
**Copyright:** © 2026 AzzCraft Inc. (重庆艾之舟科技有限公司)
**Last updated:** 2026-01-20

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
1. Repo-local docs MAY add stricter rules, but MUST NOT relax any **MUST/MUST NOT** requirements in this standard.


### 2.2 Core definitions

- **Repo boundary**: a source-control boundary (separate repo or package with an independent release lifecycle).
- **Runtime boundary**: a deployed process/service boundary (introduces network hops and distributed failure modes).
- **Contract surface**: any interface that is externally observed and/or persisted and read later. Contract surfaces are **Compatibility Mode by default**.
- **Compatibility Mode**: producer and consumer do **not** ship atomically; mixed versions are observable. Requires explicit compatibility windows and expand/contract evolution.
- **Refactor Mode**: a boundary behaves “atomically” from the perspective of the environment observing it (either within a single deployable artifact, or via a strictly enforced atomic cutover where no requests observe mixed versions). No persisted/external observation crosses the boundary.
  - **Clarification:** If you cannot *prove and enforce* “no mixed versions,” treat the boundary as **Compatibility Mode**.

- **Contract hub**: the canonical home for schemas, fixtures, identifiers, and executable checks shared across repos.
- **SDMM / Single-Deploy Modular Engineering**: build-time modularization inside a repo while shipping as one deployable artifact per app/service/library.

### 2.3 Conformance profiles and cost controls (scalable adoption)

This standard is intended to work for both small, fast-moving teams and large, multi-team organizations. To avoid accidental over-engineering (or accidental under-governance), every project MUST declare a **conformance profile** in the Master Doc (§9.1):

- **L0 - Prototype**: exploration or pre-product; prioritize speed while still protecting users and data.
- **L1 - Product (default)**: a shipped product with regular iteration; balance speed with reliability.
- **L2 - Platform/Enterprise**: multi-team, high-trust, or regulated; maximize stability, compatibility, and auditability.

Rules:

- **MUST:** Declare exactly one profile (`L0|L1|L2`) in the Master Doc.
- **MUST:** The default is **L1** if no profile is declared.
- **MUST:** Regardless of profile, externally observed or persisted surfaces (public APIs, stored artifacts, identifiers) MUST use **Compatibility Mode** and MUST be fixture-backed.
- **SHOULD:** Teams SHOULD evolve profiles over time (typical path: `L0 → L1 → L2`).
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

### 2.4 Interaction profiles (HFVI extension)

Conformance profiles (L0/L1/L2) control engineering cost and gate strictness. Some products also have a distinct risk: high-fidelity, spatial, continuous interaction surfaces (canvas/WebGL/game-like UI). For these products, textual UI specs tend to be under-specified, and naive AI generation frequently drifts (hit-testing, z-order, easing, coordinate transforms).

To keep HFVI work implementable and testable, each project MUST additionally declare an interaction profile in its Master Doc (in addition to its conformance profile).

Interaction profiles:

- `standard_ui`: form/workflow-centric UI where Appendix D is typically sufficient.
- `hfvi_canvas_webgl_game`: high-fidelity visual interaction (canvas/WebGL/game-like interaction surfaces).

Rules:

- MUST: Declare exactly one interaction profile (`standard_ui|hfvi_canvas_webgl_game`) in the Master Doc.
- MUST: The default is `standard_ui` if no interaction profile is declared.
- MUST: If `hfvi_canvas_webgl_game` is declared, the project MUST adopt the HFVI requirements in §6.8 and Appendix K.
- SHOULD: HFVI projects SHOULD treat interaction surfaces as contract surfaces for the purposes of fixtures, replayability, and verification gates.
If you choose L0, you MUST document what you are not doing yet, who owns the debt, and when it will be revisited.

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

1. `contracts` - canonical contract hub (schemas, fixtures, identifiers, codegen config)
1. `backend` - system-of-record + orchestrator (preferred owner for long-running jobs)
1. `algo` - model/compute service or algorithm library
1. `frontend` - UI client (if applicable)
1. `integration` - docker-compose/dev env + end-to-end smoke tests + compatibility runners (high leverage)
1. `data-evals` - offline datasets and benchmark reports (no secrets / no raw PII; optionally a separate artifact store)

**MUST:** Treat all cross-repo boundaries as **Compatibility Mode** unless you can prove and enforce atomic cutover.

### 3.4 What each repo owns (normative)

#### Repo: `contracts` (Contract Hub)

Owns:

- canonical schemas (JSON Schema / Protobuf / OpenAPI fragments),
- fixtures (known-good and known-bad),
- stable identifier sets (route IDs, job types, stage IDs, error codes),
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

1. **Schema**: machine-validated structure (JSON Schema / Protobuf / OpenAPI components).
1. **Semantics**: field meaning, invariants, defaults, error conditions, redaction rules.
1. **Fixtures**: known-good and known-bad examples, including edge cases.
1. **Executable checks**: CI that validates schemas and fixtures, plus compatibility runners for versioned surfaces.

**SHOULD:** Contracts that are used across languages SHOULD have:

- generated types/clients (or at least strongly-typed adapters),
- a single canonical identifier set (error codes, stage IDs, job types).

#### Minimal contract hub layout (recommended)

```
contracts/
  schemas/
    run_manifest.schema.json
    pipeline_result.schema.json
    job_envelope.schema.json
  fixtures/
    run_manifest/
      valid/
      invalid/
    pipeline_result/
      valid/
      invalid/
  ids/
    error_codes.json
    stage_ids.json
    job_types.json
  codegen/
    openapi.yaml (or components/)
    generators/
  scripts/
    verify
    compatibility_runner
  CHANGELOG.md
  README.md
```

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
- `contracts/`: shared contract types (OpenAPI/JSON Schema types, route IDs, event payloads).

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

## 9. Project documentation requirements (Master Doc + UI Spec)

### 9.1 Project Master Doc (required)

Every project MUST maintain a canonical Master Doc that is versioned with code and reviewed like code (Docs as Software). The Master Doc MUST:

- declare the project’s **conformance profile** (`L0|L1|L2`, §2.3),
- define product scope and constraints,
- define system topology (monorepo vs multi-repo) and the contract hub location,
- enumerate contract surfaces and owners (APIs, events, persisted artifacts),
- include a **Contract Inventory Index** (schema IDs + owners + compatibility windows),
- include a **Traceability Index** that maps:
  - requirements → contracts → tests/gates,
  - UI workflows → routes/jobs → run/pipeline artifacts,
- define verification gates and exact `verify` commands (per repo and system-level),
- include an execution plan (tasks with acceptance criteria and test evidence).

Doc update policy (to control cost and avoid “checkbox docs”):

- **MUST:** If a change modifies requirements, workflows, contract surfaces, budgets, determinism tiering, security posture, or verification gates, the same PR MUST update the Master Doc (or include a documented waiver with owner + expiry).
- **MAY:** Pure refactors that do not change behavior/contracts/workflows MAY omit Master Doc edits.
- **SHOULD:** For L0 projects, the Master Doc SHOULD remain short and focus on critical flows and risks; expand as the product stabilizes.

### 9.2 UI Spec Appendix (required for UI products)

If the project has a user-facing UI (web/mobile/admin), it MUST maintain a UI Spec Appendix (Appendix D) that defines:

- stable Screen IDs and Route IDs,
- explicit `Loading/Empty/Ready/Error/Permission` states, plus AI-specific `Thinking/Streaming/Repair` states when applicable (see §6.7),
- workflow-to-screen-to-contract traceability,
- stable test selectors for critical interactions,
- AI interaction mode per screen (static/streaming/async_job) and the referenced contracts when applicable (citations §4.4.9; streaming §4.4.10),
- design system contract references (tokens/components) for shared UI surfaces (see §4.5).

Design review (recommended):

- Use **Appendix H - UI Design Review Checklist** as the cross-functional UI review checklist (Design + PM + Eng).
- Items marked **automatable** SHOULD be enforced in the frontend `verify` gate; other items must be reviewed by a human (LLM assistance is optional, not authoritative).

### 9.3 Traceability automation (strongly recommended)

Manual traceability tables rot quickly unless the maintenance cost is near-zero. Projects SHOULD automate where feasible:

- Generate Traceability Index tables from code metadata (e.g., test names containing `FR-###`, Storybook stories containing `UI-###`, contract schemas containing `SCHEMA-###`).
- Provide a `scripts/traceability` (or equivalent) that fails CI when referenced IDs are missing or orphaned.

If a project does not automate traceability:

- **MUST:** Keep the Traceability Index minimal and focused on critical workflows and externally observed/persisted surfaces.
- **MUST:** Assign an owner for the Traceability Index and review it at least once per release milestone.

## 10. Verification and CI gates (minimum)

### 10.1 One canonical `verify` per repo

Each repo MUST provide a single entrypoint:

- `./scripts/verify` (or equivalent) is the canonical local and CI gate.
- It MUST be deterministic and fast enough for frequent use (review-loop fast).
- It MUST fail fast on boundary violations before running expensive tests.
- It MAY accept modes/flags (e.g., `--full`) as long as the default behavior is well-defined and documented in the Master Doc.

### 10.2 Minimum per-repo gates

- `contracts`: schema validation + fixture validation + compatibility checks for changed contracts.
- `algo`: boundary checks + unit tests + deterministic CI eval suite + replay (offline) where applicable.
- `backend`: unit + integration + contract tests + idempotency/retry tests for job flows.
- `frontend`: boundary checks + unit + minimal E2E smoke for critical flows.
- `integration`: end-to-end smoke + compatibility runner (old/new fixtures) + system verify.

### 10.3 Gate tiers and scheduling (to control cost)

- **PR gate (default):** run `verify` in its fast mode. This gate SHOULD provide feedback quickly and avoid flakiness.
- **Full gate (recommended):** run `verify --full` (or equivalent) nightly and/or before releases. This is where slow visual/E2E suites can live.
- **L0 projects:** MAY move some heavy gates to nightly/pre-release while the product is exploratory, but MUST document the tradeoff in the Master Doc and MUST keep at least a minimal smoke path for critical flows.

### 10.4 Flakiness policy

- **MUST:** Tests that gate merges MUST be stable. Flaky tests MUST be quarantined with an owner and a plan (do not “retry forever”).
- **SHOULD:** Prefer deterministic substitutes (record/replay, contract fixtures, stubs) over live external dependencies in CI.

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

## Appendix C - Project Master Doc Template

### Master Doc (PRD + Architecture + Execution Plan) - Template

> **Purpose**: Single source of truth for **product definition**, **system/code architecture**, and an **execution-ready plan** that humans and AI can implement **without ambiguity**.


> **Non-goal**: This document does **not** contain code-level implementation details (no concrete function bodies, SQL queries, UI component internals, or algorithm pseudocode beyond stage contracts). It **must** be sufficient for implementation planning, task decomposition, and verification.


> **Audience**: Product Managers, Engineering Architect(s), Tech Leads, AI coding agents, QA/Release, Security/Privacy/Compliance reviewers.

#### Placeholder and formatting rules

This template uses explicit placeholder syntax to avoid Markdown/HTML rendering issues and to make “unfilled” content machine-detectable.

- `{{REQUIRED_PLACEHOLDER}}` - **must** be filled before the doc can be marked `active`.
- `[[OPTIONAL_PLACEHOLDER]]` - optional; fill if applicable.
- `TBD:` - decision not made yet. If it blocks implementation, record it in **§10.2 Open Questions**.
- IDs like `FR-001`, `API-001` are **stable identifiers**. Once released, do not reuse IDs for different meanings.

Placeholder replacement rules apply **only** to template prose and tables. Content inside fenced code blocks is literal example text and MUST NOT be treated as placeholders.

In particular, double-bracket constructs inside code blocks (e.g., `[[importlinter:contract:layers]]` in an `import-linter` config) are tool syntax, not document placeholders.

**Do not** use angle-bracket placeholders like `<...>` in this doc; many Markdown renderers treat them as HTML.

#### Authority and precedence

**Authority scope**: This Master Doc is authoritative for **project-specific** decisions (requirements, workflows, contracts, architecture choices, rollout plan) within this repo/branch.

**Precedence order (highest → lowest)**

1. **Applicable law/regulation** + **organizational security/compliance policies**
1. **Project-wide / organization-wide engineering standards** (referenced in §0.5)
1. **This Master Doc** (branch source of truth)
1. **Input documents** (PRDs, prototype notes, meeting notes, older architecture docs)
1. **Team conventions**

If a conflict is found:

1. Record it in **§10.2 Open Questions** (or as an ADR if already decided).
1. Resolve it via the **Decision Log (ADR)** with the correct decision owner(s).
1. Update this Master Doc, bump its version, and update branch copies per **Annex C**.

#### Table of Contents

1. Document Control (#0-document-control)
1. Product Definition (#1-product-definition-pm-owned)
1. Domain Model (#2-domain-model-architect--pm)
1. System Overview (#3-system-overview-architect-owned-pm-must-understand)
1. Repo and Runtime Topology (#4-repo--runtime-topology-architect-owned)
1. Contracts (#5-contracts-schematized-testable-versioned)
1. Data, Privacy, and Compliance (#6-data-privacy-and-compliance-architect--pm)
1. AI and Algorithm Design (#7-ai--algorithm-design-architect-owned-pm-reviewed)
1. Observability, Operations, and Cost (#8-observability-operations-and-cost)
1. Release Plan (#9-release-plan-pm--architect--qa)
1. Risks, Open Questions, and Assumptions (#10-risks-open-questions-and-assumptions)
1. AI Execution Plan (#11-ai-execution-plan-no-code-unambiguous)

A. Annex A - AI Guide: Converting a PRD into this Master Doc (#annex-a--ai-guide-converting-a-prd-into-this-master-doc) B. Annex B - Template Snippets (#annex-b--template-snippets-copypaste) C. Annex C - Branch Copies and Sync Policy (#annex-c--branch-copies-and-sync-policy)

D. Annex D - UI Spec Appendix (reference) (#annex-d--ui-spec-appendix-reference)

#### 0. Document Control

##### 0.1 Metadata (required)

- **Project / Product name**: `{{PROJECT_NAME}}`
- **Codename** (optional): `[[CODENAME]]`
- **Project slug** (stable identifier; lowercase kebab-case recommended): `{{PROJECT_SLUG}}` (recommended: `my-product`)
- **Canonical doc path** (MUST be stable across branches): `{{DOC_PATH}}` (recommended: `docs/master_doc.md`)
- **Doc ID** (stable identifier): `{{DOC_ID}}` (recommended: `MASTER-{{PROJECT_SLUG}}`)
- **Repo / Branch**: `{{REPO}}@{{BRANCH}}`
- **Doc revision commit SHA** (recommended): `{{DOC_COMMIT_SHA}}`
- **Code baseline commit SHA** (recommended): `[[CODE_BASELINE_SHA]]` (the code state this doc currently describes)
- **Status**: `{{STATUS}}` (`draft | active | frozen | deprecated`)
- **Version**: `{{VERSION}}` (SemVer recommended)
- **Conformance profile**: `{{CONFORMANCE_PROFILE}}` (`L0 | L1 | L2`; default `L1`)
- **Interaction profile**: `[[INTERACTION_PROFILE]]` (`standard_ui | hfvi_canvas_webgl_game`; default `standard_ui`)

- **Last updated (date)**: `{{LAST_UPDATED_YYYY_MM_DD}}`
- **Owners**
  - Product owner: `{{OWNER_PM}}`
  - Engineering architect: `{{OWNER_ARCH}}`
  - AI execution owner (human): `{{OWNER_AI_EXEC}}`
  - QA/Release owner: `{{OWNER_QA_RELEASE}}`
  - Security/Privacy owner (if applicable): `[[OWNER_SECURITY_PRIVACY]]`

##### 0.2 Doc readiness gate (required)

A branch copy of this Master Doc **MUST NOT** be marked `active` unless:

- All `{{REQUIRED_PLACEHOLDER}}` fields are filled.
- If `[[INTERACTION_PROFILE]] = hfvi_canvas_webgl_game`, Appendix K (VIS) exists and is populated for each HFVI surface.
- All **Blocker? = Y** items in **§10.2 Open Questions** are resolved or explicitly deferred via ADR.
- §5 Contracts contains a complete **Contract Inventory Index** for all cross-boundary flows.
- §11 AI Execution Plan contains:
  - exact `verify` commands,
  - initial WBS (`T-###` tasks) with explicit scopes,
  - acceptance checklist.

##### 0.3 Normative language

The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY** indicate requirement level (RFC 2119 / RFC 8174 style normative language).

##### 0.4 How to use this doc (roles and ownership)

- **PMs** own Sections **1**, **9**, **10**; co-own Sections **2**, **6**, **8** (requirements must be testable/measurable).
- **Architects/Tech Leads** own Sections **3-8**, **11**; ensure boundaries/contracts are complete and enforceable.
- **AI agents** execute **§11**. If required information is missing, record it in **§10.2 Open Questions** and do not guess.
- **Everyone**: a code change that modifies requirements, behavior, contract surfaces, data handling, security posture, or user flows without updating this Master Doc (or explicitly marking “no doc change required”) is incomplete.

##### 0.5 Source inputs and referenced standards (append-only)

> This Master Doc is the compiled truth. The items below are inputs and references.

> Do not delete entries; supersede via changelog/ADR.

**Input PRDs / requirements**

- `[[PRD_1_PATH_OR_URL]]`
- `[[PRD_2_PATH_OR_URL]]`

**UX prototypes / design sources**

- `[[FIGMA_OR_FEISHU_LINK]]`
- `[[DESIGN_SPEC_PATH]]`
- `[[UI_SPEC_APPENDIX_PATH_OR_URL]]` (recommended: `docs/ui_spec_appendix.md`)

**Architecture references**

- `[[ARCHITECTURE_DOC_PATH_OR_URL]]`
- `[[SYSTEM_DIAGRAMS_PATH_OR_URL]]`

**Engineering standards (higher precedence than this doc)**

- Docs as Software (DAS) Standard `{{ENGINEERING_STANDARD_VERSION}}` : `{{ENGINEERING_STANDARD_PATH_OR_URL}}`
- `[[SECURITY_STANDARD_PATH]]`

**ADR directory**

- `{{ADR_DIR_PATH}}` (recommended: `docs/adr/`)

**Contract hub / schemas / fixtures**

- `{{CONTRACT_HUB_PATH}}`

**Integration harness**

- `{{INTEGRATION_HARNESS_PATH}}`

**Release notes / changelog**

- `{{CHANGELOG_PATH}}` (recommended: `docs/changelog.md`)

##### 0.6 Versioning and change control (required)

- **Versioning**: SemVer for this doc.
  - **Patch**: clarifications, typo fixes, formatting, non-semantic wording changes.
  - **Minor**: additive requirements/features/contracts that are backward compatible.
  - **Major**: breaking requirements/contracts, compatibility window changes, or architecture boundary changes.

- **Doc change rule**: any change that affects user-visible behavior, contracts, data handling, or rollout strategy MUST:
  - be recorded in **§0.7 Change Log**,
  - reference PR/ADR,
  - update relevant sections (not only the changelog).

##### 0.7 Change log (append-only)

| Date | Version | Author | Summary | Links (PR/ADR) |
| --- | --- | --- | --- | --- |

##### 0.8 Decision log (ADR index, append-only)

> Record any decision that affects behavior, data, contracts, architecture, or policy.

| ADR ID | Date | Decision | Owner | Status | Rationale | Consequences |
| --- | --- | --- | --- | --- | --- | --- |

##### 0.9 Branch progress tracking (required; branch-aware)

> Each active branch SHOULD carry a Master Doc copy reflecting its plan and completion state.

- **Baseline branch**: `{{BASELINE_BRANCH}}` (usually `main`)
- **Baseline Master Doc version**: `{{BASELINE_MASTER_DOC_VERSION}}`
- **Baseline Master Doc commit SHA**: `[[BASELINE_MASTER_DOC_SHA]]`

- **This branch goal**: `{{BRANCH_GOAL}}`
- **This branch scope delta vs baseline** (must be explicit):
  - `[[SCOPE_DELTA_1]]`
  - `[[SCOPE_DELTA_2]]`

**Plan execution status (this branch)**

- Completed:
  - [ ] `[[ITEM]]`
- In progress:
  - [ ] `[[ITEM]]`
- Not started:
  - [ ] `[[ITEM]]`

**Known drift vs baseline (MUST list all)**

- `[[DIFF_SUMMARY]]` (link to PR/commit)

##### 0.10 Glossary and canonical terminology (required)

> Any term that appears in contracts, UI labels, logs, dashboards, or acceptance criteria SHOULD be defined here.

| Term | Canonical definition | Synonyms (if any) | Notes |
| --- | --- | --- | --- |
| ConfigId | Immutable identifier for a specific configuration snapshot used by a run/job. | Config snapshot id | Required for reproducibility and rollback. Prefer registry/URI or content-addressed id. |
| Run Manifest | Immutable, replayable record of a single pipeline run (inputs, config, budgets, determinism, side-effects mode, artifact refs). | Run log | Stored and referenced by runId. |
| Job Envelope | Backend wrapper that tracks job orchestration status and contains the algorithm Pipeline Result. | Job record | Carries jobId and (once started) runId. |
| Pipeline Result | Algorithm execution envelope (status, output, stage summaries, errors, diagnostics). | Run result | status ∈ {ok,degraded,error}. |
| NormalizedError | A normalized error object with stable code, kind, and retryable. | Error code | Used across services and persisted in envelopes. |
| {{TERM_1}} | {{DEFINITION}} | [[SYNONYMS]] | [[NOTES]] |

##### 0.11 Traceability index (required; keep current)

> Maintain traceability from user value → requirements → contracts → tests → tasks.

- **Workflows**: `W1..Wn` in §1.4
- **Features**: `F-###` in §1.5
- **Functional Requirements**: `FR-###` in §1.6
- **Contracts**: `API-### / EVT-### / JOB-### / SCHEMA-### / ID-###` in §5
- **Tests/Gates**: `verify / smoke / compat / replay / eval` in §11.1 (Verification) and §11.3 (Acceptance checklist)
- **Implementation tasks**: `T-###` in §11.2

Optional traceability table:

| Workflow | Feature(s) | FR(s) | Contract(s) | Test(s) | Task(s) |
| --- | --- | --- | --- | --- | --- |

#### 1. Product Definition (PM-owned)

##### 1.1 Problem statement

- **User problem**: `{{WHO_STRUGGLES_WITH_WHAT}}`
- **Current workaround**: `{{CURRENT_WORKAROUND}}`
- **Why now**: `{{WHY_NOW}}`
- **Success is**: `{{USER_OUTCOME}}` (what changes for the user)

##### 1.2 Goals and non-goals

**Goals (measurable)**

- G1: `{{METRIC_TARGET}}` (example: `answer_citation_coverage >= 0.95`)
- G2: `[[METRIC_TARGET]]`

**Non-goals (explicit exclusions)**

- NG1: `{{OUT_OF_SCOPE_1}}`
- NG2: `[[OUT_OF_SCOPE_2]]`

##### 1.3 Users, roles, and permissions

> MUST list roles and their permission boundaries. If multi-tenant: include tenant boundary.

| Role | Primary jobs-to-be-done | Key permissions | Data scope |
| --- | --- | --- | --- |

**Permission model notes (required)**

- Permission identifiers are contracts. They MUST be stable once released.
- If you have page-level vs button-level permissions, define both.
- If multi-tenant: define isolation rules (tenant boundaries) and enforcement points.

##### 1.4 Primary user journeys (canonical workflows)

> Provide 3-7 “happy path” workflows. Each workflow MUST be testable end-to-end.

###### Workflow W1 - `{{WORKFLOW_NAME}}`

- **Actor**: `{{ROLE}}`
- **Trigger**: `{{TRIGGER}}`
- **Preconditions**: `{{PRECONDITIONS}}`
- **Steps**:
  1. `{{STEP_1}}`
  1. `{{STEP_2}}`
- **Success outcome**: `{{OBSERVABLE_RESULT}}`
- **Failure modes**: `{{EXPECTED_USER_VISIBLE_FAILURES}}`
- **Telemetry**: `{{EVENTS_METRICS_LOGS}}`

###### Workflow W2 - `[[WORKFLOW_NAME]]`

(Repeat)

##### 1.5 Feature inventory (source of truth)

> Maintain as a stable, prioritized list. Link to designs and contracts.

| Feature ID | Name | Description | Priority | Status | Owner | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |

##### 1.6 Functional requirements (testable)

> Each requirement MUST have: clear inputs/outputs, edge cases, and acceptance criteria.

**Requirement format (copy/paste)**

- **FR-XXX**: `{{TITLE}}`
  - **Description**: `{{WHAT_MUST_HAPPEN}}`
  - **Actors**: `{{ROLES}}`
  - **Preconditions**: `{{PRECONDITIONS}}`
  - **Main flow**: `{{MAIN_FLOW}}`
  - **Edge cases**: `{{EDGE_CASES}}`
  - **Acceptance criteria**:
    - AC1: `Given {{...}} When {{...}} Then {{...}}`
    - AC2: `Given {{...}} When {{...}} Then {{...}}`
  - **BDD scenarios** (recommended): `SCN-###` → `{{PATH_TO_FEATURE_OR_TEST}}` (see Appendix J)
  - **Observability**: `{{EVENTS_METRICS_LOGS}}`
  - **Security/privacy**: `{{DATA_CLASSIFICATION_ACCESS_CONTROLS}}`
  - **Contracts impacted**: `{{API/JOB/SCHEMA/ID_REFERENCES}}`

_Add FRs below:_

- FR-001: `[[...]]`

##### 1.7 Non-functional requirements (NFRs)

| NFR ID | Category | Requirement | Measurement / Test |
| --- | --- | --- | --- |
| NFR-002 | Availability | {{SLO}} | {{MONITORING_ALERTING}} |
| NFR-003 | Security | {{BASELINE_SECURITY_REQUIREMENT}} | {{SECURITY_TESTS}} |
| NFR-004 | Privacy | {{RETENTION_DELETION_REQUIREMENT}} | {{AUDIT}} |
| NFR-005 | Cost | {{COST_BUDGET}} | {{COST_DASHBOARD_GATES}} |

##### 1.8 UX/UI requirements and design assets

- **Design source of truth**: `{{DESIGN_LINK}}` (Figma or equivalent; prefer a specific file + page)
- **Prototype link (recommended)**: `{{PROTOTYPE_LINK}}` (for click-through flows / interactions)
- **Design system / tokens**: `[[DESIGN_SYSTEM_LINK_OR_PATH]]`
- **Key screens / frames** (pin to a stable frame ID or URL):
  - `{{SCREEN_NAME}}`: `[[LINK]]`

- **UI Spec Appendix** (required if UX is non-trivial): `[[UI_SPEC_APPENDIX_PATH_OR_URL]]` (use Appendix D template)

**If the UI has non-trivial interactions or ambiguous edge cases**, you MUST either:

1. fill out **Appendix D** in this Master Doc, or
1. maintain a standalone UI spec doc based on Appendix D and link it above.

Each Workflow `W#` in §1.4 SHOULD map to at least one Screen ID `UI-###` in the UI Spec Appendix.

**Embedding images in this doc**

- Store UI images under: `docs/assets/ui/{{YYYYMMDD}}/{{name}}.png`
- Reference images using a path relative to this file:
  - `!alt text (assets/ui/{{YYYYMMDD}}/{{name}}.png)`
- Each embedded image MUST include nearby:
  - owner
  - last updated date
  - what decision it supports
  - which requirement(s) it satisfies (link to §1.x)

**Hard-to-describe interactions (recommended)**

When behavior is better expressed visually (gestures, motion, transitions, complex wizards):

- Link the interactive prototype AND pin a snapshot/version (tag, commit hash, or dated export).
- Export and include at least:
  - **state screenshots** (empty/loading/success/error/edge cases)
  - **micro-interaction clips** (GIF/MP4) for animation/transition behavior
- Add a compact **interaction spec** as a diagram and/or table:
  - Mermaid `stateDiagram-v2` for UI state machines
  - Mermaid `sequenceDiagram` for UI → API → job orchestration flows
- Define **UI event contracts** (analytics events, client-side events, and API calls) in §5 Contracts.

**Testability hooks (recommended)**

- Provide stable UI selectors (data-testid) and a Playwright/Cypress happy-path plan.
- Add “golden” UI snapshots for key screens (baseline screenshots committed under `docs/assets/`).

#### 2. Domain Model (Architect + PM)

##### 2.1 Core entities and relationships

> Describe the authoritative domain model (not UI-only objects). Include IDs and lifecycle.

- Entity: `{{ENTITY_NAME}}`
  - ID: `{{ID_FORMAT}}`
  - Fields: `{{KEY_FIELDS}}`
  - Invariants: `{{MUST_ALWAYS_HOLD}}`
  - System of record: `{{COMPONENT}}`
  - Lifecycle states: `{{STATES}}`

_Add entity list:_

- `[[ENTITY_A]]`

##### 2.2 State machines (jobs, workflows, approvals)

> For any asynchronous process, define the state machine, idempotency, and cancellation rules.

- **Job/process**: `{{JOB_NAME}}`
- **States**: `{{CANONICAL_STATES}}`
- **Transitions** (allowed):
  - `{{FROM}} -> {{TO}}` when `{{CONDITION}}`
- **Idempotency**: `{{IDEMPOTENCY_KEYS_DEDUP_WINDOW_CONFLICT_POLICY_REPLAY}}`
- **Cancellation**: `{{BEST_EFFORT_OR_GUARANTEED}}`
- **Diagnostics**: `{{STABLE_CODES}}`

##### 2.3 Bounded contexts & ubiquitous language (DDD)

> Define domain ownership boundaries and the shared vocabulary. This reduces semantic drift between UI, backend, and contracts.

- **Ubiquitous Language glossary** (recommended; required for non-trivial domains):
  - Term: `{{TERM}}` - Definition: `{{DEFINITION}}` - Synonyms to avoid: `{{SYNONYMS}}` - Owner: `{{OWNER}}`
- **Bounded contexts** (map to repos and/or SDMM modules):
  - Context: `{{CONTEXT_NAME}}`
    - Owns (data + rules): `{{WHAT_IT_OWNS}}`
    - Public contracts (APIs/events/schemas): `{{CONTRACT_IDS_OR_LINKS}}`
    - Upstream/downstream: `{{CONTEXT_MAP_RELATIONSHIP}}`
- **Context map** (optional; diagram/link): `[[CONTEXT_MAP]]`
- **Anti-corruption layers** (if integrating external/legacy systems): `[[ACL_NOTES]]`

##### 2.4 Domain events, commands, and invariants (DDD → contracts)

> If the system uses events/commands, list the canonical events/commands and their contract IDs.

> Every event/command that crosses a boundary MUST be a first-class contract (schema + semantics + fixtures + checks).

- Event: `{{EVENT_NAME}}` (`{{SCHEMA_ID}}`)
  - Producer: `{{COMPONENT}}`
  - Consumers: `{{COMPONENTS}}`
  - Compatibility window: `{{WINDOW}}`
- Command: `{{COMMAND_NAME}}` (`{{SCHEMA_ID}}`)
  - Issuer: `{{COMPONENT}}`
  - Handler: `{{COMPONENT}}`

#### 3. System Overview (Architect-owned; PM must understand)

##### 3.1 Product surfaces

- Web: `{{Y_OR_N}}`
- Mobile web (H5): `{{Y_OR_N}}`
- Admin console: `{{Y_OR_N}}`
- Public API: `{{Y_OR_N}}`

##### 3.2 High-level architecture (context diagram)

> Insert a context diagram image and a short narrative.

!Context diagram (assets/{{YYYYMMDD}}/context-diagram.png)

Narrative:

- Users interact with `{{FRONTEND}}`.
- `{{BACKEND}}` is the system of record and orchestrator.
- `{{ALGO_SERVICE}}` performs `{{RETRIEVAL/LLM/...}}` and returns validated results.
- `{{CONTRACT_HUB}}` stores shared contracts, fixtures, identifiers, and checks.
- `{{INTEGRATION_HARNESS}}` runs end-to-end smoke and compatibility tests.

##### 3.3 Key architectural invariants (required)

> These invariants MUST remain true unless an ADR changes them.

- INV-01: `{{INVARIANT_1}}` (example: Backend is the sole SoR for canonical state transitions)
- INV-02: `{{INVARIANT_2}}` (example: All cross-boundary payloads validate against schemas)
- INV-03: `{{INVARIANT_3}}` (example: Model outputs are treated as untrusted inputs)

#### 4. Repo & Runtime Topology (Architect-owned)

##### 4.1 Repositories / packages (development boundaries)

> Support both multi-repo and monorepo patterns.

> List repos/modules and what each owns. Include boundary enforcement and canonical `verify` commands.

| Repo/Module | Purpose | Owner | Primary language | Canonical verify command |
| --- | --- | --- | --- | --- |
| {{FRONTEND_REPO_OR_PKG}} | UI/UX | {{TEAM}} | {{LANG}} | {{CMD}} |
| {{BACKEND_REPO_OR_PKG}} | SoR + orchestrator | {{TEAM}} | {{LANG}} | {{CMD}} |
| [[ALGO_REPO_OR_PKG]] | AI compute | [[TEAM]] | [[LANG]] | [[CMD]] |
| [[DATA_EVALS_REPO_OR_PKG]] | Offline datasets + evals + benchmarks (optional; recommended for AI products) | [[TEAM]] | [[LANG]] | [[CMD]] |
| {{INTEGRATION_REPO_OR_PKG}} | compose + smoke + compat | {{TEAM}} | {{LANG}} | {{CMD}} |

**Verification rules (required)**

- Each repo/module MUST provide a canonical `verify` entrypoint.
- `verify` SHOULD be deterministic and offline-by-default (stubs/snapshots) unless explicitly documented.

**Module boundary rules (required)**

- Allowed dependencies matrix: `{{DEPENDENCY_DAG_RULES}}`
- Boundary enforcement mechanism: `{{MECHANISM}}` (eslint/bazel/rules/etc)
- Rule: cross-boundary imports MUST use public entrypoints only (no deep imports).

##### 4.2 Runtime services (deployment boundaries)

> Keep runtime services minimal. List what runs in production and why.

| Service | Purpose | Scaling | Data stores | Notes |
| --- | --- | --- | --- | --- |

##### 4.3 Boundary classification (build/deploy/trust)

> For each boundary, state whether it is a build, deploy, and/or trust boundary.

> Use `Y/N` (no icons) to keep the doc tool-friendly.

Definitions:

- **Build boundary**: enforced module/package boundary within an artifact.
- **Deploy boundary**: mixed versions can be observed (rolling deploys, caches, async jobs).
- **Trust boundary**: inputs must be treated as untrusted (validate + sanitize + authz).

**If this project does not have an `algo` repo/service**, remove any `backend -> algo` boundary row(s).

| Boundary | Build (Y/N) | Deploy (Y/N) | Trust (Y/N) | Contracts | Evolution mode | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| backend -> algo | N | Y | Y | {{API/JOB_IDS}} | compat | {{NOTES}} |
| backend <-> db | N | N | Y | {{SCHEMA_IDS}} | expand/contract | {{NOTES}} |

#### 5. Contracts (Schematized, testable, versioned)

> **Rule**: Every cross-boundary interface MUST have:

> 1) schema, 2) semantics, 3) fixtures, 4) executable checks.

##### 5.1 Contract naming, casing, and versioning policy

This project MUST follow the governing engineering standard’s contract rules (Docs as Software (DAS) Standard {{ENGINEERING_STANDARD_VERSION}}, §4). Reference (fill in for repo-local copies): `{{ENGINEERING_STANDARD_PATH_OR_URL}}`.

- **Naming:** each contract MUST have a stable `CONTRACT_ID` (e.g., `run.manifest.v1`) and a schema version (e.g., `1.0.0`).
- **Casing (serialized contracts):** all JSON/YAML surfaces that cross a module/repo boundary **or are persisted** MUST use `camelCase`.
  - Internal code MAY use language-idiomatic casing (e.g., Python `snake_case`), but MUST adapt at the boundary.
- **Evolution:** contracts MUST follow Compatibility Mode (expand/contract; tolerant readers).
- **Documentation:** every contract used by this project MUST be listed in §5.2.

Casing examples (serialized):

```
{
  "jobId": "job_123",
  "runId": "2026-01-10T18:00:01Z/9b1d…",
  "sideEffectsMode": "dryRun",
  "inputRef": { "rawInputId": "raw_01HZ…", "inputHash": "sha256:…" }
}
```

##### 5.2 Contract inventory index (required)

| Contract ID | Type | Purpose | Owner | Schema ref | Semantics ref | Fixtures ref | Checks ref |
| --- | --- | --- | --- | --- | --- | --- | --- |

##### 5.3 API contracts (OpenAPI / RPC)

| API ID | Endpoint / Method | Purpose | Request schema | Response schema | Error codes | Owner |
| --- | --- | --- | --- | --- | --- | --- |

##### 5.4 Async/job contracts

> If long-running operations exist, define a job envelope contract.

- **Job envelope contract ID**: `{{JOB_ENVELOPE_ID}}` (example: `JOB-001`)
- **Job envelope schema**: `{{SCHEMA_REF}}`

**Required fields** (MUST match casing policy in §5.1)

- schema version field: `schemaVersion`
- job id field: `jobId`
- job type field: `jobType` (stable enum; see §5.7)
- status field: `status`
- timestamps: `createdAt` and `updatedAt` (and optionally `startedAt`/`finishedAt`)
- attempt counters + retry/backoff metadata
- correlation IDs (as applicable): `requestId`, `traceId`, `runId`
- diagnostics: stable codes + structured fields (avoid raw sensitive payload by default)

**Job state rules (minimum)**

- Terminal states MUST NOT transition back to non-terminal states.
- Cancellation MUST define semantics: best-effort vs guaranteed.
- Retry MUST be bounded and idempotent (dedup window + idempotency key policy).

##### 5.5 Streaming/realtime contracts (SSE/WS)

- **Contract ID(s)**: `[[STREAM-...]]`
- Message schema(s): `[[SCHEMA-...]]`
- Ordering guarantees: `[[...]]`
- Backpressure policy: `[[...]]`
- Reconnect policy: `[[...]]`

##### 5.6 Error taxonomy (normalized errors)

> Errors MUST be data (envelope), not language-specific exceptions across boundaries.

- Error envelope schema: `{{SCHEMA_ERROR_ID}}`
- Stable error codes: `{{ERROR_CODE_ID}}` (enumerated in an identifier contract)
- Unknown-code policy (consumer): `{{POLICY}}` (do not branch on message text)
- Retry classification policy: `{{WHERE_CLASSIFIED_AND_RULES}}`

##### 5.7 Identifier contracts

> Identifiers that appear in UI, logs, dashboards, run manifests, or cross-boundary payloads are contracts.

| ID Contract | What it contains | Owner | Stability | Path |
| --- | --- | --- | --- | --- |
| ID-ROUTES | route ids | {{TEAM}} | stable | {{PATH}} |
| ID-FEATURE-FLAGS | feature flags | {{TEAM}} | {{STABILITY}} | {{PATH}} |
| ID-JOB-TYPES | job type ids | {{TEAM}} | stable | {{PATH}} |
| ID-METRICS | metric ids | {{TEAM}} | {{STABILITY}} | {{PATH}} |
| ID-PROMPTS | prompt ids + versions | {{TEAM}} | {{STABILITY}} | {{PATH}} |
| ID-MODELS | model ids + versions | {{TEAM}} | {{STABILITY}} | {{PATH}} |

##### 5.8 Golden fixtures (examples)

| Fixture ID | Contract | Purpose | Path | Used by checks |
| --- | --- | --- | --- | --- |
| FX-002 | JOB-001 | representative failure | {{PATH}} | {{CHECKS}} |

#### 6. Data, Privacy, and Compliance (Architect + PM)

##### 6.1 Data classification

| Data type | Examples | Sensitivity | Retention | Access |
| --- | --- | --- | --- | --- |
| Raw user content | {{audio/text/images}} | high | {{DAYS}} | {{ROLES}} |
| Derived artifacts | {{embeddings/indexes/caches}} | inherits | {{DAYS}} | {{ROLES}} |

##### 6.2 Storage design

- Primary database: `{{TYPE}}`
- Vector database: `[[TYPE]]`
- Object storage: `[[TYPE]]`
- Caching: `[[TYPE]]` with key/version policy (cache keys are contracts)

##### 6.3 Deletion and retention

- User deletion flow: `{{WHAT_HAPPENS_TO_DERIVED_DATA}}`
- Retention windows: `{{...}}`
- Audit trail: `[[...]]`

##### 6.4 Security baseline (minimum)

- Authn/authz enforcement point(s): `{{WHERE_ENFORCED}}`
- Encryption at rest: `{{WHAT_DATA}}`
- Secrets management: `{{HOW}}`
- Logging policy: `{{NO_SECRETS_AVOID_RAW_SENSITIVE_BY_DEFAULT}}`

##### 6.5 Threat model (recommended)

- Threat model doc/link: `[[LINK_OR_PATH]]`
- Trust boundaries covered: `[[LIST]]`
- Top threats and mitigations: `[[SUMMARY]]`

#### 7. AI / Algorithm Design (Architect-owned; PM reviewed)

> Define AI behavior precisely enough to implement without guessing.

##### 7.1 AI capabilities

- C1: `{{CAPABILITY_1}}` (example: RAG QA with citations)
- C2: `[[CAPABILITY_2]]`

##### 7.2 Pipeline(s) (stage-based)

> For each pipeline, define stages, contracts, budgets (hard/soft), determinism tier, and failure handling.

**Pipeline P1: `{{NAME}}`**

- Determinism tier: `{{tier0|tier1|tier2}}` and why
- Budgets (declare hard vs soft):
  - `time_ms`: `{{VALUE}}` (`hard|soft`)
  - `max_external_calls`: `{{VALUE}}` (`hard|soft`)
  - `max_tokens`: `{{VALUE}}` (`hard|soft`)
  - `max_cost_units`: `{{VALUE}}` (`hard|soft`)
- Stages:
  1. `{{stage_id}}`: input `SCHEMA-...`, output `SCHEMA-...`, diagnostics `{{CODES}}`, budget ledger `SCHEMA-BUDGET-...`
  1. `[[stage_id]]`: ...

**Run manifest & replay (required for production-visible outputs)**

- Run manifest schema: `{{SCHEMA_RUN_MANIFEST_ID}}`
- Must record: version fingerprints, config/profile id, budgets, determinism tier, snapshots, tool/model identifiers.
- Replay command(s): `{{COMMANDS}}`

##### 7.3 Retrieval (RAG) design (if applicable)

- Index sources: `[[docs/cases/logs]]`
- Access control: `{{PER_TENANT_OR_PER_OWNER_RULES}}`
- Chunking rules: `[[...]]`
- Embedding model(s): `{{ID-MODELS_REFERENCE}}`
- Retrieval policy: `[[top_k, filters]]`
- Citation policy: `{{RULES_FOR_CITATIONS_AND_FAILURES}}`

##### 7.4 Prompting and tool policy (if applicable)

- Prompt IDs: `{{ID-PROMPTS_REFERENCE}}`
- Tool allowlist: `{{TOOLS}}`
- Tool budgets and timeouts: `{{...}}`
- Prompt injection mitigations: `{{RULES}}`

##### 7.5 Validation and repair ladder

- Output schema validation: `{{STRICT_OR_LENIENT}}`
- Repair steps:
  1. normalize/coerce
  1. retry with constraints
  1. fallback
  1. escalate (manual review / typed error)

##### 7.6 Evaluation as a contract

- Metrics: `{{METRICS}}` (example: faithfulness, answer_relevance, context_relevance)
- Thresholds: `{{PASS_FAIL_OR_TIERS}}`
- CI eval set: `{{WHERE_AND_SIZE}}`
- Offline benchmark: `[[WHERE_AND_SIZE]]`
- Report schema: `{{SCHEMA_EVAL_REPORT_ID}}`

#### 8. Observability, Operations, and Cost

##### 8.1 Logging, tracing, correlation IDs

- Correlation ID format: `{{FORMAT}}`
- Must propagate: `frontend -> backend -> algo -> async callbacks`
- Canonical field names (serialized; MUST be camelCase at boundaries): `requestId`, `traceId`, `jobId`, `runId`, `manifestHash`, `inputHash`, `profileId`, `sideEffectsMode`
- Redaction policy: `{{NO_SECRETS_AVOID_RAW_SENSITIVE_BY_DEFAULT}}`

##### 8.2 Metrics and dashboards

- Golden signals: latency, error rate, throughput, saturation
- AI signals: token usage, cost estimate, schema validation failure rate, repair rate, degraded rate
- Job signals (if async): queue depth, attempt counts, terminal outcomes

##### 8.3 Alerting and SLOs

| Operation | SLO | Alert condition | Owner |
| --- | --- | --- | --- |

##### 8.4 Runbooks and operational readiness (recommended)

- Common failure modes: `[[queue backlog, model outage, vector db latency spike, cost spike]]`
- Runbook links: `[[PATHS]]`
- On-call / escalation: `[[POLICY]]`

#### 9. Release Plan (PM + Architect + QA)

##### 9.1 Milestones and phases

| Phase | Duration | Scope | Exit criteria |
| --- | --- | --- | --- |
| Phase 2 | [[...]] | [[...]] | [[...]] |

##### 9.2 Rollout strategy

- Feature flags: `{{ID-FEATURE-FLAGS_REFERENCE}}`
- Shadow mode: `[[WHERE]]`
- Rollback plan: `{{STEPS}}`

##### 9.3 Compatibility and migration plan (required when breaking changes exist)

- Compatibility window: `{{DATES_OR_VERSIONS}}`
- Expand/contract steps: `{{...}}`
- Consumer upgrade plan: `{{...}}`

#### 10. Risks, Open Questions, and Assumptions

##### 10.1 Top risks

| Risk | Impact | Likelihood | Mitigation | Owner |
| --- | --- | --- | --- | --- |

##### 10.2 Open questions (must be resolved before implementation)

| Question | Blocker? (Y/N) | Owner | Target date | Notes |
| --- | --- | --- | --- | --- |

##### 10.3 Assumptions (explicit)

- A1: `{{...}}`

#### 11. AI Execution Plan (No-code, unambiguous)

> This section is what AI agents execute. It MUST be precise, scoped, and verifiable.

> It SHOULD NOT include code-level details, but MUST include contracts, tasks, and gates.

##### 11.1 AI rules of engagement (copy/paste into AI tasks)

- Allowed repos/modules: `{{LIST}}`
- Default forbidden changes (unless explicitly authorized via task or ADR):
  - no public identifier renames
  - no breaking contract changes without an explicit compatibility plan
  - no dependency upgrades **except** security patches approved by owner(s)
  - no opportunistic refactors
  - no cross-module imports that violate boundary rules

- Required verification (MUST list exact commands):
  - contracts: `{{VERIFY_CMD_CONTRACTS}}`
  - frontend: `{{VERIFY_CMD_FRONTEND}}`
  - backend: `{{VERIFY_CMD_BACKEND}}`
  - algo: `[[VERIFY_CMD_ALGO]]`
  - integration: `{{VERIFY_CMD_INTEGRATION}}` (plus `smoke`/`compat` if separate)

- Output required:
  - updated fixtures/tests where contracts or behavior changes
  - updated Master Doc sections when requirements/architecture change

##### 11.2 Work breakdown structure (WBS)

> Keep tasks small, independently verifiable, and ordered by dependencies.

| Task ID | Description | Scope (paths) | Contracts touched | Tests/verify | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |

##### 11.3 Acceptance checklist (Definition of Done)

- [ ] All referenced FRs implemented and tested
- [ ] Contract artifacts updated (schema + semantics + fixtures + checks) if applicable
- [ ] Integration smoke tests pass
- [ ] No unapproved scope creep
- [ ] Release notes / change log updated
- [ ] Master Doc updated **if required** (requirements/workflows/contracts/topology/gates changed), or explicitly marked as “no doc change required”.

#### Annex A - AI Guide: Converting a PRD into this Master Doc

> Use this when you have a “normal PRD” (narrative + screenshots) and need to produce an execution-ready Master Doc.

##### A.1 Conversion objectives

A converted Master Doc must:

1. eliminate ambiguity (precise requirements + acceptance criteria),
1. define end-to-end workflows,
1. define contracts and boundaries (APIs, jobs, schemas, identifiers),
1. define verification gates and an executable plan for implementation.

##### A.2 Step-by-step conversion procedure

1. **Ingest and index the PRD**
  - Extract: goals, non-goals, roles, workflows, screens, features, constraints, edge cases.
  - Create a PRD coverage checklist: every PRD requirement must map to a Master Doc section (Workflows, FRs, NFRs, Contracts).

1. **Normalize terminology**
  - Populate/update §0.10 Glossary.
  - Decide casing policy in §5.1.

1. **Convert narrative into workflows**
  - For each major journey, write `W1..Wn` with actor, trigger, steps, success, failures, telemetry.

1. **Convert features into stable IDs**
  - Fill §1.5 with `F-###`.
  - Write §1.6 with `FR-###` using Given/When/Then acceptance criteria.

1. **Identify domain entities and state machines**
  - Define core entities and invariants (§2.1).
  - For async operations: define state machines, idempotency, cancellation (§2.2).

1. **Derive contracts**
  - For each workflow step that crosses a boundary, define contract IDs and link:
    - schema, semantics, fixtures, checks.
  - For AI outputs: define output schema, validation, and repair ladder.

1. **Add non-functional requirements**
  - Performance targets, privacy/security, retention, observability, cost budgets.

1. **Draft architecture**
  - Repo topology (§4.1): modules, owners, boundary rules.
  - Runtime topology (§4.2): services and stores.
  - Boundary classification (§4.3): mark build/deploy/trust as Y/N.

1. **Define verification**
  - For each repo/module: define canonical `verify` command.
  - Add integration `smoke` + `compat` gates as required.

1. **Produce the AI execution plan**
  - Build WBS (§11.2): small tasks with explicit scope and gates.
  - Order tasks by dependencies and contract evolution rules.

1. **Ambiguity checks (must pass)**
  - Every FR has acceptance criteria.
  - Every cross-boundary interaction has a contract reference.
  - Every risky behavior has a fallback/repair rule.
  - Every contract change has fixtures + executable checks.
  - Traceability table (§0.11) connects workflows to tasks.

##### A.3 PRD content handling rule

- Do NOT paste the PRD verbatim into this file.
- DO extract all product/UX requirements into structured sections (Workflows, Features, FRs, NFRs).
- Keep the original PRD as an input reference in §0.5.
- For UI mockups, embed only the images necessary to disambiguate behavior, and link to the prototype source.

##### A.4 Output deliverables after conversion

- A completed Master Doc (Sections 0-11)
- A list of Open Questions that block implementation
- A complete contract inventory (API/job/schema/identifier lists)
- An initial WBS with verification commands
- A traceability table mapping workflows -> features -> FRs -> contracts -> tests -> tasks

#### Annex B - Template Snippets (copy/paste)

##### B.1 Requirement snippet

- **FR-XXX**: `{{title}}`
  - **Description**: `{{...}}`
  - **Actors**: `{{...}}`
  - **Preconditions**: `{{...}}`
  - **Main flow**: `{{...}}`
  - **Edge cases**: `{{...}}`
  - **Acceptance criteria**:
    - AC1: `Given {{...}} When {{...}} Then {{...}}`
    - AC2: `Given {{...}} When {{...}} Then {{...}}`
  - **Observability**: `{{...}}`
  - **Security/privacy**: `{{...}}`
  - **Contracts impacted**: `{{...}}`

##### B.2 Task snippet (AI execution)

| Task ID | Description | Scope (paths) | Contracts touched | Tests/verify | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |

##### B.3 AI prompt snippet (optional)

```
Task:
- Goal:
- Scope (allowed paths):
- Exclusions:
- Boundaries touched (build/deploy/trust):
- Contracts impacted (IDs + paths):
- Change classification (additive/behavioral/breaking):
- Determinism tier target (`tier0`/`tier1`/`tier2`) if applicable:
- Budgets (time_ms/max_tokens/max_external_calls/cost_units) if applicable:
- Fixtures to add/update:
- Commands to run (verify/smoke/compat/replay/eval):
- Risk + rollout/rollback:
- Non-goals:
```

#### Annex C - Branch Copies and Sync Policy

> Each Git branch may carry its own Master Doc copy.

> When the overall plan changes, you MUST update all active branch copies or explicitly document divergence.

##### C.1 When to sync

You MUST sync Master Doc changes across branches when:

- product scope changes (new/removed workflows, features, FRs)
- contract surfaces change (schemas, identifiers, API semantics)
- architecture boundaries change (repos, packages, services, dependency rules)
- rollout strategy or compatibility windows change

You SHOULD sync when:

- acceptance criteria change
- test gates change (`verify`, `smoke`, `compat`, `replay`, `eval`)
- risk/open-questions resolution changes

##### C.2 Minimal sync procedure (human or AI-assisted)

1. Make the change in the baseline branch copy (usually `main`) and bump the Master Doc version.
1. For each active branch:
  - cherry-pick or rebase the Master Doc commit(s), OR
  - manually apply the same changes and record:
    - the baseline version you synced to (§0.9)
    - any branch-specific divergence (§0.9)
1. If a branch cannot adopt the change, add an ADR entry explaining why and define a reconciliation plan.

##### C.3 Practical guardrails (recommended)

- Add a CI check that fails if:
  - required sections are missing (Glossary, Contracts Index, WBS, Open Questions), or
  - the branch copy does not declare its baseline version in §0.9.
- Add a PR checkbox: “Master Doc updated (or not needed)”.

#### Annex D - UI Spec Appendix

This Master Doc template is designed to be copied into a repo as a standalone `master_doc.md`. To avoid maintaining the **UI Spec Appendix template** in two places, this appendix intentionally contains only a reference.

If the project has user-facing UI, you MUST maintain a UI Spec Appendix using the template in **Docs as Software (DAS) Standard {{ENGINEERING_STANDARD_VERSION}}, Appendix D**.

- Repo-local UI Spec Appendix path (fill in): `{{UI_SPEC_APPENDIX_PATH}}` (recommended: `docs/ui_spec_appendix.md`)
- Standard reference (fill in): `{{ENGINEERING_STANDARD_PATH_OR_URL}}#appendix-d-ui-spec-appendix-template-v1`
  - If your doc host does not support anchors, search within the standard for `appendix-d-ui-spec-appendix-template-v1` or for the heading `Appendix D - UI Spec Appendix Template (v1)`.

Minimal procedure:

1. Create `{{UI_SPEC_APPENDIX_PATH}}` in the repo.
1. Copy the template from the standard’s Appendix D into that file.
1. Link to it from §1.8 (UI screen inventory & workflows).

<a id="appendix-d-ui-spec-appendix-template-v1"></a>

## Appendix D - UI Spec Appendix Template

### UI Spec Appendix - Template

Status: `{{STATUS}}` (`draft | active | frozen | deprecated`) Version: `{{VERSION}}` (SemVer recommended) Last updated: `{{LAST_UPDATED_YYYY_MM_DD}}` Owners: PM `{{OWNER_PM}}`, Design `{{OWNER_DESIGN}}`, Eng `{{OWNER_ENG}}` Design source of truth: `{{FIGMA_OR_PROTOTYPE_URL}}` Design system / tokens: `[[DESIGN_SYSTEM_LINK_OR_PATH]]` Asset directory (repo): `docs/assets/ui/{{YYYYMMDD}}/` (recommended)

#### 0. Purpose and scope

This appendix makes **UI/UX behavior implementable and testable** when words alone are ambiguous.

It is the canonical reference for:

- **screens** and their **states** (loading/empty/error/permission/degraded),
- **user interactions** (click/keyboard/gesture), validation, and side effects,
- mapping **Workflows (W1..Wn)** → **Screens (UI-###)** → **Contracts (API/JOB/EVT/ID)**,
- visual/interaction **fixtures** for testing and for AI agents (exported images, short recordings).

Non-goals:

- It is **not** a pixel-perfect design spec replacing the design tool.
- It does **not** document internal UI component implementation details.

#### 1. Principles and conventions

##### 1.1 Stability and identifiers

- **MUST:** Use stable **Screen IDs**: `UI-001`, `UI-002`, …
- **MUST:** If the app has routing, each screen MUST map to a stable **Route ID** (recommended to store in `contracts`).
- **MUST:** Critical interactive elements MUST have stable test selectors (e.g., `data-testid`) for E2E tests.
Treat these selectors as **identifier contracts**: do not change without updating tests + this appendix.

- **SHOULD:** Telemetry event names and properties SHOULD be treated as contracts (stable naming; versioned when breaking).

##### 1.2 How to include visuals and interactions

When behavior is hard to describe in words:

- **MUST:** Link the interactive prototype (`{{FIGMA_OR_PROTOTYPE_URL}}`) **and** embed enough exported images to disambiguate behavior.
- **SHOULD:** Prefer **annotated PNGs** for key states.
- **MAY:** Include a short **GIF/MP4** (5-20s) for interactions/animations that require motion to understand.
- **MUST:** All embedded visuals MUST use **scrubbed / synthetic data**. No production PII.
- **MUST:** Every embedded image/video MUST include:
  - caption describing the intended behavior in words,
  - owner + last-updated date,
  - what decision/requirement it supports (link to `W# / F-### / FR-###`).

Recommended file naming:

- `UI-001__create-course__empty.png`
- `UI-001__create-course__error_invalid-title.png`
- `UI-001__create-course__interaction_drag-drop.mp4`

##### 1.3 Traceability rule

- **MUST:** Every Workflow `W#` referenced in the Master Doc MUST map to:
  - at least one Screen ID `UI-###`,
  - at least one Contract ID (`API-### / JOB-### / EVT-### / ID-###`) if the step crosses a boundary.

#### 2. Screen inventory (required)

| Screen ID | Name | Surface | AI interaction mode | Route ID | Primary workflow(s) | Feature ID(s) | Design link | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Notes:

- **MUST:** Every Screen ID (`UI-###`) MUST correspond to a named Frame in the design source of truth. Prefer durable frame links over free-form URLs.
- **AI interaction mode values:** `static` (no user-facing AI), `streaming` (incremental output), `async_job` (long-running job/poll), `optimistic` (optimistic local updates with rollback).
- **SHOULD (advanced):** Automate this via the design-to-code traceability check described in §6.6 (detect orphaned specs and rotting links).

#### 3. Workflow-to-screen maps (required for W1..Wn)

> Provide at least one map per canonical workflow in the Master Doc.

##### W1 - `{{WORKFLOW_NAME}}`

| Step | User intent | Screen ID | UI action | System effect | Contracts | Success UI | Failure UI |
| --- | --- | --- | --- | --- | --- | --- | --- |

Optional diagram (Mermaid flowchart):

```
flowchart TD
  A[UI-001: {{SCREEN_NAME}}] -->|submit| B[API-001: {{ENDPOINT}}]
  B --> C{JOB-001 created?}
  C -->|yes| D[UI-002: {{STATUS_SCREEN}}]
  C -->|no| E[UI-001: show error state]
```

#### 4. Per-screen specification (repeat for each Screen ID)

##### UI-001 - `{{SCREEN_NAME}}`

**Purpose / user value** `{{WHAT_USER_IS_DOING_HERE}}`

**AI interaction mode** `{{static|streaming|async_job|optimistic}}`

- Streaming contract (if applicable): `STREAM-###`
- Citation contract (if applicable): `CIT-###` / `AnnotatedContent`

**Entry points**

- From: `{{PREV_SCREEN_OR_DEEP_LINK}}`
- Preconditions: `{{AUTH/PERMISSIONS/STATE}}`

**Primary states (required)**

| State ID | Name | When shown | Visual reference | Acceptance notes |
| --- | --- | --- | --- | --- |
| S1 | Empty | {{...}} | !UI-001 empty (assets/ui/{{YYYYMMDD}}/UI-001__empty.png) | {{NOTES}} |
| S2 | Ready | {{...}} | !UI-001 ready (assets/ui/{{YYYYMMDD}}/UI-001__ready.png) | {{NOTES}} |
| S3 | Error | {{...}} | !UI-001 error (assets/ui/{{YYYYMMDD}}/UI-001__error.png) | {{ERROR_CODE/MSG_RULES}} |
| S4 | Permission denied | {{...}} | [[OPTIONAL_IMAGE]] | {{POLICY}} |

**AI-native states (required if this screen includes AI interaction)**

> Use these when the screen’s AI interaction mode is `streaming` / `async_job` / `optimistic`, or when AI-generated content is user-facing.

| State ID | Name | When shown | Visual reference | Acceptance notes |
| --- | --- | --- | --- | --- |
| A1 | Streaming | partial output is arriving | !UI-001 streaming (assets/ui/{{YYYYMMDD}}/UI-001__streaming.png) | Define append vs replace behavior + scroll anchoring |
| A2 | Repairing | system is attempting an automated fix after a recoverable failure | [[OPTIONAL_IMAGE]] | Must be cancellable; show what is being fixed |
| A3 | Needs confirmation | AI proposes an action that requires user confirmation | [[OPTIONAL_IMAGE]] | Must show object identity + impact; safe default is “Cancel” |
| A4 | Cancelled | user/system cancelled generation | [[OPTIONAL_IMAGE]] | Provide retry/regenerate affordance |

**Controls and interactions (required)**

| Element | Selector (test id) | Interaction | Validation | System effect | Contracts | Notes |
| --- | --- | --- | --- | --- | --- | --- |

**Client-side validation rules**

- V1: `{{RULE}}` → user message: `{{COPY}}`
- V2: `[[RULE]]`

**Error mapping (user-visible)**

- `code: {{ERROR_CODE}}` → `{{UI_BEHAVIOR}}`
- `code: [[ERROR_CODE]]` → `[[...]]`

**Loading / progress / cancellation**

- Loading (network latency) indicator rules: `{{RULES}}`
- Thinking/AI processing indicator rules: `{{RULES}}` (use progress/stage summaries; distinguish from Loading)
- Streaming: `{{YES|NO}}` (if YES: contract `STREAM-###`, mode `append|replace`, scroll anchoring policy, stop/pause UX)
- Cancellation: `{{ALLOW|DISALLOW}}` (and why)

**Citations / references (required if the screen renders citations)**

- Citation contract: `CIT-###` (or `AnnotatedContent` per §4.4.9)
- Rendering: `inline markers | footnotes | side panel`
- Marker syntax / span rules: if marker-based, specify `markers.syntax` (default `[[ref:{refId}]]`); if offset-based, specify `offsetUnit` and rendering behavior for spans.
- Integrity handling: UI behavior for `integrity.status = ok|partial|invalid`.
- Interaction: `hover preview | click open panel | click open source`
- Fallback: behavior when references are missing/malformed
- Accessibility: keyboard navigation + screen-reader labels for each reference

**Telemetry (recommended)**

- Events emitted: `EVT-###` / `{{eventName}}`
- Properties: `{{PROPERTY_SCHEMA_OR_LINK}}`

**Accessibility (required)**

- Keyboard navigation: `{{REQUIREMENTS}}`
- Screen reader / ARIA: `{{REQUIREMENTS}}`
- Focus management: `{{REQUIREMENTS}}`
- Contrast / motion reduction: `{{REQUIREMENTS}}`

**Responsiveness (required if multi-device)**

- Breakpoints: `{{...}}`
- Layout changes: `{{...}}`

**Copywriting / i18n (if applicable)**

- String keys: `{{...}}`
- Localization notes: `{{...}}`

#### 5. Design system and component contracts (recommended)

- Design tokens source: `[[DESIGN_SYSTEM_LINK_OR_PATH]]`
- Shared components used/introduced:
  - `COMP-001 {{ComponentName}}` - props/events contract link: `[[STORYBOOK_OR_DOC_LINK]]`

#### 6. UX non-functional requirements (recommended)

- Perceived performance targets: `{{P95_INTERACTIVE_TIME_BUDGET}}`
- Skeleton/loading guidance: `{{...}}`
- Offline / poor network handling: `{{...}}`

#### 7. Test plan mapping (required for critical flows)

- **E2E smoke scenarios** (Playwright/Cypress/etc.):
  - `smoke-ui-01`: covers `W1` (`UI-001 → UI-002`)
- **Visual regression**: `{{YES/NO}}` (tool + baseline location)
- **Contract fixtures referenced**: `{{FIXTURE_IDS}}`

On failure, tests SHOULD capture:

- screenshot(s)
- DOM snapshot / trace
- correlation IDs / request IDs
- pins manifest / environment versions

#### 8. Change log (append-only)

| Date | Version | Author | Summary | Links |
| --- | --- | --- | --- | --- |

#### 9. Open questions (must be tracked)

| ID | Question | Owner | Blocker? | Target date | Notes |
| --- | --- | --- | --- | --- | --- |

## Appendix E - Multi-Repo Contract-Driven Standard

> **Appendix E note:** This appendix is included as a deep-dive reference; if any statement here conflicts with the Main Body, the Main Body wins per §2.1.

### AI-Optimized Contract-Driven Multi-Repo Engineering Standard

Status: General-purpose reference for AI-assisted development of full-stack AI products Scope: End-to-end systems that commonly include **Frontend**, **Business Backend (System of Record / Orchestrator)**, and an **Algorithm/Model Service** (plus optional Admin/Backoffice, Integration Harness, and Data/Evals). This standard focuses on **repo boundaries**, **contracts**, **contract evolution**, and **AI-friendly execution workflows**.

#### 0. Normative language (Appendix E)

This appendix uses **BCP 14** requirement keywords (RFC 2119 + RFC 8174).

- The primary normative keywords used in this appendix are: **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**.
- If synonymous terms appear (e.g., **REQUIRED**, **SHALL**, **SHALL NOT**, **RECOMMENDED**, **OPTIONAL**), they MUST be interpreted as the corresponding BCP 14 keyword; authors SHOULD prefer the primary keywords above for clarity.
- Lowercase forms (“must”, “should”, etc.) are non-normative unless explicitly marked.

Interpretation guidance:

- **MUST / MUST NOT**: required for correctness, safe cross-repo evolution, or to prevent drift.
- **SHOULD / SHOULD NOT**: strongly recommended; deviation requires explicit justification and compensating controls.
- **MAY**: optional.

#### 0.1 Key definitions

- **Producer**: the component/service that emits a payload or behavior (e.g., an HTTP response, an event, a callback) and is responsible for maintaining its contract.
- **Consumer**: the component/service that receives a payload or depends on a behavior and is responsible for tolerant reading and correct usage.
- **Contract**: anything two independently built units must agree on. A complete contract includes:
  1. **Schema** (machine-checkable shape),
  1. **Semantics** (behavioral rules/invariants),
  1. **Examples/fixtures** (known-good and representative failures),
  1. **Executable checks** (producer validation and/or consumer decoding tests).
- **Contract artifact**: the machine-checkable representation of a contract (spec/schema/types/fixtures/codegen config) stored in the contract hub.
- **Decision owner**: the single party that decides contract semantics and approves changes (often, but not always, the producer).
- **Contract hub**: the canonical repository (or canonical module in a monorepo) that stores contract artifacts and runs executable compatibility checks.

##### 0.1.1 Evolution modes

These terms describe **deployment reality**, not Git mechanics.

- **Compatibility Mode**: producer and consumer can deploy independently. Partial upgrades are observable in at least one environment (staging/prod), whether due to separate pipelines, rolling deploys, caches, or async processing. Breaking changes therefore require compatibility windows, explicit versioning or dual-support strategy, and observable rollout.

- **Refactor Mode**: a boundary behaves as if it can be updated “atomically” from the perspective of the environment observing it.

**Important correction:** Refactor Mode is **reliably achievable only within a single deployable artifact** (e.g., within one frontend bundle, within one backend process, within one container image) or within **strict atomic cutovers** (blue/green or equivalent) where *no requests can cross the boundary with mixed versions*.

In most real multi-service systems (even if built from a coordinated release manifest), rolling deployments and distributed caching mean partial upgrades are still observable. Therefore:

  - **MUST:** Treat cross-repo, cross-service contracts as **Compatibility Mode by default**.
  - **MAY:** Treat a cross-repo change as Refactor Mode **only** if you can demonstrate (and enforce) that no environment can observe mixed versions across the boundary during rollout.

#### 1. Purpose

AI coding is most effective when:

- the change scope is small,
- ownership is explicit,
- interfaces are mechanically checkable,
- verification is fast and deterministic,
- integration is continuously validated.

Most AI products are systems spanning multiple runtimes, languages, and release cadences. This standard defines how to:

1. split a system into repos without introducing microservice-style runtime complexity,
1. define, test, publish, and evolve contracts safely,
1. structure work so AI agents can implement changes without breaking integration.

#### 2. Critical distinction: repo boundaries vs runtime/service boundaries

A common failure mode is equating “more repos” with “more services.”

- **Repo split** is a *development organization* decision.
  - Primary effect: smaller change scope; clearer ownership; fewer AI-induced blast-radius failures.
  - It does **not** inherently add runtime latency.

- **Service split** is a *runtime architecture* decision.
  - Primary effect: adds network hops, distributed failure modes, operational/debugging cost.

**MUST:** Do not split runtime services purely to make code “AI-sized.”

Instead:

- keep runtime boundaries minimal and intentional,
- use repo boundaries plus internal modularization to keep AI change scopes small.

**Rule of thumb**

- Split into more **repos** when repo size, language/toolchain mismatch, access control, ownership boundaries, or AI-edit reliability requires it.
- Split into more **services** only when you need at least one of:
  - independent scaling,
  - hard security isolation,
  - independent deploy/rollback,
  - regulatory isolation,
  - clearly separable operational ownership.

#### 3. Topology choices

Choose the smallest topology that keeps AI tasks bounded and contracts explicit.

##### 3.1 Topology A - Monorepo with strict internal packages

Use when:

- one team owns most components,
- releases are tightly coupled,
- you want maximum refactor agility.

**SHOULD:** Use strict internal packages/modules with enforced boundaries.

##### 3.2 Topology B - Multi-repo with a contract hub

Use when:

- components differ by language/toolchain or runtime,
- teams deploy independently,
- repo size exceeds what AI agents handle safely,
- you require explicit ownership/access boundaries.

This document primarily targets Topology B.

##### 3.3 Topology C - Hybrid

Common hybrids:

- separate `algo` repo (fast-moving) + monorepo for `frontend`/`backend`,
- separate `contracts` repo + monorepo for the rest,
- separate `data-evals` repo for offline datasets and eval harness.

**MUST:** Regardless of topology, contracts MUST be explicit, testable, and governed.

#### 4. Recommended multi-repo baseline (Topology B)

##### 4.1 Minimal repo set

Most AI systems are well served by **4-6 repos**, while keeping runtime services minimal:

1. **`contracts`** - contract hub (schemas, fixtures, identifiers, codegen)
1. **`frontend`** - user experience and client logic
1. **`backend`** - system-of-record + orchestrator
1. **`algo`** - model/compute service

Optional but frequently high leverage:

1. **`integration`** - local dev environment + end-to-end smoke tests + compatibility runners
1. **`data-evals`** - offline datasets, eval harness, benchmark reports

Optional (product-dependent):

1. **`admin`** - backoffice UI and/or admin backend if it is truly a distinct product surface

**MUST:** Keep the number of runtime services small. Adding repos is often cheaper than adding services.

##### 4.2 What each repo owns

###### Repo: `contracts` (Contract Hub)

Owns canonical storage and distribution of:

- OpenAPI specs (REST), and/or gRPC/Protobuf/GraphQL schemas
- JSON Schemas / AsyncAPI for events, callbacks, and streaming messages
- standard envelopes (errors, jobs, pagination)
- cross-repo identifiers (error codes, job types, permission codes, feature flags)
- golden fixtures (known-good payloads) used by tests and mocks
- evaluation/scoring contract artifacts (rubrics, metric definitions, thresholds) when shared across repos
- code generation templates/config (and optionally generated packages)

**MUST:** `contracts` contains **representations and executable checks only** (schemas/types/constants/fixtures/validators/tests), not product/business runtime logic.

**Clarification:** A small amount of *pure* “contract execution code” is acceptable when it is the executable form of a contract (e.g., schema validators, scoring/metric functions, fixture decoders). It MUST remain dependency-light and MUST NOT require network/persistence.

###### Repo: `frontend`

Owns:

- UI/UX and view state
- client networking via generated clients or thin wrappers
- local validation and display mapping

**SHOULD:** Internally modularize (e.g., Single-Deploy Modular Engineering) so AI tasks remain small and boundaries are enforceable.

###### Repo: `backend` (system-of-record + orchestrator)

Owns:

- authoritative domain state and persistence
- authn/authz policy and enforcement
- business workflows and orchestration
- stable public APIs for clients and integrations
- canonical validation and canonical error mapping
- long-running job orchestration for AI workloads (preferred)

**SHOULD:** Remain a modular monolith unless additional runtime splits are operationally justified.

###### Repo: `algo` (model/compute service)

Owns:

- model inference, prompt pipelines, retrieval/tool calling
- structured extraction/scoring pipelines
- streaming responses (if required)
- strict validation/normalization of model outputs against schemas
- model-specific safety controls (prompt injection mitigation, tool allowlists)

**MUST:** Treat model outputs as *untrusted* until validated and normalized.

###### Repo: `integration` (optional, recommended)

Owns:

- docker-compose/dev containers and environment templates
- end-to-end smoke tests (“happy path” flows)
- contract compatibility test runners
- version-matrix compatibility checks (optional but valuable)

This repo is the strongest guardrail against cross-repo drift caused by many small AI-authored changes.

###### Repo: `data-evals` (optional, high leverage)

Owns:

- offline datasets (scrubbed, versioned)
- eval harness (runner) and scoring scripts (sourced from / pinned to the shared scoring contract artifact)
- benchmark reports and regression dashboards
- labeling prompts and annotation guidance

**MUST:** `data-evals` is not a dumping ground for secrets or raw production data.

#### 5. Contracts: system-wide taxonomy

Track at least these contract categories.

##### 5.1 External API contracts

- endpoints, methods, paths
- request/response schemas
- auth requirements
- pagination conventions
- error semantics
- timeouts, retries, idempotency
- rate limits and quota semantics (if applicable)
- compatibility expectations (Compatibility Mode is the default)

##### 5.2 Async workflow contracts

- callback/webhook payload schemas
- job envelopes and state machines
- delivery semantics (at-least-once vs best-effort)
- idempotency and dedup rules
- retry/backoff rules and poison-message handling (if applicable)

##### 5.3 Streaming/realtime contracts

- SSE/WS message shapes
- lifecycle rules (connect/heartbeat/reconnect/close)
- ordering guarantees
- backpressure behavior (buffer limits, truncation rules)
- chunk sizing and flush semantics (when relevant to UX)

##### 5.4 Identifier contracts

- permission codes, role identifiers
- feature flags / experiment keys
- error code enumerations
- route IDs when referenced cross-repo (permissions, audit, analytics)

##### 5.5 AI output contracts

- structured output schemas
- normalization rules (defaults, trimming, coercions)
- repair strategy when validation fails (retry, constrained re-prompt, fallback, manual review)
- observability fields required for debugging (e.g., `requestId`, `promptId`, `modelId`)

**MUST:** AI output schemas are contracts. They must be versioned, tested, and monitored like APIs.

##### 5.6 Persistent artifact contracts

If any repo persists artifacts consumed by another repo/process, define contracts for:

- identifier formats (`modelId`, `promptId`, `embeddingModelId`, `jobId`)
- schema versions for stored blobs/documents
- retention/privacy constraints
- replayability expectations (can you recompute outputs from stored inputs?)

**SHOULD:** Treat “model selection” as a backend⇄algo contract, not ad-hoc per consumer.

##### 5.7 Evaluation / scoring contracts (AI success criteria)

Evaluation is a contract. If one repo produces AI outputs and another repo (or pipeline) decides whether outputs are “good,” then the **scoring logic and thresholds** are part of the system contract surface.

Define, version, and test at least:

- **Metric definitions** (what is measured; how it is computed; unit/scale)
- **Pass/fail thresholds** (what “acceptable” means; tiered thresholds if applicable)
- **Sampling policy** (which inputs are evaluated; stratification; edge-case sets)
- **Determinism requirements** (seeds, temperature, tool stubs, fixed retrieval snapshots)
- **Allowed non-determinism** (when stochastic outputs are acceptable and how they are judged)
- **Reporting schema** (how results are emitted and compared over time)

**MUST:** The exact scoring implementation used by CI/`data-evals` MUST be runnable by the `algo` repo locally (same rules, same thresholds), by importing a version-pinned scoring artifact.

Acceptable ways to share scoring contracts:

- **Preferred:** a small “scoring contract” package containing **pure** scoring functions/config and lightweight fixtures (no large datasets).
- **Alternative:** a pinned container image or executable runner whose version is referenced by the contract metadata.

**MUST NOT:** Hide the definition of “success” exclusively inside `data-evals` scripts that other repos cannot run.

#### 6. Contract ownership and governance

##### 6.1 One decision owner per contract

Every contract MUST have exactly one **decision owner**.

Default mapping:

- backend public API → owned by **backend**
- algo/model service API → owned by **algo**
- callback/webhook/event schema → owned by the **producer**
- permission codes / roles → owned by **backend**
- shared system conventions (correlation headers, job envelope, error taxonomy) → owned by a designated **platform owner**

**MUST:** Decision owners MUST be encoded in `CODEOWNERS` (or equivalent review rules).

##### 6.2 Storage vs governance

- `contracts` is canonical storage.
- governance remains with the decision owner.

**MUST:** A contract-change PR MUST include:

- decision owner approval,
- updated fixtures when applicable,
- updated codegen artifacts when applicable,
- explicit change classification and evolution plan (Section 9).

##### 6.3 Producer/consumer responsibilities

- **Producer MUST:** implement the contract, provide compliance tests, document non-schema semantics.
- **Consumer MUST:** tolerate backward-compatible changes and MUST NOT invent undocumented interpretations.

Forward-compatibility guidance:

- **SHOULD:** Consumers ignore unknown fields by default.
- **SHOULD:** Producers do not break consumers by tightening validation without a migration window.

**Security exception:** At internet-facing boundaries, strict decoding MAY be required to prevent request smuggling and unsafe deserialization. If you choose strict decoding, you MUST pair it with explicit versioning/negotiation so forward evolution remains possible.

##### 6.4 Drift prevention

At least one of the following MUST exist per boundary:

- producer-side schema validation tests
- consumer-side decoding tests using fixtures
- end-to-end contract tests in the integration harness

**SHOULD:** Critical boundaries have at least two layers (e.g., producer validation + consumer decoding).

#### 7. Contract representation and tooling

##### 7.1 Canonical formats

Pick formats that support tooling and code generation:

- **OpenAPI 3.x** for REST
- **Protobuf** for gRPC (if used)
- **JSON Schema / AsyncAPI** for events/callbacks/streams
- typed enums/constants for identifiers

**SHOULD:** Avoid “schema in prose only.” If it cannot be validated, it will drift.

##### 7.2 Shared error taxonomy (avoid dependency deadlocks)

Cross-cutting error **definitions** (codes/kinds/fields) SHOULD live in `contracts` so every repo can interpret errors without importing producer implementation modules.

**MUST:** `contracts` defines only portable representations and fixtures. **MUST:** Each repo implements its own exception/error classes and mapping locally.

**MAY:** Publish a tiny, dependency-light generated helper library per language that exports only:

- DTOs/types/interfaces
- schema validators
- predicate helpers (pure functions)
- pure mapping helpers (data-in/data-out)

Helper library constraints:

- **MUST:** Be generated from contract artifacts.
- **MUST:** Be usable without network/persistence I/O.
- **MUST:** Avoid runtime dependencies that risk duplication or dependency cycles.
- **MUST NOT:** Export runtime exception/error classes (e.g., classes extending `Error`/`Exception`).
- **MUST:** If “constructors” are provided, they construct **data representations** (portable error envelopes), not runtime throwables.

##### 7.3 Contract metadata

Each contract artifact SHOULD include machine-readable metadata:

- decision owner
- stability tier (`proposed` / `experimental` / `stable` / `deprecated`)
- evolution mode (Compatibility Mode by default)
- version + changelog pointer
- required checks (fixtures, producer validation, consumer decoding)

**Important:** Contract hub **main** should represent what is safe to rely on in shared environments. Use `proposed`/`experimental` tiers for contracts that are not yet broadly deployed.

##### 7.4 Code generation (strongly recommended)

Hand-written DTOs drift across languages.

**SHOULD:** Generate:

- TypeScript clients/types for frontend
- server-side DTOs/validators/models for backend (where practical)
- Pydantic models (or equivalent) for algo

**MUST:** Generation is reproducible:

- pinned tool versions
- deterministic output
- CI verifies reproducibility

**MUST:** Generated code is not manually edited.

**MUST:** Generated artifacts are clearly separated from hand-written code (path + header markers) so AI agents do not “helpfully refactor” generated output.

##### 7.5 Golden fixtures

For high-impact contracts, store fixtures in `contracts/fixtures/*`:

- request examples
- success responses
- error responses
- stream chunk examples
- callback payload examples

Fixtures MUST be:

- scrubbed of secrets and PII,
- stable (avoid timestamps unless required; use placeholders),
- executed by automated tests.

#### 8. Publishing and consuming contracts

A contract hub only helps if every repo can consume contracts deterministically.

##### 8.1 Versioning policy

**SHOULD:** Version contract artifacts using Semantic Versioning (SemVer):

- **MAJOR**: breaking changes that impact independently deployed producers/consumers (Compatibility Mode).
- **MINOR**: additive backward-compatible changes.
- **PATCH**: clarifications, fixture additions, and bug fixes that do not change compatibility.

**Clarification:** If a contract change is merged but not yet broadly deployable, keep it in `proposed`/`experimental` tier and avoid advertising it as stable capability. Do not “publish stable” contracts that no producer supports.

##### 8.2 Choose one primary consumption mechanism

Pick one primary mechanism; allow exceptions only with explicit documentation.

1. **Versioned package artifacts (recommended)**
  - publish language-specific packages (npm/Maven/PyPI or internal registries)
  - consumers pin a version and upgrade explicitly

1. **Git tag + submodule/subtree**
  - consumers pin a tag/commit

1. **Vendor snapshot (least preferred)**
  - copy generated outputs into each repo
  - acceptable only if automation keeps it synchronized and CI verifies synchronization

**MUST:** Consumers MUST be able to build/test without relying on “latest.” Pin to a version/tag/commit.

##### 8.3 Upgrade cadence

**SHOULD:** Upgrade contracts on a predictable cadence (daily/weekly) or per feature, but keep upgrades small and require compatibility checks.

**MUST:** If a consumer upgrades contracts, it MUST run the required compatibility checks (fixtures decoding and/or integration harness).

#### 9. Contract evolution

Contracts can and should evolve. In multi-repo systems, evolution MUST assume partial upgrades.

##### 9.1 The core constraint

Even inside a single repo, deployments are often rolling; across repos, partial upgrades are the norm.

**MUST:** Treat cross-service contracts as Compatibility Mode unless you have an enforced atomic cutover that prevents mixed versions.

##### 9.2 Change classification

Every contract change MUST be labeled as one of:

- **Additive** (add optional fields/endpoints; widen accepted inputs)
- **Behavioral** (semantics change without a schema change)
- **Breaking** (remove/rename/change meaning/tighten validation)

**MUST:** Behavioral changes require explicit documentation plus fixtures/tests that demonstrate the new behavior.

##### 9.3 Safe evolution patterns (expand/contract)

Use these patterns to avoid deadlocks:

- **Be liberal in what you accept (read), conservative in what you emit (write)**
- **Extend producer first** to accept both old and new forms
- **Update consumers** to send/use the new form
- **Remove old behavior** only after a measurable adoption window

##### 9.4 Ordering depends on direction

**Correction:** “Contract-first” is a design discipline, not a mandate to publish a new stable contract version before any implementation exists.

Recommended practical ordering (Compatibility Mode):

- **Additive response fields (producer → consumer):**
  1. producer starts emitting the field (optional),
  1. contract/fixtures updated and released,
  1. consumers start using it.

- **Additive request fields (consumer → producer):**
  1. producer becomes tolerant and/or implements new behavior behind a feature flag,
  1. contract/fixtures updated and released,
  1. consumers start sending the field.

- **New endpoint/topic:**
  1. producer implements and deploys,
  1. contract/fixtures released,
  1. consumers integrate.

- **Breaking change:**
  - MUST follow expand/contract with a compatibility window (dual-read/dual-write or versioned surface).

##### 9.5 Compatibility strategies

For breaking changes in Compatibility Mode, provide an explicit strategy:

- versioned surface (`/v2`, versioned topics, or `schemaVersion`)
- content negotiation (headers)
- dual-read/dual-write within a defined window

The strategy MUST include:

- a cutoff (date/release),
- fixtures/tests for both old and new,
- a migration plan for stored data (if applicable).

#### 10. Internal modularization: keep each repo AI-sized

Multi-repo boundaries keep cross-repo work bounded. Each repo still needs internal boundaries.

##### 10.1 Frontend

**SHOULD:** Use a single-deploy modular structure (app shell + internal packages with strict dependency rules).

##### 10.2 Backend

**SHOULD:** Use a modular monolith:

- one deployable backend unless a runtime split is justified
- domain modules with explicit boundaries
- enforced import rules
- “ports and adapters” for side-effectful integrations

**MUST:** Backend owns canonical validation and canonical error mapping.

##### 10.3 Algo/model service

**SHOULD:** Structure for bounded AI edits:

- `adapters/` (decode/encode, schema validation, mapping)
- `pipelines/` (prompt pipelines and orchestration)
- `prompts/` (versioned prompts, prompt IDs)
- `tools/` (tool adapters with strict allowlists and quotas)
- `evals/` (fast deterministic checks + offline eval hooks)

**MUST:** Validate outputs at the boundary before emitting responses/callbacks.

**MUST:** Record `requestId`, `promptId`, and `modelId` (or equivalent) in logs for every user-visible output.

#### 11. Integration harness: the system truth source

**SHOULD:** Maintain an integration harness (repo or pipeline) that provides:

- one-command local startup (compose)
- smoke tests for critical end-to-end flows
- contract compatibility runners using fixtures

**MUST:** Any cross-repo contract change must be verifiable via:

- the integration harness (preferred), or
- fixture-based compatibility checks that the harness runs.

**SHOULD:** For independently deployed systems, maintain a compatibility matrix (producer version × consumer version) for at least the supported window.

#### 12. AI-assisted development workflow

##### 12.1 AI task template (MUST)

Every AI task MUST include:

1. **Repo scope**
  - which repo(s) may change
  - which folders are in scope
  - explicit exclusions

1. **Contract references**
  - impacted specs + fixtures
  - invariants that must remain stable
  - change classification (additive/behavioral/breaking)
  - evolution mode (Compatibility Mode unless proven otherwise)

1. **Determinism & replay**
  - determinism tier (`tier0`/`tier1`/`tier2`) and what must be deterministic
  - required replay harness / golden fixtures (if Tier 0/Tier 1)
  - pinned DatasetManifest(s) for any eval gates

1. **Budgets**
  - what budgets are enforced/changed (tokens, time, external calls, cost)
  - budget scope (stage/tool/pipeline) and termination behavior

1. **Acceptance criteria / verification**
  - exact commands to run (lint/typecheck/test/build/eval/replay)
  - required artifacts (updated spec/fixtures, regenerated code)
  - smoke flow expectations

1. **Non-goals**
  - forbid opportunistic refactors
  - forbid renaming public identifiers
  - forbid dependency upgrades unless requested

##### 12.2 Change sequencing across repos

**SHOULD:** For cross-repo work, use a “contract PR” plus per-repo implementation PRs.

**MUST:** Do not merge consumer changes that depend on non-deployed producer behavior unless:

- the consumer is tolerant (feature-flagged, default-off), and
- there is a defined rollout plan.

##### 12.3 Keep AI changes small and reversible

**SHOULD:**

- prefer many small PRs over one large PR
- ensure each PR is mergeable and releasable
- avoid long-lived branches where contracts drift

**MUST:** If a PR changes a contract, it MUST also change at least one automated check proving enforcement (fixture/test/codegen output).

##### 12.4 AI guardrails for cross-repo work

**MUST:** For any task that touches more than one repo, require:

- integration harness run (or fixture-based compatibility run),
- explicit contract version pin updates,
- documented rollout/compatibility plan if breaking behavior is introduced.

#### 13. Efficiency and overhead management

Splitting into multiple repos can increase development overhead if unmanaged.

##### 13.1 Typical regressions

- coordination overhead (version bumps)
- fragmented CI feedback loops
- contract drift due to ad-hoc upgrades
- duplicated tooling/config
- slower onboarding (more moving pieces)

##### 13.2 Mitigations

**SHOULD:**

- automate contract publish + consumer upgrade PRs (bot-opened PRs)
- keep one integration harness with smoke tests and version pins
- standardize repo interfaces (Section 15)
- keep runtime services minimal
- cache CI builds/tests aggressively

#### 14. Reliability and security patterns for AI workloads

##### 14.1 Prefer backend-orchestrated model calls

Prefer:

- frontend → backend
- backend → algo
- backend returns canonical responses

Direct frontend → algo calls MAY be acceptable for prototyping or trusted intranet deployments, but increase attack surface and contract complexity.

##### 14.2 Long-running operations

Use explicit job patterns when work exceeds interactive budgets:

- job creation → status polling/stream → completion
- best-effort cancellation
- idempotency keys for dedup

##### 14.3 Idempotency and retries

**MUST:** Any boundary that can be retried defines:

- idempotency keys
- dedup behavior
- safe retry classification

##### 14.4 Output validation and repair

**MUST:** Model outputs are validated against schemas before:

- persisting to the system of record,
- triggering side effects,
- showing user-visible results (unless explicitly marked “draft/unverified”).

If validation fails:

- retry with constrained prompts where safe,
- fall back to partial/manual flow where required,
- log and surface the failure with correlation IDs.

##### 14.5 Security and secrets

**MUST:**

- no secrets in git (keys, tokens, private URLs)
- secrets are injected via secret managers or environment variables
- run secret scanning in CI

**SHOULD:** Treat prompt templates, tool configurations, and retrieval sources as security-sensitive.

##### 14.6 Observability and correlation

**SHOULD:** Propagate correlation identifiers across:

- frontend request headers,
- backend logs and traces,
- algo logs,
- callbacks/webhooks.

**MUST:** Every cross-repo request/response includes a `requestId` (or equivalent) that can be traced end-to-end.

#### 15. Repo interface standard (AI-friendly)

To use AI coding efficiently across repos, each repo MUST expose a small, stable interface for verification and developer workflows.

##### 15.1 One canonical “verify” entrypoint

**MUST:** Every repo provides a single canonical entrypoint to validate changes deterministically, e.g.:

- `make verify`
- `task verify`
- `pnpm verify`
- `./scripts/verify.sh`

**MUST:** `verify` runs the repo’s relevant gates and fails fast.

**SHOULD:** `verify` runs without requiring external network access (or uses documented local stubs) so AI agents can iterate deterministically.

##### 15.2 Minimal gates by repo type

Each repo type SHOULD implement these gates (or a documented equivalent):

- **contracts**: schema/spec validation + fixture decoding tests + reproducible codegen
- **frontend**: lint + typecheck + tests + production build (and SHOULD include at least one browser-level `smoke-ui` scenario for critical workflows when a user-facing UI exists)
- **backend**: tests + build/package + static analysis where standard
- **algo**: boundary checks (graph enforcement) + unit tests for core transforms + deterministic CI eval suite (pinned DatasetManifest split) + replay verification for Tier 0 pipelines + lint/type checks
- **integration**: `up/down` + `smoke` + compatibility runners
- **data-evals**: `eval` (small representative set) + deterministic `report`

**MUST:** If a gate is “not applicable,” document why and what replaces it.

##### 15.3 Required documentation files

Each repo SHOULD contain:

- `README.md` (how to run; canonical commands; env vars)
- `ARCHITECTURE.md` (module boundaries; key flows; where contracts are enforced)
- `CONTRACTS.md` (which contracts it produces/consumes; version pins)
- `UI_SPEC.md` (for repos that ship user-facing UI: screen inventory, workflow→screen mapping, interaction edge cases, and links/exports to design prototypes)
- `RUNBOOK.md` (optional; operational notes; common failures)

##### 15.4 Environment variable contract

Each repo MUST provide:

- an `.env.example` (or equivalent)
- a clear policy for secret injection

#### 16. Minimum CI gates

##### 16.1 Per-repo minimum

Every repo MUST have CI that runs its `verify` entrypoint.

**SHOULD:** CI output is stable and machine-readable so AI agents can use it as feedback.

##### 16.2 System-level gates

At least one pipeline (often in `integration`) MUST provide:

- end-to-end smoke tests
- breaking-change detection for APIs/events (spec diffs)
- fixture decoding tests for consumers

##### 16.3 AI behavior gates (when applicable)

If model outputs affect users, you SHOULD add at least one of:

- schema compliance rate checks
- a small offline eval set with pass/fail thresholds
- latency budget checks for critical pipelines
- regression detection for “repair rate”

> Note: In the source document, the following sections were labeled “Appendix A-D”. In the unified standard, they are labeled “Annex E-A-E-D” to avoid collisions with the standard’s top-level Appendices.

#### Annex E-A - “Split into a new repo?” checklist

Split into a new repo only if all are true:

- the boundary has a clear contract
- the contract can be tested automatically
- there is independent ownership/deployment need OR language/runtime mismatch
- the split materially reduces AI task scope
- an integration harness exists to catch drift

If not, prefer modularizing inside an existing repo.

#### Annex E-B - Contract change checklist

Every contract change PR SHOULD include:

- updated spec/schema
- updated fixtures (happy path + common failure)
- change classification and compatibility plan
- producer implementation + tests (or a staged rollout plan)
- consumer updates if required (or explicit compatibility window plan)
- integration smoke test update for critical boundaries
- version bump (SemVer) + changelog entry

#### Annex E-C - AI ticket checklist (copy/paste)

1. Scope: repo(s) + folders + explicit exclusions
1. Contracts: spec paths + fixture names + invariants + evolution mode
1. Deliverables: code + tests + fixtures + regenerated clients
1. Verification: exact commands to run + smoke flow
1. Non-goals: no refactors, no renames, no dependency upgrades

#### Annex E-D - Minimal contract hub layout (example)

A practical `contracts` repo layout:

```
contracts/
  openapi/
    public-api.yaml
    algo-api.yaml
  schemas/
    errors.schema.json
    job-envelope.schema.json
    stream-message.schema.json
  fixtures/
    public-api/
      entity.create.request.json
      entity.create.response.json
      error.401.json
    algo/
      outline.request.json
      outline.response.json
      stream.chunk.json
  codegen/
    openapi-generator.json
    ts/
    java/
    python/
  scripts/
    validate.sh
    generate.sh
    test-fixtures.sh
```

**SHOULD:** Keep `contracts` dependency-light. It should be a “lowest layer” repo that is safe for every other repo to consume.

## Appendix F - SDMM refactoring & migration playbook (safe change patterns)

This appendix provides the “how” for large refactors and migrations in SDMM systems. It is intentionally **implementation-oriented** and is meant to be used as a checklist during risky change windows.

### F.1 When this playbook is required

Use this playbook for changes that are any of:

- A breaking change to a **persisted** or cross-repo contract (Compatibility Mode).
- A refactor that touches multiple SDMM modules with non-trivial coupling.
- A major algorithm change that can regress quality or cost materially.
- A migration that replaces an adapter (I/O boundary) or prompt policy in production.

### F.2 Core rule: preserve one stable seam at a time

Large migrations fail when multiple seams move simultaneously.

- **MUST:** Keep at least one stable seam (contract, adapter interface, pipeline entrypoint) unchanged while migrating others.
- **SHOULD:** Prefer “expand/contract” over “flag day” changes for anything observed externally.

### F.3 Branch-by-abstraction (recommended default)

Use when replacing an implementation behind a stable interface.

1. Introduce an interface (port) in `core/` (or a stable module).
1. Keep the existing implementation as `OldImpl`.
1. Add the new implementation as `NewImpl`.
1. Switch wiring in the composition root (`pipelines/` or `integration/`) behind a flag/config.
1. Remove `OldImpl` only after metrics and eval gates pass.

### F.4 Expand / Contract (for contract changes)

Use when changing a contract consumed by other modules/repos.

**Expand phase**

- Add new fields as optional (tolerant readers).
- Dual-write (produce both old + new) if needed.
- Add compatibility adapters.

**Contract phase**

- After consumers migrate, stop emitting old fields.
- Then remove parsing/handling of the old fields.

### F.5 Shadow mode / parallel run (for algorithms)

Use when validating a new pipeline without affecting users.

- Run the new pipeline in `dryRun` or `sandbox` sideEffectsMode.
- Compare outputs to the current pipeline using the same inputs.
- Record diffs, quality metrics, and budget deltas.
- Gate promotion on:
  - quality thresholds (EvalReport),
  - budget deltas within policy,
  - and failure-mode parity.

### F.6 Golden fixtures + replay harness (mandatory for Tier 0/Tier 1 pipelines)

Maintain a **deterministic verification path** for the pipeline using a small set of **golden inputs**.

- Maintain a small set of **golden inputs** with expected outputs (or expected invariants / tolerances).
- Provide a **replay harness** that can run the pipeline against those inputs in CI with stable results:
  - **Tier 0:** the harness MUST be fully offline/deterministic (no live network). Record tool/LLM transcripts (“cassettes”) as needed.
  - **Tier 1:** the harness MUST be replayable given **pinned dependencies** (pinned model/tool versions, pinned datasets). Prefer recorded transcripts or stubbed responses over live calls.
- Prefer **invariant-based** checks (schemas, required fields, bounded score thresholds, citation integrity) over brittle full-string equality whenever feasible.
- Run the replay harness in CI to prevent regressions. Whether it gates every PR or runs in a `--full`/nightly tier depends on the project’s profile (§2.3) and CI policy (§10.3). When a replay suite is configured as a merge gate, failures MUST block merges.

### F.7 Prompt migrations (prompt policy as a contract)

Treat prompt changes like code changes:

- Pin prompt template versions.
- Track prompt policy in the RunManifest (`configHash`).
- Use eval gates for any prompt material change.
- Avoid mixing prompt and adapter changes in one release.

### F.8 Adapter migrations (I/O boundary)

Adapters are high-risk because they are where side effects occur.

- Migrate adapters behind a stable port.
- Ensure `sideEffectsMode` checks are preserved.
- Add explicit integration tests for “no writes in dryRun”.

### F.9 Cutover checklist (minimum)

Before enabling the new path in production:

- Boundary lints pass (no deep imports; graph enforced).
- CI eval gates pass on pinned datasets.
- Replay harness passes (if Tier 0/Tier 1).
- Observability is in place (jobId/runId/manifestHash).
- Rollback path is documented and tested.
- The Master Doc traceability index is updated (§9 / Appendix C).

## Appendix G - AI Product Engineering Principles Addendum

> **Appendix G note:** This appendix is included as a deep-dive reference; if any statement here conflicts with the Main Body, the Main Body wins per §2.1.

### AI Product Engineering Principles Addendum

Scope: Addendum to the unified standard, especially §4 (contracts), §6 (SDMM frontend), and §7 (SDMM algorithm). This document defines additional principles for:

- Backend / System of Record (SoR) & Orchestrator engineering
- Integration harness and system testing
- Data & evaluations governance
- Platform/release operations plus security & privacy (combined)

#### 0. Normative language (Appendix G)

This addendum uses **BCP 14** requirement keywords (RFC 2119 + RFC 8174).

- The primary normative keywords used in this addendum are: **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**.
- If synonymous terms appear (e.g., **REQUIRED**, **SHALL**, **SHALL NOT**, **RECOMMENDED**, **OPTIONAL**), they MUST be interpreted as the corresponding BCP 14 keyword; authors SHOULD prefer the primary keywords above for clarity.
- Lowercase forms (“must”, “should”, etc.) are non-normative unless explicitly marked.

Interpretation guidance:

- **MUST / MUST NOT**: required for correctness, safe evolution, security, privacy, or drift prevention.
- **SHOULD / SHOULD NOT**: strongly recommended; deviation requires explicit justification and compensating controls.
- **MAY**: optional.

Document structure:

- **Chapter 1:** Backend (System of Record) & Orchestrator Engineering Principles
- **Chapter 2:** Integration Harness & System Testing Principles
- **Chapter 3:** Data & Evals Governance Principles
- **Chapter 4:** Platform, Release, Security & Privacy Principles (combined)
- **Annexes:** lightweight checklists and minimal templates

Note: Unless a checklist item uses normative keywords (**MUST/SHOULD/MAY**), annexes are intended as **informative** guidance.

#### 0.1 Document precedence

This addendum is **supplemental**. It does not override higher-priority standards or organizational policies.

Unless explicitly stated otherwise, use this precedence order:

1. **Security/compliance policies and applicable law/regulation**
1. **Project-wide engineering standard** (repo boundaries, contracts, evolution modes, contract hub governance)
1. **Component and surface-specific principles** (where applicable)
  - SDMM frontend principles (frontend internal modularization)
  - Algorithm project principles (algo/model service)
  - This addendum (backend/orchestration, integration harness and system testing, data & evals governance, platform/release + security/privacy operationalization)
1. **Repo- and service-specific standards**
  - they MAY be stricter than this addendum, but MUST NOT weaken higher-priority requirements
1. **Team conventions** (lowest priority)

Scope clarification:

- If a requirement is scoped to a single component, apply that component’s principles to that component.
- If a requirement governs a boundary between components (contracts, identifiers, job envelopes, correlation IDs), treat it as a contract surface and follow the **project-wide contract governance** (and any higher-precedence security/compliance policy). If multiple documents define the same boundary rule, the higher-precedence document governs.

If requirements conflict, the higher-priority item governs.

Exception handling:

- **Deviations from SHOULD/SHOULD NOT:** MUST be documented with justification and compensating controls.
- **Exceptions to MUST/MUST NOT (rare):**
  - MUST be explicitly approved by the appropriate owner (security/compliance where applicable).
  - MUST be documented as an exception record (scope, duration, rationale, compensating controls).
  - MUST include a sunset plan.
- **Policy/law:** exceptions MUST NOT violate applicable law/regulation or organizational security/compliance policy.

#### 0.2 Relationship to the existing standards

This addendum complements (and does not replace) the unified standard’s core rules. In this unified document, the related material lives in:

- **Contracts and evolution**: §4 (Canonical contracts) and §10 (Verification and CI gates), with Appendix E as a deep-dive reference.
- **SDMM modularization**: §5 (SDMM core principles), §6 (SDMM Frontend Track), and §7 (SDMM Algorithm Track).
- This addendum (Appendix G) focuses on AI-product-specific principles for backend orchestration and algorithm execution artifacts.

#### 0.3 Key definitions

- **System of record (SoR)**: the backend component that owns authoritative state and persistence.
- **Orchestrator**: backend logic that coordinates workflows across modules/services (including long-running AI jobs), enforcing canonical rules, budgets, retries, and state transitions.
- **Contract hub**: canonical storage for cross-repo contract artifacts, including:
  - schemas/specs (OpenAPI/JSON Schema/etc.),
  - non-schema semantics (documented invariants and rules),
  - fixtures/examples (happy-path and representative failures),
  - executable checks (producer validation and/or consumer decoding tests),
  - identifier enums/constants (error codes, job types, permission codes, feature flags),
  - codegen configuration/templates (when applicable).
- **Contract**: anything two independently built units need to agree on. A complete contract includes:
  1. **Schema** (machine-checkable shape),
  1. **Semantics** (behavioral rules/invariants),
  1. **Examples/fixtures** (known-good and representative failures),
  1. **Executable checks** (producer validation and/or consumer decoding tests).
- **Contract artifact**: the machine-checkable representation of a contract (spec/schema/types/constants/fixtures/codegen config) stored in the contract hub.
- **Decision owner**: the single party that defines contract semantics and approves changes to that contract.
- **Integration harness**: a runnable environment plus tests that exercise end-to-end flows and cross-repo compatibility (the executable “system truth”).
- **Environment**: a deployment/execution context such as local, CI, staging, production (and sub-modes such as canary, shadow, benchmark).
- **Artifact (stored)**: a persisted blob/document referenced by ID/URI (inputs, outputs, attachments, logs, or cached generations). Artifacts may inherit sensitivity from their source data and are governed by retention/deletion rules.
- **Fixture**: a stored example payload or dataset sample used by automated checks.
- **Evaluation (eval)**: a process that determines whether outputs are acceptable (metrics, thresholds, rubrics, regression gates).
- **Determinism tier**: a declared reproducibility level used to set expectations for tests and comparisons.
- **PII**: personally identifiable information; treat as sensitive by default.
- **Raw user content**: unredacted end-user-provided or end-user-generated content (text, files, images, audio), including prompts and model outputs. Treat as sensitive by default.
- **Sensitive data**: any data that requires heightened handling (including PII, credentials/secrets, regulated data, proprietary business data, and raw user content).
Treat as sensitive by default unless classified otherwise.

- **Derived data / derived artifacts**: outputs computed from other data (embeddings, indexes, cached generations, logs, analytics events). Derived artifacts may inherit sensitivity; retention/deletion obligations apply to derived artifacts as well.
- **Secret**: authentication or encryption material (API keys, tokens, passwords, private keys, signing material).
- **SLO**: service-level objective; a target level of reliability/performance for a user-visible operation.
- **SBOM**: software bill of materials; a machine-readable inventory of components in a build artifact.
- **Stability tier**: a classification for contract/config surfaces (`proposed`, `experimental`, `stable`, `deprecated`) that defines what downstream code is allowed to rely on (as defined in the project-wide standard).
- **Profile**: a named configuration bundle selecting defaults (budgets, thresholds, feature flags) for a runtime context (e.g., `prod`, `staging`, `debug`, `shadow`, `benchmark`).
- **Config ID (`configId`)**: an immutable identifier for a specific configuration snapshot/version applied at runtime. A `profileId` selects a named context (e.g., `prod`); a `configId` identifies the exact config version used for reproducibility and rollback.
- **Hard budget**: a budget limit that stops work when reached to prevent further cost and side effects (typically emits `budget.exhausted` diagnostics and forces a terminal job outcome).
- **Soft budget**: a budget threshold that may be exceeded, but is still recorded for governance and alerting (typically emits `budget.exceeded` diagnostics/metrics).
- **Module (backend)**: an internally enforced unit of ownership and encapsulation (package/namespace) with a declared public API surface.

#### 0.4 Evolution mode reminders

- **Compatibility Mode (default across repos/services):** mixed versions across a boundary are observable; breaking changes require a compatibility strategy and window.
- **Refactor Mode (only within a single deployable artifact or enforced atomic cutover):** mixed versions cannot be observed across the boundary.

This addendum assumes Compatibility Mode for all cross-repo, cross-service, and external-facing contracts unless you can prove Refactor Mode is enforceable.

#### Chapter 1 - Backend (System of Record) & Orchestrator Engineering Principles

##### 1.1 Purpose

The backend is the system of record and primary orchestrator. Its role is to:

- hold canonical state and enforce invariants
- provide stable APIs, contracts, and error semantics
- orchestrate long-running workflows (especially AI compute) with idempotency, retries, budgets, and observability
- enforce authn/authz and auditability
- protect the system from untrusted inputs (including model outputs and external integrations)

##### 1.2 Architectural posture

**B1 - Prefer a modular monolith for the backend**

- **SHOULD:** Ship the backend as a single deployable artifact unless a runtime split is operationally justified.
Acceptable justification examples include security isolation, independent scaling, independent deploy/rollback, and regulatory partitioning.

- **MUST NOT:** Split runtime services purely to make code “AI-sized” or to avoid enforcing internal boundaries. Prefer internal modularization and contract discipline; only introduce new runtime services when there is a clear operational justification.
- **MUST:** Modularity MUST be enforced via real module boundaries (not “folders only”).
- **MUST:** Cross-module imports MUST go through the module’s declared public API surface (no deep imports into internal paths/symbols).
- **SHOULD:** Enforce module boundaries mechanically (lint/import rules/build system), not by convention.

**B2 - Ports & adapters, not “shared utils soup”**

- **MUST:** Side-effectful code (DB, network calls, queues, storage, clocks, randomness sources) MUST be isolated behind adapters.
- **SHOULD:** Core domain logic SHOULD be deterministic and testable without infrastructure; inject time and randomness when needed.
- **MUST NOT:** Promote ad-hoc helper functions across modules without ownership; cross-cutting concerns MUST have a single owner module.

**B3 - Backend owns canonical state transitions**

- **MUST:** State-changing operations MUST be validated and applied in the backend (the SoR).
Frontend and algo services MAY perform optimistic/local validation, but MUST NOT be the authority for canonical state.

- **MUST:** Canonical state transitions MUST be committed transactionally with invariant checks before any external side effects are emitted (events, callbacks, emails, third-party calls).
When side effects are driven from persisted state, use a transactional pattern (e.g., outbox) to avoid “write succeeded, publish failed” inconsistencies.

- **SHOULD:** Invariants that span entities/modules SHOULD be enforced in one place (the SoR boundary), not duplicated across consumers.

##### 1.3 API contract discipline

**B4 - Canonical validation and canonical error mapping live in the backend**

- **MUST:** Validate and normalize all untrusted inputs at boundaries (HTTP requests, webhooks, files, events, callbacks).
- **MUST:** Publish contract artifacts for externally consumed surfaces via the contract hub (or equivalent). At minimum, each contract MUST include schema + semantics + fixtures + executable checks.
- **SHOULD:** Contract artifacts SHOULD include machine-readable metadata (decision owner, stability tier, evolution mode, version/changelog pointer).
This supports automated governance and safe cross-repo evolution.

- **MUST:** Provide canonical error mapping (stable error envelope + stable error codes); MUST NOT leak raw infrastructure/library errors as a public contract.
- **MUST:** Error codes MUST be centrally governed as stable identifier contracts (enums/constants) and versioned in the contract hub.
- **SHOULD:** Error envelopes SHOULD include a correlation identifier (e.g., `requestId`) and a retryability classification where safe.
- **SHOULD:** Validation failures SHOULD be diagnosable (field paths, codes) without exposing sensitive internals.

**B5 - API semantics are part of the contract** For any externally consumed endpoint/event:

- **MUST:** Define non-schema semantics explicitly: idempotency, pagination, timeouts, retryability, ordering guarantees, partial-success behavior, and rate-limit semantics.
- **MUST:** Declare timeout and cancellation behavior for interactive endpoints and job-creation endpoints (including when cancellation is best-effort only).
- **SHOULD:** Maintain fixtures for success and representative failure paths and exercise them in automated checks.

**B6 - Idempotency is mandatory for retryable writes**

- **MUST:** Any state-changing endpoint or message handler that can be retried (client retries, gateway retries, queue redelivery, job reprocessing) MUST be idempotent within a documented deduplication window.
- **MUST:** The deduplication window MUST cover the maximum end-to-end retry/redelivery window for that operation (client retries, gateway retries, and queue redelivery), or the system MUST ensure that retries cannot occur beyond the deduplication window.
- **MUST:** The idempotency strategy MUST specify:
  - key source and lifetime (generation + TTL),
  - deduplication scope (per tenant/user, per resource, or global),
  - canonical request normalization used for comparison (and whether a request hash is stored),
  - conflict policy (same key, different semantic request),
  - response replay semantics (return original outcome vs safe recompute that cannot duplicate side effects),
  - storage policy (what is stored to enable replay; retention window; sensitivity classification and encryption requirements).
- **MUST:** If retries are possible and there is no safe implicit idempotency (for example, a `POST` that creates a new resource with a server-generated ID or triggers an external side effect), the backend MUST require an explicit idempotency key and MUST reject missing/invalid keys with a stable, documented error code.
- **MUST:** Idempotency MUST cover externally visible side effects. If an operation triggers third-party calls, emails, payments, or event emissions that cannot duplicate, the idempotency strategy MUST include an external deduplication mechanism (e.g., propagate the idempotency key downstream, persist third-party request IDs, or drive side effects from an outbox/worker keyed by the idempotency record).
If no safe deduplication is possible, the operation MUST be classified as **non-retryable** and automatic retries MUST be prevented at every layer (client, gateway, queue, and worker).

- **MUST:** Conflict behavior MUST be deterministic and documented (including the error envelope/code returned on conflict).
- **SHOULD:** Prefer storing a hash of the normalized request (and minimal replay metadata) instead of raw request bodies; if raw bodies are stored, treat them as sensitive artifacts (access controlled, retained minimally, encrypted at rest where required).
- **SHOULD:** Standardize idempotency key transport (header/field) across clients and services so retries, support tooling, and logs are consistent.
- **MUST:** Idempotency keys MUST be treated as opaque identifiers. They MUST NOT encode secrets or PII, and MUST NOT be logged in full (log a hash/truncated form if needed).
- **MUST NOT:** Idempotency keys MUST NOT be used as metric label dimensions or analytics identifiers (high-cardinality and sensitive). If observability requires correlation, log only a hash/truncated form and prefer request/job correlation IDs.
- **MUST:** If operator tooling can replay/requeue work beyond the deduplication window, it MUST either (a) require a new idempotency key/job ID and treat the replay as a new operation, or (b) retain deduplication records for the full replay window.
- **SHOULD:** Scope idempotency keys by operation (`operationName`/endpoint/jobType) to prevent cross-operation collisions.

**B7 - Treat model output as untrusted input**

- **MUST:** Any AI/model output used for state changes MUST be validated against a schema and normalized before persistence or side effects.
- **MUST:** Repair steps (re-prompt, constrained decode, fallback, manual review) MUST be budgeted, observable, and safely bounded.
- **MUST:** Model/prompt/config identifiers used for debugging and rollout MUST be stable and treated as identifier contracts.
- **SHOULD:** Persist or emit sufficient diagnostics to reproduce failures without storing raw sensitive content by default.
Minimum recommended fields: requestId/traceId, modelId, prompt/config IDs, schema/contract version, budget outcomes.

##### 1.4 Orchestration and long-running jobs

**B8 - Use explicit job envelopes and state machines**

- **MUST:** Long-running operations MUST be modeled as explicit jobs with a stable job envelope that includes at least:
  - `jobId`
  - `jobType` (stable enum / identifier contract)
  - `schemaVersion` (or equivalent) for the job envelope
  - `status` (stable enum)
  - `createdAt` / `updatedAt`
  - attempt counters and retry/backoff metadata
  - `profileId` / `configId` (or equivalent) identifying the runtime configuration bundle used for this job (for reproducibility and rollback)
  - declared budgets and a budget consumption summary (at least the limiting budget and whether it was hard/soft)
  - references to primary input/output artifacts (IDs/URIs) rather than embedding raw sensitive content in the envelope
  - typed error/diagnostics representation (stable codes + structured fields)
  - correlation IDs linking back to the initiating request
- **SHOULD:** Job envelopes SHOULD be safe to store and inspect broadly (e.g., in logs/support tooling). Avoid embedding raw user content; prefer references plus access-controlled artifact stores.
- **MUST:** Job transitions MUST be idempotent and MUST follow a defined state machine.
- **MUST:** Terminal states MUST NOT transition back to non-terminal states (no “time travel” from `succeeded` → `running`).
- **SHOULD:** Keep the `status` enum small and explicit. A recommended baseline is: `queued`, `running`, `succeeded`, `failed`, `degraded`, `cancelled` (with allowed transitions documented).
- **SHOULD:** Job envelope schema, enums, and examples SHOULD be stored and versioned in the contract hub.

**B8.1 - Embed the algorithm Pipeline Result without lossy mapping (required)**

When a backend “job” is executing an SDMM/Algo pipeline, the JobEnvelope MUST embed the full algorithm **PipelineResult** for **each attempt** (not just a flattened status), without lossy translation.

Canonical structure (matches §4.4.6):

- `status` (job lifecycle): `queued → running → {succeeded | degraded | failed | cancelled}`
- `runs[]` (attempts): each run includes:
  - `manifestRef` (pointer to RunManifest)
  - `result` (algorithm outcome): `PipelineResult<T>` with `status ∈ {ok | degraded | error}`

**Terminal status mapping (recommended)**

Apply this mapping **only when the job is terminal** (no further retries will be scheduled, or the job was explicitly cancelled). The orchestrator MUST NOT infer terminality from `runs[-1]` alone; it MUST consider retry policy (`attempt.count` vs `attempt.max`) and cancellation state.

- If terminal and `runs[-1].result.status = ok` → `job.status = succeeded`
- If terminal and `runs[-1].result.status = degraded` → `job.status = degraded`
- If terminal and `runs[-1].result.status = error` → `job.status = failed`
- If the job is explicitly cancelled → `job.status = cancelled` (even if the last run result is absent)

If `runs[-1].result.status = error` but retries remain, `job.status` SHOULD remain `queued` (waiting to retry) or `running` (retry in progress), depending on the orchestrator state machine.

**Error and diagnostics conventions**

- Failures MUST use a shared `NormalizedError` shape (stable `code`, `kind`, and `retryable`) under `runs[].result.error`.
- Structured non-fatal signals SHOULD use a shared `Diagnostics` shape under `runs[].result.diagnostics` and/or a job-level `diagnostics` summary:
  - `codes?: string[]`
  - `kv?: { [key: string]: scalar }`
  - `counters?: { [key: string]: number }`
  - `notes?: string[]`

Note: Some systems add a derived convenience field like `job.result` that mirrors the latest run’s result. If present, it MUST be identical to `runs[-1].result` and MUST NOT be treated as the canonical source of truth.

This avoids schema drift between “algo output” and “backend envelope” and preserves replay/debuggability.

**B9 - Retry policy is bounded, safe, and observable**

- **MUST:** Define retry classification (retryable vs non-retryable) per stage.
- **MUST:** Retries MUST be bounded (attempts, elapsed time) and use backoff with jitter.
- **MUST:** Provide poison-message handling for queue redelivery (dead-letter, quarantine, or explicit terminal state).
- **SHOULD:** Prefer at-least-once delivery + idempotency over best-effort retries without dedup.
- **SHOULD:** When producing events/callbacks from persisted state, use a transactional pattern (e.g., outbox) to avoid “write succeeded, publish failed” inconsistencies.

**B10 - Cancellation, budgets, and backpressure**

- **SHOULD:** Support best-effort cancellation for long jobs and propagate cancellation downstream when safe.
- **MUST:** Each job type MUST define explicit budgets (time, steps/iterations, external calls, and cost where applicable).
  - Budgets MUST be classified as **hard** or **soft**:
    - **Hard budget:** reaching the limit MUST stop further work and MUST prevent additional side effects. The job MUST transition to a terminal outcome and MUST emit a stable diagnostic code (e.g., `budget.exhausted`) indicating which budget triggered. If a partial/best-effort result is safe to return, the outcome MUST be `degraded`; otherwise it MUST be `failed`.
    - **Soft budget:** exceeding the limit MAY allow the job to continue, but MUST emit a stable diagnostic code or metric (e.g., `budget.exceeded`) for cost governance. Soft budgets MUST be explicitly documented per job type/stage/profile (including rationale, owner, and rollback/sunset plan), and SHOULD be used only when a hard cutoff would cause worse outcomes or when spend can only be estimated until completion.
- **MUST:** Budget limits and consumption (or, at minimum, the limiting budget and its classification) MUST be recorded in the job envelope and emitted in metrics so cost regressions are observable and replayability is possible.
- **SHOULD:** Budget checks SHOULD be performed in-loop and at stage boundaries (not only at the end).
- **MUST:** Define concurrency and queue backpressure limits (max in-flight jobs, max queue depth policy) and expose them via metrics.
- **SHOULD:** Backpressure behavior SHOULD be explicit (reject, shed load, queue, or degrade).
- **MUST:** Backpressure behavior MUST be observable (metrics/logs/traces).

##### 1.5 Persistence and migrations

**B11 - Expand/contract migrations are the default**

- **MUST:** Schema changes MUST be backward compatible across rolling deploys (expand → migrate/backfill/dual-write → contract).
- **MUST:** Migrations MUST be automated, repeatable, and safe to re-run.
- **SHOULD:** Avoid production-impacting locks; when unavoidable, require explicit review and a rollout plan.
- **SHOULD:** Treat index changes as migrations with operational impact (build times, lock behavior) and plan accordingly.

**B12 - Stored artifacts are contracts**

- **MUST:** If the backend persists artifacts consumed outside the backend (documents/blobs/job outputs), version the stored schema (explicit version field or versioned namespace).
- **MUST:** Define retention and deletion rules, including handling for sensitive content and derived artifacts.
- **MUST:** For artifacts classified as sensitive, encryption-at-rest MUST be enabled (or an explicit documented exception approved by the appropriate owner).
- **SHOULD:** Define key ownership and rotation expectations for encrypted artifacts.

##### 1.6 Authn/authz and audit

**B13 - Auth enforcement is non-negotiable**

- **MUST:** Enforce authorization at the system-of-record boundary; frontend checks are not sufficient.
- **MUST:** Permission/role identifiers MUST be stable, centrally governed, and treated as identifier contracts.
- **SHOULD:** Authorization decisions SHOULD be auditable (who did what, when, which permission/policy version).

**B14 - Audit logs are part of the operational contract**

- **SHOULD:** For high-risk actions, emit audit events with actor, resource, action, outcome, and correlation IDs.
- **MUST:** Audit logs MUST avoid raw sensitive payloads unless explicitly required and protected with strict access controls.

##### 1.7 Observability and operability

**B15 - End-to-end traceability**

- **MUST:** Propagate correlation IDs across frontend → backend → algo and async callbacks.
- **MUST:** Emit structured events for job state changes and error outcomes.
- **SHOULD:** Standardize structured log fields (traceId/requestId, actor/tenant, jobId/jobType, errorCode, status, latency) so system-level debugging is not bespoke per service.

**B16 - One canonical verification entrypoint**

- **MUST:** Provide a single canonical `verify` entrypoint that runs unit tests, contract enforcement tests, build/package checks, and static analysis.
- **SHOULD:** `verify` SHOULD be hermetic with respect to third-party services (no calls to external SaaS APIs); use local stubs/snapshots where needed.

**B17 - Operational conventions are versioned**

- **SHOULD:** Treat cross-service operational conventions as contracts (correlation headers, job envelopes, error taxonomy, permission codes) and version them in the contract hub.

#### Chapter 2 - Integration Harness & System Testing Principles

##### 2.1 Purpose

The integration harness prevents cross-repo drift by providing executable system truth:

- contract fixtures decode and validate
- end-to-end critical flows run in a realistic wired environment
- mixed-version realities are discovered before production

The harness exists because, in Compatibility Mode, “everything was green in my repo” does not imply “the system works.”

##### 2.2 Environment posture

**I1 - One-command runnable environment**

- **MUST:** Provide one-command startup for local development (compose/devcontainers or equivalent).
- **MUST:** Start the minimal set of services required for smoke tests.
- **SHOULD:** Prefer a minimal, local-first dependency set:
  - stub or emulate third-party services
  - avoid requiring developer credentials for baseline smoke/compat runs

**I2 - Local/CI parity with explicit exceptions**

- **SHOULD:** CI SHOULD run the same smoke/compat checks as local using the same commands.
- **MUST:** Any divergence MUST be documented and tested (e.g., managed DB in CI).

**I3 - Version pins are part of the harness contract**

- **MUST:** The harness MUST pin versions/tags/commits for each component it wires together (including contract artifacts and images).
- **MUST:** In CI and any shared environment, container images MUST be pinned by immutable digest (tag + digest is acceptable; digest-only is acceptable; tag-only is not).
- **SHOULD:** Maintain a single machine-readable “pins manifest” (versions/commits/digests) that is emitted in CI logs and stored as a build artifact for reproducibility.
- **MUST:** CI executions MUST use deterministic pins (no implicit “latest” tags).
- **SHOULD:** The harness SHOULD support “pin to local” for active development while keeping CI pins deterministic.

##### 2.3 Smoke tests (end-to-end)

**I4 - Smoke tests are small, critical, and stable**

- **MUST:** Maintain a minimal suite covering the most important end-to-end flows.
- **SHOULD:** Keep smoke tests as deterministic and non-flaky as feasible via fixed seeds, stubs/snapshots, and time injection.
- **MUST:** Smoke tests MUST be runnable in CI.
- **SHOULD:** Smoke tests SHOULD run on pull requests (PRs) targeting the default branch (e.g., `main`).
- **MUST:** If smoke tests do not run on every PR, they MUST run on merges to the default branch (e.g., `main`).
- **SHOULD:** If smoke tests do not run on every PR, schedule them at least daily on the default branch (e.g., `main`).

**I4a - UI smoke coverage and UX evidence (when a user-facing UI exists)**

- **MUST:** If the system has a user-facing UI (web/mobile/admin), the harness SHOULD include at least one **browser-level** smoke scenario (`smoke-ui`) for each canonical workflow (or document why API-level smoke is sufficient).
- **MUST:** UI smoke tests MUST use stable selectors (e.g., `data-testid`) and SHOULD align with the UI Spec Appendix’s Screen IDs (`UI-###`).
- **MUST:** UI smoke failures MUST produce diagnosable artifacts (screenshot + trace/DOM snapshot where supported) and MUST surface correlation/request IDs so backend/job logs can be traced.
- **SHOULD:** Keep UI smoke as deterministic as practical using seeded/scrubbed data, pinned versions, and stubs/snapshots for non-deterministic AI calls.
- **SHOULD:** UI smoke scenarios SHOULD be explicitly mapped to workflows/screens in the UI Spec Appendix so coverage is reviewable.
**I5 - Diagnosable failures**

- **MUST:** On failure, tests MUST surface scenario name and correlation IDs.
- **SHOULD:** Persist failure artifacts in CI:
  - captured logs (structured where possible; scrubbed/redacted)
  - UI screenshots/traces (when UI smoke/E2E runners are used)
  - relevant request/response envelopes (scrubbed)
  - job envelopes and final diagnostics
  - component/version pins used for the run (or a reference to the pins manifest)
  - a replay hint (command + fixture/seed)

##### 2.4 Contract compatibility runners

**I6 - Fixtures are executable compatibility artifacts**

- **MUST:** For critical boundaries, run consumer decoding tests against golden fixtures.
- **SHOULD:** Include both happy-path and representative failures (validation errors, auth errors, degraded job outcomes).
- **MUST:** Any contract change MUST update fixtures and required checks.

**I7 - Mixed-version compatibility is tested intentionally**

- **SHOULD:** Test at least “N with N-1” (or equivalent) for stable contracts.
- **MAY:** Add an explicit version-matrix runner for high-risk boundaries (async callbacks, job envelopes, stored artifacts).
- **SHOULD:** If a supported compatibility window exists, document it and test within it.

##### 2.5 Data seeding and isolation

**I8 - Seeded data is deterministic and scrubbed**

- **MUST:** Seed data MUST be deterministic and scrubbed of PII.
- **SHOULD:** Provide seed scripts that reset to a known state quickly.
- **MUST:** Tests MUST NOT depend on manual local state or operator steps.

**I9 - Isolation and cleanup**

- **SHOULD:** Prefer ephemeral CI environments (fresh DB per run).
- **MUST:** In shared environments, tests MUST namespace their data and clean up reliably.

##### 2.6 Performance and budget guardrails (minimal)

**I10 - Integration budgets catch obvious regressions**

- **SHOULD:** Include at least one guard for a critical flow (request latency, job completion time).
- **MAY:** Add an AI-cost guard (token/cost budget) using stubs/snapshots where needed.

##### 2.7 Canonical harness entrypoints

**I11 - Canonical entrypoints** The harness SHOULD expose canonical commands (or equivalents):

- `verify` (default CI gate; typically runs `smoke` + `compat` plus required wiring checks)
- `up` / `down`
- `smoke`
- `compat`
- optional `matrix` (expanded version-window checks, typically scheduled on merges/nightly)

**I12 - CI is the reference execution**

- **MUST:** The harness `verify` output in CI MUST be treated as authoritative for system integration.
- **SHOULD:** When a harness check is too slow for every PR, use:
  - a small PR gate (fast smoke + compat),
  - a larger nightly/merge gate (matrix + broader scenarios),
while keeping at least one deterministic gate on merges.

#### Chapter 3 - Data & Evals Governance Principles

##### 3.1 Purpose

Data and evaluation are contract surfaces that are:

- versioned and reproducible
- privacy-safe and license-compliant
- governed with clear ownership
- integrated into CI and release decisions

##### 3.2 Dataset governance

**D1 - Dataset manifests are required**

- **MUST:** Dataset manifests MUST contain metadata only; they MUST NOT embed raw dataset contents.
- **MUST:** The dataset manifest format/schema MUST be versioned and validated (schema check) in CI to prevent drift.
- **MUST:** Every dataset used in development, evaluation, or gating MUST include a machine-readable manifest (YAML/JSON is acceptable) that records at least:
  - manifest schema version (e.g., `schemaVersion`)
  - `datasetId` and `datasetVersion` (or equivalent)
  - owner and point-of-contact
  - intended use and restrictions
  - provenance/source and collection method
  - license/terms and restrictions
  - schema/field definitions (or pointer to schema)
  - split policy (train/val/test) where applicable
  - PII/sensitivity classification and access level
  - an immutable reference to the dataset contents (required for CI/release gating datasets and any evals used for decisions or shared reporting):
    - the manifest MUST include either `contentHash` (preferred) or `snapshotId` (if hashing is not feasible)
    - `contentHash` SHOULD be used for CI/release gating when feasible
    - `snapshotId` MUST be used for CI/release gating if `contentHash` is not feasible; it MUST be an immutable snapshot identifier from a governed system
    - `storageUri` MAY be included as a convenience pointer; if present, it MUST be immutable/versioned and MUST correspond to the same bytes as `contentHash` / `snapshotId`
  - the hashing/canonicalization method used to compute `contentHash` (required if `contentHash` is present), or the snapshot system and immutability guarantees if using `snapshotId`
  - retention window and deletion contact/owner
- **SHOULD:** The manifest SHOULD include known limitations (coverage gaps, known biases, label noise risks).

**D2 - Provenance and licensing are mandatory**

- **MUST:** Every dataset MUST document source/provenance and license/terms.
- **MUST:** Datasets with unclear licensing MUST NOT be used for production decision-making or distributed outside approved scopes.

**D3 - PII and sensitive data handling**

- **MUST:** Raw production PII MUST NOT be committed to repos.
- **MUST:** Eval datasets and fixtures MUST be scrubbed/minimized, and access-controlled by least privilege.
- **SHOULD:** Prefer synthetic or de-identified datasets for broad developer access.
- **MUST:** Any “debug capture” dataset containing sensitive content MUST have:
  - explicit access approvals
  - tight retention windows
  - redaction or encryption controls
  - a documented deletion path

**D4 - Versioning and immutability**

- **MUST:** Datasets used for CI/release gating MUST be versioned and immutable (manifest + immutable dataset pointer (`contentHash`/`snapshotId`)).
- **MUST:** If a dataset is updated, the version MUST change; in-place edits are prohibited for gating sets.
- **SHOULD:** Keep stable splits for gating sets to make regressions comparable.

**D5 - Retention and deletion**

- **MUST:** Define retention windows and deletion processes for datasets, including derived artifacts (indexes, embeddings, cached generations).
- **SHOULD:** Record deletion actions and confirmation in a lightweight audit trail when compliance requires it.

##### 3.3 Evaluation as a contract

**D6 - Determinism tiers are declared**

- **MUST:** Declare a determinism tier for every eval suite.
- **SHOULD:** Prefer stable tiers for any eval suite used for gating or shared reporting.

At minimum, support these tiers (use the canonical definitions in §7.3):

- **Tier 0 (replay via cassettes):** non-deterministic or external dependencies exist, but the eval suite provides replay artifacts (golden fixtures, transcripts/cassettes, snapshot IDs) so CI can reproduce and verify behavior.
- **Tier 1 (stable given pinned dependencies):** repeatable across environments given pinned inputs and dependency snapshots; stable enough for gating, but not necessarily bitwise identical.
- **Tier 2 (bitwise / fully deterministic):** identical outputs bit-for-bit; requires strict control of floats, concurrency, randomness, and hardware (rare).

**D7 - Evaluation definitions are contracts**

- **MUST:** Define metrics/rubrics with:
  - clear definitions (what is measured and how)
  - thresholds (pass/fail or tiers)
  - sampling policy (what cases are included and why)
  - reporting schema (how results are emitted and compared)
- **MUST:** Evaluation logic used for gating MUST be runnable locally with pinned versions.

**D8 - Scoring logic belongs to a shared contract surface**

- **SHOULD:** If multiple repos/pipelines need the same “definition of success,” the scoring implementation SHOULD be distributed as a version-pinned scoring artifact.
The artifact SHOULD be small and dependency-light (package or equivalent) and referenced from the contract hub.

- **MUST:** Scoring artifacts used for CI/release gating MUST be version-pinned (no implicit `latest`), and the version used MUST be recorded in eval run manifests.
- **MUST:** Success criteria MUST NOT exist only as private scripts in a single repo that other producers/consumers cannot run.

**D9 - Two-tier eval suites (recommended)**

- **SHOULD:** Maintain:
  1. A small deterministic CI eval set (fast, stable, gating)
  1. A larger offline benchmark (slower, broader coverage)
- **MUST:** CI gating MUST avoid reliance on unstable third-party network calls; use stubs/snapshots.

**D10 - Handling nondeterminism**

- **MUST:** Declare a determinism tier for each eval suite.
- **SHOULD:** When stochasticity is inherent, define:
  - number of trials
  - aggregation method
  - acceptable variance/tolerance bands
  - regression detection method (e.g., confidence intervals)

**D11 - Regression budgets and promotion rules**

- **MUST:** Define explicit regression budgets:
  - which metrics MUST NOT regress
  - which metrics MAY regress within tolerance
- **SHOULD:** Promote new evals from report-only to gating once stable, trusted, and owned.

##### 3.4 Labeling and annotation governance (if applicable)

**D12 - Stable label definitions**

- **MUST:** Provide labeling guidelines, examples, and edge-case handling.
- **SHOULD:** Run inter-annotator agreement checks for subjective labels.
- **MUST:** Track labeling process changes as part of dataset versioning.

##### 3.5 Reproducibility and privacy-safe reporting

**D13 - Run manifests and provenance**

- **MUST:** Every eval run MUST record:
  - dataset reference: `datasetId`, `datasetVersion`, and an immutable dataset pointer (`contentHash` or `snapshotId`, plus optional `storageUri`)
  - scoring artifact version (if applicable)
  - code version (git SHA/build version)
  - model/prompt/config identifiers (including sampling parameters such as temperature/top_p and retrieval snapshot/version where applicable)
  - random seeds (if any) and determinism tier
  - environment fingerprint (optional but recommended)
- **SHOULD:** Provide a replay command that reproduces a run within the declared determinism tier.

**D14 - Privacy-safe reporting**

- **MUST:** Reports MUST avoid exposing raw sensitive examples by default.
- **SHOULD:** Prefer aggregate metrics and redacted snippets under access control for qualitative debugging.

#### Chapter 4 - Platform, Release, Security & Privacy Principles

##### 4.1 Purpose

Platform principles ensure that:

- changes are verifiable and releasable
- deployments are safe under mixed-version realities
- incidents are diagnosable and recoverable
- security and privacy are enforced systematically, not informally

This chapter combines release/ops and security/privacy because they are operationally interdependent.

##### 4.2 CI/CD and release discipline

**P1 - One canonical `verify` entrypoint per repo**

- **MUST:** Every repo MUST provide a canonical `verify` entrypoint.
- **MUST:** CI MUST run `verify` on every pull request targeting the default branch and on every merge to the default branch (e.g., `main`) and any release branch.
- **SHOULD:** `verify` SHOULD be hermetic with respect to third-party services (no calls to external SaaS APIs); use local stubs/snapshots where needed.

**P2 - Layered gates, not one mega-test**

- **SHOULD:** Use layered verification:
  - unit/module tests (fast)
  - contract enforcement (schemas/fixtures/codegen reproducibility)
  - integration smoke tests (wired environment)
  - offline eval/bench gates for AI-critical changes

**P3 - Reproducible builds and dependency control**

- **MUST:** Pin dependencies and tool versions (lockfiles).
- **MUST:** Generated code MUST be reproducible.
- **MUST:** If the repo uses code generation, CI MUST verify deterministic codegen outputs (or an equivalent reproducibility check).
- **MUST:** Generated artifacts MUST NOT be manually edited and MUST be clearly separated from hand-written code.
- **SHOULD:** Build artifacts SHOULD be reproducible across local and CI.
- **SHOULD:** Produce artifact metadata: build ID, git SHA, contract versions, and the `profileId`/`configId` (or equivalent) used for runtime behavior.
- **SHOULD:** Produce an SBOM for production artifacts where feasible.
- **SHOULD:** For production artifacts, produce signed build provenance/attestations (e.g., SLSA-style provenance) where feasible.

**P4 - Release strategy matches Compatibility Mode**

- **MUST:** Assume rolling deploys and partial upgrades unless you can enforce atomic cutover.
- **MUST:** Public contracts MUST remain backward compatible across the rollout window.
- **SHOULD:** Prefer one of:
  - rolling deploys with backward-compatible contracts (default)
  - blue/green or canary with explicit compatibility windows
- **MUST:** Every release MUST have a rollback plan covering code, config, and flags.
- **SHOULD:** Treat contract-breaking changes as planned migrations with explicit cutoffs and telemetry proving adoption.

**P5 - Feature flags: ownership, lifecycle, and audit**

- **MUST:** Feature flags MUST have owner, default value, rollout plan, and sunset plan.
- **MUST:** High-risk flags MUST be auditable (who changed what, when).
- **SHOULD:** Separate “deploy” from “release” using flags for risky behavior changes.
- **SHOULD:** Prefer “flag removal” tasks as first-class maintenance work; unowned flags are defects.

**P6 - Configuration is schema-validated and versioned**

- **MUST:** Runtime configuration MUST be schema-validated at startup (fail fast for invalid config).
- **MUST:** Configuration MUST be versioned (explicit config ID/version) for reproducibility and rollback.
- **SHOULD:** Prefer typed config + migrations over ad-hoc environment variables.
- **MUST:** Configuration changes that affect security, privacy, or spend MUST be auditable.

**P7 - Database migrations in CI/CD**

- **MUST:** Migration application MUST be a controlled step with clear ordering relative to app deploy.
- **MUST:** Expand/contract rules MUST be followed for schema evolution.
- **SHOULD:** For destructive changes (drops, narrowing types), require explicit annotation and extra review gates.

**P8 - Contract publishing and upgrade hygiene**

- **SHOULD:** Prefer automation to publish contract artifacts and open consumer upgrade PRs.
- **MUST:** Do not publish or advertise a new **stable** contract version unless at least one producer deployment supports it in shared environments; use `proposed`/`experimental` tiers for contracts that are not yet broadly deployable.
- **MUST:** Consumers MUST pin contract versions/tags; builds MUST NOT rely on “latest.”
- **SHOULD:** Keep upgrades small and run compatibility checks on every contract bump.

##### 4.3 Observability, SLOs, and cost governance

**P9 - Service-level objectives (SLOs) are explicit**

- **SHOULD:** Define SLOs for critical user-facing operations (interactive endpoints, job completion for key job types).
- **SHOULD:** Pair SLOs with alert policies and error budgets.
- **MUST:** Alerting MUST be actionable and owned.

**P10 - Golden signals plus AI-specific signals**

- **MUST:** Monitor golden signals per service: latency, error rate, throughput, saturation.
- **SHOULD:** Add AI-specific signals where relevant:
  - token usage and estimated cost per request/job
  - cache hit rates (retrieval/embeddings/LLM caches if used)
  - schema validation failure rate
  - repair/retry rate
  - fallback rate and degraded outcome rate

**P11 - Traceability across the system**

- **MUST:** Propagate correlation IDs across sync and async boundaries (jobs, callbacks, queues).
- **SHOULD:** Include trace/request IDs in user-visible error reports where safe.
- **MUST:** Observability payloads (logs/traces/metrics) MUST NOT contain secrets.
- **MUST:** Observability payloads MUST NOT contain raw sensitive user content unless explicitly required and protected (access controls, redaction, retention limits).

**P12 - Budgets and rate limits are operational contracts**

- **MUST:** Enforce request size limits, timeouts, and rate limits at internet-facing boundaries.
- **SHOULD:** Enforce per-tenant budgets in multi-tenant systems.
- **MUST:** Budget/limit enforcement MUST be explicit and typed:
  - **Hard limits/budgets** MUST fail fast (or terminate a job) with a stable, diagnosable outcome and stable diagnostic codes.
  - **Soft budgets** MAY allow completion, but MUST emit stable diagnostics/metrics for cost governance and MUST be explicitly documented.
- **MUST:** Limit/budget exhaustion MUST be handled explicitly and MUST NOT crash the process; it MUST produce a typed, diagnosable response or terminal job outcome and emit stable diagnostic codes.
  - For synchronous APIs, return a stable error envelope/code (and an HTTP status consistent with your contract, e.g., `429`, `503`, or a typed `degraded` response).
  - For async jobs, resolve to a terminal `failed` or `degraded` outcome with `budget.exhausted` (or equivalent) diagnostics.
- **SHOULD:** Prefer safe degradation modes (reduced quality, smaller result sets, delayed processing) over unbounded retries.

##### 4.4 Security baseline

**S1 - Threat modeling for internet-facing systems**

- **MUST:** Maintain a baseline threat model for internet-facing systems identifying trust boundaries, attacker goals, critical assets, and mitigations with owners.
- **SHOULD:** Update the threat model for any change that introduces new tool capabilities, data flows, or external integrations.

**S2 - Least privilege everywhere**

- **MUST:** Services and jobs MUST run with least-privilege credentials.
- **MUST:** Secrets MUST be stored in a secret manager (or equivalent) and injected at runtime.
- **MUST NOT:** Commit secrets to source control.
- **SHOULD:** Restrict and audit CI credentials; protect signing keys if used.

**S3 - Network and transport security**

- **MUST:** Use TLS for in-transit data on untrusted networks.
- **SHOULD:** Use network segmentation and egress controls to limit blast radius (especially for tool-calling or retrieval services).
- **SHOULD:** Treat outbound egress to third parties as an explicit allowlist with owners.

**S4 - Secure-by-default input handling**

- **MUST:** Validate and sanitize untrusted inputs.
- **MUST:** Avoid unsafe deserialization and unsafe dynamic evaluation.
- **MUST:** Apply size limits to prevent resource-exhaustion attacks.
- **SHOULD:** Prefer “fail closed” for authorization and “degrade safely” for availability (graceful errors, reduced functionality) while avoiding partial writes or inconsistent state.

**S5 - Supply chain security**

- **SHOULD:** Use dependency vulnerability scanning and container scanning.
- **MUST:** Define vulnerability remediation SLAs (at least for critical/high findings) and follow them.
- **SHOULD:** Prefer pinned, verified base images and minimal runtimes.
- **SHOULD:** Run secret scanning and basic SAST checks in CI.

**S6 - AI-specific security controls** If you use LLMs, tools, retrieval, or agents:

- **MUST:** Treat model outputs as untrusted and validate against schemas.
- **MUST:** Use tool allowlists and explicit tool input/output schemas.
- **MUST:** Apply tool quotas/timeouts and bound the number of tool calls per request/job.
- **MUST:** Prevent data exfiltration:
  - tools MUST NOT access secrets unless strictly necessary
  - retrieval sources MUST be access-controlled per tenant/user
- **SHOULD:** Defend against prompt injection by:
  - separating instructions from untrusted content
  - minimizing tool authority
  - using structured tool calls with validation
  - monitoring for tool-abuse patterns

**S7 - Logging and audit safety**

- **MUST:** Logs MUST be redacted for secrets and sensitive data.
- **MUST:** Audit logs MUST record security-sensitive changes (permissions, keys, flags, high-risk config).
- **MUST:** Access to logs MUST be controlled and audited.

**S8 - Encryption at rest and key management**

- **MUST:** Sensitive data stores (databases, object stores, caches containing sensitive content, and backups) MUST use encryption at rest by default.
- **MUST:** Encryption exceptions (rare) MUST be explicitly approved, documented, and time-bounded with compensating controls.
- **SHOULD:** Key management SHOULD use a centralized KMS with:
  - least-privilege key access
  - rotation expectations
  - audit logging for key usage and policy changes
- **MUST:** Secrets (API keys, tokens, private keys) MUST NOT be stored in application databases unless explicitly designed for that purpose and protected by strict access controls and encryption.

##### 4.5 Privacy baseline

**PR1 - Data minimization and purpose limitation**

- **MUST:** Collect and store only what is necessary for product function.
- **SHOULD:** Separate operational telemetry from user content; avoid logging raw user content by default.

**PR2 - Retention and deletion**

- **MUST:** Define retention windows for user data and derived artifacts.
- **MUST:** Provide deletion mechanisms that cover primary and derived data (indexes, embeddings, caches) where applicable.

**PR3 - Privacy-aware experimentation and analytics**

- **MUST:** Analytics events MUST avoid sensitive payloads.
- **SHOULD:** Use stable event schemas and versioning where analytics is used downstream for decisions.

##### 4.6 Incident response and operational readiness

**IR1 - Runbooks and escalation**

- **SHOULD:** Maintain runbooks for common failure modes:
  - job queue backlog
  - model/API degradation
  - schema validation failure spikes
  - cost spikes
- **MUST:** Define on-call and escalation responsibilities for production systems.

**IR2 - Post-incident learning**

- **SHOULD:** Perform post-incident reviews with timeline, contributing factors, and corrective actions with owners/due dates.
- **MUST:** Corrective actions that change contracts MUST follow contract evolution rules.

> Note: In the source addendum, the following sections were labeled “Appendix A-E”. In the unified standard, they are labeled “Annex G-A-G-E” to avoid collisions with the standard’s top-level Appendices.

#### Annex G-A - Lightweight checklists

##### A1. Release readiness (minimum)

- [ ] `verify` passes for all changed repos
- [ ] Contract changes classified (additive/behavioral/breaking) with compatibility plan
- [ ] Integration smoke tests pass (and compat/matrix checks if relevant)
- [ ] Rollback plan documented (code/config/flags)
- [ ] SLOs/alerts updated for new behavior (where applicable)
- [ ] Data/eval gates updated (if success criteria changed)

##### A2. Secret and logging sanity

- [ ] No secrets committed; secret scanning running
- [ ] Logs scrubbed for sensitive content; access controlled
- [ ] Encryption at rest enabled for sensitive data stores and backups (or explicit approved exception)
- [ ] Sensitive datasets have retention/deletion policy documented

#### Annex G-B - Backend change “Definition of Done” (minimum)

- [ ] Contract impact assessed (API/event/job schema, identifiers, stored artifacts)
- [ ] Validation and error mapping updated (canonical behavior preserved or intentionally changed)
- [ ] Idempotency preserved for retryable writes
- [ ] Job envelope/state changes versioned and exercised with fixtures (if applicable)
- [ ] Observability added/updated (metrics, logs, correlation IDs)
- [ ] `verify` passes locally and in CI
- [ ] Integration smoke tests pass (or updated and pass)

#### Annex G-C - Contract change checklist (system-level)

- [ ] Decision owner approval
- [ ] Change classified: additive / behavioral / breaking
- [ ] Compatibility plan defined (window, versioning/dual-support, rollout)
- [ ] Fixtures updated (happy-path + representative failures)
- [ ] Producer enforcement tests updated
- [ ] Consumer decoding/compat tests updated
- [ ] Integration harness checks updated and passing
- [ ] Versioning/tier updated (if your standards use stability tiers)

#### Annex G-D - Data/eval change checklist

- [ ] Dataset manifest updated (provenance, license, intended use, sensitivity, retention)
- [ ] PII scrubbed/minimized; access controls appropriate
- [ ] Dataset versioned/hashed; splits stable (if applicable)
- [ ] Metric definitions + thresholds updated (and owners approved)
- [ ] CI eval suite remains stable (declared determinism tier; tolerances documented)
- [ ] Reports do not expose sensitive examples

#### Annex G-E - Minimal templates (optional but recommended)

##### E1. Dataset manifest (illustrative fields)

```
schemaVersion: "1.0.0"
datasetId: ds_summarization_core
datasetVersion: "2026-01-10"
owner: team-or-person
pointOfContact: "slack:#ml-quality" # or email

intendedUse:
  purpose: "CI gating for summarization"
  restrictions: ["no-external-distribution"]

provenance:
  source: "internal-labeling"
  collectionMethod: "curated sample"
  generatedAt: "2026-01-10"
  generatedBy: "pipeline:dataset_build@9b1d4c7"

license:
  terms: "internal"
  restrictions: ["no-external-distribution"]

sensitivity:
  pii: "none|low|moderate|high"
  accessLevel: "dev|restricted|highly-restricted"

schemaRef: "schemas/ds_summarization_core.schema.json"

splits:
  ci:
    count: 200
  offline:
    count: 5000

### Immutable dataset pointer
### MUST be present for CI/release gating datasets and any evaluation whose results are used for decisions or shared reporting.
### Provide `contentHash` (preferred) OR `snapshotId` (if hashing is impractical).
### For CI/release gating, `contentHash` SHOULD be used when feasible; otherwise `snapshotId` MUST be used.
### If both are present, they MUST refer to the same bytes/snapshot.
contentHash: "sha256:..."  # preferred
contentHashMethod: "sha256 of canonical tar.gz (files sorted by path)" # required if contentHash present

### snapshotId: "registry://datasets/ds_summarization_core@2026-01-10" # alternative when contentHash is not feasible

artifactRefs:
  raw:
    uri: "s3://datasets/ds_summarization_core/2026-01-10/raw.jsonl"
  normalized:
    uri: "s3://datasets/ds_summarization_core/2026-01-10/normalized.jsonl"

### Optional convenience pointer; if present, MUST be immutable/versioned and MUST correspond to the same bytes as the primary pointer.
storageUri: "s3://datasets/ds_summarization_core/2026-01-10/" # optional

retention:
  windowDays: 90
  deletionOwner: team-or-person
notes:
  limitations: ["known bias: ...", "coverage gap: ..."]
```

##### E2. Job envelope (illustrative fields)

```
{
  "schemaVersion": "1.0.0",
  "jobId": "job_123",
  "jobType": "document.summarize",
  "status": "succeeded",

  "createdAt": "2026-01-10T18:00:00Z",
  "updatedAt": "2026-01-10T18:00:03Z",
  "startedAt": "2026-01-10T18:00:01Z",
  "finishedAt": "2026-01-10T18:00:03Z",

  "profileId": "prod@4",
  "configId": "cfg_01HZ…",
  "configHash": "sha256:…",
  "attempt": { "count": 1, "max": 5 },

  "correlation": { "requestId": "req_abc", "traceId": "trace_xyz" },

  "inputRef": {
    "rawInputId": "raw_01HZ…",
    "inputHash": "sha256:…",
    "snapshotId": "snap_01HZ…"
  },

  "sideEffectsMode": "dryRun",

  "runs": [
    {
      "attempt": 1,
      "startedAt": "2026-01-10T18:00:01Z",
      "finishedAt": "2026-01-10T18:00:03Z",
      "manifestRef": {
        "runId": "2026-01-10T18:00:01Z/9b1d…",
        "manifestHash": "sha256:…"
      },
      "result": {
        "schemaVersion": "1.0.0",
        "runId": "2026-01-10T18:00:01Z/9b1d…",
        "pipeline": { "id": "summarize.v2" },

        "status": "ok",
        "output": { "summary": "..." },
        "warnings": [],

        "diagnostics": {
          "codes": ["ok"],
          "kv": { "model": "gpt-4.1", "region": "us-east-1" },
          "counters": { "llmTokens": 812 }
        },

        "stageSummaries": [
          { "stageId": "retrieve", "status": "ok", "timeMs": 31, "codes": [] },
          { "stageId": "summarize", "status": "ok", "timeMs": 77, "codes": [] }
        ],

        "budget": {
          "scope": "pipeline",
          "allocated": { "timeMs": 1500, "tokens": 2000, "externalCalls": 50 },
          "consumed": { "timeMs": 108, "tokens": 812, "externalCalls": 3 },
          "remaining": { "timeMs": 1392, "tokens": 1188, "externalCalls": 47 },
          "termination": { "code": "ok" },
          "children": []
        },

        "manifestRef": {
          "runId": "2026-01-10T18:00:01Z/9b1d…",
          "manifestHash": "sha256:…"
        },

        "error": null
      }
    }
  ],

  "diagnostics": { "codes": ["job.succeeded"] },
  "error": null
}
```

##### E3. UI Spec Appendix (pointer)

If the product ships a user-facing UI, maintain a UI spec artifact that makes workflows implementable and testable.

Recommended options:

- **Master Doc Annex D - UI Spec Appendix (reference)** + repo-local `docs/ui_spec_appendix.md` copied from the **Standard’s Appendix D template**
- a standalone `UI_SPEC.md` / `docs/ui_spec_appendix.md` based on the same template

Minimum required content:

- design source of truth link (prototype)
- screen inventory with stable Screen IDs (`UI-###`) and route IDs (if applicable)
- workflow→screen maps for canonical workflows (`W#`)
- per-screen state coverage for critical screens (loading/empty/error/permission)
- test mapping: which `smoke-ui` / E2E scenarios cover which workflows/screens, and where CI artifacts (screenshots/traces) are stored

## Appendix H - UI Design Review Checklist

This appendix complements **Appendix D (UI Spec Appendix)**. The UI Spec Appendix makes UI behavior *implementable and testable*; this checklist standardizes the *quality bar* for usability, accessibility, and user trust.

The checklist is split into:

- **Automatable checks** - SHOULD be enforced in CI (`verify`) using linting, accessibility tests, E2E smoke, and (when applicable) visual regression.
- **Judgement checks** - MUST be reviewed by a human (multimodal LLM assistance is optional, not authoritative).

### H.1 Severity policy

- **P0 (blocker):** MUST fix before merge/release.
- **P1 (should):** SHOULD fix before release; may defer only with an explicit owner + due date + rationale.
- **P2 (nice-to-have):** MAY defer; capture as backlog if repeated.

### H.2 Checklist

| Area | Check | Typical failure mode | Severity | Automatable? | Suggested enforcement |
| --- | --- | --- | --- | --- | --- |
| Design system governance | Token contract is versioned and consumed from the canonical source (no drift between design and code) | Token values drift between design and code; ad-hoc overrides proliferate; “incubator” tokens never expire | P0 | Partial | Pin token package + review token diffs; enforce incubator namespace + expiry; run visual regression on token changes (often in verify --full) |
| Semantic colors & CTA hierarchy | Primary/Secondary/Tertiary/Danger semantics are consistent across screens | “Confirm” for delete uses primary color; multiple “primary” CTAs in same region | P0 | Partial | Component API constraints + snapshot tests; manual review for semantics |
| Readability / contrast | Text, icons, borders meet contrast baseline; placeholders are visible | Low contrast grey-on-grey; placeholder nearly invisible | P0 | Yes | Token contrast script + axe checks (color contrast) |
| Accessibility | Keyboard navigation works; focus states visible; modals trap focus; Esc/close behavior; screen reader labels | Focus lost; cannot tab to controls; icon-only buttons without aria-label | P0 | Yes | Playwright/Cypress + axe-core; dedicated keyboard tests |
| States & feedback | Each critical screen covers Loading/Empty/Error/Permission states with consistent components | “Static screenshot” feeling; missing skeleton/empty state; errors only via toast | P0 | Partial | UI Spec Appendix coverage check + E2E state tests (mocked APIs) |
| AI-native states & feedback | AI screens distinguish Loading vs Thinking, cover Streaming/Repairing/Needs-confirmation, and provide cancel/retry | Generic spinners; no progress; streaming breaks usability; no recovery path | P0 | Partial | Enforce via UI Spec coverage + E2E state tests; manual review; see §6.7 |
| Citations / references | Citations render consistently and are linkable/previewable per the citation contract (§4.4.9), including integrity.status handling | Backend emits [doc_1] labels UI cannot resolve; broken links; inaccessible tooltips; raw markers leak | P0 | Partial | Contract tests + UI renderer unit tests/E2E; spec-defined interactions in Appendix D; graceful fallback for partial/invalid |
| Form validation | Required fields are marked; inline errors near fields; clear validation copy | Errors only via toast; required not marked; unclear copy | P1 | Partial | Component-level tests + i18n lint; manual review for copy clarity |
| Destructive actions | Danger styling; confirmation includes object identity; irreversibility explained | Generic “Confirm”; no object shown; easy mis-click | P0 | Partial | Component pattern + E2E; manual review for copy |
| Information architecture | Screen/module naming matches content; navigation matches user permissions | “Permissions mgmt” screen shows only user list; teacher sees admin menu | P0 | Partial | Role-based E2E snapshots; manual review for IA |
| Consistency of list pages | Standard list toolbar layout (search/filter/sort + primary CTA); pagination consistency | Toolbars reorganized per page; pagination alignment differs | P1 | Partial | Shared layout components; visual regression across representative pages |
| Table/list density & alignment | Alignment rules (numbers/date/text) and density are consistent; optional compact mode | Numeric columns not right-aligned; row height inconsistent | P2 | Partial | CSS lint for alignment classes; visual regression |
| Discoverability | Icon-only controls have tooltips/labels; click targets meet minimum size | Small unlabeled icons; unclear click targets | P1 | Partial | E2E hover checks; a11y label enforcement; manual review for UX |
| Data credibility (dashboards) | Units, definitions, time window, and totals are correct and non-misleading | KPI shown as percent when should be count; pie chart ≠ 100% | P0 | Partial | Unit tests for data transforms; manual review for semantics |
| Review artifacts | Design/fixtures use synthetic data and cover edge cases | Repeated sample rows cause “duplicate data bug” confusion | P1 | Partial | Fixture lints; manual review checklist |
| Testability hooks | Critical interactions have stable data-testid selectors | Unstable selectors; missing hooks for E2E | P0 | Yes | Lint/check in UI Spec + E2E test harness |
| Design-to-code traceability | Screen IDs (UI-###) map to named frames in the design source of truth | Figma links rot; designs change without code noticing | P1 | Yes (advanced) | scripts/verify/design checks design source (e.g., Figma API) for frames referenced in Appendix D |
| Visual contract (atomic components) | UI kit component states defined in the spec exist as stories and are snapshotted in CI | “Should” becomes “never”; subtle component regressions ship unnoticed | P0 | Yes | Storybook (or equivalent) + snapshot baselines; run on PR when UI kit changes, otherwise in verify --full/nightly |
| Visual regression | Critical screens have baseline screenshots and are protected from accidental drift | Unreviewed UI drift; spacing changes unnoticed; flakiness causes gate fatigue | P1 | Yes | Visual regression tool (Playwright snapshot/Percy/etc.); prefer verify --full + path-based triggers to control cost |

### H.4 HFVI (canvas/WebGL/game) checks

This section applies when `interactionProfile = hfvi_canvas_webgl_game`.

| Area | Check | Typical failure mode | Severity | Automatable? | Suggested enforcement |
| --- | --- | --- | --- | --- | --- |
| Hit-testing correctness | Debug overlay renders hit areas/bounds/anchors for all interactive HFVI components | Click targets offset; invisible hit areas; transform origin bugs | P0 | Partial | verify --visual replay + debug overlay screenshots |
| No magic motion | Motion parameters are exclusively sourced from motion tokens | Hardcoded durations/easings regress feel and consistency | P0 | Yes | Token lint + grep checks + code review |
| Replay fixtures | Critical interactions have cassette fixtures and are replayable deterministically | CI cannot reproduce; manual testing required; flaky E2E | P0 | Yes | Playwright (or equivalent) replay runner |
| Visual regression | Key frames are snapshotted and reviewed on change | Unreviewed drift in layering/animation/layout | P1 | Yes | Snapshot diff tooling in verify --visual / --full |
| Performance budget | Target FPS / frame budget declared and tracked | Degraded interaction; jank; unbounded redraw | P1 | Partial | Perf smoke + telemetry + manual review |

### H.3 Recommended minimum automation bundle (frontend)

A repo with user-facing UI SHOULD include the following across its `verify` tiers (see §10.3):

**Fast / PR gate (`verify`)**

1. Boundary + lint (JS/TS + styles). Token enforcement applies per §4.5.1 and the project profile.
1. Unit tests for UI logic and state.
1. Accessibility checks (axe) on critical flows (keyboard + labels + focus + contrast).
1. Minimal E2E smoke for critical workflows, traceable to the UI Spec Appendix (Appendix D).

**Full / nightly or pre-release (`verify --full`)**

1. **UI kit visual contract** (when a UI kit exists): stories + snapshot baselines for all spec-defined component states.
1. Screen-level visual regression for critical screens or high-trust surfaces.
1. (Advanced) Design-to-code traceability check (UI-### ↔ named design frames) to detect orphaned specs.

## Appendix I - DDD playbook for SDMM + contract-driven systems

This appendix is a practical guide for applying **DDD** inside the constraints of this unified standard (multi-repo + SDMM + canonical contracts).

### I.1 When to use this playbook

You SHOULD apply this playbook when any of the following are true:

- multiple teams are contributing to the same product surface,
- there are multiple long-lived concepts with complicated lifecycle states,
- there is a mix of synchronous APIs and asynchronous jobs/events,
- or semantic drift (different meanings for the same word) has been observed.

### I.2 Core DDD concepts (minimal glossary)

- **Ubiquitous Language**: the shared vocabulary used in UI, docs, contracts, and code.
- **Bounded Context**: a semantic boundary where terms have a precise meaning and rules are consistent.
- **Aggregate**: a consistency boundary; invariants are enforced inside the aggregate and changes happen via the aggregate root.
- **Entity**: has identity and lifecycle.
- **Value Object**: immutable concept defined by value (e.g., Money, TimeRange).
- **Domain Event**: something that happened in the domain language (not a technical log).
- **Domain Service**: domain logic that doesn’t belong on an entity/value object.
- **Application Service / Use Case**: orchestration logic (calls repositories, emits events, calls other contexts).
- **Anti-corruption Layer (ACL)**: translation layer protecting the domain model from external semantics.

### I.3 Mapping DDD to this standard

**Bounded Context ↔ SDMM module (preferred) or repo boundary**

- In a modular monolith, each bounded context SHOULD be implemented as an SDMM module with a public entrypoint (no deep imports).
- In multi-repo, a repo SHOULD contain one primary bounded context; multiple contexts in one repo MUST still be separated by SDMM boundaries.

**Ubiquitous Language ↔ canonical contracts + docs**

- Contract field names, enums, and diagnostic codes MUST match the ubiquitous language.
- A “rename-only” change MUST be treated as a contract change (it is almost always semantically breaking).

**Domain Events / Commands ↔ contract surfaces**

- Events and commands that cross boundaries MUST live in the contract hub with fixtures and checks.

**Context Map ↔ integration harness**

- The integration harness is the natural home for:
  - cross-context end-to-end flows,
  - compatibility runners,
  - and “contract drift” detection (fixtures consumed across repos).

### I.4 Recommended code organization (backend example)

A DDD-friendly SDMM layout typically looks like:

```
backend/
  src/
    contexts/
      billing/
        domain/          # entities, value objects, aggregates, policies
        application/     # use cases; orchestration; transaction scripts
        adapters/        # HTTP handlers, job handlers, event consumers
        infrastructure/  # db implementations, messaging clients
        contracts/       # generated types + mapping helpers
      identity/
        ...
    shared/
      contracts/         # shared low-level contracts only (not domain coupling)
```

**Rules**

- `domain/` MUST NOT depend on infrastructure (DB/network). Keep it testable and deterministic.
- Cross-context calls MUST go through `adapters/` (API) or explicit event/command contracts.
- “Shared” code MUST be carefully scoped. Sharing domain logic across contexts SHOULD be avoided; share via contracts and adapters instead.

### I.5 Classes, inheritance, and derived types (OOP guidance)

DDD does not require OOP, but many teams implement domain models with classes. Use these rules to keep changes AI-safe:

- **Prefer composition over inheritance**. Inheritance SHOULD be shallow (0-1 levels) and SHOULD NOT be used as a code reuse hack.
- Inheritance MAY be used when:
  - the “is-a” relationship is stable in the ubiquitous language,
  - and the hierarchy is closed (sealed) with explicit exhaustiveness checks.
- Domain classes SHOULD:
  - keep invariants close to the data,
  - validate on construction or on state transitions,
  - and expose intention-revealing methods (avoid public field mutation).
- Avoid cross-context base classes like `BaseEntity` that smuggle behavior across boundaries.
- Prefer explicit **sum types** (sealed hierarchies) or `kind` enums when compatibility and exhaustiveness matter.
- For algorithm/pipeline code:
  - represent pipeline stages as **strategies** or **pure functions** behind stable interfaces,
  - keep stage inputs/outputs as explicit value objects (validated, schema-aligned),
  - avoid deep “StageBase → DerivedStage → SpecializedStage” inheritance chains.

### I.6 Testing guidance

- Aggregates MUST have unit tests that enforce invariants and state transitions.
- Domain event emission SHOULD be tested with fixtures (what event, when, with which payload).
- For cross-context integration, prefer contract tests + integration-harness scenarios over mocking internal details.

## Appendix J - BDD scenarios + verification playbook

This appendix defines how to treat **Given/When/Then** scenarios as living documentation and as automated gates.

### J.1 What “BDD” means in this standard

BDD here is not a specific framework. It is the practice of:

- describing system behavior in domain language (ubiquitous language),
- using scenarios (Given/When/Then) with concrete examples,
- and running those scenarios as part of verification (`verify`, smoke, compat, replay, eval).

### J.2 Scenario conventions (IDs, structure, traceability)

**Scenario IDs (recommended)**

- Use stable IDs to preserve traceability across refactors:
  - `SCN-001`, `SCN-002`, … (global)
  - or `W1.S1`, `W1.S2`, … (workflow-scoped)

Each scenario MUST reference:

- the workflow (`W#`) and/or functional requirement (`FR-###`) it validates,
- the contract surface(s) it exercises (route IDs, schema IDs, job types),
- and the gate(s) that run it.

**Gherkin template (example)**

```
Feature: {{FEATURE_NAME}}  # maps to F-### and/or W#

  # Traceability:
  # - Workflows: W1
  # - Requirements: FR-001, FR-007
  # - Contracts: api.public.v1/CreateJob, job-envelope.schema.json@1.0.0
  # - Gate: backend.verify (smoke), integration.verify (e2e)

  Scenario: SCN-001 {{SCENARIO_TITLE}}
    Given {{precondition in domain language}}
    And {{other setup}}
    When {{action}}
    Then {{observable outcome}}
    And {{contract-level assertion}}
```

### J.3 Where scenarios live (repo-local vs integration)

- **Repo-local scenarios** SHOULD cover:
  - domain rules (fast unit-level),
  - adapter behavior (API/job handlers),
  - and boundary validations (contract tests).
- **Integration-harness scenarios** MUST cover:
  - cross-repo flows (frontend → backend → algo),
  - compatibility windows (old/new fixtures),
  - and critical production smoke flows.

### J.4 Determinism and AI workloads (Tier 0/1/2)

Scenarios that exercise AI pipelines MUST declare their determinism expectations:

- **Tier 0 / Tier 1** scenarios MUST be runnable offline-by-default:
  - use cassettes, snapshots, or pinned fixtures,
  - treat model outputs as untrusted input and validate against schemas,
  - and enforce budgets with explicit termination codes.
- **Tier 2** scenarios MAY call live services, but MUST be isolated from the default `verify` gate and MUST have explicit cost controls.

### J.5 Turning scenarios into gates

A practical mapping:

- `unit`: domain invariants and transformations (fast, deterministic).
- `contract`: schema + fixture validation + compatibility decoding.
- `integration`: adapter-level tests (HTTP/job handlers) with fake infra.
- `e2e smoke`: a small set of critical scenarios, cross-module or cross-repo.
- `replay/eval`: pipeline scenarios with golden fixtures + deterministic reports.

**SHOULD:** Every critical workflow (`W#`) SHOULD have at least one automated scenario in a CI gate.

**MUST:** If that is infeasible in the short term, the Master Doc MUST document the gap, the owner, and a milestone date.

### J.6 Example: Job orchestration scenario (end-to-end)

```
Feature: Summarization job orchestration

  # Workflows: W1
  # Requirements: FR-001
  # Contracts: api.public.v1/SubmitJob, JobEnvelope@1.0.0, PipelineResult@1.0.0
  # Gate: integration.verify (e2e)

  Scenario: SCN-001 User submits a summarization job and receives a completed result
    Given a user with permission "summarize:run"
    And a valid input document fixture "doc.short.v1"
    When the user submits a summarization job with sideEffectsMode "dryRun"
    Then the API responds 202 with a JobEnvelope whose status is "running"
    And the job can be polled until it reaches status "succeeded"
    And the final JobEnvelope includes a PipelineResult with schemaVersion "1.0.0"
    And the RunManifest referenced by the result can be retrieved and explains the stages
```

### J.7 Step-definition guidance (framework-agnostic)

- Step definitions SHOULD assert **observable contracts**, not internal implementation details:
  - contract payload validation,
  - stable diagnostic codes,
  - state machine transitions,
  - idempotency keys,
  - and budget enforcement.
- Scenarios SHOULD reuse the contract hub fixtures (or repo-local fixtures that are derived from them) to reduce drift.
- For UI E2E, steps SHOULD operate on stable selectors defined in the UI Spec Appendix.

## Appendix K - High-Fidelity Visual Interaction (HFVI) Extension: Visual Interaction Spec Appendix (VIS) Template

Status: template (normative for HFVI projects)

### K.0 Purpose and scope

This appendix defines how to specify, implement, and verify high-fidelity canvas/WebGL/game-like interaction surfaces.

Goals:

- make spatial/temporal behavior implementable and testable (not prose-only)
- provide technical anchors so AI code generation is constrained
- enable deterministic replay and visual regression for critical interactions
- preserve traceability: workflows and screens (Appendix D) -> HFVI scenes/entities (Appendix K) -> tests (`verify --visual`)

Non-goals:

- This appendix is not a replacement for the design source of truth (Figma/prototype).
- This appendix is not a full engine architecture guide; it defines contract-like artifacts and gates.

### K.1 Conventions (MUST)

For each HFVI surface, define:

- Coordinate system: origin, units, axis direction, rotation direction.
- Scaling strategy: DPR handling, zoom, camera transforms.
- Layering rules: z-order conventions and how focus/drag reorders.
- Input model: supported inputs (mouse/touch/keyboard/gamepad) and their mapping.
- Determinism controls: random seeds, time sources, and replay mode behavior.

### K.2 Scene inventory (required)

| Scene ID | Name | Engine surface | Target FPS | Notes |
| --- | --- | --- | --- | --- |

Rules:

- MUST: Every HFVI surface referenced by Appendix D MUST have a Scene ID here.
- SHOULD: Scenes SHOULD declare a frame budget (ms) and the measurement method.

### K.3 Visual aggregates (required)

Each composite HFVI entity MUST be modeled as a visual aggregate with explicit invariants.

For each aggregate:

- Aggregate ID: `AGG-###`
- Inputs (domain/sim state): what state it consumes (and from where)
- Render props: what geometry/render state it owns
- Invariants (MUST): relationships that must always hold
- Debug checks (SHOULD): runtime assertions when `debugMode=true`

Example invariants:

- `HealthBar.y = CharacterBody.y - 20` always.
- Connection lines anchor to node ports even during drag.

### K.4 Visual component spec table (required; technical anchors)

| VC ID | Description | Engine primitive | Technical props/config anchors | Events | Test IDs |
| --- | --- | --- | --- | --- | --- |
| VC-002 | ConnectionLine | Konva.Arrow | tension:0.5; hitStrokeWidth:20 | mouseenter/click | line-{from}-{to} |

Rules:

- MUST: Any behavior that is hard to describe in prose MUST be expressed as technical anchors here.
- SHOULD: Prefer library-native names (Konva props, CSS props) as the anchor vocabulary.

### K.5 Motion design system (required; motion tokens)

HFVI projects MUST define motion tokens in the canonical token source (§4.5.1) and reference them by stable IDs.

| Token ID | Semantics | Tech spec |
| --- | --- | --- |
| MOT-REJECT | invalid action bounce | duration=400ms, elasticOut |

Rules:

- MUST: No hardcoded motion parameters outside token sources.
- MAY (L0 bounded): temporary incubator tokens with owner + expiry.

### K.6 Debug overlay contract (required)

When `debugMode=true`, each HFVI component MUST render:

- hit area / bounding box
- anchor point / transform origin
- optional: z-order/layer label and velocity vectors

Purpose:

- make hit-testing and transforms diagnosable
- make visual regression failures actionable (screenshots show geometry, not just final pixels)

### K.7 Verification mapping (required)

For each critical interaction, define:

- Cassette ID (input event sequence) and storage path
- Replay runner command (e.g., Playwright harness)
- Screenshot baseline IDs and capture timestamps
- Assertions: invariants + key-frame diffs

Template:

- Interaction: `INT-001 Drag card to zone`
  - Cassette: `fixtures/replay/int-001-drag-card.json`
  - Runner: `pnpm verify --visual`
  - Baselines: `fixtures/visual/int-001/frame-000.png`, `frame-120.png`
  - Assertions:
    - invariant: card ends within drop zone bounds
    - screenshot diff: key frames within tolerance
