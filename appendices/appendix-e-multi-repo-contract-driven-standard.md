# Appendix E - Multi-Repo Contract-Driven Standard

### AI‑Optimized Contract‑Driven Multi‑Repo Engineering Standard
Included in DAS Standard: v1.4.6 (2026-04-06)
Status: General‑purpose reference for AI‑assisted development of full‑stack AI products
Scope: End‑to‑end systems that commonly include **Frontend**, **Business Backend (System of Record / Orchestrator)**, and an **Algorithm/Model Service** (plus optional Admin/Backoffice, Integration Harness, and Data/Evals). This standard focuses on **repo boundaries**, **contracts**, **contract evolution**, and **AI‑friendly execution workflows**.

---

#### 0. Normative language (Appendix E)

This appendix uses **BCP 14** requirement keywords (RFC 2119 + RFC 8174).

- The primary normative keywords used in this appendix are: **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**.
- If synonymous terms appear (e.g., **REQUIRED**, **SHALL**, **SHALL NOT**, **RECOMMENDED**, **OPTIONAL**), they MUST be interpreted as the corresponding BCP 14 keyword; authors SHOULD prefer the primary keywords above for clarity.
- Lowercase forms (“must”, “should”, etc.) are non‑normative unless explicitly marked.

Interpretation guidance:

- **MUST / MUST NOT**: required for correctness, safe cross‑repo evolution, or to prevent drift.
- **SHOULD / SHOULD NOT**: strongly recommended; deviation requires explicit justification and compensating controls.
- **MAY**: optional.

---

#### 0.1 Key definitions

- **Producer**: the component/service that emits a payload or behavior (e.g., an HTTP response, an event, a callback) and is responsible for maintaining its contract.
- **Consumer**: the component/service that receives a payload or depends on a behavior and is responsible for tolerant reading and correct usage.
- **Contract**: anything two independently built units must agree on. A complete contract includes:
  1) **Schema** (machine‑checkable shape),
  2) **Semantics** (behavioral rules/invariants),
  3) **Examples/fixtures** (known‑good and representative failures),
  4) **Executable checks** (producer validation and/or consumer decoding tests).
- **Contract artifact**: the machine‑checkable representation of a contract (spec/schema/types/fixtures/codegen config) stored in the contract hub.
- **Decision owner**: the single party that decides contract semantics and approves changes (often, but not always, the producer).
- **Contract hub**: the canonical repository (or canonical module in a monorepo) that stores contract artifacts and runs executable compatibility checks.

##### 0.1.1 Evolution modes

These terms describe **deployment reality**, not Git mechanics.

- **Compatibility Mode**: producer and consumer can deploy independently. Partial upgrades are observable in at least one environment (staging/prod), whether due to separate pipelines, rolling deploys, caches, or async processing. Breaking changes therefore require compatibility windows, explicit versioning or dual‑support strategy, and observable rollout.

- **Refactor Mode**: a boundary behaves as if it can be updated “atomically” from the perspective of the environment observing it.

  **Important correction:** Refactor Mode is **reliably achievable only within a single deployable artifact** (e.g., within one frontend bundle, within one backend process, within one container image) or within **strict atomic cutovers** (blue/green or equivalent) where *no requests can cross the boundary with mixed versions*.

  In most real multi‑service systems (even if built from a coordinated release manifest), rolling deployments and distributed caching mean partial upgrades are still observable. Therefore:

  - **MUST:** Treat cross‑repo, cross‑service contracts as **Compatibility Mode by default**.
  - **MAY:** Treat a cross‑repo change as Refactor Mode **only** if you can demonstrate (and enforce) that no environment can observe mixed versions across the boundary during rollout.

---

#### 1. Purpose

AI coding is most effective when:

- the change scope is small,
- ownership is explicit,
- interfaces are mechanically checkable,
- verification is fast and deterministic,
- integration is continuously validated.

Most AI products are systems spanning multiple runtimes, languages, and release cadences. This standard defines how to:

1) split a system into repos without introducing microservice‑style runtime complexity,
2) define, test, publish, and evolve contracts safely,
3) structure work so AI agents can implement changes without breaking integration.

---

#### 2. Critical distinction: repo boundaries vs runtime/service boundaries

A common failure mode is equating “more repos” with “more services.”

