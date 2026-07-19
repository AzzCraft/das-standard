# Appendix J - BDD scenarios + verification playbook

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

```gherkin
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

```gherkin
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
