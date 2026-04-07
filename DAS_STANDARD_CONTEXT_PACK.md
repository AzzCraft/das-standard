# DAS Standard Context Pack (v1.3.0)
> **Read-optimized quick reference for humans + LLMs**

**Source:** Docs as Software (DAS) Standard v1.3.0 (`SPECIFICATION.md`)
**Last updated:** 2026-01-29

---

## 1. What DAS is (in one paragraph)

DAS is a unified engineering methodology for AI-enabled products. It treats **docs like code** (versioned, reviewed, verified) and treats anything crossing a boundary (repo/service/storage) as a **contract surface** with schema + semantics + fixtures + executable checks. It assumes mixed versions are the norm (Compatibility Mode) and requires a single-command `verify` gate per repo.

---

## 2. The minimum non-negotiables (MUST list)

- **MUST:** Declare a conformance profile (`L0|L1|L2`) in the project Master Doc.
- **MUST:** Maintain a canonical, versioned **Master Doc** per project with: contract inventory, traceability index, `verify` commands, and an execution plan.
- **MUST:** Treat cross-boundary and/or persisted interfaces as **Compatibility Mode** unless you can *prove and enforce* atomic cutover.
- **MUST:** For each contract surface: provide **schema + semantics + fixtures + executable checks**.
- **MUST:** Provide exactly one canonical `verify` entrypoint per repo (fast, deterministic, CI-capable).
- **MUST:** If docs and code diverge (doc drift), record it and resolve it via doc update, code fix, or ADR.

---

## 3. Boundary thinking you should not get wrong

- **Repo boundary** ≠ **runtime boundary**.
- Split repos to reduce change scope; do **not** split services unless operationally justified.
- Default to **monorepo + SDMM** or **hybrid** with a contract hub. Add runtime services only when required.

---

## 4. How to structure a typical system

Recommended repos (hybrid):

- `contracts` (contract hub): schemas, fixtures, semantics, API registry, codegen config, contract tests
- `backend` (SoR + orchestrator): validation, error mapping, async jobs
- `algo` (AI compute): pipelines, deterministic evals, replay
- `frontend` (UI): UI spec appendix, selectors, minimal E2E smoke
- `integration` (system verify): smoke tests, compatibility runner, compose/dev harness

---

## 5. Docs scaling (token-cost control)

- Use a **doc set**: a canonical Master Doc entrypoint plus linked sub-docs.
- Keep an intentionally small **Context Pack** (`docs/context-pack.md` or `AI_README.md`) with:
  - glossary + invariants
  - system diagram + critical flows
  - contract inventory summary
  - `verify` commands
  - current tasks

---

## 6. Deployment and environments (DAS-Deploy)

For real products (L1/L2), adopt **DAS-Deploy**:

- Maintain an **Environment Matrix** (dev/staging/prod) with data class rules and rollback.
- Document a **Deployment Pipeline** (artifact identity, promotion, migrations, runbooks).
- Track external vendors/AI providers in a **Dependency Registry**.

See: `DAS_DEPLOYMENT_ADDENDUM.md`.

---

## 7. Multi-team / multi-company governance (DAS-Gov)

- Every doc must have an Owner; cross-boundary rules must have a Decision Owner.
- Encode approval rules in tooling (CODEOWNERS / branch protection).
- Use RFC/ADR for contentious changes.

See: `DAS_GOVERNANCE_COLLABORATION.md`.