- **Repo split** is a *development organization* decision.
  - Primary effect: smaller change scope; clearer ownership; fewer AI‑induced blast‑radius failures.
  - It does **not** inherently add runtime latency.

- **Service split** is a *runtime architecture* decision.
  - Primary effect: adds network hops, distributed failure modes, operational/debugging cost.

**MUST:** Do not split runtime services purely to make code “AI‑sized.”

Instead:

- keep runtime boundaries minimal and intentional,
- use repo boundaries plus internal modularization to keep AI change scopes small.

**Rule of thumb**

- Split into more **repos** when repo size, language/toolchain mismatch, access control, ownership boundaries, or AI‑edit reliability requires it.
- Split into more **services** only when you need at least one of:
  - independent scaling,
  - hard security isolation,
  - independent deploy/rollback,
  - regulatory isolation,
  - clearly separable operational ownership.

---

#### 3. Topology choices

Choose the smallest topology that keeps AI tasks bounded and contracts explicit.

##### 3.1 Topology A — Monorepo with strict internal packages

Use when:

- one team owns most components,
- releases are tightly coupled,
- you want maximum refactor agility.

**SHOULD:** Use strict internal packages/modules with enforced boundaries.

##### 3.2 Topology B — Multi‑repo with a contract hub

Use when:

- components differ by language/toolchain or runtime,
- teams deploy independently,
- repo size exceeds what AI agents handle safely,
- you require explicit ownership/access boundaries.

This document primarily targets Topology B.

##### 3.3 Topology C — Hybrid

Common hybrids:

- separate `algo` repo (fast‑moving) + monorepo for `frontend`/`backend`,
- separate `contracts` repo + monorepo for the rest,
- separate `data-evals` repo for offline datasets and eval harness.

**MUST:** Regardless of topology, contracts MUST be explicit, testable, and governed.

---

#### 4. Recommended multi‑repo baseline (Topology B)

##### 4.1 Minimal repo set

Most AI systems are well served by **4–6 repos**, while keeping runtime services minimal:

1) **`contracts`** — contract hub (schemas, fixtures, identifiers, codegen)
2) **`frontend`** — user experience and client logic
3) **`backend`** — system‑of‑record + orchestrator
4) **`algo`** — model/compute service

Optional but frequently high leverage:

5) **`integration`** — local dev environment + end‑to‑end smoke tests + compatibility runners
6) **`data-evals`** — offline datasets, eval harness, benchmark reports

Optional (product‑dependent):

7) **`admin`** — backoffice UI and/or admin backend if it is truly a distinct product surface

**MUST:** Keep the number of runtime services small. Adding repos is often cheaper than adding services.

##### 4.2 What each repo owns

###### Repo: `contracts` (Contract Hub)

Owns canonical storage and distribution of:

- machine-readable endpoint inventory / API registry (recommended): `contracts/api/` for HTTP/RPC surfaces
- OpenAPI specs (REST), and/or gRPC/Protobuf/GraphQL schemas
- JSON Schemas / AsyncAPI for events, callbacks, and streaming messages
- standard envelopes (errors, jobs, pagination)
- contract semantics notes (field meaning, invariants, defaults, error mapping, redaction rules), preferably under `contracts/semantics/` or embedded in schema descriptions with stable refs
- cross‑repo identifiers (error codes, job types, permission codes, feature flags)
- golden fixtures (known‑good payloads) used by tests and mocks
- evaluation/scoring contract artifacts (rubrics, metric definitions, thresholds) when shared across repos
- executable contract checks (schema + fixture validation, drift detection) and compatibility runners
- code generation templates/config (and optionally generated packages)
- publishing artifacts (optional, read-only): generated OpenAPI 3.x snapshots for REST (SDK/docs), generated SDKs/clients

**MUST:** `contracts` contains **representations and executable checks only** (schemas/types/constants/fixtures/validators/tests), not product/business runtime logic.

**Clarification:** A small amount of *pure* “contract execution code” is acceptable when it is the executable form of a contract (e.g., schema validators, scoring/metric functions, fixture decoders). It MUST remain dependency‑light and MUST NOT require network/persistence.

###### Repo: `frontend`

Owns:

- UI/UX and view state
- client networking via generated clients or thin wrappers
- local validation and display mapping

