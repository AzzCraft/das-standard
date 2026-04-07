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
1. Update this Master Doc, bump its version, and update branch copies per **Annex C-C**.

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

Annexes:
- Annex C-A - AI Guide: Converting a PRD into this Master Doc (#annex-c-a---ai-guide-converting-a-prd-into-this-master-doc)
- Annex C-B - Template Snippets (copy/paste) (#annex-c-b---template-snippets-copypaste)
- Annex C-C - Branch Copies and Sync Policy (#annex-c-c---branch-copies-and-sync-policy)
- Annex C-D - UI Spec Appendix (reference) (#annex-c-d---ui-spec-appendix-reference)

#### 0. Document Control

##### 0.1 Metadata (required)

- **Project / Product name**: `{{PROJECT_NAME}}`
- **Codename** (optional): `[[CODENAME]]`
- **Project slug** (stable identifier; lowercase kebab-case recommended): `{{PROJECT_SLUG}}` (recommended: `my-product`)
- **Canonical doc path** (MUST be stable across branches): `{{DOC_PATH}}` (recommended: `docs/master_doc.md`)
- **Context Pack path** (recommended): `[[CONTEXT_PACK_PATH]]` (recommended: `docs/context-pack.md`)
- **Doc set / sub-doc registry path** (optional): `[[DOC_SET_REGISTRY_PATH]]` (recommended: `docs/docs_index.md`)
- **Doc ID** (stable identifier): `{{DOC_ID}}` (recommended: `MASTER-{{PROJECT_SLUG}}`)
- **Supersedes** (optional): `[[DOC_ID@VERSION]]` (previous master doc if this doc replaces another)
- **Superseded by** (optional): `[[DOC_ID@VERSION]]` (fill when deprecating this doc)
- **Migration mapping** (optional): `[[PATH_OR_URL]]` (ID remap table / migration notes)

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
- If `{{CONFORMANCE_PROFILE}} = L2`, the Context Pack (`[[CONTEXT_PACK_PATH]]`) exists and is updated for this revision (scope, invariants, contracts summary, `verify`, and current tasks).
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
| --- | --- | --- | --- | --- | --- | --- | --- |

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
| backend <-> db | N | Y | Y | {{SCHEMA_IDS}} | expand/contract | {{NOTES}} |

##### 4.4 Environments & deployment pipeline (required for L1/L2; recommended for L0)

> Define dev/staging/prod (and any preview/canary/shadow envs) as first-class engineering surfaces.

Rules:

- Same build artifact SHOULD be promoted across environments (config changes only).
- Each environment MUST declare allowed data classification (no production PII in dev by default).
- Rollback strategy MUST be explicit (what is reversible vs not).

**Environment matrix (required for L1/L2)**

| Environment | Purpose | Data class allowed | External deps mode | Deployment method | Rollback plan | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| local | developer machine | synthetic only | stubbed | `docker compose up` | `git reset` | |
| dev | feature testing | masked/synthetic | mixed | CI deploy | redeploy | |
| staging | release candidate | prod-like (masked) | prod-like | promotion | rollback + runbook | |
| prod | real users | production | production | promotion | rollback + incident | |

**Deployment pipeline (required for L1/L2)**

- Build artifact(s): `{{IMAGE/ARTIFACT}}`
- Promotion rule: `{{SAME_ARTIFACT_OR_REBUILD}}`
- DB migrations: `{{EXPAND_CONTRACT_STRATEGY}}`
- Queue/event compatibility: `{{STRATEGY}}`
- Feature flags: `{{FLAGS_POLICY}}`
- Runbooks: `{{LINKS}}`

##### 4.5 External dependencies & vendor integrations (required if any)

> Treat vendors (cloud managed services, AI APIs, third-party systems) as explicit dependencies with contracts and failure modes.

| Dependency/Vendor | Purpose | Contract surface | Auth | Rate limits | Data policy | SLA/SLO | Fallback / degraded mode | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| {{VENDOR}} | {{PURPOSE}} | {{API/SCHEMA/WEBHOOK}} | {{METHOD}} | {{LIMITS}} | {{PII/RETENTION}} | {{SLA}} | {{FALLBACK}} | {{TEAM}} |

Required notes:

- **Test strategy:** `{{STUB/SNAPSHOT/LIVE}}` (CI SHOULD avoid live vendor calls).
- **Cost controls:** budgets, quotas, and alerting.
- **Operational ownership:** on-call and escalation path.


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

**Semantics ref guidance (recommended):** Use a stable pointer.
- For payload/interface invariants (defaults, validation rules, redaction, status-code mapping), prefer `contracts/semantics/<contract_id>.md`.
- For end-to-end behavioral semantics (workflows, acceptance criteria), reference the relevant scenario/spec section (e.g., `specs/<spec_id>#<anchor>` or an equivalent BDD artifact).
- Avoid duplicating the endpoint inventory in freeform specs when `contracts/api` is the SSOT.

##### 5.3 API contracts (HTTP / RPC / Webhooks)

**Recommended:** Treat `contracts/api/` as the machine-readable **API Registry** (preferred authoring SSOT). This table SHOULD act as a human-readable index: list stable API IDs and reference the canonical registry entry or OpenAPI artifact to avoid dual-authoring drift.

| API ID | Canonical ref | Endpoint / Method | Auth | Status codes | Purpose | Request schema | Response schema | Error codes | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

> **SSOT rule:** If multiple representations exist (e.g., `contracts/api` registry, OpenAPI, and/or separate request/response schemas), you MUST declare exactly one as the authoring SSOT. All others MUST be generated (or mechanically checked) to prevent drift.


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

- Primary database engine: `{{DB_ENGINE}}` (example: `PostgreSQL`)
- Primary database version: `{{DB_VERSION}}` (example: `16`)
- Migration tooling + location: `{{MIGRATION_TOOLING}}` (example: `Prisma migrations at backend/prisma/migrations/`)
- Migration policy (expand/contract; rollback posture): `{{DB_MIGRATION_POLICY}}`
- Vector database: `[[TYPE]]`
- Object storage: `[[TYPE]]`
- Caching: `[[TYPE]]` with key/version policy (cache keys are contracts)

> Note: DB rows are persisted contract surfaces; schema changes MUST follow Compatibility Mode rules (expand/contract with a window).

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

| Task ID | Description | Scope (paths) | Contracts touched | Tests/verify | Owner | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-001 | `[[TASK_DESCRIPTION]]` | `[[PATHS]]` | `[[CONTRACT_IDS]]` | `[[VERIFY_COMMANDS]]` | `[[OWNER]]` | planned | `[[PR_OR_COMMIT_OR_TEST_REPORT]]` |

**Status vocabulary (recommended):** `planned | in_progress | blocked | partial | done`

- **MUST:** Every task starts as `planned`.
- **MUST:** A task marked `partial` or `done` MUST include objective Evidence (PR link, commit SHA, test report path, or CI run URL).
- **SHOULD:** If a task is `blocked`, record the blocking dependency in §0.8 (Decision log) or §0.11 (Traceability index).


##### 11.3 Acceptance checklist (Definition of Done)

- [ ] All referenced FRs implemented and tested
- [ ] Contract artifacts updated (schema + semantics + fixtures + checks) if applicable
- [ ] Integration smoke tests pass
- [ ] No unapproved scope creep
- [ ] Release notes / change log updated
- [ ] Master Doc updated **if required** (requirements/workflows/contracts/topology/gates changed), or explicitly marked as “no doc change required”.

##### 11.4 Multi-worker implementation protocol (recommended when parallelizing)

If implementation is split across multiple workers (human or AI), the project MUST pick one of the following models and follow its rules to avoid contract drift and merge conflicts.

**Model A — Central coordinator (recommended):**

- A single coordinator (human or AI) owns **contract changes** (`contracts/*`) and integration sequencing.
- Workers implement in parallel **only on non-overlapping scopes** (module- or folder-level slices).
- Contract changes MUST be serialized (one active PR touching `contracts/` at a time), or guarded by explicit locks (see below).

**Model B — Federated (allowed only with mechanical locks):**

- Any worker MAY propose contract changes, but MUST acquire an explicit lock before editing SSOT files (e.g., `contracts/LOCKS/<path>.lock` or an equivalent repo policy).
- Locks MUST be released in the same PR that merges the change.

**Rules (apply to both models):**

- **MUST:** Each worker works on a separate branch/PR. Direct commits to shared branches are forbidden.
- **MUST:** No two concurrent tasks may edit the same SSOT file (schema/identifier/api registry) unless they are in the same PR.
- **MUST:** Every PR that changes boundary behavior MUST update the relevant contracts and fixtures, and MUST pass `verify` (per §11.1) before merge.
- **SHOULD:** Use the integration harness as the final arbiter for cross-repo drift (see §3.6).


#### Annex C-A - AI Guide: Converting a PRD into this Master Doc

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

#### Annex C-B - Template Snippets (copy/paste)

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

| Task ID | Description | Scope (paths) | Contracts touched | Tests/verify | Owner | Status | Evidence |
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

#### Annex C-C - Branch Copies and Sync Policy

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

#### Annex C-D - UI Spec Appendix (reference)

This Master Doc template is designed to be copied into a repo as a standalone `master_doc.md`. To avoid maintaining the **UI Spec Appendix template** in two places, this appendix intentionally contains only a reference.

If the project has user-facing UI, you MUST maintain a UI Spec Appendix using the template in **Docs as Software (DAS) Standard {{ENGINEERING_STANDARD_VERSION}}, Appendix D**.

- Repo-local UI Spec Appendix path (fill in): `{{UI_SPEC_APPENDIX_PATH}}` (recommended: `docs/ui_spec_appendix.md`)
- Standard reference (fill in): `{{ENGINEERING_STANDARD_PATH_OR_URL}}#appendix-d-ui-spec-appendix-template-v1`
  - If your doc host does not support anchors, search within the standard for `appendix-d-ui-spec-appendix-template-v1` or for the heading `Appendix D - UI Spec Appendix Template`.

Minimal procedure:

1. Create `{{UI_SPEC_APPENDIX_PATH}}` in the repo.
1. Copy the template from the standard’s Appendix D into that file.
1. Link to it from §1.8 (UI screen inventory & workflows).
