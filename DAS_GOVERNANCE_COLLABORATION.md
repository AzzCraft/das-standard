# DAS Governance & Collaboration Addendum (DAS-Gov)
> **Normative companion to the Docs as Software (DAS) Standard v1.3.0**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

**Name:** DAS Governance & Collaboration Addendum (中文：文码合一治理与协作附录)
**Maintained by:** AzzCraft Inc.
**Last updated:** 2026-01-29
**Status:** Normative

---

## Normative language

This document uses BCP 14 requirement keywords (**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**) as defined in the main DAS Standard.

---

## 1. Purpose and scope

This addendum defines the minimum governance required when **multiple people**, **multiple teams**, or **multiple companies** co-author DAS documents (Master Doc set, UI Spec, contract semantics, deployment addenda, etc.).

It covers:

- roles, ownership, and decision rights,
- PR/review rules and how to encode them,
- multi-company collaboration constraints (confidentiality, licensing, auditability),
- how to manage parallel doc edits safely (conflict avoidance + dispute resolution),
- practical templates.

This addendum **does not** replace your organization’s security/compliance policies. If there is a conflict, security/compliance wins.

---

## 2. Core principles

1. **One canonical intent**
   - There MUST be a single, version-controlled source of truth for each project’s requirements, contracts, and gates.

2. **Explicit decision ownership**
   - When a doc describes a contract surface or a cross-team integration rule, there MUST be exactly one decision owner.

3. **Docs move with code**
   - If docs describe behavior, the docs MUST be updated in the same PR that changes that behavior (or a waiver with expiry MUST exist).

4. **Fast conflict detection**
   - Governance SHOULD bias toward mechanical checks (links, IDs, schema inventories) so drift is detected early.

5. **Small, scannable “execution context”**
   - LLMs and humans both need small, high-signal entrypoints (Context Packs). Modularity is a governance tool, not just a formatting choice.

---

## 3. Roles and decision rights

### 3.1 Required roles

Each DAS-governed document MUST define these roles (they MAY be groups):

- **Document Owner**: accountable for correctness and freshness of the document.
- **Decision Owner**: final arbiter for contested changes impacting a cross-boundary surface (contracts, identifiers, security posture, deployment rules).
- **Reviewers**: required approvers (encoded in CODEOWNERS or equivalent).
- **Contributors**: anyone proposing changes.

Rules:

- **MUST:** Every document MUST declare a Document Owner.
- **MUST:** Any document section that defines a contract surface or cross-team rule MUST have a Decision Owner.
- **MUST:** Decision rights MUST be encoded in tooling (CODEOWNERS / branch protection), not only in prose.

### 3.2 Decision domains (recommended)

To avoid repeated disputes, programs SHOULD define decision domains:

- **Architecture/topology** (repo boundaries, runtime boundaries)
- **Contracts + identifiers** (schemas, semantics, fixtures, registries)
- **Security/compliance** (data classes, retention, audit)
- **Operations/deployment** (environment strategy, on-call, SLOs)
- **UX/system design** (screen IDs, routes, interaction contracts)

Each domain SHOULD have a named owner group.

---

## 4. Document control and structure

### 4.1 Required Document Control header

Every doc in the **Master Doc set** (including sub-docs) MUST begin with a minimal Document Control header.

**MUST include:**

- Doc Title
- Doc ID (stable)
- Owner
- Status (Draft/Active/Deprecated)
- Last updated (YYYY-MM-DD)
- Scope (what this doc covers / does not cover)

Recommended additional fields:

- Decision Owner(s)
- Related contracts (IDs)
- Related repos/modules
- Change log pointer

A minimal template is provided in §10.1.

### 4.2 Doc set rules (Master Doc modularization)

The main DAS Standard allows a Master Doc to be implemented as a **doc set** (canonical index + linked sub-docs).

Rules:

- **MUST:** There MUST be exactly one canonical Master Doc entrypoint.
- **MUST:** The entrypoint MUST contain the minimum required content (§9.4 of the main standard) and MUST link to any delegated content.
- **MUST:** All links in the canonical doc set MUST be stable (prefer repo-relative paths).
- **SHOULD:** Avoid duplicating the same truth in multiple places. If duplication is unavoidable, you MUST declare which one is SSOT.