**SHOULD:** Internally modularize (e.g., Single‑Deploy Modular Engineering) so AI tasks remain small and boundaries are enforceable.

###### Repo: `backend` (system‑of‑record + orchestrator)

Owns:

- authoritative domain state and persistence
- authn/authz policy and enforcement
- business workflows and orchestration
- stable public APIs for clients and integrations
- canonical validation and canonical error mapping
- long‑running job orchestration for AI workloads (preferred)

**SHOULD:** Remain a modular monolith unless additional runtime splits are operationally justified.

###### Repo: `algo` (model/compute service)

Owns:

- model inference, prompt pipelines, retrieval/tool calling
- structured extraction/scoring pipelines
- streaming responses (if required)
- strict validation/normalization of model outputs against schemas
- model‑specific safety controls (prompt injection mitigation, tool allowlists)

**MUST:** Treat model outputs as *untrusted* until validated and normalized.

###### Repo: `integration` (optional, recommended)

Owns:

- docker‑compose/dev containers and environment templates
- end‑to‑end smoke tests (“happy path” flows)
- contract compatibility test runners
- version‑matrix compatibility checks (optional but valuable)

This repo is the strongest guardrail against cross‑repo drift caused by many small AI‑authored changes.

###### Repo: `data-evals` (optional, high leverage)

Owns:

- offline datasets (scrubbed, versioned)
- eval harness (runner) and scoring scripts (sourced from / pinned to the shared scoring contract artifact)
- benchmark reports and regression dashboards
- labeling prompts and annotation guidance

**MUST:** `data-evals` is not a dumping ground for secrets or raw production data.

---

#### 5. Contracts: system‑wide taxonomy

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
- delivery semantics (at‑least‑once vs best‑effort)
- idempotency and dedup rules
- retry/backoff rules and poison‑message handling (if applicable)

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
- route IDs when referenced cross‑repo (permissions, audit, analytics)

##### 5.5 AI output contracts

- structured output schemas
- normalization rules (defaults, trimming, coercions)
- repair strategy when validation fails (retry, constrained re‑prompt, fallback, manual review)
- observability fields required for debugging (e.g., `requestId`, `promptId`, `modelId`)

**MUST:** AI output schemas are contracts. They must be versioned, tested, and monitored like APIs.

##### 5.6 Persistent artifact contracts

If any repo persists artifacts consumed by another repo/process, define contracts for:

- identifier formats (`modelId`, `promptId`, `embeddingModelId`, `jobId`)
- schema versions for stored blobs/documents
- retention/privacy constraints
- replayability expectations (can you recompute outputs from stored inputs?)

**SHOULD:** Treat “model selection” as a backend⇄algo contract, not ad‑hoc per consumer.

##### 5.7 Evaluation / scoring contracts (AI success criteria)

Evaluation is a contract. If one repo produces AI outputs and another repo (or pipeline) decides whether outputs are “good,” then the **scoring logic and thresholds** are part of the system contract surface.

Define, version, and test at least:

- **Metric definitions** (what is measured; how it is computed; unit/scale)
- **Pass/fail thresholds** (what “acceptable” means; tiered thresholds if applicable)
- **Sampling policy** (which inputs are evaluated; stratification; edge‑case sets)
- **Determinism requirements** (seeds, temperature, tool stubs, fixed retrieval snapshots)
- **Allowed non‑determinism** (when stochastic outputs are acceptable and how they are judged)
- **Reporting schema** (how results are emitted and compared over time)

**MUST:** The exact scoring implementation used by CI/`data-evals` MUST be runnable by the `algo` repo locally (same rules, same thresholds), by importing a version‑pinned scoring artifact.

Acceptable ways to share scoring contracts:

- **Preferred:** a small “scoring contract” package containing **pure** scoring functions/config and lightweight fixtures (no large datasets).
- **Alternative:** a pinned container image or executable runner whose version is referenced by the contract metadata.

**MUST NOT:** Hide the definition of “success” exclusively inside `data-evals` scripts that other repos cannot run.

---

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

**MUST:** A contract‑change PR MUST include:

- decision owner approval,
- updated fixtures when applicable,
- updated codegen artifacts when applicable,
- explicit change classification and evolution plan (Section 9).

##### 6.3 Producer/consumer responsibilities

