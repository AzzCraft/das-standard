<a id="appendix-d-ui-spec-appendix-template-v1"></a>

## Appendix D - UI Spec Appendix Template

### UI Spec Appendix - Template

- **Status:** `{{STATUS}}` (`draft | active | frozen | deprecated`)
- **Version:** `{{VERSION}}` (SemVer recommended)
- **Last updated:** `{{LAST_UPDATED_YYYY_MM_DD}}`
- **Owners:** PM `{{OWNER_PM}}`, Design `{{OWNER_DESIGN}}`, Eng `{{OWNER_ENG}}`
- **Design source of truth:** `{{FIGMA_OR_PROTOTYPE_URL}}`
- **Design system / tokens:** `[[DESIGN_SYSTEM_LINK_OR_PATH]]`
- **Asset directory (repo):** `docs/assets/ui/{{YYYYMMDD}}/` (recommended)

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
