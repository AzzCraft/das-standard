# Appendix L - DAS Tooling Standard (Reproducible Verify + Version Closure)

This appendix externalizes the tooling rules referenced by `SPECIFICATION.md` §10.5-§10.8.

## L.1 Purpose and scope

Tooling is part of the governed release surface. A repo cannot claim reproducible verification if the toolchain floats, if the verify runtime silently diverges from the standard/factory used to create the repo, or if the published release bundle omits the artifacts that the machine-readable manifest marks as required.

## L.2 Required concepts

### Repo-local tooling lock
A governed repo MUST pin the exact toolchain used by `verify` via a tooling lock, pinned image digest, `tool-versions` file, or an equivalent hermetic mechanism. The lock SHOULD record at least:

- the standard manifest version,
- the verify runtime ref,
- the source-of-truth ref for the repo-local verify environment,
- core tool versions,
- optional generator/policy-pack versions when they materially affect outputs,
- and, when local copies of the standard/policy packs exist, the originating snapshot ref and mirror purpose.

### Verify registry
A repo with multiple governed gates SHOULD keep a machine-readable verify registry so suites and dashboards do not infer semantics from CI job names.

### Verify report
Governed verify runs SHOULD emit a machine-readable report that records mode, build ref, toolchain pins, per-gate outcomes, and artifact refs.

### Verification tooling self-tests
Regulated or high-stakes repos SHOULD keep self-tests for custom verification tooling (at least one pass-case and one fail-case) so release gates do not rely on unvalidated validators.

### Suite lock
When standard/factory/verify runtime/policy packs are split across repos, a suite needs a lock artifact that pins module refs, repo roles, and override policy.

### Suite-level version closure
When standard, factory, verify runtime, policy pack, or orchestration tooling are versioned separately, a machine-readable closure manifest is required so release-critical flows do not drift.

### Release snapshots
Canonical standard releases and governed mirrors SHOULD be consumable as immutable snapshots rather than only as ad-hoc document drops.

## L.3 Pinned reference rules

Structured refs MUST use the following minimal shape:

```json
{
  "kind": "git|container_image|package|file|ci_workflow|custom",
  "uri": "...",
  "pinType": "commit|tag|digest|version|path|manifest",
  "pinValue": "...",
  "floating": false
}
```

Governed rules:

- `git -> commit | tag`
- `container_image -> digest`
- `package -> version`
- `file -> path | manifest`
- `ci_workflow -> path | manifest`
- floating `latest` / unpinned HEAD MUST NOT be treated as release truth
- governed release schemas MUST NOT accept legacy bare string refs where a structured ref is expected

## L.4 Report-only vs enforcement

Collecting tool metadata is not the same as enforcing it.

- `report_only` means the check emits information but does not block.
- `blocking` means failure prevents merge/promotion.
- `source_of_truth` means downstream systems should treat this emitted artifact as canonical for that governed surface.

Repos and suites MUST NOT present `report_only` checks as if they were equivalent to blocking conformance gates.

## L.5 No clone-tip / no floating-source rule

Release-critical or adoption-critical flows MUST NOT rely on clone-tip behavior as their effective source of truth. If a workflow needs a remote repo/module, it MUST pin a tag, commit, digest, version, manifest, or other machine-checkable immutable ref.

## L.6 Suite lock and closure together

A suite lock and a suite version closure are related but not identical.

- `suite.lock` captures module refs, repo roles, override policy, and allowed local states.
- suite version closure captures the exact standard/factory/runtime/policy-pack versions used together by a governed flow.

Pre-release flows SHOULD validate both artifacts together.

## L.7 Verify registry and verify report rules

A governed verify registry SHOULD declare, per gate:

- `gateId`
- gate kind
- cadence
- enforcement class
- command
- owner(s)
- `failureOnNoResults`
- expected artifact classes or refs when relevant

A governed verify report SHOULD record, per gate:

- whether the gate was expected,
- whether it executed,
- explicit outcome (`pass|fail|error|skipped|not_run`),
- artifact count / refs,
- and any fail-open prevention notes.

Blocking or source-of-truth gates that expect results MUST fail closed when no results are produced.

## L.8 Release-package completeness

If a governed release advertises `requiredArtifacts` and `normativeArtifactRefs`, the released bundle MUST physically ship those paths. The release bundle SHOULD also ship:

- an actual `verify_registry.json` for the bundle/repo,
- an actual `release_snapshot_manifest.json`,
- and examples for the shipped schemas.

A release self-check SHOULD validate:

1. every `requiredArtifacts` path exists,
2. every `normativeArtifactRefs` path resolves,
3. every `supportingArtifactRefs` path resolves,
4. every shipped example validates against the schema it claims to illustrate,
5. `VERSION` matches `standard_manifest.json`,
6. the release snapshot manifest inventories the shipped bundle consistently.

## L.9 Local mirrors and snapshot provenance

If a repo keeps a local copy of the canonical standard, policy pack, or another governed artifact:

- that copy MUST be declared as a mirror,
- the mirror MUST point to an immutable snapshot,
- local modifications MUST be forbidden unless governed as an extension,
- and adoption / standard-diff tooling SHOULD compare the mirror against the snapshot before mutation.

## L.10 Recommended release checks

Pre-release or adoption flows SHOULD run all of the following when applicable:

- tooling-lock schema validation,
- suite-lock schema validation,
- suite version closure schema validation,
- verify-registry schema validation,
- verify-report schema validation (for emitted reports),
- pinned-ref semantic checks,
- machine-readable manifest validation,
- release-package completeness audit,
- release snapshot verification,
- mirror provenance checks.