- **Producer MUST:** implement the contract, provide compliance tests, document non‑schema semantics.
- **Consumer MUST:** tolerate backward‑compatible changes and MUST NOT invent undocumented interpretations.

Forward‑compatibility guidance:

- **SHOULD:** Consumers ignore unknown fields by default.
- **SHOULD:** Producers do not break consumers by tightening validation without a migration window.

**Security exception:** At internet‑facing boundaries, strict decoding MAY be required to prevent request smuggling and unsafe deserialization. If you choose strict decoding, you MUST pair it with explicit versioning/negotiation so forward evolution remains possible.

##### 6.4 Drift prevention

At least one of the following MUST exist per boundary:

- producer‑side schema validation tests
- consumer‑side decoding tests using fixtures
- end‑to‑end contract tests in the integration harness

**SHOULD:** Critical boundaries have at least two layers (e.g., producer validation + consumer decoding).

---

#### 7. Contract representation and tooling

##### 7.1 Canonical formats (and SSOT discipline)

Pick formats that support tooling and mechanical enforcement, but avoid dual-authoring.

**MUST:** For any boundary surface, the project MUST designate exactly one **authoring SSOT** (single source of truth). If multiple representations exist, one MUST be declared SSOT and the others MUST be treated as generated or publishing artifacts with drift checks.

**Recommended format split (authoring vs publishing):**

- **HTTP/REST**
  - **Authoring (recommended):** `contracts/api` machine-readable endpoint inventory plus payload schemas (JSON Schema / Protobuf), identifiers, and fixtures/tests.
  - **Publishing/interchange:** generated **OpenAPI 3.x** snapshots for SDKs/docs, kept read-only.
  - **Exception (OpenAPI-first):** OpenAPI MAY be the authoring SSOT, but only if linting, breaking-change checks, and code/schema consistency gates are enforced.
- **gRPC**
  - **Authoring:** Protobuf (`.proto`) plus fixtures and compatibility runners.
  - **Publishing:** generated SDKs and docs.
- **Events / callbacks / streams**
  - **Authoring:** JSON Schema / Protobuf / AsyncAPI (choose one) plus fixtures and replay/compat runners.
  - **Publishing:** generated docs and consumer SDKs (optional).
- **Identifiers**
  - **Authoring:** typed enums/constants (format is language-agnostic; TS/JSON/etc. are acceptable).
  - **Publishing:** derived JSON/Markdown tables if needed.

**SHOULD:** Avoid “schema in prose only.” If it cannot be validated, it will drift.
**SHOULD:** Every cross-boundary schema or API surface SHOULD have a stable semantics reference. Semantics MAY live in schema descriptions, but they SHOULD also be linkable as a dedicated doc such as `contracts/semantics/<contract_id>.md`.

##### 7.2 Shared error taxonomy (avoid dependency deadlocks)

Cross‑cutting error **definitions** (codes/kinds/fields) SHOULD live in `contracts` so every repo can interpret errors without importing producer implementation modules.

**MUST:** `contracts` defines only portable representations and fixtures.
**MUST:** Each repo implements its own exception/error classes and mapping locally.

**MAY:** Publish a tiny, dependency‑light generated helper library per language that exports only:

- DTOs/types/interfaces
- schema validators
- predicate helpers (pure functions)
- pure mapping helpers (data‑in/data‑out)

Helper library constraints:

- **MUST:** Be generated from contract artifacts.
- **MUST:** Be usable without network/persistence I/O.
- **MUST:** Avoid runtime dependencies that risk duplication or dependency cycles.
- **MUST NOT:** Export runtime exception/error classes (e.g., classes extending `Error`/`Exception`).
- **MUST:** If “constructors” are provided, they construct **data representations** (portable error envelopes), not runtime throwables.

##### 7.3 Contract metadata

Each contract artifact SHOULD include machine‑readable metadata:

- decision owner
- stability tier (`proposed` / `experimental` / `stable` / `deprecated`)
- evolution mode (Compatibility Mode by default)
- version + changelog pointer
- required checks (fixtures, producer validation, consumer decoding)

**Important:** Contract hub **main** should represent what is safe to rely on in shared environments. Use `proposed`/`experimental` tiers for contracts that are not yet broadly deployed.

##### 7.4 Code generation (strongly recommended)

