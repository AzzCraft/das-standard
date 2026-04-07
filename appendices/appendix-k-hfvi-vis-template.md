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

## Appendix L - Deployment, environments, and external integrations (DAS-Deploy addendum)

The Main Body of this standard focuses on *design + implementation + verification*. Real-world delivery also requires consistent deployment practices across **dev/staging/prod**, cloud resources, external vendors, and AI providers.

This standard therefore defines a companion, normative addendum:

- **DAS Deployment & Environment Addendum (DAS-Deploy):** `DAS_DEPLOYMENT_ADDENDUM.md`

Minimum adoption rules (summary):

- **MUST (L1/L2):** Projects MUST document an **Environment Matrix** (dev/staging/prod and any canary/shadow envs) including: data class allowed, secrets strategy, external dependencies, rollback strategy, and verification gates per environment.
- **MUST (L1/L2):** Projects MUST document a **Deployment Pipeline**: artifact build strategy, promotion rules (same artifact promoted vs rebuild), migration strategy (DB / message / cache), and rollback/runbook links.
- **MUST:** External services (cloud managed services, AI APIs, vendors) MUST be treated as **contracted dependencies** with an owner, SLA/SLO expectations, rate limits, cost controls, and failure-mode handling.
- **SHOULD:** `verify` SHOULD be offline-by-default; reliance on live external vendors in CI SHOULD be stubbed/snapshotted unless explicitly justified.
- **MUST (L2):** L2 programs MUST add program-level governance controls for cross-team delivery (service catalog, change management, auditability, and security review gates).

If a project chooses not to adopt DAS-Deploy (e.g., pure library work), it MUST explicitly document the reason and the alternative operational standards it follows.
