# Appendix K - High-Fidelity Visual Interaction (HFVI) Extension: Visual Interaction Spec (VIS) Template

This appendix externalizes the VIS companion referenced by `SPECIFICATION.md` §6.8. It is used when a project declares interaction profile `hfvi_canvas_webgl_game`.

## K.1 Purpose and scope

The VIS template complements the normal UI Spec when interaction quality depends on real-time rendering, camera/input behavior, motion semantics, or replayable visual state. It exists so canvas/WebGL/game-like products can still be implemented and verified as Docs-as-Software rather than falling back to informal demo videos.

Goals:

- make spatial/temporal behavior implementable and testable (not prose-only)
- provide technical anchors so AI code generation is constrained
- enable deterministic replay and visual regression for critical interactions
- preserve traceability: workflows and screens (Appendix D) -> HFVI scenes/entities (Appendix K) -> tests (`verify --visual`)

Non-goals:

- This appendix is not a replacement for the design source of truth (Figma/prototype).
- This appendix is not a full engine architecture guide; it defines contract-like artifacts and gates.

## K.2 Minimum Document Control header

A governed VIS SHOULD include, at minimum:

- `Doc ID`
- `Owner`
- `Status`
- `Governing standard`
- `Last updated`
- `Scope`
- `Parent Master Doc`
- `Interaction profile: hfvi_canvas_webgl_game`

## K.3 Conventions and scene inventory (required)

For each HFVI surface, define:

- Coordinate system: origin, units, axis direction, rotation direction.
- Scaling strategy: DPR handling, zoom, camera transforms.
- Layering rules: z-order conventions and how focus/drag reorders.
- Input model: supported inputs (mouse/touch/keyboard/gamepad) and their mapping.
- Determinism controls: random seeds, time sources, and replay mode behavior.

**Scene inventory**

| Scene ID | Name | Engine surface | Target FPS | Notes |
|---|---|---|---|---|
| `SCN-001` | `{{NAME}}` | `{{ENGINE_OR_SURFACE}}` | `{{TARGET_FPS}}` | `[[NOTES]]` |

Rules:

- MUST: Every HFVI surface referenced by Appendix D MUST have a Scene ID here.
- SHOULD: Scenes SHOULD declare a frame budget (ms) and the measurement method.

## K.4 Visual aggregates and component anchors (required)

Each composite HFVI entity MUST be modeled as a visual aggregate with explicit invariants.

For each aggregate:

- Aggregate ID: `AGG-###`
- Inputs (domain/sim state): what state it consumes and from where
- Render props: what geometry/render state it owns
- Invariants (MUST): relationships that must always hold
- Debug checks (SHOULD): runtime assertions when `debugMode=true`

Example invariants:

- `HealthBar.y = CharacterBody.y - 20` always.
- Connection lines anchor to node ports even during drag.

**Visual component spec table**

| VC ID | Description | Engine primitive | Technical props/config anchors | Events | Test IDs |
|---|---|---|---|---|---|
| `VC-002` | `ConnectionLine` | `Konva.Arrow` | `tension:0.5; hitStrokeWidth:20` | `mouseenter/click` | `line-{from}-{to}` |

Rules:

- MUST: Any behavior that is hard to describe in prose MUST be expressed as technical anchors here.
- SHOULD: Prefer library-native names (Konva props, CSS props) as the anchor vocabulary.

## K.5 Motion design system and debug overlay contract (required)

HFVI projects MUST define motion tokens in the canonical token source (§4.5.1) and reference them by stable IDs.

| Token ID | Semantics | Tech spec |
|---|---|---|
| `MOT-REJECT` | `invalid action bounce` | `duration=400ms, elasticOut` |

Rules:

- MUST: No hardcoded motion parameters outside token sources.
- MAY (L0 bounded): temporary incubator tokens with owner + expiry.

When `debugMode=true`, each HFVI component MUST render:

- hit area / bounding box
- anchor point / transform origin
- optional: z-order/layer label and velocity vectors

Purpose:

- make hit-testing and transforms diagnosable
- make visual regression failures actionable (screenshots show geometry, not just final pixels)

## K.6 Verification mapping (required)

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

## K.7 Minimal VIS template

```markdown
# VIS - {{PRODUCT_OR_SCREEN}}

## Document Control
- Doc ID: {{DOC_ID}}
- Owner: {{OWNER}}
- Status: {{draft|active|frozen|deprecated}}
- Governing standard: {{STANDARD_REF}}
- Last updated: {{YYYY-MM-DD}}
- Scope: {{WHAT_THIS_VIS_COVERS}}
- Parent Master Doc: {{MASTER_DOC_PATH}}
- Interaction profile: hfvi_canvas_webgl_game

## 1. Purpose and interaction boundary
- Goal: {{USER_GOAL}}
- In scope: {{IN_SCOPE}}
- Out of scope: {{OUT_OF_SCOPE}}

## 2. Conventions
- Coordinate system: {{COORDINATE_SYSTEM}}
- Scaling / camera: {{SCALING_AND_CAMERA_RULES}}
- Layering rules: {{LAYERING_RULES}}
- Input model: {{INPUT_MODEL}}
- Determinism controls: {{DETERMINISM_CONTROLS}}

## 3. Scene inventory
| Scene ID | Name | Engine surface | Target FPS | Notes |
|---|---|---|---|---|
| {{SCENE_ID}} | {{NAME}} | {{ENGINE_SURFACE}} | {{TARGET_FPS}} | {{NOTES}} |

## 4. State model and camera / viewport behavior
- Entry state: {{ENTRY_STATE}}
- Primary interactive states: {{STATE_LIST}}
- Degraded / error states: {{DEGRADED_LIST}}
- Camera modes / zoom / pan rules: {{CAMERA_RULES}}

## 5. Visual aggregates and invariants
- Aggregate ID: {{AGG_ID}}
- Inputs: {{INPUTS}}
- Render props: {{RENDER_PROPS}}
- Invariants: {{INVARIANTS}}
- Debug checks: {{DEBUG_CHECKS}}

## 6. Visual component spec table
| VC ID | Description | Engine primitive | Technical props/config anchors | Events | Test IDs |
|---|---|---|---|---|---|
| {{VC_ID}} | {{DESCRIPTION}} | {{ENGINE_PRIMITIVE}} | {{ANCHORS}} | {{EVENTS}} | {{TEST_IDS}} |

## 7. Motion tokens and timing
| Token ID | Semantics | Tech spec |
|---|---|---|
| {{TOKEN_ID}} | {{SEMANTICS}} | {{TECH_SPEC}} |

## 8. Debug overlay contract
- Required overlays: {{OVERLAY_ELEMENTS}}
- Optional overlays: {{OPTIONAL_OVERLAYS}}
- Reduced-motion behavior: {{REDUCED_MOTION_RULES}}

## 9. Replayable fixtures and verification mapping
- Fixture IDs / seeds / manifests: {{FIXTURE_IDS}}
- Replay runner: {{RUNNER}}
- Visual baselines: {{BASELINE_IDS}}
- Assertions: {{ASSERTIONS}}
```

## K.8 Verification expectations

- HFVI products SHOULD treat scene state and interaction state as contract-adjacent surfaces.
- Replay fixtures SHOULD be deterministic enough for CI to detect regressions without relying on manual eyeballing alone.
- Visual regression SHOULD be paired with semantic state assertions so purely pixel-based baselines do not become the only source of truth.
- Frontend repos that ship HFVI surfaces MUST provide a `verify --visual` gate or an equivalent replay/visual baseline workflow.
