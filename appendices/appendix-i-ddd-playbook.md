# Appendix I - DDD playbook for SDMM + contract-driven systems

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
- **Anti‑corruption Layer (ACL)**: translation layer protecting the domain model from external semantics.

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
      contracts/         # shared low-level contract types only (NOT the SSOT Contract Hub; avoid domain coupling)
```

**Rules**
- `domain/` MUST NOT depend on infrastructure (DB/network). Keep it testable and deterministic.
- Cross-context calls MUST go through `adapters/` (API) or explicit event/command contracts.
- “Shared” code MUST be carefully scoped. Sharing domain logic across contexts SHOULD be avoided; share via contracts and adapters instead.

### I.5 Classes, inheritance, and derived types (OOP guidance)

DDD does not require OOP, but many teams implement domain models with classes. Use these rules to keep changes AI-safe:

- **Prefer composition over inheritance**. Inheritance SHOULD be shallow (0–1 levels) and SHOULD NOT be used as a code reuse hack.
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