### 4.3 Confidentiality and redaction

Multi-company programs often have mixed confidentiality.

Rules:

- **MUST:** Each doc SHOULD declare its confidentiality classification (public/internal/partner/restricted) if applicable.
- **MUST:** Restricted material MUST NOT be copied into repositories that are accessible to unauthorized parties.
- **SHOULD:** If the Master Doc must be shared externally, produce a redacted “Partner Pack” with the same IDs but with sensitive details removed.

---

## 5. Contribution workflow

### 5.1 Default workflow (required)

- **MUST:** All changes MUST be made via version control and PRs.
- **MUST:** PRs MUST reference an issue/task and must state:
  - scope (docs/sections touched),
  - impacted contracts/IDs,
  - expected verification gates.
- **MUST:** PRs that change contracts or deployment rules MUST include an explicit compatibility/rollout note.

### 5.2 RFC workflow (recommended for multi-company)

For high-impact or contentious changes, teams SHOULD use an RFC process.

When to require an RFC (recommended triggers):

- repo boundary changes,
- new contract families / envelope shapes,
- environment strategy changes (e.g., adding canary/shadow),
- data classification changes,
- vendor/provider changes (new AI provider, new cloud account model),
- SLO/availability commitments.

Rules:

- **SHOULD:** RFCs SHOULD be merged as PRs into `docs/rfcs/` (or similar).
- **MUST:** RFCs MUST have an explicit outcome: Accepted / Rejected / Superseded.

An RFC template is provided in §10.2.

### 5.3 Deprecation and supersession

- **MUST:** Deprecations MUST be explicit and time-bounded.
- **MUST:** A deprecated doc MUST link to its replacement.
- **SHOULD:** Use a consistent front-matter marker, e.g., `Status: Deprecated` + `Superseded by: ...`.

---

## 6. Reviews, approvals, and enforcement

### 6.1 Encoding approvals

Rules:

- **MUST:** Decision owners MUST be encoded in `CODEOWNERS` (or equivalent review rules).
- **MUST:** Branch protection MUST enforce required reviews for the docs paths that matter.
- **SHOULD:** Treat doc checks as part of `verify` (broken links, missing required headers, duplicate IDs).

### 6.2 Approval matrix (recommended)

Programs SHOULD document a simple approval matrix.

Example (customize):

| Change type | Required approvers |
| --- | --- |
| Master Doc scope/workflows | Document Owner + PM/Architect |
| Contract schema change | Contract Decision Owner + Consumer rep |
| Deployment policy change | Ops/SRE owner + Security |
| UI spec ID changes | Design owner + Frontend owner |
| Vendor integration | Integration owner + Security/Privacy |

---

## 6.3 Break-glass protocol (emergency changes)

Real systems sometimes fail at 03:00. A governance system that cannot handle emergencies will be bypassed informally, creating drift and hidden risk.

This section defines a **standardized emergency override** (“break-glass”) protocol.

### 6.3.1 When break-glass is allowed

- **MUST:** Break-glass MUST be limited to **Sev1/Sev2 incidents** (material user impact, data loss risk, safety risk, or significant financial loss).
- **MUST:** The incident commander (IC) MUST be named, and MUST record: incident ID, start time, impacted systems, and the rationale for override.

### 6.3.2 What can be overridden

- **MAY:** Slow gates MAY be deferred (e.g., long E2E suites, full visual regression, exhaustive evals).
- **MUST NOT:** Contract compatibility rules for externally observed or persisted surfaces MUST NOT be violated under break-glass.
- **MUST NOT (regulated / safety):** For systems operating under a regulated profile, break-glass MUST NOT bypass required compliance gates (e.g., mandated static analysis, required sign-offs). Tailoring MUST be defined in the profile/master doc.

### 6.3.3 Required controls during break-glass

- **MUST:** Every break-glass change MUST be:
  - in version control,
  - linked to the incident ID,
  - reviewed by at least one senior engineer not authoring the change (two-person rule).
- **MUST:** The PR description MUST explicitly list which gates were deferred.

### 6.3.4 Payback and drift prevention

