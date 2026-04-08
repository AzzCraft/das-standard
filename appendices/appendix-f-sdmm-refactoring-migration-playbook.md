# Appendix F - SDMM refactoring & migration playbook

This appendix provides the “how” for large refactors and migrations in SDMM systems. It is intentionally **implementation‑oriented** and is meant to be used as a checklist during risky change windows.

### F.1 When this playbook is required

Use this playbook for changes that are any of:

- A breaking change to a **persisted** or cross‑repo contract (Compatibility Mode).
- A refactor that touches multiple SDMM modules with non‑trivial coupling.
- A major algorithm change that can regress quality or cost materially.
- A migration that replaces an adapter (I/O boundary) or prompt policy in production.

### F.2 Core rule: preserve one stable seam at a time

Large migrations fail when multiple seams move simultaneously.

- **MUST:** Keep at least one stable seam (contract, adapter interface, pipeline entrypoint) unchanged while migrating others.
- **SHOULD:** Prefer “expand/contract” over “flag day” changes for anything observed externally.

### F.3 Branch‑by‑abstraction (recommended default)

Use when replacing an implementation behind a stable interface.

1) Introduce an interface (port) in `core/` (or a stable module).
2) Keep the existing implementation as `OldImpl`.
3) Add the new implementation as `NewImpl`.
4) Switch wiring in the composition root (`pipelines/` or `integration/`) behind a flag/config.
5) Remove `OldImpl` only after metrics and eval gates pass.

### F.4 Expand / Contract (for contract changes)

Use when changing a contract consumed by other modules/repos.

**Expand phase**
- Add new fields as optional (tolerant readers).
- Dual‑write (produce both old + new) if needed.
- Add compatibility adapters.

**Contract phase**
- After consumers migrate, stop emitting old fields.
- Then remove parsing/handling of the old fields.

### F.5 Shadow mode / parallel run (for algorithms)

Use when validating a new pipeline without affecting users.

- Run the new pipeline in `dryRun` or `sandbox` sideEffectsMode.
- Compare outputs to the current pipeline using the same inputs.
- Record diffs, quality metrics, and budget deltas.
- Gate promotion on:
  - quality thresholds (EvalReport),
  - budget deltas within policy,
  - and failure‑mode parity.

### F.6 Golden fixtures + replay harness (mandatory for Tier 0/Tier 1 pipelines)

Maintain a **deterministic verification path** for the pipeline using a small set of **golden inputs**.

- Maintain a small set of **golden inputs** with expected outputs (or expected invariants / tolerances).
- Provide a **replay harness** that can run the pipeline against those inputs in CI with stable results:
  - **Tier 0:** the harness MUST be fully offline/deterministic (no live network). Record tool/LLM transcripts (“cassettes”) as needed.
  - **Tier 1:** the harness MUST be replayable given **pinned dependencies** (pinned model/tool versions, pinned datasets). Prefer recorded transcripts or stubbed responses over live calls.
- Prefer **invariant-based** checks (schemas, required fields, bounded score thresholds, citation integrity) over brittle full-string equality whenever feasible.
- Run the replay harness in CI to prevent regressions. Whether it gates every PR or runs in a `--full`/nightly tier depends on the project’s profile (§2.3) and CI policy (§10.3). When a replay suite is configured as a merge gate, failures MUST block merges.

### F.7 Prompt migrations (prompt policy as a contract)

Treat prompt changes like code changes:

- Pin prompt template versions.
- Track prompt policy in the RunManifest (`configHash`).
- Use eval gates for any prompt material change.
- Avoid mixing prompt and adapter changes in one release.

### F.8 Adapter migrations (I/O boundary)

Adapters are high‑risk because they are where side effects occur.

- Migrate adapters behind a stable port.
- Ensure `sideEffectsMode` checks are preserved.
- Add explicit integration tests for “no writes in dryRun”.

### F.9 Cutover checklist (minimum)

Before enabling the new path in production:

- Boundary lints pass (no deep imports; graph enforced).
- CI eval gates pass on pinned datasets.
- Replay harness passes (if Tier 0/Tier 1).
- Observability is in place (jobId/runId/manifestHash).
- Rollback path is documented and tested.
- The Master Doc traceability index is updated (§9 / Appendix C).
