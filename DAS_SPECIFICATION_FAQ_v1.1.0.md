# DAS Standard FAQ (v1.1.0)

This FAQ is a companion to **The Docs as Software (DAS) Standard** v1.1.0. It captures (a) clarifications introduced in the v1.1.0 update and (b) common questions teams run into when adopting the standard.

---

## 1) What changed in v1.1.0?

v1.1.0 is a **minor** release: it focuses on **clarity, internal consistency, and drift-prevention ergonomics**. It does not change the core methodology.

Key fixes and clarifications:

- **Metadata consistency**
  - Updated the version badge and “Last updated” date to match v1.1.0.

- **Conformance profile guidance**
  - Moved and clarified the “L0 requires explicit deferrals + ownership + revisit trigger/date” rule so it is clearly part of **conformance profiles**, not the HFVI interaction profile section.

- **UI Spec Appendix anchor/reference correctness**
  - Corrected the “search for the heading” instruction so it matches the actual Appendix D heading text, while keeping the `appendix-d-ui-spec-appendix-template-v1` anchor stable.

- **Contract Hub layout consistency**
  - Updated Appendix E’s “minimal contract hub layout” example to match the standard’s recommended structure:
    - includes `api/` (API registry) and `identifiers/`
    - treats `openapi/` as an **optional generated artifact** (read-only), not an authoring source

- **Reduced ambiguity around `contracts/` naming**
  - Clarified that repo-local folders named `contracts/` (inside frontend/backend code) are typically **generated/imported types + adapters**, and are **not** the SSOT Contract Hub in multi-repo systems.
  - Added guidance to prefer names like `contract_types/` when ambiguity is likely.

- **Master Doc template improved to prevent SSOT drift**
  - Expanded the Master Doc’s “API contracts” table to include:
    - a **Canonical ref** column (contracts/api or OpenAPI SSOT)
    - **Auth** and **Status codes** fields (common sources of drift)
  - Added explicit guidance that the table should act as an **index**, not a second SSOT.

- **Fixed an incorrect internal reference**
  - Corrected a reference that incorrectly pointed to “Appendix E §3.6” (which does not exist) to point to **§3.6** (Integration harness requirements).

---

## 2) Does DAS require a specific backend framework, language, or database?

No. DAS is **technology-agnostic** at the “vendor/framework” level.

What it *does* require:

- explicit repo boundaries and ownership rules
- contract discipline (schema + semantics + fixtures + executable checks)
- compatibility discipline on externally observed or persisted surfaces
- deterministic/replayable practices for AI workflows where applicable

Where you specify concrete choices:

- In the **Project Master Doc** template (Appendix C), you declare:
  - primary language(s)
  - primary database engine
  - hosting/runtime assumptions
  - repos/topology

---

## 3) What is the “single source of truth (SSOT)” rule, in plain terms?

If the same “truth” exists in two formats, one will drift.

DAS requires you to pick **exactly one authoring SSOT** per boundary surface, and treat everything else as:

- generated artifacts, or
- mechanically checked derivatives

Examples:

- If you author request/response schemas in JSON Schema, and also have OpenAPI:
  - **either** JSON Schema is SSOT and OpenAPI is generated/checked
  - **or** OpenAPI is SSOT and JSON Schemas are generated/checked
  - but you must not “hand-maintain both” without drift enforcement

---

## 4) Do we need to hand-write OpenAPI YAML?

Not necessarily — and often **you should not**.

Recommended patterns:

- **Code-first frameworks**: generate OpenAPI from code/decorators; publish it as a read-only artifact.
- **Contract-first**: OpenAPI can be SSOT, but only with:
  - linting
  - breaking-change detection
  - client/server consistency gates
  - compatibility-mode rollout discipline

In all cases: avoid dual-authoring without drift checks.

---

## 5) What is `contracts/api/`? Do we have to use it?

`contracts/api/` is the recommended home for a **machine-readable endpoint inventory** (an API registry) that captures what payload schemas alone cannot:

- method/path
- authentication and authorization requirements
- status code matrix
- idempotency/streaming/upload semantics (as applicable)

Whether it is mandatory depends on your topology and risk tolerance:

- **Multi-repo / multiple teams / external consumers**: strongly recommended.
- **Small monorepo / tightly coupled**: optional, but still useful as systems scale.

If you do not use `contracts/api/`, you must still store those semantics somewhere verifiable and drift-resistant.

---

## 6) Where do error codes and permission codes live?

In **identifier contracts** (e.g., `contracts/identifiers/`).

These are contracts because they appear in:

- UI states and user-visible behavior
- logs, dashboards, and monitoring
- cross-boundary payloads (backend ↔ frontend/algo)
- replay fixtures and evaluations