- **MUST:** The system MUST generate a “debt payback” ticket (or equivalent) for each deferred gate set.
- **MUST:** Deferred gates MUST be re-run within **24 hours** (or the next business day) and results attached to the ticket.
- **SHOULD:** Teams SHOULD implement an automated enforcement rule: if payback is overdue, the default merge gate is tightened (branch freeze or release freeze) until resolved.

## 7. Multi-company specifics

### 7.1 IP/licensing

The DAS Standard is CC BY 4.0, but **project code and project docs may not be**.

Rules:

- **MUST:** Multi-company programs MUST define how contributions are licensed/attributed for project repos.
- **MUST:** If your program uses contributor agreements (CLA/DCO), it MUST be documented and enforced.
- **SHOULD:** Avoid copying proprietary content across organizations without an explicit agreement.

### 7.2 Auditability

Government/enterprise projects often need audit trails.

Rules:

- **MUST (L2):** Changes to cross-boundary rules (contracts, deployment policy, security posture) MUST be traceable to:
  - an issue/RFC/ADR,
  - PR approvals,
  - and a release milestone.

---

## 8. Parallel work, conflicts, and dispute resolution

### 8.1 Avoiding collisions

- **SHOULD:** Use doc modularization to reduce merge conflicts (split by repo/workflow/contract family).
- **SHOULD:** Use stable IDs and avoid renaming sections casually (renames create unnecessary conflicts).
- **MAY:** Use a lightweight “edit lease” convention (issue assignment) for high-churn sections.

### 8.2 Dispute resolution (required)

When two parties disagree on a change:

- **MUST:** The Decision Owner makes the final call.
- **MUST:** The outcome MUST be documented (ADR or RFC resolution) with:
  - what changed,
  - why,
  - compatibility/migration implications,
  - and who approved.
- **SHOULD:** If the Decision Owner is part of the dispute, escalate to the program’s architecture/security steering group.

---

## 9. AI-assisted writing and multi-orchestrator collaboration (optional but recommended)

This section is guidance for teams using multiple LLM “orchestrators” or AI agents while co-authoring docs.

Rules:

- **MUST:** AI-generated content MUST be reviewed by a human owner. LLM output is non-authoritative.
- **MUST:** Any AI-generated change that affects contracts, security posture, or deployment policy MUST be validated by `verify` and a domain owner.
- **SHOULD:** Use a bounded “Context Pack” as the only input context for orchestrators unless deeper docs are explicitly required.
- **SHOULD:** Require orchestrators to output changes as PR-ready diffs (not ad-hoc doc text) to preserve auditability.

---

## 10. Templates

### 10.1 Document Control header (template)

Copy/paste:

```md
---
Doc ID: DOC-XXX
Owner: <team or person>
Decision Owner: <team or person>  # optional if no cross-boundary decisions
Status: Draft | Active | Deprecated
Last updated: YYYY-MM-DD
Scope: <what this doc covers and what it explicitly does not>
---
```

### 10.2 DAS RFC (template)

```md
# RFC-YYYY-NNN: <title>

- Status: Draft | Accepted | Rejected | Superseded
- Owners: <names/teams>
- Decision Owner: <name/team>
- Related repos: <...>
- Related contracts/IDs: <...>
- Last updated: YYYY-MM-DD

## Problem

## Goals / non-goals

## Options considered

## Decision

## Compatibility / migration plan

## Verification plan

## Rollout plan

## Risks

## Open questions
```

### 10.3 Drift Decision Record (template)

```md
## Drift Decision Record

- Date: YYYY-MM-DD
- Discovered by: <...>
- Area: <docs|code|contracts|gates>
- Severity: <P0/P1/P2>

### What is drifting?

### Chosen resolution (pick one)

- [ ] Docs were wrong → update docs
- [ ] Code was wrong → fix code
- [ ] Intent changed → ADR + update both

### Compatibility impact

### Verification updates

### Owner + deadline
```

### 10.4 Waiver (template)

```md
## Waiver: <short title>

- Scope: <what requirement is being waived>
- Reason: <why>
- Owner: <who is accountable>
- Expiry: <date or milestone>
- Compensating controls: <tests, reviews, monitoring>
```