Hand‑written DTOs drift across languages.

**SHOULD:** Generate:

- TypeScript clients/types for frontend
- server‑side DTOs/validators/models for backend (where practical)
- Pydantic models (or equivalent) for algo

**MUST:** Generation is reproducible:

- pinned tool versions
- deterministic output
- CI verifies reproducibility

**MUST:** Generated code is not manually edited.

**MUST:** Generated artifacts are clearly separated from hand‑written code (path + header markers) so AI agents do not “helpfully refactor” generated output.

##### 7.5 Golden fixtures

For high‑impact contracts, store fixtures in `contracts/fixtures/*`:

- request examples
- success responses
- error responses
- stream chunk examples
- callback payload examples

Fixtures MUST be:

- scrubbed of secrets and PII,
- stable (avoid timestamps unless required; use placeholders),
- executed by automated tests.

---

#### 8. Publishing and consuming contracts

A contract hub only helps if every repo can consume contracts deterministically.

##### 8.1 Versioning policy

**SHOULD:** Version contract artifacts using Semantic Versioning (SemVer):

- **MAJOR**: breaking changes that impact independently deployed producers/consumers (Compatibility Mode).
- **MINOR**: additive backward‑compatible changes.
- **PATCH**: clarifications, fixture additions, and bug fixes that do not change compatibility.

**Clarification:** If a contract change is merged but not yet broadly deployable, keep it in `proposed`/`experimental` tier and avoid advertising it as stable capability. Do not “publish stable” contracts that no producer supports.

##### 8.2 Choose one primary consumption mechanism

Pick one primary mechanism; allow exceptions only with explicit documentation.

1) **Versioned package artifacts (recommended)**
   - publish language‑specific packages (npm/Maven/PyPI or internal registries)
   - consumers pin a version and upgrade explicitly

2) **Git tag + submodule/subtree**
   - consumers pin a tag/commit

3) **Vendor snapshot (least preferred)**
   - copy generated outputs into each repo
   - acceptable only if automation keeps it synchronized and CI verifies synchronization

**MUST:** Consumers MUST be able to build/test without relying on “latest.” Pin to a version/tag/commit.

##### 8.3 Upgrade cadence

**SHOULD:** Upgrade contracts on a predictable cadence (daily/weekly) or per feature, but keep upgrades small and require compatibility checks.

**MUST:** If a consumer upgrades contracts, it MUST run the required compatibility checks (fixtures decoding and/or integration harness).

---

#### 9. Contract evolution

Contracts can and should evolve. In multi‑repo systems, evolution MUST assume partial upgrades.

##### 9.1 The core constraint

Even inside a single repo, deployments are often rolling; across repos, partial upgrades are the norm.

**MUST:** Treat cross‑service contracts as Compatibility Mode unless you have an enforced atomic cutover that prevents mixed versions.

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

**Correction:** “Contract‑first” is a design discipline, not a mandate to publish a new stable contract version before any implementation exists.

Recommended practical ordering (Compatibility Mode):

- **Additive response fields (producer → consumer):**
  1) producer starts emitting the field (optional),
  2) contract/fixtures updated and released,
  3) consumers start using it.

- **Additive request fields (consumer → producer):**
  1) producer becomes tolerant and/or implements new behavior behind a feature flag,
  2) contract/fixtures updated and released,
  3) consumers start sending the field.

- **New endpoint/topic:**
  1) producer implements and deploys,
  2) contract/fixtures released,
  3) consumers integrate.

- **Breaking change:**
  - MUST follow expand/contract with a compatibility window (dual‑read/dual‑write or versioned surface).

##### 9.5 Compatibility strategies

For breaking changes in Compatibility Mode, provide an explicit strategy:

- versioned surface (`/v2`, versioned topics, or `schemaVersion`)
- content negotiation (headers)
- dual‑read/dual‑write within a defined window

The strategy MUST include:

- a cutoff (date/release),
- fixtures/tests for both old and new,
- a migration plan for stored data (if applicable).

---

#### 10. Internal modularization: keep each repo AI‑sized

Multi‑repo boundaries keep cross‑repo work bounded. Each repo still needs internal boundaries.

##### 10.1 Frontend

**SHOULD:** Use a single‑deploy modular structure (app shell + internal packages with strict dependency rules).

