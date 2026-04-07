## Appendix H - UI Design Review Checklist

This appendix complements **Appendix D (UI Spec Appendix)**. The UI Spec Appendix makes UI behavior *implementable and testable*; this checklist standardizes the *quality bar* for usability, accessibility, and user trust.

The checklist is split into:

- **Automatable checks** - SHOULD be enforced in CI (`verify`) using linting, accessibility tests, E2E smoke, and (when applicable) visual regression.
- **Judgement checks** - MUST be reviewed by a human (multimodal LLM assistance is optional, not authoritative).

### H.1 Severity policy

- **P0 (blocker):** MUST fix before merge/release.
- **P1 (should):** SHOULD fix before release; may defer only with an explicit owner + due date + rationale.
- **P2 (nice-to-have):** MAY defer; capture as backlog if repeated.

### H.2 Checklist

| Area | Check | Typical failure mode | Severity | Automatable? | Suggested enforcement |
| --- | --- | --- | --- | --- | --- |
| Design system governance | Token contract is versioned and consumed from the canonical source (no drift between design and code) | Token values drift between design and code; ad-hoc overrides proliferate; “incubator” tokens never expire | P0 | Partial | Pin token package + review token diffs; enforce incubator namespace + expiry; run visual regression on token changes (often in verify --full) |
| Semantic colors & CTA hierarchy | Primary/Secondary/Tertiary/Danger semantics are consistent across screens | “Confirm” for delete uses primary color; multiple “primary” CTAs in same region | P0 | Partial | Component API constraints + snapshot tests; manual review for semantics |
| Readability / contrast | Text, icons, borders meet contrast baseline; placeholders are visible | Low contrast grey-on-grey; placeholder nearly invisible | P0 | Yes | Token contrast script + axe checks (color contrast) |
| Accessibility | Keyboard navigation works; focus states visible; modals trap focus; Esc/close behavior; screen reader labels | Focus lost; cannot tab to controls; icon-only buttons without aria-label | P0 | Yes | Playwright/Cypress + axe-core; dedicated keyboard tests |
| States & feedback | Each critical screen covers Loading/Empty/Error/Permission states with consistent components | “Static screenshot” feeling; missing skeleton/empty state; errors only via toast | P0 | Partial | UI Spec Appendix coverage check + E2E state tests (mocked APIs) |
| AI-native states & feedback | AI screens distinguish Loading vs Thinking, cover Streaming/Repairing/Needs-confirmation, and provide cancel/retry | Generic spinners; no progress; streaming breaks usability; no recovery path | P0 | Partial | Enforce via UI Spec coverage + E2E state tests; manual review; see §6.7 |
| Citations / references | Citations render consistently and are linkable/previewable per the citation contract (§4.4.9), including integrity.status handling | Backend emits [doc_1] labels UI cannot resolve; broken links; inaccessible tooltips; raw markers leak | P0 | Partial | Contract tests + UI renderer unit tests/E2E; spec-defined interactions in Appendix D; graceful fallback for partial/invalid |
| Form validation | Required fields are marked; inline errors near fields; clear validation copy | Errors only via toast; required not marked; unclear copy | P1 | Partial | Component-level tests + i18n lint; manual review for copy clarity |
| Destructive actions | Danger styling; confirmation includes object identity; irreversibility explained | Generic “Confirm”; no object shown; easy mis-click | P0 | Partial | Component pattern + E2E; manual review for copy |
| Information architecture | Screen/module naming matches content; navigation matches user permissions | “Permissions mgmt” screen shows only user list; teacher sees admin menu | P0 | Partial | Role-based E2E snapshots; manual review for IA |
| Consistency of list pages | Standard list toolbar layout (search/filter/sort + primary CTA); pagination consistency | Toolbars reorganized per page; pagination alignment differs | P1 | Partial | Shared layout components; visual regression across representative pages |
| Table/list density & alignment | Alignment rules (numbers/date/text) and density are consistent; optional compact mode | Numeric columns not right-aligned; row height inconsistent | P2 | Partial | CSS lint for alignment classes; visual regression |
| Discoverability | Icon-only controls have tooltips/labels; click targets meet minimum size | Small unlabeled icons; unclear click targets | P1 | Partial | E2E hover checks; a11y label enforcement; manual review for UX |
| Data credibility (dashboards) | Units, definitions, time window, and totals are correct and non-misleading | KPI shown as percent when should be count; pie chart ≠ 100% | P0 | Partial | Unit tests for data transforms; manual review for semantics |
| Review artifacts | Design/fixtures use synthetic data and cover edge cases | Repeated sample rows cause “duplicate data bug” confusion | P1 | Partial | Fixture lints; manual review checklist |
| Testability hooks | Critical interactions have stable data-testid selectors | Unstable selectors; missing hooks for E2E | P0 | Yes | Lint/check in UI Spec + E2E test harness |
| Design-to-code traceability | Screen IDs (UI-###) map to named frames in the design source of truth | Figma links rot; designs change without code noticing | P1 | Yes (advanced) | scripts/verify/design checks design source (e.g., Figma API) for frames referenced in Appendix D |
| Visual contract (atomic components) | UI kit component states defined in the spec exist as stories and are snapshotted in CI | “Should” becomes “never”; subtle component regressions ship unnoticed | P0 | Yes | Storybook (or equivalent) + snapshot baselines; run on PR when UI kit changes, otherwise in verify --full/nightly |
| Visual regression | Critical screens have baseline screenshots and are protected from accidental drift | Unreviewed UI drift; spacing changes unnoticed; flakiness causes gate fatigue | P1 | Yes | Visual regression tool (Playwright snapshot/Percy/etc.); prefer verify --full + path-based triggers to control cost |

### H.4 HFVI (canvas/WebGL/game) checks

This section applies when `interactionProfile = hfvi_canvas_webgl_game`.

| Area | Check | Typical failure mode | Severity | Automatable? | Suggested enforcement |
| --- | --- | --- | --- | --- | --- |
| Hit-testing correctness | Debug overlay renders hit areas/bounds/anchors for all interactive HFVI components | Click targets offset; invisible hit areas; transform origin bugs | P0 | Partial | verify --visual replay + debug overlay screenshots |
| No magic motion | Motion parameters are exclusively sourced from motion tokens | Hardcoded durations/easings regress feel and consistency | P0 | Yes | Token lint + grep checks + code review |
| Replay fixtures | Critical interactions have cassette fixtures and are replayable deterministically | CI cannot reproduce; manual testing required; flaky E2E | P0 | Yes | Playwright (or equivalent) replay runner |
| Visual regression | Key frames are snapshotted and reviewed on change | Unreviewed drift in layering/animation/layout | P1 | Yes | Snapshot diff tooling in verify --visual / --full |
| Performance budget | Target FPS / frame budget declared and tracked | Degraded interaction; jank; unbounded redraw | P1 | Partial | Perf smoke + telemetry + manual review |

### H.3 Recommended minimum automation bundle (frontend)

A repo with user-facing UI SHOULD include the following across its `verify` tiers (see §10.3):

**Fast / PR gate (`verify`)**

1. Boundary + lint (JS/TS + styles). Token enforcement applies per §4.5.1 and the project profile.
1. Unit tests for UI logic and state.
1. Accessibility checks (axe) on critical flows (keyboard + labels + focus + contrast).
1. Minimal E2E smoke for critical workflows, traceable to the UI Spec Appendix (Appendix D).

**Full / nightly or pre-release (`verify --full`)**

1. **UI kit visual contract** (when a UI kit exists): stories + snapshot baselines for all spec-defined component states.
1. Screen-level visual regression for critical screens or high-trust surfaces.
1. (Advanced) Design-to-code traceability check (UI-### ↔ named design frames) to detect orphaned specs.
