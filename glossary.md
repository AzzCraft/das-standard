# DAS Glossary

Definitions of standard terms used within the Docs as Software (DAS) ecosystem. These terms are normative; they must be used consistently in code, documentation, and architecture diagrams.

## Core Engineering Concepts

### SDMM (Single-Deploy Modular Engineering)
An architecture discipline where a codebase is split into many independently understandable modules (for local reasoning) but built and shipped as a single deployable unit (for operational simplicity). It relies on strict boundary enforcement to prevent coupling.

### Docs as Software (DAS)
The methodology of treating documentation and specifications with the same rigor as software code, including version control, automated linting, testing, and release gating.

### Boundary (Repo vs. Runtime)
* **Repo Boundary:** A source-control separation (different Git repositories) used to manage change scope and ownership. Does not imply network latency.
* **Runtime Boundary:** A deployment separation (different processes/services) that introduces network hops and distributed failure modes.

### Integration Harness
The canonical repository or pipeline that wires the system together to run end-to-end smoke tests and contract compatibility checks. It serves as the "System Truth" source.

## Contracts & Evolution

### Contract Surface
Any interface that is **externally observed** (by another team/repo) or **persisted** (read later). Examples: APIs, Event Schemas, DB Rows, Logs. By default, these surfaces operate in **Compatibility Mode**.

### Compatibility Mode
The evolution state where producers and consumers do **not** ship atomically (e.g., rolling deploys, separate repos). Changes must be additive, and breaking changes require a compatibility window (expand/contract).

### Refactor Mode
The evolution state where a boundary behaves "atomically" (e.g., strictly internal modules). Breaking changes are allowed because all callers are updated in the same atomic commit/deploy.

### Tolerant Reader
A design pattern where a consumer explicitly ignores unknown fields in a payload. This is a **MUST** for consumers in Compatibility Mode to allow producers to add new fields without breaking the system.

### Contract Hub
The canonical repository (or module) that stores the "Source of Truth" for all shared schemas, identifiers, fixtures, and executable checks. It must not contain business logic.

## AI & Execution Artifacts

### RunManifest
An immutable, persisted artifact that records **"Why a result was produced."** It captures input snapshots, configuration hashes, software versions, determinism tiers, and budget outcomes for a specific execution of an algorithm.

### JobEnvelope
The canonical backend object that wraps an algorithm's execution. It tracks the orchestration state (queueing, retries, cancellation) and contains the `PipelineResult`.

### PipelineResult
The standardized output envelope of an AI algorithm or pipeline. It must be losslessly wrappable into a `JobEnvelope`.

### DatasetManifest
An immutable, versioned record that pins evaluation inputs (provenance, license, content hash) to ensure reproducible scoring.

### ConfigId
An immutable identifier for a specific configuration snapshot used by a run or job. Required for reproducibility and rollback.

### SideEffectsMode
A control flag passed to algorithms to determine safety:
* `dryRun`: No external writes/mutations allowed.
* `sandbox`: Writes allowed only to isolated sandbox namespaces.
* `live`: Production writes allowed.

### Determinism Tier
A declaration of reproducibility for an AI pipeline:
* **Tier 0:** Replayable only via recorded cassettes (non-deterministic external dependencies).
* **Tier 1:** Stable given pinned dependencies/inputs.
* **Tier 2:** Bitwise deterministic (identical outputs).

## Operational Terms

### Hard Budget
A resource limit (tokens, time, cost) that, when reached, **stops work** immediately to prevent runaway costs. Must result in a terminal job state.

### Soft Budget
A resource threshold that, when exceeded, triggers alerts/logs but allows the work to complete. Used for cost governance.

### Canonical Validation
The principle that the **Backend (System of Record)** is the final authority on data validity. While UI and Algo services may pre-validate, the Backend performs the authoritative check.

### Golden Fixture
A "Known Good" data file used to test contracts. It represents a valid payload that Producers promise to emit and Consumers promise to understand.

## Roles

### Decision Owner
The single party that defines contract semantics and approves changes to that contract. (See Appendix G §0.3).