##### 10.2 Backend

**SHOULD:** Use a modular monolith:

- one deployable backend unless a runtime split is justified
- domain modules with explicit boundaries
- enforced import rules
- “ports and adapters” for side‑effectful integrations

**MUST:** Backend owns canonical validation and canonical error mapping.

##### 10.3 Algo/model service

**SHOULD:** Structure for bounded AI edits:

- `adapters/` (decode/encode, schema validation, mapping)
- `pipelines/` (prompt pipelines and orchestration)
- `prompts/` (versioned prompts, prompt IDs)
- `tools/` (tool adapters with strict allowlists and quotas)
- `evals/` (fast deterministic checks + offline eval hooks)

**MUST:** Validate outputs at the boundary before emitting responses/callbacks.

**MUST:** Record `requestId`, `promptId`, and `modelId` (or equivalent) in logs for every user‑visible output.

---

#### 11. Integration harness: the system truth source

**SHOULD:** Maintain an integration harness (repo or pipeline) that provides:

- one‑command local startup (compose)
- smoke tests for critical end‑to‑end flows
- contract compatibility runners using fixtures

**MUST:** Any cross‑repo contract change must be verifiable via:

- the integration harness (preferred), or
- fixture‑based compatibility checks that the harness runs.

**SHOULD:** For independently deployed systems, maintain a compatibility matrix (producer version × consumer version) for at least the supported window.

---

#### 12. AI‑assisted development workflow

##### 12.1 AI task template (MUST)

Every AI task MUST include:

1) **Repo scope**
   - which repo(s) may change
   - which folders are in scope
   - explicit exclusions

2) **Contract references**
   - impacted specs + fixtures
   - invariants that must remain stable
   - change classification (additive/behavioral/breaking)
   - evolution mode (Compatibility Mode unless proven otherwise)

3) **Determinism & replay**
   - determinism tier (`tier0`/`tier1`/`tier2`) and what must be deterministic
   - required replay harness / golden fixtures (if Tier 0/Tier 1)
   - pinned DatasetManifest(s) for any eval gates

4) **Budgets**
   - what budgets are enforced/changed (tokens, time, external calls, cost)
   - budget scope (stage/tool/pipeline) and termination behavior

5) **Acceptance criteria / verification**
   - exact commands to run (lint/typecheck/test/build/eval/replay)
   - required artifacts (updated spec/fixtures, regenerated code)
   - smoke flow expectations

6) **Non‑goals**
   - forbid opportunistic refactors
   - forbid renaming public identifiers
   - forbid dependency upgrades unless requested

##### 12.2 Change sequencing across repos

**SHOULD:** For cross‑repo work, use a “contract PR” plus per‑repo implementation PRs.

**MUST:** Do not merge consumer changes that depend on non‑deployed producer behavior unless:

- the consumer is tolerant (feature‑flagged, default‑off), and
- there is a defined rollout plan.

##### 12.3 Keep AI changes small and reversible

**SHOULD:**

- prefer many small PRs over one large PR
- ensure each PR is mergeable and releasable
- avoid long‑lived branches where contracts drift

**MUST:** If a PR changes a contract, it MUST also change at least one automated check proving enforcement (fixture/test/codegen output).

##### 12.4 AI guardrails for cross‑repo work

**MUST:** For any task that touches more than one repo, require:

- integration harness run (or fixture‑based compatibility run),
- explicit contract version pin updates,
- documented rollout/compatibility plan if breaking behavior is introduced.

---

#### 13. Efficiency and overhead management

Splitting into multiple repos can increase development overhead if unmanaged.

##### 13.1 Typical regressions

- coordination overhead (version bumps)
- fragmented CI feedback loops
- contract drift due to ad‑hoc upgrades
- duplicated tooling/config
- slower onboarding (more moving pieces)

##### 13.2 Mitigations

**SHOULD:**

- automate contract publish + consumer upgrade PRs (bot‑opened PRs)
- keep one integration harness with smoke tests and version pins
- standardize repo interfaces (Section 15)
- keep runtime services minimal
- cache CI builds/tests aggressively

---

#### 14. Reliability and security patterns for AI workloads

##### 14.1 Prefer backend‑orchestrated model calls

Prefer:

- frontend → backend
- backend → algo
- backend returns canonical responses