They must be stable and versioned like schemas.

---

## 7) How do we represent “implemented vs planned vs partial” work?

Use the **WBS table** in the Master Doc template (§11.2 in Appendix C).

Recommended status vocabulary:

- `planned | in_progress | blocked | partial | done`

Rules:

- everything starts `planned`
- `partial` and `done` require objective evidence (PR link, commit SHA, CI run link, or test report path)

This makes progress auditable and prevents “silent partial implementations.”

---

## 8) How do we avoid conflicts when multiple workers (humans or AIs) implement in parallel?

Follow the Master Doc’s **Multi-worker implementation protocol** (§11.4 template):

- **Model A (Central coordinator)**: one owner serializes contract changes; workers implement disjoint scopes.
- **Model B (Federated with locks)**: workers can edit SSOT files only with explicit locks.

Non-negotiables:

- no two concurrent tasks edit the same SSOT file unless in the same PR
- contract changes require fixtures + checks and must pass verify gates

---

## 9) Where should “how to implement” details live vs “what to build” requirements?

- **Master Doc**: “what” (requirements, workflows, contracts, gates, plan)
- **Implementation code**: “how”
- **Appendices**: standardized templates, checklists, and playbooks

Avoid putting deep implementation details in the Master Doc; keep it execution-ready but not code-heavy.

---

## 10) What if we create a new Master Doc by merging two systems’ docs?

Treat it as a **controlled migration**:

1. Create a new document with a new Doc ID and version.
2. Preserve stable IDs from System A; prefix/remap IDs from System B to prevent collisions.
3. Build a consolidated Contracts Index and update ownership.
4. Add a migration plan (data, traffic, and compatibility considerations).
5. Use the Doc lineage fields:
   - `Supersedes` / `Replaces`
   - baseline version fields for branches

---

## 11) What should we do when the DAS standard itself updates (e.g., v1.0.0 → v1.1.0)?

Recommended process:

1. **Update the standard reference** in each project’s Master Doc (standard version + link/path).
2. Create a “Standard migration task” in the WBS:
   - list affected repos and contracts
   - list verification commands
   - specify what must change (if anything)
3. Apply changes in a PR that includes:
   - doc updates (Master Doc / appendices)
   - contract updates (if needed)
   - code changes (if needed)
   - verify evidence

Patch releases usually require minimal changes; minor/major releases may require explicit refactors.

---

## 12) When do we need Appendix D (UI Spec Appendix)?

If the project has user-facing UI (web/mobile/admin), you **must** maintain Appendix D (or a repo-local copy based on it).

The UI Spec Appendix is the place to specify:

- screen inventory and key states
- flows/workflows
- error and empty-state behavior
- accessibility requirements
- integration points with backend/algo
- (if HFVI) references from screens to VIS scene IDs

---

## 13) When do we need Appendix K (HFVI / VIS)?

If the project’s Master Doc declares:

- `interactionProfile = hfvi_canvas_webgl_game`

Then Appendix K is **normative** and required for each HFVI surface.

It provides the structure needed to keep spatial/temporal behavior implementable and testable, including:

- coordinate systems and transforms
- z-order/layering rules
- input mapping
- invariants
- debug overlay requirements
- replay + visual regression gates

---

## 14) Common adoption pitfalls

- Maintaining both OpenAPI and schema files by hand without drift checks.
- Not fixture-backing contracts (schemas without golden examples).
- Treating identifiers as “just strings” instead of stable contracts.
- Forgetting that persisted artifacts (job envelopes, run manifests) are contracts too.
- Skipping an integration harness in multi-repo systems.
- Allowing contract changes to happen in parallel without locks or a coordinator.
- Putting ambiguous “design intent” in prose without concrete acceptance criteria or invariants.

---

## 15) Quick pointers: “Where do I put X?”

- **User workflow requirements** → Master Doc (Appendix C template), §3–§7
- **API endpoint inventory** → `contracts/api/` (recommended)
- **Payload schemas** → `contracts/schemas/`
- **Golden samples** → `contracts/fixtures/`
- **Error/permission/job enums** → `contracts/identifiers/`
- **OpenAPI for publishing** → `contracts/openapi/` (generated, read-only)
- **UI screens/states/flows** → UI Spec Appendix (Appendix D or repo-local copy)
- **HFVI scenes/entities/invariants** → VIS (Appendix K or repo-local copy)
- **Verification commands** → Master Doc §11 + repo scripts (`verify`, `verify --full`, etc.)

---

## 16) If something in the FAQ conflicts with the standard, which wins?

The standard wins. This FAQ is explanatory; the standard is normative.
