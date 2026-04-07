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
  - schemas (JSON Schema / Protobuf; OpenAPI snapshots when OpenAPI-first or as generated artifacts),
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

> Note: In the source addendum, the following sections were labeled “Appendix A-E”. In the unified standard, they are labeled “Annex G-A through G-E” to avoid collisions with the standard’s top-level Appendices.

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

- **Master Doc Annex C-D - UI Spec Appendix (reference)** + repo-local `docs/ui_spec_appendix.md` copied from the **Standard’s Appendix D template**
- a standalone `UI_SPEC.md` / `docs/ui_spec_appendix.md` based on the same template

Minimum required content:

- design source of truth link (prototype)
- screen inventory with stable Screen IDs (`UI-###`) and route IDs (if applicable)
- workflow→screen maps for canonical workflows (`W#`)
- per-screen state coverage for critical screens (loading/empty/error/permission)
- test mapping: which `smoke-ui` / E2E scenarios cover which workflows/screens, and where CI artifacts (screenshots/traces) are stored