Direct frontend → algo calls MAY be acceptable for prototyping or trusted intranet deployments, but increase attack surface and contract complexity.

##### 14.2 Long‑running operations

Use explicit job patterns when work exceeds interactive budgets:

- job creation → status polling/stream → completion
- best‑effort cancellation
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
- showing user‑visible results (unless explicitly marked “draft/unverified”).

If validation fails:

- retry with constrained prompts where safe,
- fall back to partial/manual flow where required,
- log and surface the failure with correlation IDs.

##### 14.5 Security and secrets

**MUST:**

- no secrets in git (keys, tokens, private URLs)
- secrets are injected via secret managers or environment variables
- run secret scanning in CI

**SHOULD:** Treat prompt templates, tool configurations, and retrieval sources as security‑sensitive.

##### 14.6 Observability and correlation

**SHOULD:** Propagate correlation identifiers across:

- frontend request headers,
- backend logs and traces,
- algo logs,
- callbacks/webhooks.

**MUST:** Every cross‑repo request/response includes a `requestId` (or equivalent) that can be traced end‑to‑end.

---

#### 15. Repo interface standard (AI‑friendly)

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

---

#### 16. Minimum CI gates

##### 16.1 Per‑repo minimum

Every repo MUST have CI that runs its `verify` entrypoint.

**SHOULD:** CI output is stable and machine‑readable so AI agents can use it as feedback.

##### 16.2 System‑level gates

At least one pipeline (often in `integration`) MUST provide:

- end‑to‑end smoke tests
- breaking‑change detection for APIs/events (spec diffs)
- fixture decoding tests for consumers

##### 16.3 AI behavior gates (when applicable)

If model outputs affect users, you SHOULD add at least one of:

- schema compliance rate checks
- a small offline eval set with pass/fail thresholds
- latency budget checks for critical pipelines
- regression detection for “repair rate”

---

> Note: In the source document, the following sections were labeled “Appendix A–D”. In the unified standard, they are labeled “Annex E-A–E-D” to avoid collisions with the standard’s top-level Appendices.

#### Annex E-A — “Split into a new repo?” checklist

Split into a new repo only if all are true:

- the boundary has a clear contract
- the contract can be tested automatically
- there is independent ownership/deployment need OR language/runtime mismatch
- the split materially reduces AI task scope
- an integration harness exists to catch drift

If not, prefer modularizing inside an existing repo.

---

#### Annex E-B — Contract change checklist

Every contract change PR SHOULD include:

- updated spec/schema
- updated fixtures (happy path + common failure)
- change classification and compatibility plan
- producer implementation + tests (or a staged rollout plan)
- consumer updates if required (or explicit compatibility window plan)
- integration smoke test update for critical boundaries
- version bump (SemVer) + changelog entry

---

#### Annex E-C — AI ticket checklist (copy/paste)

1) Scope: repo(s) + folders + explicit exclusions
2) Contracts: spec paths + fixture names + invariants + evolution mode
3) Deliverables: code + tests + fixtures + regenerated clients
4) Verification: exact commands to run + smoke flow
5) Non‑goals: no refactors, no renames, no dependency upgrades

---

#### Annex E-D — Minimal contract hub layout (example)

A practical `contracts` repo layout:

```
contracts/
  api/                    # recommended machine-readable endpoint inventory (method/path/auth/status codes)
    public.(ts|json)
    algo.(ts|json)
  openapi/
    public-api.yaml       # optional generated snapshots for publishing/SDKs (DO NOT EDIT by hand)
    algo-api.yaml
  schemas/
    errors.schema.json
    job-envelope.schema.json
    stream-message.schema.json
  semantics/
    errors.md
    job-envelope.md
    stream-message.md
  fixtures/
    public-api/
      entity.create.request.json
      entity.create.response.json
      error.401.json
    algo/
      outline.request.json
      outline.response.json
      stream.chunk.json
  identifiers/
    error_codes.(json|ts)
    permission_codes.(json|ts)
    job_types.(json|ts)
  codegen/
    generators/
      openapi-generator.json
  scripts/
    verify
    compatibility_runner
    codegen
  CHANGELOG.md
  README.md
```

**SHOULD:** Keep `contracts` dependency‑light. It should be a “lowest layer” repo that is safe for every other repo to consume.

---
